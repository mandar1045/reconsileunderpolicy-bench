# CloudNativePG Benchmark Study

- Study directory: `/home/mandar12/Desktop/reconcileunderpolicy-bench/benchmark/reconcileunderpolicy/results/cloudnative-pg/multi-node/study-20260426-174248`
- Environment: `Multi-node kind`
- Cluster context: `kind-reconcile-under-policy-multi-node`
- Trials completed: `3`
- Overall success: `True`

## Scenario statistics

| Scenario | Success | Mean (s) | Median (s) | Min (s) | Max (s) | Stddev (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `baseline_create` | `3/3` | 114.38 | 35.93 | 35.68 | 271.54 | 111.13 |
| `restart_during_scale` | `3/3` | 102.06 | 31.50 | 29.16 | 245.51 | 101.44 |
| `quota_blocked_scale` | `3/3` | 54.71 | 54.13 | 53.85 | 56.15 | 1.02 |
| `delete_and_recreate` | `3/3` | 32.94 | 33.58 | 31.63 | 33.60 | 0.92 |

## Per-trial durations

### Trial 01

- `baseline_create`: 271.54s
- `restart_during_scale`: 245.51s
- `quota_blocked_scale`: 56.15s
- `delete_and_recreate`: 33.58s

### Trial 02

- `baseline_create`: 35.68s
- `restart_during_scale`: 31.50s
- `quota_blocked_scale`: 54.13s
- `delete_and_recreate`: 31.63s

### Trial 03

- `baseline_create`: 35.93s
- `restart_during_scale`: 29.16s
- `quota_blocked_scale`: 53.85s
- `delete_and_recreate`: 33.60s

