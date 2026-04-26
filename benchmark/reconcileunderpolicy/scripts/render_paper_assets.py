#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULTS_ROOT = ROOT / "benchmark" / "reconcileunderpolicy" / "results"
DEFAULT_OUTPUT_DIR = ROOT / "paper" / "generated"

OPERATOR_ORDER = ["rabbitmq", "cloudnative-pg"]
ENVIRONMENT_ORDER = ["single-node", "multi-node"]
SCENARIO_ORDER = [
    "baseline_create",
    "restart_during_scale",
    "quota_blocked_scale",
    "delete_and_recreate",
]

OPERATOR_LABELS = {
    "rabbitmq": "RabbitMQ",
    "cloudnative-pg": "CloudNativePG",
}

ENVIRONMENT_LABELS = {
    "single-node": "Single-node",
    "multi-node": "Multi-node",
}

SCENARIO_LABELS = {
    "baseline_create": "Baseline create",
    "restart_during_scale": "Restart during scale",
    "quota_blocked_scale": "Quota-blocked scale",
    "delete_and_recreate": "Delete and recreate",
}


def load_summary(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def parse_list_arg(raw_value, known_values):
    if raw_value == "all":
        return list(known_values)
    values = [item.strip() for item in raw_value.split(",") if item.strip()]
    unknown = [item for item in values if item not in known_values]
    if unknown:
        raise SystemExit(f"Unknown values: {', '.join(unknown)}")
    return values


def discover_latest_summary_paths(results_root: Path, operators, environments):
    paths = []
    for operator in operators:
        for environment in environments:
            summary_path = results_root / operator / environment / "latest_study_summary.json"
            if summary_path.exists():
                paths.append(summary_path)
    if not paths:
        raise SystemExit("No latest_study_summary.json files found for the requested matrix.")
    return paths


def sort_studies(studies):
    operator_rank = {name: index for index, name in enumerate(OPERATOR_ORDER)}
    environment_rank = {name: index for index, name in enumerate(ENVIRONMENT_ORDER)}
    return sorted(
        studies,
        key=lambda study: (
            operator_rank.get(study["operator_key"], 999),
            environment_rank.get(study["environment"], 999),
        ),
    )


def aggregate_by_name(study):
    return {item["scenario"]: item for item in study["aggregates"]}


def trial_durations_by_name(study):
    trial_map = {}
    for aggregate in study["aggregates"]:
        trial_map[aggregate["scenario"]] = aggregate["durations_seconds"]
    return trial_map


def format_median_table(studies):
    lines = []
    for study in studies:
        aggregates = aggregate_by_name(study)
        row = [
            OPERATOR_LABELS.get(study["operator_key"], study["operator"]),
            ENVIRONMENT_LABELS.get(study["environment"], study["environment_display_name"]),
        ]
        for scenario in SCENARIO_ORDER:
            row.append(f"{aggregates[scenario]['median_seconds']:.2f}")
        lines.append(" & ".join(row) + " \\tabularnewline")
    return "\n".join(lines) + "\n"


def format_detailed_table(studies):
    lines = []
    for study in studies:
        aggregates = aggregate_by_name(study)
        for scenario in SCENARIO_ORDER:
            item = aggregates[scenario]
            lines.append(
                " & ".join(
                    [
                        OPERATOR_LABELS.get(study["operator_key"], study["operator"]),
                        ENVIRONMENT_LABELS.get(study["environment"], study["environment_display_name"]),
                        SCENARIO_LABELS.get(scenario, scenario),
                        f"{item['successful_trials']}/{item['total_trials']}",
                        f"{item['mean_seconds']:.2f}",
                        f"{item['stdev_seconds']:.2f}",
                        f"{item['min_seconds']:.2f}--{item['max_seconds']:.2f}",
                    ]
                )
                + " \\tabularnewline"
            )
    return "\n".join(lines) + "\n"


def build_matrix_cache(studies):
    cache = []
    for study in studies:
        entry = {
            "operator": study["operator"],
            "operator_key": study["operator_key"],
            "environment": study["environment"],
            "environment_display_name": study["environment_display_name"],
            "trial_count": len(study["trials"]),
            "aggregates": [],
        }
        for item in study["aggregates"]:
            entry["aggregates"].append(
                {
                    "scenario": item["scenario"],
                    "success": f"{item['successful_trials']}/{item['total_trials']}",
                    "mean_seconds": item["mean_seconds"],
                    "median_seconds": item["median_seconds"],
                    "stdev_seconds": item["stdev_seconds"],
                    "min_seconds": item["min_seconds"],
                    "max_seconds": item["max_seconds"],
                }
            )
        cache.append(entry)
    return cache


def format_macro_file(studies):
    total_trials = sum(len(study["trials"]) for study in studies)
    total_scenarios = sum(len(trial["scenarios"]) for study in studies for trial in study["trials"])
    successful_scenarios = sum(
        1
        for study in studies
        for trial in study["trials"]
        for scenario in trial["scenarios"]
        if scenario.get("success")
    )
    lines = [
        f"\\newcommand{{\\RUPStudyCount}}{{{len(studies)}}}",
        f"\\newcommand{{\\RUPOperatorCount}}{{{len({study['operator_key'] for study in studies})}}}",
        f"\\newcommand{{\\RUPEnvironmentCount}}{{{len({study['environment'] for study in studies})}}}",
        f"\\newcommand{{\\RUPTrialCount}}{{{len(studies[0]['trials']) if studies else 0}}}",
        f"\\newcommand{{\\RUPTotalTrials}}{{{total_trials}}}",
        f"\\newcommand{{\\RUPScenarioExecutions}}{{{total_scenarios}}}",
        f"\\newcommand{{\\RUPSuccessfulScenarioExecutions}}{{{successful_scenarios}}}",
        f"\\newcommand{{\\RUPStudyStarted}}{{{min(study['started_at'] for study in studies)}}}",
        f"\\newcommand{{\\RUPStudyCompleted}}{{{max(study['completed_at'] for study in studies)}}}",
    ]
    return "\n".join(lines) + "\n"


def parse_args():
    parser = argparse.ArgumentParser(description="Render LaTeX include files from benchmark study summaries.")
    parser.add_argument(
        "--summary",
        action="append",
        default=[],
        help="Path to a study_summary.json file. May be provided multiple times. If omitted, latest summaries are discovered automatically.",
    )
    parser.add_argument(
        "--results-root",
        default=str(DEFAULT_RESULTS_ROOT),
        help="Results root used for automatic matrix discovery.",
    )
    parser.add_argument(
        "--operators",
        default="all",
        help="Comma-separated operator keys to include, or 'all'.",
    )
    parser.add_argument(
        "--environments",
        default="all",
        help="Comma-separated environment keys to include, or 'all'.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for generated LaTeX assets.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    results_root = Path(args.results_root)
    operators = parse_list_arg(args.operators, OPERATOR_ORDER)
    environments = parse_list_arg(args.environments, ENVIRONMENT_ORDER)

    summary_paths = [Path(path) for path in args.summary]
    if not summary_paths:
        summary_paths = discover_latest_summary_paths(results_root, operators, environments)

    studies = sort_studies([load_summary(path) for path in summary_paths])
    output_dir = Path(args.output_dir)

    write_text(output_dir / "median_results_rows.tex", format_median_table(studies))
    write_text(output_dir / "matrix_results_rows.tex", format_detailed_table(studies))
    write_text(output_dir / "study_macros.tex", format_macro_file(studies))
    write_json(output_dir / "matrix_summary.json", build_matrix_cache(studies))


if __name__ == "__main__":
    main()
