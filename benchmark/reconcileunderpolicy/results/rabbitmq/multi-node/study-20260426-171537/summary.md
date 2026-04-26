# RabbitMQ Cluster Operator Benchmark Study

- Study directory: `/home/mandar12/Desktop/reconcileunderpolicy-bench/benchmark/reconcileunderpolicy/results/rabbitmq/multi-node/study-20260426-171537`
- Environment: `Multi-node kind`
- Cluster context: `kind-reconcile-under-policy-multi-node`
- Trials completed: `3`
- Overall success: `True`

## Scenario statistics

| Scenario | Success | Mean (s) | Median (s) | Min (s) | Max (s) | Stddev (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `baseline_create` | `3/3` | 192.33 | 189.58 | 189.49 | 197.93 | 3.96 |
| `restart_during_scale` | `3/3` | 149.33 | 88.74 | 88.58 | 270.66 | 85.80 |
| `quota_blocked_scale` | `3/3` | 93.53 | 92.97 | 92.85 | 94.76 | 0.87 |
| `delete_and_recreate` | `3/3` | 72.82 | 72.81 | 72.67 | 72.98 | 0.13 |

## Per-trial durations

### Trial 01

- `baseline_create`: 197.93s
- `restart_during_scale`: 270.66s
- `quota_blocked_scale`: 92.85s
- `delete_and_recreate`: 72.98s

### Trial 02

- `baseline_create`: 189.58s
- `restart_during_scale`: 88.58s
- `quota_blocked_scale`: 94.76s
- `delete_and_recreate`: 72.67s

### Trial 03

- `baseline_create`: 189.49s
- `restart_during_scale`: 88.74s
- `quota_blocked_scale`: 92.97s
- `delete_and_recreate`: 72.81s

