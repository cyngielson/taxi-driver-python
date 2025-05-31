from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

class TaxiDriverApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(
            text='Taxi Driver App\nSimple Version',
            size_hint=(1, 0.3),
            font_size='24sp'
        )
        
        start_btn = Button(
            text='Start Work',
            size_hint=(1, 0.2),
            font_size='18sp'
        )
        start_btn.bind(on_press=self.start_work)
        
        stop_btn = Button(
            text='Stop Work', 
            size_hint=(1, 0.2),
            font_size='18sp'
        )
        stop_btn.bind(on_press=self.stop_work)
        
        status_label = Label(
            text='Status: Ready',
            size_hint=(1, 0.3),
            font_size='16sp'
        )
        
        layout.add_widget(title)
        layout.add_widget(start_btn)
        layout.add_widget(stop_btn)
        layout.add_widget(status_label)
        
        self.status_label = status_label
        return layout
    
    def start_work(self, instance):
        print("Starting taxi driver work...")
        self.status_label.text = "Status: Working"
        
    def stop_work(self, instance):
        print("Stopping taxi driver work...")
        self.status_label.text = "Status: Stopped"

if __name__ == '__main__':
    TaxiDriverApp().run()
