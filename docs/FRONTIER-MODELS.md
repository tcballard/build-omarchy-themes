# Models and hosts

The twelve portable skills share instructions across providers; the OpenAI copy is
generated. Select the model and effort in the host. The skills do not set API
parameters, require subagents or assume proprietary tools. Adapter parity establishes
packaging consistency, not model quality or live host discovery.

## Provider guidance and host settings

API defaults below come from the provider guides; Claude Code and other hosts may
set their own effort. On Fable 5.1, Opus 5.5 and Sonnet 5.5, notes between tool calls
can arrive as thinking blocks that are empty under the default display setting, so
enable progress-update display in the host. Fable 5.1 also writes fewer updates than
Fable 5.

- **Astra:** [OpenAI skills guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
  informs task-relevant loading, clear completion and avoiding excessive procedural
  constraints. Select supported effort in the host; effort labels are not equivalent
  across models.
- **Claude Fable 5.1:** [Anthropic guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1).
  API default effort: **high**. Guidance informs focused edits, completing requested
  work with an exception for questions and problems, a self-check before stopping,
  evidence before state-changing commands, and current-source checks at low effort.
  Add tests only when asked or when the repository already keeps relevant tests.
- **Claude Opus 5.5:** [Anthropic guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5).
  API default effort: **medium**. Include an explicit early-stop self-check: a closing
  plan for in-scope work means that work remains to be done.
- **Claude Sonnet 5.5:** [Anthropic guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-sonnet-5-5).
  Use **medium** for well-specified agentic work. Open-ended requests can trigger
  builds, so explicitly distinguish ideas and assessments from implementation.
  Add tests only when asked or already maintained for that change, and require fresh
  source evidence even at low effort.

Review record, 29 September 2026: re-read the Fable 5.1, Opus 5.5 and Sonnet 5.5
guides linked above. Sonnet's guidance confirms medium effort for well-specified
agentic work, explicit ideas-only scope, limits on unrequested additions and current
source checks. All three guides describe progress-update display in the host.
The shared instructions enforce scope, test policy, evidence and recency at every
effort level. Scaffolded theme repositories contain no tests by default.

No Claude model has executed the skills. Two earlier candidate-only smoke exercises
ran on ChatGPT Work subagents with the model and effort not exposed; they predate the
replacement completion block. These are not Astra or Claude benchmarks. No measured
cross-model improvement is claimed.

## Useful requests

- Build: “Implement the attached theme brief in this repository. Preserve the slug
  and selected wallpaper. Finish portable checks and prepare a development PR;
  record live checks as pending. Do not apply the theme or publish.”
- Small fix: “Change the accent to #80bfa0. Preserve the other palette values and
  rerun affected checks. Do not redesign the theme.”
- Ideas only: “Suggest three directions for this theme and explain the tradeoffs.
  Deliver a brief only; do not create or change theme files.”
- Diagnosis: “Explain why this Git-installed theme loses its terminal settings.
  Inspect the supplied sources; do not change files or switch my desktop.”
- Resume: “Continue from the project record and finish the missing credits. Keep
  its decisions and distinguish previous tests from results reproduced now.”

See the [behavioural protocol](../evals/README.md) and the
[144-session Claude evaluation planned for v0.2.1](../evals/claude-v0.2.1.md).
Record exact model and host identifiers; unavailable identifiers are not inferred.
