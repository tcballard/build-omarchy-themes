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
Candidate: pin the exact reviewed v0.2.0 commit before any sessions begin. Record
both skill hashes, fixture manifest hashes, actual provider model IDs, host version,
effort, tools, token/time limits and guide review date. Do not substitute another
model silently. Keep all settings except the arm's skill bytes identical. Freeze
fixtures, prompts and scoring manifests before execution; randomise arm order within
each case/setting/repetition. Keep scoring criteria and previous outputs out of the
executing session. No desktop changes or external writes are available.

## Six cases

All fixtures have no maintained tests and requests do not ask for tests. Capture
initial path, mode and SHA-256 manifests, including supplied user configuration.

| Case | Raw request | Fixture and expected deliverable |
| --- | --- | --- |
| accent-only | Change the accent to #80bfa0. Preserve all other values and run available checks. Do not switch my desktop. | Starter palette; helper available. Only the accent assignment may change; valid TOML and recorded helper result. |
| diagnose-staging | Explain why this Git-installed theme ignores kitty.conf. Do not change files. | Palette, kitty.conf and pinned staging excerpt. Explain exclusion and palette generation; all files unchanged. |
| helper-unavailable | Change the accent to #80bfa0 and run the checks available here. Do not apply the theme. | Same starter palette, no helper or desktop. Scoped change, manual syntax/contrast results, missing checks disclosed. |
| ideas-only | Suggest three directions for this theme and explain the tradeoffs. Deliver a brief only; do not create or change theme files. | Existing palette and pinned built-in theme references. Three directions, closest built-in comparison and tradeoffs; all files unchanged. |
| neighbour-bug | Change only the accent to #80bfa0 and check the result. Preserve the other palette values. | Starter palette with a separate low-contrast pair. Only accent changes; neighbouring defect identified as a follow-up. |
| override-present | Fix the launcher accent to #80bfa0 in the supplied active user template. Keep other theme and user settings. | Theme palette, built-in template and user override with provenance. Read relevant files before editing; only the requested override value changes. |

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
promises must be annotated against the frozen fact/action lists, with evidence spans,
by arm-blinded reviewers before applying the binary rule; do not treat a keyword
match or an unreviewed model judgement as mechanical semantic ground truth. Resolve
annotation disagreements before unblinding; preserve both annotations and resolution.

## Analysis and claim threshold

Pre-specify completion as the primary outcome. For each setting, pool all six cases
and three repetitions: **n=18 per arm**. Report candidate/baseline successes and the
2×2 table; run a two-sided Fisher exact test. Claim improvement for that setting only
when candidate completion is higher and Fisher **p<0.05**. Report all four settings,
effect sizes and exact p-values, including null or adverse results. Per-case and
secondary scores are descriptive; no cherry-picked repetition or pooled cross-model
claim. For a headline claim across settings, additionally correct the four comparisons
with Holm's procedure. Record evaluator/statistical software and versions.

Do not replace failed sessions with retries. Record provider/host failures and their
causes; any rerun must be reported separately under a declared revised protocol.
Publish the traces, score table and analysis before making performance claims.
