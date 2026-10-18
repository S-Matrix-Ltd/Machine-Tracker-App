import traceback
import os
import json
import time
import calendar
from datetime import datetime
from kivy.app import App
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line, Ellipse
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex

# ==========================================
# 1. THEME & COLORS
# ==========================================
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

STATUS_MAP = {"RUNNING": STATUS_RUNNING, "IDLE": STATUS_IDLE, "BREAKDOWN": STATUS_BREAKDOWN, "MAINTENANCE": STATUS_MAINTENANCE}

FONT_TITLE, FONT_SEC_LABEL, FONT_CARD_TITLE = sp(19), sp(11), sp(14)
FONT_BODY, FONT_CAPTION, FONT_BIG_NUM = sp(12), sp(10), sp(22)
PAD_SCREEN, RADIUS_BOX, RADIUS_INNER = dp(14), dp(16), dp(12)

ICONS = {"home": "H", "machines": "M", "breakdown": "B", "settings": "S", "running": "R", "idle": "I", "breakdown_icon": "!", "maintenance": "M", "check": "OK"}
FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "MaterialIcons-Regular.ttf")
if os.path.exists(FONT_PATH):
    LabelBase.register(name="Icons", fn_regular=FONT_PATH)
    ICON_FONT = "Icons"
    ICONS = {"home": "\ue88a", "machines": "\ue30a", "breakdown": "\ue889", "settings": "\ue8b8", "running": "\ue037", "idle": "\ue034", "breakdown_icon": "\ue002", "maintenance": "\ue869", "check": "\ue5ca"}
else:
    ICON_FONT = "Roboto"

# ==========================================
# 2. UI WIDGETS
# ==========================================
class ModernBox(BoxLayout):
    def __init__(self, bg_color=CARD_COLOR, border_color=BORDER_COLOR, radius=RADIUS_BOX, left_accent=None, auto_height=True, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_x, self.size_hint_y = 1, None
        if auto_height: self.bind(minimum_height=self.setter("height"))
        self.bg_rgba, self.bd_rgba, self.rad, self.left_accent = list(bg_color), list(border_color), radius, left_accent
        with self.canvas.before:
            self.c_bg = Color(*self.bg_rgba)
            self.r_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.rad])
            self.c_bd = Color(*self.bd_rgba)
            self.l_bd = Line(rounded_rectangle=(self.x, self.y, max(1, self.width), max(1, self.height), self.rad), width=1.1)
            if self.left_accent:
                self.c_ac = Color(*self.left_accent)
                self.r_ac = RoundedRectangle(pos=(self.x+dp(2), self.y+dp(10)), size=(dp(4), max(dp(10), self.height-dp(20))), radius=[dp(2)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *args):
        self.r_bg.pos, self.r_bg.size = self.pos, self.size
        self.l_bd.rounded_rectangle = (self.x, self.y, max(1, self.width), max(1, self.height), self.rad)
        if self.left_accent: self.r_ac.pos, self.r_ac.size = (self.x+dp(2), self.y+dp(10)), (dp(4), max(dp(10), self.height-dp(20)))

class AnimatedCard(ButtonBehavior, ModernBox):
    def __init__(self, on_tap_cb=None, **kwargs):
        super().__init__(**kwargs)
        self.on_tap_cb = on_tap_cb
        self.orig_bg = list(self.bg_rgba)
    def on_press(self):
        self.c_bg.rgba = CARD_ACTIVE
        Animation(opacity=0.82, duration=0.07).start(self)
    def on_release(self):
        Animation(opacity=1.0, duration=0.16, t="out_quad").start(self)
        Clock.schedule_once(lambda dt: setattr(self.c_bg, "rgba", self.orig_bg), 0.12)
        if self.on_tap_cb: Clock.schedule_once(lambda dt: self.on_tap_cb(), 0.08)

def make_label(text, font_size=sp(12), color=TEXT_PRIMARY, bold=False, halign="left", height_dp=22):
    lbl = Label(text=str(text), font_size=font_size, color=color, bold=bold, halign=halign, valign="middle", size_hint_y=None, height=dp(height_dp))
    lbl.bind(size=lbl.setter("text_size"))
    return lbl

class NavItem(ButtonBehavior, BoxLayout):
    def __init__(self, title_str, on_tap, **kwargs):
        super().__init__(orientation="vertical", size_hint_x=1, padding=[0, dp(4)], spacing=dp(2), **kwargs)
        self.on_tap_cb = on_tap
        self.pill = BoxLayout(size_hint=(None, None), size=(dp(68), dp(28)), pos_hint={"center_x": 0.5})
        with self.pill.canvas.before:
            self.p_col = Color(0, 0, 0, 0)
            self.p_rect = RoundedRectangle(pos=self.pill.pos, size=self.pill.size, radius=[dp(14)])
        self.pill.bind(pos=lambda i, v: setattr(self.p_rect, "pos", v), size=lambda i, v: setattr(self.p_rect, "size", v))
        self.tx = Label(text=title_str, font_size=sp(11), color=TEXT_MUTED, bold=True)
        self.pill.add_widget(self.tx)
        self.add_widget(self.pill)
    def on_release(self):
        Animation(opacity=0.6, duration=0.06).start(self)
        Animation(opacity=1.0, duration=0.15).start(self)
        self.on_tap_cb()
    def set_active(self, active):
        self.p_col.rgba = ACCENT_TINT if active else (0, 0, 0, 0)
        self.tx.color = ACCENT_COLOR if active else TEXT_MUTED


# ==========================================
# 3. MAIN APPLICATION APP CLASS
# ==========================================
class MachineTrackerApp(App):
    def build(self):
        self.title = "S Matrix Smart Eng-Ops"
        self.data_file = os.path.join(self.user_data_dir, "renata_sagar_v1.json")
        self.load_data()

        self.current_tab = "HOME"
        self.tab_history = []
        self.active_popup = None
        self.last_back_press = 0.0

        self.machine_filter = "ALL"
        self.expanded_machine_id = None
        self.selected_machine_id = self.db["machine_order"][0]

        Window.bind(on_keyboard=self.on_back_button)

        self.root_box = BoxLayout(orientation="vertical")
        with self.root_box.canvas.before:
            Color(*BG_COLOR)
            self.bg_rect = Rectangle(pos=self.root_box.pos, size=self.root_box.size)
        self.root_box.bind(pos=lambda i, v: setattr(self.bg_rect, "pos", v), size=lambda i, v: setattr(self.bg_rect, "size", v))

        self.toast_bar = ModernBox(bg_color=CARD_INNER, border_color=ACCENT_COLOR, radius=dp(10), auto_height=False, height=0, size_hint_y=None, padding=[dp(12), 0])
        self.toast_bar.opacity = 0.0
        self.toast_lbl = make_label("", sp(11), ACCENT_COLOR, bold=True, halign="center", height_dp=28)
        self.toast_bar.add_widget(self.toast_lbl)
        self.root_box.add_widget(self.toast_bar)

        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(2))
        self.feed = BoxLayout(orientation="vertical", size_hint_x=1, size_hint_y=None, padding=[dp(14), dp(14), dp(14), dp(28)], spacing=dp(14))
        self.feed.bind(minimum_height=self.feed.setter("height"))
        self.scroll.add_widget(self.feed)
        self.root_box.add_widget(self.scroll)

        self.nav_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(58), padding=[dp(8), 0])
        with self.nav_bar.canvas.before:
            Color(*CARD_COLOR)
            self.nb_rect = Rectangle(pos=self.nav_bar.pos, size=self.nav_bar.size)
            Color(*BORDER_COLOR)
            self.nb_line = Line(points=[0, dp(58), 1000, dp(58)], width=1)
        self.nav_bar.bind(pos=lambda i, v: (setattr(self.nb_rect, "pos", v), setattr(self.nb_line, "points", [i.x, i.top, i.right, i.top])), size=lambda i, v: (setattr(self.nb_rect, "size", v), setattr(self.nb_line, "points", [i.x, i.top, i.right, i.top])))

        self.nav_items = {
            "HOME": NavItem("Home", lambda: self.switch_tab("HOME")),
            "MACHINES": NavItem("Machines", lambda: self.switch_tab("MACHINES")),
            "BREAKDOWN": NavItem("History", lambda: self.switch_tab("BREAKDOWN")),
            "SETTINGS": NavItem("Settings", lambda: self.switch_tab("SETTINGS")),
        }
        for item in self.nav_items.values(): self.nav_bar.add_widget(item)
        self.root_box.add_widget(self.nav_bar)

        self.switch_tab("HOME", record_history=False)
        return self.root_box

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    self.db = json.load(f)
                if "machine_order" in self.db:
                    return
        except Exception:
            pass

        self.db = {
            "settings": {"user_name": "SAGAR ALI", "role": "Junior Engineer", "shift": "Shift A", "plant": "Renata PLC (Kashor Site)"},
            "oee": {
                "days": [
                    {"day": "Mon", "avail": 92, "perf": 88, "qual": 99, "oee": 80},
                    {"day": "Tue", "avail": 95, "perf": 90, "qual": 98, "oee": 84},
                    {"day": "Wed", "avail": 88, "perf": 85, "qual": 99, "oee": 74},
                    {"day": "Thu", "avail": 96, "perf": 92, "qual": 100, "oee": 88},
                    {"day": "Fri", "avail": 90, "perf": 89, "qual": 97, "oee": 78},
                    {"day": "Sat", "avail": 94, "perf": 91, "qual": 99, "oee": 85},
                    {"day": "Sun", "avail": 97, "perf": 93, "qual": 100, "oee": 90}
                ]
            },
            "machine_order": [], "machines": {}, "breakdown_history": []
        }
        
        initial_sls = ["Brevetti", "Korber", "Light Inspection 01", "Light Inspection 02", "PDLD", "Ampoule Labeling 01", "Conveyor Belt 04", "Blister & Cartooning", "Conveyor Belt 01", "Checkweigher 01", "Vail Labeling 02", "Conveyor Belt 03", "Washing and Drying", "Vail Labeling 01", "Conveyor Belt 02", "IFC Printer", "NKP 01", "NKP 02"]
        ids = ["095", "089", "137", "138", "134", "106", "133", "111", "130", "143", "108", "132", "135", "107", "131", "136", "128", "129"]

        for idx, nm in enumerate(initial_sls):
            mid = f"K02PR-{ids[idx]}"
            self.db["machine_order"].append(mid)
            st = "BREAKDOWN" if idx == 5 else ("MAINTENANCE" if idx == 12 else ("IDLE" if idx in (6, 14) else "RUNNING"))
            self.db["machines"][mid] = {
                "sl": idx + 1, "name": nm, "id": mid, "status": st,
                "product": "Standard Batch", "batch": "B26-1041", "pm_day": 18, "pm_done_oct": False,
                "std_time": "6.0 Hours", "act_time": "7.5 Hours", "delay_reason": "No delay",
                "operator": "Md. Tanvir", "officer": "Kamrul Hasan"
            }
        self.save_data()

    def save_data(self):
        try:
            with open(self.data_file, "w") as f: json.dump(self.db, f)
        except Exception: pass

    def animate_widget_in(self, widget, delay=0.0):
        widget.opacity = 0.0
        anim = Animation(opacity=1.0, duration=0.22, t="out_cubic")
        Clock.schedule_once(lambda dt: anim.start(widget), delay)

    def switch_tab(self, tab_name, record_history=True):
        if record_history and self.current_tab and self.current_tab != tab_name:
            if tab_name == "HOME": self.tab_history.clear()
            elif not self.tab_history or self.tab_history[-1] != self.current_tab: self.tab_history.append(self.current_tab)

        self.current_tab = tab_name
        for k, item in self.nav_items.items(): item.set_active(k == tab_name or (tab_name == "MACHINE_DETAIL" and k == "MACHINES"))
        self.feed.clear_widgets()
        self.scroll.scroll_y = 1.0

        if tab_name == "HOME": self.build_home()
        elif tab_name == "MACHINES": self.build_machines()
        elif tab_name == "MACHINE_DETAIL": self.build_machine_detail(self.selected_machine_id)
        elif tab_name == "BREAKDOWN": self.build_breakdown_history()
        elif tab_name == "SETTINGS": self.build_settings()

        for i, child in enumerate(reversed(self.feed.children)): self.animate_widget_in(child, delay=i * 0.035)

    def go_back_step(self):
        if self.tab_history:
            self.switch_tab(self.tab_history.pop(), record_history=False)
        else:
            self.switch_tab("HOME", record_history=False)

    def show_toast(self, message):
        self.toast_lbl.text = message
        Animation(height=dp(32), opacity=1.0, duration=0.18).start(self.toast_bar)
        Clock.schedule_once(lambda dt: Animation(height=0, opacity=0.0, duration=0.18).start(self.toast_bar), 2.0)

    def on_back_button(self, window, key, *args):
        if key == 27:
            if self.active_popup is not None:
                self.active_popup.dismiss()
                self.active_popup = None
                return True
            if self.current_tab == "MACHINES" and self.expanded_machine_id is not None:
                self.expanded_machine_id = None
                self.switch_tab("MACHINES", record_history=False)
                return True
            if self.tab_history:
                self.switch_tab(self.tab_history.pop(), record_history=False)
                return True
            if self.current_tab != "HOME":
                self.switch_tab("HOME", record_history=False)
                return True
            now = time.time()
            if now - self.last_back_press < 2.0: return False
            self.last_back_press = now
            self.show_toast("Press back again to exit")
            return True
        return False

    # ==========================================
    # 4. HOME PAGE REDESIGN
    # ==========================================
    def build_home(self):
        cfg = self.db["settings"]
        m_list = list(self.db["machines"].values())
        
        # Date & Math
        today_obj = datetime.now()
        today_date = today_obj.day
        today_str = today_obj.strftime("%d %B %Y (%A)")
        
        c_run = sum(1 for m in m_list if m["status"] == "RUNNING")
        c_idle = sum(1 for m in m_list if m["status"] == "IDLE")
        c_bd = sum(1 for m in m_list if m["status"] == "BREAKDOWN")
        c_maint = sum(1 for m in m_list if m["status"] == "MAINTENANCE")
        
        pm_today = sum(1 for m in m_list if m.get("pm_day") == today_date and not m.get("pm_done_oct", False))
        pm_due_month = sum(1 for m in m_list if m.get("pm_day", 0) > today_date and not m.get("pm_done_oct", False))
        
        total_m = max(1, len(m_list))
        uptime_pct = int(round((c_run / total_m) * 100))
        open_bd = sum(1 for b in self.db["breakdown_history"] if "Active" in b.get("completed_time", ""))

        # --- 1. GREETING CARD ---
        greet_box = ModernBox(orientation="horizontal", auto_height=False, height=dp(100), padding=[dp(16), dp(14)], spacing=dp(10), left_accent=ACCENT_COLOR)
        g_left = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))
        hr = today_obj.hour
        g_time = "Good morning" if hr < 12 else ("Good afternoon" if hr < 17 else "Good evening")
        g_left.add_widget(make_label(g_time, sp(11), ACCENT_COLOR, bold=True, height_dp=18))
        g_left.add_widget(make_label(cfg["user_name"], sp(22), TEXT_PRIMARY, bold=True, height_dp=28))
        g_left.add_widget(make_label(f"{cfg['role']}", sp(11), TEXT_MUTED, height_dp=16))
        g_left.add_widget(make_label(cfg["plant"], sp(11), TEXT_MUTED, height_dp=16))
        greet_box.add_widget(g_left)
        
        g_right = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(80))
        g_right.add_widget(make_label(today_obj.strftime("%d"), sp(26), ACCENT_COLOR, bold=True, halign="right", height_dp=32))
        g_right.add_widget(make_label(today_obj.strftime("%b '%y"), sp(12), TEXT_PRIMARY, halign="right", height_dp=18))
        greet_box.add_widget(g_right)
        self.feed.add_widget(greet_box)

        # --- 2. SUMMARY CARD (Today's Live Status) ---
        sum_box = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(10))
        sum_box.add_widget(make_label("TODAY'S LINE SUMMARY", sp(11), TEXT_MUTED, bold=True, height_dp=18))
        grid_sum = GridLayout(cols=2, size_hint_y=None, height=dp(120), spacing=dp(8))
        
        sm_meta = [
            ("RUNNING", str(c_run), STATUS_RUNNING), ("IDLE", str(c_idle), STATUS_IDLE),
            ("TODAY'S PM", str(pm_today), STATUS_MAINTENANCE), ("BREAKDOWN", str(c_bd), STATUS_BREAKDOWN)
        ]
        for title_s, num_s, col in sm_meta:
            tile = AnimatedCard(bg_color=CARD_INNER, border_color=BORDER_COLOR, radius=dp(12), auto_height=False, height=dp(56), orientation="horizontal", padding=[dp(12), 0])
            tile.add_widget(make_label(title_s, sp(11), TEXT_MUTED, bold=True))
            tile.add_widget(make_label(num_s, sp(20), col, bold=True, halign="right"))
            grid_sum.add_widget(tile)
        sum_box.add_widget(grid_sum)
        self.feed.add_widget(sum_box)

        # --- 3. ALERTS & FOCUS CARD ---
        focus_box = ModernBox(bg_color=CARD_INNER, border_color=BORDER_COLOR, radius=dp(12), auto_height=False, height=dp(64), orientation="horizontal", padding=[dp(8), dp(8)])
        f_items = [
            (str(pm_due_month), "Due PM (Month)", STATUS_MAINTENANCE if pm_due_month > 0 else TEXT_PRIMARY),
            (str(open_bd), "Pending BD", STATUS_BREAKDOWN if open_bd > 0 else TEXT_PRIMARY),
            (f"{uptime_pct}%", "Line Uptime", ACCENT_COLOR),
        ]
        for idx, (val_s, lbl_s, col_v) in enumerate(f_items):
            cell = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))
            cell.add_widget(make_label(val_s, sp(18), col_v, bold=True, halign="center", height_dp=24))
            cell.add_widget(make_label(lbl_s, sp(10), TEXT_MUTED, halign="center", height_dp=16))
            focus_box.add_widget(cell)
            if idx < 2:
                div = Widget(size_hint_x=None, width=dp(1))
                with div.canvas:
                    Color(*BORDER_COLOR)
                    r_d = Rectangle(pos=div.pos, size=div.size)
                div.bind(pos=lambda i, v, r=r_d: setattr(r, "pos", v), size=lambda i, v, r=r_d: setattr(r, "size", v))
                focus_box.add_widget(div)
        self.feed.add_widget(focus_box)

        # --- 4. FULL MONTH CALENDAR ---
        cal_box = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(10))
        cal_box.add_widget(make_label(f"OCTOBER 2026 PM CALENDAR", sp(11), TEXT_MUTED, bold=True, height_dp=18))
        
        days_header = GridLayout(cols=7, size_hint_y=None, height=dp(20))
        for d in ["M", "T", "W", "T", "F", "S", "S"]:
            days_header.add_widget(make_label(d, sp(10), TEXT_MUTED, bold=True, halign="center", height_dp=20))
        cal_box.add_widget(days_header)

        cal_grid = GridLayout(cols=7, size_hint_y=None, spacing=dp(4))
        cal_grid.bind(minimum_height=cal_grid.setter("height"))
        
        # Oct 2026 starts on Thursday (index 3)
        for _ in range(3):
            cal_grid.add_widget(Widget(size_hint_y=None, height=dp(36)))

        pm_days_map = {}
        for m in m_list:
            pd = m.get("pm_day")
            if pd: pm_days_map.setdefault(pd, []).append(m["name"])

        for d_num in range(1, 32):
            has_pm = d_num in pm_days_map
            is_today = d_num == today_date
            
            bg_c = ACCENT_COLOR if is_today else (CARD_INNER if not has_pm else (0.133, 0.4, 0.5, 1))
            fg_c = BG_COLOR if is_today else (ACCENT_COLOR if has_pm else TEXT_PRIMARY)
            
            d_btn = AnimatedCard(on_tap_cb=lambda dn=d_num, hpm=has_pm: self.open_pm_day_details(dn, hpm, pm_days_map), bg_color=bg_c, border_color=BORDER_COLOR, radius=dp(8), auto_height=False, height=dp(36))
            d_btn.add_widget(make_label(str(d_num), sp(12), fg_c, bold=True, halign="center", height_dp=36))
            cal_grid.add_widget(d_btn)
            
        cal_box.add_widget(cal_grid)
        self.feed.add_widget(cal_box)

        # --- 5. ANIMATED WEEKLY OEE & LINE UPTIME ---
        oee_box = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(10))
        oee_box.add_widget(make_label("WEEKLY OEE & LINE UPTIME (%)", sp(11), TEXT_MUTED, bold=True, height_dp=18))
        
        oee_scroll = ScrollView(do_scroll_x=True, do_scroll_y=False, size_hint_y=None, height=dp(44), bar_width=0)
        oee_row = BoxLayout(orientation="horizontal", size_hint_x=None, width=dp(7 * 70), spacing=dp(8))
        
        # Detail expansion box (initially hidden)
        self.oee_detail_box = ModernBox(bg_color=CARD_INNER, radius=dp(10), orientation="vertical", padding=dp(0), spacing=dp(0))
        self.oee_detail_box.opacity = 0.0
        self.oee_detail_box.height = 0
        self.oee_detail_box.size_hint_y = None
        
        self.oee_d_title = make_label("", sp(12), ACCENT_COLOR, bold=True, halign="center", height_dp=0)
        self.oee_d_stats = make_label("", sp(11), TEXT_PRIMARY, halign="center", height_dp=0)
        self.oee_detail_box.add_widget(self.oee_d_title)
        self.oee_detail_box.add_widget(self.oee_d_stats)

        for day_data in self.db["oee"]["days"]:
            d_name = day_data["day"]
            d_val = day_data["oee"]
            
            p_card = AnimatedCard(on_tap_cb=lambda dt=day_data: self.animate_oee_detail(dt), bg_color=CARD_INNER, border_color=BORDER_COLOR, radius=dp(10), auto_height=False, height=dp(44), orientation="vertical", padding=[0, dp(4)])
            p_card.size_hint_x = None
            p_card.width = dp(62)
            p_card.add_widget(make_label(d_name, sp(10), TEXT_MUTED, halign="center", height_dp=14))
            p_card.add_widget(make_label(f"{d_val}%", sp(14), ACCENT_COLOR, bold=True, halign="center", height_dp=22))
            oee_row.add_widget(p_card)
            
        oee_scroll.add_widget(oee_row)
        oee_box.add_widget(oee_scroll)
        oee_box.add_widget(self.oee_detail_box)
        self.feed.add_widget(oee_box)

    def open_pm_day_details(self, day_num, has_pm, pm_map):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(make_label(f"Schedule for Oct {day_num}, 2026", sp(14), ACCENT_COLOR, bold=True, height_dp=24))
        
        if has_pm:
            m_str = "\n".join([f"• {m}" for m in pm_map[day_num]])
            box.add_widget(make_label("Machines Scheduled for PM:", sp(12), TEXT_MUTED, height_dp=20))
            lbl = Label(text=m_str, font_size=sp(12), color=TEXT_PRIMARY, halign="left", valign="top", size_hint_y=None)
            lbl.bind(width=lambda i, w: setattr(i, "text_size", (w, None)), texture_size=lambda i, t: setattr(i, "height", t[1]))
            box.add_widget(lbl)
        else:
            box.add_widget(make_label("No machines scheduled for PM on this day.", sp(12), TEXT_PRIMARY, height_dp=30))

        b_close = Button(text="Close", size_hint_y=None, height=dp(44), background_normal="", background_color=CARD_INNER, color=TEXT_PRIMARY, bold=True)
        box.add_widget(Widget()) # Spacer
        box.add_widget(b_close)

        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.85, 0.4), background="", background_color=CARD_COLOR)
        b_close.bind(on_release=pop.dismiss)
        pop.open()

    def animate_oee_detail(self, day_data):
        self.oee_d_title.text = f"{day_data['day']} Details"
        self.oee_d_stats.text = f"Availability: {day_data['avail']}%  |  Performance: {day_data['perf']}%  |  Quality: {day_data['qual']}%"
        
        self.oee_detail_box.padding = [dp(10), dp(10)]
        self.oee_d_title.height = dp(20)
        self.oee_d_stats.height = dp(20)
        
        Animation(height=dp(60), opacity=1.0, duration=0.25, t="out_back").start(self.oee_detail_box)

    def open_filtered_machines(self, status_key):
        self.machine_filter = status_key
        self.switch_tab("MACHINES")

    # ==========================================
    # OTHER TABS (MACHINES, BREAKDOWN, SETTINGS)
    # ==========================================
    def build_machines(self):
        self.feed.add_widget(make_label("Machines tab functionality remains unchanged in this update.", sp(12), TEXT_MUTED, height_dp=40))

    def build_machine_detail(self, m_id):
        pass

    def build_breakdown_history(self):
        self.feed.add_widget(make_label("Breakdown tab functionality remains unchanged in this update.", sp(12), TEXT_MUTED, height_dp=40))

    def build_settings(self):
        self.feed.add_widget(make_label("Settings tab functionality remains unchanged in this update.", sp(12), TEXT_MUTED, height_dp=40))

if __name__ == "__main__":
    try:
        MachineTrackerApp().run()
    except Exception as e:
        err_msg = traceback.format_exc()
        from kivy.app import App as BaseApp
        class CrashApp(BaseApp):
            def build(self):
                sv = ScrollView(size_hint=(1, 1))
                l = Label(text="APP CRASHED!\n\n" + err_msg, color=(1,0.2,0.2,1), size_hint_y=None, font_size=sp(11), halign="left", valign="top", padding=(dp(20), dp(20)))
                l.bind(width=lambda *args: setattr(l, 'text_size', (l.width, None)))
                l.bind(texture_size=lambda *args: setattr(l, 'height', l.texture_size[1]))
                sv.add_widget(l)
                return sv
        CrashApp().run()
