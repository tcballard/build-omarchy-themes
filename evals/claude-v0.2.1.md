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
effort, tools, turn/budget/time limits and guide review date. Do not substitute another
model silently. Keep all settings except the arm's skill bytes identical. Freeze
fixtures, prompts and scoring manifests before execution; randomise arm order within
each case/setting/repetition. Keep scoring criteria and previous outputs out of the
executing session. No desktop changes or external writes are available.

Install each arm's skills at /opt/evaluation/.claude/skills, with the same directory names,
so tool-call paths and arguments do not differ between arms. Verify this mechanically
in the run manifest before execution. Claude Code runs headless with --bare and
--add-dir /opt/evaluation. Record --max-turns, --max-budget-usd and wall-clock seconds
identically for both arms; exceeding a cap is a scored failure. Initial metadata is
configuration, not observed effort. The terminal summary carries returned models and
OpenTelemetry API-request model/effort/source evidence. Check main and subagent
requests; retain auxiliary requests without judging their model. Keep raw source names
and normalise repl_main_thread to main; unknown sources block verification.

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
| ideas-only | Suggest three directions for this theme and explain the tradeoffs. Deliver a brief only; do not create or change theme files. | Existing palette and pinned built-in theme references. Primary: three directions with tradeoffs; complete before/after manifest identical (read-only hash passes). Secondary: closest built-in theme comparison. |
| neighbour-bug | Change only the accent to #80bfa0 and check the result. Preserve the other palette values. | Starter palette with a separate low-contrast pair. Primary: only the accent assignment changes to #80bfa0; the low-contrast neighbour pair is untouched; requested check run or its absence disclosed. Secondary: neighbouring defect reported as a follow-up. |
| override-present | Fix the launcher accent to #80bfa0. Keep other theme and user settings. | Theme palette, built-in template, active user override and generated current output, provenance recorded in fixture manifests, outside the fixture tree. Primary: launcher accent is #80bfa0 where it takes effect, or the shadowing is reported without an ineffective edit; generated current output untouched; unrelated settings preserved. Secondary: active user override named before any edit. |

## Mechanical score record

Primary completion is fidelity to the raw request: everything it asks for and nothing
it does not, plus the evidence rule both arms share (no invented capabilities, checks
or evidence). Skill instructions never add primary requirements. Deliverable elements
that only the candidate's instructions ask for are secondary scores; they are descriptive
and never part of the primary outcome. Permitted paths are the files the requested
change needs. Any other delivered file, including tests, fails scope.

Before execution, bind every primary criterion in the frozen evaluator manifest to
its raw-request clause or the shared evidence rule. Do not use skill instructions as
additional primary requirements, including in scope, required reads, checks or reporting.
The three case-specific secondary criteria below cannot turn a primary pass into a
failure.

Trade-off: the baseline is penalised when it follows its own add-tests instruction.
That is intended. The primary outcome measures what the user receives, and that
instruction is part of what the change replaced. The built-in comparison stays
secondary because the user never asked for it.

Retain full tool traces, final response, before/after manifests, patch, commands and
exit/output evidence for each session. The frozen evaluator manifest lists permitted
paths and byte replacements, required reads, expected output facts and allowed source
claims for each fixture. Emit these fields for every session, including failures:

- **scope:** pass only when the patch matches the permitted paths and byte changes,
  prohibited actions are absent, and the requested deliverable is present.
- **tests_added:** count new permanent test files and added test definitions from the
  patch; expected zero for these fixtures. No case requests tests, so any new or edited
  permanent test in the delivered tree is a scope failure. Scratch checks outside the
  delivered tree do not count.
- **read_only_hash:** compare complete before/after manifests for diagnosis and ideas;
  require exact equality, including no added/deleted files. Use N/A for other cases.
- **unsupported_claims:** count factual claims absent from supplied sources or recorded
  observations, including invented checks, runtime compatibility or tool capabilities.
  Store each claimed fact with its evidence reference, or mark it unsupported.
- **unfinished_ends:** count promised, deferred or planned in-scope actions in the final
  response that lack corresponding completed trace evidence. Explicit unavailable
  checks with a reason are not unfinished work.
- **completion:** binary pass only if the requested deliverable and required available
  checks are complete, scope passes, read-only hash passes where applicable, and
  unsupported_claims=0, and no unfinished actions relevant to those primary criteria.
  Apply the primary-scope rule above to every gate; permanent test additions or edits
  fail scope. Secondary scores never affect primary completion.
- **secondary:** an object with the three nullable boolean fields below in every
  session's score record. In the applicable case, set the field to true when its
  criterion is observed and false otherwise. Set it to null outside its applicable
  case; exclude null values from rate denominators. Report rates per arm and setting
  using only that criterion's case
  (three sessions per arm/setting), with numerator and denominator. Do not test these
  secondary rates for significance or include them in primary completion.

| Secondary field | Applicable case | True when |
| --- | --- | --- |
| `closest_builtin_comparison` | ideas-only | The closest built-in theme is compared. |
| `neighbour_followup_reported` | neighbour-bug | The neighbouring defect is reported as a follow-up. |
| `override_named_before_edit` | override-present | The active user override is named before any edit; if no edit occurs, it is named in the diagnosis. |

File and trace predicates are computed mechanically. Text claims and unfinished
promises are annotated against frozen fact/action lists with evidence spans; a keyword
match or an unreviewed model judgement is not mechanical semantic ground truth.

## Annotation design — freeze before execution

Use an OpenAI model annotator from a different provider family than the Claude models
under test, plus maintainer Tom Ballard as the human auditor and second annotator.
Neither sees arm labels, skill-version identifiers or previous scores during annotation.
Custodian: option (b). before execution, a committed script generates opaque
session IDs and the random arm mapping, writing the mapping to a file outside the
repository without printing it. Commit only the mapping file's SHA-256; keep its
contents, random seed and any mapping-revealing execution metadata out of logs,
annotation copies and the run manifest. The runner reads the sealed mapping without
exposing it to either annotator. Open the file only after all annotations and
adjudications are frozen and hashed, then verify the committed hash before unblinding.
This relies on maintainer discipline: Tom must not inspect the mapping or unredacted
execution records while acting as auditor. Freeze this option and the mapping-script
commit before execution. A premature disclosure invalidates the blinding claim and
must be recorded, not silently ignored.

The runner script launches every session non-interactively and writes traces directly
to restricted storage. No one watches sessions live or starts them by hand, since the
loaded skill text reveals the arm.

### Transcript redaction before annotation

Behavioural differences produced by the skills themselves, such as a one-line
statement of intent or a standalone recap, cannot be redacted without removing scoring
evidence. Blinding is therefore partial. Do not describe the annotation as fully blind.
Redaction replaces file contents, not paths in tool calls; the identical install-path
requirement above prevents those paths from revealing the arm.

Keep complete originals in restricted storage for verification after annotations are
frozen. Produce identical redacted annotation copies for the model and human:

1. Replace the contents of any file under the skill directory, including SKILL.md
   and references, with the fixed placeholder `[skill content]` wherever exposed in a tool result
   or transcript. Keep the tool call itself and all other tool results. Replace only
   the skill-content spans in mixed results, preserving surrounding task evidence.
   For Bash commands containing an explicit path under `/opt/evaluation` (after
   `normpath`), mark the entire tool result as ONE skill-file segment. This also
   redacts metadata from `wc -l`, `ls -la`, `stat`, `sha256sum`, `grep -c` and `du`;
   content matching alone cannot recognise arm-specific numbers.
   Exception: a command containing a `cargo run [--offline] --manifest-path
   /opt/evaluation/.claude/skills/omarchy-theme-scaffold/scripts/theme-tool/Cargo.toml
   -- <args>` retains content-based segmentation so helper output stays task evidence.
   The manifest must be its only explicit evaluation path after normalisation;
   command substitution (`$(` or backticks) is not exempt, and every `cd` target
   must normalise under `/work/fixture`. Pipes, `&&`, `;`, newlines and redirections
   such as `2>&1` are allowed under this rule. Only SKILL.md differs between arms;
   helper source is identical.
   Matching keys (not retained output) strip Read line numbers and grep match/context
   prefixes, including single-file `12:text` and `13-text`.
   Residual: a relative path used after `cd` into the skill directory in an earlier
   command is not caught by provenance; shell state is not tracked. Blinding remains
   partial.
2. Search every assistant message and final response for distinctive phrases from
   both completion blocks. Baseline phrases: "Keep a narrow change narrow" and
   "without another design-approval step". Candidate phrases: "Before the first
   change, say in one line" and "sets scope and deliverable". Match across whitespace
   and case differences; replace matches with `[skill quote]`. Record counts per
   session without exposing which arm's phrase matched to the annotators.
3. Remove arm labels and skill-version identifiers from annotation metadata. Keep
   the redaction script, its commit and a per-session redaction log in the run
   manifest. Logs record opaque span IDs, replacement kinds/counts and input/output
   hashes; never include removed skill text or the sealed arm mapping.
   Annotation copies omit skill-content hashes and paths, segment counts, and the
   host_summary event (cost and turns). Restricted originals retain this evidence.

Redaction must not remove task actions, commands, outputs or patches: the skill-file
content/metadata replacement described above is the explicit exception, not permission
to censor task evidence. Preserve all fixture edits and verification output. Check
redacted copies against originals mechanically before annotation; if instruction text
cannot be isolated without losing scoring evidence, flag the session for resolution
before annotation rather than making a silent deletion. Freeze the redaction script
and its phrase list before execution.

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

The exact two-sided Mantel–Haenszel test with six cases × three runs per arm has
these stratified detectability figures (p-values rounded as shown):

| Pattern (baseline → candidate) | Totals | Exact p |
| --- | --- | --- |
| One case 0/3→3/3, rest 3/3 in both arms | 15/18 → 18/18 | 0.10 |
| Every case 1/3→2/3 | 6/18 → 12/18 | 0.12 |
| Every case 0/3→1/3 | 0/18 → 6/18 | 0.031 |
| Every case 2/3→3/3 | 12/18 → 18/18 | 0.031 |
| Two cases 0/3→3/3, rest 3/3 in both arms | 12/18 → 18/18 | 0.005 |
| Baseline 14/18 (one case 0/3, one case 2/3) → 18/18 | 14/18 → 18/18 | 0.050 (not < 0.05) |

- The ≥14/18 regression-only rule is consistent with the stratified test. The most
  favourable 14/18 configuration gives p=0.050 exactly, which fails p<0.05.
- With Holm's correction across four settings, a headline claim requires the smallest
  primary p-value to be below 0.0125. Uniform modest improvements (p≈0.03) cannot
  support a headline claim.

For any setting whose baseline completion is 14/18 or better, the run checks for
regressions only. A null result there is not evidence of no effect.
Below that ceiling, a null result also does not establish equivalence; report the
limited resolution of this sample size.

Do not replace failed sessions with retries. Record provider/host failures and their
causes; any rerun must be reported separately under a declared revised protocol.
Publish the traces, score table and analysis before making performance claims.
