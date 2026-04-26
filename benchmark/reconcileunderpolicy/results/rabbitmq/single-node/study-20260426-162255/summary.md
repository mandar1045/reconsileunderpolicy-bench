# RabbitMQ Cluster Operator Benchmark Study

- Study directory: `/home/mandar12/Desktop/reconcileunderpolicy-bench/benchmark/reconcileunderpolicy/results/rabbitmq/single-node/study-20260426-162255`
- Environment: `Single-node kind`
- Cluster context: `kind-reconcile-under-policy-single-node`
- Trials completed: `1`
- Overall success: `False`

## Scenario statistics

| Scenario | Success | Mean (s) | Median (s) | Min (s) | Max (s) | Stddev (s) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `baseline_create` | `1/1` | 174.63 | 174.63 | 174.63 | 174.63 | 0.00 |
| `restart_during_scale` | `1/1` | 78.85 | 78.85 | 78.85 | 78.85 | 0.00 |
| `quota_blocked_scale` | `1/1` | 79.62 | 79.62 | 79.62 | 79.62 | 0.00 |
| `delete_and_recreate` | `1/1` | 61.88 | 61.88 | 61.88 | 61.88 | 0.00 |

## Per-trial durations

### Trial 01

- `baseline_create`: 174.63s
- `restart_during_scale`: 78.85s
- `quota_blocked_scale`: 79.62s
- `delete_and_recreate`: 61.88s

