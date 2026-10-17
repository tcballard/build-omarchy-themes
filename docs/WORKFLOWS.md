# Workflow entry points

Personal theme / Agents panel: shipped Omarchy guide → inspiration → build locally
→ apply when requested → inspect → preserve rollback. No repository, archive or
registry gate is required. The panel launches the default agent, not this bundle.

Distributable theme: design → palette → scaffold → shell/apps/wallpapers as needed
→ test local and Git-installed paths → development handoff.
Existing bug: debug → affected implementation skill → focused test → development handoff.
Legacy theme: migrate → test → development handoff.
Small colour adjustment: palette → focused test; handoff only for an archive or PR.
Diagnosis-only requests stay read-only; do not force every skill into every task.

**Every theme archive or development PR reaches development handoff**, regardless
of which implementation skill was used. Follow the scaffold’s
[handoff reference](../skills/omarchy-theme-scaffold/references/handoff.md): generated
README defaults, file-bound evidence and repeatable `handoff` checks. This gate
also applies to documentation/media-only corrections; rerun only affected checks.

Live acceptance and demo require a real desktop. Without one, report NOT RUN and
still deliver a useful development PR. Release preparation follows separately
when requested; registry submission follows publish and its own authorization.
A development handoff pass does not imply any of those later gates passed.

Skills are portable and contain their own contract reference. Resolve the scaffold
helper by installed skill name, not an assumed sibling folder or working directory.
