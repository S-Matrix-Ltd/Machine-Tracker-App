import json
import os
from datetime import datetime
from kivy.app import App
from kivy.lang import Builder
from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import StringProperty, ListProperty, BooleanProperty
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

import theme as T

# Register Material Icons Font
FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "MaterialIcons-Regular.ttf")
if os.path.exists(FONT_PATH):
    LabelBase.register(name="Icons", fn_regular=FONT_PATH)
else:
    LabelBase.register(name="Icons", fn_regular="Roboto")

Builder.load_file("style.kv")

PM_ORDER = {"OVERDUE": 0, "TODAY": 1, "3 DAYS": 2, "OK": 3}

INITIAL_MACHINES = [
    {"sl": 1, "name": "Brevetti", "id": "K02PR-095", "prod": "Cefixime 200mg Amp", "batch": "B26-1041", "pm_due": "3 DAYS", "pm_label": "In 3 days"},
    {"sl": 2, "name": "Korber", "id": "K02PR-089", "prod": "Pantoprazole 40mg IV", "batch": "B26-1042", "pm_due": "OK", "pm_label": "On track"},
    {"sl": 3, "name": "Light Inspection 01", "id": "K02PR-137", "prod": "Ondansetron 8mg Inj", "batch": "B26-1039", "pm_due": "OVERDUE", "pm_label": "Overdue 3d"},
    {"sl": 4, "name": "Light Inspection 02", "id": "K02PR-138", "prod": "Ketorolac 30mg Amp", "batch": "B26-1045", "pm_due": "OK", "pm_label": "On track"},
    {"sl": 5, "name": "PDLD", "id": "K02PR-134", "prod": "Cefixime 200mg Amp", "batch": "B26-1041", "pm_due": "OK", "pm_label": "On track"},
    {"sl": 6, "name": "Ampoule Labeling 01", "id": "K02PR-106", "prod": "Dexamethasone 5mg", "batch": "B26-1048", "pm_due": "OVERDUE", "pm_label": "Overdue 2d"},
    {"sl": 7, "name": "Conveyor Belt 04", "id": "K02PR-133", "prod": "Line 04 Transfer", "batch": "B26-1041", "pm_due": "OK", "pm_label": "On track"},
    {"sl": 8, "name": "Blister & Cartooning", "id": "K02PR-111", "prod": "Esomeprazole 20mg", "batch": "B26-1050", "pm_due": "TODAY", "pm_label": "Today"},
    {"sl": 9, "name": "Conveyor Belt 01", "id": "K02PR-130", "prod": "Line 01 Transfer", "batch": "B26-1042", "pm_due": "OK", "pm_label": "On track"},
    {"sl": 10, "name": "Checkweigher 01", "id": "K02PR-143", "prod": "Pantoprazole 40mg IV", "batch": "B26-1042", "pm_due": "OK", "pm_label": "On track"},
    {"sl": 11, "name": "Vail Labeling 02", "id": "K02PR-108", "prod": "Meropenem 1g Vial", "batch": "B26-1052", "pm_due": "OK", "pm_label": "On track"},
    {"sl": 12, "name": "Conveyor Belt 03", "id": "K02PR-132", "prod": "Line 03 Transfer", "batch": "B26-1052", "pm_due": "OK", "pm_label": "On track"},
    {"sl": 13, "name": "Washing and Drying", "id": "K02PR-135", "prod": "Sterile Vial Prep", "batch": "B26-1055", "pm_due": "OVERDUE", "pm_label": "Overdue 4d"},
    {"sl": 14, "name": "Vail Labeling 01", "id": "K02PR-107", "prod": "Ceftriaxone 1g Vial", "batch": "B26-1054", "pm_due": "OK", "pm_label": "On track"},
    {"sl": 15, "name": "Conveyor Belt 02", "id": "K02PR-131", "prod": "Line 02 Transfer", "batch": "B26-1054", "pm_due": "OK", "pm_label": "On track"},
    {"sl": 16, "name": "IFC Printer- (Morico)", "id": "K02PR-136", "prod": "Ceftriaxone Outer", "batch": "B26-1054", "pm_due": "3 DAYS", "pm_label": "In 3 days"},
    {"sl": 17, "name": "NKP 01", "id": "K02PR-128", "prod": "Ceftriaxone 1g Vial", "batch": "B26-1054", "pm_due": "TODAY", "pm_label": "Today"},
    {"sl": 18, "name": "NKP 02", "id": "K02PR-129", "prod": "Meropenem 1g Vial", "batch": "B26-1052", "pm_due": "OK", "pm_label": "On track"},
]


class ThemedCard(BoxLayout):
    pass


class StatusChip(BoxLayout):
    chip_text = StringProperty("RUNNING")
    dot_rgba = ListProperty(T.STATUS_RUNNING)
    bg_rgba = ListProperty(T.STATUS_TINT_MAP["RUNNING"])


class StatTile(ButtonBehavior, BoxLayout):
    icon_char = StringProperty(T.ICONS["running"])
    count_text = StringProperty("0")
    label_text = StringProperty("Running")
    status_rgba = ListProperty(T.STATUS_RUNNING)
    tint_rgba = ListProperty(T.STATUS_TINT_MAP["RUNNING"])


class QuickAction(ButtonBehavior, BoxLayout):
    icon_char = StringProperty(T.ICONS["build"])
    title_text = StringProperty("Action")


class IconButtonCircle(ButtonBehavior, Widget):
    def __init__(self, icon_char, bg_rgba=T.ACCENT_TINT, fg_rgba=T.ACCENT_COLOR, diameter=dp(48), **kwargs):
        super().__init__(size_hint=(None, None), size=(diameter, diameter), **kwargs)
        self.bg_rgba = bg_rgba
        self.fg_rgba = fg_rgba
        with self.canvas.before:
            Color(*self.bg_rgba)
            self.bg_circle = Ellipse(pos=self.pos, size=self.size)
        self.lbl = Label(
            text=icon_char,
            font_name="Icons",
            font_size=dp(20),
            color=self.fg_rgba,
            halign="center",
            valign="middle"
        )
        self.add_widget(self.lbl)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *args):
        self.bg_circle.pos = self.pos
        self.bg_circle.size = self.size
        self.lbl.pos = self.pos
        self.lbl.size = self.size


class SectionHeader(BoxLayout):
    def __init__(self, title_text, badge_count=None, action_text=None, on_action=None, extra_icon=None, on_extra=None, **kwargs):
        super().__init__(orientation="horizontal", size_hint_x=1, size_hint_y=None, height=dp(36), spacing=dp(8), **kwargs)
        lbl = Label(
            text=title_text.upper(),
            font_size=T.FONT_SEC_LABEL,
            bold=True,
            color=T.TEXT_MUTED,
            size_hint_x=None,
            width=dp(190),
            halign="left",
            valign="middle"
        )
        lbl.bind(size=lbl.setter("text_size"))
        self.add_widget(lbl)

        if badge_count is not None:
            badge = BoxLayout(size_hint=(None, None), size=(dp(24), dp(20)), pos_hint={"center_y": 0.5})
            with badge.canvas.before:
                Color(*T.ACCENT_TINT)
                r = RoundedRectangle(pos=badge.pos, size=badge.size, radius=[dp(6)])
            badge.bind(pos=lambda inst, v: setattr(r, "pos", v), size=lambda inst, v: setattr(r, "size", v))
            badge.add_widget(Label(text=str(badge_count), font_size=T.FONT_CAPTION, bold=True, color=T.ACCENT_COLOR))
            self.add_widget(badge)

        self.add_widget(Widget())

        if extra_icon and on_extra:
            cal_btn = IconButtonCircle(extra_icon, diameter=dp(34))
            cal_btn.pos_hint = {"center_y": 0.5}
            cal_btn.bind(on_release=lambda x: on_extra())
            self.add_widget(cal_btn)

        if action_text and on_action:
            act_btn = Button(
                text=action_text,
                font_size=T.FONT_CAPTION,
                bold=True,
                color=T.ACCENT_COLOR,
                background_normal="",
                background_color=(0, 0, 0, 0),
                size_hint=(None, None),
                size=(dp(64), dp(36)),
                pos_hint={"center_y": 0.5}
            )
            act_btn.bind(on_release=lambda x: on_action())
            self.add_widget(act_btn)


class PmCard(BoxLayout):
    def __init__(self, machine_dict, on_complete_cb, **kwargs):
        super().__init__(orientation="horizontal", size_hint_x=1, size_hint_y=None, padding=[dp(14), dp(12)], spacing=dp(10), **kwargs)
        self.bind(minimum_height=self.setter("height"))

        pm_st = machine_dict.get("pm_status", "OVERDUE")
        if pm_st == "OVERDUE":
            self.bar_col = T.STATUS_BREAKDOWN
            chip_tint = T.STATUS_TINT_MAP["BREAKDOWN"]
        elif pm_st == "TODAY":
            self.bar_col = T.STATUS_MAINTENANCE
            chip_tint = T.STATUS_TINT_MAP["MAINTENANCE"]
        else:
            self.bar_col = T.ACCENT_COLOR
            chip_tint = T.ACCENT_TINT

        with self.canvas.before:
            Color(*T.CARD_COLOR)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[T.RADIUS_CARD])
            Color(*T.BORDER_COLOR)
            self.border_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, T.RADIUS_CARD), width=1)
            Color(*self.bar_col)
            self.left_bar = RoundedRectangle(pos=(self.x, self.y + dp(8)), size=(dp(3), max(dp(10), self.height - dp(16))), radius=[dp(2)])
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        info_col = BoxLayout(orientation="vertical", size_hint_x=1, size_hint_y=None, spacing=dp(6))
        info_col.bind(minimum_height=info_col.setter("height"))

        # Top row: Machine Name Bold + ID Muted
        top_r = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22), spacing=dp(8))
        name_l = Label(
            text=f"{machine_dict['name']}  ",
            font_size=T.FONT_CARD_TITLE,
            bold=True,
            color=T.TEXT_PRIMARY,
            size_hint_x=1,
            halign="left",
            valign="middle"
        )
        name_l.bind(size=name_l.setter("text_size"))
        id_l = Label(
            text=machine_dict["id"],
            font_size=T.FONT_CAPTION,
            color=T.TEXT_MUTED,
            size_hint_x=None,
            width=dp(80),
            halign="right",
            valign="middle"
        )
        id_l.bind(size=id_l.setter("text_size"))
        top_r.add_widget(name_l)
        top_r.add_widget(id_l)
        info_col.add_widget(top_r)

        # Bottom row: Small Chip + Last PM Muted
        bot_r = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24), spacing=dp(10))
        chip = StatusChip(
            chip_text=machine_dict.get("pm_label", pm_st),
            dot_rgba=self.bar_col,
            bg_rgba=chip_tint
        )
        last_l = Label(
            text=f"Last PM: {machine_dict.get('last_pm_short', '18 Sep')}",
            font_size=T.FONT_CAPTION,
            color=T.TEXT_MUTED,
            halign="left",
            valign="middle"
        )
        last_l.bind(size=last_l.setter("text_size"))
        bot_r.add_widget(chip)
        bot_r.add_widget(last_l)
        info_col.add_widget(bot_r)

        self.add_widget(info_col)

        # 48dp Round Check Icon Button
        chk_btn = IconButtonCircle(
            icon_char=T.ICONS["check"],
            bg_rgba=(0.133, 0.773, 0.369, 0.16),
            fg_rgba=T.STATUS_RUNNING,
            diameter=dp(48)
        )
        chk_btn.pos_hint = {"center_y": 0.5}
        chk_btn.bind(on_release=lambda x: on_complete_cb(machine_dict["id"]))
        self.add_widget(chk_btn)

    def _update_canvas(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, T.RADIUS_CARD)
        self.left_bar.pos = (self.x + dp(1), self.y + dp(10))
        self.left_bar.size = (dp(3), max(dp(12), self.height - dp(20)))


class UptimeMiniChart(ThemedCard):
    def __init__(self, days_data, **kwargs):
        super().__init__(**kwargs)
        self.days_data = days_data
        avg_val = sum(v for _, v in days_data) / max(1, len(days_data))

        # Top row: Title + Avg % at top right
        hdr = BoxLayout(size_hint_y=None, height=dp(24))
        t_lbl = Label(text="7-Day Availability", font_size=T.FONT_BODY, bold=True, color=T.TEXT_PRIMARY, halign="left", valign="middle")
        t_lbl.bind(size=t_lbl.setter("text_size"))
        avg_lbl = Label(text=f"Avg {avg_val:.1f}%", font_size=T.FONT_BODY, bold=True, color=T.ACCENT_COLOR, halign="right", valign="middle")
        avg_lbl.bind(size=avg_lbl.setter("text_size"))
        hdr.add_widget(t_lbl)
        hdr.add_widget(avg_lbl)
        self.add_widget(hdr)

        # Canvas Drawing Area
        self.plot_area = Widget(size_hint_x=1, size_hint_y=None, height=dp(96))
        self.plot_area.bind(pos=self._redraw_bars, size=self._redraw_bars)
        self.add_widget(self.plot_area)

        # Day Labels (Mon, Tue, Wed...)
        day_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
        for idx, (d_name, _) in enumerate(days_data):
            is_today = idx == len(days_data) - 1
            dl = Label(
                text=d_name,
                font_size=T.FONT_CAPTION,
                bold=is_today,
                color=T.ACCENT_COLOR if is_today else T.TEXT_MUTED
            )
            day_row.add_widget(dl)
        self.add_widget(day_row)

    def _redraw_bars(self, *args):
        self.plot_area.canvas.clear()
        x0, y0 = self.plot_area.pos
        w, h = self.plot_area.size
        if w <= 10 or h <= 10:
            return

        n = len(self.days_data)
        slot_w = w / float(n)
        bar_w = min(dp(12), slot_w * 0.38)

        with self.plot_area.canvas:
            # Dashed 85% Target Line
            target_y = y0 + (0.85 * (h - dp(12)))
            Color(0.545, 0.596, 0.663, 0.45)
            dash_w = dp(6)
            gap_w = dp(5)
            curr_x = x0
            while curr_x < x0 + w:
                end_x = min(x0 + w, curr_x + dash_w)
                Line(points=[curr_x, target_y, end_x, target_y], width=1.1)
                curr_x += dash_w + gap_w

            # Thin Vertical Bars (Muted for past days, Accent for Today)
            for i, (_, val) in enumerate(self.days_data):
                is_today = i == n - 1
                pct = max(0.08, min(1.0, val / 100.0))
                bh = pct * (h - dp(12))
                bx = x0 + (i * slot_w) + (slot_w - bar_w) / 2.0
                if is_today:
                    Color(*T.ACCENT_COLOR)
                else:
                    Color(0.32, 0.39, 0.49, 0.65)
                RoundedRectangle(pos=(bx, y0), size=(bar_w, bh), radius=[dp(4)])


class TappableCard(ButtonBehavior, ThemedCard):
    pass


class NavTabButton(ButtonBehavior, BoxLayout):
    def __init__(self, icon_char, label_text, on_tap, **kwargs):
        super().__init__(orientation="vertical", size_hint_x=1, padding=[0, dp(4)], spacing=dp(2), **kwargs)
        self.on_tap = on_tap
        self.indicator = Widget(size_hint=(None, None), size=(dp(24), dp(3)), pos_hint={"center_x": 0.5})
        with self.indicator.canvas:
            self.ind_col = Color(0, 0, 0, 0)
            self.ind_rect = RoundedRectangle(pos=self.indicator.pos, size=self.indicator.size, radius=[dp(1.5)])
        self.indicator.bind(pos=self._sync_ind, size=self._sync_ind)

        self.icon_lbl = Label(text=icon_char, font_name="Icons", font_size=dp(20), color=T.TEXT_MUTED, size_hint_y=None, height=dp(24))
        self.txt_lbl = Label(text=label_text, font_size=T.FONT_CAPTION, color=T.TEXT_MUTED, size_hint_y=None, height=dp(16))

        self.add_widget(self.indicator)
        self.add_widget(self.icon_lbl)
        self.add_widget(self.txt_lbl)
        self.bind(on_release=lambda x: self.on_tap())

    def _sync_ind(self, *args):
        self.ind_rect.pos = self.indicator.pos
        self.ind_rect.size = self.indicator.size

    def set_active(self, active):
        if active:
            self.ind_col.rgba = T.ACCENT_COLOR
            self.icon_lbl.color = T.ACCENT_COLOR
            self.txt_lbl.color = T.ACCENT_COLOR
            self.txt_lbl.bold = True
        else:
            self.ind_col.rgba = (0, 0, 0, 0)
            self.icon_lbl.color = T.TEXT_MUTED
            self.txt_lbl.color = T.TEXT_MUTED
            self.txt_lbl.bold = False


class MachineTrackerApp(App):
    def build(self):
        self.title = "Smart Eng-Ops"
        self.data_file = os.path.join(self.user_data_dir, "smatrix_clean_v4.json")
        self.load_data()

        self.current_tab = "HOME"
        self.machine_filter = "ALL"
        self.show_all_pms = False
        self.selected_machine_id = self.db["machine_order"][0]

        self.root_box = BoxLayout(orientation="vertical")
        with self.root_box.canvas.before:
            Color(*T.BG_COLOR)
            self.bg_rect = Rectangle(pos=self.root_box.pos, size=self.root_box.size)
        self.root_box.bind(pos=self._sync_bg, size=self._sync_bg)

        # Main ScrollView with 16dp horizontal padding
        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(2))
        self.feed = BoxLayout(
            orientation="vertical",
            size_hint_x=1,
            size_hint_y=None,
            padding=[T.PAD_SCREEN, dp(16), T.PAD_SCREEN, dp(32)],
            spacing=T.GAP_CARD
        )
        self.feed.bind(minimum_height=self.feed.setter("height"))
        self.scroll.add_widget(self.feed)
        self.root_box.add_widget(self.scroll)

        # Subtle Bottom Navigation Bar (48dp+ touch targets, no heavy blue blocks)
        self.nav_wrap = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(58), padding=[dp(8), 0])
        with self.nav_wrap.canvas.before:
            Color(*T.CARD_COLOR)
            self.nav_bg = Rectangle(pos=self.nav_wrap.pos, size=self.nav_wrap.size)
            Color(*T.BORDER_COLOR)
            self.nav_line = Line(points=[0, dp(58), 1000, dp(58)], width=1)
        self.nav_wrap.bind(pos=self._sync_nav, size=self._sync_nav)

        self.tab_btns = {
            "HOME": NavTabButton(T.ICONS["home"], "Home", lambda: self.switch_tab("HOME")),
            "MACHINES": NavTabButton(T.ICONS["machines"], "Machines", lambda: self.switch_tab("MACHINES")),
            "CAPA": NavTabButton(T.ICONS["capa"], "CAPA", lambda: self.switch_tab("CAPA")),
            "SETTINGS": NavTabButton(T.ICONS["settings"], "Settings", lambda: self.switch_tab("SETTINGS")),
        }
        for b in self.tab_btns.values():
            self.nav_wrap.add_widget(b)
        self.root_box.add_widget(self.nav_wrap)

        self.switch_tab("HOME")
        return self.root_box

    def _sync_bg(self, *args):
        self.bg_rect.pos = self.root_box.pos
        self.bg_rect.size = self.root_box.size

    def _sync_nav(self, *args):
        self.nav_bg.pos = self.nav_wrap.pos
        self.nav_bg.size = self.nav_wrap.size
        self.nav_line.points = [self.nav_wrap.x, self.nav_wrap.top, self.nav_wrap.right, self.nav_wrap.top]

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    self.db = json.load(f)
                return
            except Exception:
                pass

        self.db = {
            "settings": {
                "user_name": "Ahmeed Sunny",
                "role": "Sr. Automation Engr",
                "shift": "Shift A",
                "plant": "Sterile Unit"
            },
            "uptime_7d": [
                ["Mon", 86], ["Tue", 89], ["Wed", 82], ["Thu", 91], ["Fri", 88], ["Sat", 93], ["Sun", 90]
            ],
            "machine_order": [],
            "machines": {},
            "capa_logs": [
                {
                    "id": "CAPA-101", "machine_id": "K02PR-106", "machine_name": "Ampoule Labeling 01",
                    "severity": "CRITICAL", "status": "OPEN", "date": "17 Oct",
                    "issue": "Label gap optical sensor intermittent false trigger at >320 RPM",
                    "rca": "Adhesive residue buildup on fiber lens",
                    "action": "Cleaned lens with IPA & recalibrated threshold to 75%",
                    "parts": "Optical Sensor Swab", "person": "Ahmeed Sunny"
                },
                {
                    "id": "CAPA-102", "machine_id": "K02PR-135", "machine_name": "Washing and Drying",
                    "severity": "HIGH", "status": "IN PROGRESS", "date": "16 Oct",
                    "issue": "Tunnel drying zone temperature fluctuation (+/- 6C)",
                    "rca": "Blower HEPA filter partial choking",
                    "action": "Replaced HEPA Filter G4-09 & tuned PID loop",
                    "parts": "HEPA Filter G4-09", "person": "Engr. Mahmudul"
                }
            ],
            "handovers": [
                {"time": "17 Oct 14:00", "by": "Ahmeed Sunny", "note": "Verify Ampoule Labeling 01 reject bin every 30 mins."}
            ]
        }

        for idx, m in enumerate(INITIAL_MACHINES):
            mid = m["id"]
            self.db["machine_order"].append(mid)
            st = "RUNNING"
            if idx == 5:
                st = "BREAKDOWN"
            elif idx == 12:
                st = "MAINTENANCE"
            elif idx in (6, 14):
                st = "IDLE"

            self.db["machines"][mid] = {
                "sl": m["sl"], "name": m["name"], "id": mid, "status": st,
                "product": m["prod"], "batch": m["batch"],
                "pm_status": m["pm_due"], "pm_label": m["pm_label"],
                "last_pm_short": "18 Sep", "operator": "Md. Tanvir", "officer": "Kamrul Hasan",
                "std_time": "6.0h", "act_time": "7.5h" if idx == 5 else "5.8h",
                "delay_reason": "Sensor recalibration" if idx == 5 else "On schedule",
                "parts_used": "None"
            }
        self.save_data()

    def save_data(self):
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.db, f)
        except Exception:
            pass

    def switch_tab(self, tab_name):
        self.current_tab = tab_name
        for k, b in self.tab_btns.items():
            b.set_active(k == tab_name or (tab_name == "MACHINE_DETAIL" and k == "MACHINES"))

        self.feed.clear_widgets()
        self.feed.opacity = 0.0
        Animation(opacity=1.0, duration=0.20).start(self.feed)

        if tab_name == "HOME":
            self.build_home()
        elif tab_name == "MACHINES":
            self.build_machines()
        elif tab_name == "MACHINE_DETAIL":
            self.build_machine_detail(self.selected_machine_id)
        elif tab_name == "CAPA":
            self.build_capa()
        elif tab_name == "SETTINGS":
            self.build_settings()

    def add_section_gap(self):
        self.feed.add_widget(Widget(size_hint_y=None, height=T.GAP_SECTION - T.GAP_CARD))

    # =========================================================================
    # HOME SCREEN (STRICT 7-PART ARCHITECTURE)
    # =========================================================================
    def build_home(self):
        cfg = self.db["settings"]
        m_list = list(self.db["machines"].values())
        total_m = max(1, len(m_list))

        c_run = sum(1 for m in m_list if m["status"] == "RUNNING")
        c_idle = sum(1 for m in m_list if m["status"] == "IDLE")
        c_bd = sum(1 for m in m_list if m["status"] == "BREAKDOWN")
        c_maint = sum(1 for m in m_list if m["status"] == "MAINTENANCE")
        uptime_pct = int(round((c_run / total_m) * 100))

        overdue_cnt = sum(1 for m in m_list if m.get("pm_status") == "OVERDUE")
        open_issues = sum(1 for c in self.db["capa_logs"] if c.get("status") != "CLOSED")

        # 1. Clean Header without colored box + Initials Avatar on Right
        hdr_row = BoxLayout(orientation="horizontal", size_hint_x=1, size_hint_y=None, height=dp(68), spacing=dp(12))
        hdr_left = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))

        hr = datetime.now().hour
        greet_str = "Good morning" if hr < 12 else ("Good afternoon" if hr < 17 else "Good evening")

        lbl_g = Label(text=greet_str, font_size=T.FONT_BODY, color=T.TEXT_MUTED, halign="left", valign="middle")
        lbl_g.bind(size=lbl_g.setter("text_size"))
        lbl_n = Label(text=cfg["user_name"], font_size=T.FONT_TITLE, bold=True, color=T.TEXT_PRIMARY, halign="left", valign="middle")
        lbl_n.bind(size=lbl_n.setter("text_size"))
        lbl_m = Label(text=f"{cfg['role']} · {cfg['shift']} · {cfg['plant']}", font_size=T.FONT_CAPTION, color=T.TEXT_MUTED, halign="left", valign="middle")
        lbl_m.bind(size=lbl_m.setter("text_size"))

        hdr_left.add_widget(lbl_g)
        hdr_left.add_widget(lbl_n)
        hdr_left.add_widget(lbl_m)
        hdr_row.add_widget(hdr_left)

        initials = "".join([w[0] for w in cfg["user_name"].split()[:2]]).upper() or "AS"
        avatar = BoxLayout(size_hint=(None, None), size=(dp(44), dp(44)), pos_hint={"center_y": 0.5})
        with avatar.canvas.before:
            Color(*T.ACCENT_TINT)
            av_el = Ellipse(pos=avatar.pos, size=avatar.size)
            Color(*T.ACCENT_COLOR)
            av_ln = Line(circle=(avatar.center_x, avatar.center_y, dp(22)), width=1.1)
        avatar.bind(
            pos=lambda inst, v: (setattr(av_el, "pos", v), setattr(av_ln, "circle", (inst.center_x, inst.center_y, dp(22)))),
            size=lambda inst, v: setattr(av_el, "size", v)
        )
        avatar.add_widget(Label(text=initials, font_size=T.FONT_BODY, bold=True, color=T.ACCENT_COLOR))
        hdr_row.add_widget(avatar)
        self.feed.add_widget(hdr_row)

        # 2. 2x2 KPI StatTiles (No "Tap to view..." clutter)
        kpi_grid = GridLayout(cols=2, size_hint_x=1, size_hint_y=None, spacing=T.GAP_CARD)
        kpi_grid.bind(minimum_height=kpi_grid.setter("height"))

        tiles_cfg = [
            ("RUNNING", T.ICONS["running"], str(c_run), "Running"),
            ("IDLE", T.ICONS["idle"], str(c_idle), "Idle"),
            ("BREAKDOWN", T.ICONS["breakdown"], str(c_bd), "Breakdown"),
            ("MAINTENANCE", T.ICONS["maintenance"], str(c_maint), "Maintenance"),
        ]
        for st_key, ic, cnt_s, lbl_s in tiles_cfg:
            tile = StatTile(
                icon_char=ic,
                count_text=cnt_s,
                label_text=lbl_s,
                status_rgba=T.STATUS_MAP[st_key],
                tint_rgba=T.STATUS_TINT_MAP[st_key]
            )
            tile.bind(on_release=lambda x, k=st_key: self.filter_machines_from_home(k))
            kpi_grid.add_widget(tile)
        self.feed.add_widget(kpi_grid)

        # 3. Today's Focus Slim Inline Card (Overdue PM | Open Issues | Uptime %)
        focus_card = ThemedCard(orientation="horizontal", padding=[dp(12), dp(12)], spacing=0)
        focus_card.height = dp(64)
        focus_card.size_hint_y = None

        overdue_col = T.STATUS_BREAKDOWN if overdue_cnt > 0 else T.TEXT_PRIMARY
        metrics = [
            (str(overdue_cnt), "Overdue PM", overdue_col),
            (str(open_issues), "Open Issues", T.TEXT_PRIMARY),
            (f"{uptime_pct}%", "Uptime", T.ACCENT_COLOR),
        ]
        for idx, (m_val, m_lbl, m_col) in enumerate(metrics):
            col_b = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))
            v_l = Label(text=m_val, font_size=sp(18), bold=True, color=m_col, halign="center", valign="middle")
            k_l = Label(text=m_lbl, font_size=T.FONT_CAPTION, color=T.TEXT_MUTED, halign="center", valign="middle")
            col_b.add_widget(v_l)
            col_b.add_widget(k_l)
            focus_card.add_widget(col_b)
            if idx < 2:
                div = Widget(size_hint_x=None, width=dp(1))
                with div.canvas:
                    Color(*T.BORDER_COLOR)
                    d_rect = Rectangle(pos=div.pos, size=div.size)
                div.bind(pos=lambda inst, v, r=d_rect: setattr(r, "pos", v), size=lambda inst, v, r=d_rect: setattr(r, "size", v))
                focus_card.add_widget(div)
        self.feed.add_widget(focus_card)

        self.add_section_gap()

        # 4. Quick Actions Row (4 Monochrome Icon-Over-Label Buttons)
        self.feed.add_widget(SectionHeader("Quick Actions"))
        qa_grid = GridLayout(cols=4, size_hint_x=1, size_hint_y=None, height=dp(74), spacing=T.GAP_GRID)
        qa_items = [
            (T.ICONS["report"], "Log BD", lambda: self.open_capa_modal("BREAKDOWN")),
            (T.ICONS["build"], "Add Issue", lambda: self.open_capa_modal("ISSUE")),
            (T.ICONS["inventory"], "Add Spare", self.open_spare_modal),
            (T.ICONS["handover"], "Handover", self.open_handover_modal),
        ]
        for ic_c, t_str, cb in qa_items:
            qa_btn = QuickAction(icon_char=ic_c, title_text=t_str)
            qa_btn.bind(on_release=lambda x, fn=cb: fn())
            qa_grid.add_widget(qa_btn)
        self.feed.add_widget(qa_grid)

        self.add_section_gap()

        # 5. Preventive Maintenance Section (Count Badge, Calendar Icon, Top 3 Urgent Cards)
        pm_due = [m for m in m_list if m.get("pm_status", "OK") != "OK"]
        pm_due.sort(key=lambda x: PM_ORDER.get(x.get("pm_status", "OK"), 9))

        self.feed.add_widget(
            SectionHeader(
                title_text="Preventive Maintenance",
                badge_count=len(pm_due),
                action_text="Show 3" if self.show_all_pms else "View all",
                on_action=self.toggle_pm_view_all,
                extra_icon=T.ICONS["calendar"],
                on_extra=self.open_pm_calendar_modal
            )
        )

        if not pm_due:
            emp = ThemedCard(orientation="horizontal", padding=dp(16), spacing=dp(10))
            emp.add_widget(Label(text=T.ICONS["check_circle"], font_name="Icons", font_size=dp(22), color=T.STATUS_RUNNING, size_hint_x=None, width=dp(28)))
            emp.add_widget(Label(text="All PMs on track", font_size=T.FONT_BODY, bold=True, color=T.TEXT_PRIMARY, halign="left"))
            self.feed.add_widget(emp)
        else:
            visible_pms = pm_due if self.show_all_pms else pm_due[:3]
            for pm_m in visible_pms:
                self.feed.add_widget(PmCard(pm_m, on_complete_cb=self.open_pm_confirm_sheet))

        self.add_section_gap()

        # 6. Uptime Trend Mini Chart (Canvas-drawn thin bars + 85% dashed target line)
        self.feed.add_widget(SectionHeader("Uptime Trend"))
        self.feed.add_widget(UptimeMiniChart(self.db["uptime_7d"]))

    def filter_machines_from_home(self, status_key):
        self.machine_filter = status_key
        self.switch_tab("MACHINES")

    def toggle_pm_view_all(self):
        self.show_all_pms = not self.show_all_pms
        self.switch_tab("HOME")

    def open_pm_confirm_sheet(self, m_id):
        m = self.db["machines"][m_id]
        box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        box.add_widget(Label(text=f"Complete PM · {m['name']} ({m_id})", font_size=T.FONT_CARD_TITLE, bold=True, color=T.TEXT_PRIMARY, size_hint_y=None, height=dp(24)))

        in_dt = self.make_field(box, "Completion Date", datetime.now().strftime("%d %b %Y"))
        in_rem = self.make_field(box, "Technician Remarks", "Routine lubrication, sensor cleaning & calibration verified")

        btn_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        b_cancel = Button(text="Cancel", background_normal="", background_color=T.CARD_ALT_COLOR, color=T.TEXT_MUTED, bold=True)
        b_save = Button(text="Confirm PM", background_normal="", background_color=T.STATUS_RUNNING, color=T.BG_COLOR, bold=True)
        btn_row.add_widget(b_cancel)
        btn_row.add_widget(b_save)
        box.add_widget(btn_row)

        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.92, None), height=dp(290), background="", background_color=T.CARD_COLOR)
        b_cancel.bind(on_release=pop.dismiss)

        def _save(*a):
            m["pm_status"] = "OK"
            m["pm_label"] = "On track"
            m["last_pm_short"] = in_dt.text.strip()[:6]
            self.save_data()
            pop.dismiss()
            self.switch_tab(self.current_tab)

        b_save.bind(on_release=_save)
        pop.open()

    # =========================================================================
    # MACHINES LIST & DETAIL DASHBOARD
    # =========================================================================
    def build_machines(self):
        self.feed.add_widget(SectionHeader("Plant Machines", badge_count=len(self.db["machine_order"])))

        # Filter Chips Row
        f_scroll = ScrollView(do_scroll_x=True, do_scroll_y=False, size_hint_y=None, height=dp(40))
        f_row = BoxLayout(orientation="horizontal", size_hint_x=None, width=dp(460), spacing=dp(8))
        for k in ["ALL", "RUNNING", "IDLE", "BREAKDOWN", "MAINTENANCE"]:
            active = self.machine_filter == k
            b = Button(
                text=k.title(),
                font_size=T.FONT_CAPTION,
                bold=active,
                background_normal="",
                background_color=T.ACCENT_TINT if active else T.CARD_COLOR,
                color=T.ACCENT_COLOR if active else T.TEXT_MUTED
            )
            b.bind(on_release=lambda x, flt=k: self.set_m_filter(flt))
            f_row.add_widget(b)
        f_scroll.add_widget(f_row)
        self.feed.add_widget(f_scroll)

        for mid in self.db["machine_order"]:
            m = self.db["machines"][mid]
            st = m["status"]
            if self.machine_filter != "ALL" and st != self.machine_filter:
                continue

            card = TappableCard(padding=dp(14), spacing=dp(8))
            card.bind(on_release=lambda x, m_id=mid: self.open_machine(m_id))

            r1 = BoxLayout(size_hint_y=None, height=dp(24))
            t_l = Label(text=f"#{m['sl']} {m['name']}", font_size=T.FONT_CARD_TITLE, bold=True, color=T.TEXT_PRIMARY, halign="left", valign="middle")
            t_l.bind(size=t_l.setter("text_size"))
            chip = StatusChip(chip_text=st, dot_rgba=T.STATUS_MAP[st], bg_rgba=T.STATUS_TINT_MAP[st])
            r1.add_widget(t_l)
            r1.add_widget(chip)
            card.add_widget(r1)

            sub_txt = f"{mid} · Standby (No active batch)" if st == "IDLE" else f"{mid} · {m['product']} ({m['batch']})"
            s_l = Label(text=sub_txt, font_size=T.FONT_BODY, color=T.TEXT_MUTED, size_hint_y=None, height=dp(20), halign="left", valign="middle")
            s_l.bind(size=s_l.setter("text_size"))
            card.add_widget(s_l)
            self.feed.add_widget(card)

    def set_m_filter(self, flt):
        self.machine_filter = flt
        self.switch_tab("MACHINES")

    def open_machine(self, m_id):
        self.selected_machine_id = m_id
        self.switch_tab("MACHINE_DETAIL")

    def build_machine_detail(self, m_id):
        m = self.db["machines"][m_id]
        st = m["status"]

        top = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        back_b = IconButtonCircle(T.ICONS["back"], diameter=dp(42))
        back_b.bind(on_release=lambda x: self.switch_tab("MACHINES"))
        t_l = Label(text=f"{m['name']} ({m_id})", font_size=T.FONT_TITLE, bold=True, color=T.TEXT_PRIMARY, halign="left", valign="middle")
        t_l.bind(size=t_l.setter("text_size"))
        top.add_widget(back_b)
        top.add_widget(t_l)
        self.feed.add_widget(top)

        form = ThemedCard(padding=dp(16), spacing=dp(10))
        sp_st = Spinner(
            text=st,
            values=["RUNNING", "IDLE", "BREAKDOWN", "MAINTENANCE"],
            size_hint_y=None,
            height=dp(44),
            background_normal="",
            background_color=T.CARD_ALT_COLOR,
            color=T.ACCENT_COLOR,
            bold=True
        )
        form.add_widget(sp_st)

        in_prod = self.make_field(form, "Running Product", m["product"])
        in_batch = self.make_field(form, "Batch Number", m["batch"])
        in_act = self.make_field(form, "Batch Completion Time (Std: 6.0h)", m["act_time"])
        in_delay = self.make_field(form, "Delay Reason (If > Standard Time)", m["delay_reason"])
        in_parts = self.make_field(form, "New Spare Parts Installed", m["parts_used"])
        in_op = self.make_field(form, "Machine Operator", m["operator"])
        in_off = self.make_field(form, "Responsible Officer", m["officer"])

        save_b = Button(
            text="Save Machine Batch Record",
            size_hint_y=None,
            height=dp(48),
            background_normal="",
            background_color=T.ACCENT_COLOR,
            color=T.BG_COLOR,
            bold=True
        )

        def _sv(*a):
            m["status"] = sp_st.text
            m["product"] = in_prod.text.strip()
            m["batch"] = in_batch.text.strip()
            m["act_time"] = in_act.text.strip()
            m["delay_reason"] = in_delay.text.strip()
            m["parts_used"] = in_parts.text.strip()
            m["operator"] = in_op.text.strip()
            m["officer"] = in_off.text.strip()
            self.save_data()
            self.switch_tab("MACHINES")

        save_b.bind(on_release=_sv)
        form.add_widget(save_b)
        self.feed.add_widget(form)

    # =========================================================================
    # CAPA & SETTINGS TABS
    # =========================================================================
    def build_capa(self):
        self.feed.add_widget(
            SectionHeader(
                "CAPA & Breakdown Register",
                badge_count=len(self.db["capa_logs"]),
                action_text="+ Log New",
                on_action=lambda: self.open_capa_modal("BREAKDOWN")
            )
        )
        for c in self.db["capa_logs"]:
            card = ThemedCard(padding=dp(14), spacing=dp(6))
            r1 = BoxLayout(size_hint_y=None, height=dp(24))
            tl = Label(text=f"{c['machine_name']} ({c['machine_id']})", font_size=T.FONT_CARD_TITLE, bold=True, color=T.TEXT_PRIMARY, halign="left")
            tl.bind(size=tl.setter("text_size"))
            chip = StatusChip(
                chip_text=c["status"],
                dot_rgba=T.STATUS_BREAKDOWN if c["status"] == "OPEN" else T.STATUS_MAINTENANCE,
                bg_rgba=T.STATUS_TINT_MAP["BREAKDOWN"] if c["status"] == "OPEN" else T.STATUS_TINT_MAP["MAINTENANCE"]
            )
            r1.add_widget(tl)
            r1.add_widget(chip)
            card.add_widget(r1)

            for line_txt in [f"Issue: {c['issue']}", f"RCA: {c['rca']}", f"Action: {c['action']}", f"Parts: {c['parts']} · By {c['person']}"]:
                l = Label(text=line_txt, font_size=T.FONT_BODY, color=T.TEXT_MUTED, size_hint_y=None, halign="left")
                l.bind(width=lambda inst, w: setattr(inst, "text_size", (w, None)), texture_size=lambda inst, ts: setattr(inst, "height", ts[1] + dp(2)))
                card.add_widget(l)
            self.feed.add_widget(card)

    def build_settings(self):
        cfg = self.db["settings"]
        self.feed.add_widget(SectionHeader("Engineer & Plant Settings"))
        card = ThemedCard(padding=dp(16), spacing=dp(10))
        in_n = self.make_field(card, "Engineer Name", cfg["user_name"])
        in_r = self.make_field(card, "Role / Designation", cfg["role"])
        in_s = self.make_field(card, "Shift", cfg["shift"])
        in_p = self.make_field(card, "Plant Name", cfg["plant"])

        b_sv = Button(text="Save Settings", size_hint_y=None, height=dp(48), background_normal="", background_color=T.ACCENT_COLOR, color=T.BG_COLOR, bold=True)

        def _sv(*a):
            cfg["user_name"] = in_n.text.strip()
            cfg["role"] = in_r.text.strip()
            cfg["shift"] = in_s.text.strip()
            cfg["plant"] = in_p.text.strip()
            self.save_data()
            self.switch_tab("HOME")

        b_sv.bind(on_release=_sv)
        card.add_widget(b_sv)
        self.feed.add_widget(card)

    # =========================================================================
    # HELPER MODALS
    # =========================================================================
    def make_field(self, parent, label_txt, val=""):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(62), spacing=dp(4))
        lbl = Label(text=label_txt, font_size=T.FONT_CAPTION, color=T.TEXT_MUTED, size_hint_y=None, height=dp(16), halign="left")
        lbl.bind(size=lbl.setter("text_size"))
        ti = TextInput(
            text=str(val),
            multiline=False,
            font_size=T.FONT_BODY,
            size_hint_y=None,
            height=dp(40),
            background_normal="",
            background_active="",
            background_color=T.CARD_ALT_COLOR,
            foreground_color=T.TEXT_PRIMARY,
            cursor_color=T.ACCENT_COLOR,
            padding=[dp(10), dp(10)]
        )
        box.add_widget(lbl)
        box.add_widget(ti)
        parent.add_widget(box)
        return ti

    def open_capa_modal(self, mode="BREAKDOWN"):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(8))
        m_opts = [f"{mid} - {self.db['machines'][mid]['name']}" for mid in self.db["machine_order"]]
        sp_m = Spinner(text=m_opts[0], values=m_opts, size_hint_y=None, height=dp(42), background_normal="", background_color=T.CARD_ALT_COLOR, color=T.TEXT_PRIMARY)
        box.add_widget(sp_m)

        in_iss = self.make_field(box, "Issue Description", "")
        in_rca = self.make_field(box, "Root Cause (RCA)", "")
        in_act = self.make_field(box, "Corrective Action", "")
        in_prt = self.make_field(box, "Parts Replaced", "None")

        b_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        b_can = Button(text="Cancel", background_normal="", background_color=T.CARD_ALT_COLOR, color=T.TEXT_MUTED)
        b_ok = Button(text="Save Record", background_normal="", background_color=T.ACCENT_COLOR, color=T.BG_COLOR, bold=True)
        b_row.add_widget(b_can)
        b_row.add_widget(b_ok)
        box.add_widget(b_row)

        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.92, None), height=dp(420), background="", background_color=T.CARD_COLOR)
        b_can.bind(on_release=pop.dismiss)

        def _sv(*a):
            mid, mname = sp_m.text.split(" - ")
            if mode == "BREAKDOWN":
                self.db["machines"][mid]["status"] = "BREAKDOWN"
            self.db["capa_logs"].insert(0, {
                "id": f"CAPA-{100 + len(self.db['capa_logs']) + 1}",
                "machine_id": mid, "machine_name": mname,
                "severity": "CRITICAL" if mode == "BREAKDOWN" else "HIGH",
                "status": "OPEN", "date": datetime.now().strftime("%d %b"),
                "issue": in_iss.text.strip() or "Fault logged",
                "rca": in_rca.text.strip() or "Under investigation",
                "action": in_act.text.strip() or "Inspection ongoing",
                "parts": in_prt.text.strip(),
                "person": self.db["settings"]["user_name"]
            })
            self.save_data()
            pop.dismiss()
            self.switch_tab(self.current_tab)

        b_ok.bind(on_release=_sv)
        pop.open()

    def open_spare_modal(self):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        in_p = self.make_field(box, "Spare Part Name & Code", "Optical Fiber Sensor SP-101")
        in_q = self.make_field(box, "Quantity Used", "1")
        b_ok = Button(text="Log Spare Usage", size_hint_y=None, height=dp(48), background_normal="", background_color=T.ACCENT_COLOR, color=T.BG_COLOR, bold=True)
        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.9, None), height=dp(240), background="", background_color=T.CARD_COLOR)
        b_ok.bind(on_release=lambda x: pop.dismiss())
        box.add_widget(b_ok)
        pop.open()

    def open_handover_modal(self):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        in_n = self.make_field(box, "Shift Handover Note", "")
        b_ok = Button(text="Save Handover Note", size_hint_y=None, height=dp(48), background_normal="", background_color=T.ACCENT_COLOR, color=T.BG_COLOR, bold=True)
        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.9, None), height=dp(200), background="", background_color=T.CARD_COLOR)

        def _sv(*a):
            if in_n.text.strip():
                self.db["handovers"].insert(0, {"time": datetime.now().strftime("%d %b %H:%M"), "by": self.db["settings"]["user_name"], "note": in_n.text.strip()})
                self.save_data()
            pop.dismiss()

        b_ok.bind(on_release=_sv)
        box.add_widget(b_ok)
        pop.open()

    def open_pm_calendar_modal(self):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        box.add_widget(Label(text="OCTOBER 2026 PM SCHEDULE", font_size=T.FONT_CARD_TITLE, bold=True, color=T.TEXT_PRIMARY, size_hint_y=None, height=dp(26)))
        grid = GridLayout(cols=7, spacing=dp(4))
        for d in range(1, 32):
            due = d in (17, 18, 20)
            b = Button(
                text=str(d),
                font_size=T.FONT_CAPTION,
                bold=due,
                background_normal="",
                background_color=T.ACCENT_TINT if due else T.CARD_ALT_COLOR,
                color=T.ACCENT_COLOR if due else T.TEXT_MUTED
            )
            grid.add_widget(b)
        box.add_widget(grid)
        b_cl = Button(text="Close", size_hint_y=None, height=dp(44), background_normal="", background_color=T.CARD_ALT_COLOR, color=T.TEXT_PRIMARY)
        pop = Popup(title="", separator_height=0, content=box, size_hint=(0.92, None), height=dp(340), background="", background_color=T.CARD_COLOR)
        b_cl.bind(on_release=pop.dismiss)
        box.add_widget(b_cl)
        pop.open()


if __name__ == "__main__":
    MachineTrackerApp().run()
