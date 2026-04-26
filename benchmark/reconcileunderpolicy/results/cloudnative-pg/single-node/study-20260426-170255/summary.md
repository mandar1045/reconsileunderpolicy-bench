# CloudNativePG Benchmark Study

- Study directory: `/home/mandar12/Desktop/reconcileunderpolicy-bench/benchmark/reconcileunderpolicy/results/cloudnative-pg/single-node/study-20260426-170255`
- Environment: `Single-node kind`
- Cluster context: `kind-reconcile-under-policy-single-node`
- Trials completed: `3`
- Overall success: `True`

## Scenario statistics

| Scenario | Success | Mean (s) | Median (s) | Min (s) | Max (s) | Stddev (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `baseline_create` | `3/3` | 103.39 | 38.04 | 35.37 | 236.76 | 94.31 |
| `restart_during_scale` | `3/3` | 28.78 | 27.72 | 27.53 | 31.09 | 1.64 |
| `quota_blocked_scale` | `3/3` | 52.93 | 54.27 | 50.00 | 54.51 | 2.07 |
| `delete_and_recreate` | `3/3` | 33.05 | 32.17 | 32.16 | 34.81 | 1.25 |

## Per-trial durations

### Trial 01

- `baseline_create`: 236.76s
- `restart_during_scale`: 27.72s
- `quota_blocked_scale`: 50.00s
- `delete_and_recreate`: 32.16s

### Trial 02

- `baseline_create`: 35.37s
- `restart_during_scale`: 27.53s
- `quota_blocked_scale`: 54.27s
- `delete_and_recreate`: 34.81s

### Trial 03

- `baseline_create`: 38.04s
- `restart_during_scale`: 31.09s
- `quota_blocked_scale`: 54.51s
- `delete_and_recreate`: 32.17s

