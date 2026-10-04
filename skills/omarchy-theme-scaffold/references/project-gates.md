# Optional project gates

The existing Rust `check` stays advisory for contrast and ignored files. Use the
separate Python 3.11+ checker when the project has chosen requirements:

```sh
python3 "<scaffold-skill-dir>/scripts/check_policy.py" /path/to/theme \
  --contrast foreground/background=4.5 \
  --contrast bright_foreground/selection=4.5 \
  --contrast accent/background=3 \
  --deny-ignored-files --check-images
```

Choose actual resolved text/background keys and thresholds for the intended use.
Do not copy this entire command blindly: optional palette keys may be absent.
Ratios range from 1 to 21. All selected pairs must pass, using unrounded ratios.
Missing keys, malformed TOML or selected values other than explicit `#RRGGBB`
fail. This checker does not implement the runtime's aliases, fallback derivation,
gradients or alpha composition. Resolve those separately instead of changing a
valid theme to satisfy the helper. Ratios are project rules, not registry rules
or full accessibility certification.

`--deny-ignored-files` fails for the reviewed root `.lua` and terminal/VS Code
files. Nested filenames do not receive that root-only rule. Links and special
files fail all selected gates; root Git metadata is excluded. This is a staging
compatibility check, not a malware scan or sandbox. Review upstream drift before
changing the list.

`--check-images` requires Pillow. Install the tested decoder into an appropriate
virtual environment using `python3 -m pip install -r
"<scaffold-skill-dir>/scripts/requirements-media.txt"` (one shell command). A missing
decoder fails the gate. Every jpg/jpeg/png/gif/bmp/webp file in the theme tree is
verified and decoded, including animation frames; filename and decoded format
must match. No supported images also fails. Project resource limits are 50 MiB
per image, 40 million total decoded pixels per image including frames, and 256
frames. A valid larger animation can fail these project limits. They are not a
claim about upstream animation limits.

Video decoding, image rights, preview minimum dimensions/composition, crop safety,
reserved slugs, registry acceptance and live desktop rendering remain separate.
The tool is read-only. Run on a stable checkout, not one being changed concurrently.
Record selected flags, file/commit identity and output with the handoff evidence.
