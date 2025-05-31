# filepath: taxi-driver-python/screens/home_screen.py
"""
🏠 Home Screen - Enhanced with comprehensive error handling
Main screen with map, orders, and real-time functionality
Maintains stability and provides graceful error recovery
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.logger import Logger
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.label import MDLabel
from kivymd.toast import toast
import asyncio
import threading
import traceback


class HomeScreenError(Exception):
    """Custom exception for HomeScreen errors"""
    pass


class MapViewWidget(FloatLayout):
    """Safe map view widget with error handling"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.region = {
            'latitude': 52.2297,
            'longitude': 21.0122,
            'latitudeDelta': 0.0922,
            'longitudeDelta': 0.0421
        }
        self.build_fallback_ui()

    def build_fallback_ui(self):
        """Build fallback UI when map is not available"""
        try:
            # Fallback map display
            self.location_label = Label(
                text=f"Lokalizacja: "
                     f"{self.region['latitude']:.4f}, "
                     f"{self.region['longitude']:.4f}",
                size_hint=(1, 0.1),
                pos_hint={'top': 1}
            )

            self.map_label = Label(
                text="🗺️ MAPA\n"
                     "(Tutaj będzie widok mapy z lokalizacją i zleceniami)",
                halign='center',
                valign='center'
            )

            self.add_widget(self.location_label)
            self.add_widget(self.map_label)

        except Exception as e:
            Logger.error(f"MapViewWidget build error: {e}")

    def update_region(self, latitude, longitude):
        """Update map region safely"""
        try:
            self.region['latitude'] = latitude
            self.region['longitude'] = longitude
            if hasattr(self, 'location_label'):
                text = f"Lokalizacja: {latitude:.4f}, {longitude:.4f}"
                self.location_label.text = text
        except Exception as e:
            Logger.error(f"Map region update error: {e}")


class OrderDialog(MDDialog):
    """Safe order dialog with error handling"""

    def __init__(self, order_data, on_accept=None, on_reject=None, **kwargs):
        self.order_data = order_data
        self.on_accept_callback = on_accept
        self.on_reject_callback = on_reject

        try:
            super().__init__(
                title="Nowe zlecenie",
                text=self._format_order_text(),
                buttons=[
                    MDFlatButton(
                        text="ODRZUĆ",
                        on_release=self.safe_reject
                    ),
                    MDRaisedButton(
                        text="PRZYJMIJ",
                        on_release=self.safe_accept
                    ),
                ],
                **kwargs
            )
        except Exception as e:
            Logger.error(f"OrderDialog init error: {e}")

    def _format_order_text(self):
        """Format order text safely"""
        try:
            if not self.order_data:
                return "Brak danych zlecenia"

            pickup = self.order_data.get('pickup_address', 'Nieznana')
            destination = self.order_data.get('destination_address', 'Nieznana')
            distance = self.order_data.get('distance', 'N/A')

            return f"Od: {pickup}\nDo: {destination}\nOdległość: {distance} km"
        except Exception as e:
            Logger.error(f"Order text formatting error: {e}")
            return "Błąd formatowania zlecenia"

    def safe_accept(self, *args):
        """Safely handle order acceptance"""
        try:
            if self.on_accept_callback:
                self.on_accept_callback(self.order_data)
            self.dismiss()
        except Exception as e:
            Logger.error(f"Order accept error: {e}")

    def safe_reject(self, *args):
        """Safely handle order rejection"""
        try:
            if self.on_reject_callback:
                self.on_reject_callback(self.order_data)
            self.dismiss()
        except Exception as e:
            Logger.error(f"Order reject error: {e}")


class MapScreen(Screen):
    """Original MapScreen with enhanced error handling"""

    def __init__(self, api_service, location_service, sound_service, **kwargs):
        super().__init__(**kwargs)
        self.api_service = api_service
        self.location_service = location_service
        self.sound_service = sound_service

        # State management
        self.current_orders = []
        self.current_pool_order = None
        self.driver_status = 'online'
        self.is_location_tracking = False

        # Error handling
        self.error_count = 0
        self.max_errors = 10

        try:
            self.build_ui()
            self.setup_services()
        except Exception as e:
            Logger.error(f"MapScreen initialization error: {e}")
            self.show_error_state()

    def build_ui(self):
        """Build UI with error handling"""
        try:
            main_layout = BoxLayout(orientation='vertical')

            # Status bar
            self.status_bar = Label(
                text="Status: 🟢 Online | Zleceń: 0",
                size_hint_y=None,
                height='40dp'
            )

            # Map view
            self.map_view = MapViewWidget()

            # Control buttons
            control_layout = BoxLayout(
                size_hint_y=None,
                height='60dp',
                spacing='10dp'
            )

            self.status_button = Button(
                text="Status: Online",
                on_release=self.safe_toggle_status
            )

            self.refresh_button = Button(
                text="Odśwież",
                on_release=self.safe_refresh_orders
            )

            control_layout.add_widget(self.status_button)
            control_layout.add_widget(self.refresh_button)

            main_layout.add_widget(self.status_bar)
            main_layout.add_widget(self.map_view)
            main_layout.add_widget(control_layout)

            self.add_widget(main_layout)

        except Exception as e:
            Logger.error(f"UI build error: {e}")
            raise HomeScreenError(f"Failed to build UI: {e}")

    def setup_services(self):
        """Setup services with error handling"""
        try:
            # Setup location service
            if self.location_service:
                self.location_service.add_location_listener(
                    self.handle_location_change
                )
                self.location_service.safe_start_location_updates()
            else:
                Logger.warning("Location service not available")

            # Setup periodic order checking
            check_interval = 10  # seconds
            self.pool_check_event = Clock.schedule_interval(
                self.check_order_pool_sync, check_interval
            )

        except Exception as e:
            Logger.error(f"Service setup error: {e}")

    def handle_location_change(self, location):
        """Handle location changes with error handling"""
        try:
            if not location:
                return

            if 'latitude' in location and 'longitude' in location:
                if hasattr(self, 'map_view'):
                    self.map_view.update_region(
                        location['latitude'],
                        location['longitude']
                    )

                # Update location on server
                self.safe_update_location(
                    location['latitude'],
                    location['longitude']
                )

        except Exception as e:
            Logger.error(f"Location change handling error: {e}")

    def safe_update_location(self, latitude, longitude):
        """Safely update location on server"""
        try:
            def update_task():
                try:
                    asyncio.run(
                        self.api_service.update_location(latitude, longitude)
                    )
                except Exception as e:
                    Logger.error(f"Location update API error: {e}")

            threading.Thread(target=update_task, daemon=True).start()

        except Exception as e:
            Logger.error(f"Location update error: {e}")

    def check_order_pool_sync(self, dt):
        """Check order pool synchronously with error handling"""
        try:
            threading.Thread(
                target=self.safe_check_order_pool,
                daemon=True
            ).start()
        except Exception as e:
            Logger.error(f"Order pool check scheduling error: {e}")

    def safe_check_order_pool(self):
        """Safely check order pool"""
        try:
            # Simulate order pool check
            new_pool_orders = []  # Would come from API

            if new_pool_orders:
                Logger.info(f"Found {len(new_pool_orders)} orders in pool")

                # Check if current order still exists
                if self.current_pool_order:
                    still_exists = any(
                        order['id'] == self.current_pool_order['id']
                        for order in new_pool_orders
                    )

                    if not still_exists:
                        msg = f"Order {self.current_pool_order['id']} " \
                              f"no longer in pool"
                        Logger.info(msg)
                        self.current_pool_order = None

                # Look for new acceptable orders
                acceptable_orders = [
                    order for order in new_pool_orders
                    if not order.get('status') or
                    order.get('status') == 'pending'
                ]

                if acceptable_orders and not self.current_pool_order:
                    Logger.info(f"Found new order: {acceptable_orders[0]}")
                    self.current_pool_order = acceptable_orders[0]
                    Clock.schedule_once(
                        lambda dt: self.safe_show_order_dialog(
                            acceptable_orders[0]
                        ), 0
                    )

        except Exception as e:
            Logger.error(f"Order pool check error: {e}")

    def safe_show_order_dialog(self, order):
        """Safely show order dialog"""
        try:
            dialog = OrderDialog(
                order,
                on_accept=self.safe_accept_order,
                on_reject=self.safe_reject_order
            )
            dialog.open()

            # Play notification sound
            if self.sound_service:
                self.sound_service.play_sound('new_order')

        except Exception as e:
            Logger.error(f"Order dialog error: {e}")
            toast("Błąd wyświetlania zlecenia")

    def safe_accept_order(self, order):
        """Safely accept order"""
        try:
            self.current_orders.append(order)
            self.current_pool_order = None
            self.update_status_display()
            toast("Zlecenie przyjęte")
            Logger.info(f"Order accepted: {order.get('id')}")
        except Exception as e:
            Logger.error(f"Order acceptance error: {e}")
            toast("Błąd przyjmowania zlecenia")

    def safe_reject_order(self, order):
        """Safely reject order"""
        try:
            self.current_pool_order = None
            toast("Zlecenie odrzucone")
            Logger.info(f"Order rejected: {order.get('id')}")
        except Exception as e:
            Logger.error(f"Order rejection error: {e}")

    def safe_toggle_status(self, instance=None):
        """Safely toggle driver status"""
        try:
            if self.driver_status == 'online':
                self.driver_status = 'offline'
            else:
                self.driver_status = 'online'

            self.update_status_display()
            toast(f"Status zmieniony na: {self.driver_status}")

        except Exception as e:
            Logger.error(f"Status toggle error: {e}")

    def safe_refresh_orders(self, instance=None):
        """Safely refresh orders"""
        try:
            toast("Odświeżanie zleceń...")
            # Would refresh from API
            self.update_status_display()
        except Exception as e:
            Logger.error(f"Order refresh error: {e}")
            toast("Błąd odświeżania")

    def update_status_display(self):
        """Update status display safely"""
        try:
            status_icons = {
                'online': '🟢 Online',
                'busy': '🟡 Zajęty',
                'offline': '🔴 Offline',
            }

            status_text = status_icons.get(self.driver_status, '❓ Nieznany')
            orders_count = len(self.current_orders)

            if hasattr(self, 'status_bar'):
                self.status_bar.text = f"Status: {status_text} | " \
                                       f"Zleceń: {orders_count}"

            if hasattr(self, 'status_button'):
                self.status_button.text = f"Status: {self.driver_status}"

        except Exception as e:
            Logger.error(f"Status display update error: {e}")

    def show_error_state(self):
        """Show error state UI"""
        try:
            self.clear_widgets()
            error_layout = BoxLayout(
                orientation='vertical',
                spacing='20dp'
            )

            error_label = Label(
                text='Błąd inicjalizacji aplikacji\n'
                     'Spróbuj ponownie uruchomić',
                halign='center'
            )

            retry_button = Button(
                text='Spróbuj ponownie',
                size_hint=(None, None),
                size=('200dp', '50dp'),
                pos_hint={'center_x': 0.5},
                on_release=self.safe_retry_initialization
            )

            error_layout.add_widget(error_label)
            error_layout.add_widget(retry_button)
            self.add_widget(error_layout)

        except Exception as e:
            Logger.error(f"Error state display error: {e}")

    def safe_retry_initialization(self, instance=None):
        """Safely retry initialization"""
        try:
            self.clear_widgets()
            self.error_count = 0
            self.build_ui()
            self.setup_services()
            toast("Ponowna inicjalizacja zakończona")
        except Exception as e:
            Logger.error(f"Retry initialization error: {e}")
            toast("Błąd ponownej inicjalizacji")

    def cleanup(self):
        """Clean up resources safely"""
        try:
            # Stop scheduled events
            if hasattr(self, 'pool_check_event'):
                self.pool_check_event.cancel()

            # Remove location listeners
            if self.location_service:
                self.location_service.remove_location_listener(
                    self.handle_location_change
                )

            # Clear state
            self.current_orders = []
            self.current_pool_order = None

            Logger.info("MapScreen cleanup completed")

        except Exception as e:
            Logger.error(f"MapScreen cleanup error: {e}")


class SafeHomeScreen(Screen):
    """Enhanced HomeScreen with comprehensive error handling"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Error handling state
        self.error_count = 0
        self.max_errors = 10
        self.is_initialized = False
        self.services_validated = False

        # Service references
        self.api_service = None
        self.location_service = None
        self.sound_service = None

        try:
            self.validate_services()
            self.safe_build_ui()
            self.safe_setup_services()
            self.is_initialized = True
            Logger.info("SafeHomeScreen initialized successfully")

        except Exception as e:
            self.handle_critical_error(e)

    def validate_services(self):
        """Validate required services"""
        try:
            # Try to import and validate services
            try:
                from services.api_service import APIService
                self.api_service = APIService("https://api.example.com")
            except Exception as e:
                Logger.warning(f"API service validation failed: {e}")

            try:
                from services.location_service import LocationService
                self.location_service = LocationService()
            except Exception as e:
                Logger.warning("Location service not available - simulation mode")

            try:
                from services.sound_service import SoundService
                self.sound_service = SoundService()
            except Exception as e:
                Logger.warning("Sound service not available - silent mode")

            self.services_validated = True

        except Exception as e:
            Logger.error(f"Service validation error: {e}")
            raise HomeScreenError(f"Service validation failed: {e}")

    def safe_build_ui(self):
        """Safely build UI components"""
        try:
            # Create map screen with validated services
            self.map_screen = MapScreen(
                api_service=self.api_service,
                location_service=self.location_service,
                sound_service=self.sound_service
            )

            self.add_widget(self.map_screen)

        except Exception as e:
            Logger.error(f"UI build error: {e}")
            self.create_error_state()

    def safe_setup_services(self):
        """Safely setup background services"""
        try:
            if self.location_service:
                # Setup location updates
                self.location_service.add_location_listener(
                    self.handle_location_update
                )

            Logger.info("Services setup completed")

        except Exception as e:
            Logger.error(f"Service setup error: {e}")

    def handle_location_update(self, location):
        """Handle location updates with validation"""
        try:
            if not location:
                return

            # Validate location data
            required_fields = ['latitude', 'longitude']
            if not all(field in location for field in required_fields):
                Logger.warning("Invalid location data received")
                return

            # Process location update
            if hasattr(self, 'map_screen'):
                self.map_screen.handle_location_change(location)

        except Exception as e:
            Logger.error(f"Location update handling error: {e}")

    def handle_critical_error(self, error):
        """Handle critical errors that prevent normal operation"""
        try:
            self.error_count += 1
            Logger.error(f"Critical HomeScreen error ({self.error_count}): "
                         f"{error}")

            if self.error_count >= self.max_errors:
                Logger.critical("Maximum error count reached - showing "
                                "fallback UI")
                self.create_error_state()
            else:
                self.create_error_state()

        except Exception as e:
            Logger.critical(f"Error handling failure: {e}")

    def create_error_state(self):
        """Create error state UI"""
        try:
            self.clear_widgets()

            error_layout = BoxLayout(
                orientation='vertical',
                spacing='20dp',
                padding='20dp'
            )

            error_label = MDLabel(
                text='Błąd inicjalizacji aplikacji\n'
                     'Spróbuj ponownie uruchomić',
                halign='center',
                theme_text_color='Error'
            )

            retry_button = MDRaisedButton(
                text='Spróbuj ponownie',
                size_hint=(None, None),
                size=('200dp', '50dp'),
                pos_hint={'center_x': 0.5},
                on_release=self.safe_retry
            )

            error_layout.add_widget(error_label)
            error_layout.add_widget(retry_button)
            self.add_widget(error_layout)

        except Exception as e:
            Logger.critical(f"Error state creation failed: {e}")

    def safe_retry(self, instance=None):
        """Safely retry initialization"""
        try:
            self.clear_widgets()
            self.error_count = 0
            self.is_initialized = False

            self.validate_services()
            self.safe_build_ui()
            self.safe_setup_services()
            self.is_initialized = True

            toast("Aplikacja zresetowana pomyślnie")

        except Exception as e:
            Logger.error(f"Retry failed: {e}")
            toast("Błąd podczas resetowania")
            self.create_error_state()

    def cleanup(self):
        """Clean up resources safely"""
        try:
            if hasattr(self, 'map_screen'):
                self.map_screen.cleanup()

            if self.location_service:
                self.location_service.cleanup()

            Logger.info("SafeHomeScreen cleanup completed")

        except Exception as e:
            Logger.error(f"SafeHomeScreen cleanup error: {e}")


# Export the safe version as default
HomeScreen = SafeHomeScreen
