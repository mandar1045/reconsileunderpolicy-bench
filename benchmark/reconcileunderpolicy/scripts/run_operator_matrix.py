#!/usr/bin/env python3

import argparse
import csv
import json
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median, pstdev


ROOT = Path(__file__).resolve().parents[3]
BENCH_ROOT = ROOT / "benchmark" / "reconcileunderpolicy"
DEFAULT_RESULTS_ROOT = BENCH_ROOT / "results"
ENV_ROOT = BENCH_ROOT / "environments"

SCENARIO_ORDER = [
    "baseline_create",
    "restart_during_scale",
    "quota_blocked_scale",
    "delete_and_recreate",
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def timestamp_slug():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def run(cmd, check=True, capture_output=True):
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    result = subprocess.run(
        cmd,
        text=True,
        capture_output=capture_output,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({' '.join(cmd)}):\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload):
    write_text(path, json.dumps(payload, indent=2))


def wait_for(condition_fn, timeout_s, interval_s=2.0, description="condition"):
    deadline = time.time() + timeout_s
    last_error = None
    while time.time() < deadline:
        try:
            if condition_fn():
                return True
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(interval_s)
    if last_error is not None:
        raise RuntimeError(f"Timed out waiting for {description}: {last_error}")
    return False


def mean_or_zero(values):
    return round(mean(values), 2) if values else 0.0


def median_or_zero(values):
    return round(median(values), 2) if values else 0.0


def stdev_or_zero(values):
    return round(pstdev(values), 2) if len(values) > 1 else 0.0


@dataclass(frozen=True)
class EnvironmentProfile:
    key: str
    display_name: str
    cluster_name: str
    config_path: Path
    node_count: int

    @property
    def context_name(self):
        return f"kind-{self.cluster_name}"


ENVIRONMENTS = {
    "single-node": EnvironmentProfile(
        key="single-node",
        display_name="Single-node kind",
        cluster_name="reconcile-under-policy-single-node",
        config_path=ENV_ROOT / "kind-single-node.yaml",
        node_count=1,
    ),
    "multi-node": EnvironmentProfile(
        key="multi-node",
        display_name="Multi-node kind",
        cluster_name="reconcile-under-policy-multi-node",
        config_path=ENV_ROOT / "kind-multi-node.yaml",
        node_count=3,
    ),
}


class KubectlClient:
    def __init__(self, context: str):
        self.context = context

    def run(self, *args, check=True):
        return run(["kubectl", "--context", self.context, *args], check=check)


class BaseOperatorBenchmark:
    operator_key = ""
    operator_display_name = ""
    namespace = ""
    operator_namespace = ""
    cluster_name = "hello-world"
    operator_deployment = ""
    operator_pod_selector = ""

    def __init__(self, study_dir: Path, client: KubectlClient):
        self.study_dir = study_dir
        self.client = client
        self.temp_dir = study_dir / "tmp"
        self.manifest_path = self.temp_dir / f"{self.operator_key}-cluster.yaml"
        self.quota_path = self.temp_dir / f"{self.operator_key}-quota.yaml"
        self.operator_manifest_path = study_dir / f"{self.operator_key}-operator-install.yaml"

    def kubectl(self, *args, check=True):
        return self.client.run(*args, check=check)

    def ensure_namespace(self):
        self.kubectl("create", "namespace", self.namespace, check=False)

    def install_operator(self):
        write_text(self.operator_manifest_path, self.render_operator_manifest())
        self.kubectl("apply", "-f", str(self.operator_manifest_path))
        self.wait_for_operator_ready(timeout_s=240)

    def render_operator_manifest(self):
        raise NotImplementedError

    def wait_for_operator_ready(self, timeout_s=240):
        self.kubectl(
            "wait",
            "-n",
            self.operator_namespace,
            "--for=condition=Available",
            f"deployment/{self.operator_deployment}",
            f"--timeout={timeout_s}s",
        )

    def build_cluster_manifest(self, replicas: int) -> str:
        raise NotImplementedError

    def apply_cluster(self, replicas: int):
        write_text(self.manifest_path, self.build_cluster_manifest(replicas))
        self.kubectl("apply", "-f", str(self.manifest_path))

    def patch_cluster_replicas(self, replicas: int):
        raise NotImplementedError

    def delete_cluster(self):
        raise NotImplementedError

    def get_operator_pod(self):
        result = self.kubectl(
            "-n",
            self.operator_namespace,
            "get",
            "pods",
            "-l",
            self.operator_pod_selector,
            "-o",
            "jsonpath={.items[0].metadata.name}",
        )
        return result.stdout.strip()

    def delete_operator_pod(self):
        pod = self.get_operator_pod()
        self.kubectl("-n", self.operator_namespace, "delete", "pod", pod, "--wait=false")
        return pod

    def get_ready_replicas(self):
        raise NotImplementedError

    def get_desired_replicas(self):
        raise NotImplementedError

    def wait_for_replicas(self, expected: int, timeout_s=360):
        def cond():
            return self.get_desired_replicas() == expected and self.get_ready_replicas() == expected

        ok = wait_for(cond, timeout_s, description=f"{expected} ready replicas")
        if not ok:
            raise RuntimeError(f"Timed out waiting for {expected} ready replicas")

    def wait_for_cluster_absent(self, timeout_s=360):
        raise NotImplementedError

    def create_quota(self, max_pods: int):
        manifest = f"""apiVersion: v1
kind: ResourceQuota
metadata:
  name: pod-quota
  namespace: {self.namespace}
spec:
  hard:
    pods: "{max_pods}"
"""
        write_text(self.quota_path, manifest)
        self.kubectl("apply", "-f", str(self.quota_path))

    def delete_quota(self):
        self.kubectl("-n", self.namespace, "delete", "resourcequota", "pod-quota", check=False)

    def snapshot_commands(self):
        return {}

    def collect_snapshot(self, scenario_name: str, trial_dir: Path):
        snapshot_dir = trial_dir / scenario_name
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        write_text(
            snapshot_dir / "pods.txt",
            self.kubectl("-n", self.namespace, "get", "pods", "-o", "wide", check=False).stdout,
        )
        write_text(
            snapshot_dir / "pvc.txt",
            self.kubectl("-n", self.namespace, "get", "pvc", "-o", "wide", check=False).stdout,
        )
        write_text(
            snapshot_dir / "events.txt",
            self.kubectl("-n", self.namespace, "get", "events", "--sort-by=.lastTimestamp", check=False).stdout,
        )
        for filename, command in self.snapshot_commands().items():
            write_text(snapshot_dir / filename, self.kubectl(*command, check=False).stdout)

    def cleanup_workloads(self):
        raise NotImplementedError

    def scenario_baseline_create(self, trial_dir: Path):
        start = time.time()
        self.cleanup_workloads()
        self.apply_cluster(1)
        self.wait_for_replicas(1, timeout_s=420)
        duration = time.time() - start
        self.collect_snapshot("baseline_create", trial_dir)
        return {
            "name": "baseline_create",
            "success": True,
            "duration_seconds": round(duration, 2),
            "final_ready_replicas": self.get_ready_replicas(),
            "notes": f"Created a one-node {self.operator_display_name} cluster and measured time to first healthy reconciliation.",
        }

    def scenario_restart_during_scale(self, trial_dir: Path):
        start = time.time()
        self.patch_cluster_replicas(2)
        deleted_operator_pod = self.delete_operator_pod()
        self.wait_for_operator_ready(timeout_s=240)
        self.wait_for_replicas(2, timeout_s=480)
        duration = time.time() - start
        self.collect_snapshot("restart_during_scale", trial_dir)
        return {
            "name": "restart_during_scale",
            "success": True,
            "duration_seconds": round(duration, 2),
            "final_ready_replicas": self.get_ready_replicas(),
            "operator_pod_deleted": deleted_operator_pod,
            "notes": "Scaled from 1 to 2 replicas while deleting the operator pod to force recovery from an interrupted reconcile path.",
        }

    def scenario_quota_blocked_scale(self, trial_dir: Path):
        start = time.time()
        self.create_quota(2)
        self.patch_cluster_replicas(3)
        time.sleep(20)
        ready_while_blocked = self.get_ready_replicas()
        self.delete_quota()
        self.wait_for_replicas(3, timeout_s=480)
        duration = time.time() - start
        self.collect_snapshot("quota_blocked_scale", trial_dir)
        return {
            "name": "quota_blocked_scale",
            "success": True,
            "duration_seconds": round(duration, 2),
            "ready_replicas_during_policy_block": ready_while_blocked,
            "final_ready_replicas": self.get_ready_replicas(),
            "notes": "Applied a ResourceQuota to intentionally block pod creation during scale-up, then removed it and measured recovery.",
        }

    def scenario_delete_and_recreate(self, trial_dir: Path):
        start = time.time()
        self.delete_cluster()
        self.wait_for_cluster_absent(timeout_s=480)
        self.apply_cluster(1)
        self.wait_for_replicas(1, timeout_s=480)
        duration = time.time() - start
        self.collect_snapshot("delete_and_recreate", trial_dir)
        return {
            "name": "delete_and_recreate",
            "success": True,
            "duration_seconds": round(duration, 2),
            "final_ready_replicas": self.get_ready_replicas(),
            "notes": "Deleted the managed cluster and measured the time required to recreate it and return to a healthy single-replica state.",
        }

    def run_trial(self, trial_number: int):
        trial_dir = self.study_dir / f"trial_{trial_number:02d}"
        trial_dir.mkdir(parents=True, exist_ok=True)
        trial_summary = {
            "trial": trial_number,
            "started_at": now_iso(),
            "scenarios": [],
        }
        self.wait_for_operator_ready(timeout_s=240)
        try:
            trial_summary["scenarios"].append(self.scenario_baseline_create(trial_dir))
            trial_summary["scenarios"].append(self.scenario_restart_during_scale(trial_dir))
            trial_summary["scenarios"].append(self.scenario_quota_blocked_scale(trial_dir))
            trial_summary["scenarios"].append(self.scenario_delete_and_recreate(trial_dir))
            trial_summary["success"] = True
        except Exception as exc:  # noqa: BLE001
            trial_summary["success"] = False
            trial_summary["error"] = str(exc)
            self.collect_snapshot("failure_snapshot", trial_dir)
            raise
        finally:
            trial_summary["completed_at"] = now_iso()
            write_json(trial_dir / "trial_summary.json", trial_summary)
        return trial_summary


class RabbitMQBenchmark(BaseOperatorBenchmark):
    operator_key = "rabbitmq"
    operator_display_name = "RabbitMQ Cluster Operator"
    namespace = "rup-rabbitmq"
    operator_namespace = "rabbitmq-system"
    operator_deployment = "rabbitmq-cluster-operator"
    operator_pod_selector = "app.kubernetes.io/name=rabbitmq-cluster-operator"
    operator_root = ROOT / "vendor" / "cluster-operator-main"
    operator_install_root = operator_root / "config" / "installation"

    def render_operator_manifest(self):
        return self.kubectl("kustomize", str(self.operator_install_root)).stdout

    def build_cluster_manifest(self, replicas: int) -> str:
        return f"""apiVersion: rabbitmq.com/v1beta1
kind: RabbitmqCluster
metadata:
  name: {self.cluster_name}
  namespace: {self.namespace}
spec:
  replicas: {replicas}
  persistence:
    storageClassName: standard
    storage: 2Gi
  resources:
    requests:
      cpu: 200m
      memory: 512Mi
    limits:
      cpu: 500m
      memory: 1Gi
"""

    def patch_cluster_replicas(self, replicas: int):
        self.kubectl(
            "-n",
            self.namespace,
            "patch",
            "rabbitmqcluster",
            self.cluster_name,
            "--type=merge",
            "-p",
            json.dumps({"spec": {"replicas": replicas}}),
        )

    def delete_cluster(self):
        self.kubectl(
            "-n",
            self.namespace,
            "delete",
            "rabbitmqcluster",
            self.cluster_name,
            "--wait=false",
            check=False,
        )

    def get_ready_replicas(self):
        result = self.kubectl(
            "-n",
            self.namespace,
            "get",
            "statefulset",
            f"{self.cluster_name}-server",
            "-o",
            "jsonpath={.status.readyReplicas}",
            check=False,
        )
        value = result.stdout.strip()
        return int(value) if value else 0

    def get_desired_replicas(self):
        result = self.kubectl(
            "-n",
            self.namespace,
            "get",
            "statefulset",
            f"{self.cluster_name}-server",
            "-o",
            "jsonpath={.spec.replicas}",
            check=False,
        )
        value = result.stdout.strip()
        return int(value) if value else 0

    def wait_for_cluster_absent(self, timeout_s=360):
        def cond():
            cluster_result = self.kubectl(
                "-n",
                self.namespace,
                "get",
                "rabbitmqcluster",
                self.cluster_name,
                check=False,
            )
            sts_result = self.kubectl(
                "-n",
                self.namespace,
                "get",
                "statefulset",
                f"{self.cluster_name}-server",
                check=False,
            )
            return cluster_result.returncode != 0 and sts_result.returncode != 0

        ok = wait_for(cond, timeout_s, description="RabbitMQ cluster deletion")
        if not ok:
            raise RuntimeError("Timed out waiting for RabbitMQ cluster deletion")

    def wait_for_workload_cleanup(self, timeout_s=360):
        def cond():
            cluster_result = self.kubectl(
                "-n",
                self.namespace,
                "get",
                "rabbitmqcluster",
                self.cluster_name,
                check=False,
            )
            sts_result = self.kubectl(
                "-n",
                self.namespace,
                "get",
                "statefulset",
                f"{self.cluster_name}-server",
                check=False,
            )
            pods_result = self.kubectl(
                "-n",
                self.namespace,
                "get",
                "pods",
                "-o",
                "name",
                check=False,
            )
            pvc_result = self.kubectl(
                "-n",
                self.namespace,
                "get",
                "pvc",
                "-o",
                "name",
                check=False,
            )
            return (
                cluster_result.returncode != 0
                and sts_result.returncode != 0
                and not pods_result.stdout.strip()
                and not pvc_result.stdout.strip()
            )

        ok = wait_for(cond, timeout_s, description="RabbitMQ workload cleanup")
        if not ok:
            raise RuntimeError("Timed out waiting for RabbitMQ workload cleanup")

    def snapshot_commands(self):
        return {
            "cluster.yaml": ["-n", self.namespace, "get", "rabbitmqcluster", self.cluster_name, "-o", "yaml"],
            "statefulset.yaml": ["-n", self.namespace, "get", "statefulset", "-o", "yaml"],
        }

    def cleanup_workloads(self):
        self.delete_quota()
        self.delete_cluster()
        self.kubectl("-n", self.namespace, "delete", "statefulset", f"{self.cluster_name}-server", "--ignore-not-found=true", check=False)
        self.kubectl("-n", self.namespace, "delete", "service", self.cluster_name, f"{self.cluster_name}-nodes", "--ignore-not-found=true", check=False)
        self.kubectl("-n", self.namespace, "delete", "secret", f"{self.cluster_name}-default-user", "--ignore-not-found=true", check=False)
        self.kubectl("-n", self.namespace, "delete", "pvc", "--all", check=False)
        self.wait_for_workload_cleanup(timeout_s=480)
        time.sleep(5)


class CloudNativePgBenchmark(BaseOperatorBenchmark):
    operator_key = "cloudnative-pg"
    operator_display_name = "CloudNativePG"
    namespace = "rup-cnpg"
    operator_namespace = "cnpg-system"
    operator_deployment = "cnpg-controller-manager"
    operator_pod_selector = "app.kubernetes.io/name=cloudnative-pg"
    operator_release_manifest = ROOT / "vendor" / "cloudnative-pg" / "releases" / "cnpg-1.29.0.yaml"
    cluster_pod_selector = "cnpg.io/cluster=hello-world"

    def render_operator_manifest(self):
        return self.operator_release_manifest.read_text(encoding="utf-8")

    def install_operator(self):
        write_text(self.operator_manifest_path, self.render_operator_manifest())
        self.kubectl("apply", "--server-side=true", "-f", str(self.operator_manifest_path))
        self.wait_for_operator_ready(timeout_s=240)

    def build_cluster_manifest(self, replicas: int) -> str:
        return f"""apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: {self.cluster_name}
  namespace: {self.namespace}
spec:
  imageName: ghcr.io/cloudnative-pg/postgresql:17
  instances: {replicas}
  primaryUpdateStrategy: unsupervised
  storage:
    size: 1Gi
  resources:
    requests:
      cpu: 200m
      memory: 512Mi
    limits:
      cpu: 500m
      memory: 1Gi
"""

    def patch_cluster_replicas(self, replicas: int):
        self.kubectl(
            "-n",
            self.namespace,
            "patch",
            "cluster",
            self.cluster_name,
            "--type=merge",
            "-p",
            json.dumps({"spec": {"instances": replicas}}),
        )

    def delete_cluster(self):
        self.kubectl(
            "-n",
            self.namespace,
            "delete",
            "cluster",
            self.cluster_name,
            "--wait=false",
            check=False,
        )

    def get_ready_replicas(self):
        result = self.kubectl(
            "-n",
            self.namespace,
            "get",
            "cluster",
            self.cluster_name,
            "-o",
            "jsonpath={.status.readyInstances}",
            check=False,
        )
        value = result.stdout.strip()
        return int(value) if value else 0

    def get_desired_replicas(self):
        result = self.kubectl(
            "-n",
            self.namespace,
            "get",
            "cluster",
            self.cluster_name,
            "-o",
            "jsonpath={.spec.instances}",
            check=False,
        )
        value = result.stdout.strip()
        return int(value) if value else 0

    def wait_for_cluster_absent(self, timeout_s=360):
        def cond():
            cluster_result = self.kubectl(
                "-n",
                self.namespace,
                "get",
                "cluster",
                self.cluster_name,
                check=False,
            )
            pods_result = self.kubectl(
                "-n",
                self.namespace,
                "get",
                "pods",
                "-l",
                self.cluster_pod_selector,
                "-o",
                "name",
                check=False,
            )
            return cluster_result.returncode != 0 and not pods_result.stdout.strip()

        ok = wait_for(cond, timeout_s, description="CloudNativePG cluster deletion")
        if not ok:
            raise RuntimeError("Timed out waiting for CloudNativePG cluster deletion")

    def snapshot_commands(self):
        return {
            "cluster.yaml": ["-n", self.namespace, "get", "cluster", self.cluster_name, "-o", "yaml"],
            "services.yaml": ["-n", self.namespace, "get", "svc", "-l", self.cluster_pod_selector, "-o", "yaml"],
        }

    def cleanup_workloads(self):
        self.delete_quota()
        self.delete_cluster()
        wait_for(
            lambda: self.kubectl("-n", self.namespace, "get", "cluster", self.cluster_name, check=False).returncode != 0,
            timeout_s=120,
            description="CloudNativePG cluster resource removal",
        )
        self.kubectl("-n", self.namespace, "delete", "pod", "-l", self.cluster_pod_selector, "--wait=false", check=False)
        self.kubectl("-n", self.namespace, "delete", "pvc", "--all", check=False)
        self.kubectl("-n", self.namespace, "delete", "job", "--all", check=False)
        self.kubectl("-n", self.namespace, "delete", "secret", "-l", self.cluster_pod_selector, check=False)
        time.sleep(5)


OPERATORS = {
    "rabbitmq": RabbitMQBenchmark,
    "cloudnative-pg": CloudNativePgBenchmark,
}


def build_aggregates(trials):
    scenario_map = {
        name: {
            "scenario": name,
            "successful_trials": 0,
            "total_trials": len(trials),
            "durations_seconds": [],
        }
        for name in SCENARIO_ORDER
    }
    for trial in trials:
        for scenario in trial.get("scenarios", []):
            slot = scenario_map[scenario["name"]]
            if scenario.get("success"):
                slot["successful_trials"] += 1
            if "duration_seconds" in scenario:
                slot["durations_seconds"].append(scenario["duration_seconds"])

    aggregates = []
    for name in SCENARIO_ORDER:
        slot = scenario_map[name]
        durations = slot["durations_seconds"]
        aggregates.append(
            {
                "scenario": name,
                "successful_trials": slot["successful_trials"],
                "total_trials": slot["total_trials"],
                "success_rate": round(slot["successful_trials"] / slot["total_trials"], 2) if slot["total_trials"] else 0.0,
                "mean_seconds": mean_or_zero(durations),
                "median_seconds": median_or_zero(durations),
                "min_seconds": round(min(durations), 2) if durations else 0.0,
                "max_seconds": round(max(durations), 2) if durations else 0.0,
                "stdev_seconds": stdev_or_zero(durations),
                "durations_seconds": durations,
            }
        )
    return aggregates


def write_csv_summary(study_dir: Path, aggregates):
    csv_path = study_dir / "scenario_stats.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "scenario",
                "successful_trials",
                "total_trials",
                "success_rate",
                "mean_seconds",
                "median_seconds",
                "min_seconds",
                "max_seconds",
                "stdev_seconds",
                "durations_seconds",
            ]
        )
        for item in aggregates:
            writer.writerow(
                [
                    item["scenario"],
                    item["successful_trials"],
                    item["total_trials"],
                    item["success_rate"],
                    item["mean_seconds"],
                    item["median_seconds"],
                    item["min_seconds"],
                    item["max_seconds"],
                    item["stdev_seconds"],
                    ";".join(str(value) for value in item["durations_seconds"]),
                ]
            )


def write_markdown_summary(study_dir: Path, summary):
    lines = [
        f"# {summary['operator']} Benchmark Study",
        "",
        f"- Study directory: `{summary['study_dir']}`",
        f"- Environment: `{summary['environment_display_name']}`",
        f"- Cluster context: `{summary['cluster_context']}`",
        f"- Trials completed: `{len(summary['trials'])}`",
        f"- Overall success: `{summary['success']}`",
        "",
        "## Scenario statistics",
        "",
        "| Scenario | Success | Mean (s) | Median (s) | Min (s) | Max (s) | Stddev (s) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summary["aggregates"]:
        lines.append(
            f"| `{item['scenario']}` | `{item['successful_trials']}/{item['total_trials']}` | "
            f"{item['mean_seconds']:.2f} | {item['median_seconds']:.2f} | {item['min_seconds']:.2f} | "
            f"{item['max_seconds']:.2f} | {item['stdev_seconds']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Per-trial durations",
            "",
        ]
    )
    for trial in summary["trials"]:
        lines.append(f"### Trial {trial['trial']:02d}")
        lines.append("")
        for scenario in trial["scenarios"]:
            lines.append(f"- `{scenario['name']}`: {scenario['duration_seconds']:.2f}s")
        lines.append("")

    write_text(study_dir / "summary.md", "\n".join(lines) + "\n")


def ensure_kind_cluster(environment: EnvironmentProfile, recreate=False):
    clusters = run(["kind", "get", "clusters"]).stdout.splitlines()
    exists = environment.cluster_name in clusters
    if exists and recreate:
        run(["kind", "delete", "cluster", "--name", environment.cluster_name])
        exists = False
    if not exists:
        run(
            [
                "kind",
                "create",
                "cluster",
                "--name",
                environment.cluster_name,
                "--config",
                str(environment.config_path),
                "--wait",
                "180s",
            ]
        )


def run_single_study(operator_key: str, environment_key: str, trials: int, results_root: Path, ensure_cluster_flag: bool, recreate_cluster: bool):
    environment = ENVIRONMENTS[environment_key]
    if ensure_cluster_flag or recreate_cluster:
        ensure_kind_cluster(environment, recreate=recreate_cluster)

    study_dir = results_root / operator_key / environment_key / f"study-{timestamp_slug()}"
    study_dir.mkdir(parents=True, exist_ok=True)

    client = KubectlClient(environment.context_name)
    benchmark = OPERATORS[operator_key](study_dir, client)
    summary = {
        "started_at": now_iso(),
        "study_dir": str(study_dir),
        "cluster_context": environment.context_name,
        "environment": environment.key,
        "environment_display_name": environment.display_name,
        "environment_node_count": environment.node_count,
        "namespace": benchmark.namespace,
        "operator_namespace": benchmark.operator_namespace,
        "operator": benchmark.operator_display_name,
        "operator_key": operator_key,
        "trials_requested": trials,
        "scenario_order": SCENARIO_ORDER,
        "trials": [],
    }

    try:
        benchmark.ensure_namespace()
        benchmark.install_operator()
        for trial_number in range(1, trials + 1):
            summary["trials"].append(benchmark.run_trial(trial_number))
        summary["aggregates"] = build_aggregates(summary["trials"])
        summary["completed_at"] = now_iso()
        summary["success"] = all(trial.get("success") for trial in summary["trials"])
    except Exception as exc:  # noqa: BLE001
        summary["completed_at"] = now_iso()
        summary["success"] = False
        summary["error"] = str(exc)
        if "aggregates" not in summary:
            summary["aggregates"] = build_aggregates(summary["trials"])
        raise
    finally:
        write_json(study_dir / "study_summary.json", summary)
        write_json(results_root / operator_key / environment_key / "latest_study_summary.json", summary)
        write_json(results_root / "latest_study_summary.json", summary)
        write_csv_summary(study_dir, summary["aggregates"])
        write_markdown_summary(study_dir, summary)

    return summary


def write_matrix_summary(results_root: Path, matrix_summary):
    write_json(results_root / "latest_matrix_summary.json", matrix_summary)


def parse_list_arg(raw_value, known_keys):
    if raw_value == "all":
        return list(known_keys)
    values = [item.strip() for item in raw_value.split(",") if item.strip()]
    unknown = [item for item in values if item not in known_keys]
    if unknown:
        raise ValueError(f"Unknown values: {', '.join(unknown)}")
    return values


def build_parser():
    parser = argparse.ArgumentParser(description="Run repeated multi-operator recovery benchmark studies.")
    parser.add_argument("--trials", type=int, default=3, help="Number of complete benchmark trials to execute per operator/environment combination.")
    parser.add_argument(
        "--results-root",
        default=str(DEFAULT_RESULTS_ROOT),
        help="Directory under which study outputs will be written.",
    )
    parser.add_argument(
        "--operators",
        default="rabbitmq",
        help=f"Comma-separated operator list or 'all'. Available: {', '.join(OPERATORS)}.",
    )
    parser.add_argument(
        "--environments",
        default="single-node",
        help=f"Comma-separated environment list or 'all'. Available: {', '.join(ENVIRONMENTS)}.",
    )
    parser.add_argument(
        "--ensure-cluster",
        action="store_true",
        help="Create the requested kind cluster profiles if they do not already exist.",
    )
    parser.add_argument(
        "--recreate-cluster",
        action="store_true",
        help="Delete and recreate the requested kind cluster profiles before running the study.",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    operator_keys = parse_list_arg(args.operators, OPERATORS.keys())
    environment_keys = parse_list_arg(args.environments, ENVIRONMENTS.keys())
    results_root = Path(args.results_root).resolve()
    matrix_summary = {
        "started_at": now_iso(),
        "results_root": str(results_root),
        "operators_requested": operator_keys,
        "environments_requested": environment_keys,
        "studies": [],
    }

    try:
        for environment_key in environment_keys:
            for operator_key in operator_keys:
                summary = run_single_study(
                    operator_key=operator_key,
                    environment_key=environment_key,
                    trials=args.trials,
                    results_root=results_root,
                    ensure_cluster_flag=args.ensure_cluster,
                    recreate_cluster=args.recreate_cluster,
                )
                matrix_summary["studies"].append(
                    {
                        "operator": summary["operator"],
                        "operator_key": summary["operator_key"],
                        "environment": summary["environment"],
                        "environment_display_name": summary["environment_display_name"],
                        "study_dir": summary["study_dir"],
                        "success": summary["success"],
                        "aggregates": summary["aggregates"],
                    }
                )
        matrix_summary["completed_at"] = now_iso()
        matrix_summary["success"] = all(study["success"] for study in matrix_summary["studies"])
    except Exception as exc:  # noqa: BLE001
        matrix_summary["completed_at"] = now_iso()
        matrix_summary["success"] = False
        matrix_summary["error"] = str(exc)
        write_matrix_summary(results_root, matrix_summary)
        raise

    write_matrix_summary(results_root, matrix_summary)
    print(json.dumps(matrix_summary, indent=2))


def legacy_main(argv=None):
    forwarded_args = list(argv) if argv is not None else sys.argv[1:]
    main(["--operators", "rabbitmq", "--environments", "single-node", *forwarded_args])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        sys.exit(1)
