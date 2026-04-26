# ReconcileUnderPolicy Bench

Standalone benchmark repository for policy-constrained recovery experiments on
stateful Kubernetes operators.

## Repository layout

- `benchmark/reconcileunderpolicy/`: benchmark harness, study outputs, and run instructions
- `paper/`: LaTeX paper draft, bibliography, and compiled PDF
- `vendor/cluster-operator-main/`: locally vendored RabbitMQ Cluster Operator source tree

## Current status

The repository contains:

- a runnable multi-operator benchmark for the RabbitMQ Cluster Operator and CloudNativePG
- repeated-trial recovery scenarios focused on controller interruption, policy blocking, and delete/recreate behavior across single-node and multi-node `kind` profiles
- paper-ready study summaries in JSON, CSV, and Markdown
- a LaTeX paper draft that can be updated from the collected study outputs
