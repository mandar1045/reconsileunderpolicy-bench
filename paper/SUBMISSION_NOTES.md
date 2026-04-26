# Submission Notes

As of `2026-04-26`, this repository contains:

- a runnable multi-operator benchmark artifact
- completed results for `RabbitMQ` and `CloudNativePG`
- completed results for both `single-node` and `multi-node` `kind`
- a comparative paper draft regenerated from the finished benchmark matrix

The current manuscript is now suitable for a scoped research-paper submission
in the benchmark, reproducibility, artifact-evaluation, or experience-report
space. It is no longer only a RabbitMQ pilot.

## What the paper now claims

- `2` operators
- `2` environments
- `3` full trials per operator/environment pair
- `4` scenarios per trial
- `48` successful scenario executions total

The paper’s comparative claims are aligned with the benchmark results that are
already present in the repository.

The manuscript source is also prepared for ACM packaging: if `acmart.cls` is
installed on the build machine, `paper/reconcileunderpolicy_study.tex` will
automatically compile in ACM `sigconf` mode; otherwise it falls back to the
local article-mode build used in this repository.

## Best current fit

The strongest near-term targets are venues or tracks that value:

- reproducible systems artifacts
- empirical benchmark papers
- experience reports on controller or operator behavior
- workshop-scale systems evaluations

This is now a stronger submission than a narrow pilot, but it is still best
framed as a comparative benchmark study rather than as a broad ecosystem-wide
characterization of Kubernetes operators.

## Remaining work before a real submission

- move the manuscript into the exact venue template
- prepare an anonymized version if the chosen venue is double-blind
- do a final page-limit and wording pass for the specific call for papers
- publish or archive the artifact in whatever form the venue requires
- optionally extend the benchmark further if a main-track systems venue expects
  a larger operator sample

## Honest positioning

What is now strong:

- the artifact is executable
- the study is comparative rather than single-operator
- the manuscript reports real repeated-trial data
- the benchmark surfaces meaningful operator- and environment-level differences

What is still bounded:

- only two operators are covered
- the environments are local `kind` deployments
- the policy suite is still small
- workload semantic correctness is not measured beyond healthy reconciliation
