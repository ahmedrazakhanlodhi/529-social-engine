"""Brand system for The 529 Network social engine.
Single source of truth for colors, fonts, and asset paths.
Change values here to retune the whole app."""

from pathlib import Path

ROOT = Path(__file__).parent
FONT_DIR = ROOT / "fonts"
ASSET_DIR = ROOT / "assets"

# Colors. Greens and steel/mist are the stated brand palette; the leaf accent is
# sampled from the logo cap. The gold accent is a proposed warm neutral and is
# the one value awaiting confirmation.
COLORS = {
    "green":        "#3A8916",   # primary
    "green_deep":   "#2B650B",   # deep green (footers, panels)
    "green_bright": "#4C942D",   # leaf accent (from logo)
    "steel":        "#708686",   # steel gray (wordmark family)
    "mist":         "#C6DDBB",   # light mist green
    "gold":         "#A8883C",   # warm gold accent  <-- confirm
    "ink":          "#242A24",   # near-black text
    "paper":        "#F4F6F1",   # light neutral background
    "white":        "#FFFFFF",
}

FONTS = {
    "regular":  str(FONT_DIR / "Archivo-Regular.ttf"),
    "semibold": str(FONT_DIR / "Archivo-SemiBold.ttf"),
    "bold":     str(FONT_DIR / "Archivo-Bold.ttf"),
    "black":    str(FONT_DIR / "Archivo-Black.ttf"),
}

LOGOS = {
    "529_color": str(ASSET_DIR / "logo_529_color.png"),
    "529_white": str(ASSET_DIR / "logo_529_white.png"),
    "nast_white": str(ASSET_DIR / "nast_white.png"),
    "nast_steel": str(ASSET_DIR / "nast_steel.png"),
    "nast_dark":  str(ASSET_DIR / "nast_dark.png"),
}

# Output sizes offered per platform.
SIZES = {
    "Instagram portrait (1080x1350)": (1080, 1350),
    "Instagram / Facebook square (1080x1080)": (1080, 1080),
    "Facebook landscape (1200x630)": (1200, 630),
    "LinkedIn (1200x627)": (1200, 627),
    "Story / Reel cover (1080x1920)": (1080, 1920),
}

# Five content pillars and target monthly mix (from the strategy).
PILLARS = {
    "1. 529 Made Simple": 30,
    "2. Proof in Numbers": 20,
    "3. Across the States": 20,
    "4. Education Paths": 15,
    "5. People & Partnerships": 15,
}

# Feed balance (useful / community / organizational).
FEED_BALANCE = {"Useful / educational": 70, "Community / member": 20, "Organizational": 10}

# Approval lanes.
LANES = {
    "GREEN": "Evergreen basics, previously approved copy, reposts, event photos. Fast approval.",
    "AMBER": "Compendium numbers, state examples, tax or eligibility language. Data verification required.",
    "RED": "Federal or state policy, legal or tax interpretation, controversy, corrections. Leadership review.",
}

# Which lane a template/pillar defaults to.
def default_lane(template_type: str, pillar: str) -> str:
    t = (template_type or "").upper()
    if "MYTH" in t or "STATE" in t or "ACCESS" in t or "PARTNER" in t or "BIG NUMBER" in t:
        return "AMBER"
    return "GREEN"
