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
# 1. UNIFIED THEME (NO EXTERNAL FILES NEEDED)
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

STATUS_MAP = {
    "RUNNING": STATUS_RUNNING, "IDLE": STATUS_IDLE,
    "BREAKDOWN": STATUS_BREAKDOWN, "MAINTENANCE": STATUS_MAINTENANCE,
}

STATUS_TINT_MAP = {
    "RUNNING": (0.063, 0.725, 0.506, 0.16),
    "IDLE": (0.392, 0.455, 0.545, 0.16),
    "BREAKDOWN": (0.957, 0.247, 0.369, 0.16),
    "MAINTENANCE": (0.961, 0.620, 0.043, 0.16),
}

FONT_TITLE, FONT_SEC_LABEL, FONT_CARD_TITLE = sp(19), sp(11), sp(14)
FONT_BODY, FONT_CAPTION, FONT_BIG_NUM = sp(12), sp(10), sp(22)

PAD_SCREEN, RADIUS_BOX, RADIUS_INNER = dp(14), dp(16), dp(12)

# ==========================================
# 2. REUSABLE UI WIDGETS
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
    def __init__(self, title_str, on_tap, **kwargs):
        super().__init__(orientation="vertical", size_hint_x=1, padding=[0, dp(4)], spacing=dp(2), **kwargs)
        self.on_tap_cb = on_tap
        self.pill = BoxLayout(size_hint=(None, None), size=(dp(64), dp(28)), pos_hint={"center_x": 0.5})
        with self.pill.canvas.before:
            self.p_col = Color(0, 0, 0, 0)
            self.p_rect = RoundedRectangle(pos=self.pill.pos, size=self.pill.size, radius=[dp(14)])
        self.pill.bind(pos=lambda i, v: setattr(self.p_rect, "pos", v), size=lambda i, v: setattr(self.p_rect, "size", v))

        self.tx = Label(text=title_str, font_size=dp(11), color=TEXT_MUTED, bold=True)
        self.pill.add_widget(self.tx)
        self.add_widget(self.pill)

    def on_release(self):
        Animation(opacity=0.6, duration=0.06).start(self)
        Animation(opacity=1.0, duration=0.15).start(self)
        self.on_tap_cb()

    def set_active(self, active):
        self.p_col.rgba = ACCENT_TINT if active else (0, 0, 0, 0)
        self.tx.color = ACCENT_COLOR if active else TEXT_MUTED


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
        sp_param = Spinner(text="Select Option", values=["No", "Yes"], size_hint_y=None, height=dp(38), background_normal="", background_color=CARD_INNER, color=TEXT_PRIMARY, bold=True)
        param_box.add_widget(sp_param)
        box.add_widget(param_box)

        param_entry_box = BoxLayout(orientation="vertical", size_hint_y=None, height=0, opacity=0.0, spacing=dp(3))
        lbl_pr = make_label("Parameter Details / Remarks:", FONT_CAPTION, ACCENT_COLOR, bold=True, height_dp=0)
        in_param_desc = TextInput(text="", hint_text="Enter parameter details...", multiline=False, font_size=FONT_BODY, size_hint_y=None, height=0, background_normal="", background_color=CARD_INNER, foreground_color=TEXT_PRIMARY, padding=[dp(10), dp(8)])
        param_entry_box.add_widget(lbl_pr)
        param_entry_box.add_widget(in_param_desc)
        box.add_widget(param_entry_box)

        def _toggle_param(sp_inst, val):
            if val == "Yes":
                lbl_pr.height = dp(16)
                in_param_desc.height = dp(38)
                Animation(height=dp(58), opacity=1.0, duration=0.18).start(param_entry_box)
            else:
                lbl_pr.height = 0
                in_param_desc.height = 0
                Animation(height=0, opacity=0.0, duration=0.18).start(param_entry_box)
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
            pr_chg = sp_param.text
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
                "param_desc": in_param_desc.text.strip() if pr_chg == "Yes" else "None",
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
