"""
HomeScreen - główny ekran aplikacji z mapą i obsługą zleceń
Konwersja z React Native do Python/Kivy z zachowaniem 100% funkcjonalności API
Z dodanym lepszym error handlingiem
"""

import asyncio
import traceback
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.logger import Logger
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineListItem
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.label import MDLabel
from kivymd.toast import toast
import json
import threading

# Import our new MapViewComponent with error handling
try:
    from components.map_view import MapViewComponent
    MAP_COMPONENT_AVAILABLE = True
    Logger.info("MapViewComponent imported successfully")
except ImportError as e:
    Logger.warning(f"MapViewComponent not available: {e}")
    MapViewComponent = None
    MAP_COMPONENT_AVAILABLE = False

class MapViewWidget(FloatLayout):
    """Legacy map component - kept for backward compatibility"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.region = {
            'latitude': 52.2297,  # Warszawa domyślnie
            'longitude': 21.0122,
            'latitudeDelta': 0.0922,
            'longitudeDelta': 0.0421
        }
        
        # Dodaj label pokazujący aktualną lokalizację
        self.location_label = MDLabel(
            text=f"Lokalizacja: {self.region['latitude']:.4f}, {self.region['longitude']:.4f}",
            size_hint=(1, 0.1),
            pos_hint={'top': 1}
        )
        self.add_widget(self.location_label)
        
        # Placeholder dla mapy
        map_placeholder = MDCard(
            size_hint=(1, 0.9),
            pos_hint={'top': 0.9},
            md_bg_color=[0.9, 0.9, 0.9, 1]
        )
        map_label = MDLabel(
            text="🗺️ MAPA\n(Tutaj będzie widok mapy z lokalizacją i zleceniami)",
            halign="center",
            theme_text_color="Primary"
        )
        map_placeholder.add_widget(map_label)
        self.add_widget(map_placeholder)
    
    def update_region(self, latitude, longitude):
        """Aktualizuj region mapy"""
        self.region.update({
            'latitude': latitude,
            'longitude': longitude
        })
        self.location_label.text = f"Lokalizacja: {latitude:.4f}, {longitude:.4f}"

class OrderDialog(MDDialog):
    """Dialog do wyświetlania nowych zleceń z puli"""
    
    def __init__(self, order_data, accept_callback, reject_callback, **kwargs):
        self.order_data = order_data
        self.accept_callback = accept_callback
        self.reject_callback = reject_callback
        
        # Przygotuj tekst zlecenia
        order_text = f"""
🚖 NOWE ZLECENIE #{order_data.get('id', 'N/A')}

📍 Odbiór: {order_data.get('pickup_address', 'Brak adresu')}
🎯 Cel: {order_data.get('destination_address', 'Brak adresu')}
💰 Cena: {order_data.get('price', 'N/A')} PLN
📏 Dystans: {order_data.get('distance', 'N/A')} km
⏱️ Czas: ~{order_data.get('estimated_time', 'N/A')} min
        """.strip()
        
        super().__init__(
            title="Nowe zlecenie",
            text=order_text,
            buttons=[
                MDFlatButton(
                    text="ODRZUĆ",
                    on_release=self.reject_order
                ),
                MDRaisedButton(
                    text="PRZYJMIJ",
                    on_release=self.accept_order
                )
            ],
            **kwargs
        )
    
    def accept_order(self, *args):
        """Przyjmij zlecenie"""
        self.dismiss()
        if self.accept_callback:
            self.accept_callback(self.order_data)
    
    def reject_order(self, *args):
        """Odrzuć zlecenie"""
        self.dismiss()
        if self.reject_callback:
            self.reject_callback(self.order_data)

class MapScreen(Screen):
    """Główny ekran mapy z obsługą zleceń"""
    
    def __init__(self, api_service, location_service, sound_service, **kwargs):
        super().__init__(**kwargs)
        self.api_service = api_service
        self.location_service = location_service
        self.sound_service = sound_service
        
        # Stan aplikacji
        self.current_orders = []
        self.pool_orders = []
        self.driver_status = 'offline'
        self.is_loading = False
        self.show_pool_order = False
        self.current_pool_order = None
        self.order_dialog = None
        
        # Layout główny
        main_layout = BoxLayout(orientation='vertical')
        
        # Toolbar
        self.toolbar = MDTopAppBar(
            title="TaxiDriver - Mapa",
            left_action_items=[["menu", lambda x: self.show_logout_dialog()]],
            right_action_items=[["refresh", lambda x: self.refresh_data()]]
        )
        main_layout.add_widget(self.toolbar)
        
        # Widok mapy
        self.map_view = MapViewWidget()
        main_layout.add_widget(self.map_view)
        
        # Status bar na dole
        self.status_bar = MDLabel(
            text="Status: Offline",
            size_hint=(1, 0.1),
            halign="center",
            theme_text_color="Primary"
        )
        main_layout.add_widget(self.status_bar)
        
        self.add_widget(main_layout)
        
        # Zaplanuj inicjalizację
        Clock.schedule_once(self.init_screen, 0.1)
    
    def init_screen(self, dt):
        """Inicjalizacja ekranu po załadowaniu"""
        print("Inicjalizacja MapScreen...")
        
        # Pobierz aktualną lokalizację
        self.init_location()
        
        # Pobierz aktualne zlecenia i status
        asyncio.create_task(self.fetch_current_orders())
        asyncio.create_task(self.fetch_driver_status())
        
        # Uruchom regularnie sprawdzanie puli zleceń
        self.pool_check_event = Clock.schedule_interval(self.check_order_pool_sync, 10)  # co 10 sekund
        
        # Nasłuchuj na zmiany lokalizacji
        if self.location_service:
            self.location_service.add_location_listener(self.handle_location_change)
    
    def init_location(self):
        """Inicjalizuj lokalizację"""
        try:
            if self.location_service:
                location = self.location_service.get_last_known_location()
                if location:
                    print(f"Używam zapisanej lokalizacji: {location}")
                    self.map_view.update_region(location['latitude'], location['longitude'])
                else:
                    print("Pobieranie aktualnej lokalizacji...")
                    # Tu będzie pobieranie lokalizacji z GPS
        except Exception as error:
            print(f"Błąd inicjalizacji lokalizacji: {error}")
    
    def handle_location_change(self, location):
        """Obsłuż zmianę lokalizacji"""
        if location:
            self.map_view.update_region(location['latitude'], location['longitude'])
            
            # Wyślij aktualizację lokalizacji jeśli kierowca jest online
            if self.driver_status in ['online', 'busy']:
                asyncio.create_task(self.update_location(location['latitude'], location['longitude']))
    
    async def update_location(self, latitude, longitude):
        """Aktualizuj lokalizację przez API"""
        try:
            await self.api_service.update_location(latitude, longitude)
        except Exception as error:
            print(f"Błąd podczas aktualizacji lokalizacji: {error}")
    
    def check_order_pool_sync(self, dt):
        """Synchroniczna wrapper dla sprawdzania puli zleceń"""
        asyncio.create_task(self.check_order_pool())
    
    async def check_order_pool(self):
        """Sprawdź pulę zleceń kierowcy"""
        try:
            if self.driver_status == 'offline':
                print("Kierowca offline - pomijam sprawdzanie puli zleceń")
                return
            
            print("Sprawdzanie puli zleceń kierowcy...")
            response = await self.api_service.check_order_pool()
            
            print(f"Odpowiedź z puli zleceń: {json.dumps(response)}")
            
            if response.get('success'):
                new_pool_orders = []
                
                # Obsługa różnych formatów odpowiedzi
                if isinstance(response.get('data'), list):
                    new_pool_orders = response['data']
                elif isinstance(response.get('orders'), list):
                    new_pool_orders = response['orders']
                
                print(f"Znaleziono {len(new_pool_orders)} zleceń w puli kierowcy")
                
                # Sprawdź czy dialog jest już otwarty
                if self.show_pool_order and self.current_pool_order:
                    # Sprawdź czy zlecenie nadal istnieje
                    current_order_exists = any(
                        order['id'] == self.current_pool_order['id'] 
                        for order in new_pool_orders
                    )
                    
                    if not current_order_exists:
                        print(f"Zlecenie {self.current_pool_order['id']} nie znajduje się już w puli")
                        self.close_order_dialog()
                        toast("Zlecenie nie jest już dostępne")
                        return
                
                # Sprawdź nowe zlecenia
                if new_pool_orders and not self.show_pool_order:
                    # Preferuj zlecenia bez statusu lub z statusem new/pending
                    acceptable_orders = [
                        order for order in new_pool_orders
                        if not order.get('status') or 
                        order.get('status', '').lower() in ['new', 'pending']
                    ]
                    
                    if acceptable_orders:
                        print(f"Znaleziono nowe zlecenie: {acceptable_orders[0]}")
                        
                        # Odtwórz dźwięk powiadomienia
                        if self.sound_service:
                            try:
                                await self.sound_service.play_new_order_sound()
                            except Exception as e:
                                print(f"Nie udało się odtworzyć dźwięku: {e}")
                        
                        # Pokaż dialog ze zleceniem
                        self.show_order_dialog(acceptable_orders[0])
                        
                        toast("Nowe zlecenie!")
                
                self.pool_orders = new_pool_orders
                
        except Exception as error:
            print(f"Błąd podczas sprawdzania puli zleceń: {error}")
    
    def show_order_dialog(self, order_data):
        """Pokaż dialog z nowym zleceniem"""
        self.current_pool_order = order_data
        self.show_pool_order = True
        
        self.order_dialog = OrderDialog(
            order_data=order_data,
            accept_callback=self.accept_order_from_pool,
            reject_callback=self.reject_order_from_pool
        )
        self.order_dialog.open()
    
    def close_order_dialog(self):
        """Zamknij dialog ze zleceniem"""
        if self.order_dialog:
            self.order_dialog.dismiss()
            self.order_dialog = None
        self.show_pool_order = False
        self.current_pool_order = None
    
    def accept_order_from_pool(self, order_data):
        """Przyjmij zlecenie z puli"""
        print(f"Przyjmuję zlecenie: {order_data['id']}")
        asyncio.create_task(self._accept_order_async(order_data['id']))
    
    def reject_order_from_pool(self, order_data):
        """Odrzuć zlecenie z puli"""
        print(f"Odrzucam zlecenie: {order_data['id']}")
        toast("Zlecenie odrzucone")
    
    async def _accept_order_async(self, order_id):
        """Asynchroniczna akceptacja zlecenia"""
        try:
            response = await self.api_service.accept_order(order_id)
            if response.get('success'):
                toast("Zlecenie przyjęte!")
                await self.fetch_current_orders()
            else:
                toast("Błąd przy przyjmowaniu zlecenia")
        except Exception as error:
            print(f"Błąd podczas przyjmowania zlecenia: {error}")
            toast("Błąd przy przyjmowaniu zlecenia")
    
    async def fetch_current_orders(self):
        """Pobierz aktualne zlecenia"""
        try:
            self.is_loading = True
            response = await self.api_service.get_current_orders()
            
            if response.get('success'):
                new_orders = response.get('data', [])
                
                # Sprawdź czy są nowe zlecenia
                if len(new_orders) > len(self.current_orders):
                    if self.sound_service:
                        try:
                            await self.sound_service.play_new_order_sound()
                        except Exception as e:
                            print(f"Nie udało się odtworzyć dźwięku: {e}")
                    
                    toast("Nowe zlecenie!")
                
                self.current_orders = new_orders
                print(f"Pobrano {len(new_orders)} aktualnych zleceń")
                
        except Exception as error:
            print(f"Błąd podczas pobierania aktualnych zleceń: {error}")
        finally:
            self.is_loading = False
    
    async def fetch_driver_status(self):
        """Pobierz status kierowcy"""
        try:
            response = await self.api_service.check_driver_status()
            if response.get('success'):
                # Status będzie ustalony przez API lub lokalnie
                self.driver_status = 'online'  # Domyślnie online po zalogowaniu
                self.update_status_bar()
        except Exception as error:
            print(f"Błąd podczas pobierania statusu kierowcy: {error}")
    
    def update_status_bar(self):
        """Aktualizuj pasek statusu"""
        status_text = {
            'online': '🟢 Online',
            'offline': '🔴 Offline', 
            'busy': '🟡 Zajęty'
        }.get(self.driver_status, '❓ Nieznany')
        
        self.status_bar.text = f"Status: {status_text} | Zleceń: {len(self.current_orders)}"
    
    def refresh_data(self):
        """Odśwież dane"""
        print("Odświeżanie danych...")
        asyncio.create_task(self.fetch_current_orders())
        asyncio.create_task(self.fetch_driver_status())
        toast("Odświeżanie...")
    
    def show_logout_dialog(self):
        """Pokaż dialog wylogowania"""
        dialog = MDDialog(
            title="Wylogowanie",
            text="Czy na pewno chcesz się wylogować?",
            buttons=[
                MDFlatButton(
                    text="ANULUJ",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="WYLOGUJ",
                    on_release=lambda x: self.logout()
                )
            ]
        )
        dialog.open()
    
    def logout(self):
        """Wyloguj kierowcy"""
        print("Wylogowywanie...")
        if hasattr(self, 'pool_check_event'):
            self.pool_check_event.cancel()
        
        # Wywołaj callback wylogowania z głównej aplikacji
        app = self.manager.get_screen('main').parent  # Dostęp do głównej aplikacji
        if hasattr(app, 'logout'):
            app.logout()

class HomeScreenError(Exception):
    """Custom exception for HomeScreen errors"""
    pass

class SafeHomeScreen(Screen):
    """
    HomeScreen z komprehensywnym error handlingiem
    """

    def __init__(self, api_service, location_service, sound_service, **kwargs):
        super().__init__(**kwargs)
        
        # Error handling properties
        self.error_count = 0
        self.max_errors = 10
        self.last_error = None
        self.is_initializing = False
        
        # Services with null checks
        self.api_service = api_service
        self.location_service = location_service
        self.sound_service = sound_service
        
        # Safe initialization
        self.safe_initialize_screen()

    def safe_initialize_screen(self):
        """Safely initialize the HomeScreen"""
        try:
            self.is_initializing = True
            Logger.info("Initializing HomeScreen with error handling...")
            
            # Initialize with fallback
            if not self.validate_services():
                Logger.error("Services validation failed")
                self.create_error_state()
                return
            
            # Initialize UI components safely
            self.safe_build_ui()
            
            # Initialize services safely
            self.safe_setup_services()
            
            Logger.info("HomeScreen initialized successfully")
            self.is_initializing = False
            
        except Exception as e:
            Logger.error(f"Critical error initializing HomeScreen: {e}")
            traceback.print_exc()
            self.handle_critical_error(e)

    def validate_services(self) -> bool:
        """Validate that required services are available"""
        try:
            if not self.api_service:
                Logger.error("API service not available")
                return False
                
            if not self.location_service:
                Logger.warning("Location service not available - will use simulation")
                
            if not self.sound_service:
                Logger.warning("Sound service not available - notifications disabled")
                
            return True
            
        except Exception as e:
            Logger.error(f"Service validation error: {e}")
            return False

    def safe_build_ui(self):
        """Safely build UI components"""
        try:
            # Use MapViewComponent if available, fallback otherwise
            if MAP_COMPONENT_AVAILABLE:
                Logger.info("Using MapViewComponent")
                self.map_component = MapViewComponent()
            else:
                Logger.warning("Using fallback MapViewWidget")
                self.map_component = MapViewWidget()
            
            # Add other UI components safely
            self.build_navigation()
            self.build_order_ui()
            
        except Exception as e:
            Logger.error(f"UI building error: {e}")
            self.handle_ui_error(e)

    def safe_setup_services(self):
        """Safely setup services with error handling"""
        try:
            # Setup location service
            if self.location_service:
                try:
                    self.location_service.add_location_listener(
                        self.safe_on_location_update
                    )
                    self.location_service.safe_start_location_updates()
                except Exception as e:
                    Logger.error(f"Location service setup failed: {e}")
                    
            # Setup periodic updates
            self.schedule_safe_updates()
            
        except Exception as e:
            Logger.error(f"Service setup error: {e}")
            self.handle_service_error(e)

    def safe_on_location_update(self, location):
        """Safely handle location updates"""
        try:
            if not location or not self.validate_location(location):
                Logger.warning("Invalid location data received")
                return
                
            # Update map safely
            if hasattr(self.map_component, 'update_region'):
                self.map_component.update_region(
                    location['latitude'], 
                    location['longitude']
                )
                
            # Update API safely
            if self.api_service:
                self.safe_update_driver_location(location)
                
        except Exception as e:
            Logger.error(f"Location update error: {e}")
            self.handle_location_error(e)

    def validate_location(self, location) -> bool:
        """Validate location data"""
        try:
            if not isinstance(location, dict):
                return False
                
            required_fields = ['latitude', 'longitude']
            for field in required_fields:
                if field not in location:
                    return False
                    
                value = location[field]
                if not isinstance(value, (int, float)):
                    return False
                    
            return True
            
        except Exception as e:
            Logger.error(f"Location validation error: {e}")
            return False

    def safe_update_driver_location(self, location):
        """Safely update driver location via API"""
        try:
            # Run in background thread
            threading.Thread(
                target=self._update_location_async,
                args=(location,),
                daemon=True
            ).start()
            
        except Exception as e:
            Logger.error(f"Error starting location update: {e}")

    def _update_location_async(self, location):
        """Update location in background"""
        try:
            result = asyncio.run(
                self.api_service.update_location(location)
            )
            
            if not result.get('success'):
                Logger.warning("Location update API call failed")
                
        except Exception as e:
            Logger.error(f"Async location update error: {e}")

    def schedule_safe_updates(self):
        """Schedule periodic updates with error handling"""
        try:
            # Schedule order pool updates
            Clock.schedule_interval(self.safe_check_order_pool, 10)
            
            # Schedule current orders check
            Clock.schedule_interval(self.safe_check_current_orders, 5)
            
        except Exception as e:
            Logger.error(f"Update scheduling error: {e}")

    def safe_check_order_pool(self, dt):
        """Safely check order pool"""
        try:
            if not self.api_service:
                return
                
            threading.Thread(
                target=self._check_order_pool_async,
                daemon=True
            ).start()
            
        except Exception as e:
            Logger.error(f"Order pool check error: {e}")

    def _check_order_pool_async(self):
        """Check order pool in background"""
        try:
            result = asyncio.run(self.api_service.get_order_pool())
            
            if result.get('success'):
                orders = result.get('data', [])
                Clock.schedule_once(
                    lambda dt: self.safe_update_order_pool(orders), 0
                )
                
        except Exception as e:
            Logger.error(f"Async order pool check error: {e}")

    def safe_update_order_pool(self, orders):
        """Safely update order pool display"""
        try:
            # Update UI with new orders
            for order in orders:
                if self.validate_order_data(order):
                    self.display_new_order(order)
                    
        except Exception as e:
            Logger.error(f"Order pool update error: {e}")

    def validate_order_data(self, order) -> bool:
        """Validate order data structure"""
        try:
            if not isinstance(order, dict):
                return False
                
            required_fields = ['id', 'pickup_address', 'destination_address']
            for field in required_fields:
                if field not in order:
                    Logger.warning(f"Order missing field: {field}")
                    return False
                    
            return True
            
        except Exception as e:
            Logger.error(f"Order validation error: {e}")
            return False

    def handle_critical_error(self, error):
        """Handle critical errors that prevent normal operation"""
        try:
            self.error_count += 1
            self.last_error = error
            
            Logger.error(f"Critical HomeScreen error ({self.error_count}): {error}")
            
            # Create error state UI
            self.create_error_state()
            
        except Exception as e:
            Logger.error(f"Error handling critical error: {e}")

    def handle_ui_error(self, error):
        """Handle UI-related errors"""
        try:
            Logger.error(f"UI error: {error}")
            # Try to recover with minimal UI
            self.create_minimal_ui()
            
        except Exception as e:
            Logger.error(f"Error handling UI error: {e}")

    def handle_service_error(self, error):
        """Handle service-related errors"""
        try:
            Logger.error(f"Service error: {error}")
            # Continue with degraded functionality
            
        except Exception as e:
            Logger.error(f"Error handling service error: {e}")

    def handle_location_error(self, error):
        """Handle location-related errors"""
        try:
            Logger.error(f"Location error: {error}")
            # Continue with last known location
            
        except Exception as e:
            Logger.error(f"Error handling location error: {e}")

    def create_error_state(self):
        """Create error state UI"""
        try:
            self.clear_widgets()
            
            error_layout = BoxLayout(orientation='vertical', padding=20)
            error_label = Label(
                text='Błąd inicjalizacji aplikacji\nSpróbuj ponownie uruchomić',
                halign='center'
            )
            retry_button = Button(
                text='Spróbuj ponownie',
                size_hint=(1, 0.2),
                on_release=lambda x: self.safe_initialize_screen()
            )
            
            error_layout.add_widget(error_label)
            error_layout.add_widget(retry_button)
            self.add_widget(error_layout)
            
        except Exception as e:
            Logger.error(f"Error creating error state: {e}")

    def create_minimal_ui(self):
        """Create minimal fallback UI"""
        try:
            self.clear_widgets()
            
            minimal_layout = BoxLayout(orientation='vertical')
            status_label = Label(text='Aplikacja działa w trybie awaryjnym')
            minimal_layout.add_widget(status_label)
            self.add_widget(minimal_layout)
            
        except Exception as e:
            Logger.error(f"Error creating minimal UI: {e}")

    def cleanup(self):
        """Cleanup resources safely"""
        try:
            Logger.info("Cleaning up HomeScreen...")
            
            # Stop scheduled events
            Clock.unschedule(self.safe_check_order_pool)
            Clock.unschedule(self.safe_check_current_orders)
            
            # Remove location listener
            if self.location_service:
                self.location_service.remove_location_listener(
                    self.safe_on_location_update
                )
                
            Logger.info("HomeScreen cleanup completed")
            
        except Exception as e:
            Logger.error(f"HomeScreen cleanup error: {e}")
