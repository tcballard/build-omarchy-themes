# Astra, Fable and other models

Select the model and effort in the agent host. The twelve portable skills use the
same instructions across providers; the OpenAI copy is generated. They do not set
API parameters, require subagents, or assume proprietary tools. An adapter proves
packaging compatibility only, not model quality or live host discovery.

## Guidance reviewed on 29 September 2026

[OpenAI's Astra skills guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
supports loading task-relevant material, defining completion and avoiding excessive
procedural constraints. Themes uses short entry points, existing authorisation and
verification selected for the change. A supplied brief can proceed to implementation.

[Anthropic's Fable 5.1 guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-1)
informs focused edits, completion of authorised work, preservation of settled decisions
and factual progress updates. Host operators separately configure effort, progress
rendering, history handling and tool batching; those settings do not belong in theme
files. Re-evaluate settings in each host instead of assuming effort names are equivalent.

These are instruction-design decisions, not benchmark results. No Fable runner is
connected in the preparation environment. Do not advertise Fable execution or measured
Astra gains without recorded task traces. Other models can use the portable core;
capability and host support still require their own evaluation.

## Useful requests

- Build: “Implement the attached theme brief in this repository. Preserve the slug
  and selected wallpaper. Finish portable checks and prepare a development PR;
  record live checks as pending. Do not apply the theme or publish.”
- Small fix: “Change the accent to #80bfa0. Preserve the other palette values and
  rerun affected checks. Do not redesign the theme.”
- Diagnosis: “Explain why this Git-installed theme loses its terminal settings.
  Inspect the supplied sources; do not change files or switch my desktop.”
- Resume: “Continue from the project record and finish the missing credits. Keep
  its decisions and distinguish previous tests from results reproduced now.”

Use the [behavioural protocol](../evals/README.md) for baseline/candidate comparisons.
Record exact model and host identifiers when exposed, otherwise say not exposed.
A bounded workflow exercise is a smoke test, not an optimisation benchmark.
