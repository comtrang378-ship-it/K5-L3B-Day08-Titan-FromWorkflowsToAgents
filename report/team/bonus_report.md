# Bonus report: B1

- **Topic + source:** B1 — parallel investigators and critical path. Google Research (2026), *Towards a Science of Scaling Agent Systems*, slides 15, 24, 33, 41; as referenced in `docs/bonus_topics.md`.
- **CLAIM:** parallel agents help only when the work can actually be decomposed; the source reports substantial regressions for sequential tasks in its evaluated settings.
- **BOUNDARY:** the source result is not a prediction for every workflow. This experiment uses 14 public LogiX claims, a local SQLite world, seeded MockLLM, and a hand-authored latency model; it does not measure production or wall-clock latency.
- **HYPOTHESIS:** parallelizing the independent order, policy, and refund-history reads will preserve output/ledger and cost, with a modest simulated critical-path speedup because quoting depends on order and the host remains the sole writer.
- **Fixed / changed:** same public claims, seeds `11,22,33,44,55`, MockLLM, tools, policy date, pricing, fresh SQLite per trial, and `lab8.metrics.trial_pass` evaluator. Only investigator scheduling changes: sequential versus `ThreadPoolExecutor`.
- **Reproduction (run from `src/`):** `python -m bonus.run_b1 --extra-shape orchestrator_parallel=bonus.orchestrator_parallel:run_claim --seeds 11,22,33,44,55 --out reports/bonus_b1.json`
- **Report and example run IDs:** `src/reports/bonus_b1.json`; `R-orchestrator-C-001-s11` and `R-orchestrator_parallel-C-001-s11`.

## Kết quả

The report contains 70 paired trials per shape. Latency values below are simulated DAG critical paths, not measured execution times. Cost is simulated VND.

| Shape | Pass rate | Pass^5 | Seed variance | Cost/success | Critical path mean / p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Orchestrator tuần tự | 1.000 | 1.000 | 0.000000 | 56.46 | 258.429 / 290 ms |
| Orchestrator song song | 1.000 | 1.000 | 0.000000 | 56.46 | 203.829 / 235 ms |

Paired output and ledger mismatches: **0 / 70** each. Both shapes had zero public trials with invalid traces, privacy leaks, approval bypasses, duplicate refunds, unexpected ledger rows, result/ledger mismatches, or missing `policy_denied` audit.

Mean-path speedup is **1.2679×** (the mean of per-trial speedups is 1.2515×); the three-worker Amdahl estimate is **1.2704×**. Model/tool call counts and cost are unchanged.

The flow's parallel section is limited to `lookup_order`, `lookup_policy`, and `lookup_refund_history`. The quote depends on the order result, and `issue_refund` remains a single host-controlled write after investigators join. The modelled DAG therefore keeps the quote and host gate on the critical path.

## Kết luận

The public simulation supports the hypothesis narrowly: independent reads reduce the modelled mean critical path by about 21%, while pass rate, ledger, and cost remain unchanged. The Amdahl estimate is close to the DAG result, but Amdahl's simple three-worker approximation does not fully represent the quote-to-order dependency. The conclusion could reverse if real worker/connection overhead or database contention exceeded the saved read latency, or if the reads were not independent.

## Giới hạn và bonus gate

MockLLM makes one deterministic orchestration call; all latency is simulated from `src/bonus/latency.yaml` with jitter keyed by seed/tool/call index. No `time.sleep` or wall-clock speed claim is used. The result covers only the public 14-claim corpus.

The bonus eligibility gate is **not fully verified**: the hidden 40 × 5 pass-rate threshold for the selected main shape is unavailable in this workspace. Public evidence does not establish hidden pass rate ≥ 0.80 or earn the bonus points by itself.
