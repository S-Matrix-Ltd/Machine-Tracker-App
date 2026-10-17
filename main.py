from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class MachineTrackerApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20)
        layout.add_widget(Label(text='SMART ENG-OPS LOGBOOK\nOctober 2026', font_size='20sp', halign='center'))
        return layout

if __name__ == '__main__':
    MachineTrackerApp().run()
