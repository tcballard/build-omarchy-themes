# Build Omarchy Themes

<p>
  <a href="https://github.com/tcballard/build-omarchy-themes/actions/workflows/ci.yml"><img alt="CI status" height="20" src="https://github.com/tcballard/build-omarchy-themes/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="LICENSE"><img alt="Licence: MIT" height="20" src="https://img.shields.io/badge/license-MIT-blue?style=flat-square"></a>
  <a href="https://github.com/tcballard/omarchy-badges"><img alt="Built for Omarchy: Theme" height="20" src="https://raw.githubusercontent.com/tcballard/omarchy-badges/75975e5b5bf75e7ede3764bcd2950046f7abfe2c/badges/v1/omarchy-theme.svg"></a>
</p>

A companion to [Build Omarchy Plugins](https://github.com/tcballard/build-omarchy-plugins):
**twelve portable agent skills for turning a visual idea into an installable Omarchy theme.**

Design the palette, style the shell, check applications, prepare wallpapers,
check a development handoff, verify the desktop and submit to the Theme Registry.

## Status and compatibility

**v0.2.1.** Evaluation tooling and redaction fixes. The twelve theme skills are unchanged; the Claude evaluation remains **NOT RUN**.
Upstream runtime and registry contracts were inspected on 29 September 2026 at recorded revisions.
No live Omarchy desktop acceptance or provider-directory acceptance is claimed.
See [acceptance evidence](evals/ACCEPTANCE.md) and [source provenance](NOTICE.md).
Compatibility means the installed Omarchy version reported by `omarchy-version`,
not the ISO or Quickshell version. Themes built with this bundle must establish
and declare their own tested range.

## Use it

From a reviewed checkout, install the portable skills:

```sh
python3 scripts/install_agent_skills.py --target agents --scope user
```

The inherited installer supports agents, codex, cursor, gemini, claude, opencode,
and a generic destination. Use `--dry-run` first to inspect the destination;
`--update --diff` previews updates and `--uninstall --diff` previews removal.
Locally modified managed files are protected unless `--force` is explicitly used.
Installing agent skills never applies a desktop theme.

For a local Claude Code plugin, use `claude --plugin-dir .`. The OpenAI adapter
lives at `plugins/build-omarchy-themes`. These are distribution formats, not
claims of official marketplace approval or live host testing.

Try: “Build a warm ivory and deep green Omarchy theme, with readable terminals.”
Or: “Explain why this theme works locally but loses its terminal colours when installed.”

## Skills

- [omarchy-theme-design](skills/omarchy-theme-design/SKILL.md): Turn an Omarchy theme idea or visual reference into an implementable desktop theme brief.
- [omarchy-theme-palette](skills/omarchy-theme-palette/SKILL.md): Create or refine Omarchy semantic palettes, ANSI colours and light or dark variants with readability checks.
- [omarchy-theme-scaffold](skills/omarchy-theme-scaffold/SKILL.md): Generate a new Omarchy theme repository with a semantic palette and checks, without changing the active desktop.
- [omarchy-theme-shell](skills/omarchy-theme-shell/SKILL.md): Style Omarchy shell surfaces using supported shell.toml tokens and scoped theme overrides.
- [omarchy-theme-apps](skills/omarchy-theme-apps/SKILL.md): Check and fix how an Omarchy theme reaches terminals, editors, GTK apps and other themed applications.
- [omarchy-theme-wallpapers](skills/omarchy-theme-wallpapers/SKILL.md): Prepare Omarchy theme wallpapers and lock artwork with suitable crops, sizes and redistribution records.
- [omarchy-theme-test](skills/omarchy-theme-test/SKILL.md): Validate an Omarchy theme locally and on a live desktop, separating static checks from registry and runtime evidence.
- [omarchy-theme-debug](skills/omarchy-theme-debug/SKILL.md): Diagnose Omarchy theme loading, stale colours, ignored files, missing wallpapers and application reload problems.
- [omarchy-theme-demo](skills/omarchy-theme-demo/SKILL.md): Capture honest Omarchy theme screenshots and comparison demos for README and registry previews.
- [omarchy-theme-migrate](skills/omarchy-theme-migrate/SKILL.md): Migrate legacy Omarchy theme files and colour aliases to current palette-driven themes while preserving intended appearance.
- [omarchy-theme-release](skills/omarchy-theme-release/SKILL.md): Prepare a reproducible Omarchy theme release with compatibility notes, media provenance and installation evidence.
- [omarchy-theme-publish](skills/omarchy-theme-publish/SKILL.md): Prepare or submit an Omarchy theme to the Theme Registry using its current form and validation workflow.

See [workflow entry points](docs/WORKFLOWS.md) and [Models and hosts](docs/FRONTIER-MODELS.md).
The instructions are informed by current provider guidance; this is not a claim of
measured cross-model improvement. The host selects the model and effort level.

## Theme helper

The helper is Rust with no external crates (content manifests also require Git):

```sh
cargo run --manifest-path skills/omarchy-theme-scaffold/scripts/theme-tool/Cargo.toml -- scaffold /tmp/omarchy-my-theme-theme
cargo run --manifest-path skills/omarchy-theme-scaffold/scripts/theme-tool/Cargo.toml -- check /tmp/omarchy-my-theme-theme
```

It creates an original starter palette without replacing existing directories,
reports missing keys and ignored files, rejects symlinks, and measures contrast.
It deliberately supports a strict flat authoring subset, not all upstream TOML,
legacy migration or gradient syntax. Registry checks, decoded-image validation,
licensing, live rendering and final screenshots remain separate gates.

Before any theme archive or PR, follow [development handoff](skills/omarchy-theme-scaffold/references/handoff.md). The scaffold supplies badges, installation/rollback and honest evidence defaults; `snapshot` binds evidence to files and `handoff` checks documentation, media references and evidence consistency. A missing live desktop stays visible without blocking a development PR.

The desktop theme belongs in its own `omarchy-<slug>-theme` repository. This
repository is an **agent bundle**, not a theme to pass to `omarchy theme install`.

## Verification and packaging

```sh
./scripts/test
python3 scripts/sync_openai_adapter.py --check
python3 scripts/package.py --output-dir dist
```

Packaging requires a clean commit and emits deterministic source, portable plugin,
OpenAI adapter, Claude plugin and skills archives with SHA256SUMS. No release is
published by the packaging command.

## Licence

MIT for bundle code and instructions. Wallpaper and third-party artwork licences
must be established separately for each theme.

The workflow guidance is provider-informed. No Claude model has executed the skills;
the two ChatGPT Work smoke exercises had no exposed model identifier and predate the
guidance correction. See the [planned Claude evaluation](evals/claude-v0.2.1.md).
