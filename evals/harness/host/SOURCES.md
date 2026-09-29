# Host sources and verification boundary

Reviewed 2026-09-29 (HTML pages; the retrieval service rejected text/markdown):
- https://code.claude.com/docs/en/cli-reference
- https://code.claude.com/docs/en/headless
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/env-vars
- https://code.claude.com/docs/en/monitoring-usage

The adapter uses explicit added-directory skills in bare mode, turns/budget caps,
and local OTLP request evidence. API event source names include repl_main_thread;
the adapter retains raw values and normalises known main/subagent/auxiliary sources.
Unknown sources block validation rather than being silently treated as auxiliary.

Docker Hub authenticated public-registry manifest lookups on 2026-09-29 supplied
the Node 22 bookworm slim, Rust 1.85.1 slim bookworm and collector 0.123.0 digests
in Dockerfile. npm metadata confirmed @anthropic-ai/claude-code 2.1.284 with integrity
sha512-IuENsoLa+Y5fx5VaP0Md3n5UO7aYxjbFE/iydSDw6tMo2171oaxaaBa9oIepPG9NILd1owSx74ozsqAkTbEOjw==.
An image build/version smoke is not evidence of successful provider access or effort.

The annotator uses the OpenAI Responses endpoint, JSON output mode and explicit
reasoning effort, following https://developers.openai.com/api/docs/guides/structured-outputs
and https://developers.openai.com/api/docs/guides/reasoning. No annotator identity is
inferred from the requested label; the returned exact snapshot must match the pin.
