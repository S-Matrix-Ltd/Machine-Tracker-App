from kivy.utils import get_color_from_hex
from kivy.metrics import dp, sp

# Core Palette
BG_COLOR = get_color_from_hex("#0B0F17")
CARD_COLOR = get_color_from_hex("#131A26")
CARD_ALT_COLOR = get_color_from_hex("#182232")
BORDER_COLOR = get_color_from_hex("#1F2937")
ACCENT_COLOR = get_color_from_hex("#22D3EE")
ACCENT_TINT = (0.133, 0.827, 0.933, 0.14)

# Text Hierarchy
TEXT_PRIMARY = get_color_from_hex("#F8FAFC")
TEXT_MUTED = get_color_from_hex("#8B98A9")

# Status Palette (Used ONLY for dots, 3dp left borders, and small chips)
STATUS_RUNNING = get_color_from_hex("#22C55E")
STATUS_IDLE = get_color_from_hex("#94A3B8")
STATUS_BREAKDOWN = get_color_from_hex("#EF4444")
STATUS_MAINTENANCE = get_color_from_hex("#F59E0B")

STATUS_MAP = {
    "RUNNING": STATUS_RUNNING,
    "IDLE": STATUS_IDLE,
    "BREAKDOWN": STATUS_BREAKDOWN,
    "MAINTENANCE": STATUS_MAINTENANCE,
}

STATUS_TINT_MAP = {
    "RUNNING": (0.133, 0.773, 0.369, 0.14),
    "IDLE": (0.580, 0.639, 0.722, 0.14),
    "BREAKDOWN": (0.937, 0.267, 0.267, 0.14),
    "MAINTENANCE": (0.961, 0.620, 0.043, 0.14),
}

# Typography Scale
FONT_TITLE = sp(20)
FONT_SEC_LABEL = sp(12)
FONT_CARD_TITLE = sp(15)
FONT_BODY = sp(13)
FONT_CAPTION = sp(11)
FONT_BIG_NUM = sp(26)

# 8dp Spacing System
PAD_SCREEN = dp(16)
GAP_SECTION = dp(24)
GAP_CARD = dp(12)
GAP_GRID = dp(8)
RADIUS_CARD = dp(14)

# MaterialIcons-Regular.ttf Unicode Codepoints
ICONS = {
    "home": "\ue88a",
    "machines": "\ue8b8",
    "capa": "\ue85d",
    "settings": "\ue8b8",
    "running": "\ue037",
    "idle": "\ue034",
    "breakdown": "\ue002",
    "maintenance": "\ue869",
    "check": "\ue5ca",
    "check_circle": "\ue86c",
    "calendar": "\ue878",
    "add": "\ue145",
    "build": "\ue869",
    "report": "\ue8b2",
    "inventory": "\ue179",
    "handover": "\ue873",
    "search": "\ue8b6",
    "back": "\ue5c4",
    "chevron_right": "\ue5cc",
}
