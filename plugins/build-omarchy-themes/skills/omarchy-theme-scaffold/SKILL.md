---
name: omarchy-theme-scaffold
description: Generate a new Omarchy theme repository with a semantic palette and checks, without changing the active desktop.
---

# Omarchy Theme Scaffold

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Read the local contract reference, then choose an unused theme slug. Check upstream reserved/taken slugs before public release; a valid local name is not a reservation.

Use the bundled dependency-free Rust helper:

```sh
cargo run --manifest-path scripts/theme-tool/Cargo.toml -- scaffold /path/to/omarchy-my-theme-theme
cargo run --manifest-path scripts/theme-tool/Cargo.toml -- check /path/to/omarchy-my-theme-theme
```

The destination must not already exist. The scaffold supplies an original starter palette, README and media attribution guidance. It intentionally has no fabricated desktop preview, no wallpaper licence claim and no theme install hook. Add a licensed wallpaper directly in backgrounds/ and a real desktop preview after live verification. Use palette and shell skills to implement the requested character.

The helper accepts a deliberately narrow flat palette syntax and performs local structural/contrast checks. It does not claim full TOML, legacy or registry parity. `--release` adds the recommended preview.png presence check, not a complete publish gate. Installing this agent bundle does not install or apply a desktop theme. Hand back files and outstanding live/media checks.
