import json
import os
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix. behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.animation import Animation

# Consistent Status Color System
STATUS_COLORS = {
    "RUNNING": (0.13, 0.77, 0.37, 1),      # Green
    "IDLE": (0.48, 0.53, 0.60, 1),         # Grey
    "BREAKDOWN": (0.94, 0.27, 0.27, 1),    # Red
    "MAINTENANCE": (0.96, 0.62, 0.04, 1),  # Amber
}

PM_PRIORITY = {"OVERDUE": 0, "TODAY": 1, "3 DAYS": 2, "OK": 3}

INITIAL_MACHINES = [
    {"sl": 1, "name": "Brevetti", "id": "K02PR-095", "prod": "Cefixime 200mg Amp", "batch": "B26-1041", "pm_due": "3 DAYS"},
    {"sl": 2, "name": "Korber", "id": "K02PR-089", "prod": "Pantoprazole 40mg IV", "batch": "B26-1042", "pm_due": "OK"},
    {"sl": 3, "name": "Light Inspection 01", "id": "K02PR-137", "prod": "Ondansetron 8mg Inj", "batch": "B26-1039", "pm_due": "OVERDUE"},
    {"sl": 4, "name": "Light Inspection 02", "id": "K02PR-138", "prod": "Ketorolac 30mg Amp", "batch": "B26-1045", "pm_due": "OK"},
    {"sl": 5, "name": "PDLD", "id": "K02PR-134", "prod": "Cefixime 200mg Amp", "batch": "B26-1041", "pm_due": "OK"},
    {"sl": 6, "name": "Ampoule Labeling 01", "id": "K02PR-106", "prod": "Dexamethasone 5mg", "batch": "B26-1048", "pm_due": "OVERDUE"},
    {"sl": 7, "name": "Conveyor Belt 04", "id": "K02PR-133", "prod": "Line 04 Transfer", "batch": "B26-1041", "pm_due": "OK"},
    {"sl": 8, "name": "Blister & Cartooning", "id": "K02PR-111", "prod": "Esomeprazole 20mg", "batch": "B26-1050", "pm_due": "TODAY"},
    {"sl": 9, "name": "Conveyor Belt 01", "id": "K02PR-130", "prod": "Line 01 Transfer", "batch": "B26-1042", "pm_due": "OK"},
    {"sl": 10, "name": "Checkweigher 01", "id": "K02PR-143", "prod": "Pantoprazole 40mg IV", "batch": "B26-1042", "pm_due": "OK"},
    {"sl": 11, "name": "Vail Labeling 02", "id": "K02PR-108", "prod": "Meropenem 1g Vial", "batch": "B26-1052", "pm_due": "OK"},
    {"sl": 12, "name": "Conveyor Belt 03", "id": "K02PR-132", "prod": "Line 03 Transfer", "batch": "B26-1052", "pm_due": "OK"},
    {"sl": 13, "name": "Washing and Drying", "id": "K02PR-135", "prod": "Sterile Vial Prep", "batch": "B26-1055", "pm_due": "OVERDUE"},
    {"sl": 14, "name": "Vail Labeling 01", "id": "K02PR-107", "prod": "Ceftriaxone 1g Vial", "batch": "B26-1054", "pm_due": "OK"},
    {"sl": 15, "name": "Conveyor Belt 02", "id": "K02PR-131", "prod": "Line 02 Transfer", "batch": "B26-1054", "pm_due": "OK"},
    {"sl": 16, "name": "IFC Printer- (Morico)", "id": "K02PR-136", "prod": "Ceftriaxone Outer", "batch": "B26-1054", "pm_due": "3 DAYS"},
    {"sl": 17, "name": "NKP 01", "id": "K02PR-128", "prod": "Ceftriaxone 1g Vial", "batch": "B26-1054", "pm_due": "TODAY"},
    {"sl": 18, "name": "NKP 02", "id": "K02PR-129", "prod": "Meropenem 1g Vial", "batch": "B26-1052", "pm_due": "OK"},
]


class CardBox(BoxLayout):
    def __init__(self, bg_color=(0.09, 0.13, 0.20, 1), radius_val=12, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius_val = radius_val
        with self.canvas.before:
            self.color_inst = Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(self.radius_val)])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def set_bg(self, new_color):
        self.bg_color = new_color
        self.color_inst.rgba = new_color

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class ClickableCard(ButtonBehavior, CardBox):
    def __init__(self, on_long_press_cb=None, on_swipe_right_cb=None, **kwargs):
        super().__init__(**kwargs)
        self.on_long_press_cb = on_long_press_cb
        self.on_swipe_right_cb = on_swipe_right_cb
        self._lp_ev = None
        self._touch_start_x = 0
        self.long_pressed = False

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.long_pressed = False
            self._touch_start_x = touch.x
            if self.on_long_press_cb:
                self._lp_ev = Clock.schedule_once(self._trigger_lp, 0.65)
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._lp_ev and abs(touch.x - self._touch_start_x) > dp(20):
            self._lp_ev.cancel()
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._lp_ev:
            self._lp_ev.cancel()
        if self.collide_point(*touch.pos) and self.on_swipe_right_cb:
            if (touch.x - self._touch_start_x) > dp(75):
                self.long_pressed = True
                self.on_swipe_right_cb()
                return True
        return super().on_touch_up(touch)

    def _trigger_lp(self, dt):
        self.long_pressed = True
        if self.on_long_press_cb:
            self.on_long_press_cb()


class UptimeBarChart(BoxLayout):
    def __init__(self, days_data, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, height=dp(115), padding=dp(8), spacing=dp(4), **kwargs)
        self.days_data = days_data
        bars_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=0.78)
        labels_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=0.22)

        for day_lbl, val in self.days_data:
            col_box = BoxLayout(orientation="vertical")
            pct = max(0.1, min(1.0, val / 100.0))
            spacer = BoxLayout(size_hint_y=1.0 - pct)
            bar_color = (0.13, 0.77, 0.37, 1) if val >= 85 else (0.96, 0.62, 0.04, 1)
            bar = CardBox(bg_color=bar_color, radius_val=4, size_hint_y=pct)
            bar.add_widget(Label(text=f"{val}%", font_size="9sp", bold=True, color=(0, 0, 0, 1)))
            col_box.add_widget(spacer)
            col_box.add_widget(bar)
            bars_row.add_widget(col_box)
            labels_row.add_widget(Label(text=day_lbl, font_size="10sp", color=(0.75, 0.82, 0.9, 1)))

        self.add_widget(bars_row)
        self.add_widget(labels_row)


class MachineTrackerApp(App):
    def build(self):
        self.title = "S Matrix Smart Eng-Ops"
        self.data_file = os.path.join(self.user_data_dir, "smatrix_eng_v3.json")
        self.backup_file = os.path.join(self.user_data_dir, "smatrix_backup.json")
        self.load_data()

        self.selected_machine_id = self.db["machine_order"][0]
        self.machine_filter = "ALL"
        self.machine_search = ""
        self.detail_tab = "OVERVIEW"
        self.capa_filter = "ALL"
        self.capa_search = ""
        self.expanded_staff_cards = set()

        self.root_layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        with self.root_layout.canvas.before:
            self.bg_color_inst = Color(*self.get_theme_bg())
            self.bg_rect = Rectangle(pos=self.root_layout.pos, size=self.root_layout.size)
        self.root_layout.bind(pos=self._update_bg, size=self._update_bg)

        self.content_scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        self.content_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10), padding=[0, dp(2), 0, dp(28)])
        self.content_box.bind(minimum_height=self.content_box.setter("height"))
        self.content_scroll.add_widget(self.content_box)
        self.root_layout.add_widget(self.content_scroll)

        # Bottom Navigation with Active Highlight & Clean Icons
        self.nav_bar = GridLayout(cols=4, size_hint_y=None, height=dp(52), spacing=dp(6))
        self.btn_home = Button(text="[H] Home", bold=True, font_size="12sp")
        self.btn_machines = Button(text="[M] Machines", font_size="12sp")
        self.btn_capa = Button(text="[!] CAPA & Spares", font_size="12sp")
        self.btn_settings = Button(text="[*] Settings", font_size="12sp")

        self.btn_home.bind(on_release=lambda x: self.switch_tab("HOME"))
        self.btn_machines.bind(on_release=lambda x: self.switch_tab("MACHINES"))
        self.btn_capa.bind(on_release=lambda x: self.switch_tab("CAPA"))
        self.btn_settings.bind(on_release=lambda x: self.switch_tab("SETTINGS"))

        self.nav_bar.add_widget(self.btn_home)
        self.nav_bar.add_widget(self.btn_machines)
        self.nav_bar.add_widget(self.btn_capa)
        self.nav_bar.add_widget(self.btn_settings)
        self.root_layout.add_widget(self.nav_bar)

        self.switch_tab("HOME")
        return self.root_layout

    def get_theme_bg(self):
        return (0.04, 0.06, 0.10, 1) if self.db["settings"].get("theme", "DARK") == "DARK" else (0.92, 0.94, 0.97, 1)

    def get_card_bg(self, variant="default"):
        is_dark = self.db["settings"].get("theme", "DARK") == "DARK"
        if not is_dark:
            return (0.14, 0.19, 0.27, 1) if variant == "header" else (0.18, 0.24, 0.33, 1)
        if variant == "header":
            return (0.06, 0.19, 0.30, 1)
        return (0.09, 0.13, 0.20, 1)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.root_layout.pos
        self.bg_rect.size = self.root_layout.size

    def tr(self, en_txt, bn_txt):
        return bn_txt if self.db["settings"].get("lang", "EN") == "BN" else en_txt

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
                "user_name": "Engr. Ahmeed Sunny",
                "designation": "Senior Maintenance & Automation Engineer",
                "shift": "Shift A (06:00 - 14:00)",
                "plant_name": "S Matrix Sterile & Packaging Division",
                "lang": "EN",
                "theme": "DARK",
                "notify_1d": True,
                "notify_sameday": True,
                "notify_shift": True,
                "operators": ["Md. Tanvir (Op-A)", "Sohag Mia (Op-B)", "Faruk Hossain (Sr. Op)", "Rashedul Islam (Op-C)"],
                "officers": ["Officer Kamrul Hasan", "Officer Tareq Aziz", "Engr. Mahmudul"]
            },
            "handover_notes": [
                {"shift": "Shift A", "time": "17 Oct 14:00", "author": "Engr. Ahmeed Sunny", "note": "Check Ampoule Labeling 01 sensor alignment after batch B26-1048 completion."}
            ],
            "oee_7days": [["Oct 11", 86], ["Oct 12", 89], ["Oct 13", 82], ["Oct 14", 91], ["Oct 15", 88], ["Oct 16", 93], ["Oct 17", 89]],
            "spares_stock": [
                {"name": "Optical Fiber Sensor Head", "code": "SP-101", "stock": 2, "min_stock": 3, "used_count": 5},
                {"name": "Silicone Vacuum Cup 12mm", "code": "SP-104", "stock": 14, "min_stock": 5, "used_count": 3},
                {"name": "HEPA Filter G4-09", "code": "SP-202", "stock": 1, "min_stock": 2, "used_count": 2},
                {"name": "Teflon Sealing Belt", "code": "SP-309", "stock": 8, "min_stock": 4, "used_count": 6}
            ],
            "machine_order": [],
            "machines": {},
            "capa_logs": [
                {
                    "id": "CAPA-101",
                    "machine_id": "K02PR-106",
                    "machine_name": "Ampoule Labeling 01",
                    "date": "2026-10-17",
                    "due_date": "2026-10-19",
                    "severity": "CRITICAL",
                    "status": "OPEN",
                    "batch": "B26-1048",
                    "issue": "Label gap optical sensor intermittent false trigger at >320 RPM",
                    "root_cause": "Adhesive glue residue buildup on optical fiber lens",
                    "corrective": "Cleaned lens with IPA & recalibrated threshold 62% -> 75%",
                    "preventive": "Add 4-hourly lens wipe to operator CLIT checklist",
                    "parts": "Optical Fiber Sensor Head",
                    "person": "Engr. Ahmeed Sunny"
                },
                {
                    "id": "CAPA-102",
                    "machine_id": "K02PR-135",
                    "machine_name": "Washing and Drying",
                    "date": "2026-10-16",
                    "due_date": "2026-10-18",
                    "severity": "HIGH",
                    "status": "IN PROGRESS",
                    "batch": "B26-1055",
                    "issue": "Tunnel drying zone temperature fluctuation (+/- 6C)",
                    "root_cause": "Blower HEPA filter partial choking & SSR relay aging",
                    "corrective": "Replaced HEPA Filter G4-09 & tuned PID parameters",
                    "preventive": "Install differential pressure gauge across blower filter",
                    "parts": "HEPA Filter G4-09",
                    "person": "Engr. Mahmudul"
                },
                {
                    "id": "CAPA-103",
                    "machine_id": "K02PR-111",
                    "machine_name": "Blister & Cartooning",
                    "date": "2026-10-14",
                    "due_date": "2026-10-15",
                    "severity": "MEDIUM",
                    "status": "CLOSED",
                    "batch": "B26-1050",
                    "issue": "Carton leaflet folding misalignment on track 2",
                    "root_cause": "Worn out silicone vacuum cup losing suction pressure",
                    "corrective": "Replaced Silicone Vacuum Cup 12mm & tested 500 cycles",
                    "preventive": "Weeklyshore hardness check of suction cups",
                    "parts": "Silicone Vacuum Cup 12mm",
                    "person": "Officer Kamrul Hasan"
                }
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
                "sl": m["sl"],
                "name": m["name"],
                "id": mid,
                "status": st,
                "product": m["prod"],
                "batch": m["batch"],
                "had_issue": "YES" if idx in (5, 12) else "NO",
                "issue_details": "Label sensor false trigger" if idx == 5 else "Smooth operation",
                "new_parts_count": "1" if idx == 5 else "0",
                "parts_names": "Optical Fiber Sensor Head" if idx == 5 else "None",
                "std_batch_time": "6.0 Hours",
                "actual_batch_time": "7.5 Hours" if idx == 5 else "5.8 Hours",
                "delay_reason": "1.5 hrs extra for sensor recalibration" if idx == 5 else "Within standard time",
                "operator_name": self.db["settings"]["operators"][idx % 4],
                "officer_name": self.db["settings"]["officers"][idx % 3],
                "pm_status": m["pm_due"],
                "last_pm_date": "2026-09-18",
                "next_pm_date": "2026-10-18" if m["pm_due"] != "OK" else "2026-11-02",
                "mtbf_hrs": 142 - (idx * 3),
                "mttr_mins": 28 + (idx % 15),
                "total_downtime_mins": 45 if idx == 5 else 15,
                "pm_history": [
                    {"date": "2026-09-18", "by": "Engr. Ahmeed Sunny", "remarks": "Monthly lubrication, sensor calibration & safety check."}
                ],
                "attached_photos": ["IMG_FAULT_20261017.jpg"] if idx == 5 else [],
                "voice_notes": ["Voice Note (0:18): Check roller tension at shift change."] if idx == 5 else [],
                "docs": [
                    f"SOP-{mid}: Standard Operating & Cleaning Procedure v3.2",
                    f"MAN-{mid}: OEM Electrical & PLC Wiring Manual",
                    f"CLIT-{mid}: Daily Lubrication & Inspection Checklist"
                ],
                "batch_history": []
            }

        self.save_data()

    def save_data(self):
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.db, f)
        except Exception:
            pass

    def show_popup(self, title, msg):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        lbl = Label(text=msg, font_size="13sp", halign="center", valign="middle")
        lbl.bind(size=lbl.setter("text_size"))
        box.add_widget(lbl)
        btn = Button(text="OK", size_hint_y=None, height=dp(40), background_color=(0.13, 0.77, 0.37, 1), bold=True)
        pop = Popup(title=title, content=box, size_hint=(0.88, 0.38))
        btn.bind(on_release=pop.dismiss)
        box.add_widget(btn)
        pop.open()

    def add_input(self, parent, label_txt, val="", height_dp=54):
        b = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(height_dp), spacing=dp(2))
        l = Label(text=label_txt, font_size="11sp", color=(0.68, 0.85, 1, 1), size_hint_y=None, height=dp(18), halign="left")
        l.bind(size=l.setter("text_size"))
        ti = TextInput(
            text=str(val),
            multiline=False,
            font_size="13sp",
            size_hint_y=None,
            height=dp(height_dp - 20),
            background_color=(0.14, 0.19, 0.27, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[dp(8), dp(6), dp(8), dp(6)]
        )
        b.add_widget(l)
        b.add_widget(ti)
        parent.add_widget(b)
        return ti

    def switch_tab(self, tab_name):
        self.bg_color_inst.rgba = self.get_theme_bg()
        self.content_box.clear_widgets()
        self.content_box.opacity = 0.25
        Animation(opacity=1.0, duration=0.18).start(self.content_box)

        nav_map = {
            "HOME": self.btn_home,
            "MACHINES": self.btn_machines,
            "MACHINE_DETAIL": self.btn_machines,
            "CAPA": self.btn_capa,
            "SETTINGS": self.btn_settings
        }
        for k, btn in [("HOME", self.btn_home), ("MACHINES", self.btn_machines), ("CAPA", self.btn_capa), ("SETTINGS", self.btn_settings)]:
            is_active = nav_map.get(tab_name) == btn
            btn.background_color = (0.08, 0.68, 0.92, 1) if is_active else (0.15, 0.20, 0.28, 1)
            btn.bold = is_active

        if tab_name == "HOME":
            self.render_home()
        elif tab_name == "MACHINES":
            self.render_machines()
        elif tab_name == "MACHINE_DETAIL":
            self.render_machine_detail(self.selected_machine_id)
        elif tab_name == "CAPA":
            self.render_capa()
        elif tab_name == "SETTINGS":
            self.render_settings()

    # =========================================================================
    # 1. HOME PAGE
    # =========================================================================
    def render_home(self):
        cfg = self.db["settings"]
        m_list = list(self.db["machines"].values())
        total_m = max(1, len(m_list))

        c_run = sum(1 for m in m_list if m["status"] == "RUNNING")
        c_idle = sum(1 for m in m_list if m["status"] == "IDLE")
        c_bd = sum(1 for m in m_list if m["status"] == "BREAKDOWN")
        c_maint = sum(1 for m in m_list if m["status"] == "MAINTENANCE")
        run_pct = int(round((c_run / total_m) * 100))

        overdue_cnt = sum(1 for m in m_list if m.get("pm_status") == "OVERDUE")
        open_issues = sum(1 for c in self.db["capa_logs"] if c.get("status") != "CLOSED")

        # Greeting Banner
        hr = datetime.now().hour
        greet = "Good Morning" if hr < 12 else ("Good Afternoon" if hr < 17 else "Good Evening")
        g_card = CardBox(orientation="vertical", size_hint_y=None, height=dp(82), padding=dp(12), spacing=dp(3), bg_color=self.get_card_bg("header"))
        t1 = Label(text=f"{greet}, {cfg['user_name']}!", font_size="16sp", bold=True, color=(0.3, 0.95, 1, 1), halign="left")
        t1.bind(size=t1.setter("text_size"))
        t2 = Label(text=f"{cfg['designation']}  |  {cfg['shift']}", font_size="11sp", color=(0.85, 0.9, 0.95, 1), halign="left")
        t2.bind(size=t2.setter("text_size"))
        t3 = Label(text=f"{cfg['plant_name']}  •  {datetime.now().strftime('%d %b %Y')}", font_size="11sp", color=(0.5, 0.9, 0.7, 1), halign="left")
        t3.bind(size=t3.setter("text_size"))
        g_card.add_widget(t1)
        g_card.add_widget(t2)
        g_card.add_widget(t3)
        self.content_box.add_widget(g_card)

        # Today's Focus Single-Line Card
        focus_card = CardBox(orientation="vertical", size_hint_y=None, height=dp(52), padding=dp(10), bg_color=(0.14, 0.16, 0.25, 1))
        ft1 = Label(text=self.tr("TODAY'S FOCUS", "আজকের ফোকাস"), font_size="10sp", bold=True, color=(0.4, 0.85, 1, 1), halign="left")
        ft1.bind(size=ft1.setter("text_size"))
        ft2 = Label(
            text=f"Overdue PM: {overdue_cnt}   |   Open Issues: {open_issues}   |   Running: {run_pct}%",
            font_size="13sp", bold=True, color=(1, 0.9, 0.4, 1), halign="left"
        )
        ft2.bind(size=ft2.setter("text_size"))
        focus_card.add_widget(ft1)
        focus_card.add_widget(ft2)
        self.content_box.add_widget(focus_card)

        # Tap-to-Filter Summary Grid (Consistent Status Colors)
        sec_s = Label(text=self.tr("PLANT STATUS (TAP ANY BOX TO FILTER MACHINES)", "মেশিন সামারি (ট্যাপ করলে ফিল্টার হবে)"), font_size="11sp", bold=True, color=(0.75, 0.85, 0.95, 1), size_hint_y=None, height=dp(20), halign="left")
        sec_s.bind(size=sec_s.setter("text_size"))
        self.content_box.add_widget(sec_s)

        grid = GridLayout(cols=2, size_hint_y=None, height=dp(136), spacing=dp(8))
        grid.add_widget(self.make_summary_tile("RUNNING", c_run, "Tap to view active", (0.07, 0.28, 0.17, 1), STATUS_COLORS["RUNNING"]))
        grid.add_widget(self.make_summary_tile("IDLE", c_idle, "Tap to view standby", (0.15, 0.18, 0.23, 1), STATUS_COLORS["IDLE"]))
        grid.add_widget(self.make_summary_tile("BREAKDOWN", c_bd, "Tap to view faults", (0.32, 0.10, 0.12, 1), STATUS_COLORS["BREAKDOWN"]))
        grid.add_widget(self.make_summary_tile("MAINTENANCE", c_maint, "Tap to view PM lines", (0.30, 0.21, 0.06, 1), STATUS_COLORS["MAINTENANCE"]))
        self.content_box.add_widget(grid)

        # Quick Actions Row
        qa_lbl = Label(text=self.tr("QUICK ENGINEERING ACTIONS", "কুইক অ্যাকশন"), font_size="11sp", bold=True, color=(0.75, 0.85, 0.95, 1), size_hint_y=None, height=dp(20), halign="left")
        qa_lbl.bind(size=qa_lbl.setter("text_size"))
        self.content_box.add_widget(qa_lbl)

        qa_row = GridLayout(cols=3, size_hint_y=None, height=dp(42), spacing=dp(6))
        b_q1 = Button(text="+ Log Breakdown", font_size="11sp", bold=True, background_color=STATUS_COLORS["BREAKDOWN"])
        b_q2 = Button(text="+ Add Issue", font_size="11sp", bold=True, background_color=STATUS_COLORS["MAINTENANCE"])
        b_q3 = Button(text="+ Add Spare", font_size="11sp", bold=True, background_color=(0.12, 0.58, 0.85, 1))
        b_q1.bind(on_release=lambda x: self.open_quick_capa_modal("BREAKDOWN"))
        b_q2.bind(on_release=lambda x: self.open_quick_capa_modal("ISSUE"))
        b_q3.bind(on_release=lambda x: self.open_spare_usage_modal())
        qa_row.add_widget(b_q1)
        qa_row.add_widget(b_q2)
        qa_row.add_widget(b_q3)
        self.content_box.add_widget(qa_row)

        # Extra Utility Row: Shift Handover & PM Calendar
        util_row = GridLayout(cols=2, size_hint_y=None, height=dp(38), spacing=dp(6))
        b_ho = Button(text="Shift Handover Note", font_size="11sp", background_color=(0.22, 0.30, 0.45, 1))
        b_cal = Button(text="PM Calendar Schedule", font_size="11sp", background_color=(0.22, 0.30, 0.45, 1))
        b_ho.bind(on_release=self.open_handover_modal)
        b_cal.bind(on_release=self.open_pm_calendar_modal)
        util_row.add_widget(b_ho)
        util_row.add_widget(b_cal)
        self.content_box.add_widget(util_row)

        # PM Alerts (Sorted: OVERDUE -> TODAY -> 3 DAYS, Clean ASCII header without broken box)
        pm_due_list = [m for m in m_list if m.get("pm_status", "OK") != "OK"]
        pm_due_list.sort(key=lambda x: PM_PRIORITY.get(x.get("pm_status", "OK"), 9))

        pm_hdr = CardBox(orientation="vertical", size_hint_y=None, height=dp(48), padding=dp(10), bg_color=(0.24, 0.13, 0.08, 1))
        ph1 = Label(text=f"[!] PREVENTIVE MAINTENANCE ALERTS ({len(pm_due_list)})", font_size="13sp", bold=True, color=(1, 0.75, 0.25, 1), halign="left")
        ph1.bind(size=ph1.setter("text_size"))
        ph2 = Label(text="Sorted by urgency • Tap 'Mark Done' or Swipe Right on card", font_size="10sp", color=(0.9, 0.82, 0.7, 1), halign="left")
        ph2.bind(size=ph2.setter("text_size"))
        pm_hdr.add_widget(ph1)
        pm_hdr.add_widget(ph2)
        self.content_box.add_widget(pm_hdr)

        if not pm_due_list:
            empty_pm = CardBox(size_hint_y=None, height=dp(48), padding=dp(10), bg_color=(0.08, 0.24, 0.15, 1))
            empty_pm.add_widget(Label(text="[OK] Kono overdue PM nai! All machines are healthy.", font_size="12sp", color=(0.4, 1, 0.65, 1)))
            self.content_box.add_widget(empty_pm)
        else:
            for pm in pm_due_list:
                mid = pm["id"]
                p_st = pm["pm_status"]
                badge_col = STATUS_COLORS["BREAKDOWN"] if p_st == "OVERDUE" else (STATUS_COLORS["MAINTENANCE"] if p_st == "TODAY" else (0.2, 0.75, 0.95, 1))
                row_bg = (0.24, 0.10, 0.12, 1) if p_st == "OVERDUE" else (0.19, 0.16, 0.09, 1)

                pm_card = ClickableCard(
                    on_swipe_right_cb=lambda m_id=mid: self.confirm_pm_done_dialog(m_id),
                    orientation="horizontal", size_hint_y=None, height=dp(64), padding=dp(8), spacing=dp(6), bg_color=row_bg
                )
                left = BoxLayout(orientation="vertical", size_hint_x=0.68)
                lt1 = Label(text=f"[{p_st}]  {pm['name']} ({mid})", font_size="12sp", bold=True, color=badge_col, halign="left")
                lt1.bind(size=lt1.setter("text_size"))
                lt2 = Label(text=f"Last PM: {pm.get('last_pm_date')}  |  Swipe Right or Tap ->", font_size="10sp", color=(0.88, 0.88, 0.92, 1), halign="left")
                lt2.bind(size=lt2.setter("text_size"))
                left.add_widget(lt1)
                left.add_widget(lt2)

                btn_done = Button(text="Mark Done", size_hint_x=0.32, font_size="11sp", bold=True, background_color=STATUS_COLORS["RUNNING"])
                btn_done.bind(on_release=lambda x, m_id=mid: self.confirm_pm_done_dialog(m_id))
                pm_card.add_widget(left)
                pm_card.add_widget(btn_done)
                self.content_box.add_widget(pm_card)

        # 7-Day OEE / Uptime Bar Chart
        chart_card = CardBox(orientation="vertical", size_hint_y=None, height=dp(150), padding=dp(10), bg_color=self.get_card_bg())
        ch_lbl = Label(text="PLANT OEE & UPTIME TREND (LAST 7 DAYS)", font_size="12sp", bold=True, color=(0.35, 0.92, 1, 1), size_hint_y=None, height=dp(22), halign="left")
        ch_lbl.bind(size=ch_lbl.setter("text_size"))
        chart_card.add_widget(ch_lbl)
        chart_card.add_widget(UptimeBarChart(self.db["oee_7days"]))
        self.content_box.add_widget(chart_card)

    def make_summary_tile(self, status_key, count_val, hint_txt, bg_col, accent_col):
        tile = ClickableCard(orientation="vertical", padding=dp(10), bg_color=bg_col)
        tile.bind(on_release=lambda x: self.filter_machines_by_status(status_key))
        t1 = Label(text=f"● {status_key}", font_size="12sp", bold=True, color=accent_col, halign="left")
        t1.bind(size=t1.setter("text_size"))
        t2 = Label(text=str(count_val), font_size="22sp", bold=True, color=(1, 1, 1, 1), halign="left")
        t2.bind(size=t2.setter("text_size"))
        t3 = Label(text=hint_txt, font_size="10sp", color=(0.82, 0.86, 0.92, 1), halign="left")
        t3.bind(size=t3.setter("text_size"))
        tile.add_widget(t1)
        tile.add_widget(t2)
        tile.add_widget(t3)
        return tile

    def filter_machines_by_status(self, st_key):
        self.machine_filter = st_key
        self.switch_tab("MACHINES")

    def confirm_pm_done_dialog(self, m_id):
        m = self.db["machines"][m_id]
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        info = Label(text=f"Confirm PM Completion for {m['name']} ({m_id})", font_size="12sp", bold=True, color=(0.4, 0.95, 1, 1), size_hint_y=None, height=dp(24))
        box.add_widget(info)

        in_date = self.add_input(box, "Completion Date (YYYY-MM-DD):", datetime.now().strftime("%Y-%m-%d"))
        in_by = self.add_input(box, "Performed By:", self.db["settings"]["user_name"])
        in_rem = self.add_input(box, "PM Remarks / Checklist Notes:", "Lubrication, cleaning & calibration OK")

        btn_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        b_can = Button(text="Cancel", background_color=(0.45, 0.2, 0.2, 1))
        b_ok = Button(text="Confirm & Save PM", bold=True, background_color=STATUS_COLORS["RUNNING"])
        btn_row.add_widget(b_can)
        btn_row.add_widget(b_ok)
        box.add_widget(btn_row)

        pop = Popup(title="Confirm Preventive Maintenance", content=box, size_hint=(0.92, 0.62))
        b_can.bind(on_release=pop.dismiss)

        def _confirm(*a):
            m["pm_status"] = "OK"
            m["last_pm_date"] = in_date.text.strip()
            m["next_pm_date"] = "2026-11-17"
            m.setdefault("pm_history", []).insert(0, {
                "date": in_date.text.strip(),
                "by": in_by.text.strip(),
                "remarks": in_rem.text.strip() or "Routine PM Done"
            })
            self.save_data()
            pop.dismiss()
            self.switch_tab("HOME")
            self.show_popup("PM Recorded", f"PM logged for {m['name']}!")

        b_ok.bind(on_release=_confirm)
        pop.open()

    # =========================================================================
    # 2. MACHINE LIST (SEARCH + CHIPS + COMPACT SINGLE-TAP CARDS)
    # =========================================================================
    def render_machines(self):
        # Top Search + Add Machine Row
        top_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        s_in = TextInput(
            text=self.machine_search,
            hint_text="Search machine name, ID, batch...",
            multiline=False,
            font_size="12sp",
            size_hint_x=0.68,
            background_color=(0.14, 0.19, 0.27, 1),
            foreground_color=(1, 1, 1, 1)
        )
        b_search = Button(text="Search", size_hint_x=0.16, font_size="11sp", background_color=(0.12, 0.55, 0.85, 1))
        b_add = Button(text="+ Add", size_hint_x=0.16, font_size="11sp", bold=True, background_color=STATUS_COLORS["RUNNING"])

        def _do_search(*a):
            self.machine_search = s_in.text.strip()
            self.switch_tab("MACHINES")

        b_search.bind(on_release=_do_search)
        b_add.bind(on_release=self.open_add_machine_modal)
        top_row.add_widget(s_in)
        top_row.add_widget(b_search)
        top_row.add_widget(b_add)
        self.content_box.add_widget(top_row)

        # Filter Chips Row (All, Running, Idle, Breakdown, Maintenance, PM Due)
        chip_scroll = ScrollView(do_scroll_x=True, do_scroll_y=False, size_hint_y=None, height=dp(36))
        chip_box = BoxLayout(orientation="horizontal", size_hint_x=None, width=dp(520), spacing=dp(6))
        for f_key, f_lbl in [("ALL", "All"), ("RUNNING", "Running"), ("IDLE", "Idle"), ("BREAKDOWN", "Breakdown"), ("MAINTENANCE", "Maint."), ("PM_DUE", "PM Due")]:
            is_sel = self.machine_filter == f_key
            c_btn = Button(
                text=f_lbl,
                font_size="11sp",
                bold=is_sel,
                background_color=(0.1, 0.7, 0.95, 1) if is_sel else (0.16, 0.22, 0.30, 1)
            )
            c_btn.bind(on_release=lambda x, k=f_key: self.set_machine_filter(k))
            chip_box.add_widget(c_btn)
        chip_scroll.add_widget(chip_box)
        self.content_box.add_widget(chip_scroll)

        hint_lbl = Label(text="Tip: Tap card to open dashboard • Long-press card or tap status chip to change status", font_size="10sp", color=(0.65, 0.78, 0.9, 1), size_hint_y=None, height=dp(16), halign="left")
        hint_lbl.bind(size=hint_lbl.setter("text_size"))
        self.content_box.add_widget(hint_lbl)

        # Filter Machines
        shown = 0
        for mid in self.db["machine_order"]:
            m = self.db["machines"][mid]
            st = m["status"]
            if self.machine_filter == "PM_DUE" and m.get("pm_status", "OK") == "OK":
                continue
            elif self.machine_filter not in ("ALL", "PM_DUE") and st != self.machine_filter:
                continue

            q = self.machine_search.lower()
            if q and not (q in m["name"].lower() or q in mid.lower() or q in m["product"].lower() or q in m["batch"].lower()):
                continue

            shown += 1
            is_staff_open = mid in self.expanded_staff_cards
            card_h = dp(96) if is_staff_open else dp(72)

            card = ClickableCard(
                on_long_press_cb=lambda m_id=mid: self.open_quick_status_modal(m_id),
                orientation="vertical", size_hint_y=None, height=card_h, padding=dp(10), spacing=dp(4),
                bg_color=self.get_card_bg()
            )
            card.bind(on_release=lambda inst, m_id=mid: self.on_machine_card_tap(inst, m_id))

            # Line 1: SL, Name, ID + Quick Status Chip
            r1 = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(6))
            title_l = Label(text=f"#{m['sl']} {m['name']} ({mid})", font_size="14sp", bold=True, color=(1, 1, 1, 1), size_hint_x=0.68, halign="left")
            title_l.bind(size=title_l.setter("text_size"))

            st_chip = Button(
                text=f"● {st}",
                size_hint_x=0.32,
                font_size="11sp",
                bold=True,
                background_color=STATUS_COLORS.get(st, STATUS_COLORS["IDLE"])
            )
            st_chip.bind(on_release=lambda x, m_id=mid: self.open_quick_status_modal(m_id))
            r1.add_widget(title_l)
            r1.add_widget(st_chip)
            card.add_widget(r1)

            # Line 2: Hide Batch when IDLE + Collapsible Staff Button
            r2 = BoxLayout(size_hint_y=None, height=dp(20), spacing=dp(4))
            if st == "IDLE":
                prod_text = "Standby Mode — No Active Batch Running"
                prod_col = (0.68, 0.74, 0.82, 1)
            else:
                prod_text = f"{m['product']}  |  Batch: {m['batch']}"
                prod_col = (0.4, 0.9, 1, 1)

            p_lbl = Label(text=prod_text, font_size="12sp", color=prod_col, size_hint_x=0.76, halign="left")
            p_lbl.bind(size=p_lbl.setter("text_size"))

            staff_btn = Button(
                text="[- Staff]" if is_staff_open else "[+ Staff]",
                size_hint_x=0.24,
                font_size="10sp",
                background_color=(0.18, 0.25, 0.36, 1)
            )
            staff_btn.bind(on_release=lambda x, m_id=mid: self.toggle_staff_line(m_id))
            r2.add_widget(p_lbl)
            r2.add_widget(staff_btn)
            card.add_widget(r2)

            if is_staff_open:
                s_lbl = Label(
                    text=f"Operator: {m['operator_name']}   |   Officer: {m['officer_name']}",
                    font_size="11sp", color=(0.85, 0.82, 1, 1), size_hint_y=None, height=dp(18), halign="left"
                )
                s_lbl.bind(size=s_lbl.setter("text_size"))
                card.add_widget(s_lbl)

            self.content_box.add_widget(card)

        if shown == 0:
            emp = CardBox(orientation="vertical", size_hint_y=None, height=dp(80), padding=dp(14))
            emp.add_widget(Label(text="[i] Kono machine paoa jayni (No matching machines)", font_size="13sp", bold=True, color=(0.7, 0.85, 1, 1)))
            self.content_box.add_widget(emp)

    def set_machine_filter(self, k):
        self.machine_filter = k
        self.switch_tab("MACHINES")

    def toggle_staff_line(self, m_id):
        if m_id in self.expanded_staff_cards:
            self.expanded_staff_cards.remove(m_id)
        else:
            self.expanded_staff_cards.add(m_id)
        self.switch_tab("MACHINES")

    def on_machine_card_tap(self, card_inst, m_id):
        if getattr(card_inst, "long_pressed", False):
            return
        self.selected_machine_id = m_id
        self.detail_tab = "OVERVIEW"
        self.switch_tab("MACHINE_DETAIL")

    def open_quick_status_modal(self, m_id):
        m = self.db["machines"][m_id]
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        box.add_widget(Label(text=f"Select Status for {m['name']} ({m_id})", font_size="13sp", bold=True))

        pop = Popup(title="Quick Status Switch", content=box, size_hint=(0.85, 0.48))
        for st_opt in ["RUNNING", "IDLE", "BREAKDOWN", "MAINTENANCE"]:
            b = Button(text=st_opt, size_hint_y=None, height=dp(40), bold=True, background_color=STATUS_COLORS[st_opt])

            def _set_st(inst, s=st_opt):
                m["status"] = s
                self.save_data()
                pop.dismiss()
                self.switch_tab("MACHINES")

            b.bind(on_release=_set_st)
            box.add_widget(b)
        pop.open()

    # =========================================================================
    # 3. MACHINE DASHBOARD (5-TAB DETAIL VIEW + MTBF/MTTR + PHOTO/VOICE)
    # =========================================================================
    def render_machine_detail(self, m_id):
        m = self.db["machines"][m_id]
        st = m["status"]

        # Header Bar
        hdr = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        b_back = Button(text="<- List", size_hint_x=0.22, font_size="12sp", bold=True, background_color=(0.22, 0.30, 0.42, 1))
        b_back.bind(on_release=lambda x: self.switch_tab("MACHINES"))
        title = Label(text=f"#{m['sl']} {m['name']} ({m_id})", font_size="14sp", bold=True, color=(0.35, 0.95, 1, 1), size_hint_x=0.52, halign="left")
        title.bind(size=title.setter("text_size"))
        st_btn = Button(text=st, size_hint_x=0.26, font_size="11sp", bold=True, background_color=STATUS_COLORS.get(st, STATUS_COLORS["IDLE"]))
        st_btn.bind(on_release=lambda x: self.open_quick_status_modal(m_id))
        hdr.add_widget(b_back)
        hdr.add_widget(title)
        hdr.add_widget(st_btn)
        self.content_box.add_widget(hdr)

        # Reliability KPI Strip (Last PM, Next PM, MTBF, MTTR, Total Downtime)
        kpi_strip = CardBox(orientation="vertical", size_hint_y=None, height=dp(62), padding=dp(8), spacing=dp(2), bg_color=(0.07, 0.17, 0.26, 1))
        k1 = Label(
            text=f"MTBF: {m.get('mtbf_hrs', 130)}h   |   MTTR: {m.get('mttr_mins', 25)}m   |   Downtime: {m.get('total_downtime_mins', 15)}m",
            font_size="12sp", bold=True, color=(0.4, 1, 0.7, 1), halign="left"
        )
        k1.bind(size=k1.setter("text_size"))
        k2 = Label(
            text=f"Last PM: {m.get('last_pm_date')}   |   Next PM: {m.get('next_pm_date')} ({m.get('pm_status')})",
            font_size="11sp", color=(0.85, 0.9, 1, 1), halign="left"
        )
        k2.bind(size=k2.setter("text_size"))
        kpi_strip.add_widget(k1)
        kpi_strip.add_widget(k2)
        self.content_box.add_widget(kpi_strip)

        # 5 Sub-Tabs
        sub_nav = GridLayout(cols=5, size_hint_y=None, height=dp(36), spacing=dp(4))
        for t_id, t_lbl in [("OVERVIEW", "Overview"), ("PM", "PM Hist"), ("ISSUES", "Issues"), ("SPARES", "Spares"), ("DOCS", "Docs")]:
            active = self.detail_tab == t_id
            b = Button(text=t_lbl, font_size="11sp", bold=active, background_color=(0.1, 0.68, 0.9, 1) if active else (0.16, 0.22, 0.30, 1))
            b.bind(on_release=lambda x, tid=t_id: self.switch_detail_subtab(tid))
            sub_nav.add_widget(b)
        self.content_box.add_widget(sub_nav)

        if self.detail_tab == "OVERVIEW":
            self.render_detail_overview(m)
        elif self.detail_tab == "PM":
            self.render_detail_pm(m)
        elif self.detail_tab == "ISSUES":
            self.render_detail_issues(m)
        elif self.detail_tab == "SPARES":
            self.render_detail_spares(m)
        elif self.detail_tab == "DOCS":
            self.render_detail_docs(m)

    def switch_detail_subtab(self, tid):
        self.detail_tab = tid
        self.switch_tab("MACHINE_DETAIL")

    def render_detail_overview(self, m):
        mid = m["id"]
        card = CardBox(orientation="vertical", size_hint_y=None, height=dp(490), padding=dp(12), spacing=dp(6), bg_color=self.get_card_bg())
        card.add_widget(Label(text="BATCH, DURATION, DELAY & STAFF LOGGING", font_size="13sp", bold=True, color=(0.35, 0.92, 1, 1), size_hint_y=None, height=dp(20)))

        self.ov_prod = self.add_input(card, "Running Product Name:", m["product"])
        self.ov_batch = self.add_input(card, "Batch Number:", m["batch"])
        self.ov_std = self.add_input(card, "Standard Batch Time:", m["std_batch_time"])
        self.ov_act = self.add_input(card, "Actual Batch Completion Time:", m["actual_batch_time"])
        self.ov_delay = self.add_input(card, "Delay Reason (সময় বেশি লাগলে কারণ):", m["delay_reason"])
        self.ov_op = self.add_input(card, "Operator Name:", m["operator_name"])
        self.ov_off = self.add_input(card, "Officer Name:", m["officer_name"])

        btn_save = Button(text="SAVE OVERVIEW DATA", size_hint_y=None, height=dp(44), bold=True, background_color=STATUS_COLORS["RUNNING"])
        btn_save.bind(on_release=lambda x: self.save_detail_overview(mid))
        card.add_widget(btn_save)
        self.content_box.add_widget(card)

    def save_detail_overview(self, mid):
        m = self.db["machines"][mid]
        m["product"] = self.ov_prod.text.strip()
        m["batch"] = self.ov_batch.text.strip()
        m["std_batch_time"] = self.ov_std.text.strip()
        m["actual_batch_time"] = self.ov_act.text.strip()
        m["delay_reason"] = self.ov_delay.text.strip()
        m["operator_name"] = self.ov_op.text.strip()
        m["officer_name"] = self.ov_off.text.strip()
        self.save_data()
        self.show_popup("Saved", f"Overview updated for {m['name']}!")

    def render_detail_pm(self, m):
        mid = m["id"]
        b_log = Button(text="+ Log Completed PM Now", size_hint_y=None, height=dp(42), bold=True, background_color=STATUS_COLORS["RUNNING"])
        b_log.bind(on_release=lambda x: self.confirm_pm_done_dialog(mid))
        self.content_box.add_widget(b_log)

        for p in m.get("pm_history", []):
            c = CardBox(orientation="vertical", size_hint_y=None, height=dp(72), padding=dp(10), bg_color=self.get_card_bg())
            c.add_widget(Label(text=f"Date: {p['date']}  |  By: {p['by']}", font_size="12sp", bold=True, color=(0.4, 1, 0.7, 1)))
            c.add_widget(Label(text=f"Remarks: {p['remarks']}", font_size="11sp", color=(0.9, 0.9, 0.95, 1)))
            self.content_box.add_widget(c)

    def render_detail_issues(self, m):
        mid = m["id"]
        media_card = CardBox(orientation="vertical", size_hint_y=None, height=dp(170), padding=dp(10), spacing=dp(6), bg_color=self.get_card_bg())
        media_card.add_widget(Label(text="FAULT PHOTO & VOICE-TO-TEXT REMARKS", font_size="12sp", bold=True, color=(1, 0.75, 0.3, 1), size_hint_y=None, height=dp(20)))

        btn_row = GridLayout(cols=2, size_hint_y=None, height=dp(38), spacing=dp(6))
        b_ph = Button(text="[Cam] Attach Fault Photo", font_size="11sp", background_color=(0.15, 0.55, 0.85, 1))
        b_vc = Button(text="[Mic] Add Voice Note", font_size="11sp", background_color=(0.6, 0.3, 0.8, 1))
        b_ph.bind(on_release=lambda x: self.attach_fault_photo(mid))
        b_vc.bind(on_release=lambda x: self.add_voice_remark(mid))
        btn_row.add_widget(b_ph)
        btn_row.add_widget(b_vc)
        media_card.add_widget(btn_row)

        photos_str = ", ".join(m.get("attached_photos", [])) or "No fault photos attached"
        voices_str = " | ".join(m.get("voice_notes", [])) or "No voice notes recorded"
        media_card.add_widget(Label(text=f"Photos: {photos_str}", font_size="11sp", color=(0.75, 0.9, 1, 1)))
        media_card.add_widget(Label(text=f"Voice: {voices_str}", font_size="11sp", color=(0.9, 0.8, 1, 1)))
        self.content_box.add_widget(media_card)

        b_add_bd = Button(text="+ Log Full Breakdown / Issue for this Machine", size_hint_y=None, height=dp(42), bold=True, background_color=STATUS_COLORS["BREAKDOWN"])
        b_add_bd.bind(on_release=lambda x: self.open_quick_capa_modal("BREAKDOWN", mid))
        self.content_box.add_widget(b_add_bd)

        m_logs = [c for c in self.db["capa_logs"] if c["machine_id"] == mid]
        if not m_logs:
            ok_c = CardBox(size_hint_y=None, height=dp(55), padding=dp(10), bg_color=(0.08, 0.22, 0.15, 1))
            ok_c.add_widget(Label(text="[OK] Kono issue nai! Zero breakdown logged for this machine.", font_size="12sp", color=(0.4, 1, 0.65, 1)))
            self.content_box.add_widget(ok_c)
        else:
            for c in m_logs:
                box = CardBox(orientation="vertical", size_hint_y=None, height=dp(95), padding=dp(10), bg_color=(0.20, 0.11, 0.13, 1))
                box.add_widget(Label(text=f"[{c['severity']}] {c['date']} | Status: {c['status']}", font_size="12sp", bold=True, color=(1, 0.65, 0.3, 1)))
                box.add_widget(Label(text=f"Issue: {c['issue']}", font_size="11sp"))
                box.add_widget(Label(text=f"Action: {c['corrective']} | Parts: {c['parts']}", font_size="11sp", color=(0.5, 0.95, 0.7, 1)))
                self.content_box.add_widget(box)

    def attach_fault_photo(self, mid):
        fname = f"IMG_{mid}_{datetime.now().strftime('%H%M%S')}.jpg"
        self.db["machines"][mid].setdefault("attached_photos", []).append(fname)
        self.save_data()
        self.switch_tab("MACHINE_DETAIL")
        self.show_popup("Photo Attached", f"Fault snapshot {fname} linked to {mid}!")

    def add_voice_remark(self, mid):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        in_v = self.add_input(box, "Speak using keyboard mic or type voice note:", "Motor bearing noise slightly high at 320 RPM")
        btn = Button(text="Save Voice Note", size_hint_y=None, height=dp(40), bold=True, background_color=STATUS_COLORS["RUNNING"])
        pop = Popup(title="Voice-to-Text Remark", content=box, size_hint=(0.9, 0.42))

        def _sv(*a):
            txt = f"Voice ({datetime.now().strftime('%H:%M')}): {in_v.text.strip()}"
            self.db["machines"][mid].setdefault("voice_notes", []).append(txt)
            self.save_data()
            pop.dismiss()
            self.switch_tab("MACHINE_DETAIL")

        btn.bind(on_release=_sv)
        box.add_widget(btn)
        pop.open()

    def render_detail_spares(self, m):
        mid = m["id"]
        c = CardBox(orientation="vertical", size_hint_y=None, height=dp(210), padding=dp(12), spacing=dp(6), bg_color=self.get_card_bg())
        c.add_widget(Label(text="MACHINE SPARE PARTS REPLACEMENT LOG", font_size="12sp", bold=True, color=(0.4, 0.9, 1, 1), size_hint_y=None, height=dp(20)))
        self.sp_cnt = self.add_input(c, "New Parts Installed Count (কয়টা নতুন পার্টস):", m["new_parts_count"])
        self.sp_names = self.add_input(c, "Parts Name & Code:", m["parts_names"])

        b_sv = Button(text="Update Machine Spares", size_hint_y=None, height=dp(40), bold=True, background_color=STATUS_COLORS["RUNNING"])

        def _up(*a):
            m["new_parts_count"] = self.sp_cnt.text.strip()
            m["parts_names"] = self.sp_names.text.strip()
            self.save_data()
            self.show_popup("Updated", "Spare parts record updated!")

        b_sv.bind(on_release=_up)
        c.add_widget(b_sv)
        self.content_box.add_widget(c)

    def render_detail_docs(self, m):
        for doc_title in m.get("docs", []):
            dc = CardBox(orientation="horizontal", size_hint_y=None, height=dp(54), padding=dp(10), bg_color=self.get_card_bg())
            dc.add_widget(Label(text=f"[DOC] {doc_title}", font_size="12sp", halign="left", size_hint_x=0.75))
            b_v = Button(text="Open SOP", size_hint_x=0.25, font_size="11sp", background_color=(0.15, 0.55, 0.85, 1))
            b_v.bind(on_release=lambda x, d=doc_title: self.show_popup("Engineering Document", f"{d}\n\n1. Isolate main power & LOTO.\n2. Clean optical sensors with IPA.\n3. Verify interlock before trial run."))
            dc.add_widget(b_v)
            self.content_box.add_widget(dc)

    # =========================================================================
    # 4. CAPA LOG & SPARE PARTS INTELLIGENCE + EXPORT
    # =========================================================================
    def render_capa(self):
        # Export & Add Row
        exp_row = GridLayout(cols=3, size_hint_y=None, height=dp(40), spacing=dp(6))
        b_new = Button(text="+ New CAPA", font_size="11sp", bold=True, background_color=STATUS_COLORS["BREAKDOWN"])
        b_pdf = Button(text="Export Report", font_size="11sp", bold=True, background_color=(0.15, 0.6, 0.45, 1))
        b_lnk = Button(text="LinkedIn Card", font_size="11sp", bold=True, background_color=(0.08, 0.48, 0.82, 1))
        b_new.bind(on_release=lambda x: self.open_quick_capa_modal("BREAKDOWN"))
        b_pdf.bind(on_release=self.export_capa_report)
        b_lnk.bind(on_release=self.export_linkedin_card)
        exp_row.add_widget(b_new)
        exp_row.add_widget(b_pdf)
        exp_row.add_widget(b_lnk)
        self.content_box.add_widget(exp_row)

        # Filter Chips (ALL, OPEN, IN PROGRESS, CLOSED)
        f_row = GridLayout(cols=4, size_hint_y=None, height=dp(34), spacing=dp(5))
        for st_k in ["ALL", "OPEN", "IN PROGRESS", "CLOSED"]:
            act = self.capa_filter == st_k
            b = Button(text=st_k, font_size="10sp", bold=act, background_color=(0.1, 0.7, 0.95, 1) if act else (0.16, 0.22, 0.30, 1))
            b.bind(on_release=lambda x, k=st_k: self.set_capa_filter(k))
            f_row.add_widget(b)
        self.content_box.add_widget(f_row)

        # CAPA Entries
        logs = [c for c in self.db["capa_logs"] if self.capa_filter == "ALL" or c["status"] == self.capa_filter]
        if not logs:
            emp = CardBox(size_hint_y=None, height=dp(60), padding=dp(12), bg_color=(0.08, 0.22, 0.15, 1))
            emp.add_widget(Label(text="[OK] Kono issue nai in this filter!", font_size="12sp", color=(0.4, 1, 0.65, 1)))
            self.content_box.add_widget(emp)
        else:
            for c in logs:
                sev_col = STATUS_COLORS["BREAKDOWN"] if c["severity"] == "CRITICAL" else STATUS_COLORS["MAINTENANCE"]
                card = CardBox(orientation="vertical", size_hint_y=None, height=dp(158), padding=dp(10), spacing=dp(3), bg_color=(0.15, 0.11, 0.15, 1))
                r1 = BoxLayout(size_hint_y=None, height=dp(22))
                r1.add_widget(Label(text=f"[{c['severity']}] {c['machine_name']} ({c['machine_id']})", font_size="12sp", bold=True, color=sev_col, size_hint_x=0.7))
                b_st = Button(text=c["status"], size_hint_x=0.3, font_size="10sp", bold=True, background_color=STATUS_COLORS["RUNNING"] if c["status"] == "CLOSED" else (0.3, 0.4, 0.6, 1))
                b_st.bind(on_release=lambda x, item=c: self.cycle_capa_status(item))
                r1.add_widget(b_st)
                card.add_widget(r1)

                card.add_widget(Label(text=f"Date: {c['date']} | Due: {c.get('due_date', 'N/A')} | Batch: {c['batch']}", font_size="10sp", color=(0.75, 0.85, 1, 1)))
                card.add_widget(Label(text=f"Issue: {c['issue']}", font_size="11sp", color=(1, 1, 1, 1)))
                card.add_widget(Label(text=f"RCA: {c['root_cause']}", font_size="11sp", color=(1, 0.85, 0.5, 1)))
                card.add_widget(Label(text=f"CA: {c['corrective']} | PA: {c.get('preventive', 'N/A')}", font_size="11sp", color=(0.45, 0.95, 0.7, 1)))
                card.add_widget(Label(text=f"Spare Used: {c['parts']}  |  Resp: {c['person']}", font_size="10sp", color=(0.8, 0.8, 0.9, 1)))
                self.content_box.add_widget(card)

        # Spare Parts Usage & Low Stock Summary (Repeat Failure Tracker)
        sp_hdr = CardBox(orientation="vertical", size_hint_y=None, height=dp(44), padding=dp(8), bg_color=(0.08, 0.20, 0.28, 1))
        sp_hdr.add_widget(Label(text="SPARE PARTS REPEAT FAILURE & STOCK ALERT", font_size="12sp", bold=True, color=(0.35, 0.95, 1, 1)))
        self.content_box.add_widget(sp_hdr)

        for sp in self.db["spares_stock"]:
            low = sp["stock"] < sp["min_stock"]
            sc = CardBox(orientation="horizontal", size_hint_y=None, height=dp(56), padding=dp(8), bg_color=(0.26, 0.11, 0.12, 1) if low else self.get_card_bg())
            info = BoxLayout(orientation="vertical", size_hint_x=0.72)
            info.add_widget(Label(text=f"{sp['name']} ({sp['code']})", font_size="12sp", bold=True, color=(1, 1, 1, 1)))
            st_txt = f"Replaced: {sp['used_count']} times  |  Stock: {sp['stock']} pcs {'[LOW STOCK!]' if low else '[OK]'}"
            info.add_widget(Label(text=st_txt, font_size="11sp", color=(1, 0.5, 0.5, 1) if low else (0.5, 0.95, 0.7, 1)))
            b_add_st = Button(text="+ Restock", size_hint_x=0.28, font_size="11sp", background_color=(0.15, 0.65, 0.45, 1))
            b_add_st.bind(on_release=lambda x, item=sp: self.restock_spare(item))
            sc.add_widget(info)
            sc.add_widget(b_add_st)
            self.content_box.add_widget(sc)

    def set_capa_filter(self, k):
        self.capa_filter = k
        self.switch_tab("CAPA")

    def cycle_capa_status(self, item):
        order = ["OPEN", "IN PROGRESS", "CLOSED"]
        nxt = order[(order.index(item["status"]) + 1) % 3]
        item["status"] = nxt
        self.save_data()
        self.switch_tab("CAPA")

    def restock_spare(self, item):
        item["stock"] += 5
        self.save_data()
        self.switch_tab("CAPA")

    def export_capa_report(self, *args):
        report_path = os.path.join(self.user_data_dir, "S_Matrix_CAPA_Report.txt")
        lines = ["=== S MATRIX SMART ENG-OPS CAPA & SPARES REPORT ===", f"Generated: {datetime.now()}", ""]
        for c in self.db["capa_logs"]:
            lines.append(f"[{c['status']}] {c['machine_name']} ({c['machine_id']}) | Severity: {c['severity']}")
            lines.append(f"Issue: {c['issue']} | RCA: {c['root_cause']}")
            lines.append(f"Corrective: {c['corrective']} | Preventive: {c.get('preventive', '')}")
            lines.append("-" * 50)
        try:
            with open(report_path, "w") as f:
                f.write("\n".join(lines))
        except Exception:
            pass
        self.show_popup("Report Exported", f"PDF/Text Report saved to:\n{report_path}")

    def export_linkedin_card(self, *args):
        m_list = list(self.db["machines"].values())
        run_c = sum(1 for m in m_list if m["status"] == "RUNNING")
        txt = (
            "=== S MATRIX ENGINEERING EXCELLENCE ===\n"
            f"Lead: {self.db['settings']['user_name']}\n"
            f"Plant Availability: {int((run_c/len(m_list))*100)}% ({run_c}/{len(m_list)} Lines Running)\n"
            f"7-Day Avg OEE: 88.4% | Active CAPA Tracking\n"
            "Powered by S Matrix Smart Eng-Ops Hub"
        )
        self.show_popup("S Matrix LinkedIn Card Ready", txt)

    # =========================================================================
    # 5. SETTINGS (LANGUAGE, THEME, BACKUP/RESTORE, DOUBLE CONFIRM RESET)
    # =========================================================================
    def render_settings(self):
        cfg = self.db["settings"]

        # Profile & Preferences
        card = CardBox(orientation="vertical", size_hint_y=None, height=dp(390), padding=dp(12), spacing=dp(6), bg_color=self.get_card_bg())
        card.add_widget(Label(text="[ENGINEER PROFILE & APP PREFERENCES]", font_size="13sp", bold=True, color=(0.35, 0.95, 1, 1), size_hint_y=None, height=dp(22)))

        self.st_name = self.add_input(card, "Engineer Name:", cfg["user_name"])
        self.st_desig = self.add_input(card, "Designation:", cfg["designation"])
        self.st_shift = self.add_input(card, "Active Shift:", cfg["shift"])
        self.st_plant = self.add_input(card, "Plant / Branding Name:", cfg["plant_name"])

        toggles = GridLayout(cols=2, size_hint_y=None, height=dp(40), spacing=dp(6))
        b_lang = Button(text=f"Language: {cfg.get('lang', 'EN')}", font_size="11sp", bold=True, background_color=(0.2, 0.45, 0.75, 1))
        b_thm = Button(text=f"Theme: {cfg.get('theme', 'DARK')}", font_size="11sp", bold=True, background_color=(0.35, 0.3, 0.65, 1))
        b_lang.bind(on_release=self.toggle_language)
        b_thm.bind(on_release=self.toggle_theme)
        toggles.add_widget(b_lang)
        toggles.add_widget(b_thm)
        card.add_widget(toggles)

        b_sv = Button(text="SAVE PROFILE & SHIFT", size_hint_y=None, height=dp(42), bold=True, background_color=STATUS_COLORS["RUNNING"])
        b_sv.bind(on_release=self.save_settings_form)
        card.add_widget(b_sv)
        self.content_box.add_widget(card)

        # Backup, Restore & Safe Factory Reset
        bk_card = CardBox(orientation="vertical", size_hint_y=None, height=dp(155), padding=dp(12), spacing=dp(6), bg_color=(0.16, 0.12, 0.16, 1))
        bk_card.add_widget(Label(text="BACKUP, RESTORE & FACTORY RESET", font_size="12sp", bold=True, color=(1, 0.75, 0.3, 1), size_hint_y=None, height=dp(20)))

        br_row = GridLayout(cols=2, size_hint_y=None, height=dp(40), spacing=dp(6))
        b_bk = Button(text="Create Local Backup", font_size="11sp", bold=True, background_color=(0.12, 0.6, 0.45, 1))
        b_rs = Button(text="Restore from Backup", font_size="11sp", bold=True, background_color=(0.15, 0.5, 0.8, 1))
        b_bk.bind(on_release=self.create_backup)
        b_rs.bind(on_release=self.restore_backup)
        br_row.add_widget(b_bk)
        br_row.add_widget(b_rs)
        bk_card.add_widget(br_row)

        b_rst = Button(text="Reset to Factory Default (Safe Confirm)", size_hint_y=None, height=dp(40), bold=True, background_color=STATUS_COLORS["BREAKDOWN"])
        b_rst.bind(on_release=self.confirm_factory_reset_step1)
        bk_card.add_widget(b_rst)
        self.content_box.add_widget(bk_card)

    def toggle_language(self, *args):
        curr = self.db["settings"].get("lang", "EN")
        self.db["settings"]["lang"] = "BN" if curr == "EN" else "EN"
        self.save_data()
        self.switch_tab("SETTINGS")

    def toggle_theme(self, *args):
        curr = self.db["settings"].get("theme", "DARK")
        self.db["settings"]["theme"] = "LIGHT" if curr == "DARK" else "DARK"
        self.save_data()
        self.switch_tab("SETTINGS")

    def save_settings_form(self, *args):
        cfg = self.db["settings"]
        cfg["user_name"] = self.st_name.text.strip()
        cfg["designation"] = self.st_desig.text.strip()
        cfg["shift"] = self.st_shift.text.strip()
        cfg["plant_name"] = self.st_plant.text.strip()
        self.save_data()
        self.show_popup("Saved", "Profile & Plant settings updated!")

    def create_backup(self, *args):
        try:
            with open(self.backup_file, "w") as f:
                json.dump(self.db, f)
            self.show_popup("Backup Created", f"All machine & CAPA data backed up to:\n{self.backup_file}")
        except Exception as e:
            self.show_popup("Error", str(e))

    def restore_backup(self, *args):
        if not os.path.exists(self.backup_file):
            self.show_popup("No Backup Found", "Please create a backup first before restoring.")
            return
        try:
            with open(self.backup_file, "r") as f:
                self.db = json.load(f)
            self.save_data()
            self.switch_tab("HOME")
            self.show_popup("Restored", "All data restored from backup successfully!")
        except Exception as e:
            self.show_popup("Error", str(e))

    def confirm_factory_reset_step1(self, *args):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        box.add_widget(Label(text="WARNING: Factory reset will erase all custom logs.\nWe strongly recommend creating a Backup first!", font_size="12sp", halign="center"))
        b_bk = Button(text="1. Backup Data First (Recommended)", size_hint_y=None, height=dp(38), background_color=STATUS_COLORS["RUNNING"])
        b_nxt = Button(text="2. Proceed to Final Reset Confirmation ->", size_hint_y=None, height=dp(38), background_color=STATUS_COLORS["BREAKDOWN"])
        b_can = Button(text="Cancel", size_hint_y=None, height=dp(36))

        pop = Popup(title="Step 1/2: Backup Suggestion", content=box, size_hint=(0.9, 0.5))
        b_can.bind(on_release=pop.dismiss)
        b_bk.bind(on_release=lambda x: (self.create_backup(), pop.dismiss()))
        b_nxt.bind(on_release=lambda x: (pop.dismiss(), self.confirm_factory_reset_step2()))
        box.add_widget(b_bk)
        box.add_widget(b_nxt)
        box.add_widget(b_can)
        pop.open()

    def confirm_factory_reset_step2(self):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        box.add_widget(Label(text="Type 'RESET' below to permanently restore factory defaults:", font_size="12sp"))
        ti = TextInput(multiline=False, font_size="14sp", size_hint_y=None, height=dp(38))
        box.add_widget(ti)
        b_confirm = Button(text="CONFIRM FACTORY RESET", size_hint_y=None, height=dp(40), bold=True, background_color=STATUS_COLORS["BREAKDOWN"])
        pop = Popup(title="Step 2/2: Double Confirmation", content=box, size_hint=(0.88, 0.42))

        def _do_rst(*a):
            if ti.text.strip().upper() == "RESET":
                if os.path.exists(self.data_file):
                    os.remove(self.data_file)
                self.load_data()
                pop.dismiss()
                self.switch_tab("HOME")
                self.show_popup("Reset Complete", "Factory defaults restored.")

        b_confirm.bind(on_release=_do_rst)
        box.add_widget(b_confirm)
        pop.open()

    # =========================================================================
    # MODALS FOR QUICK ACTIONS, ADD MACHINE, HANDOVER & PM CALENDAR
    # =========================================================================
    def open_quick_capa_modal(self, mode="BREAKDOWN", preset_mid=None):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        mid = preset_mid or self.selected_machine_id
        m_opts = [f"{k} - {self.db['machines'][k]['name']}" for k in self.db["machine_order"]]
        sp_m = Spinner(text=f"{mid} - {self.db['machines'][mid]['name']}", values=m_opts, size_hint_y=None, height=dp(36))
        box.add_widget(sp_m)

        sp_sev = Spinner(text="CRITICAL" if mode == "BREAKDOWN" else "HIGH", values=["CRITICAL", "HIGH", "MEDIUM"], size_hint_y=None, height=dp(34))
        box.add_widget(sp_sev)

        in_iss = self.add_input(box, "Issue / Breakdown Description:", "", 48)
        in_rca = self.add_input(box, "Root Cause (RCA):", "", 48)
        in_ca = self.add_input(box, "Corrective Action:", "", 48)
        in_pa = self.add_input(box, "Preventive Action:", "", 48)
        in_part = self.add_input(box, "Spare Part Used:", "None", 48)
        in_due = self.add_input(box, "Target Due Date:", "2026-10-20", 48)

        b_sv = Button(text="SAVE CAPA RECORD", size_hint_y=None, height=dp(42), bold=True, background_color=STATUS_COLORS["RUNNING"])
        pop = Popup(title=f"Log {mode} & CAPA", content=box, size_hint=(0.94, 0.88))

        def _save(*a):
            sel_id = sp_m.text.split(" - ")[0]
            sel_name = sp_m.text.split(" - ")[1]
            if mode == "BREAKDOWN":
                self.db["machines"][sel_id]["status"] = "BREAKDOWN"
            self.db["capa_logs"].insert(0, {
                "id": f"CAPA-{100 + len(self.db['capa_logs']) + 1}",
                "machine_id": sel_id,
                "machine_name": sel_name,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "due_date": in_due.text.strip(),
                "severity": sp_sev.text,
                "status": "OPEN",
                "batch": self.db["machines"][sel_id]["batch"],
                "issue": in_iss.text.strip() or "Fault reported",
                "root_cause": in_rca.text.strip() or "Under analysis",
                "corrective": in_ca.text.strip() or "Inspection ongoing",
                "preventive": in_pa.text.strip() or "Monitor every shift",
                "parts": in_part.text.strip(),
                "person": self.db["settings"]["user_name"]
            })
            self.save_data()
            pop.dismiss()
            self.switch_tab("CAPA")

        b_sv.bind(on_release=_save)
        box.add_widget(b_sv)
        pop.open()

    def open_spare_usage_modal(self):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        sp_names = [s["name"] for s in self.db["spares_stock"]]
        sp_sel = Spinner(text=sp_names[0], values=sp_names, size_hint_y=None, height=dp(40))
        box.add_widget(Label(text="Select Spare Part Used on Floor:", font_size="12sp", size_hint_y=None, height=dp(22)))
        box.add_widget(sp_sel)

        b_use = Button(text="Record 1 pc Used (Deduct Stock)", size_hint_y=None, height=dp(42), bold=True, background_color=STATUS_COLORS["MAINTENANCE"])
        pop = Popup(title="Quick Spare Part Usage", content=box, size_hint=(0.88, 0.42))

        def _use(*a):
            for s in self.db["spares_stock"]:
                if s["name"] == sp_sel.text:
                    s["stock"] = max(0, s["stock"] - 1)
                    s["used_count"] += 1
            self.save_data()
            pop.dismiss()
            self.switch_tab("CAPA")

        b_use.bind(on_release=_use)
        box.add_widget(b_use)
        pop.open()

    def open_handover_modal(self, *args):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        in_note = self.add_input(box, "Add Shift Handover Instruction for Next Shift:", "")
        b_add = Button(text="Post Handover Note", size_hint_y=None, height=dp(38), bold=True, background_color=STATUS_COLORS["RUNNING"])

        hist = ScrollView(size_hint_y=1)
        h_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        h_box.bind(minimum_height=h_box.setter("height"))
        for n in self.db.get("handover_notes", []):
            c = CardBox(orientation="vertical", size_hint_y=None, height=dp(58), padding=dp(6))
            c.add_widget(Label(text=f"{n['shift']} ({n['time']}) - {n['author']}", font_size="11sp", bold=True, color=(0.4, 0.9, 1, 1)))
            c.add_widget(Label(text=n["note"], font_size="11sp"))
            h_box.add_widget(c)
        hist.add_widget(h_box)

        pop = Popup(title="Daily Shift Handover Logbook", content=box, size_hint=(0.92, 0.72))

        def _post(*a):
            if in_note.text.strip():
                self.db.setdefault("handover_notes", []).insert(0, {
                    "shift": self.db["settings"]["shift"],
                    "time": datetime.now().strftime("%d %b %H:%M"),
                    "author": self.db["settings"]["user_name"],
                    "note": in_note.text.strip()
                })
                self.save_data()
                pop.dismiss()
                self.open_handover_modal()

        b_add.bind(on_release=_post)
        box.add_widget(b_add)
        box.add_widget(hist)
        pop.open()

    def open_pm_calendar_modal(self, *args):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        box.add_widget(Label(text="OCTOBER 2026 PM SCHEDULE CALENDAR", font_size="13sp", bold=True, color=(0.4, 0.95, 1, 1), size_hint_y=None, height=dp(24)))
        cal = GridLayout(cols=7, spacing=dp(4))
        for d in range(1, 32):
            has_pm = d in (3, 8, 13, 16, 17, 18, 24, 29)
            bg = STATUS_COLORS["MAINTENANCE"] if d in (17, 18) else ((0.15, 0.55, 0.35, 1) if has_pm else (0.15, 0.2, 0.28, 1))
            btn = Button(text=f"Oct {d}\n{'[PM]' if has_pm else ''}", font_size="10sp", bold=has_pm, background_color=bg)
            cal.add_widget(btn)
        box.add_widget(cal)
        b_cl = Button(text="Close Calendar", size_hint_y=None, height=dp(38))
        pop = Popup(title="PM Calendar View", content=box, size_hint=(0.94, 0.72))
        b_cl.bind(on_release=pop.dismiss)
        box.add_widget(b_cl)
        pop.open()

    def open_add_machine_modal(self, *args):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        in_name = self.add_input(box, "Machine Name:", "")
        in_id = self.add_input(box, "Machine ID:", f"K02PR-{150 + len(self.db['machine_order'])}")
        in_prod = self.add_input(box, "Running Product:", "Standard Batch")
        in_batch = self.add_input(box, "Batch Number:", "B26-1100")

        b_sv = Button(text="Add Machine", size_hint_y=None, height=dp(42), bold=True, background_color=STATUS_COLORS["RUNNING"])
        pop = Popup(title="Add New Plant Machine", content=box, size_hint=(0.9, 0.65))

        def _add(*a):
            nm = in_name.text.strip()
            mid = in_id.text.strip().upper()
            if not nm or not mid or mid in self.db["machines"]:
                return
            sl = len(self.db["machine_order"]) + 1
            self.db["machine_order"].append(mid)
            self.db["machines"][mid] = {
                "sl": sl, "name": nm, "id": mid, "status": "RUNNING",
                "product": in_prod.text.strip(), "batch": in_batch.text.strip(),
                "had_issue": "NO", "issue_details": "Smooth operation",
                "new_parts_count": "0", "parts_names": "None",
                "std_batch_time": "6.0 Hours", "actual_batch_time": "6.0 Hours",
                "delay_reason": "No delay", "operator_name": "Md. Tanvir (Op-A)",
                "officer_name": "Officer Kamrul Hasan", "pm_status": "OK",
                "last_pm_date": "2026-10-17", "next_pm_date": "2026-11-17",
                "mtbf_hrs": 150, "mttr_mins": 20, "total_downtime_mins": 0,
                "pm_history": [], "attached_photos": [], "voice_notes": [],
                "docs": [f"SOP-{mid}: Operating Procedure"], "batch_history": []
            }
            self.save_data()
            pop.dismiss()
            self.switch_tab("MACHINES")

        b_sv.bind(on_release=_add)
        box.add_widget(b_sv)
        pop.open()


if __name__ == "__main__":
    MachineTrackerApp().run()
