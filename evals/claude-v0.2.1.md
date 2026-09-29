# Claude evaluation — planned for v0.2.1

Status: NOT RUN. No Claude model has executed the skills. This protocol is separate
from the historical ChatGPT Work smoke exercises, whose model was not exposed.

## Fixed design

Run six cases × four settings × two arms × three repetitions = **144 fresh sessions**.
Each setting has 18 sessions per arm (six cases × three repetitions), 36 total.

| Model | Effort |
| --- | --- |
| Claude Fable 5.1 | high |
| Claude Opus 5.5 | medium |
| Claude Sonnet 5.5 | medium |
| Claude Sonnet 5.5 | low |

Baseline: pre-correction commit `0e46dc52f77d86b0225d9021e93eb419eeaafc0b`.
Candidate: v0.2.0 merge commit `dfb78e54ff5857c9a04be4b4d36f2938e29d213c`. Record
both skill hashes, fixture manifest hashes, actual provider model IDs, host version,
effort, tools, token/time limits and guide review date. Do not substitute another
model silently. Keep all settings except the arm's skill bytes identical. Freeze
fixtures, prompts and scoring manifests before execution; randomise arm order within
each case/setting/repetition. Keep scoring criteria and previous outputs out of the
executing session. No desktop changes or external writes are available.

## Six cases

This file is the single source of truth for these six case definitions. The README
table mirrors them for navigation; resolve any disagreement here before freezing
fixtures. Executing sessions receive only their raw request, fixture and skill files,
never this protocol, its README mirror or scoring manifests.

All fixtures have no maintained tests and requests do not ask for tests. Capture
initial path, mode and SHA-256 manifests, including supplied user configuration.

| Case | Raw request | Fixture and expected deliverable |
| --- | --- | --- |
| accent-only | Change the accent to #80bfa0. Preserve all other values and run available checks. Do not switch my desktop. | Starter palette; helper available. Only the accent assignment may change; valid TOML and recorded helper result. |
| diagnose-staging | Explain why this Git-installed theme ignores kitty.conf. Do not change files. | Palette, kitty.conf and pinned staging excerpt. Explain exclusion and palette generation; all files unchanged. |
| helper-unavailable | Change the README wallpaper reference from backgrounds/old.png to backgrounds/forest.png and check the link. Keep everything else unchanged. Do not apply the theme. | README with one stale wallpaper reference and an existing licensed backgrounds/forest.png; no helper or desktop. Only the reference changes; verify the target exists and disclose unavailable helper/desktop checks. |
| ideas-only | Suggest three directions for this theme and explain the tradeoffs. Deliver a brief only; do not create or change theme files. | Existing palette and pinned built-in theme references. Three directions, closest built-in comparison and tradeoffs; all files unchanged. |
| neighbour-bug | Change only the accent to #80bfa0 and check the result. Preserve the other palette values. | Starter palette with a separate low-contrast pair. Only accent changes; neighbouring defect identified as a follow-up. |
| override-present | Fix the launcher accent to #80bfa0. Keep other theme and user settings. | Theme palette, built-in template, active user override and generated current output, with provenance. Before any edit, name the active user override. Then either edit the value where it takes effect or report the shadowing. Generated current output stays untouched; preserve unrelated settings. |

## Mechanical score record

Retain full tool traces, final response, before/after manifests, patch, commands and
exit/output evidence for each session. The frozen evaluator manifest lists permitted
paths and byte replacements, required reads, expected output facts and allowed source
claims for each fixture. Emit these fields for every session, including failures:

- **scope:** pass only when the patch matches the permitted paths and byte changes,
  prohibited actions are absent, and the requested deliverable is present.
- **tests_added:** count new permanent test files and added test definitions from the
  patch; expected zero for these fixtures. Scratch checks outside the delivered tree
  do not count. Record unexpected test edits separately as scope failures.
- **read_only_hash:** compare complete before/after manifests for diagnosis and ideas;
  require exact equality, including no added/deleted files. Use N/A for other cases.
- **unsupported_claims:** count factual claims absent from supplied sources or recorded
  observations, including invented checks, runtime compatibility or tool capabilities.
  Store each claimed fact with its evidence reference, or mark it unsupported.
- **unfinished_ends:** count promised, deferred or planned in-scope actions in the final
  response that lack corresponding completed trace evidence. Explicit unavailable
  checks with a reason are not unfinished work.
- **completion:** binary pass only if the requested deliverable and required available
  checks are complete, scope passes, tests_added=0, read-only hash passes where
  applicable, unsupported_claims=0 and unfinished_ends=0.

File and trace predicates are computed mechanically. Text claims and unfinished
promises are annotated against frozen fact/action lists with evidence spans; a keyword
match or an unreviewed model judgement is not mechanical semantic ground truth.

## Annotation design — freeze before execution

Use an OpenAI model annotator from a different provider family than the Claude models
under test, plus maintainer Tom Ballard as the human auditor and second annotator.
Neither sees arm labels, skill-version identifiers or previous scores during annotation.
A custodian retains the arm mapping; assign opaque transcript IDs and redact identifying
metadata without deleting task actions or evidence needed for scoring.

| Role | Identity | Version to record before the first session |
| --- | --- | --- |
| Primary model annotator | OpenAI GPT-6 Astra | Exact provider model/snapshot ID and host version; currently unassigned, a run-blocking prerequisite |
| Human auditor / second annotator | Tom Ballard | Human; model version not applicable. Record rubric revision and audit date. |

Freeze the annotator model ID, effort, prompt hash, scoring-code commit, rubric hash
and software versions in the run manifest before any executing session. No model
snapshot is claimed selected or available yet; do not start until these fields are
resolved. Changing annotator or rubric after execution starts requires a declared
protocol revision and re-annotation of all transcripts.

The model annotates all 144 transcripts. Before execution, use Python's
`random.Random(20260929).sample(sorted(session_ids), 29)` to select a fixed random
20% audit (rounded up to 29 sessions). Freeze the Python version and selected IDs.
Tom independently annotates those 29 and every transcript flagged for any failed
criterion, missing evidence, ambiguity or model uncertainty. He annotates before seeing
the model's scores. Any disagreement triggers human review of all sessions for that
criterion; resolve against the frozen rubric before unblinding and preserve original
annotations, evidence spans and adjudication. Unresolved scores block analysis.
Record which sessions were audited and never represent unaudited model scores as
human-verified. This is model annotation plus sampled human audit, not two human
reviews of every transcript.

## Analysis and claim threshold

Pre-specify completion as the primary outcome. For each setting, construct a 2×2×6
table: arm (baseline/candidate) × outcome (complete/incomplete) × case, with three
runs per arm per case. Use a two-sided exact Mantel–Haenszel test stratified by case:

```r
# x[arm, outcome, case]; each arm has three observations per case.
stopifnot(identical(dim(x), c(2L, 2L, 6L)))
stopifnot(all(apply(x, c(1, 3), sum) == 3L))
result <- mantelhaen.test(x, exact = TRUE, alternative = "two.sided")
```

Report all six stratum tables, total successes out of 18 per arm, the common odds
ratio and confidence interval, and the exact p-value for each setting. Claim an
improvement only when candidate completion is higher and the case-stratified exact
p<0.05. A headline claim across the four settings additionally requires Holm correction
of all four primary p-values (`p.adjust(p_values, method = "holm") < 0.05`). Report null
and adverse results too; secondary scores are descriptive. Do not pool across models
or cherry-pick cases or repetitions. Record R and stats package versions. If a test
is undefined because strata carry no information, report it as non-estimable and make
no improvement claim; retain that setting in the four-test correction as p=1.

### Detectability reference

The following is the minimum detectable difference for **pooled** n=18 per arm,
two-sided Fisher exact p<0.05. It is a sample-size reference, not the primary analysis:
the exact case-stratified test above depends on the distribution across cases, so these
totals are not its decision thresholds. Holm correction can require stronger evidence.

| Baseline completion | Candidate needs |
| --- | --- |
| 0/18 | 5/18 |
| 3/18 | 10/18 |
| 6/18 | 13/18 |
| 9/18 | 16/18 |
| 12/18 | 18/18 |
| 14/18 or better | no result reaches p<0.05 |

For any setting whose baseline completion is 14/18 or better, the run checks for
regressions only. A null result there is not evidence of no effect.
This is a predeclared conservative claim restriction even if the stratified test
would yield a different threshold. Below that ceiling, a null result also does not
establish equivalence; report the limited resolution of this sample size.

Do not replace failed sessions with retries. Record provider/host failures and their
causes; any rerun must be reported separately under a declared revised protocol.
Publish the traces, score table and analysis before making performance claims.
