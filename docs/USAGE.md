# Installation and development

## Install and manage skills

Run the installer from a reviewed checkout. Python 3.11+ is required.

```sh
python3 scripts/install_agent_skills.py --target agents --scope user
```

Targets include `agents`, `codex`, `cursor`, `gemini`, `claude`, `opencode` and a
generic destination. Run `--help` for destination and scope options. Add `--dry-run`
to preview an installation. Preview updates with `--update --diff`, or removal with
`--uninstall --diff`. Modified managed files are protected unless you use `--force`.

For a local Claude Code plugin, run `claude --plugin-dir .`. The OpenAI adapter is
at `plugins/build-omarchy-themes`. See [models and hosts](FRONTIER-MODELS.md).

Installation adds agent instructions and helpers. Applying a desktop theme is a
separate action. A theme belongs in its own directory, not in this bundle.

## Theme helper

The Rust helper has no external crates. Manifest commands also require Git.

```sh
cargo run --manifest-path skills/omarchy-theme-scaffold/scripts/theme-tool/Cargo.toml -- scaffold /tmp/omarchy-example-theme
cargo run --manifest-path skills/omarchy-theme-scaffold/scripts/theme-tool/Cargo.toml -- check /tmp/omarchy-example-theme
```

It creates a starter palette, checks semantic keys and contrast, reports ignored
files and rejects symlinks. It accepts a strict flat palette subset; use Omarchy’s
resolver for other supported syntax and legacy migration.

Optional [project gates](../skills/omarchy-theme-scaffold/references/project-gates.md)
add contrast requirements, ignored-file failures and image decoding. Follow the
[development handoff](../skills/omarchy-theme-scaffold/references/handoff.md) when
preparing a theme archive or PR. Live installation, rendering and artwork rights
need their own evidence.

## Development

```sh
python3 -m pip install -r skills/omarchy-theme-scaffold/scripts/requirements-media.txt
./scripts/test
python3 scripts/sync_openai_adapter.py --check
python3 scripts/package.py --output-dir dist
```

Edit canonical `skills/` files, then refresh adapters with
`python3 scripts/sync_openai_adapter.py --write`. Packaging requires a clean commit
and produces five deterministic archives, a source manifest and checksums.
See [release preparation](RELEASING.md).

Check [source provenance](../NOTICE.md) and [validation evidence](../evals/ACCEPTANCE.md)
for inspected revisions and testing limits. Compatibility refers to the installed
`omarchy-version`; each theme must establish its own tested range.
