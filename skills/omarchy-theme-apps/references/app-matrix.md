# Application validation matrix

Use installed requested apps. Familiar, Familiar Paint and Task Manager are
examples from the development workflow, not a supported-version promise.

Record one row per app and state: app/version or commit, Omarchy version, theme
commit, palette/config path actually read, override source, test action, expected
result, observed result, PASS/FAIL/NOT RUN, and screenshot/log path. Record display
scale, font size and light/dark mode. Do not copy a pass between versions.

| Action | Evidence to inspect |
| --- | --- |
| Switch light → dark → light while app remains open | Current staged files, actual app colours, watcher/reload behaviour; distinguish immediate update from restart-only update |
| Select text and focus controls with keyboard | Resolved selection text/background, visible focus, hover versus focus, disabled readability |
| Change personal font/spacing override, then switch theme | Effective settings persist where the consumer supports them; unrelated preferences unchanged |
| Change scale or use a second monitor where available | Clipping, dialogs, menus and target sizes; unavailable hardware stays NOT RUN |
| Reopen app and restore original desktop | Reload differences, original theme/background/settings restored |

Start read-only: source palette → generated output → machine override → app input
→ consumer state. If generated output is wrong, investigate templates/staging.
If it is right but the app is stale or hard-coded, report the app-side defect and
use the relevant app/plugin skill for an authorised repair. A screenshot alone
cannot prove which file supplied a colour.

Use disposable fixtures for automated tests. Desktop switching/restarting needs
existing task authorisation; prepare useful offline checks when it is absent.
