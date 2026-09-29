---
name: omarchy-theme-apps
description: Check and fix how an Omarchy theme reaches terminals, editors, GTK apps and other themed applications.
---

# Omarchy Theme Apps

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Build a matrix of requested app, installed version, template/hook source, generated config, reload behaviour and observed result. Begin with current `default/themed` and theme-set commands, not a historical list of dotfiles.

Prefer shared palette generation. Git-installed themes lose terminal configs and Lua/vscode.json payloads under the current staging rules. Do not promise an editor extension or Neovim plugin will be installed by shipping those files. If an app needs separate user configuration, document it honestly and keep it outside theme installation unless explicitly requested.

When one app is wrong, compare source palette, generated current output, application config path and reload state. Preserve unrelated user settings. Mark absent apps untested instead of installing a broad suite just to complete a matrix. Deliver only the necessary fixes and tested coverage.

Before delivering a theme archive or PR, run the scaffold skill’s development handoff gate, independently of release; resolve its actual installed directory. Diagnosis-only work stays read-only.

## Task completion

Use the existing brief and project decisions; complete the requested implementation
and relevant verification without another design-approval step. Load only references
needed for the affected contract and reuse evidence whose inputs are unchanged.
Keep a narrow change narrow. Add permanent tests when they protect changed behaviour;
do not turn a cosmetic edit into a new test framework. Give concise progress updates
for substantial work and report only observed results. Reuse existing authorisation;
prepare concrete changes before asking about a remaining live or publication action.
If a helper or desktop is unavailable, finish the portable work, perform the available
manual checks and identify what was not run. Do not invent capabilities or evidence.
