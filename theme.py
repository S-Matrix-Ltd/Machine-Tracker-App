from kivy.utils import get_color_from_hex
from kivy.metrics import dp, sp

BG_COLOR = get_color_from_hex("#070B12")
CARD_COLOR = get_color_from_hex("#111827")
CARD_INNER = get_color_from_hex("#1B2436")
CARD_ACTIVE = get_color_from_hex("#1E293B")
BORDER_COLOR = get_color_from_hex("#26334D")
ACCENT_COLOR = get_color_from_hex("#22D3EE")
ACCENT_TINT = (0.133, 0.827, 0.933, 0.15)

TEXT_PRIMARY = get_color_from_hex("#F8FAFC")
TEXT_MUTED = get_color_from_hex("#94A3B8")

STATUS_RUNNING = get_color_from_hex("#10B981")
STATUS_IDLE = get_color_from_hex("#64748B")
STATUS_BREAKDOWN = get_color_from_hex("#F43F5E")
STATUS_MAINTENANCE = get_color_from_hex("#F59E0B")

STATUS_MAP = {
    "RUNNING": STATUS_RUNNING,
    "IDLE": STATUS_IDLE,
    "BREAKDOWN": STATUS_BREAKDOWN,
    "MAINTENANCE": STATUS_MAINTENANCE,
}

STATUS_TINT_MAP = {
    "RUNNING": (0.063, 0.725, 0.506, 0.16),
    "IDLE": (0.392, 0.455, 0.545, 0.16),
    "BREAKDOWN": (0.957, 0.247, 0.369, 0.16),
    "MAINTENANCE": (0.961, 0.620, 0.043, 0.16),
}

FONT_TITLE = sp(19)
FONT_SEC_LABEL = sp(11)
FONT_CARD_TITLE = sp(14)
FONT_BODY = sp(12)
FONT_CAPTION = sp(10)
FONT_BIG_NUM = sp(22)

PAD_SCREEN = dp(14)
RADIUS_BOX = dp(16)
RADIUS_INNER = dp(12)

ICONS = {
    "home": "\ue88a",
    "machines": "\ue30a",
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
    "back": "\ue5c4",
    "expand": "\ue5cf",
    "bolt": "\uea0b",
}
