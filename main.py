import os
import json
import time
import traceback
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

FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "MaterialIcons-Regular.ttf")
if os.path.exists(FONT_PATH):
    LabelBase.register(name="Icons", fn_regular=FONT_PATH)
    ICON_FONT = "Icons"
    ICONS = {
        "home": "\ue88a", "machines": "\ue30a", "breakdown": "\ue889", "settings": "\ue8b8",
        "running": "\ue037", "idle": "\ue034", "breakdown_icon": "\ue002", "maintenance": "\ue869",
        "check": "\ue5ca", "calendar": "\ue878", "chart": "\ue26b"
    }
else:
    ICON_FONT = "Roboto"
    ICONS = {
        "home": "H", "machines": "M", "breakdown": "B", "settings": "S",
        "running": "R", "idle": "I", "breakdown_icon": "!", "maintenance": "M",
        "check": "OK", "calendar": "C", "chart": "G"
    }


def make_label(text, font_size=sp(12), color=TEXT_PRIMARY, bold=False, halign="left", height_dp=22):
    lbl = Label(
        text=str(text), font_size=font_size, color=color, bold=bold,
        halign=halign, valign="middle", size_hint_y=None, height=dp(height_dp)
    )
    lbl.bind(size=lbl.setter("text_size"))
    return lbl


class ModernBox(BoxLayout):
    def __init__(self, bg_color=CARD_COLOR, border_color=BORDER_COLOR, radius=dp(16), left_accent=None, auto_height=True, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_x, self.size_hint_y = 1, None
        if auto_height:
            self.bind(minimum_height=self.setter("height"))
        self.bg_rgba, self.bd_rgba, self.rad, self.left_accent = list(bg_color), list(border_color), radius, left_accent
        with self.canvas.before:
            self.c_bg = Color(*self.bg_rgba)
            self.r_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.rad])
            self.c_bd = Color(*self.bd_rgba)
            self.l_bd = Line(rounded_rectangle=(self.x, self.y, max(1, self.width), max(1, self.height), self.rad), width=1.1)
            if self.left_accent:
                self.c_ac = Color(*self.left_accent)
                self.r_ac = RoundedRectangle(pos=(self.x + dp(2), self.y + dp(10)), size=(dp(4), max(dp(10), self.height - dp(20))), radius=[dp(2)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *args):
        self.r_bg.pos, self.r_bg.size = self.pos, self.size
        self.l_bd.rounded_rectangle = (self.x, self.y, max(1, self.width), max(1, self.height), self.rad)
        if self.left_accent:
            self.r_ac.pos, self.r_ac.size = (self.x + dp(2), self.y + dp(10)), (dp(4), max(dp(10), self.height - dp(20)))


class AnimatedCard(ButtonBehavior, ModernBox):
    def __init__(self, on_tap_cb=None, **kwargs):
        super().__init__(**kwargs)
        self.on_tap_cb, self.orig_bg = on_tap_cb, list(self.bg_rgba)

    def on_press(self):
        self.c_bg.rgba = CARD_ACTIVE
        Animation(opacity=0.80, duration=0.06).start(self)

    def on_release(self):
        Animation(opacity=1.0, duration=0.16, t="out_quad").start(self)
        Clock.schedule_once(lambda dt: setattr(self.c_bg, "rgba", self.orig_bg), 0.10)
        if self.on_tap_cb:
            Clock.schedule_once(lambda dt: self.on_tap_cb(), 0.06)


class NavItem(ButtonBehavior, BoxLayout):
    def __init__(self, icon_char, title_str, on_tap, **kwargs):
        super().__init__(orientation="vertical", size_hint_x=1, padding=[0, dp(4)], spacing=dp(2), **kwargs)
        self.on_tap_cb = on_tap
        self.pill = BoxLayout(size_hint=(None, None), size=(dp(56), dp(26)), pos_hint={"center_x": 0.5})
        with self.pill.canvas.before:
            self.p_col = Color(0, 0, 0, 0)
            self.p_rect = RoundedRectangle(pos=self.pill.pos, size=self.pill.size, radius=[dp(13)])
        self.pill.bind(pos=lambda i, v: setattr(self.p_rect, "pos", v), size=lambda i, v: setattr(self.p_rect, "size", v))
        self.ic = Label(text=icon_char, font_name=ICON_FONT, font_size=dp(18), color=TEXT_MUTED)
        self.pill.add_widget(self.ic)
        self.tx = Label(text=title_str, font_size=sp(10), color=TEXT_MUTED, bold=True)
        self.add_widget(self.pill)
        self.add_widget(self.tx)

    def on_release(self):
        Animation(opacity=0.5, duration=0.06).start(self)
        Animation(opacity=1.0, duration=0.18).start(self)
        self.on_tap_cb()

    def set_active(self, active):
        self.p_col.rgba = ACCENT_TINT if active else (0, 0, 0, 0)
        self.ic.color = ACCENT_COLOR if active else TEXT_MUTED
        self.tx.color = ACCENT_COLOR if active else TEXT_MUTED


class MachineTrackerApp(App):
    def build(self):
        self.title = "Renata PLC Smart Eng-Ops"
        self.data_file = os.path.join(self.user_data_dir, "renata_sagar_v20.json")
        self.load_data()

        self.current_tab = "HOME"
        self.tab_history = []
        self.active_popup = None
        self.last_back_press = 0.0
        self.selected_oee_day = None
        self.machine_filter = "ALL"

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

        self.nav_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(58), padding=[dp(6), 0])
        with self.nav_bar.canvas.before:
            Color(*CARD_COLOR)
            self.nb_rect = Rectangle(pos=self.nav_bar.pos, size=self.nav_bar.size)
            Color(*BORDER_COLOR)
            self.nb_line = Line(points=[0, dp(58), 1000, dp(58)], width=1)
        self.nav_bar.bind(
            pos=lambda i, v: (setattr(self.nb_rect, "pos", v), setattr(self.nb_line, "points", [i.x, i.top, i.right, i.top])),
            size=lambda i, v: (setattr(self.nb_rect, "size", v), setattr(self.nb_line, "points", [i.x, i.top, i.right, i.top]))
        )

        self.nav_items = {
            "HOME": NavItem(ICONS["home"], "Home", lambda: self.switch_tab("HOME")),
            "MACHINES": NavItem(ICONS["machines"], "Machines", lambda: self.switch_tab("MACHINES")),
            "BREAKDOWN": NavItem(ICONS["breakdown"], "History", lambda: self.switch_tab("BREAKDOWN")),
            "SETTINGS": NavItem(ICONS["settings"], "Settings", lambda: self.switch_tab("SETTINGS")),
        }
        for item in self.nav_items.values():
            self.nav_bar.add_widget(item)
        self.root_box.add_widget(self.nav_bar)

        self.switch_tab("HOME", record_history=False)
        return self.root_box

    def make_status_pill(self, text_str, status_key):
        col = STATUS_MAP.get(status_key, ACCENT_COLOR)
        tint = STATUS_TINT_MAP.get(status_key, ACCENT_TINT)
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
                if "machine_order" in self.db:
                    return
        except Exception:
            pass

        self.db = {
            "settings": {
                "user_name": "SAGAR ALI",
                "role": "Junior Engineer",
                "dept": "Sterile Secondary Packaging",
                "plant": "Renata PLC (Kashor Site)",
                "address": "Kashor, Hobirbari, Bhaluka, Mymensingh"
            },
            "oee": {
                "days": [
                    {"day": "Sat", "avail": 94, "perf": 91, "qual": 99, "oee": 85, "uptime": 94},
                    {"day": "Sun", "avail": 97, "perf": 93, "qual": 100, "oee": 90, "uptime": 96},
                    {"day": "Mon", "avail": 92, "perf": 88, "qual": 99, "oee": 80, "uptime": 89},
                    {"day": "Tue", "avail": 95, "perf": 90, "qual": 98, "oee": 84, "uptime": 92},
                    {"day": "Wed", "avail": 88, "perf": 85, "qual": 99, "oee": 74, "uptime": 84},
                    {"day": "Thu", "avail": 96, "perf": 92, "qual": 100, "oee": 88, "uptime": 95},
                    {"day": "Fri", "avail": 90, "perf": 89, "qual": 97, "oee": 78, "uptime": 88}
                ]
            },
            "machine_order": [], "machines": {}, "breakdown_history": []
        }

        initial_sls = ["Brevetti", "Korber", "Light Inspection 01", "Light Inspection 02", "PDLD", "Ampoule Labeling 01", "Conveyor Belt 04", "Blister & Cartooning", "Conveyor Belt 01", "Checkweigher 01", "Vail Labeling 02", "Conveyor Belt 03", "Washing and Drying", "Vail Labeling 01", "Conveyor Belt 02", "IFC Printer", "NKP 01", "NKP 02"]
        ids = ["095", "089", "137", "138", "134", "106", "133", "111", "130", "143", "108", "132", "135", "107", "131", "136", "128", "129"]
        today_d = datetime.now().day

        for idx, nm in enumerate(initial_sls):
            mid = f"K02PR-{ids[idx]}"
            self.db["machine_order"].append(mid)
            st = "BREAKDOWN" if idx == 5 else ("IDLE" if idx in (6, 14) else "RUNNING")
            pm_d = today_d if idx in (0, 2, 7) else (today_d + 3 if idx % 3 == 0 else 26)
            self.db["machines"][mid] = {
                "sl": idx + 1, "name": nm, "id": mid, "status": st,
                "product": "Standard Batch", "batch": f"B26-10{40+idx}",
                "pm_day": pm_d, "pm_done_oct": False,
                "operator": "Md. Tanvir", "officer": "Kamrul Hasan"
            }
        self.save_data()

    def save_data(self):
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.db, f)
        except Exception:
            pass

    def get_time_greeting(self):
        hr = datetime.now().hour
        if 5 <= hr < 12:
            return "Good Morning!"
        elif 12 <= hr < 16:
            return "Good Noon!"
        elif 16 <= hr < 18:
            return "Good Afternoon!"
        elif 18 <= hr < 21:
            return "Good Evening!"
        return "Good Night!"

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
            if self.current_tab == "HOME" and self.selected_oee_day is not None:
                self.close_oee_detail()
                return True
            if self.tab_history:
                self.switch_tab(self.tab_history.pop(), record_history=False)
                return True
            if self.current_tab != "HOME":
                self.switch_tab("HOME", record_history=False)
                return True
            now = time.time()
            if now - self.last_back_press < 2.0:
                return False
            self.last_back_press = now
            self.show_toast("Press back again to exit")
            return True
        return False

    def switch_tab(self, tab_name, record_history=True):
        if record_history and self.current_tab and self.current_tab != tab_name:
            if tab_name == "HOME":
                self.tab_history.clear()
            elif not self.tab_history or self.tab_history[-1] != self.current_tab:
                self.tab_history.append(self.current_tab)

        self.current_tab = tab_name
        for k, item in self.nav_items.items():
            item.set_active(k == tab_name)
        self.feed.clear_widgets()
        self.scroll.scroll_y = 1.0

        if tab_name == "HOME":
            self.build_home()
        elif tab_name == "MACHINES":
            self.build_machines()
        elif tab_name == "BREAKDOWN":
            self.build_breakdown_history()
        elif tab_name == "SETTINGS":
            self.build_settings()

    # ==========================================
    # HOME PAGE (BUILD v20)
    # ==========================================
    def build_home(self):
        cfg = self.db["settings"]
        m_list = list(self.db["machines"].values())
        today_obj = datetime.now()
        today_date = today_obj.day

        c_run = sum(1 for m in m_list if m["status"] == "RUNNING")
        c_idle = sum(1 for m in m_list if m["status"] == "IDLE")
        c_bd = sum(1 for m in m_list if m["status"] == "BREAKDOWN")

        pm_today_list = [m for m in m_list if m.get("pm_day") == today_date and not m.get("pm_done_oct", False)]
        pm_due_month_list = [m for m in m_list if m.get("pm_day", 0) != today_date and not m.get("pm_done_oct", False)]

        total_m = max(1, len(m_list))
        uptime_pct = int(round((c_run / total_m) * 100))

        # 1. GREETING CARD (Dynamic height so nothing ever overflows)
        greet_box = ModernBox(orientation="vertical", padding=[dp(16), dp(14)], spacing=dp(4), left_accent=ACCENT_COLOR)
        top_row = BoxLayout(size_hint_y=None, height=dp(22))
        top_row.add_widget(make_label(self.get_time_greeting(), sp(13), ACCENT_COLOR, bold=True, height_dp=22))
        top_row.add_widget(make_label(f"Date: {today_obj.strftime('%d %b %Y')}", sp(11), TEXT_PRIMARY, bold=True, halign="right", height_dp=22))
        greet_box.add_widget(top_row)

        greet_box.add_widget(make_label(cfg["user_name"], sp(20), TEXT_PRIMARY, bold=True, height_dp=26))
        greet_box.add_widget(make_label(cfg["role"], sp(12), ACCENT_COLOR, bold=True, height_dp=18))
        greet_box.add_widget(make_label(cfg.get("dept", "Sterile Secondary Packaging"), sp(11), TEXT_PRIMARY, height_dp=18))
        greet_box.add_widget(make_label(cfg["plant"], sp(11), TEXT_MUTED, height_dp=18))
        greet_box.add_widget(make_label(cfg["address"], sp(10), TEXT_MUTED, height_dp=16))
        self.feed.add_widget(greet_box)

        # 2. TODAY'S SUMMARY CARD (Tap to view & complete Today's PM)
        sum_box = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(10))
        sum_box.add_widget(make_label("TODAY'S LINE SUMMARY (TAP ANY CARD)", sp(11), TEXT_MUTED, bold=True, height_dp=18))
        grid_sum = GridLayout(cols=2, size_hint_x=1, size_hint_y=None, height=dp(132), spacing=dp(8))

        sm_meta = [
            ("RUNNING", str(c_run), STATUS_RUNNING, ICONS["running"], "RUNNING"),
            ("IDLE", str(c_idle), STATUS_IDLE, ICONS["idle"], "IDLE"),
            ("PM DUE TODAY", str(len(pm_today_list)), STATUS_MAINTENANCE, ICONS["maintenance"], "PM_TODAY"),
            ("BREAKDOWN", str(c_bd), STATUS_BREAKDOWN, ICONS["breakdown_icon"], "BREAKDOWN"),
        ]
        for title_s, num_s, col, ic_ch, st_val in sm_meta:
            tile = AnimatedCard(
                on_tap_cb=lambda sv=st_val, ts=title_s: self.open_summary_drilldown(sv, ts),
                bg_color=CARD_INNER, border_color=BORDER_COLOR, radius=dp(12),
                left_accent=col, auto_height=False, height=dp(62),
                orientation="horizontal", padding=[dp(10), dp(6)], spacing=dp(8)
            )
            ic_l = Label(text=ic_ch, font_name=ICON_FONT, font_size=dp(18), color=col, size_hint_x=None, width=dp(24))
            txt_c = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))
            txt_c.add_widget(make_label(title_s, sp(10), TEXT_MUTED, bold=True, height_dp=16))
            txt_c.add_widget(make_label(num_s, sp(19), col, bold=True, height_dp=24))
            tile.add_widget(ic_l)
            tile.add_widget(txt_c)
            grid_sum.add_widget(tile)
        sum_box.add_widget(grid_sum)
        self.feed.add_widget(sum_box)

        # 3. MONTHLY FOCUS CARD (Remaining Month Due PM, Pending BD, Today's Uptime %)
        focus_box = ModernBox(bg_color=CARD_INNER, border_color=BORDER_COLOR, radius=dp(12), auto_height=False, height=dp(68), orientation="horizontal", padding=[dp(8), dp(8)])
        f_items = [
            (str(len(pm_due_month_list)), "Due PM (Month)", STATUS_MAINTENANCE),
            (str(c_bd), "Pending BD", STATUS_BREAKDOWN if c_bd > 0 else TEXT_PRIMARY),
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

        # 4. FULL MONTH CALENDAR (Starts Saturday, Highlights PM dates)
        cal_box = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(10))
        cal_box.add_widget(make_label("OCTOBER 2026 PM SCHEDULE CALENDAR (SAT - FRI)", sp(11), TEXT_MUTED, bold=True, height_dp=18))

        days_header = GridLayout(cols=7, size_hint_y=None, height=dp(20))
        for d in ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]:
            days_header.add_widget(make_label(d, sp(10), ACCENT_COLOR if d == "Sat" else TEXT_MUTED, bold=True, halign="center", height_dp=20))
        cal_box.add_widget(days_header)

        cal_grid = GridLayout(cols=7, size_hint_y=None, spacing=dp(4))
        cal_grid.bind(minimum_height=cal_grid.setter("height"))

        # Oct 1, 2026 is Thursday -> 5 empty slots from Saturday (Sat, Sun, Mon, Tue, Wed)
        for _ in range(5):
            cal_grid.add_widget(Widget(size_hint_y=None, height=dp(36)))

        pm_days_map = {}
        for m in m_list:
            pd = m.get("pm_day")
            if pd:
                pm_days_map.setdefault(pd, []).append(m)

        for d_num in range(1, 32):
            has_pm = d_num in pm_days_map
            all_done = has_pm and all(x.get("pm_done_oct", False) for x in pm_days_map[d_num])
            is_today = d_num == today_date

            if is_today:
                bg_c, fg_c = ACCENT_COLOR, BG_COLOR
            elif has_pm and not all_done:
                bg_c, fg_c = (0.35, 0.23, 0.05, 1), STATUS_MAINTENANCE
            elif has_pm and all_done:
                bg_c, fg_c = (0.06, 0.28, 0.18, 1), STATUS_RUNNING
            else:
                bg_c, fg_c = CARD_INNER, TEXT_PRIMARY

            d_btn = AnimatedCard(
                on_tap_cb=lambda dn=d_num, hpm=has_pm: self.open_pm_day_details(dn, hpm, pm_days_map),
                bg_color=bg_c, border_color=ACCENT_COLOR if is_today else BORDER_COLOR,
                radius=dp(8), auto_height=False, height=dp(36)
            )
            d_btn.add_widget(make_label(str(d_num), sp(12), fg_c, bold=True, halign="center", height_dp=36))
            cal_grid.add_widget(d_btn)
        cal_box.add_widget(cal_grid)
        self.feed.add_widget(cal_box)

        # 5. INTERACTIVE VISUAL BAR GRAPH FOR WEEKLY OEE & UPTIME (Starts Saturday)
        oee_box = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(10))
        hdr_o = BoxLayout(size_hint_y=None, height=dp(20))
        hdr_o.add_widget(make_label("WEEKLY OEE & UPTIME GRAPH (SAT - FRI)", sp(11), TEXT_MUTED, bold=True, height_dp=20))
        hdr_o.add_widget(make_label("Tap bar for details", sp(10), ACCENT_COLOR, halign="right", height_dp=20))
        oee_box.add_widget(hdr_o)

        bars_Grid = GridLayout(cols=7, size_hint_y=None, height=dp(120), spacing=dp(6))
        for day_data in self.db["oee"]["days"]:
            is_sel = self.selected_oee_day == day_data["day"]
            col_wrap = AnimatedCard(
                on_tap_cb=lambda dt=day_data: self.toggle_oee_day(dt),
                bg_color=ACCENT_TINT if is_sel else CARD_INNER,
                border_color=ACCENT_COLOR if is_sel else BORDER_COLOR,
                radius=dp(8), auto_height=False, height=dp(120),
                orientation="vertical", padding=[dp(4), dp(6)], spacing=dp(4)
            )
            col_wrap.add_widget(make_label(f"{day_data['oee']}%", sp(9), ACCENT_COLOR if is_sel else TEXT_PRIMARY, bold=True, halign="center", height_dp=14))

            # Visual vertical bar inside each column
            bar_area = BoxLayout(orientation="vertical", size_hint_y=1, padding=[dp(6), 0])
            pct = max(0.15, min(1.0, day_data["oee"] / 100.0))
            bar_area.add_widget(Widget(size_hint_y=1.0 - pct))
            bar_fill = ModernBox(
                bg_color=ACCENT_COLOR if is_sel else STATUS_RUNNING,
                border_color=ACCENT_COLOR if is_sel else STATUS_RUNNING,
                radius=dp(4), auto_height=False, size_hint_y=pct
            )
            bar_area.add_widget(bar_fill)
            col_wrap.add_widget(bar_area)

            col_wrap.add_widget(make_label(day_data["day"], sp(10), ACCENT_COLOR if is_sel else TEXT_MUTED, bold=True, halign="center", height_dp=16))
            bars_Grid.add_widget(col_wrap)

        oee_box.add_widget(bars_Grid)

        # Collapsible OEE Detail Drawer (Closes on tap or Back button)
        self.oee_detail_box = AnimatedCard(
            on_tap_cb=self.close_oee_detail,
            bg_color=CARD_INNER, border_color=ACCENT_COLOR, radius=dp(10),
            orientation="vertical", auto_height=False, height=0, padding=[dp(10), 0], spacing=dp(4)
        )
        self.oee_detail_box.opacity = 0.0
        self.oee_d_title = make_label("", sp(12), ACCENT_COLOR, bold=True, halign="center", height_dp=0)
        self.oee_d_stats = make_label("", sp(11), TEXT_PRIMARY, halign="center", height_dp=0)
        self.oee_d_hint = make_label("Tap here or press Back to close", sp(9), TEXT_MUTED, halign="center", height_dp=0)
        self.oee_detail_box.add_widget(self.oee_d_title)
        self.oee_detail_box.add_widget(self.oee_d_stats)
        self.oee_detail_box.add_widget(self.oee_d_hint)
        oee_box.add_widget(self.oee_detail_box)

        self.feed.add_widget(oee_box)

    def toggle_oee_day(self, day_data):
        if self.selected_oee_day == day_data["day"]:
            self.close_oee_detail()
            return
        self.selected_oee_day = day_data["day"]
        self.oee_d_title.text = f"{day_data['day']} — OEE: {day_data['oee']}%  |  Line Uptime: {day_data.get('uptime', day_data['avail'])}%"
        self.oee_d_stats.text = f"Availability: {day_data['avail']}%   •   Performance: {day_data['perf']}%   •   Quality: {day_data['qual']}%"
        self.oee_d_title.height = dp(20)
        self.oee_d_stats.height = dp(18)
        self.oee_d_hint.height = dp(14)
        self.oee_detail_box.padding = [dp(10), dp(8)]
        Animation(height=dp(72), opacity=1.0, duration=0.22, t="out_cubic").start(self.oee_detail_box)

    def close_oee_detail(self):
        self.selected_oee_day = None
        self.oee_d_title.height = 0
        self.oee_d_stats.height = 0
        self.oee_d_hint.height = 0
        self.oee_detail_box.padding = [dp(10), 0]
        Animation(height=0, opacity=0.0, duration=0.18, t="out_quad").start(self.oee_detail_box)

    def open_summary_drilldown(self, status_val, title_str):
        m_list = list(self.db["machines"].values())
        today_date = datetime.now().day
        if status_val == "PM_TODAY":
            matched = [m for m in m_list if m.get("pm_day") == today_date]
        else:
            matched = [m for m in m_list if m["status"] == status_val]

        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(make_label(f"{title_str} ({len(matched)} Machines)", sp(14), ACCENT_COLOR, bold=True, height_dp=24))

        scroll_m = ScrollView(size_hint=(1, 1))
        m_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        m_box.bind(minimum_height=m_box.setter("height"))

        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.92, 0.65), background="", background_color=CARD_COLOR)

        if not matched:
            m_box.add_widget(make_label("No machines in this category right now.", sp(12), TEXT_MUTED, height_dp=30))
        else:
            for mat in matched:
                c = ModernBox(bg_color=CARD_INNER, radius=dp(8), auto_height=False, height=dp(48), padding=[dp(10), 0], spacing=dp(6), orientation="horizontal")
                c.add_widget(make_label(f"#{mat['sl']} {mat['name']} ({mat['id']})", sp(12), TEXT_PRIMARY, bold=True, height_dp=48))
                if status_val == "PM_TODAY":
                    is_done = mat.get("pm_done_oct", False)
                    if is_done:
                        c.add_widget(self.make_status_pill("COMPLETED", "RUNNING"))
                    else:
                        btn_done = Button(
                            text="Complete PM", size_hint=(None, None), size=(dp(96), dp(32)),
                            pos_hint={"center_y": 0.5}, font_size=sp(10), bold=True,
                            background_normal="", background_color=STATUS_RUNNING, color=BG_COLOR
                        )
                        btn_done.bind(on_release=lambda x, mid=mat["id"]: (self.mark_pm_complete(mid), pop.dismiss()))
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
        box.add_widget(make_label(f"PM Schedule — Oct {day_num}, 2026", sp(14), ACCENT_COLOR, bold=True, height_dp=24))

        scroll_m = ScrollView(size_hint=(1, 1))
        m_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        m_box.bind(minimum_height=m_box.setter("height"))

        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.92, 0.60), background="", background_color=CARD_COLOR)

        if has_pm:
            for mach in pm_map[day_num]:
                is_done = mach.get("pm_done_oct", False)
                row = ModernBox(bg_color=CARD_INNER, radius=dp(8), auto_height=False, height=dp(48), padding=[dp(10), 0], orientation="horizontal")
                info = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))
                info.add_widget(make_label(f"{mach['name']} ({mach['id']})", sp(12), TEXT_PRIMARY, bold=True, height_dp=22))
                info.add_widget(make_label("PM Completed" if is_done else "Maintenance Due", sp(10), STATUS_RUNNING if is_done else STATUS_MAINTENANCE, height_dp=16))
                row.add_widget(info)

                if not is_done:
                    btn_comp = Button(
                        text="Complete", size_hint=(None, None), size=(dp(85), dp(32)),
                        pos_hint={"center_y": 0.5}, font_size=sp(10), bold=True,
                        background_normal="", background_color=STATUS_RUNNING, color=BG_COLOR
                    )
                    btn_comp.bind(on_release=lambda x, mid=mach["id"]: (self.mark_pm_complete(mid), pop.dismiss()))
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
            c = ModernBox(bg_color=CARD_INNER, radius=dp(10), auto_height=False, height=dp(46), padding=[dp(12), 0], orientation="horizontal", left_accent=STATUS_MAP.get(m["status"], ACCENT_COLOR))
            c.add_widget(make_label(f"#{m['sl']} {m['name']} ({mid})", sp(12), TEXT_PRIMARY, bold=True, height_dp=46))
            c.add_widget(self.make_status_pill(m["status"], m["status"]))
            self.feed.add_widget(c)

    def build_breakdown_history(self):
        hdr = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        b_back = Button(text="<- Home", size_hint=(None, None), size=(dp(72), dp(34)), font_size=sp(10), bold=True, background_normal="", background_color=CARD_COLOR, color=ACCENT_COLOR)
        b_back.bind(on_release=lambda x: self.go_back_step())
        hdr.add_widget(b_back)
        hdr.add_widget(make_label("BREAKDOWN HISTORY", sp(11), TEXT_MUTED, bold=True, height_dp=36))
        self.feed.add_widget(hdr)
        if not self.db["breakdown_history"]:
            self.feed.add_widget(make_label("No breakdowns logged today.", sp(12), TEXT_MUTED, height_dp=30))

    def build_settings(self):
        hdr = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        b_back = Button(text="<- Home", size_hint=(None, None), size=(dp(72), dp(34)), font_size=sp(10), bold=True, background_normal="", background_color=CARD_COLOR, color=ACCENT_COLOR)
        b_back.bind(on_release=lambda x: self.go_back_step())
        hdr.add_widget(b_back)
        hdr.add_widget(make_label("SETTINGS & PM SCHEDULE", sp(11), TEXT_MUTED, bold=True, height_dp=36))
        self.feed.add_widget(hdr)

        pm_cfg_box = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(8), left_accent=STATUS_MAINTENANCE)
        pm_cfg_box.add_widget(make_label("SET OCTOBER PM DATE PER MACHINE", sp(11), STATUS_MAINTENANCE, bold=True, height_dp=20))
        day_vals = [f"Oct {d}" for d in range(1, 32)]
        for mid in self.db["machine_order"]:
            m = self.db["machines"][mid]
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(8))
            row.add_widget(make_label(f"#{m['sl']} {m['name']}", sp(12), TEXT_PRIMARY, height_dp=36))
            sp_day = Spinner(text=f"Oct {m.get('pm_day', 19)}", values=day_vals, size_hint=(None, None), size=(dp(92), dp(32)), font_size=sp(10), bold=True, background_normal="", background_color=CARD_INNER, color=ACCENT_COLOR)
            def _on_d(sp_i, txt, mach_id=mid):
                try:
                    self.db["machines"][mach_id]["pm_day"] = int(txt.replace("Oct ", ""))
                    self.db["machines"][mach_id]["pm_done_oct"] = False
                    self.save_data()
                except Exception:
                    pass
            sp_day.bind(text=_on_d)
            row.add_widget(sp_day)
            pm_cfg_box.add_widget(row)
        self.feed.add_widget(pm_cfg_box)


if __name__ == "__main__":
    MachineTrackerApp().run()
