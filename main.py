import json
import os
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

INITIAL_MACHINES = [
    {"sl": 1, "name": "Brevetti", "id": "K02PR-095", "prod": "Cefixime 200mg Amp", "batch": "B26-1041", "pm_due": "Due in 2 Days"},
    {"sl": 2, "name": "Körber", "id": "K02PR-089", "prod": "Pantoprazole 40mg IV", "batch": "B26-1042", "pm_due": "OK"},
    {"sl": 3, "name": "Light Inspection 01", "id": "K02PR-137", "prod": "Ondansetron 8mg Inj", "batch": "B26-1039", "pm_due": "OVERDUE"},
    {"sl": 4, "name": "Light Inspection 02", "id": "K02PR-138", "prod": "Ketorolac 30mg Amp", "batch": "B26-1045", "pm_due": "OK"},
    {"sl": 5, "name": "PDLD", "id": "K02PR-134", "prod": "Cefixime 200mg Amp", "batch": "B26-1041", "pm_due": "OK"},
    {"sl": 6, "name": "Ampoule Labeling 01", "id": "K02PR-106", "prod": "Dexamethasone 5mg", "batch": "B26-1048", "pm_due": "OVERDUE"},
    {"sl": 7, "name": "Conveyor Belt 04", "id": "K02PR-133", "prod": "Line 04 Transfer", "batch": "B26-1041", "pm_due": "OK"},
    {"sl": 8, "name": "Blister & Cartooning", "id": "K02PR-111", "prod": "Esomeprazole 20mg", "batch": "B26-1050", "pm_due": "Due Tomorrow"},
    {"sl": 9, "name": "Conveyor Belt 01", "id": "K02PR-130", "prod": "Line 01 Transfer", "batch": "B26-1042", "pm_due": "OK"},
    {"sl": 10, "name": "Checkweigher 01", "id": "K02PR-143", "prod": "Pantoprazole 40mg IV", "batch": "B26-1042", "pm_due": "OK"},
    {"sl": 11, "name": "Vail Labeling 02", "id": "K02PR-108", "prod": "Meropenem 1g Vial", "batch": "B26-1052", "pm_due": "OK"},
    {"sl": 12, "name": "Conveyor Belt 03", "id": "K02PR-132", "prod": "Line 03 Transfer", "batch": "B26-1052", "pm_due": "OK"},
    {"sl": 13, "name": "Washing and Drying", "id": "K02PR-135", "prod": "Sterile Vial Prep", "batch": "B26-1055", "pm_due": "OVERDUE"},
    {"sl": 14, "name": "Vail Labeling 01", "id": "K02PR-107", "prod": "Ceftriaxone 1g Vial", "batch": "B26-1054", "pm_due": "OK"},
    {"sl": 15, "name": "Conveyor Belt 02", "id": "K02PR-131", "prod": "Line 02 Transfer", "batch": "B26-1054", "pm_due": "OK"},
    {"sl": 16, "name": "IFC Printer- (Morico)", "id": "K02PR-136", "prod": "Ceftriaxone Outer", "batch": "B26-1054", "pm_due": "Due in 3 Days"},
    {"sl": 17, "name": "NKP 01", "id": "K02PR-128", "prod": "Ceftriaxone 1g Vial", "batch": "B26-1054", "pm_due": "OK"},
    {"sl": 18, "name": "NKP 02", "id": "K02PR-129", "prod": "Meropenem 1g Vial", "batch": "B26-1052", "pm_due": "OK"},
]


class CardBox(BoxLayout):
    def __init__(self, bg_color=(0.09, 0.13, 0.20, 1), radius_val=12, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius_val = radius_val
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(self.radius_val)])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class MachineTrackerApp(App):
    def build(self):
        self.title = "Smart Eng-Ops Hub"
        self.data_file = os.path.join(self.user_data_dir, "smart_eng_v2.json")
        self.load_data()
        self.selected_machine_id = self.db["machine_order"][0]

        self.root_layout = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        with self.root_layout.canvas.before:
            Color(0.04, 0.06, 0.10, 1)
            self.bg_rect = RoundedRectangle(pos=self.root_layout.pos, size=self.root_layout.size)
        self.root_layout.bind(pos=self._update_bg, size=self._update_bg)

        # Dynamic Scrollable Area
        self.content_scroll = ScrollView(do_scroll_x=False)
        self.content_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10), padding=[0, dp(2), 0, dp(24)])
        self.content_box.bind(minimum_height=self.content_box.setter("height"))
        self.content_scroll.add_widget(self.content_box)
        self.root_layout.add_widget(self.content_scroll)

        # Bottom Navigation Bar (Mobile Optimized)
        nav = GridLayout(cols=4, size_hint_y=None, height=dp(48), spacing=dp(6))
        self.btn_home = Button(text="Home", bold=True, font_size="12sp", background_color=(0.1, 0.65, 0.9, 1))
        self.btn_machines = Button(text="Machines", font_size="12sp", background_color=(0.16, 0.22, 0.32, 1))
        self.btn_bd = Button(text="CAPA Log", font_size="12sp", background_color=(0.16, 0.22, 0.32, 1))
        self.btn_settings = Button(text="Settings", font_size="12sp", background_color=(0.16, 0.22, 0.32, 1))

        self.btn_home.bind(on_release=lambda x: self.switch_tab("HOME"))
        self.btn_machines.bind(on_release=lambda x: self.switch_tab("MACHINES"))
        self.btn_bd.bind(on_release=lambda x: self.switch_tab("CAPA"))
        self.btn_settings.bind(on_release=lambda x: self.switch_tab("SETTINGS"))

        nav.add_widget(self.btn_home)
        nav.add_widget(self.btn_machines)
        nav.add_widget(self.btn_bd)
        nav.add_widget(self.btn_settings)
        self.root_layout.add_widget(nav)

        self.switch_tab("HOME")
        return self.root_layout

    def _update_bg(self, *args):
        self.bg_rect.pos = self.root_layout.pos
        self.bg_rect.size = self.root_layout.size

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
                "plant_name": "Sterile & Packaging Unit - Oct 2026"
            },
            "machine_order": [],
            "machines": {},
            "capa_logs": []
        }

        for idx, m in enumerate(INITIAL_MACHINES):
            mid = m["id"]
            self.db["machine_order"].append(mid)
            status = "RUNNING"
            if idx == 5:
                status = "BREAKDOWN"
            elif idx == 12:
                status = "MAINTENANCE"
            elif idx in (6, 14):
                status = "IDLE"

            self.db["machines"][mid] = {
                "sl": m["sl"],
                "name": m["name"],
                "id": mid,
                "status": status,
                "product": m["prod"],
                "batch": m["batch"],
                "had_issue": "YES" if idx in (5, 12) else "NO",
                "issue_details": "Label sensor false trigger & glue buildup" if idx == 5 else "Smooth operation, no abnormality",
                "new_parts_count": "2" if idx == 5 else "0",
                "parts_names": "Optical Fiber Head x1, Guide Roller x1" if idx == 5 else "None",
                "std_batch_time": "6.0 Hours",
                "actual_batch_time": "7.5 Hours" if idx == 5 else "5.8 Hours",
                "delay_reason": "1.5 hrs extra due to label roll splicing & sensor recalibration" if idx == 5 else "Completed within standard time",
                "operator_name": "Md. Tanvir (Op-A)" if idx % 2 == 0 else "Sohag Mia (Op-B)",
                "officer_name": "Officer Kamrul Hasan" if idx % 2 == 0 else "Officer Rashedul Islam",
                "pm_status": m["pm_due"],
                "last_pm_date": "2026-10-02",
                "batch_history": []
            }

        self.save_data()

    def save_data(self):
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.db, f)
        except Exception:
            pass

    def get_greeting(self):
        hr = datetime.now().hour
        if hr < 12:
            return "Good Morning"
        elif hr < 17:
            return "Good Afternoon"
        return "Good Evening"

    def show_popup(self, title, message):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        lbl = Label(text=message, font_size="13sp", halign="center", valign="middle")
        lbl.bind(size=lbl.setter("text_size"))
        box.add_widget(lbl)
        btn = Button(text="Close", size_hint_y=None, height=dp(40), background_color=(0.1, 0.7, 0.5, 1), bold=True)
        pop = Popup(title=title, content=box, size_hint=(0.86, 0.36))
        btn.bind(on_release=pop.dismiss)
        box.add_widget(btn)
        pop.open()

    def add_labeled_input(self, parent, label_text, default_val="", height_dp=54):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(height_dp), spacing=dp(2))
        lbl = Label(text=label_text, font_size="11sp", color=(0.65, 0.85, 1, 1), size_hint_y=None, height=dp(18), halign="left")
        lbl.bind(size=lbl.setter("text_size"))
        ti = TextInput(
            text=str(default_val),
            multiline=False,
            font_size="13sp",
            size_hint_y=None,
            height=dp(height_dp - 20),
            background_color=(0.13, 0.18, 0.26, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[dp(8), dp(6), dp(8), dp(6)]
        )
        box.add_widget(lbl)
        box.add_widget(ti)
        parent.add_widget(box)
        return ti

    def switch_tab(self, tab_name):
        self.content_box.clear_widgets()
        btn_map = {
            "HOME": self.btn_home,
            "MACHINES": self.btn_machines,
            "CAPA": self.btn_bd,
            "SETTINGS": self.btn_settings
        }
        for k, b in btn_map.items():
            b.background_color = (0.1, 0.65, 0.9, 1) if k == tab_name else (0.16, 0.22, 0.32, 1)

        if tab_name == "HOME":
            self.render_home()
        elif tab_name == "MACHINES":
            self.render_machine_list()
        elif tab_name == "MACHINE_DETAIL":
            self.render_machine_detail(self.selected_machine_id)
        elif tab_name == "CAPA":
            self.render_capa_logs()
        elif tab_name == "SETTINGS":
            self.render_settings()

    # =========================================================================
    # 1. HOME PAGE (GREETING + TODAY'S SUMMARY + PM DUE ALERTS)
    # =========================================================================
    def render_home(self):
        cfg = self.db["settings"]
        today_str = datetime.now().strftime("%d %b %Y (%A)")

        # Greeting Banner
        greet_card = CardBox(orientation="vertical", size_hint_y=None, height=dp(96), padding=dp(12), spacing=dp(4), bg_color=(0.07, 0.22, 0.34, 1))
        lbl_g1 = Label(text=f"{self.get_greeting()}, {cfg['user_name']}!", font_size="16sp", bold=True, color=(0.3, 0.95, 1, 1), halign="left")
        lbl_g1.bind(size=lbl_g1.setter("text_size"))
        lbl_g2 = Label(text=f"{cfg['designation']}  |  {cfg['shift']}", font_size="11sp", color=(0.85, 0.9, 0.95, 1), halign="left")
        lbl_g2.bind(size=lbl_g2.setter("text_size"))
        lbl_g3 = Label(text=f"Plant: {cfg['plant_name']}  •  Date: {today_str}", font_size="11sp", color=(0.5, 0.85, 0.7, 1), halign="left")
        lbl_g3.bind(size=lbl_g3.setter("text_size"))
        greet_card.add_widget(lbl_g1)
        greet_card.add_widget(lbl_g2)
        greet_card.add_widget(lbl_g3)
        self.content_box.add_widget(greet_card)

        # Today's Summary Counts (Running, Idle, Breakdown, Maintenance)
        m_vals = list(self.db["machines"].values())
        c_run = sum(1 for m in m_vals if m["status"] == "RUNNING")
        c_idle = sum(1 for m in m_vals if m["status"] == "IDLE")
        c_bd = sum(1 for m in m_vals if m["status"] == "BREAKDOWN")
        c_maint = sum(1 for m in m_vals if m["status"] == "MAINTENANCE")

        sec_lbl = Label(text=f"TODAY'S PLANT SUMMARY (TOTAL {len(m_vals)} MACHINES)", font_size="12sp", bold=True, color=(0.8, 0.9, 1, 1), size_hint_y=None, height=dp(22), halign="left")
        sec_lbl.bind(size=sec_lbl.setter("text_size"))
        self.content_box.add_widget(sec_lbl)

        grid = GridLayout(cols=2, size_hint_y=None, height=dp(140), spacing=dp(8))
        grid.add_widget(self.make_kpi_card("RUNNING", str(c_run), "Active Production", (0.08, 0.32, 0.22, 1), (0.3, 1, 0.6, 1)))
        grid.add_widget(self.make_kpi_card("IDLE", str(c_idle), "Standby / No Batch", (0.16, 0.20, 0.28, 1), (0.7, 0.85, 1, 1)))
        grid.add_widget(self.make_kpi_card("BREAKDOWN", str(c_bd), "Urgent Attention", (0.38, 0.12, 0.14, 1), (1, 0.45, 0.45, 1)))
        grid.add_widget(self.make_kpi_card("MAINTENANCE", str(c_maint), "Scheduled PM / Calib", (0.32, 0.24, 0.08, 1), (1, 0.85, 0.3, 1)))
        self.content_box.add_widget(grid)

        # Preventive Maintenance (PM) Due Alert Section
        pm_machines = [m for m in m_vals if m.get("pm_status", "OK") != "OK"]
        pm_header = CardBox(orientation="vertical", size_hint_y=None, height=dp(50), padding=dp(10), bg_color=(0.30, 0.15, 0.08, 1))
        pm_title = Label(text=f"⚠️ PREVENTIVE MAINTENANCE DUE ALERTS ({len(pm_machines)})", font_size="13sp", bold=True, color=(1, 0.75, 0.25, 1), halign="left")
        pm_title.bind(size=pm_title.setter("text_size"))
        pm_sub = Label(text="Action required to prevent unscheduled breakdown", font_size="10sp", color=(0.95, 0.85, 0.7, 1), halign="left")
        pm_sub.bind(size=pm_sub.setter("text_size"))
        pm_header.add_widget(pm_title)
        pm_header.add_widget(pm_sub)
        self.content_box.add_widget(pm_header)

        if not pm_machines:
            ok_card = CardBox(size_hint_y=None, height=dp(45), padding=dp(10), bg_color=(0.08, 0.24, 0.16, 1))
            ok_card.add_widget(Label(text="All machines are up-to-date with Preventive Maintenance!", font_size="12sp", color=(0.4, 1, 0.6, 1)))
            self.content_box.add_widget(ok_card)
        else:
            for pm_m in pm_machines:
                mid = pm_m["id"]
                is_overdue = pm_m["pm_status"] == "OVERDUE"
                row = CardBox(orientation="horizontal", size_hint_y=None, height=dp(66), padding=dp(8), spacing=dp(6), bg_color=(0.24, 0.11, 0.12, 1) if is_overdue else (0.20, 0.18, 0.10, 1))
                info = BoxLayout(orientation="vertical", size_hint_x=0.68)
                t1 = Label(text=f"{pm_m['name']} ({mid})", font_size="13sp", bold=True, color=(1, 1, 1, 1), halign="left")
                t1.bind(size=t1.setter("text_size"))
                t2 = Label(text=f"Status: {pm_m['pm_status']} | Last PM: {pm_m.get('last_pm_date', 'N/A')}", font_size="11sp", color=(1, 0.6, 0.4, 1) if is_overdue else (1, 0.85, 0.4, 1), halign="left")
                t2.bind(size=t2.setter("text_size"))
                info.add_widget(t1)
                info.add_widget(t2)

                btn_done = Button(text="Mark PM Done", size_hint_x=0.32, font_size="11sp", bold=True, background_color=(0.15, 0.75, 0.45, 1))
                btn_done.bind(on_release=lambda x, m_id=mid: self.complete_pm(m_id))
                row.add_widget(info)
                row.add_widget(btn_done)
                self.content_box.add_widget(row)

        # Quick Jump Button to Machines Section
        btn_go = Button(text="OPEN ALL MACHINES & BATCH DATA ->", size_hint_y=None, height=dp(46), background_color=(0.1, 0.6, 0.85, 1), bold=True, font_size="13sp")
        btn_go.bind(on_release=lambda x: self.switch_tab("MACHINES"))
        self.content_box.add_widget(btn_go)

    def make_kpi_card(self, title, count_str, subtitle, bg, text_col):
        c = CardBox(orientation="vertical", padding=dp(8), bg_color=bg)
        c.add_widget(Label(text=title, font_size="11sp", bold=True, color=text_col))
        c.add_widget(Label(text=count_str, font_size="22sp", bold=True, color=(1, 1, 1, 1)))
        c.add_widget(Label(text=subtitle, font_size="10sp", color=(0.85, 0.85, 0.85, 1)))
        return c

    def complete_pm(self, m_id):
        self.db["machines"][m_id]["pm_status"] = "OK"
        self.db["machines"][m_id]["last_pm_date"] = datetime.now().strftime("%Y-%m-%d")
        self.save_data()
        self.switch_tab("HOME")
        self.show_popup("PM Completed", f"Preventive Maintenance marked OK for {m_id}!")

    # =========================================================================
    # 2. MACHINES DIRECTORY + ADD NEW MACHINE OPTION
    # =========================================================================
    def render_machine_list(self):
        top_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        lbl = Label(text=f"PLANT MACHINES ({len(self.db['machine_order'])})", font_size="14sp", bold=True, color=(0.3, 0.9, 1, 1), size_hint_x=0.55, halign="left")
        lbl.bind(size=lbl.setter("text_size"))
        btn_add = Button(text="+ Add New Machine", size_hint_x=0.45, font_size="12sp", bold=True, background_color=(0.1, 0.75, 0.45, 1))
        btn_add.bind(on_release=self.open_add_machine_modal)
        top_bar.add_widget(lbl)
        top_bar.add_widget(btn_add)
        self.content_box.add_widget(top_bar)

        for mid in self.db["machine_order"]:
            m = self.db["machines"][mid]
            st = m["status"]
            bg = (0.08, 0.15, 0.22, 1)
            badge_col = (0.3, 1, 0.6, 1)
            if st == "BREAKDOWN":
                bg = (0.28, 0.11, 0.13, 1)
                badge_col = (1, 0.45, 0.45, 1)
            elif st == "MAINTENANCE":
                bg = (0.24, 0.18, 0.08, 1)
                badge_col = (1, 0.85, 0.3, 1)
            elif st == "IDLE":
                bg = (0.13, 0.16, 0.20, 1)
                badge_col = (0.75, 0.8, 0.9, 1)

            card = CardBox(orientation="vertical", size_hint_y=None, height=dp(122), padding=dp(10), spacing=dp(4), bg_color=bg)

            r1 = BoxLayout(size_hint_y=None, height=dp(24))
            t_name = Label(text=f"#{m['sl']} {m['name']} ({mid})", font_size="14sp", bold=True, color=(1, 1, 1, 1), halign="left")
            t_name.bind(size=t_name.setter("text_size"))
            t_stat = Label(text=f"[{st}]", font_size="12sp", bold=True, color=badge_col, size_hint_x=0.35, halign="right")
            t_stat.bind(size=t_stat.setter("text_size"))
            r1.add_widget(t_name)
            r1.add_widget(t_stat)
            card.add_widget(r1)

            r2 = Label(text=f"Product: {m['product']}  |  Batch: {m['batch']}", font_size="12sp", color=(0.45, 0.9, 1, 1), size_hint_y=None, height=dp(20), halign="left")
            r2.bind(size=r2.setter("text_size"))
            card.add_widget(r2)

            r3 = Label(text=f"Operator: {m['operator_name']}  |  Officer: {m['officer_name']}", font_size="11sp", color=(0.85, 0.85, 0.9, 1), size_hint_y=None, height=dp(18), halign="left")
            r3.bind(size=r3.setter("text_size"))
            card.add_widget(r3)

            btn_open = Button(
                text="Open Machine Dashboard & Batch Entry ->",
                size_hint_y=None,
                height=dp(34),
                font_size="12sp",
                bold=True,
                background_color=(0.12, 0.55, 0.82, 1)
            )
            btn_open.bind(on_release=lambda x, m_id=mid: self.open_machine_detail(m_id))
            card.add_widget(btn_open)

            self.content_box.add_widget(card)

    def open_add_machine_modal(self, *args):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        in_name = self.add_labeled_input(box, "Machine Name (যেমন: Blister Line 03):", "")
        in_id = self.add_labeled_input(box, "Machine ID (যেমন: K02PR-150):", f"K02PR-{150 + len(self.db['machine_order'])}")
        in_prod = self.add_labeled_input(box, "Running Product Name:", "Standard Batch")
        in_batch = self.add_labeled_input(box, "Current Batch No:", "B26-1099")

        btn_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        btn_cancel = Button(text="Cancel", background_color=(0.5, 0.2, 0.2, 1))
        btn_save = Button(text="Add Machine", bold=True, background_color=(0.1, 0.75, 0.45, 1))
        btn_row.add_widget(btn_cancel)
        btn_row.add_widget(btn_save)
        box.add_widget(btn_row)

        pop = Popup(title="Add New Machine to Plant", content=box, size_hint=(0.92, 0.68))
        btn_cancel.bind(on_release=pop.dismiss)

        def save_new(*a):
            name = in_name.text.strip()
            mid = in_id.text.strip().upper()
            if not name or not mid:
                return
            if mid in self.db["machines"]:
                self.show_popup("Duplicate ID", "This Machine ID already exists!")
                return
            new_sl = len(self.db["machine_order"]) + 1
            self.db["machine_order"].append(mid)
            self.db["machines"][mid] = {
                "sl": new_sl,
                "name": name,
                "id": mid,
                "status": "RUNNING",
                "product": in_prod.text.strip() or "N/A",
                "batch": in_batch.text.strip() or "N/A",
                "had_issue": "NO",
                "issue_details": "Newly added machine - smooth run",
                "new_parts_count": "0",
                "parts_names": "None",
                "std_batch_time": "6.0 Hours",
                "actual_batch_time": "6.0 Hours",
                "delay_reason": "No delay",
                "operator_name": "Assigned Operator",
                "officer_name": "Assigned Officer",
                "pm_status": "OK",
                "last_pm_date": datetime.now().strftime("%Y-%m-%d"),
                "batch_history": []
            }
            self.save_data()
            pop.dismiss()
            self.switch_tab("MACHINES")
            self.show_popup("Success", f"Machine {name} ({mid}) added!")

        btn_save.bind(on_release=save_new)
        pop.open()

    def open_machine_detail(self, m_id):
        self.selected_machine_id = m_id
        self.switch_tab("MACHINE_DETAIL")

    # =========================================================================
    # 3. INDIVIDUAL MACHINE PROFILE (PRIORITY-ORDERED SECTIONS)
    # =========================================================================
    def render_machine_detail(self, m_id):
        m = self.db["machines"][m_id]

        # Back button & Machine Title
        top = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        btn_back = Button(text="<- Back", size_hint_x=0.26, font_size="12sp", bold=True, background_color=(0.25, 0.32, 0.44, 1))
        btn_back.bind(on_release=lambda x: self.switch_tab("MACHINES"))
        lbl_t = Label(text=f"#{m['sl']} {m['name']} ({m_id})", font_size="15sp", bold=True, color=(0.3, 0.95, 1, 1), size_hint_x=0.74, halign="left")
        lbl_t.bind(size=lbl_t.setter("text_size"))
        top.add_widget(btn_back)
        top.add_widget(lbl_t)
        self.content_box.add_widget(top)

        # ---------------- PRIORITY 1: LIVE STATUS, PRODUCT & BATCH ----------------
        sec1 = CardBox(orientation="vertical", size_hint_y=None, height=dp(215), padding=dp(12), spacing=dp(6), bg_color=(0.08, 0.16, 0.24, 1))
        sec1.add_widget(self.make_sec_header("PRIORITY 1: RUNNING STATUS, PRODUCT & BATCH", (0.3, 0.95, 1, 1)))

        lbl_st = Label(text="Machine Current Status (Running / Idle / Breakdown / Maintenance):", font_size="11sp", color=(0.8, 0.9, 1, 1), size_hint_y=None, height=dp(18), halign="left")
        lbl_st.bind(size=lbl_st.setter("text_size"))
        sec1.add_widget(lbl_st)

        self.det_status = Spinner(
            text=m["status"],
            values=["RUNNING", "IDLE", "BREAKDOWN", "MAINTENANCE"],
            size_hint_y=None,
            height=dp(38),
            bold=True,
            background_color=(0.12, 0.55, 0.75, 1)
        )
        sec1.add_widget(self.det_status)

        self.det_prod = self.add_labeled_input(sec1, "Running Product Name (কোন প্রোডাক্ট চলছে):", m["product"])
        self.det_batch = self.add_labeled_input(sec1, "Batch Number (ব্যাচ নাম্বার):", m["batch"])
        self.content_box.add_widget(sec1)

        # ---------------- PRIORITY 2: BATCH DURATION & DELAY REASON ----------------
        sec2 = CardBox(orientation="vertical", size_hint_y=None, height=dp(210), padding=dp(12), spacing=dp(6), bg_color=(0.12, 0.15, 0.22, 1))
        sec2.add_widget(self.make_sec_header("PRIORITY 2: BATCH COMPLETION TIME & DELAY LOG", (0.4, 1, 0.65, 1)))

        self.det_std_time = self.add_labeled_input(sec2, "Standard Batch Time (নির্ধারিত সময়):", m.get("std_batch_time", "6.0 Hours"))
        self.det_act_time = self.add_labeled_input(sec2, "Actual Time Taken to Finish Batch (ব্যাচ শেষ হতে কত সময় লাগছে):", m.get("actual_batch_time", "6.0 Hours"))
        self.det_delay = self.add_labeled_input(sec2, "Why Extra Time Needed? (সময় বেশি লাগলে কেন বেশি লাগলো তার কারণ):", m.get("delay_reason", "No delay"))
        self.content_box.add_widget(sec2)

        # ---------------- PRIORITY 3: BATCH ISSUES & NEW SPARE PARTS ----------------
        sec3 = CardBox(orientation="vertical", size_hint_y=None, height=dp(270), padding=dp(12), spacing=dp(6), bg_color=(0.18, 0.12, 0.14, 1))
        sec3.add_widget(self.make_sec_header("PRIORITY 3: BATCH TROUBLE / ISSUES & SPARE PARTS", (1, 0.75, 0.3, 1)))

        lbl_iss = Label(text="Did Any Problem Occur in this Batch? (এই ব্যাচে কোনো সমস্যা হয়েছে কিনা):", font_size="11sp", color=(1, 0.85, 0.7, 1), size_hint_y=None, height=dp(18), halign="left")
        lbl_iss.bind(size=lbl_iss.setter("text_size"))
        sec3.add_widget(lbl_iss)

        self.det_had_issue = Spinner(
            text=m.get("had_issue", "NO"),
            values=["NO - Smooth Batch Run", "YES - Problem Occurred"],
            size_hint_y=None,
            height=dp(36),
            background_color=(0.65, 0.35, 0.15, 1)
        )
        sec3.add_widget(self.det_had_issue)

        self.det_issue_desc = self.add_labeled_input(sec3, "What Problems Occurred? (কী কী সমস্যা হয়েছে বিস্তারিত):", m.get("issue_details", "None"))
        self.det_parts_cnt = self.add_labeled_input(sec3, "How Many New Parts Installed? (কয়টা নতুন পার্টস দেওয়া হয়েছে):", m.get("new_parts_count", "0"))
        self.det_parts_list = self.add_labeled_input(sec3, "New Parts Name & Specification (পার্টসগুলোর নাম):", m.get("parts_names", "None"))
        self.content_box.add_widget(sec3)

        # ---------------- PRIORITY 4: OPERATOR, OFFICER & PM STATUS ----------------
        sec4 = CardBox(orientation="vertical", size_hint_y=None, height=dp(215), padding=dp(12), spacing=dp(6), bg_color=(0.10, 0.14, 0.20, 1))
        sec4.add_widget(self.make_sec_header("PRIORITY 4: OPERATOR, OFFICER & PM ALERT", (0.75, 0.65, 1, 1)))

        self.det_op = self.add_labeled_input(sec4, "Batch Machine Operator Name (মেশিন অপারেটর কে ছিল):", m.get("operator_name", ""))
        self.det_off = self.add_labeled_input(sec4, "Production / Engr. Officer Name (অফিসার কে ছিল):", m.get("officer_name", ""))

        lbl_pm = Label(text="Preventive Maintenance (PM) Alert Status:", font_size="11sp", color=(0.8, 0.85, 1, 1), size_hint_y=None, height=dp(18), halign="left")
        lbl_pm.bind(size=lbl_pm.setter("text_size"))
        sec4.add_widget(lbl_pm)

        self.det_pm = Spinner(
            text=m.get("pm_status", "OK"),
            values=["OK", "Due Tomorrow", "Due in 2 Days", "Due in 3 Days", "OVERDUE"],
            size_hint_y=None,
            height=dp(36),
            background_color=(0.25, 0.35, 0.55, 1)
        )
        sec4.add_widget(self.det_pm)
        self.content_box.add_widget(sec4)

        # SAVE BUTTON
        btn_save = Button(
            text=f"SAVE ALL BATCH & MACHINE DATA ({m_id})",
            size_hint_y=None,
            height=dp(50),
            font_size="13sp",
            bold=True,
            background_color=(0.1, 0.8, 0.45, 1)
        )
        btn_save.bind(on_release=lambda x: self.save_machine_profile(m_id))
        self.content_box.add_widget(btn_save)

        # PREVIOUS BATCH LOG HISTORY FOR THIS MACHINE
        hist_list = m.get("batch_history", [])
        h_lbl = Label(text=f"SAVED BATCH LOG HISTORY FOR {m['name']} ({len(hist_list)})", font_size="12sp", bold=True, color=(0.4, 0.9, 1, 1), size_hint_y=None, height=dp(26), halign="left")
        h_lbl.bind(size=h_lbl.setter("text_size"))
        self.content_box.add_widget(h_lbl)

        for item in hist_list:
            hcard = CardBox(orientation="vertical", size_hint_y=None, height=dp(115), padding=dp(8), spacing=dp(2), bg_color=(0.07, 0.11, 0.16, 1))
            l1 = Label(text=f"Batch: {item['batch']} ({item['product']}) | Saved: {item['time']}", font_size="12sp", bold=True, color=(0.3, 0.95, 0.7, 1), halign="left")
            l1.bind(size=l1.setter("text_size"))
            l2 = Label(text=f"Duration: {item['actual_time']} (Std: {item['std_time']}) | Delay: {item['delay']}", font_size="11sp", color=(0.9, 0.9, 0.95, 1), halign="left")
            l2.bind(size=l2.setter("text_size"))
            l3 = Label(text=f"Issues: {item['issue']} | New Parts ({item['parts_cnt']}): {item['parts']}", font_size="11sp", color=(1, 0.8, 0.4, 1), halign="left")
            l3.bind(size=l3.setter("text_size"))
            l4 = Label(text=f"Operator: {item['operator']} | Officer: {item['officer']}", font_size="11sp", color=(0.75, 0.8, 1, 1), halign="left")
            l4.bind(size=l4.setter("text_size"))
            hcard.add_widget(l1)
            hcard.add_widget(l2)
            hcard.add_widget(l3)
            hcard.add_widget(l4)
            self.content_box.add_widget(hcard)

    def make_sec_header(self, title, col):
        lbl = Label(text=title, font_size="12sp", bold=True, color=col, size_hint_y=None, height=dp(20), halign="left")
        lbl.bind(size=lbl.setter("text_size"))
        return lbl

    def save_machine_profile(self, m_id):
        m = self.db["machines"][m_id]
        m["status"] = self.det_status.text
        m["product"] = self.det_prod.text.strip()
        m["batch"] = self.det_batch.text.strip()
        m["std_batch_time"] = self.det_std_time.text.strip()
        m["actual_batch_time"] = self.det_act_time.text.strip()
        m["delay_reason"] = self.det_delay.text.strip()
        m["had_issue"] = "YES" if "YES" in self.det_had_issue.text else "NO"
        m["issue_details"] = self.det_issue_desc.text.strip()
        m["new_parts_count"] = self.det_parts_cnt.text.strip()
        m["parts_names"] = self.det_parts_list.text.strip()
        m["operator_name"] = self.det_op.text.strip()
        m["officer_name"] = self.det_off.text.strip()
        m["pm_status"] = self.det_pm.text

        log_entry = {
            "time": datetime.now().strftime("%d %b %H:%M"),
            "product": m["product"],
            "batch": m["batch"],
            "std_time": m["std_batch_time"],
            "actual_time": m["actual_batch_time"],
            "delay": m["delay_reason"],
            "issue": m["issue_details"],
            "parts_cnt": m["new_parts_count"],
            "parts": m["parts_names"],
            "operator": m["operator_name"],
            "officer": m["officer_name"]
        }
        m.setdefault("batch_history", []).insert(0, log_entry)

        if m["had_issue"] == "YES" or m["status"] == "BREAKDOWN":
            self.db["capa_logs"].insert(0, {
                "machine": f"{m['name']} ({m_id})",
                "batch": m["batch"],
                "time": log_entry["time"],
                "issue": m["issue_details"],
                "delay": m["delay_reason"],
                "parts": f"{m['new_parts_count']} pcs ({m['parts_names']})",
                "staff": f"Op: {m['operator_name']} | Off: {m['officer_name']}"
            })

        self.save_data()
        self.switch_tab("MACHINE_DETAIL")
        self.show_popup("Saved Successfully", f"All batch & engineering records updated for {m['name']}!")

    # =========================================================================
    # 4. CENTRAL BREAKDOWN & BATCH DELAY REGISTER (CAPA LOG)
    # =========================================================================
    def render_capa_logs(self):
        hdr = CardBox(orientation="vertical", size_hint_y=None, height=dp(56), padding=dp(10), bg_color=(0.26, 0.12, 0.14, 1))
        hdr.add_widget(Label(text="PLANT-WIDE BATCH ISSUES, DELAYS & SPARE PARTS LOG", font_size="13sp", bold=True, color=(1, 0.75, 0.3, 1)))
        hdr.add_widget(Label(text="Automatically synced when an issue or breakdown is logged on any machine", font_size="10sp", color=(0.9, 0.8, 0.8, 1)))
        self.content_box.add_widget(hdr)

        if not self.db["capa_logs"]:
            empty = CardBox(size_hint_y=None, height=dp(60), padding=dp(12))
            empty.add_widget(Label(text="No batch breakdowns logged yet. Open any machine to log issues.", font_size="12sp"))
            self.content_box.add_widget(empty)
            return

        for log in self.db["capa_logs"]:
            c = CardBox(orientation="vertical", size_hint_y=None, height=dp(115), padding=dp(10), spacing=dp(3), bg_color=(0.14, 0.11, 0.15, 1))
            l1 = Label(text=f"{log['machine']}  |  Batch: {log['batch']}  ({log['time']})", font_size="12sp", bold=True, color=(1, 0.7, 0.3, 1), halign="left")
            l1.bind(size=l1.setter("text_size"))
            l2 = Label(text=f"Issue: {log['issue']}", font_size="11sp", color=(1, 1, 1, 1), halign="left")
            l2.bind(size=l2.setter("text_size"))
            l3 = Label(text=f"Delay Reason: {log['delay']}  |  Parts: {log['parts']}", font_size="11sp", color=(0.4, 0.95, 0.7, 1), halign="left")
            l3.bind(size=l3.setter("text_size"))
            l4 = Label(text=log["staff"], font_size="10sp", color=(0.75, 0.85, 1, 1), halign="left")
            l4.bind(size=l4.setter("text_size"))
            c.add_widget(l1)
            c.add_widget(l2)
            c.add_widget(l3)
            c.add_widget(l4)
            self.content_box.add_widget(c)

    # =========================================================================
    # 5. SETTINGS MENU
    # =========================================================================
    def render_settings(self):
        cfg = self.db["settings"]
        card = CardBox(orientation="vertical", size_hint_y=None, height=dp(360), padding=dp(12), spacing=dp(8), bg_color=(0.09, 0.14, 0.22, 1))
        card.add_widget(self.make_sec_header("ENGINEER PROFILE & PLANT SETTINGS", (0.3, 0.95, 1, 1)))

        self.set_name = self.add_labeled_input(card, "Engineer Name (Home Screen Greeting):", cfg["user_name"])
        self.set_desig = self.add_labeled_input(card, "Designation / Role:", cfg["designation"])
        self.set_shift = self.add_labeled_input(card, "Current Active Shift:", cfg["shift"])
        self.set_plant = self.add_labeled_input(card, "Plant / Department Name:", cfg["plant_name"])

        btn_save = Button(text="SAVE SETTINGS", size_hint_y=None, height=dp(44), bold=True, background_color=(0.1, 0.75, 0.45, 1))
        btn_save.bind(on_release=self.save_settings)
        card.add_widget(btn_save)
        self.content_box.add_widget(card)

        # Reset / Demo Data Option
        danger = CardBox(orientation="vertical", size_hint_y=None, height=dp(100), padding=dp(12), spacing=dp(6), bg_color=(0.22, 0.10, 0.12, 1))
        danger.add_widget(self.make_sec_header("DATA MANAGEMENT", (1, 0.5, 0.5, 1)))
        btn_reset = Button(text="Reset All Data to Factory Default", size_hint_y=None, height=dp(40), background_color=(0.8, 0.2, 0.2, 1), bold=True)
        btn_reset.bind(on_release=self.reset_all_data)
        danger.add_widget(btn_reset)
        self.content_box.add_widget(danger)

    def save_settings(self, *args):
        self.db["settings"]["user_name"] = self.set_name.text.strip() or "Engineer"
        self.db["settings"]["designation"] = self.set_desig.text.strip()
        self.db["settings"]["shift"] = self.set_shift.text.strip()
        self.db["settings"]["plant_name"] = self.set_plant.text.strip()
        self.save_data()
        self.show_popup("Settings Saved", "Greeting & profile settings updated!")

    def reset_all_data(self, *args):
        if os.path.exists(self.data_file):
            os.remove(self.data_file)
        self.load_data()
        self.switch_tab("HOME")
        self.show_popup("Reset Complete", "All machine data restored to default!")


if __name__ == "__main__":
    MachineTrackerApp().run()
