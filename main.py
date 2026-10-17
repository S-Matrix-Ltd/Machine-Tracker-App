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

MACHINES = [
    {"sl": 1, "name": "Brevetti", "id": "K02PR-095", "prod": "Cefixime 200mg Amp", "batch": "B26-1041"},
    {"sl": 2, "name": "Körber", "id": "K02PR-089", "prod": "Pantoprazole 40mg IV", "batch": "B26-1042"},
    {"sl": 3, "name": "Light Inspection 01", "id": "K02PR-137", "prod": "Ondansetron 8mg Inj", "batch": "B26-1039"},
    {"sl": 4, "name": "Light Inspection 02", "id": "K02PR-138", "prod": "Ketorolac 30mg Amp", "batch": "B26-1045"},
    {"sl": 5, "name": "PDLD", "id": "K02PR-134", "prod": "Cefixime 200mg Amp", "batch": "B26-1041"},
    {"sl": 6, "name": "Ampoule Labeling 01", "id": "K02PR-106", "prod": "Dexamethasone 5mg", "batch": "B26-1048"},
    {"sl": 7, "name": "Conveyor Belt 04", "id": "K02PR-133", "prod": "Line 04 Transfer", "batch": "B26-1041"},
    {"sl": 8, "name": "Blister & Cartooning", "id": "K02PR-111", "prod": "Esomeprazole 20mg", "batch": "B26-1050"},
    {"sl": 9, "name": "Conveyor Belt 01", "id": "K02PR-130", "prod": "Line 01 Transfer", "batch": "B26-1042"},
    {"sl": 10, "name": "Checkweigher 01", "id": "K02PR-143", "prod": "Pantoprazole 40mg IV", "batch": "B26-1042"},
    {"sl": 11, "name": "Vail Labeling 02", "id": "K02PR-108", "prod": "Meropenem 1g Vial", "batch": "B26-1052"},
    {"sl": 12, "name": "Conveyor Belt 03", "id": "K02PR-132", "prod": "Line 03 Transfer", "batch": "B26-1052"},
    {"sl": 13, "name": "Washing and Drying", "id": "K02PR-135", "prod": "Sterile Vial Prep", "batch": "B26-1055"},
    {"sl": 14, "name": "Vail Labeling 01", "id": "K02PR-107", "prod": "Ceftriaxone 1g Vial", "batch": "B26-1054"},
    {"sl": 15, "name": "Conveyor Belt 02", "id": "K02PR-131", "prod": "Line 02 Transfer", "batch": "B26-1054"},
    {"sl": 16, "name": "IFC Printer- (Morico)", "id": "K02PR-136", "prod": "Ceftriaxone Outer", "batch": "B26-1054"},
    {"sl": 17, "name": "NKP 01", "id": "K02PR-128", "prod": "Ceftriaxone 1g Vial", "batch": "B26-1054"},
    {"sl": 18, "name": "NKP 02", "id": "K02PR-129", "prod": "Meropenem 1g Vial", "batch": "B26-1052"},
]


class CardBox(BoxLayout):
    def __init__(self, bg_color=(0.09, 0.13, 0.20, 1), **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class MachineTrackerApp(App):
    def build(self):
        self.title = "Smart Eng-Ops Logbook"
        self.data_file = os.path.join(self.user_data_dir, "eng_machine_logs.json")
        self.load_data()
        self.selected_machine_id = MACHINES[0]["id"]

        self.root_layout = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))
        with self.root_layout.canvas.before:
            Color(0.04, 0.06, 0.11, 1)
            self.bg_rect = RoundedRectangle(pos=self.root_layout.pos, size=self.root_layout.size)
        self.root_layout.bind(pos=self._update_bg, size=self._update_bg)

        # Top Header
        header = CardBox(orientation="vertical", size_hint_y=None, height=dp(68), padding=dp(8), bg_color=(0.06, 0.18, 0.28, 1))
        header.add_widget(Label(text="SMART ENG-OPS & BREAKDOWN LOGBOOK", font_size="16sp", bold=True, color=(0.2, 0.9, 1, 1)))
        self.kpi_label = Label(text="", font_size="12sp", color=(0.8, 0.9, 0.8, 1))
        header.add_widget(self.kpi_label)
        self.root_layout.add_widget(header)

        # Navigation Tabs
        nav = GridLayout(cols=4, size_hint_y=None, height=dp(42), spacing=dp(5))
        self.btn_tab_machines = Button(text="1. Machines", background_color=(0.1, 0.7, 0.9, 1), bold=True, font_size="12sp")
        self.btn_tab_entry = Button(text="2. 2Hr Entry", background_color=(0.2, 0.25, 0.35, 1), font_size="12sp")
        self.btn_tab_bd = Button(text="3. Breakdown", background_color=(0.2, 0.25, 0.35, 1), font_size="12sp")
        self.btn_tab_streak = Button(text="4. Streak", background_color=(0.2, 0.25, 0.35, 1), font_size="12sp")

        self.btn_tab_machines.bind(on_release=lambda x: self.switch_tab("MACHINES"))
        self.btn_tab_entry.bind(on_release=lambda x: self.switch_tab("ENTRY"))
        self.btn_tab_bd.bind(on_release=lambda x: self.switch_tab("BREAKDOWN"))
        self.btn_tab_streak.bind(on_release=lambda x: self.switch_tab("STREAK"))

        nav.add_widget(self.btn_tab_machines)
        nav.add_widget(self.btn_tab_entry)
        nav.add_widget(self.btn_tab_bd)
        nav.add_widget(self.btn_tab_streak)
        self.root_layout.add_widget(nav)

        # Dynamic Content Area
        self.content_scroll = ScrollView(do_scroll_x=False)
        self.content_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=[0, dp(4), 0, dp(20)])
        self.content_box.bind(minimum_height=self.content_box.setter("height"))
        self.content_scroll.add_widget(self.content_box)
        self.root_layout.add_widget(self.content_scroll)

        self.update_kpis()
        self.switch_tab("MACHINES")
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

        self.db = {"machines": {}, "breakdowns": []}
        for idx, m in enumerate(MACHINES):
            self.db["machines"][m["id"]] = {
                "name": m["name"],
                "sl": m["sl"],
                "status": "RUNNING" if idx != 5 else "BREAKDOWN",
                "product": m["prod"],
                "batch": m["batch"],
                "output_2hr": 18500 + (idx * 400),
                "reject_2hr": 15 + idx,
                "rpm": 320,
                "temp": 44,
                "operator": "Md. Tanvir (Op-A)",
                "engineer": "Engr. Ahmeed Sunny",
                "issue_note": "Smooth operation" if idx != 5 else "Label gap sensor intermittent trigger",
                "streak": 12 + (idx % 5),
                "hours_logged": 16 + (idx % 6)
            }

        self.db["breakdowns"] = [
            {
                "machine_id": "K02PR-106",
                "machine_name": "Ampoule Labeling 01",
                "date": "2026-10-17",
                "start_time": "09:15",
                "end_time": "09:50",
                "batch": "B26-1048",
                "issue": "Label gap optical sensor false trigger at >320 RPM",
                "root_cause": "Adhesive residue buildup on sensor lens",
                "action": "Cleaned optical sensor with IPA & recalibrated threshold",
                "advice": "Wipe roller & sensor head every 4 hours during batch run",
                "param_change": "Sensor sensitivity 62% -> 75%",
                "parts": "Optical cleaning swab x2",
                "person": "Engr. Ahmeed Sunny"
            }
        ]
        self.save_data()

    def save_data(self):
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.db, f)
        except Exception:
            pass
        if hasattr(self, "kpi_label"):
            self.update_kpis()

    def update_kpis(self):
        m_list = self.db["machines"].values()
        running = sum(1 for m in m_list if m["status"] == "RUNNING")
        total_out = sum(int(m.get("output_2hr", 0)) for m in m_list)
        bds = len(self.db["breakdowns"])
        self.kpi_label.text = f"Running: {running}/18  |  2Hr Output: {total_out:,} pcs  |  CAPA Logs: {bds}"

    def show_msg(self, title, msg):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        box.add_widget(Label(text=msg, font_size="14sp"))
        btn = Button(text="OK", size_hint_y=None, height=dp(40), background_color=(0.1, 0.7, 0.5, 1))
        pop = Popup(title=title, content=box, size_hint=(0.85, 0.35))
        btn.bind(on_release=pop.dismiss)
        box.add_widget(btn)
        pop.open()

    def switch_tab(self, tab_name):
        self.content_box.clear_widgets()
        tabs = {
            "MACHINES": self.btn_tab_machines,
            "ENTRY": self.btn_tab_entry,
            "BREAKDOWN": self.btn_tab_bd,
            "STREAK": self.btn_tab_streak,
        }
        for k, b in tabs.items():
            b.background_color = (0.1, 0.7, 0.9, 1) if k == tab_name else (0.2, 0.25, 0.35, 1)

        if tab_name == "MACHINES":
            self.render_machines_tab()
        elif tab_name == "ENTRY":
            self.render_entry_tab()
        elif tab_name == "BREAKDOWN":
            self.render_breakdown_tab()
        elif tab_name == "STREAK":
            self.render_streak_tab()

    # ---------------- TAB 1: ALL 18 MACHINES OVERVIEW ----------------
    def render_machines_tab(self):
        for m in MACHINES:
            mid = m["id"]
            st = self.db["machines"][mid]
            is_ok = st["status"] == "RUNNING"
            bg = (0.08, 0.14, 0.22, 1) if is_ok else (0.24, 0.12, 0.12, 1)

            card = CardBox(orientation="vertical", size_hint_y=None, height=dp(135), padding=dp(10), spacing=dp(4), bg_color=bg)

            row1 = BoxLayout(size_hint_y=None, height=dp(26))
            row1.add_widget(Label(text=f"#{m['sl']} {m['name']} ({mid})", bold=True, font_size="14sp", color=(1, 1, 1, 1), halign="left", text_size=(dp(230), None)))
            status_color = (0.2, 0.95, 0.5, 1) if is_ok else (1, 0.6, 0.2, 1)
            row1.add_widget(Label(text=f"[{st['status']}]  Streak: {st['streak']}d", bold=True, font_size="12sp", color=status_color))
            card.add_widget(row1)

            card.add_widget(Label(text=f"Product: {st['product']}  |  Batch: {st['batch']}", font_size="12sp", color=(0.4, 0.85, 1, 1), halign="left", size_hint_y=None, height=dp(20)))
            card.add_widget(Label(text=f"Last 2Hr Output: {st['output_2hr']} pcs  |  Reject: {st['reject_2hr']}  |  {st['rpm']} RPM", font_size="12sp", color=(0.8, 0.9, 0.8, 1), size_hint_y=None, height=dp(20)))
            card.add_widget(Label(text=f"Operator: {st['operator']}  |  Note: {st['issue_note']}", font_size="11sp", color=(0.75, 0.75, 0.85, 1), size_hint_y=None, height=dp(20)))

            btn_row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(6))
            b_edit = Button(text="Edit 2Hr Log / Batch", font_size="11sp", background_color=(0.1, 0.6, 0.8, 1))
            b_bd = Button(text="Log Breakdown CAPA", font_size="11sp", background_color=(0.85, 0.45, 0.1, 1))
            b_hr = Button(text=f"+1h Run ({st['hours_logged']}h)", font_size="11sp", background_color=(0.15, 0.7, 0.4, 1))

            b_edit.bind(on_release=lambda x, m_id=mid: self.open_machine_for_entry(m_id, "ENTRY"))
            b_bd.bind(on_release=lambda x, m_id=mid: self.open_machine_for_entry(m_id, "BREAKDOWN"))
            b_hr.bind(on_release=lambda x, m_id=mid: self.quick_add_hour(m_id))

            btn_row.add_widget(b_edit)
            btn_row.add_widget(b_bd)
            btn_row.add_widget(b_hr)
            card.add_widget(btn_row)

            self.content_box.add_widget(card)

    def open_machine_for_entry(self, m_id, tab):
        self.selected_machine_id = m_id
        self.switch_tab(tab)

    def quick_add_hour(self, m_id):
        st = self.db["machines"][m_id]
        st["hours_logged"] = min(24, st.get("hours_logged", 16) + 1)
        st["output_2hr"] = int(st.get("output_2hr", 18000)) + 4500
        self.save_data()
        self.switch_tab("MACHINES")

    # ---------------- TAB 2: 2-HOUR SMART ENGINEERING ENTRY ----------------
    def render_entry_tab(self):
        form = CardBox(orientation="vertical", size_hint_y=None, height=dp(580), padding=dp(12), spacing=dp(8))
        form.add_widget(Label(text="SECTION A & B: 2-HOUR PRODUCTION & TELEMETRY ENTRY", bold=True, font_size="14sp", color=(0.3, 0.9, 1, 1), size_hint_y=None, height=dp(24)))

        m_options = [f"{m['id']} - {m['name']}" for m in MACHINES]
        curr_m = self.db["machines"][self.selected_machine_id]
        default_opt = f"{self.selected_machine_id} - {curr_m['name']}"

        self.sp_machine = Spinner(text=default_opt, values=m_options, size_hint_y=None, height=dp(40), background_color=(0.15, 0.4, 0.6, 1))
        self.sp_machine.bind(text=self.on_spinner_machine_change)
        form.add_widget(self.sp_machine)

        self.sp_status = Spinner(text=curr_m["status"], values=["RUNNING", "BREAKDOWN", "MAINTENANCE", "IDLE"], size_hint_y=None, height=dp(38))
        form.add_widget(self.sp_status)

        self.in_prod = self.add_field(form, "Running Product Name:", curr_m["product"])
        self.in_batch = self.add_field(form, "Batch Number:", curr_m["batch"])
        self.in_out2hr = self.add_field(form, "Last 2 Hours Good Output (pcs):", str(curr_m["output_2hr"]))
        self.in_rej2hr = self.add_field(form, "Last 2 Hours Rejects (pcs):", str(curr_m["reject_2hr"]))
        self.in_rpm = self.add_field(form, "Machine Speed (RPM) / Temp (°C):", f"{curr_m['rpm']} RPM / {curr_m['temp']} C")
        self.in_op = self.add_field(form, "Machine Operator Name:", curr_m["operator"])
        self.in_eng = self.add_field(form, "Shift Engineer Name:", curr_m["engineer"])
        self.in_note = self.add_field(form, "Any Problem / Observation Note:", curr_m["issue_note"])

        btn_save = Button(text="SAVE 2-HOUR ENGINEERING UPDATE", size_hint_y=None, height=dp(46), background_color=(0.1, 0.8, 0.45, 1), bold=True)
        btn_save.bind(on_release=self.save_2hr_entry)
        form.add_widget(btn_save)

        self.content_box.add_widget(form)

    def add_field(self, parent, label_text, val):
        row = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(48))
        row.add_widget(Label(text=label_text, font_size="11sp", color=(0.75, 0.85, 0.95, 1), size_hint_y=None, height=dp(16)))
        ti = TextInput(text=val, multiline=False, font_size="13sp", size_hint_y=None, height=dp(32), background_color=(0.14, 0.18, 0.26, 1), foreground_color=(1, 1, 1, 1))
        row.add_widget(ti)
        parent.add_widget(row)
        return ti

    def on_spinner_machine_change(self, spinner, text):
        m_id = text.split(" - ")[0]
        self.selected_machine_id = m_id
        self.switch_tab("ENTRY")

    def save_2hr_entry(self, *args):
        m_id = self.sp_machine.text.split(" - ")[0]
        st = self.db["machines"][m_id]
        st["status"] = self.sp_status.text
        st["product"] = self.in_prod.text
        st["batch"] = self.in_batch.text
        try:
            st["output_2hr"] = int(self.in_out2hr.text)
        except Exception:
            st["output_2hr"] = 0
        try:
            st["reject_2hr"] = int(self.in_rej2hr.text)
        except Exception:
            st["reject_2hr"] = 0
        st["operator"] = self.in_op.text
        st["engineer"] = self.in_eng.text
        st["issue_note"] = self.in_note.text
        self.save_data()
        self.show_msg("Saved!", f"{st['name']} ({m_id}) 2-Hour Update Saved!")

    # ---------------- TAB 3: BREAKDOWN, RCA & CAPA REGISTER ----------------
    def render_breakdown_tab(self):
        form = CardBox(orientation="vertical", size_hint_y=None, height=dp(690), padding=dp(12), spacing=dp(7), bg_color=(0.16, 0.11, 0.12, 1))
        form.add_widget(Label(text="SECTION C: BREAKDOWN, RCA & CAPA ENTRY", bold=True, font_size="14sp", color=(1, 0.7, 0.2, 1), size_hint_y=None, height=dp(24)))

        m_options = [f"{m['id']} - {m['name']}" for m in MACHINES]
        curr_m = self.db["machines"][self.selected_machine_id]
        self.bd_machine = Spinner(text=f"{self.selected_machine_id} - {curr_m['name']}", values=m_options, size_hint_y=None, height=dp(38), background_color=(0.6, 0.3, 0.1, 1))
        form.add_widget(self.bd_machine)

        today_str = datetime.now().strftime("%Y-%m-%d")
        now_str = datetime.now().strftime("%H:%M")

        self.bd_date = self.add_field(form, "1. Date (তারিখ):", today_str)
        self.bd_start = self.add_field(form, "2. Breakdown Start Time (শুরুর সময়):", now_str)
        self.bd_end = self.add_field(form, "3. Completed Time (শেষ হওয়ার সময়):", "11:30")
        self.bd_batch = self.add_field(form, "4. Batch Number (ব্যাচ নং):", curr_m["batch"])
        self.bd_issue = self.add_field(form, "5. Issue Details (কি সমস্যা হয়েছে):", "")
        self.bd_rca = self.add_field(form, "6. Root Cause - RCA (সমস্যার মূল কারণ):", "")
        self.bd_action = self.add_field(form, "7. Corrective Action (কি সমাধান করা হয়েছে):", "")
        self.bd_advice = self.add_field(form, "8. Advice for Production (প্রোডাকশনের জন্য পরামর্শ):", "")
        self.bd_param = self.add_field(form, "9. Any Change Parameter (প্যারামিটার পরিবর্তন):", "None")
        self.bd_parts = self.add_field(form, "10. Parts or Others Used (স্পেয়ার পার্টস):", "None")
        self.bd_person = self.add_field(form, "11. Responsible Person (দায়িত্বপ্রাপ্ত ইঞ্জিনিয়ার):", curr_m["engineer"])

        btn_bd_save = Button(text="SUBMIT BREAKDOWN & CAPA RECORD", size_hint_y=None, height=dp(44), background_color=(0.95, 0.5, 0.1, 1), bold=True)
        btn_bd_save.bind(on_release=self.save_breakdown_entry)
        form.add_widget(btn_bd_save)
        self.content_box.add_widget(form)

        # Breakdown History List
        self.content_box.add_widget(Label(text="RECENT BREAKDOWN & CAPA LOGS", bold=True, font_size="13sp", color=(1, 0.8, 0.3, 1), size_hint_y=None, height=dp(28)))
        for b in self.db["breakdowns"]:
            bcard = CardBox(orientation="vertical", size_hint_y=None, height=dp(135), padding=dp(8), spacing=dp(2))
            bcard.add_widget(Label(text=f"{b['machine_name']} ({b['machine_id']}) | Date: {b['date']} ({b['start_time']} - {b['end_time']})", bold=True, font_size="12sp", color=(1, 0.75, 0.3, 1)))
            bcard.add_widget(Label(text=f"Batch: {b['batch']} | Issue: {b['issue']}", font_size="11sp", color=(1, 1, 1, 1)))
            bcard.add_widget(Label(text=f"RCA: {b['root_cause']} | Action: {b['action']}", font_size="11sp", color=(0.5, 0.95, 0.7, 1)))
            bcard.add_widget(Label(text=f"Advice: {b['advice']}", font_size="11sp", color=(0.5, 0.85, 1, 1)))
            bcard.add_widget(Label(text=f"Param Change: {b['param_change']} | Parts: {b['parts']} | By: {b['person']}", font_size="10sp", color=(0.8, 0.8, 0.8, 1)))
            self.content_box.add_widget(bcard)

    def save_breakdown_entry(self, *args):
        m_id = self.bd_machine.text.split(" - ")[0]
        m_name = self.bd_machine.text.split(" - ")[1]
        entry = {
            "machine_id": m_id,
            "machine_name": m_name,
            "date": self.bd_date.text,
            "start_time": self.bd_start.text,
            "end_time": self.bd_end.text,
            "batch": self.bd_batch.text,
            "issue": self.bd_issue.text or "Unspecified fault",
            "root_cause": self.bd_rca.text or "Under investigation",
            "action": self.bd_action.text or "Rectified & tested",
            "advice": self.bd_advice.text or "Monitor closely",
            "param_change": self.bd_param.text,
            "parts": self.bd_parts.text,
            "person": self.bd_person.text,
        }
        self.db["breakdowns"].insert(0, entry)
        self.db["machines"][m_id]["issue_note"] = entry["issue"]
        self.save_data()
        self.switch_tab("BREAKDOWN")
        self.show_msg("CAPA Saved", f"Breakdown log added for {m_name}!")

    # ---------------- TAB 4: WEEKLY & MONTHLY STREAK MATRIX ----------------
    def render_streak_tab(self):
        top = CardBox(orientation="vertical", size_hint_y=None, height=dp(55), padding=dp(8))
        top.add_widget(Label(text="OCTOBER 2026 MACHINE STREAK & DAILY HOURS LEADERBOARD", bold=True, font_size="13sp", color=(1, 0.65, 0.2, 1)))
        top.add_widget(Label(text="Tap '+1 Day Streak' to increment active run streak", font_size="11sp", color=(0.75, 0.8, 0.9, 1)))
        self.content_box.add_widget(top)

        for m in MACHINES:
            mid = m["id"]
            st = self.db["machines"][mid]
            row = CardBox(orientation="horizontal", size_hint_y=None, height=dp(54), padding=dp(8), spacing=dp(8))
            row.add_widget(Label(text=f"#{m['sl']} {m['name']}\n({mid})", font_size="12sp", bold=True, size_hint_x=0.42))
            row.add_widget(Label(text=f"Today: {st['hours_logged']}/24h\nStreak: {st['streak']} Days", font_size="12sp", color=(0.3, 0.95, 0.6, 1), size_hint_x=0.33))
            btn = Button(text="+1d Streak", size_hint_x=0.25, font_size="11sp", background_color=(0.9, 0.45, 0.1, 1))
            btn.bind(on_release=lambda x, m_id=mid: self.bump_streak(m_id))
            row.add_widget(btn)
            self.content_box.add_widget(row)

    def bump_streak(self, m_id):
        self.db["machines"][m_id]["streak"] += 1
        self.save_data()
        self.switch_tab("STREAK")


if __name__ == "__main__":
    MachineTrackerApp().run()
