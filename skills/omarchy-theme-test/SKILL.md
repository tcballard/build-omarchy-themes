---
name: omarchy-theme-test
description: Validate an Omarchy theme locally and on a live desktop, separating static checks from registry and runtime evidence.
---

# Omarchy Theme Test

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Locate omarchy-theme-scaffold by its installed skill name and resolve its actual directory; do not assume a sibling folder name or the project working directory. Run `cargo run --manifest-path "<scaffold-skill-dir>/scripts/theme-tool/Cargo.toml" -- check /absolute/path/to/theme`. If that skill is unavailable, continue with the palette/TOML and file checks available here and report the helper check as not run.

Run the scaffold helper's check command and inspect all warnings. Its palette subset and file checks are advisory; use the upstream registry validator for the actual submission contract. Verify syntax of custom shell TOML with a real TOML parser, then test the target consumer.

Decode final images, confirm size/aspect/crops, check root layout, links, ignored files, licensing and source controls. Record upstream validator revision and output when available. Never weaken a check to turn missing evidence into a pass.

For live validation, record installed Omarchy version, theme commit, session and display scale. Preserve the previous theme and wallpaper. Exercise switching into/out of the theme, a second switch, shell restart/login, focused/disabled/selected states and representative app reloads. Test both local development and the Git-installed staging path in a disposable account/VM when appropriate. Theme install can remove an existing destination: inspect it first. Restore the prior state after a temporary test. Report PASS/FAIL/NOT RUN with evidence and exact remaining gates.
