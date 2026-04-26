# RabbitMQ Benchmark Study

- Study directory: `/home/mandar12/Desktop/reconcileunderpolicy-bench/benchmark/reconcileunderpolicy/results/study-20260426-153650`
- Cluster context: `kind-reconcile-under-policy`
- Trials completed: `3`
- Overall success: `True`

## Scenario statistics

| Scenario | Success | Mean (s) | Median (s) | Min (s) | Max (s) | Stddev (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `baseline_create` | `3/3` | 172.08 | 171.76 | 171.70 | 172.79 | 0.50 |
| `restart_during_scale` | `3/3` | 78.32 | 78.82 | 77.04 | 79.10 | 0.91 |
| `quota_blocked_scale` | `3/3` | 79.54 | 79.56 | 79.51 | 79.56 | 0.02 |
| `delete_and_recreate` | `3/3` | 60.81 | 61.38 | 59.44 | 61.62 | 0.98 |

## Per-trial durations

### Trial 01

- `baseline_create`: 171.70s
- `restart_during_scale`: 78.82s
- `quota_blocked_scale`: 79.56s
- `delete_and_recreate`: 61.38s

### Trial 02

- `baseline_create`: 171.76s
- `restart_during_scale`: 77.04s
- `quota_blocked_scale`: 79.51s
- `delete_and_recreate`: 61.62s

### Trial 03

- `baseline_create`: 172.79s
- `restart_during_scale`: 79.10s
- `quota_blocked_scale`: 79.56s
- `delete_and_recreate`: 59.44s

