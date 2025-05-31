"""
OrderStorageScreen - ekran magazynu zleceń
Konwersja z React Native do Python/Kivy z zachowaniem 100% funkcjonalności API
"""

import asyncio
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem, TwoLineListItem, ThreeLineListItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.refreshlayout import MDSwipeToRefresh
from kivymd.toast import toast
from kivy.clock import Clock
import json
from datetime import datetime

class OrderCard(MDCard):
    """Karta pojedynczego zlecenia"""
    
    def __init__(self, order_data, accept_callback, details_callback, **kwargs):
        super().__init__(**kwargs)
        self.order_data = order_data
        self.accept_callback = accept_callback
        self.details_callback = details_callback
        
        self.size_hint_y = None
        self.height = "180dp"
        self.elevation = 2
        self.padding = "10dp"
        self.spacing = "5dp"
        
        # Layout główny karty
        card_layout = MDBoxLayout(
            orientation='vertical',
            spacing="8dp"
        )
        
        # Header z ID i ceną
        header_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height="30dp"
        )
        
        order_id_label = MDLabel(
            text=f"Zlecenie #{order_data.get('id', 'N/A')}",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_x=0.7
        )
        
        price_label = MDLabel(
            text=f"{order_data.get('price', 'N/A')} PLN",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_x=0.3,
            halign="right"
        )
        
        header_layout.add_widget(order_id_label)
        header_layout.add_widget(price_label)
        card_layout.add_widget(header_layout)
        
        # Adresy
        pickup_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height="25dp"
        )
        pickup_icon = MDLabel(
            text="📍",
            size_hint_x=None,
            width="30dp"
        )
        pickup_text = MDLabel(
            text=f"Z: {order_data.get('pickup_address', 'Brak adresu')}",
            theme_text_color="Secondary",
            font_style="Body2"
        )
        pickup_layout.add_widget(pickup_icon)
        pickup_layout.add_widget(pickup_text)
        card_layout.add_widget(pickup_layout)
        
        destination_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height="25dp"
        )
        dest_icon = MDLabel(
            text="🎯",
            size_hint_x=None,
            width="30dp"
        )
        dest_text = MDLabel(
            text=f"Do: {order_data.get('destination_address', 'Brak adresu')}",
            theme_text_color="Secondary",
            font_style="Body2"
        )
        destination_layout.add_widget(dest_icon)
        destination_layout.add_widget(dest_text)
        card_layout.add_widget(destination_layout)
        
        # Informacje o dystansie i czasie
        info_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height="25dp"
        )
        
        distance_text = MDLabel(
            text=f"📏 {order_data.get('distance', 'N/A')} km",
            theme_text_color="Secondary",
            font_style="Caption",
            size_hint_x=0.5
        )
        
        time_text = MDLabel(
            text=f"⏱️ ~{order_data.get('estimated_time', 'N/A')} min",
            theme_text_color="Secondary",
            font_style="Caption",
            size_hint_x=0.5
        )
        
        info_layout.add_widget(distance_text)
        info_layout.add_widget(time_text)
        card_layout.add_widget(info_layout)
        
        # Data utworzenia (jeśli dostępna)
        if order_data.get('created_at'):
            created_text = MDLabel(
                text=f"Utworzono: {self.format_date(order_data['created_at'])}",
                theme_text_color="Hint",
                font_style="Caption",
                size_hint_y=None,
                height="20dp"
            )
            card_layout.add_widget(created_text)
        
        # Przyciski akcji
        buttons_layout = MDBoxLayout(
            orientation='horizontal',
            spacing="10dp",
            size_hint_y=None,
            height="40dp"
        )
        
        details_button = MDFlatButton(
            text="Szczegóły",
            size_hint_x=0.5,
            on_release=lambda x: self.show_details()
        )
        
        accept_button = MDRaisedButton(
            text="Przyjmij",
            size_hint_x=0.5,
            on_release=lambda x: self.accept_order()
        )
        
        buttons_layout.add_widget(details_button)
        buttons_layout.add_widget(accept_button)
        card_layout.add_widget(buttons_layout)
        
        self.add_widget(card_layout)
    
    def format_date(self, date_string):
        """Formatuj datę dla wyświetlenia"""
        try:
            # Obsługa różnych formatów daty
            if 'T' in date_string:
                dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d.%m.%Y %H:%M')
        except:
            return date_string
    
    def show_details(self):
        """Pokaż szczegóły zlecenia"""
        if self.details_callback:
            self.details_callback(self.order_data)
    
    def accept_order(self):
        """Przyjmij zlecenie"""
        if self.accept_callback:
            self.accept_callback(self.order_data)

class OrderStorageScreen(Screen):
    """Ekran magazynu zleceń do podjęcia"""
    
    def __init__(self, api_service, **kwargs):
        super().__init__(**kwargs)
        self.api_service = api_service
        self.orders = []
        self.is_loading = False
        
        # Layout główny
        main_layout = BoxLayout(orientation='vertical')
        
        # Toolbar
        self.toolbar = MDTopAppBar(
            title="Zlecenia do podjęcia",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[["refresh", lambda x: self.refresh_orders()]]
        )
        main_layout.add_widget(self.toolbar)
        
        # SwipeToRefresh wrapper
        self.refresh_layout = MDSwipeToRefresh(
            on_refresh=self.on_refresh
        )
        
        # ScrollView dla listy zleceń
        scroll = ScrollView()
        
        # Layout dla zleceń
        self.orders_layout = MDBoxLayout(
            orientation='vertical',
            adaptive_height=True,
            spacing="10dp",
            padding="10dp"
        )
        
        # Placeholder
        self.empty_label = MDLabel(
            text="Ładowanie zleceń...",
            halign="center",
            size_hint_y=None,
            height="50dp"
        )
        self.orders_layout.add_widget(self.empty_label)
        
        scroll.add_widget(self.orders_layout)
        self.refresh_layout.add_widget(scroll)
        main_layout.add_widget(self.refresh_layout)
        
        self.add_widget(main_layout)
        
        # Załaduj zlecenia po utworzeniu ekranu
        Clock.schedule_once(lambda dt: asyncio.create_task(self.load_orders()), 0.1)
        
        # Automatyczne odświeżanie co 30 sekund
        self.refresh_event = Clock.schedule_interval(
            lambda dt: asyncio.create_task(self.load_orders(silent=True)), 
            30
        )
    
    def on_refresh(self, *args):
        """Obsługa swipe to refresh"""
        asyncio.create_task(self.refresh_complete())
    
    async def refresh_complete(self):
        """Zakończ odświeżanie"""
        await self.load_orders()
        self.refresh_layout.refresh_done()
    
    async def load_orders(self, silent=False):
        """Załaduj zlecenia z magazynu"""
        try:
            if not silent:
                self.is_loading = True
                self.update_empty_state("Ładowanie zleceń...")
            
            print("Ładowanie zleceń z magazynu...")
            response = await self.api_service.get_order_storage()
            
            if response.get('success'):
                new_orders = response.get('data', [])
                print(f"Załadowano {len(new_orders)} zleceń z magazynu")
                
                # Sprawdź czy są nowe zlecenia
                if len(new_orders) > len(self.orders) and not silent:
                    toast(f"Znaleziono {len(new_orders)} zleceń")
                
                self.orders = new_orders
                self.build_orders_list()
            else:
                self.show_error("Nie udało się załadować zleceń")
                
        except Exception as error:
            print(f"Błąd podczas ładowania zleceń: {error}")
            if not silent:
                self.show_error(f"Błąd: {error}")
        finally:
            self.is_loading = False
    
    def build_orders_list(self):
        """Zbuduj listę zleceń"""
        # Usuń stare elementy
        self.orders_layout.clear_widgets()
        
        if not self.orders:
            self.update_empty_state("Brak dostępnych zleceń")
            return
        
        # Dodaj karty zleceń
        for order in self.orders:
            order_card = OrderCard(
                order_data=order,
                accept_callback=self.accept_order,
                details_callback=self.show_order_details
            )
            self.orders_layout.add_widget(order_card)
        
        # Dodaj informację o liczbie zleceń
        count_label = MDLabel(
            text=f"Łącznie: {len(self.orders)} zleceń",
            halign="center",
            theme_text_color="Hint",
            size_hint_y=None,
            height="30dp"
        )
        self.orders_layout.add_widget(count_label)
    
    def update_empty_state(self, message):
        """Aktualizuj stan pustej listy"""
        self.orders_layout.clear_widgets()
        self.empty_label.text = message
        self.orders_layout.add_widget(self.empty_label)
    
    def show_error(self, message):
        """Pokaż błąd"""
        self.orders_layout.clear_widgets()
        
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
            on_release=lambda x: asyncio.create_task(self.load_orders())
        )
        
        self.orders_layout.add_widget(error_label)
        self.orders_layout.add_widget(retry_button)
    
    def accept_order(self, order_data):
        """Przyjmij zlecenie z magazynu"""
        order_id = order_data.get('id')
        print(f"Przyjmuję zlecenie z magazynu: {order_id}")
        
        # Pokaż dialog potwierdzenia
        dialog = MDDialog(
            title="Potwierdzenie",
            text=f"Czy na pewno chcesz przyjąć zlecenie #{order_id}?",
            buttons=[
                MDFlatButton(
                    text="ANULUJ",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="PRZYJMIJ",
                    on_release=lambda x: self.confirm_accept_order(dialog, order_id)
                )
            ]
        )
        dialog.open()
    
    def confirm_accept_order(self, dialog, order_id):
        """Potwierdź przyjęcie zlecenia"""
        dialog.dismiss()
        asyncio.create_task(self._accept_order_async(order_id))
    
    async def _accept_order_async(self, order_id):
        """Asynchronicznie przyjmij zlecenie"""
        try:
            toast("Przyjmowanie zlecenia...")
            response = await self.api_service.accept_order_from_storage(order_id)
            
            if response.get('success'):
                toast("Zlecenie przyjęte!")
                # Odśwież listę zleceń
                await self.load_orders()
            else:
                toast("Nie udało się przyjąć zlecenia")
                
        except Exception as error:
            print(f"Błąd podczas przyjmowania zlecenia: {error}")
            toast("Błąd przy przyjmowaniu zlecenia")
    
    def show_order_details(self, order_data):
        """Pokaż szczegóły zlecenia"""
        order_id = order_data.get('id', 'N/A')
        pickup = order_data.get('pickup_address', 'Brak')
        destination = order_data.get('destination_address', 'Brak')
        price = order_data.get('price', 'N/A')
        distance = order_data.get('distance', 'N/A')
        time = order_data.get('estimated_time', 'N/A')
        created = order_data.get('created_at', 'N/A')
        
        details_text = f"""
🚖 Zlecenie #{order_id}

📍 Odbiór:
{pickup}

🎯 Cel:
{destination}

💰 Cena: {price} PLN
📏 Dystans: {distance} km
⏱️ Czas: ~{time} min
📅 Utworzono: {self.format_date(created) if created != 'N/A' else 'N/A'}
        """.strip()
        
        dialog = MDDialog(
            title="Szczegóły zlecenia",
            text=details_text,
            buttons=[
                MDFlatButton(
                    text="ZAMKNIJ",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="PRZYJMIJ",
                    on_release=lambda x: self.accept_from_details(dialog, order_data)
                )
            ]
        )
        dialog.open()
    
    def accept_from_details(self, dialog, order_data):
        """Przyjmij zlecenie z okna szczegółów"""
        dialog.dismiss()
        self.accept_order(order_data)
    
    def format_date(self, date_string):
        """Formatuj datę"""
        try:
            if 'T' in date_string:
                dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d.%m.%Y %H:%M')
        except:
            return date_string
    
    def refresh_orders(self):
        """Odśwież zlecenia"""
        toast("Odświeżanie zleceń...")
        asyncio.create_task(self.load_orders())
    
    def go_back(self):
        """Wróć do poprzedniego ekranu"""
        if self.manager:
            self.manager.current = 'home'
    
    def on_leave(self):
        """Anuluj automatyczne odświeżanie przy opuszczeniu ekranu"""
        if hasattr(self, 'refresh_event'):
            self.refresh_event.cancel()
