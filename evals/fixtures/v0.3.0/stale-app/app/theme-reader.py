# Synthetic fixture, not Familiar Paint production code.
from pathlib import Path
PALETTE = Path("current/theme/colors.toml").read_text()
def current_palette():
    return PALETTE
