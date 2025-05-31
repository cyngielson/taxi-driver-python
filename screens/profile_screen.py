"""
ProfileScreen - ekran profilu kierowcy
Konwersja z React Native do Python/Kivy z zachowaniem 100% funkcjonalności API
"""

import asyncio
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem, TwoLineListItem, ThreeLineListItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.toast import toast
import json

class ProfileScreen(Screen):
    """Ekran profilu kierowcy z danymi z API"""
    
    def __init__(self, api_service, **kwargs):
        super().__init__(**kwargs)
        self.api_service = api_service
        self.profile_data = {}
        
        # Layout główny
        main_layout = BoxLayout(orientation='vertical')
        
        # Toolbar
        self.toolbar = MDTopAppBar(
            title="Mój profil",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[["refresh", lambda x: self.refresh_profile()]]
        )
        main_layout.add_widget(self.toolbar)
        
        # ScrollView dla zawartości
        scroll = ScrollView()
        
        # Główna zawartość
        self.content_layout = MDBoxLayout(
            orientation='vertical',
            adaptive_height=True,
            spacing="10dp",
            padding="10dp"
        )
        
        # Placeholder - dane będą załadowane asynchronicznie
        self.loading_label = MDLabel(
            text="Ładowanie profilu...",
            halign="center",
            size_hint_y=None,
            height="50dp"
        )
        self.content_layout.add_widget(self.loading_label)
        
        scroll.add_widget(self.content_layout)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
        
        # Załaduj profil po utworzeniu ekranu
        asyncio.create_task(self.load_profile())
    
    async def load_profile(self):
        """Załaduj dane profilu z API"""
        try:
            print("Ładowanie profilu kierowcy...")
            response = await self.api_service.get_driver_profile()
            
            if response.get('success') and response.get('data'):
                self.profile_data = response['data']
                self.build_profile_ui()
            else:
                self.show_error("Nie udało się załadować profilu")
                
        except Exception as error:
            print(f"Błąd podczas ładowania profilu: {error}")
            self.show_error(f"Błąd: {error}")
    
    def build_profile_ui(self):
        """Zbuduj interfejs profilu na podstawie danych z API"""
        # Usuń loading label
        self.content_layout.clear_widgets()
        
        # Dane podstawowe kierowcy
        self.add_basic_info_card()
        
        # Dane pojazdu
        self.add_vehicle_info_card()
        
        # Statystyki
        self.add_stats_card()
        
        # Działania
        self.add_actions_card()
    
    def add_basic_info_card(self):
        """Dodaj kartę z podstawowymi informacjami"""
        card = MDCard(
            size_hint_y=None,
            height="200dp",
            elevation=2,
            padding="15dp"
        )
        
        card_layout = MDBoxLayout(
            orientation='vertical',
            spacing="5dp"
        )
        
        # Nagłówek
        header = MDLabel(
            text="👤 Podstawowe informacje",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="30dp"
        )
        card_layout.add_widget(header)
        
        # Informacje
        info_data = [
            ("Imię i nazwisko", self.profile_data.get('name', 'N/A')),
            ("Telefon", self.profile_data.get('phone', 'N/A')),
            ("Email", self.profile_data.get('email', 'N/A')),
            ("ID kierowcy", str(self.profile_data.get('id', 'N/A'))),
            ("Status", self.get_status_display())
        ]
        
        for label, value in info_data:
            item_layout = MDBoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height="25dp"
            )
            
            label_widget = MDLabel(
                text=f"{label}:",
                size_hint_x=0.4,
                theme_text_color="Secondary"
            )
            value_widget = MDLabel(
                text=str(value),
                size_hint_x=0.6,
                theme_text_color="Primary"
            )
            
            item_layout.add_widget(label_widget)
            item_layout.add_widget(value_widget)
            card_layout.add_widget(item_layout)
        
        card.add_widget(card_layout)
        self.content_layout.add_widget(card)
    
    def add_vehicle_info_card(self):
        """Dodaj kartę z informacjami o pojeździe"""
        card = MDCard(
            size_hint_y=None,
            height="180dp",
            elevation=2,
            padding="15dp"
        )
        
        card_layout = MDBoxLayout(
            orientation='vertical',
            spacing="5dp"
        )
        
        # Nagłówek
        header = MDLabel(
            text="🚗 Informacje o pojeździe",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="30dp"
        )
        card_layout.add_widget(header)
        
        # Informacje o pojeździe
        vehicle_data = [
            ("Model", self.profile_data.get('vehicle_model', 'N/A')),
            ("Numer rejestracyjny", self.profile_data.get('vehicle_plate', 'N/A')),
            ("Typ pojazdu", self.profile_data.get('vehicle_type', 'N/A')),
            ("Numer licencji", self.profile_data.get('license_number', 'N/A')),
            ("Ważność licencji", self.profile_data.get('license_expiry', 'N/A'))
        ]
        
        for label, value in vehicle_data:
            item_layout = MDBoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height="25dp"
            )
            
            label_widget = MDLabel(
                text=f"{label}:",
                size_hint_x=0.4,
                theme_text_color="Secondary"
            )
            value_widget = MDLabel(
                text=str(value),
                size_hint_x=0.6,
                theme_text_color="Primary"
            )
            
            item_layout.add_widget(label_widget)
            item_layout.add_widget(value_widget)
            card_layout.add_widget(item_layout)
        
        card.add_widget(card_layout)
        self.content_layout.add_widget(card)
    
    def add_stats_card(self):
        """Dodaj kartę ze statystykami"""
        card = MDCard(
            size_hint_y=None,
            height="150dp",
            elevation=2,
            padding="15dp"
        )
        
        card_layout = MDBoxLayout(
            orientation='vertical',
            spacing="5dp"
        )
        
        # Nagłówek
        header = MDLabel(
            text="📊 Statystyki",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="30dp"
        )
        card_layout.add_widget(header)
        
        # Grid dla statystyk
        stats_grid = MDGridLayout(
            cols=2,
            spacing="10dp",
            size_hint_y=None,
            height="100dp"
        )
        
        # Statystyki
        stats_data = [
            ("Łączne zlecenia", str(self.profile_data.get('total_orders', 0))),
            ("Średnia ocena", f"{self.profile_data.get('average_rating', 0):.1f} ⭐"),
            ("Lata doświadczenia", str(self.profile_data.get('experience_years', 0))),
            ("Status konta", "Aktywny" if self.profile_data.get('status') == 'online' else "Nieaktywny")
        ]
        
        for label, value in stats_data:
            stat_layout = MDBoxLayout(
                orientation='vertical',
                spacing="2dp"
            )
            
            value_label = MDLabel(
                text=str(value),
                theme_text_color="Primary",
                font_style="H6",
                halign="center",
                size_hint_y=None,
                height="30dp"
            )
            label_label = MDLabel(
                text=label,
                theme_text_color="Secondary",
                font_style="Caption",
                halign="center",
                size_hint_y=None,
                height="20dp"
            )
            
            stat_layout.add_widget(value_label)
            stat_layout.add_widget(label_label)
            stats_grid.add_widget(stat_layout)
        
        card_layout.add_widget(stats_grid)
        card.add_widget(card_layout)
        self.content_layout.add_widget(card)
    
    def add_actions_card(self):
        """Dodaj kartę z akcjami"""
        card = MDCard(
            size_hint_y=None,
            height="120dp",
            elevation=2,
            padding="15dp"
        )
        
        card_layout = MDBoxLayout(
            orientation='vertical',
            spacing="10dp"
        )
        
        # Nagłówek
        header = MDLabel(
            text="⚙️ Działania",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="30dp"
        )
        card_layout.add_widget(header)
        
        # Przyciski akcji
        buttons_layout = MDBoxLayout(
            orientation='horizontal',
            spacing="10dp",
            size_hint_y=None,
            height="50dp"
        )
        
        edit_button = MDRaisedButton(
            text="Edytuj profil",
            size_hint_x=0.5,
            on_release=self.edit_profile
        )
        
        settings_button = MDFlatButton(
            text="Ustawienia",
            size_hint_x=0.5,
            on_release=self.show_settings
        )
        
        buttons_layout.add_widget(edit_button)
        buttons_layout.add_widget(settings_button)
        card_layout.add_widget(buttons_layout)
        
        card.add_widget(card_layout)
        self.content_layout.add_widget(card)
    
    def get_status_display(self):
        """Pobierz wyświetlany status"""
        status = self.profile_data.get('status', 'offline')
        status_map = {
            'online': '🟢 Online',
            'offline': '🔴 Offline',
            'busy': '🟡 Zajęty'
        }
        return status_map.get(status, f'❓ {status}')
    
    def edit_profile(self, *args):
        """Otwórz edycję profilu"""
        dialog = MDDialog(
            title="Edycja profilu",
            text="Funkcja edycji profilu będzie dostępna wkrótce.",
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
    
    def show_settings(self, *args):
        """Pokaż ustawienia"""
        dialog = MDDialog(
            title="Ustawienia",
            text="Panel ustawień będzie dostępny wkrótce.",
            buttons=[
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()
    
    def refresh_profile(self):
        """Odśwież profil"""
        toast("Odświeżanie profilu...")
        asyncio.create_task(self.load_profile())
    
    def show_error(self, message):
        """Pokaż błąd"""
        self.content_layout.clear_widgets()
        
        error_label = MDLabel(
            text=f"❌ {message}",
            halign="center",
            theme_text_color="Error"
        )
        
        retry_button = MDRaisedButton(
            text="Spróbuj ponownie",
            size_hint=(None, None),
            size=("200dp", "40dp"),
            pos_hint={'center_x': 0.5},
            on_release=lambda x: asyncio.create_task(self.load_profile())
        )
        
        self.content_layout.add_widget(error_label)
        self.content_layout.add_widget(retry_button)
    
    def go_back(self):
        """Wróć do poprzedniego ekranu"""
        if self.manager:
            self.manager.current = 'home'
