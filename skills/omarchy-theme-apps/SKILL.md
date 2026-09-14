---
name: omarchy-theme-apps
description: Check and fix how an Omarchy theme reaches terminals, editors, GTK apps and other themed applications.
---

# Omarchy Theme Apps

Read [the contract reference](references/contract.md) when target-version, staging or registry details affect the task. Recheck upstream when the target differs.

Build a matrix of requested app, installed version, template/hook source, generated config, reload behaviour and observed result. Begin with current `default/themed` and theme-set commands, not a historical list of dotfiles.

Prefer shared palette generation. Git-installed themes lose terminal configs and Lua/vscode.json payloads under the current staging rules. Do not promise an editor extension or Neovim plugin will be installed by shipping those files. If an app needs separate user configuration, document it honestly and keep it outside theme installation unless explicitly requested.

When one app is wrong, compare source palette, generated current output, application config path and reload state. Preserve unrelated user settings. Mark absent apps untested instead of installing a broad suite just to complete a matrix. Deliver only the necessary fixes and tested coverage.
