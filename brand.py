"""Brand and strategy constants for The 529 Network Content Hub."""
from pathlib import Path

ROOT = Path(__file__).parent
ASSET_DIR = ROOT / "assets"

COLORS = {
    "green": "#3A8916",
    "green_deep": "#2B650B",
    "green_bright": "#4C942D",
    "steel": "#708686",
    "mist": "#C6DDBB",
    "gold": "#A8883C",
    "ink": "#242A24",
    "paper": "#F4F6F1",
    "white": "#FFFFFF",
}

# Font names only. The distributable intentionally does not bundle font files.
# Pillow will try these common system fonts and fall back safely if unavailable.
FONTS = {
    "regular": ["DejaVuSans.ttf", "Arial.ttf"],
    "semibold": ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "DejaVuSans.ttf"],
    "bold": ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "DejaVuSans.ttf"],
    "black": ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "DejaVuSans.ttf"],
}

LOGOS = {
    "529_color": str(ASSET_DIR / "logo_529_color.png"),
    "529_white": str(ASSET_DIR / "logo_529_white.png"),
    "nast_white": str(ASSET_DIR / "nast_white.png"),
    "nast_steel": str(ASSET_DIR / "nast_steel.png"),
    "nast_dark": str(ASSET_DIR / "nast_dark.png"),
}

SIZES = {
    "Instagram portrait (1080x1350)": (1080, 1350),
    "Instagram / Facebook square (1080x1080)": (1080, 1080),
    "Facebook landscape (1200x630)": (1200, 630),
    "LinkedIn (1200x627)": (1200, 627),
    "Story / Reel cover (1080x1920)": (1080, 1920),
}

PILLARS = {
    "1. 529 Made Simple": 30,
    "2. Proof in Numbers": 20,
    "3. Across the States": 20,
    "4. Education Paths": 15,
    "5. People & Partnerships": 15,
}

CHANNELS = ["Instagram", "LinkedIn", "Facebook", "Other"]
WORKFLOW = ["Draft", "Fact checked", "Communications review", "Approved", "Scheduled", "Published", "Archived", "Retired"]


def default_lane(template_type: str, pillar: str) -> str:
    """Legacy compatibility helper; the new app uses explicit workflow status."""
    t = (template_type or "").upper()
    return "AMBER" if any(x in t for x in ["MYTH", "STATE", "ACCESS", "PARTNER", "PEOPLE", "BIG NUMBER"]) else "GREEN"
