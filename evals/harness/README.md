# Claude evaluation preparation pipeline

Status: NOT RUN. This branch prepares the pipeline; it does not authorise or start
real sessions. See issue #5 and the canonical ../claude-v0.2.1.md protocol.

`python3 evals/harness/test_pipeline.py -v` runs synthetic records only. R is required
for the analysis tests; CI installs r-base-core and executes the same command. An R
skip is not a full synthetic pipeline pass. No provider calls occur in these tests.

Fixture files are under ../fixtures/claude-v0.2.1/. Their manifests live separately
under ../fixture-manifests/ to avoid a self-referential file hash or contaminating a
session. Evaluator manifests, rubric, prompt, scripts and run metadata stay outside
container mounts. Sources are pinned development snapshots, not live acceptance.
The 1×1 forest PNG is a CC0 synthetic link-test asset, not a usable theme preview.
The generated launcher snapshot is deliberately reduced and synthetic; provenance is
recorded outside the fixture tree in fixture-manifests/provenance. No fixture contains tests.

## Host contract (implementation supplied; live verification pending)

The runner requires a digest-pinned, preinstalled container image with a non-interactive
host command that reads one JSON request on stdin. Only /work/fixture (writable) and
/opt/evaluation/.claude/skills (read-only) are mounted. Do not mount this repository, evaluator
files, mapping, Docker socket, personal configuration or restricted traces. The host
must disable global/project memory outside the supplied skills and fixture and load
no auto-discovered evaluation docs. An independently verified API-only network must
permit provider traffic but deny tool-initiated external writes; this is an integration
prerequisite, not a security guarantee provided by a Docker network name. The host
must expose the fixture's home/ configuration as the task's user configuration.

The first JSONL line must be a `host_metadata` record, emitted before any model call, with configured_model_id, requested_effort, host_version, tools and loaded_skills. Tool events must contain complete `tool_call`
arguments and `tool_result` typed segments: `skill_file` (path/text under the fixed
skill root) or `task_output`. Record `action` effects, `read`, `check`, `patch`,
`assistant` and `final` events. Export a normalized trace object with session_id,
metadata.actions_complete, events and exit_status for redact.py/score.py.
The last JSONL line must be {"type":"host_summary","actions_complete":<bool>}.
Only this terminal summary supplies actions_complete; first-line host_metadata cannot
attest to completed actions. Missing/invalid terminal summary after matching metadata
is host_summary_missing_no_retry: score failure and continue without retry. Raw traces
remain restricted. Missing segmentation/action coverage/settings is a blocker, not a
pass. No live host is connected here, so integration and effort controls remain
unverified. No substitute model or effort is allowed.

All host state/configuration/caches must stay under /tmp, never /work/fixture. Set
HOME=/work/fixture/home only for a fixture containing home/; otherwise HOME=/tmp/home.
Relocate the host's own configuration with its verified config_environment_name to
/tmp/host-config. Use XDG_CONFIG_HOME=/tmp/config, XDG_CACHE_HOME=/tmp/cache,
XDG_DATA_HOME=/tmp/data, XDG_STATE_HOME=/tmp/state, PIP_CACHE_DIR=/tmp/pip-cache,
npm_config_cache=/tmp/npm-cache, CARGO_HOME=/tmp/cargo-home and
CARGO_TARGET_DIR=/tmp/cargo-target. The image includes rustc and cargo; the scaffold
helper has no dependencies and must build offline against the read-only skill mount.

Every injected skill file in every channel (system messages, prompt preambles,
skill-tool expansions as well as ordinary tool reads) must be exported as tool_result
segments of kind skill_file. Do not duplicate the unredacted content in other events.
Missing all-channel coverage blocks host verification (skill_content_all_channels).

Before freeze step 5, perform host pre-flight on scratch fixtures only, never the six
case trees: a no-op request with home/ and another without must preserve complete
before/after inventories. Inside the container, with networking disabled, run:
`cargo run --manifest-path /opt/evaluation/.claude/skills/omarchy-theme-scaffold/scripts/theme-tool/Cargo.toml -- check <scratch theme>`.
It must exit 0. Record restricted evidence and host.preflight as no_write_home=true,
no_write_no_home=true, helper_build=true and evidence_sha256 (64 lowercase hex).
This environment has no connected host; these checks remain unobserved, not passed.

## Freeze and execution

1. Commit and verify fixtures/manifests.
2. Commit evaluator manifests and their hashes.
3. Commit scripts and record their exact Git commits and SHA-256 values.
4. Pass synthetic Python and R pipeline checks; retain evidence and versions.
5. Supply and verify host/model settings from capability/metadata observations without
   running evaluation cases. Record provider-returned IDs, actual effort and evidence.
6. Pin Astra annotator snapshot, effort and host; freeze prompt/rubric/code and versions.
7. `mapping.py --manifest ... --restricted-dir /outside/repo --public-output ...`
   generates a mapping only when steps 1–6 validate. Commit only public IDs and hash.
   Never print/open the mapping until annotations and adjudications are frozen.
8. `audit.py public-mapping.json audit.json` writes the fixed 29-ID sample and Python
   version in audit.python; commit it before execution.
9. Complete runs/claude-v0.2.1/manifest.json, set freeze state FROZEN, commit, and run
   readiness.py under the same Python version recorded in audit.python, because audit
   comparison includes it. It must pass with a clean tree. Any later change requires a declared
   protocol revision and a fresh freeze. Draft BLOCKED fields are intentionally not
   valid freeze values; "not exposed" is only for genuinely hidden optional metadata,
   never unresolved model identity, effort, isolation or annotator configuration.
10. Only then use runner.py. It creates an exclusive execution marker and never retries
    sessions. All output goes to restricted storage. No live observers. On an actual
    first session, change the protocol status and record execution start. An accidental
    pre-freeze session must be declared and excluded, not used to tune these fixtures.

Redact before annotation. Run score.py with before/after trees and normalized traces;
without evidence-bound annotations, completion stays null. Append frozen independent
annotations, adjudicate, then unseal the mapping and prepare the 144-row analysis CSV.
analysis.R rejects missing, duplicate or mis-sized strata and emits settings.csv,
strata.csv and versions.txt. Secondary fields are reported descriptively per applicable
case; never include null placeholders in denominators or test significance.

## Failures, resume and assembly

Matching metadata followed by a timeout, crash or non-zero exit is scored as failure,
with record.json and trace.json retained, and the batch continues without retry.
Missing first-line metadata or mismatched settings halts for a protocol revision.
`runner.py --resume` requires the same manifest hash in EXECUTION_STARTED.json. It
skips every existing session directory, marks directories without record.json as
interrupted_no_retry, and appends skipped/interrupted IDs to restricted execution-log.jsonl.
Any existing record.json with halt=true blocks resume before any mutation.
It never repeats a session. Score interrupted traces even when snapshots are absent.

After annotation/adjudication is frozen, record its file SHA-256 in a restricted copy
of the run manifest as annotations.frozen_sha256. Preserve the original pre-execution
manifest unchanged. This post-run analysis attestation is not an execution input.
`assemble.py analysis-manifest.json sealed-mapping.json frozen-scores.json output-dir`
verifies both hashes and all 144 terminal scores before unblinding. The frozen file
contains a scores array. The output directory must not exist; primary.csv is the R
input and secondary.csv contains only applicable non-null descriptive observations.
The generated case-specific six-word phrase list is pinned in the run manifest;
redact.py requires the case supplied from restricted metadata, never inferred from text.

## Claude Code host implementation (Phase 1)

Build: `docker build -f evals/harness/host/Dockerfile -t claude-eval-host .`.
The image pins Claude Code 2.1.284, a Node base, Rust 1.85.1 and the collector by
version/digest. CI builds and checks the offline helper without provider credentials.
Publish the image to your authorised registry, record its repository digest (not just
its local image ID), then run `host/setup-network.sh IMAGE@sha256:DIGEST` on the host.
The execution network is internal; only the separate CONNECT proxy reaches the
outside, and it accepts api.anthropic.com:443 only. Never attach execution containers
to bridge or host networking. The shared container command runs as UID 1000 with
read-only skills/root, a writable scratch fixture, and writable /tmp. Host mount
preparation supports UID 1000 or root; it changes ownership only in disposable trees.

Use full model IDs claude-fable-5-1, claude-opus-5-5 and claude-sonnet-5-5. Initial
host_metadata is configuration from system/init plus claude --version, not observed
effort. The terminal host_summary includes matched tool coverage, successful result,
returned message models, request telemetry, cost and turns. Main/subagent request
model or effort drift halts; auxiliary requests are retained. Missing telemetry or
unknown sources block verification. Missing summary remains a scored no-retry failure.
The effort environment override is explicitly removed. Limits are max_turns,
max_budget_usd and seconds; defaults are 100 turns, $20 and 1,800 seconds per session,
identical for both arms. Caps fail the session. The maximum authorised run budget must
be considered before execution; these are caps, not cost predictions.

Phase 2: `preflight.py manifest.json /restricted/preflight observed-manifest.json`.
It uses only newly created scratch content, tests both HOME layouts, offline helper,
proxy allow/direct-and-proxy deny, skill segmentation, and all four settings. It writes
restricted evidence and only marks verified after all checks pass. The normalised
shared command template hash is included in preflight and compared by readiness.
No evaluation case is used for preflight. Do not claim verification from CI alone.
Pin the separate Astra annotator and pass `readiness.py manifest.json --through 6`.
Then follow the existing mapping → audit → committed freeze order. Execution stays
NOT RUN until the first real evaluation session; preflight is recorded separately.

After redaction and mechanical scoring, use:
1. `prepare_packets.py REDACTED SCORES PACKETS` (no mapping input).
2. `annotate.py MANIFEST PACKETS MODEL_ANNOTATIONS` (pinned OpenAI snapshot, exclusive
   files and started markers; valid results are never retried, schema errors flagged).
3. `human-annotate.py MANIFEST PACKETS MODEL_ANNOTATIONS HUMAN_ANNOTATIONS`. This shows
   evidence without the model annotation, and requires independent human input.
4. `adjudicate.py MANIFEST PACKETS MODEL_ANNOTATIONS HUMAN_ANNOTATIONS RESOLUTIONS OUTPUT`.
   A review plan expands each disputed criterion to all 144 sessions. Re-run human
   annotation with --expanded-review PLAN into a fresh review directory, preserving
   the first-pass files. Resolve disputed values with evidence spans. All flags need
   explicit resolution. Frozen output keeps both originals and all decisions.
5. Hash frozen output into the restricted analysis manifest, then assemble.py and
   analysis.R. Publish redacted traces and complete score/analysis tables, including
   null/adverse results, only after checking for credentials or other private data.

The code does not substitute for Tom's independent human audit. Until host evidence,
annotator identity, mapping, audit and freeze are supplied, readiness must stay BLOCKED.
