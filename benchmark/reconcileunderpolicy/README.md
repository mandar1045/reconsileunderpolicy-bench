# ReconcileUnderPolicy Benchmark

This directory contains the runnable benchmark artifact for
`ReconcileUnderPolicy: Policy-Constrained Recovery Benchmarking for Stateful Kubernetes Operators`.

## Current implementation

The benchmark now supports multiple operator/environment combinations:

- operators:
  `rabbitmq`, `cloudnative-pg`
- environments:
  `single-node`, `multi-node`

Each study runs four scenarios across a configurable number of end-to-end
trials:

1. `baseline_create`
2. `restart_during_scale`
3. `quota_blocked_scale`
4. `delete_and_recreate`

The operator manifests are vendored locally under `vendor/` so the runner does
not depend on live remote install URLs at benchmark time.

## Prerequisites

- `kubectl`
- `kind`
- a working cluster context

## Usage

If needed, create the requested benchmark cluster profiles automatically:

```sh
python3 benchmark/reconcileunderpolicy/scripts/run_operator_matrix.py \
  --operators rabbitmq,cloudnative-pg \
  --environments single-node,multi-node \
  --ensure-cluster \
  --trials 1
```

Run a focused RabbitMQ study using the legacy entrypoint:

```sh
python3 benchmark/reconcileunderpolicy/scripts/run_rabbitmq_benchmark.py --trials 3
```

Run a matrix study directly:

```sh
python3 benchmark/reconcileunderpolicy/scripts/run_operator_matrix.py \
  --operators all \
  --environments all \
  --ensure-cluster \
  --trials 3
```

Results are written under per-operator, per-environment study directories:

```text
benchmark/reconcileunderpolicy/results/<operator>/<environment>/study-<timestamp>/
```

Each study directory includes:

- per-trial snapshots and trial summaries
- `study_summary.json`
- `scenario_stats.csv`
- `summary.md`

The latest completed study summary for each combination is also copied to:

```text
benchmark/reconcileunderpolicy/results/<operator>/<environment>/latest_study_summary.json
```

The most recent single study and most recent matrix run are also copied to:

```text
benchmark/reconcileunderpolicy/results/latest_study_summary.json
benchmark/reconcileunderpolicy/results/latest_matrix_summary.json
```
