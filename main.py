#!/usr/bin/env python3
"""
🚗 TaxiDriver App - Python/Kivy Version
Dokładna konwersja z React Native na Python/Kivy
Zachowuje 100% kompatybilności z API
Dodany lepszy error handling żeby się nie wykładała
"""

import os
import sys
import traceback
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.logger import Logger

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFabButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.toolbar import MDTopAppBar

import asyncio
import threading

# Safe imports with error handling
try:
    from services.api_service import APIService
except ImportError as e:
    Logger.error(f"Failed to import APIService: {e}")
    APIService = None

try:
    from services.location_service import LocationService
except ImportError as e:
    Logger.error(f"Failed to import LocationService: {e}")
    LocationService = None

try:
    from services.sound_service import SoundService
except ImportError as e:
    Logger.error(f"Failed to import SoundService: {e}")
    SoundService = None

try:
    from screens.login_screen import LoginScreen
except ImportError as e:
    Logger.error(f"Failed to import LoginScreen: {e}")
    LoginScreen = None

try:
    from screens.home_screen import HomeScreen
except ImportError as e:
    Logger.error(f"Failed to import HomeScreen: {e}")
    HomeScreen = None

try:
    from screens.profile_screen import ProfileScreen
except ImportError as e:
    Logger.error(f"Failed to import ProfileScreen: {e}")
    ProfileScreen = None

try:
    from screens.order_storage_screen import OrderStorageScreen
except ImportError as e:
    Logger.error(f"Failed to import OrderStorageScreen: {e}")
    OrderStorageScreen = None

try:
    from screens.messages_screen import MessagesScreen
except ImportError as e:
    Logger.error(f"Failed to import MessagesScreen: {e}")
    MessagesScreen = None


class ErrorScreen(MDScreen):
    """Screen to display errors gracefully"""
    
    def __init__(self, error_message="An error occurred", **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(20)
        )
        
        error_card = MDCard(
            size_hint=(1, None),
            height=dp(300),
            padding=dp(20),
            md_bg_color=(1, 0.95, 0.95, 1)
        )
        
        error_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(10)
        )
        
        title = MDLabel(
            text="⚠️ Error",
            font_style="H5",
            halign="center",
            size_hint_y=None,
            height=dp(50)
        )
        
        message = MDLabel(
            text=error_message,
            halign="center",
            text_color=(0.8, 0, 0, 1),
            size_hint_y=None,
            height=dp(100)
        )
        
        retry_button = MDRaisedButton(
            text="Retry",
            size_hint=(None, None),
            size=(dp(120), dp(40)),
            pos_hint={'center_x': 0.5},
            on_release=self.retry
        )
        
        error_layout.add_widget(title)
        error_layout.add_widget(message)
        error_layout.add_widget(retry_button)
        
        error_card.add_widget(error_layout)
        layout.add_widget(error_card)
        
        self.add_widget(layout)
    
    def retry(self, *args):
        """Retry the application"""
        try:
            app = App.get_running_app()
            if app:
                app.restart()
        except Exception as e:
            Logger.error(f"Failed to retry: {e}")


class TaxiDriverApp(MDApp):
    """
    Główna aplikacja kierowcy z lepszym error handlingiem
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "TaxiDriver"
        self.theme_cls.theme_style = "Light" 
        self.theme_cls.primary_palette = "Blue"
        
        # Services - initialized safely
        self.api_service = None
        self.location_service = None
        self.sound_service = None
        
        # Application state
        self.is_logged_in = False
        self.driver_data = None
        self.current_orders = []
        self.order_pool = []
        self.error_count = 0
        self.max_errors = 5
        
    def build(self):
        """Builds the application interface with error handling"""
        try:
            Logger.info("Starting TaxiDriver app build process")
            
            # Initialize screen manager
            self.screen_manager = ScreenManager()
            
            # Initialize services safely
            if not self.init_services():
                return self.create_error_screen("Failed to initialize services")
            
            # Add screens safely
            if not self.add_screens():
                return self.create_error_screen("Failed to add screens")
            
            # Schedule auto-login check
            Clock.schedule_once(self.safe_check_credentials, 1)
            
            Logger.info("TaxiDriver app built successfully")
            return self.screen_manager
            
        except Exception as e:
            Logger.error(f"Critical error building app: {e}")
            traceback.print_exc()
            return self.create_error_screen(f"Critical error: {str(e)}")
    
    def init_services(self):
        """Initialize services with error handling"""
        try:
            Logger.info("Initializing services...")
            
            # API Service
            if APIService:
                self.api_service = APIService()
                Logger.info("API service initialized")
            else:
                Logger.warning("APIService not available")
                return False
            
            # Location Service
            if LocationService:
                self.location_service = LocationService()
                Logger.info("Location service initialized")
            else:
                Logger.warning("LocationService not available")
            
            # Sound Service
            if SoundService:
                self.sound_service = SoundService()
                Logger.info("Sound service initialized")
            else:
                Logger.warning("SoundService not available")
            
            return True
            
        except Exception as e:
            Logger.error(f"Failed to initialize services: {e}")
            traceback.print_exc()
            return False
    
    def add_screens(self):
        """Add screens with error handling"""
        try:
            Logger.info("Adding screens...")
            
            # Login screen
            if LoginScreen:
                try:
                    self.login_screen = LoginScreen(
                        name='login',
                        api_service=self.api_service,
                        on_login_success=self.on_login_success
                    )
                    self.screen_manager.add_widget(self.login_screen)
                    Logger.info("Login screen added")
                except Exception as e:
                    Logger.error(f"Failed to add login screen: {e}")
                    return False
            else:
                Logger.error("LoginScreen class not available")
                return False
            
            # Home screen
            if HomeScreen:
                try:
                    self.home_screen = HomeScreen(
                        name='home',
                        api_service=self.api_service,
                        location_service=self.location_service,
                        sound_service=self.sound_service,
                        on_logout=self.on_logout
                    )
                    self.screen_manager.add_widget(self.home_screen)
                    Logger.info("Home screen added")
                except Exception as e:
                    Logger.error(f"Failed to add home screen: {e}")
                    # Continue without home screen for now
            else:
                Logger.warning("HomeScreen class not available")
            
            return True
            
        except Exception as e:
            Logger.error(f"Failed to add screens: {e}")
            traceback.print_exc()
            return False
    
    def create_error_screen(self, message):
        """Create an error screen"""
        try:
            error_screen = ErrorScreen(error_message=message, name='error')
            screen_manager = ScreenManager()
            screen_manager.add_widget(error_screen)
            return screen_manager
        except Exception as e:
            Logger.error(f"Failed to create error screen: {e}")
            # Return minimal widget
            from kivy.uix.label import Label
            return Label(text=f"Critical Error: {message}")
    
    def safe_check_credentials(self, dt):
        """Safely check saved credentials"""
        try:
            if not self.api_service:
                Logger.warning("Cannot check credentials - API service not available")
                return
            
            threading.Thread(
                target=self._check_credentials_async,
                daemon=True
            ).start()
        except Exception as e:
            Logger.error(f"Error scheduling credential check: {e}")
    
    def _check_credentials_async(self):
        """Check credentials in background thread"""
        try:
            if not self.api_service:
                return
            
            # Try auto-login
            result = asyncio.run(self.api_service.auto_login())
            
            if result.get('success'):
                Clock.schedule_once(
                    lambda dt: self.safe_login_success(result.get('data')), 0
                )
            else:
                Logger.info("No saved credentials found")
                
        except Exception as e:
            Logger.error(f"Error checking credentials: {e}")
            self.error_count += 1
            if self.error_count >= self.max_errors:
                Logger.error("Too many errors, stopping credential checks")
    
    def safe_login_success(self, driver_data):
        """Safely handle login success"""
        try:
            self.on_login_success(driver_data)
        except Exception as e:
            Logger.error(f"Error handling login success: {e}")
    
    def on_login_success(self, driver_data):
        """Handle successful login"""
        try:
            Logger.info("Login successful")
            self.is_logged_in = True
            self.driver_data = driver_data
            self.error_count = 0  # Reset error count
            
            # Switch to home screen if available
            if hasattr(self, 'home_screen'):
                self.screen_manager.current = 'home'
            
            # Start location tracking if available
            if self.location_service:
                try:
                    self.location_service.start_tracking()
                except Exception as e:
                    Logger.error(f"Failed to start location tracking: {e}")
            
            # Start order monitoring
            Clock.schedule_interval(self.safe_update_orders, 10)
            
        except Exception as e:
            Logger.error(f"Error in login success handler: {e}")
    
    def on_logout(self):
        """Handle logout"""
        try:
            Logger.info("Logging out")
            self.is_logged_in = False
            self.driver_data = None
            self.current_orders = []
            self.order_pool = []
            
            # Stop services
            if self.location_service:
                try:
                    self.location_service.stop_tracking()
                except Exception as e:
                    Logger.error(f"Error stopping location service: {e}")
            
            Clock.unschedule(self.safe_update_orders)
            
            # Logout from API
            if self.api_service:
                threading.Thread(
                    target=lambda: self.safe_api_logout(),
                    daemon=True
                ).start()
            
            # Return to login screen
            self.screen_manager.current = 'login'
            
        except Exception as e:
            Logger.error(f"Error during logout: {e}")
    
    def safe_api_logout(self):
        """Safely logout from API"""
        try:
            if self.api_service:
                asyncio.run(self.api_service.logout())
        except Exception as e:
            Logger.error(f"Error logging out from API: {e}")
    
    def safe_update_orders(self, dt):
        """Safely update orders"""
        try:
            if not self.is_logged_in or not self.api_service:
                return
            
            threading.Thread(
                target=self._update_orders_async,
                daemon=True
            ).start()
        except Exception as e:
            Logger.error(f"Error scheduling order update: {e}")
    
    def _update_orders_async(self):
        """Update orders in background"""
        try:
            if not self.api_service:
                return
            
            # Get current orders
            try:
                current_result = asyncio.run(self.api_service.get_current_orders())
                if current_result.get('success'):
                    self.current_orders = current_result.get('data', [])
            except Exception as e:
                Logger.error(f"Error getting current orders: {e}")
            
            # Get order pool
            try:
                pool_result = asyncio.run(self.api_service.check_order_pool())
                if pool_result.get('success'):
                    new_orders = pool_result.get('data', [])
                    
                    # Check for new orders
                    if len(new_orders) > len(self.order_pool):
                        if self.sound_service:
                            try:
                                self.sound_service.play_new_order_sound()
                            except Exception as e:
                                Logger.error(f"Error playing sound: {e}")
                    
                    self.order_pool = new_orders
            except Exception as e:
                Logger.error(f"Error getting order pool: {e}")
            
            # Update UI
            Clock.schedule_once(self._safe_update_ui, 0)
            
        except Exception as e:
            Logger.error(f"Error updating orders: {e}")
            self.error_count += 1
    
    def _safe_update_ui(self, dt):
        """Safely update UI with orders"""
        try:
            if hasattr(self.home_screen, 'update_orders'):
                self.home_screen.update_orders(self.current_orders, self.order_pool)
        except Exception as e:
            Logger.error(f"Error updating UI: {e}")
    
    def restart(self):
        """Restart the application"""
        try:
            Logger.info("Restarting application")
            self.stop()
            # Note: Full restart would require external process management
        except Exception as e:
            Logger.error(f"Error restarting app: {e}")


def safe_main():
    """Safely run the main application"""
    try:
        Logger.info("Starting TaxiDriver app")
        app = TaxiDriverApp()
        app.run()
    except Exception as e:
        Logger.error(f"Critical error running app: {e}")
        traceback.print_exc()
        
        # Try to show a basic error message
        try:
            from kivy.uix.label import Label
            from kivy.app import App
            
            class ErrorApp(App):
                def build(self):
                    return Label(
                        text=f"Critical Error:\n{str(e)}\n\nCheck logs for details",
                        halign='center'
                    )
            
            ErrorApp().run()
        except:
            print(f"CRITICAL ERROR: {e}")
            sys.exit(1)


if __name__ == '__main__':
    safe_main()

