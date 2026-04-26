# RabbitMQ Cluster Operator Benchmark Study

- Study directory: `/home/mandar12/Desktop/reconcileunderpolicy-bench/benchmark/reconcileunderpolicy/results/rabbitmq/single-node/study-20260426-164100`
- Environment: `Single-node kind`
- Cluster context: `kind-reconcile-under-policy-single-node`
- Trials completed: `3`
- Overall success: `True`

## Scenario statistics

| Scenario | Success | Mean (s) | Median (s) | Min (s) | Max (s) | Stddev (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `baseline_create` | `3/3` | 175.00 | 174.93 | 174.80 | 175.27 | 0.20 |
| `restart_during_scale` | `3/3` | 77.16 | 77.61 | 75.17 | 78.71 | 1.48 |
| `quota_blocked_scale` | `3/3` | 80.23 | 79.54 | 79.37 | 81.77 | 1.09 |
| `delete_and_recreate` | `3/3` | 59.49 | 59.50 | 59.41 | 59.57 | 0.07 |

## Per-trial durations

### Trial 01

- `baseline_create`: 174.80s
- `restart_during_scale`: 78.71s
- `quota_blocked_scale`: 79.37s
- `delete_and_recreate`: 59.41s

### Trial 02

- `baseline_create`: 175.27s
- `restart_during_scale`: 77.61s
- `quota_blocked_scale`: 81.77s
- `delete_and_recreate`: 59.57s

### Trial 03

- `baseline_create`: 174.93s
- `restart_during_scale`: 75.17s
- `quota_blocked_scale`: 79.54s
- `delete_and_recreate`: 59.50s

