import traceback
import os
import json
import time
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
STATUS_TINT_MAP = {
    "RUNNING": (0.063, 0.725, 0.506, 0.16),
    "IDLE": (0.392, 0.455, 0.545, 0.16),
    "BREAKDOWN": (0.957, 0.247, 0.369, 0.16),
    "MAINTENANCE": (0.961, 0.620, 0.043, 0.16),
}

FONT_TITLE, FONT_SEC_LABEL, FONT_CARD_TITLE = sp(19), sp(11), sp(14)
FONT_BODY, FONT_CAPTION, FONT_BIG_NUM = sp(12), sp(10), sp(22)
PAD_SCREEN, RADIUS_BOX, RADIUS_INNER = dp(14), dp(16), dp(12)

FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "MaterialIcons-Regular.ttf")
if os.path.exists(FONT_PATH):
    LabelBase.register(name="Icons", fn_regular=FONT_PATH)
    ICON_FONT = "Icons"
    ICONS = {"home": "\ue88a", "machines": "\ue30a", "breakdown": "\ue889", "settings": "\ue8b8", "running": "\ue037", "idle": "\ue034", "breakdown_icon": "\ue002", "maintenance": "\ue869", "check": "\ue5ca", "calendar": "\ue878", "report": "\ue8b2", "inventory": "\ue179", "handover": "\ue873"}
else:
    ICON_FONT = "Roboto"
    ICONS = {"home": "H", "machines": "M", "breakdown": "B", "settings": "S", "running": "R", "idle": "I", "breakdown_icon": "!", "maintenance": "M", "check": "OK", "calendar": "C", "report": "R", "inventory": "S", "handover": "N"}

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
        self.on_tap_cb, self.orig_bg = on_tap_cb, list(self.bg_rgba)
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
    def __init__(self, icon_char, title_str, on_tap, **kwargs):
        super().__init__(orientation="vertical", size_hint_x=1, padding=[0, dp(4)], spacing=dp(2), **kwargs)
        self.on_tap_cb = on_tap
        self.pill = BoxLayout(size_hint=(None, None), size=(dp(54), dp(26)), pos_hint={"center_x": 0.5})
        with self.pill.canvas.before:
            self.p_col = Color(0, 0, 0, 0)
            self.p_rect = RoundedRectangle(pos=self.pill.pos, size=self.pill.size, radius=[dp(13)])
        self.pill.bind(pos=lambda i, v: setattr(self.p_rect, "pos", v), size=lambda i, v: setattr(self.p_rect, "size", v))
        self.ic = Label(text=icon_char, font_name=ICON_FONT, font_size=dp(17), color=TEXT_MUTED)
        self.pill.add_widget(self.ic)
        self.tx = Label(text=title_str, font_size=sp(10), color=TEXT_MUTED, bold=True)
        self.add_widget(self.pill)
        self.add_widget(self.tx)
    def on_release(self):
        Animation(opacity=0.6, duration=0.06).start(self)
        Animation(opacity=1.0, duration=0.15).start(self)
        self.on_tap_cb()
    def set_active(self, active):
        self.p_col.rgba = ACCENT_TINT if active else (0, 0, 0, 0)
        self.ic.color = ACCENT_COLOR if active else TEXT_MUTED
        self.tx.color = ACCENT_COLOR if active else TEXT_MUTED

class MachineTrackerApp(App):
    def build(self):
        self.title = "Renata PLC Smart Eng-Ops"
        self.data_file = os.path.join(self.user_data_dir, "renata_sagar_v25.json")
        self.load_data()

        self.current_tab = "HOME"
        self.tab_history = []
        self.active_popup = None
        self.last_back_press = 0.0

        self.selected_cal_day = datetime.now().day
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
        
        # PADDING UPDATED HERE: dp(50) for TOP padding to fix layout overlap with Notch
        self.feed = BoxLayout(orientation="vertical", size_hint_x=1, size_hint_y=None, padding=[dp(14), dp(50), dp(14), dp(28)], spacing=dp(14))
        self.feed.bind(minimum_height=self.feed.setter("height"))
        self.scroll.add_widget(self.feed)
        self.root_box.add_widget(self.scroll)

        self.nav_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(58), padding=[dp(6), 0])
        with self.nav_bar.canvas.before:
            Color(*CARD_COLOR)
            self.nb_rect = Rectangle(pos=self.nav_bar.pos, size=self.nav_bar.size)
            Color(*BORDER_COLOR)
            self.nb_line = Line(points=[0, dp(58), 1000, dp(58)], width=1)
        self.nav_bar.bind(pos=lambda i, v: (setattr(self.nb_rect, "pos", v), setattr(self.nb_line, "points", [i.x, i.top, i.right, i.top])), size=lambda i, v: (setattr(self.nb_rect, "size", v), setattr(self.nb_line, "points", [i.x, i.top, i.right, i.top])))

        self.nav_items = {
            "HOME": NavItem(ICONS["home"], "Home", lambda: self.switch_tab("HOME")),
            "MACHINES": NavItem(ICONS["machines"], "Machines", lambda: self.switch_tab("MACHINES")),
            "BREAKDOWN": NavItem(ICONS["breakdown"], "History", lambda: self.switch_tab("BREAKDOWN")),
            "SETTINGS": NavItem(ICONS["settings"], "Settings", lambda: self.switch_tab("SETTINGS")),
        }
        for item in self.nav_items.values(): self.nav_bar.add_widget(item)
        self.root_box.add_widget(self.nav_bar)

        self.switch_tab("HOME", record_history=False)
        return self.root_box

    def make_status_pill(self, text_str, status_key):
        col, tint = STATUS_MAP.get(status_key, ACCENT_COLOR), STATUS_TINT_MAP.get(status_key, ACCENT_TINT)
        pill = BoxLayout(size_hint=(None, None), size=(dp(92), dp(24)), padding=[dp(8), 0], spacing=dp(5))
        with pill.canvas.before:
            Color(*tint)
            r = RoundedRectangle(pos=pill.pos, size=pill.size, radius=[dp(12)])
        pill.bind(pos=lambda i, v: setattr(r, "pos", v), size=lambda i, v: setattr(r, "size", v))
        dot = Widget(size_hint=(None, None), size=(dp(6), dp(6)), pos_hint={"center_y": 0.5})
        with dot.canvas:
            Color(*col)
            el = Ellipse(pos=dot.pos, size=dot.size)
        dot.bind(pos=lambda i, v: setattr(el, "pos", v), size=lambda i, v: setattr(el, "size", v))
        pill.add_widget(dot)
        pill.add_widget(Label(text=text_str, font_size=sp(10), bold=True, color=col, halign="center", valign="middle"))
        return pill

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    self.db = json.load(f)
                if "machine_order" in self.db: return
        except Exception: pass

        self.db = {
            "settings": {
                "user_name": "SAGAR ALI",
                "role": "Junior Engineer",
                "shift": "Sterile Secondary Packaging",
                "plant": "Renata PLC (Kashor Site)",
                "address": "Kashor, Hobirbari, Bhaluka, Mymensingh"
            },
            "oee": {
                "days": [
                    {"day": "Sat", "avail": 94, "perf": 91, "qual": 99, "oee": 85},
                    {"day": "Sun", "avail": 97, "perf": 93, "qual": 100, "oee": 90},
                    {"day": "Mon", "avail": 92, "perf": 88, "qual": 99, "oee": 80},
                    {"day": "Tue", "avail": 95, "perf": 90, "qual": 98, "oee": 84},
                    {"day": "Wed", "avail": 88, "perf": 85, "qual": 99, "oee": 74},
                    {"day": "Thu", "avail": 96, "perf": 92, "qual": 100, "oee": 88},
                    {"day": "Fri", "avail": 90, "perf": 89, "qual": 97, "oee": 78}
                ]
            },
            "machine_order": [], "machines": {},
            "breakdown_history": [
                {
                    "id": "BD-101", "machine_id": "K02PR-106", "machine_name": "Ampoule Labeling 01",
                    "date_time": "19 Oct 2026, 09:30 AM", "completed_time": "19 Oct 2026, 10:15 AM",
                    "issue": "Label gap optical sensor false trigger at >320 RPM",
                    "rca": "Adhesive residue on optical fiber head",
                    "corrective": "Cleaned optical lens with IPA & recalibrated threshold",
                    "parts_changed": "Yes", "parts_desc": "Optical Fiber Head x1",
                    "param_changed": "Yes", "param_desc": "Sensitivity threshold 62% -> 75%",
                    "work_desc": "Dismantled sensor bracket, solvent cleaned lens.",
                    "responsible": "Sagar Ali & Md. Tanvir"
                }
            ]
        }
        
        initial_sls = ["Brevetti", "Korber", "Light Inspection 01", "Light Inspection 02", "PDLD", "Ampoule Labeling 01", "Conveyor Belt 04", "Blister & Cartooning", "Conveyor Belt 01", "Checkweigher 01", "Vail Labeling 02", "Conveyor Belt 03", "Washing and Drying", "Vail Labeling 01", "Conveyor Belt 02", "IFC Printer", "NKP 01", "NKP 02"]
        ids = ["095", "089", "137", "138", "134", "106", "133", "111", "130", "143", "108", "132", "135", "107", "131", "136", "128", "129"]

        today_d = datetime.now().day
        for idx, nm in enumerate(initial_sls):
            mid = f"K02PR-{ids[idx]}"
            self.db["machine_order"].append(mid)
            st = "BREAKDOWN" if idx == 5 else ("MAINTENANCE" if idx == 12 else ("IDLE" if idx in (6, 14) else "RUNNING"))
            self.db["machines"][mid] = {
                "sl": idx + 1, "name": nm, "id": mid, "status": st,
                "product": "Standard Batch", "batch": "B26-1041", "pm_day": today_d if idx in (0,7) else 23, "pm_done_oct": False,
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

    def build_home(self):
        cfg = self.db["settings"]
        m_list = list(self.db["machines"].values())
        
        today_obj = datetime.now()
        today_date = today_obj.day
        
        c_run = sum(1 for m in m_list if m["status"] == "RUNNING")
        c_idle = sum(1 for m in m_list if m["status"] == "IDLE")
        c_bd = sum(1 for m in m_list if m["status"] == "BREAKDOWN")
        c_off = sum(1 for m in m_list if m["status"] in ("IDLE", "BREAKDOWN", "MAINTENANCE"))
        
        pm_today = sum(1 for m in m_list if m.get("pm_day") == today_date and not m.get("pm_done_oct", False))
        pm_due_month = sum(1 for m in m_list if m.get("pm_day", 0) > today_date and not m.get("pm_done_oct", False))
        
        total_m = max(1, len(m_list))
        uptime_pct = int(round((c_run / total_m) * 100))

        # --- 1. NEW GREETING CARD ---
        greet_box = ModernBox(orientation="vertical", auto_height=False, height=dp(135), padding=[dp(16), dp(12)], spacing=dp(2), left_accent=ACCENT_COLOR)
        
        hr = today_obj.hour
        g_time = "Good morning!" if hr < 12 else ("Good afternoon!" if hr < 17 else "Good evening!")

        top_row = BoxLayout(size_hint_y=None, height=dp(20))
        top_row.add_widget(make_label(g_time, sp(12), ACCENT_COLOR, bold=True, height_dp=20))
        top_row.add_widget(make_label(f"Date: {today_obj.strftime('%d %b %Y')}", sp(13), ACCENT_COLOR, bold=True, halign="right", height_dp=20))
        greet_box.add_widget(top_row)
        
        greet_box.add_widget(make_label(cfg["user_name"], sp(19), TEXT_PRIMARY, bold=True, height_dp=26))
        greet_box.add_widget(make_label(cfg["role"], sp(11), TEXT_MUTED, height_dp=16))
        greet_box.add_widget(make_label(cfg["shift"], sp(11), TEXT_MUTED, height_dp=16))
        greet_box.add_widget(make_label(cfg["plant"], sp(11), TEXT_MUTED, height_dp=16))
        greet_box.add_widget(make_label(cfg["address"], sp(10), TEXT_MUTED, height_dp=15))
        self.feed.add_widget(greet_box)

        # --- 2. SUMMARY CARD (Interactive Drill-Downs) ---
        sum_box = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(10))
        sum_box.add_widget(make_label("TODAY'S LINE SUMMARY", sp(11), TEXT_MUTED, bold=True, height_dp=18))
        grid_sum = GridLayout(cols=2, size_hint_x=1, size_hint_y=None, height=dp(180), spacing=dp(8))
        
        sm_meta = [
            ("RUNNING", str(c_run), STATUS_RUNNING, "RUNNING"),
            ("IDLE", str(c_idle), STATUS_IDLE, "IDLE"),
            ("PM (Today)", str(pm_today), STATUS_MAINTENANCE, "PM_TODAY"),
            ("BREAKDOWN", str(c_bd), STATUS_BREAKDOWN, "BREAKDOWN"),
            ("OFF MACHINES", str(c_off), STATUS_IDLE, "OFF_MACHINES"),
            ("LINE UPTIME", f"{uptime_pct}%", ACCENT_COLOR, "UPTIME")
        ]
        for title_s, num_s, col, st_val in sm_meta:
            tile = AnimatedCard(on_tap_cb=lambda sv=st_val, ts=title_s: self.open_summary_drilldown(sv, ts), bg_color=CARD_INNER, border_color=BORDER_COLOR, radius=dp(12), auto_height=False, height=dp(54), orientation="horizontal", padding=[dp(12), 0])
            tile.add_widget(make_label(title_s, sp(11), TEXT_MUTED, bold=True))
            tile.add_widget(make_label(num_s, sp(18), col, bold=True, halign="right"))
            grid_sum.add_widget(tile)
        sum_box.add_widget(grid_sum)
        self.feed.add_widget(sum_box)

        # --- 3. FOCUS CARD (Today's PM Due, Full Month Due, Breakdown) ---
        focus_box = ModernBox(bg_color=CARD_INNER, border_color=BORDER_COLOR, radius=dp(12), auto_height=False, height=dp(64), orientation="horizontal", padding=[dp(8), dp(8)])
        f_items = [
            (str(pm_today), "Today's PM Due", STATUS_MAINTENANCE if pm_today > 0 else TEXT_PRIMARY, "PM_TODAY"),
            (str(pm_due_month), "Full Month Due", STATUS_MAINTENANCE if pm_due_month > 0 else TEXT_PRIMARY, "PM_MONTH"),
            (str(c_bd), "Breakdown", STATUS_BREAKDOWN if c_bd > 0 else TEXT_PRIMARY, "BREAKDOWN"),
        ]
        for idx, (val_s, lbl_s, col_v, st_val) in enumerate(f_items):
            cell = AnimatedCard(on_tap_cb=lambda sv=st_val, ts=lbl_s: self.open_summary_drilldown(sv, ts), bg_color=CARD_INNER, border_color=CARD_INNER, radius=dp(8), orientation="vertical", size_hint_x=1, spacing=dp(2))
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

        # --- 4. FULL CALENDAR ---
        cal_box = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(10))
        cal_box.add_widget(make_label("OCTOBER 2026 PM SCHEDULE CALENDAR", sp(11), TEXT_MUTED, bold=True, height_dp=18))
        
        days_header = GridLayout(cols=7, size_hint_y=None, height=dp(20))
        for d in ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]:
            days_header.add_widget(make_label(d, sp(9), TEXT_MUTED, bold=True, halign="center", height_dp=20))
        cal_box.add_widget(days_header)

        cal_grid = GridLayout(cols=7, size_hint_y=None, spacing=dp(4))
        cal_grid.bind(minimum_height=cal_grid.setter("height"))
        
        for _ in range(5): cal_grid.add_widget(Widget(size_hint_y=None, height=dp(36)))

        pm_days_map = {}
        for m in m_list:
            pd = m.get("pm_day")
            if pd: pm_days_map.setdefault(pd, []).append(m)

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

        # --- 5. WEEKLY OEE & LINE UPTIME (Starts Saturday) ---
        oee_box = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(10))
        oee_box.add_widget(make_label("WEEKLY OEE & LINE UPTIME (%) (Starts Saturday)", sp(11), TEXT_MUTED, bold=True, height_dp=18))
        
        oee_scroll = ScrollView(do_scroll_x=True, do_scroll_y=False, size_hint_y=None, height=dp(44), bar_width=0)
        oee_row = BoxLayout(orientation="horizontal", size_hint_x=None, width=dp(7 * 70), spacing=dp(8))
        
        self.oee_detail_box = ModernBox(bg_color=CARD_INNER, radius=dp(10), orientation="vertical", padding=dp(0), spacing=dp(0))
        self.oee_detail_box.opacity, self.oee_detail_box.height, self.oee_detail_box.size_hint_y = 0.0, 0, None
        self.oee_d_title = make_label("", sp(12), ACCENT_COLOR, bold=True, halign="center", height_dp=0)
        self.oee_d_stats = make_label("", sp(11), TEXT_PRIMARY, halign="center", height_dp=0)
        self.oee_detail_box.add_widget(self.oee_d_title)
        self.oee_detail_box.add_widget(self.oee_d_stats)

        for day_data in self.db["oee"]["days"]:
            p_card = AnimatedCard(on_tap_cb=lambda dt=day_data: self.animate_oee_detail(dt), bg_color=CARD_INNER, border_color=BORDER_COLOR, radius=dp(10), auto_height=False, height=dp(44), orientation="vertical", padding=[0, dp(4)])
            p_card.size_hint_x, p_card.width = None, dp(62)
            p_card.add_widget(make_label(day_data["day"], sp(10), TEXT_MUTED, halign="center", height_dp=14))
            p_card.add_widget(make_label(f"{day_data['oee']}%", sp(14), ACCENT_COLOR, bold=True, halign="center", height_dp=22))
            oee_row.add_widget(p_card)
            
        oee_scroll.add_widget(oee_row)
        oee_box.add_widget(oee_scroll)
        oee_box.add_widget(self.oee_detail_box)
        self.feed.add_widget(oee_box)

    def open_summary_drilldown(self, status_val, title_str):
        if status_val == "UPTIME": return
        m_list = list(self.db["machines"].values())
        if status_val == "PM_TODAY":
            today_date = datetime.now().day
            matched = [m for m in m_list if m.get("pm_day") == today_date and not m.get("pm_done_oct", False)]
        elif status_val == "PM_MONTH":
            today_date = datetime.now().day
            matched = [m for m in m_list if m.get("pm_day", 0) > today_date and not m.get("pm_done_oct", False)]
        elif status_val == "OFF_MACHINES":
            matched = [m for m in m_list if m["status"] in ("IDLE", "BREAKDOWN", "MAINTENANCE")]
        elif status_val == "BREAKDOWN":
            matched = self.db["breakdown_history"]
        else:
            matched = [m for m in m_list if m["status"] == status_val]
        
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(make_label(f"Machines: {title_str} ({len(matched)})", sp(14), ACCENT_COLOR, bold=True, height_dp=24))
        
        scroll_m = ScrollView(size_hint=(1, 1))
        m_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        m_box.bind(minimum_height=m_box.setter("height"))
        
        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.9, 0.6), background="", background_color=CARD_COLOR)

        if not matched:
            m_box.add_widget(make_label("No machines found.", sp(12), TEXT_MUTED, height_dp=30))
        else:
            if status_val == "BREAKDOWN":
                for b in matched:
                    c = AnimatedCard(on_tap_cb=lambda bd=b, p=pop: (self.open_breakdown_detail_popup(bd), p.dismiss()), bg_color=CARD_INNER, radius=dp(8), auto_height=False, height=dp(58), padding=[dp(10), dp(6)], orientation="vertical", left_accent=STATUS_BREAKDOWN)
                    c.add_widget(make_label(f"{b['machine_name']} ({b['machine_id']})", sp(12), TEXT_PRIMARY, bold=True, height_dp=20))
                    c.add_widget(make_label(f"Issue: {b['issue']} · Tap for details", sp(10), STATUS_BREAKDOWN, height_dp=18))
                    m_box.add_widget(c)
            else:
                for mat in matched:
                    c = ModernBox(bg_color=CARD_INNER, radius=dp(8), auto_height=False, height=dp(42), padding=[dp(10), 0], orientation="horizontal")
                    c.add_widget(make_label(f"{mat['name']} ({mat['id']})", sp(12), TEXT_PRIMARY, bold=True, height_dp=42))
                    if status_val in ("PM_TODAY", "PM_MONTH"):
                        btn_done = Button(text="Mark Done", size_hint=(None, None), size=(dp(80), dp(28)), pos_hint={"center_y": 0.5}, font_size=sp(10), bold=True, background_normal="", background_color=STATUS_RUNNING, color=BG_COLOR)
                        btn_done.bind(on_release=lambda x, mid=mat["id"], p=pop: (self.mark_pm_complete(mid), p.dismiss()))
                        c.add_widget(btn_done)
                    else:
                        c.add_widget(self.make_status_pill(mat["status"], mat["status"]))
                    m_box.add_widget(c)
                
        scroll_m.add_widget(m_box)
        box.add_widget(scroll_m)

        b_close = Button(text="Close", size_hint_y=None, height=dp(42), background_normal="", background_color=CARD_INNER, color=TEXT_PRIMARY, bold=True)
        b_close.bind(on_release=pop.dismiss)
        box.add_widget(b_close)
        self.open_tracked_popup(pop)

    def open_pm_day_details(self, day_num, has_pm, pm_map):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(make_label(f"PM Schedule for Oct {day_num}, 2026", sp(14), ACCENT_COLOR, bold=True, height_dp=24))
        
        scroll_m = ScrollView(size_hint=(1, 1))
        m_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        m_box.bind(minimum_height=m_box.setter("height"))

        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.9, 0.6), background="", background_color=CARD_COLOR)

        if has_pm:
            for mach in pm_map[day_num]:
                is_done = mach.get("pm_done_oct", False)
                row = ModernBox(bg_color=CARD_INNER, radius=dp(8), auto_height=False, height=dp(48), padding=[dp(10), 0], orientation="horizontal")
                info = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))
                info.add_widget(make_label(f"{mach['name']} ({mach['id']})", sp(12), TEXT_PRIMARY, bold=True, height_dp=22))
                info.add_widget(make_label("Completed" if is_done else "Pending Maintenance", sp(10), STATUS_RUNNING if is_done else STATUS_MAINTENANCE, height_dp=16))
                row.add_widget(info)
                
                if not is_done:
                    btn_comp = Button(text="Complete", size_hint=(None, None), size=(dp(85), dp(32)), pos_hint={"center_y": 0.5}, font_size=sp(10), bold=True, background_normal="", background_color=STATUS_RUNNING, color=BG_COLOR)
                    btn_comp.bind(on_release=lambda x, mid=mach["id"], p=pop: (self.mark_pm_complete(mid), p.dismiss()))
                    row.add_widget(btn_comp)
                m_box.add_widget(row)
        else:
            m_box.add_widget(make_label("No maintenance scheduled for this date.", sp(12), TEXT_MUTED, height_dp=30))

        scroll_m.add_widget(m_box)
        box.add_widget(scroll_m)

        b_close = Button(text="Close", size_hint_y=None, height=dp(42), background_normal="", background_color=CARD_INNER, color=TEXT_PRIMARY, bold=True)
        b_close.bind(on_release=pop.dismiss)
        box.add_widget(b_close)
        self.open_tracked_popup(pop)

    def mark_pm_complete(self, m_id):
        self.db["machines"][m_id]["pm_done_oct"] = True
        self.save_data()
        self.show_toast(f"PM completed for {m_id}!")
        self.switch_tab("HOME", record_history=False)

    def animate_oee_detail(self, day_data):
        self.oee_d_title.text = f"Day: {day_data['day']} Performance Pulse"
        self.oee_d_stats.text = f"Availability: {day_data['avail']}%  |  Performance: {day_data['perf']}%  |  Quality: {day_data['qual']}%"
        self.oee_detail_box.padding = [dp(10), dp(10)]
        self.oee_d_title.height, self.oee_d_stats.height = dp(20), dp(20)
        Animation(height=dp(60), opacity=1.0, duration=0.25, t="out_back").start(self.oee_detail_box)

    def open_breakdown_detail_popup(self, b_data):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        box.add_widget(make_label(f"Breakdown Details: {b_data['machine_name']}", sp(14), STATUS_BREAKDOWN, bold=True, height_dp=24))
        
        scroll_m = ScrollView(size_hint=(1, 1))
        m_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4))
        m_box.bind(minimum_height=m_box.setter("height"))
        
        details = [
            f"Machine ID: {b_data['machine_id']}", f"Date & Time: {b_data['date_time']}",
            f"Issue: {b_data['issue']}", f"Root Cause (RCA): {b_data['rca']}",
            f"Corrective Action: {b_data['corrective']}", f"Parts Changed?: {b_data['parts_changed']} ({b_data['parts_desc']})",
            f"Parameter Change?: {b_data['param_changed']} ({b_data['param_desc']})", f"Work Description: {b_data['work_desc']}",
            f"Completed Time: {b_data['completed_time']}", f"Responsible: {b_data['responsible']}"
        ]
        for d in details: m_box.add_widget(make_label(d, sp(11), TEXT_PRIMARY, height_dp=22))
            
        scroll_m.add_widget(m_box)
        box.add_widget(scroll_m)

        b_close = Button(text="Close", size_hint_y=None, height=dp(42), background_normal="", background_color=CARD_INNER, color=TEXT_PRIMARY, bold=True)
        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.92, 0.75), background="", background_color=CARD_COLOR)
        b_close.bind(on_release=pop.dismiss)
        box.add_widget(b_close)
        self.open_tracked_popup(pop)

    def open_tracked_popup(self, pop):
        self.active_popup = pop
        pop.bind(on_dismiss=lambda *a: setattr(self, "active_popup", None))
        pop.open()

    def build_machines(self):
        hdr = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        b_back = Button(text="<- Home", size_hint=(None, None), size=(dp(72), dp(34)), font_size=sp(10), bold=True, background_normal="", background_color=CARD_COLOR, color=ACCENT_COLOR)
        b_back.bind(on_release=lambda x: self.go_back_step())
        hdr.add_widget(b_back)
        hdr.add_widget(make_label("MACHINES DIRECTORY", sp(11), TEXT_MUTED, bold=True, height_dp=38))
        self.feed.add_widget(hdr)
        for mid in self.db["machine_order"]:
            m = self.db["machines"][mid]
            c = ModernBox(bg_color=CARD_INNER, radius=dp(10), auto_height=False, height=dp(44), padding=[dp(12), 0], orientation="horizontal", left_accent=STATUS_MAP.get(m["status"], ACCENT_COLOR))
            c.add_widget(make_label(f"{m['name']} ({mid})", sp(12), TEXT_PRIMARY, bold=True, height_dp=44))
            c.add_widget(self.make_status_pill(m["status"], m["status"]))
            self.feed.add_widget(c)

    def build_breakdown_history(self):
        hdr = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        b_back = Button(text="<- Home", size_hint=(None, None), size=(dp(72), dp(34)), font_size=sp(10), bold=True, background_normal="", background_color=CARD_COLOR, color=ACCENT_COLOR)
        b_back.bind(on_release=lambda x: self.go_back_step())
        hdr.add_widget(b_back)
        hdr.add_widget(make_label("BREAKDOWN LIST & DETAILS", sp(11), TEXT_MUTED, bold=True, height_dp=36))
        self.feed.add_widget(hdr)
        
        if not self.db["breakdown_history"]:
            self.feed.add_widget(make_label("No breakdowns logged.", sp(12), TEXT_MUTED, height_dp=30))
        else:
            for b in self.db["breakdown_history"]:
                card = AnimatedCard(
                    on_tap_cb=lambda bd=b: self.open_breakdown_detail_popup(bd),
                    bg_color=CARD_INNER, border_color=BORDER_COLOR, radius=dp(10),
                    auto_height=False, height=dp(58), orientation="vertical",
                    padding=[dp(12), dp(6)], spacing=dp(2), left_accent=STATUS_BREAKDOWN
                )
                card.add_widget(make_label(f"{b['machine_name']} ({b['machine_id']})", sp(12), TEXT_PRIMARY, bold=True, height_dp=20))
                card.add_widget(make_label(f"Issue: {b['issue']} · Tap for details", sp(10), STATUS_BREAKDOWN, height_dp=18))
                self.feed.add_widget(card)

    def build_settings(self):
        hdr = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        b_back = Button(text="<- Home", size_hint=(None, None), size=(dp(72), dp(34)), font_size=sp(10), bold=True, background_normal="", background_color=CARD_COLOR, color=ACCENT_COLOR)
        b_back.bind(on_release=lambda x: self.go_back_step())
        hdr.add_widget(b_back)
        hdr.add_widget(make_label("SETTINGS", sp(11), TEXT_MUTED, bold=True, height_dp=36))
        self.feed.add_widget(hdr)
        self.feed.add_widget(make_label("Settings configuration active.", sp(12), TEXT_PRIMARY, height_dp=30))


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
