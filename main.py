import json
import os
import time
from datetime import datetime
from kivy.app import App
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
from kivy.core.window import Window

# ==========================================
# 1. ULTRA-SAFE THEME (No Custom Fonts Required)
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

STATUS_MAP = {
    "RUNNING": get_color_from_hex("#10B981"),
    "IDLE": get_color_from_hex("#64748B"),
    "BREAKDOWN": get_color_from_hex("#F43F5E"),
    "MAINTENANCE": get_color_from_hex("#F59E0B"),
}
STATUS_TINT_MAP = {
    "RUNNING": (0.063, 0.725, 0.506, 0.16),
    "IDLE": (0.392, 0.455, 0.545, 0.16),
    "BREAKDOWN": (0.957, 0.247, 0.369, 0.16),
    "MAINTENANCE": (0.961, 0.620, 0.043, 0.16),
}

FONT_TITLE, FONT_SEC_LABEL, FONT_CARD_TITLE = sp(19), sp(11), sp(14)
FONT_BODY, FONT_CAPTION, FONT_BIG_NUM = sp(12), sp(10), sp(22)

# Safe Text-based Icons
ICONS = {
    "home": "HOME", "machines": "LIST", "breakdown": "CAPA", "settings": "SETTING",
    "running": "R", "idle": "I", "breakdown_icon": "!", "maintenance": "M",
    "check": "OK", "check_circle": "DONE", "calendar": "CAL", "add": "+",
    "build": "FIX", "report": "REP", "inventory": "BOX", "handover": "NOTE", "back": "<-",
}

# ==========================================
# 2. REUSABLE UI COMPONENTS
# ==========================================
class ModernBox(BoxLayout):
    def __init__(self, bg_color=CARD_COLOR, border_color=BORDER_COLOR, radius=dp(16), left_accent=None, auto_height=True, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_x = 1
        self.size_hint_y = None
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
        if self.left_accent:
            self.r_ac.pos, self.r_ac.size = (self.x+dp(2), self.y+dp(10)), (dp(4), max(dp(10), self.height-dp(20)))

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

def make_label(text, font_size=FONT_BODY, color=TEXT_PRIMARY, bold=False, halign="left", height_dp=22):
    lbl = Label(text=str(text), font_size=font_size, color=color, bold=bold, halign=halign, valign="middle", size_hint_y=None, height=dp(height_dp))
    lbl.bind(size=lbl.setter("text_size"))
    return lbl

def make_status_pill(text_str, status_key):
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
    pill.add_widget(Label(text=text_str, font_size=FONT_CAPTION, bold=True, color=col, halign="center", valign="middle"))
    return pill

class NavItem(ButtonBehavior, BoxLayout):
    def __init__(self, icon_char, title_str, on_tap, **kwargs):
        super().__init__(orientation="vertical", size_hint_x=1, padding=[0, dp(4)], spacing=dp(2), **kwargs)
        self.on_tap_cb = on_tap
        self.pill = BoxLayout(size_hint=(None, None), size=(dp(46), dp(26)), pos_hint={"center_x": 0.5})
        with self.pill.canvas.before:
            self.p_col = Color(0, 0, 0, 0)
            self.p_rect = RoundedRectangle(pos=self.pill.pos, size=self.pill.size, radius=[dp(13)])
        self.pill.bind(pos=lambda i, v: setattr(self.p_rect, "pos", v), size=lambda i, v: setattr(self.p_rect, "size", v))

        self.tx = Label(text=title_str, font_size=FONT_CAPTION, color=TEXT_MUTED, size_hint_y=None, height=dp(15), bold=True)
        self.add_widget(self.pill)
        self.add_widget(self.tx)

    def on_release(self):
        Animation(opacity=0.6, duration=0.06).start(self)
        Animation(opacity=1.0, duration=0.15).start(self)
        self.on_tap_cb()

    def set_active(self, active):
        self.p_col.rgba = ACCENT_TINT if active else (0, 0, 0, 0)
        self.tx.color, self.tx.bold = (ACCENT_COLOR, True) if active else (TEXT_MUTED, False)

# ==========================================
# 3. MAIN APPLICATION
# ==========================================
class MachineTrackerApp(App):
    def build(self):
        self.title = "S Matrix Smart Eng-Ops"
        self.data_file = os.path.join(self.user_data_dir, "smatrix_safe_v11.json")
        self.load_data()

        self.current_tab = "HOME"
        self.tab_history = []
        self.active_popup = None
        self.last_back_press = 0.0

        self.selected_cal_day = 18
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
        self.toast_lbl = make_label("", FONT_CAPTION, ACCENT_COLOR, bold=True, halign="center", height_dp=28)
        self.toast_bar.add_widget(self.toast_lbl)
        self.root_box.add_widget(self.toast_bar)

        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(2))
        self.feed = BoxLayout(orientation="vertical", size_hint_x=1, size_hint_y=None, padding=[PAD_SCREEN, dp(14), PAD_SCREEN, dp(28)], spacing=dp(14))
        self.feed.bind(minimum_height=self.feed.setter("height"))
        self.scroll.add_widget(self.feed)
        self.root_box.add_widget(self.scroll)

        self.nav_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(58), padding=[dp(8), 0])
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
            "BREAKDOWN": NavItem(ICONS["breakdown"], "Breakdown", lambda: self.switch_tab("BREAKDOWN")),
            "SETTINGS": NavItem(ICONS["settings"], "Settings", lambda: self.switch_tab("SETTINGS")),
        }
        for item in self.nav_items.values():
            self.nav_bar.add_widget(item)
        self.root_box.add_widget(self.nav_bar)

        self.switch_tab("HOME", record_history=False)
        return self.root_box

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
                prev_tab = self.tab_history.pop()
                self.switch_tab(prev_tab, record_history=False)
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

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    self.db = json.load(f)
                if "machine_order" in self.db and "machines" in self.db:
                    return
        except Exception:
            pass

        self.db = {
            "settings": {"user_name": "Ahmeed Sunny", "role": "Sr. Automation Engr", "shift": "Shift A", "plant": "Sterile Unit"},
            "oee": {
                "overall": 88.4, "availability": 92, "performance": 89, "quality": 98,
                "days": [["M", 86], ["T", 89], ["W", 84], ["T", 91], ["F", 88], ["S", 93], ["S", 90]]
            },
            "machine_order": [],
            "machines": {},
            "breakdown_history": [
                {
                    "id": "BD-101", "machine_id": "K02PR-106", "machine_name": "Ampoule Labeling 01",
                    "date_time": "18 Oct 2026, 09:30 AM", "completed_time": "18 Oct 2026, 10:15 AM",
                    "issue": "Label gap optical sensor false trigger at >320 RPM",
                    "rca": "Adhesive residue on optical fiber head",
                    "corrective": "Cleaned optical lens with IPA & recalibrated threshold",
                    "parts_changed": "Yes", "parts_desc": "Optical Fiber Head x1",
                    "param_changed": "Yes", "param_desc": "Sensitivity threshold 62% -> 75%",
                    "work_desc": "Dismantled sensor bracket, solvent cleaned lens, tested 500 ampoules.",
                    "responsible": "Ahmeed Sunny & Tanvir"
                }
            ]
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
                "std_time": "6.0 Hours", "act_time": "7.5 Hours" if idx == 5 else "5.8 Hours",
                "delay_reason": "Sensor recalibration" if idx == 5 else "Completed on schedule",
                "operator": "Md. Tanvir", "officer": "Kamrul Hasan"
            }
        self.save_data()

    def save_data(self):
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.db, f)
        except Exception:
            pass

    def animate_widget_in(self, widget, delay=0.0):
        widget.opacity = 0.0
        anim = Animation(opacity=1.0, duration=0.22, t="out_cubic")
        Clock.schedule_once(lambda dt: anim.start(widget), delay)

    def switch_tab(self, tab_name, record_history=True):
        if record_history and self.current_tab and self.current_tab != tab_name:
            if tab_name == "HOME":
                self.tab_history.clear()
            else:
                if not self.tab_history or self.tab_history[-1] != self.current_tab:
                    self.tab_history.append(self.current_tab)

        self.current_tab = tab_name
        for k, item in self.nav_items.items():
            item.set_active(k == tab_name or (tab_name == "MACHINE_DETAIL" and k == "MACHINES"))

        self.feed.clear_widgets()
        self.scroll.scroll_y = 1.0

        if tab_name == "HOME": self.build_home()
        elif tab_name == "MACHINES": self.build_machines()
        elif tab_name == "MACHINE_DETAIL": self.build_machine_detail(self.selected_machine_id)
        elif tab_name == "BREAKDOWN": self.build_breakdown_history()
        elif tab_name == "SETTINGS": self.build_settings()

        for i, child in enumerate(reversed(self.feed.children)):
            self.animate_widget_in(child, delay=i * 0.035)

    def go_back_step(self):
        if self.tab_history:
            prev = self.tab_history.pop()
            self.switch_tab(prev, record_history=False)
        else:
            self.switch_tab("HOME", record_history=False)

    def build_home(self):
        cfg = self.db["settings"]
        m_list = list(self.db["machines"].values())
        total_m = max(1, len(m_list))

        c_run = sum(1 for m in m_list if m["status"] == "RUNNING")
        c_idle = sum(1 for m in m_list if m["status"] == "IDLE")
        c_bd = sum(1 for m in m_list if m["status"] == "BREAKDOWN")
        c_maint = sum(1 for m in m_list if m["status"] == "MAINTENANCE")

        greet_box = ModernBox(orientation="horizontal", auto_height=False, height=dp(90), padding=[dp(16), dp(12)], spacing=dp(10), left_accent=ACCENT_COLOR)
        g_left = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))
        hr = datetime.now().hour
        g_time = "Good morning" if hr < 12 else ("Good afternoon" if hr < 17 else "Good evening")
        g_left.add_widget(make_label(f"{g_time} · LIVE TELEMETRY", FONT_CAPTION, ACCENT_COLOR, bold=True, height_dp=18))
        g_left.add_widget(make_label(cfg["user_name"], FONT_TITLE, TEXT_PRIMARY, bold=True, height_dp=26))
        g_left.add_widget(make_label(f"{cfg['role']}  •  {cfg['shift']}  •  {cfg['plant']}", FONT_CAPTION, TEXT_MUTED, height_dp=18))
        greet_box.add_widget(g_left)

        initials = "".join([w[0] for w in cfg["user_name"].split()[:2]]).upper() or "AS"
        av_box = AnimatedCard(on_tap_cb=lambda: self.switch_tab("SETTINGS"), bg_color=CARD_INNER, border_color=ACCENT_COLOR, radius=dp(22), auto_height=False, size_hint=(None, None), size=(dp(46), dp(46)), pos_hint={"center_y": 0.5})
        av_box.size_hint_x, av_box.width = None, dp(46)
        av_box.add_widget(Label(text=initials, font_size=FONT_BODY, bold=True, color=ACCENT_COLOR))
        greet_box.add_widget(av_box)
        self.feed.add_widget(greet_box)

        summary_container = ModernBox(orientation="vertical", padding=dp(12), spacing=dp(10))
        hdr_s = BoxLayout(size_hint_y=None, height=dp(20))
        hdr_s.add_widget(make_label("TODAY'S PLANT SUMMARY", FONT_SEC_LABEL, TEXT_MUTED, bold=True, height_dp=20))
        hdr_s.add_widget(make_label("Tap card to filter ->", FONT_CAPTION, ACCENT_COLOR, halign="right", height_dp=20))
        summary_container.add_widget(hdr_s)

        grid_2x2 = GridLayout(cols=2, size_hint_x=1, size_hint_y=None, height=dp(156), spacing=dp(8))
        cards_meta = [
            ("RUNNING", str(c_run), "Running"), ("IDLE", str(c_idle), "Idle"),
            ("BREAKDOWN", str(c_bd), "Breakdown"), ("MAINTENANCE", str(c_maint), "Maintenance"),
        ]
        for st_key, num_s, title_s in cards_meta:
            st_col = STATUS_MAP[st_key]
            tile = AnimatedCard(on_tap_cb=lambda k=st_key: self.open_filtered_machines(k), bg_color=CARD_INNER, border_color=BORDER_COLOR, radius=RADIUS_INNER, left_accent=st_col, auto_height=False, height=dp(74), orientation="horizontal", padding=[dp(12), dp(8)], spacing=dp(10))
            txt_col = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))
            txt_col.add_widget(make_label(num_s, FONT_BIG_NUM, TEXT_PRIMARY, bold=True, height_dp=28))
            txt_col.add_widget(make_label(title_s, FONT_CAPTION, TEXT_MUTED, height_dp=16))
            tile.add_widget(txt_col)
            grid_2x2.add_widget(tile)
        summary_container.add_widget(grid_2x2)
        self.feed.add_widget(summary_container)

        qa_row = GridLayout(cols=3, size_hint_x=1, size_hint_y=None, height=dp(42), spacing=dp(6))
        qa_meta = [
            ("+ Breakdown", STATUS_BREAKDOWN, lambda: self.open_breakdown_modal()),
            ("+ Spare Part", ACCENT_COLOR, self.open_spare_modal),
            ("+ Handover", STATUS_RUNNING, self.open_handover_modal),
        ]
        for txt_s, ac_col, cb_fn in qa_meta:
            pill = AnimatedCard(on_tap_cb=cb_fn, bg_color=CARD_COLOR, border_color=BORDER_COLOR, radius=dp(21), auto_height=False, height=dp(42), orientation="horizontal", padding=[dp(8), 0], spacing=dp(6))
            pill.add_widget(Label(text=txt_s, font_size=FONT_CAPTION, bold=True, color=ac_col, halign="center", valign="middle"))
            qa_row.add_widget(pill)
        self.feed.add_widget(qa_row)

        cal_box = ModernBox(orientation="vertical", padding=dp(12), spacing=dp(10))
        cal_hdr = BoxLayout(size_hint_y=None, height=dp(24))
        cal_hdr.add_widget(make_label("PM SCHEDULE CALENDAR", FONT_SEC_LABEL, TEXT_MUTED, bold=True, height_dp=24))
        btn_cfg_pm = Button(text="Set Schedule ->", font_size=FONT_CAPTION, bold=True, color=ACCENT_COLOR, background_normal="", background_color=(0, 0, 0, 0), size_hint=(None, None), size=(dp(95), dp(24)))
        btn_cfg_pm.bind(on_release=lambda x: self.switch_tab("SETTINGS"))
        cal_hdr.add_widget(btn_cfg_pm)
        cal_box.add_widget(cal_hdr)

        cal_scroll = ScrollView(do_scroll_x=True, do_scroll_y=False, size_hint_y=None, height=dp(60), bar_width=0)
        cal_strip = BoxLayout(orientation="horizontal", size_hint_x=None, width=dp(14 * 48), spacing=dp(6))
        day_names = ["Thu", "Fri", "Sat", "Sun", "Mon", "Tue", "Wed"]

        for idx, d_num in enumerate(range(15, 29)):
            is_sel = d_num == self.selected_cal_day
            has_machines = any(m.get("pm_day") == d_num for m in m_list)
            d_card = AnimatedCard(on_tap_cb=lambda dn=d_num: self.select_calendar_day(dn), bg_color=ACCENT_TINT if is_sel else CARD_INNER, border_color=ACCENT_COLOR if is_sel else BORDER_COLOR, radius=dp(12), auto_height=False, size_hint=(None, None), size=(dp(42), dp(56)), orientation="vertical", padding=[0, dp(5)], spacing=dp(2))
            d_card.size_hint_x, d_card.width = None, dp(42)
            d_card.add_widget(make_label(day_names[idx % 7], sp(9), ACCENT_COLOR if is_sel else TEXT_MUTED, halign="center", height_dp=14))
            d_card.add_widget(make_label(str(d_num), sp(14), TEXT_PRIMARY, bold=True, halign="center", height_dp=20))

            dot_wrap = BoxLayout(size_hint_y=None, height=dp(8))
            dot_wrap.add_widget(Widget())
            if has_machines:
                dot = Widget(size_hint=(None, None), size=(dp(6), dp(6)))
                with dot.canvas:
                    Color(*(STATUS_MAINTENANCE if d_num >= 18 else STATUS_BREAKDOWN))
                    el = Ellipse(pos=dot.pos, size=dot.size)
                dot.bind(pos=lambda i, v: setattr(el, "pos", v), size=lambda i, v: setattr(el, "size", v))
                dot_wrap.add_widget(dot)
            dot_wrap.add_widget(Widget())
            d_card.add_widget(dot_wrap)
            cal_strip.add_widget(d_card)

        cal_scroll.add_widget(cal_strip)
        cal_box.add_widget(cal_scroll)

        day_machines = [m for m in m_list if m.get("pm_day") == self.selected_cal_day]
        if not day_machines:
            empty_d = ModernBox(bg_color=CARD_INNER, radius=dp(10), auto_height=False, height=dp(42), padding=[dp(12), 0])
            empty_d.add_widget(make_label(f"Oct {self.selected_cal_day}: No PM scheduled", FONT_BODY, TEXT_MUTED, height_dp=42))
            cal_box.add_widget(empty_d)
        else:
            for pm_m in day_machines:
                is_done = pm_m.get("pm_done_oct", False)
                p_row = AnimatedCard(on_tap_cb=lambda mid=pm_m["id"]: self.open_pm_confirm_modal(mid), bg_color=CARD_INNER, border_color=BORDER_COLOR, radius=dp(10), left_accent=STATUS_RUNNING if is_done else STATUS_MAINTENANCE, auto_height=False, height=dp(52), orientation="horizontal", padding=[dp(12), dp(6)], spacing=dp(8))
                p_info = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))
                p_info.add_widget(make_label(f"{pm_m['name']} ({pm_m['id']})", FONT_BODY, TEXT_PRIMARY, bold=True, height_dp=20))
                st_str = "Completed for Oct" if is_done else f"Scheduled Oct {self.selected_cal_day} · Tap to complete"
                p_info.add_widget(make_label(st_str, FONT_CAPTION, STATUS_RUNNING if is_done else ACCENT_COLOR, height_dp=16))
                p_row.add_widget(p_info)
                cal_box.add_widget(p_row)
        self.feed.add_widget(cal_box)

    def select_calendar_day(self, day_num):
        self.selected_cal_day = day_num
        self.switch_tab("HOME", record_history=False)

    def open_filtered_machines(self, status_key):
        self.machine_filter = status_key
        self.switch_tab("MACHINES")

    def open_tracked_popup(self, pop):
        self.active_popup = pop
        pop.bind(on_dismiss=lambda *a: setattr(self, "active_popup", None))
        pop.open()

    def open_pm_confirm_modal(self, m_id):
        m = self.db["machines"][m_id]
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(make_label(f"Complete PM · {m['name']} ({m_id})", FONT_CARD_TITLE, ACCENT_COLOR, bold=True, height_dp=24))
        self.make_input(box, "Maintenance Remarks", "Cleaned, lubricated & calibrated")

        b_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        b_can = Button(text="Cancel", background_normal="", background_color=CARD_INNER, color=TEXT_MUTED)
        b_ok = Button(text="Mark Completed", background_normal="", background_color=STATUS_RUNNING, color=BG_COLOR, bold=True)
        b_row.add_widget(b_can)
        b_row.add_widget(b_ok)
        box.add_widget(b_row)

        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.9, None), height=dp(210), background="", background_color=CARD_COLOR)
        b_can.bind(on_release=pop.dismiss)
        def _done(*a):
            m["pm_done_oct"] = True
            self.save_data()
            pop.dismiss()
            self.switch_tab("HOME", record_history=False)
        b_ok.bind(on_release=_done)
        self.open_tracked_popup(pop)

    def build_machines(self):
        top_bar = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        b_back = Button(text="<- Home", size_hint=(None, None), size=(dp(72), dp(34)), font_size=FONT_CAPTION, bold=True, background_normal="", background_color=CARD_COLOR, color=ACCENT_COLOR)
        b_back.bind(on_release=lambda x: self.go_back_step())
        top_bar.add_widget(b_back)
        top_bar.add_widget(make_label(f"MACHINES ({len(self.db['machine_order'])})", FONT_SEC_LABEL, TEXT_MUTED, bold=True, height_dp=38))
        self.feed.add_widget(top_bar)

        f_scroll = ScrollView(do_scroll_x=True, do_scroll_y=False, size_hint_y=None, height=dp(36), bar_width=0)
        f_row = BoxLayout(orientation="horizontal", size_hint_x=None, width=dp(450), spacing=dp(6))
        for fk in ["ALL", "RUNNING", "IDLE", "BREAKDOWN", "MAINTENANCE"]:
            act = self.machine_filter == fk
            fb = Button(text=fk.title(), font_size=FONT_CAPTION, bold=act, background_normal="", background_color=ACCENT_COLOR if act else CARD_COLOR, color=BG_COLOR if act else TEXT_MUTED)
            fb.bind(on_release=lambda x, k=fk: self.set_machine_filter(k))
            f_row.add_widget(fb)
        f_scroll.add_widget(f_row)
        self.feed.add_widget(f_scroll)

        for mid in self.db["machine_order"]:
            m = self.db["machines"][mid]
            st = m["status"]
            if self.machine_filter != "ALL" and st != self.machine_filter:
                continue

            is_exp = self.expanded_machine_id == mid
            card = AnimatedCard(on_tap_cb=lambda m_id=mid: self.toggle_machine_expand(m_id), left_accent=STATUS_MAP.get(st, ACCENT_COLOR), orientation="vertical", padding=dp(14), spacing=dp(6))
            r1 = BoxLayout(size_hint_y=None, height=dp(24))
            r1.add_widget(make_label(f"#{m['sl']} {m['name']} ({mid})", FONT_CARD_TITLE, TEXT_PRIMARY, bold=True, height_dp=24))
            r1.add_widget(make_status_pill(st, st))
            card.add_widget(r1)

            sub_line = f"Standby Mode · PM: Oct {m.get('pm_day', 18)}" if st == "IDLE" else f"{m['product']} · Batch: {m['batch']} · PM: Oct {m.get('pm_day', 18)}"
            card.add_widget(make_label(sub_line, FONT_BODY, TEXT_MUTED, height_dp=20))

            if is_exp:
                drawer = ModernBox(bg_color=CARD_INNER, radius=dp(10), orientation="vertical", padding=dp(10), spacing=dp(4))
                drawer.add_widget(make_label(f"Batch Time: {m['act_time']} (Std: {m['std_time']}) · Delay: {m['delay_reason']}", FONT_CAPTION, ACCENT_COLOR, height_dp=18))
                drawer.add_widget(make_label(f"Operator: {m['operator']}  |  Officer: {m['officer']}", FONT_CAPTION, TEXT_MUTED, height_dp=18))
                b_open = Button(text="Edit Full Batch & Engineering Data ->", size_hint_y=None, height=dp(36), font_size=FONT_CAPTION, bold=True, background_normal="", background_color=ACCENT_COLOR, color=BG_COLOR)
                b_open.bind(on_release=lambda x, m_id=mid: self.open_machine_editor(m_id))
                drawer.add_widget(b_open)
                card.add_widget(drawer)
            self.feed.add_widget(card)

    def set_machine_filter(self, flt):
        self.machine_filter = flt
        self.switch_tab("MACHINES", record_history=False)

    def toggle_machine_expand(self, m_id):
        self.expanded_machine_id = None if self.expanded_machine_id == m_id else m_id
        self.switch_tab("MACHINES", record_history=False)

    def open_machine_editor(self, m_id):
        self.selected_machine_id = m_id
        self.switch_tab("MACHINE_DETAIL")

    def build_machine_detail(self, m_id):
        m = self.db["machines"][m_id]
        hdr = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        b_back = Button(text="<- Back", size_hint=(None, None), size=(dp(76), dp(36)), font_size=FONT_BODY, bold=True, background_normal="", background_color=CARD_COLOR, color=ACCENT_COLOR)
        b_back.bind(on_release=lambda x: self.go_back_step())
        hdr.add_widget(b_back)
        hdr.add_widget(make_label(f"#{m['sl']} {m['name']} ({m_id})", FONT_TITLE, TEXT_PRIMARY, bold=True, height_dp=36))
        self.feed.add_widget(hdr)

        b1 = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(8), left_accent=ACCENT_COLOR)
        b1.add_widget(make_label("1. STATUS, PRODUCT & BATCH", FONT_SEC_LABEL, ACCENT_COLOR, bold=True, height_dp=18))
        sp_st = Spinner(text=m["status"], values=["RUNNING", "IDLE", "BREAKDOWN", "MAINTENANCE"], size_hint_y=None, height=dp(40), background_normal="", background_color=CARD_INNER, color=TEXT_PRIMARY, bold=True)
        b1.add_widget(sp_st)
        in_prod = self.make_input(b1, "Running Product Name", m["product"])
        in_batch = self.make_input(b1, "Batch Number", m["batch"])
        self.feed.add_widget(b1)

        b2 = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(8), left_accent=STATUS_RUNNING)
        b2.add_widget(make_label("2. BATCH COMPLETION TIME & DELAY REASON", FONT_SEC_LABEL, STATUS_RUNNING, bold=True, height_dp=18))
        in_act = self.make_input(b2, "Time Taken to Finish Batch (Std: 6.0 Hours)", m["act_time"])
        in_delay = self.make_input(b2, "Why Extra Time Needed? (সময় বেশি লাগলে কারণ)", m["delay_reason"])
        self.feed.add_widget(b2)

        b4 = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(8))
        b4.add_widget(make_label("3. RESPONSIBLE OPERATOR & OFFICER", FONT_SEC_LABEL, TEXT_MUTED, bold=True, height_dp=18))
        in_op = self.make_input(b4, "Machine Operator Name", m["operator"])
        in_off = self.make_input(b4, "Responsible Officer Name", m["officer"])
        self.feed.add_widget(b4)

        btn_sv = Button(text="SAVE MACHINE BATCH RECORD", size_hint_y=None, height=dp(48), background_normal="", background_color=ACCENT_COLOR, color=BG_COLOR, bold=True)
        def _save_all(*a):
            m["status"] = sp_st.text
            m["product"] = in_prod.text.strip()
            m["batch"] = in_batch.text.strip()
            m["act_time"] = in_act.text.strip()
            m["delay_reason"] = in_delay.text.strip()
            m["operator"] = in_op.text.strip()
            m["officer"] = in_off.text.strip()
            self.save_data()
            self.expanded_machine_id = m_id
            self.go_back_step()
        btn_sv.bind(on_release=_save_all)
        self.feed.add_widget(btn_sv)

    def build_breakdown_history(self):
        hdr = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        b_back = Button(text="<- Back", size_hint=(None, None), size=(dp(72), dp(34)), font_size=FONT_CAPTION, bold=True, background_normal="", background_color=CARD_COLOR, color=ACCENT_COLOR)
        b_back.bind(on_release=lambda x: self.go_back_step())
        hdr.add_widget(b_back)
        hdr.add_widget(make_label("BREAKDOWN HISTORY", FONT_SEC_LABEL, TEXT_MUTED, bold=True, height_dp=36))
        b_new = Button(text="+ Log Breakdown", size_hint=(None, None), size=(dp(115), dp(34)), font_size=FONT_CAPTION, bold=True, background_normal="", background_color=ACCENT_TINT, color=ACCENT_COLOR)
        b_new.bind(on_release=lambda x: self.open_breakdown_modal())
        hdr.add_widget(b_new)
        self.feed.add_widget(hdr)

        for b in self.db["breakdown_history"]:
            card = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(6), left_accent=STATUS_BREAKDOWN)
            r1 = BoxLayout(size_hint_y=None, height=dp(24))
            r1.add_widget(make_label(f"{b['machine_name']} ({b['machine_id']})", FONT_CARD_TITLE, TEXT_PRIMARY, bold=True, height_dp=24))
            r1.add_widget(make_label(b["date_time"], FONT_CAPTION, TEXT_MUTED, halign="right", height_dp=24))
            card.add_widget(r1)

            card.add_widget(make_label(f"Issue: {b['issue']}", FONT_BODY, TEXT_PRIMARY, height_dp=20))
            card.add_widget(make_label(f"Root Cause: {b['rca']}", FONT_BODY, STATUS_MAINTENANCE, height_dp=20))
            card.add_widget(make_label(f"Corrective Action: {b['corrective']}", FONT_BODY, STATUS_RUNNING, height_dp=20))
            card.add_widget(make_label(f"Parts Changed?: {b['parts_changed']} ({b['parts_desc']})  |  Param Change?: {b['param_changed']} ({b['param_desc']})", FONT_CAPTION, ACCENT_COLOR, height_dp=18))
            card.add_widget(make_label(f"Work Desc: {b['work_desc']}", FONT_CAPTION, TEXT_PRIMARY, height_dp=18))
            card.add_widget(make_label(f"Completed: {b['completed_time']}  •  Responsible: {b['responsible']}", FONT_CAPTION, TEXT_MUTED, height_dp=18))
            self.feed.add_widget(card)

    def open_breakdown_modal(self):
        scroll_p = ScrollView(do_scroll_x=False, size_hint=(1, 1))
        box = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(14), spacing=dp(8))
        box.bind(minimum_height=box.setter("height"))

        box.add_widget(make_label("LOG MACHINE BREAKDOWN DETAILS", FONT_CARD_TITLE, ACCENT_COLOR, bold=True, height_dp=24))
        m_opts = [f"{mid} - {self.db['machines'][mid]['name']}" for mid in self.db["machine_order"]]
        sp_m = Spinner(text=m_opts[0], values=m_opts, size_hint_y=None, height=dp(40), background_normal="", background_color=CARD_INNER, color=ACCENT_COLOR, bold=True)
        box.add_widget(sp_m)

        in_dt = self.make_input(box, "Start Date & Time", datetime.now().strftime("%d %b %Y, %H:%M"))
        in_iss = self.make_input(box, "Issue Description (কি সমস্যা হয়েছে)", "")
        in_rca = self.make_input(box, "Root Cause (মূল কারণ)", "")
        in_cor = self.make_input(box, "Corrective Action (সমাধান)", "")

        parts_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(58), spacing=dp(3))
        parts_box.add_widget(make_label("Any Parts Change? (Yes/No)", FONT_CAPTION, TEXT_MUTED, height_dp=16))
        sp_parts = Spinner(text="No", values=["No", "Yes"], size_hint_y=None, height=dp(38), background_normal="", background_color=CARD_INNER, color=TEXT_PRIMARY, bold=True)
        parts_box.add_widget(sp_parts)
        box.add_widget(parts_box)

        parts_entry_box = BoxLayout(orientation="vertical", size_hint_y=None, height=0, opacity=0.0, spacing=dp(3))
        lbl_p = make_label("What Parts Were Given? (কী পার্টস দিয়েছেন):", FONT_CAPTION, ACCENT_COLOR, bold=True, height_dp=0)
        in_parts_desc = TextInput(text="", hint_text="Enter parts name & qty...", multiline=False, font_size=FONT_BODY, size_hint_y=None, height=0, background_normal="", background_color=CARD_INNER, foreground_color=TEXT_PRIMARY, padding=[dp(10), dp(8)])
        parts_entry_box.add_widget(lbl_p)
        parts_entry_box.add_widget(in_parts_desc)
        box.add_widget(parts_entry_box)

        def _toggle_parts(sp_inst, val):
            if val == "Yes":
                lbl_p.height = dp(16)
                in_parts_desc.height = dp(38)
                Animation(height=dp(58), opacity=1.0, duration=0.18).start(parts_entry_box)
            else:
                lbl_p.height = 0
                in_parts_desc.height = 0
                Animation(height=0, opacity=0.0, duration=0.18).start(parts_entry_box)
        sp_parts.bind(text=_toggle_parts)

        param_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(58), spacing=dp(3))
        param_box.add_widget(make_label("Parameter Change? (Yes/No)", FONT_CAPTION, TEXT_MUTED, height_dp=16))
        sp_param = Spinner(text="Select Option", values=["Yes", "No"], size_hint_y=None, height=dp(38), background_normal="", background_color=CARD_INNER, color=TEXT_PRIMARY, bold=True)
        param_box.add_widget(sp_param)
        box.add_widget(param_box)

        param_entry_box = BoxLayout(orientation="vertical", size_hint_y=None, height=0, opacity=0.0, spacing=dp(3))
        lbl_pr = make_label("Parameter Details / Remarks:", FONT_CAPTION, ACCENT_COLOR, bold=True, height_dp=0)
        in_param_desc = TextInput(text="", hint_text="Enter parameter details...", multiline=False, font_size=FONT_BODY, size_hint_y=None, height=0, background_normal="", background_color=CARD_INNER, foreground_color=TEXT_PRIMARY, padding=[dp(10), dp(8)])
        param_entry_box.add_widget(lbl_pr)
        param_entry_box.add_widget(in_param_desc)
        box.add_widget(param_entry_box)

        def _toggle_param(sp_inst, val):
            if val in ("Yes", "No"):
                lbl_pr.text = "Which Parameter Changed?:" if val == "Yes" else "Why No Parameter Changed / Remarks:"
                lbl_pr.height = dp(16)
                in_param_desc.height = dp(38)
                Animation(height=dp(58), opacity=1.0, duration=0.18).start(param_entry_box)
        sp_param.bind(text=_toggle_param)

        in_work = self.make_input(box, "Work Description (কাজের বিস্তারিত বিবরণ)", "")
        in_comp = self.make_input(box, "Completed Time & Date", datetime.now().strftime("%d %b %Y, %H:%M"))
        in_resp = self.make_input(box, "Responsible Person(s) (কে কে দায়িত্বে ছিলেন)", self.db["settings"]["user_name"])

        b_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        b_can = Button(text="Cancel", background_normal="", background_color=CARD_INNER, color=TEXT_MUTED)
        b_ok = Button(text="Save Breakdown", background_normal="", background_color=ACCENT_COLOR, color=BG_COLOR, bold=True)
        b_row.add_widget(b_can)
        b_row.add_widget(b_ok)
        box.add_widget(b_row)

        scroll_p.add_widget(box)
        pop = Popup(title="", separator_height=0, content=scroll_p, size_hint=(0.94, 0.88), background="", background_color=CARD_COLOR)
        b_can.bind(on_release=pop.dismiss)

        def _sv_bd(*a):
            mid, mname = sp_m.text.split(" - ")
            self.db["machines"][mid]["status"] = "BREAKDOWN"
            p_chg = sp_parts.text
            pr_chg = sp_param.text if sp_param.text in ("Yes", "No") else "No"
            self.db["breakdown_history"].insert(0, {
                "id": f"BD-{100 + len(self.db['breakdown_history']) + 1}",
                "machine_id": mid, "machine_name": mname,
                "date_time": in_dt.text.strip(),
                "completed_time": in_comp.text.strip(),
                "issue": in_iss.text.strip() or "Mechanical/Electrical Fault",
                "rca": in_rca.text.strip() or "Under investigation",
                "corrective": in_cor.text.strip() or "Rectified & tested",
                "parts_changed": p_chg,
                "parts_desc": in_parts_desc.text.strip() if p_chg == "Yes" else "None",
                "param_changed": pr_chg,
                "param_desc": in_param_desc.text.strip() or "Standard",
                "work_desc": in_work.text.strip() or "Completed full checkup",
                "responsible": in_resp.text.strip() or self.db["settings"]["user_name"]
            })
            self.save_data()
            pop.dismiss()
            self.switch_tab("BREAKDOWN")

        b_ok.bind(on_release=_sv_bd)
        self.open_tracked_popup(pop)

    def build_settings(self):
        cfg = self.db["settings"]
        hdr = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        b_back = Button(text="<- Back", size_hint=(None, None), size=(dp(72), dp(34)), font_size=FONT_CAPTION, bold=True, background_normal="", background_color=CARD_COLOR, color=ACCENT_COLOR)
        b_back.bind(on_release=lambda x: self.go_back_step())
        hdr.add_widget(b_back)
        hdr.add_widget(make_label("SETTINGS & PM SCHEDULE", FONT_SEC_LABEL, TEXT_MUTED, bold=True, height_dp=36))
        self.feed.add_widget(hdr)

        p_box = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(8), left_accent=ACCENT_COLOR)
        p_box.add_widget(make_label("ENGINEER PROFILE & SHIFT", FONT_SEC_LABEL, ACCENT_COLOR, bold=True, height_dp=20))
        in_name = self.make_input(p_box, "Engineer Name", cfg["user_name"])
        in_role = self.make_input(p_box, "Designation", cfg["role"])
        in_shift = self.make_input(p_box, "Shift", cfg["shift"])
        in_plant = self.make_input(p_box, "Plant Unit", cfg["plant"])

        b_sv = Button(text="Save Profile", size_hint_y=None, height=dp(42), background_normal="", background_color=ACCENT_COLOR, color=BG_COLOR, bold=True)
        def _sv_p(*a):
            cfg["user_name"] = in_name.text.strip()
            cfg["role"] = in_role.text.strip()
            cfg["shift"] = in_shift.text.strip()
            cfg["plant"] = in_plant.text.strip()
            self.save_data()
            self.switch_tab("HOME")
        b_sv.bind(on_release=_sv_p)
        p_box.add_widget(b_sv)
        self.feed.add_widget(p_box)

        pm_cfg_box = ModernBox(orientation="vertical", padding=dp(14), spacing=dp(8), left_accent=STATUS_MAINTENANCE)
        pm_cfg_box.add_widget(make_label("MACHINE PM SCHEDULE (SYNCED TO HOME CALENDAR)", FONT_SEC_LABEL, STATUS_MAINTENANCE, bold=True, height_dp=20))
        day_vals = [f"Oct {d}" for d in range(1, 32)]
        for mid in self.db["machine_order"]:
            m = self.db["machines"][mid]
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(38), spacing=dp(8))
            row.add_widget(make_label(f"#{m['sl']} {m['name']} ({mid})", FONT_BODY, TEXT_PRIMARY, height_dp=36))
            sp_day = Spinner(text=f"Oct {m.get('pm_day', 18)}", values=day_vals, size_hint=(None, None), size=(dp(96), dp(34)), font_size=FONT_CAPTION, bold=True, background_normal="", background_color=CARD_INNER, color=ACCENT_COLOR)
            def _on_day_change(spinner_inst, new_txt, mach_id=mid):
                try:
                    d_int = int(new_txt.replace("Oct ", "").strip())
                    self.db["machines"][mach_id]["pm_day"] = d_int
                    self.db["machines"][mach_id]["pm_done_oct"] = False
                    self.selected_cal_day = d_int
                    self.save_data()
                except Exception:
                    pass
            sp_day.bind(text=_on_day_change)
            row.add_widget(sp_day)
            pm_cfg_box.add_widget(row)
        self.feed.add_widget(pm_cfg_box)

    def make_input(self, parent, label_str, default_val=""):
        wrap = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(58), spacing=dp(3))
        wrap.add_widget(make_label(label_str, FONT_CAPTION, TEXT_MUTED, height_dp=16))
        ti = TextInput(text=str(default_val), multiline=False, font_size=FONT_BODY, size_hint_y=None, height=dp(38), background_normal="", background_active="", background_color=CARD_INNER, foreground_color=TEXT_PRIMARY, cursor_color=ACCENT_COLOR, padding=[dp(10), dp(9)])
        wrap.add_widget(ti)
        parent.add_widget(wrap)
        return ti

    def open_spare_modal(self):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        self.make_input(box, "Spare Part Name", "Optical Sensor Head")
        self.make_input(box, "Quantity Used", "1")
        b_ok = Button(text="Save Spare Log", size_hint_y=None, height=dp(44), background_normal="", background_color=ACCENT_COLOR, color=BG_COLOR, bold=True)
        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.9, None), height=dp(220), background="", background_color=CARD_COLOR)
        b_ok.bind(on_release=pop.dismiss)
        box.add_widget(b_ok)
        self.open_tracked_popup(pop)

    def open_handover_modal(self):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        self.make_input(box, "Shift Handover Note for Next Shift", "")
        b_ok = Button(text="Post Handover", size_hint_y=None, height=dp(44), background_normal="", background_color=ACCENT_COLOR, color=BG_COLOR, bold=True)
        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.9, None), height=dp(170), background="", background_color=CARD_COLOR)
        b_ok.bind(on_release=pop.dismiss)
        box.add_widget(b_ok)
        self.open_tracked_popup(pop)

if __name__ == "__main__":
    MachineTrackerApp().run()
