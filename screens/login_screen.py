# filepath: taxi-driver-python/screens/login_screen.py
"""
🔐 Login Screen - Enhanced with comprehensive error handling
Maintains identical functionality with robust error prevention
"""

from kivy.clock import Clock
from kivy.logger import Logger
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.relativelayout import MDRelativeLayout
import asyncio
import threading
import keyring
import re


class LoginScreenError(Exception):
    """Custom exception for LoginScreen errors"""
    pass


class LoginScreen(MDScreen):
    """
    Enhanced Login Screen with comprehensive error handling
    Prevents crashes and provides graceful error recovery
    """

    def __init__(self, api_service, on_login_success, **kwargs):
        super().__init__(**kwargs)
        self.api_service = api_service
        self.on_login_success = on_login_success

        # State management
        self.phone = ""
        self.password = ""
        self.is_loading = False
        self.error = ""
        self.secure_text_entry = True

        # Validation state
        self.validation_errors = {}
        self.login_attempts = 0
        self.max_login_attempts = 5

        # Error handling state
        self.is_initialized = False
        self.error_count = 0
        self.max_errors = 10

        try:
            self.build_ui()
            self.is_initialized = True
            # Load saved credentials after UI is ready
            Clock.schedule_once(self.safe_load_saved_credentials, 0.1)
        except Exception as e:
            Logger.error(f"Failed to initialize LoginScreen: {e}")
            self.show_error("Błąd inicjalizacji ekranu logowania")

    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format with error handling"""
        try:
            if not phone or len(phone.strip()) == 0:
                msg = "Numer telefonu jest wymagany"
                self.validation_errors['phone'] = msg
                return False

            # Remove spaces and special characters
            clean_phone = re.sub(r'[^\d+]', '', phone.strip())

            if len(clean_phone) < 9:
                msg = "Numer telefonu jest za krótki"
                self.validation_errors['phone'] = msg
                return False

            if len(clean_phone) > 15:
                msg = "Numer telefonu jest za długi"
                self.validation_errors['phone'] = msg
                return False

            # Clear validation error
            if 'phone' in self.validation_errors:
                del self.validation_errors['phone']

            return True
        except Exception as e:
            Logger.error(f"Phone validation error: {e}")
            self.validation_errors['phone'] = "Błąd walidacji numeru"
            return False

    def validate_password(self, password: str) -> bool:
        """Validate password with error handling"""
        try:
            if not password or len(password.strip()) == 0:
                msg = "Hasło jest wymagane"
                self.validation_errors['password'] = msg
                return False

            if len(password) < 3:
                msg = "Hasło jest za krótkie"
                self.validation_errors['password'] = msg
                return False

            # Clear validation error
            if 'password' in self.validation_errors:
                del self.validation_errors['password']

            return True
        except Exception as e:
            Logger.error(f"Password validation error: {e}")
            self.validation_errors['password'] = "Błąd walidacji hasła"
            return False

    def validate_form(self) -> bool:
        """Validate entire form and update UI"""
        try:
            phone_valid = self.validate_phone(self.phone)
            password_valid = self.validate_password(self.password)

            # Update UI with validation errors
            self.update_validation_ui()

            return phone_valid and password_valid
        except Exception as e:
            Logger.error(f"Form validation error: {e}")
            return False

    def update_validation_ui(self):
        """Update UI to show validation errors"""
        try:
            if not self.is_initialized:
                return

            self.update_field_references()

            # Update phone field
            if 'phone' in self.validation_errors:
                if hasattr(self, 'phone_field'):
                    self.phone_field.error = True
                    msg = self.validation_errors['phone']
                    self.phone_field.helper_text = msg
            else:
                if hasattr(self, 'phone_field'):
                    self.phone_field.error = False
                    self.phone_field.helper_text = ""

            # Update password field
            if 'password' in self.validation_errors:
                if hasattr(self, 'password_field'):
                    self.password_field.error = True
                    msg = self.validation_errors['password']
                    self.password_field.helper_text = msg
            else:
                if hasattr(self, 'password_field'):
                    self.password_field.error = False
                    self.password_field.helper_text = ""

        except Exception as e:
            Logger.error(f"UI validation update error: {e}")

    def build_ui(self):
        """Build user interface with error handling"""
        try:
            # Main container
            main_layout = MDBoxLayout(
                orientation='vertical',
                spacing='20dp',
                adaptive_height=True,
                pos_hint={'center_x': 0.5, 'center_y': 0.5}
            )

            # Logo container
            logo_container = MDBoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height='100dp',
                spacing='10dp'
            )

            # Logo
            logo_label = MDLabel(
                text='🚖 TaxiDriver',
                theme_text_color='Primary',
                font_style='H4',
                halign='center',
                size_hint_y=None,
                height='60dp'
            )
            logo_container.add_widget(logo_label)

            # Card container
            card = MDCard(
                size_hint=(None, None),
                size=('300dp', '400dp'),
                pos_hint={'center_x': 0.5},
                elevation=10,
                padding='20dp'
            )

            # Card layout
            card_layout = MDBoxLayout(
                orientation='vertical',
                spacing='15dp',
                adaptive_height=True
            )

            # Title
            title_label = MDLabel(
                text='Zaloguj się',
                theme_text_color='Primary',
                font_style='H6',
                halign='center',
                size_hint_y=None,
                height='40dp'
            )
            card_layout.add_widget(title_label)

            # Phone input
            self.phone_field = MDTextField(
                hint_text='Numer telefonu',
                helper_text='Wprowadź numer telefonu',
                helper_text_mode='on_focus',
                icon_right='phone',
                size_hint_y=None,
                height='56dp'
            )
            self.phone_field.bind(text=self.on_phone_change)
            card_layout.add_widget(self.phone_field)

            # Password container
            password_container = MDRelativeLayout(
                size_hint_y=None,
                height='56dp'
            )

            # Password input
            self.password_field = MDTextField(
                hint_text='Hasło',
                helper_text='Wprowadź hasło',
                helper_text_mode='on_focus',
                password=True,
                icon_right='eye-off'
            )
            self.password_field.bind(text=self.on_password_change)

            # Password toggle button
            self.toggle_password_btn = MDIconButton(
                icon='eye-off',
                pos_hint={'center_y': 0.5, 'right': 1},
                on_release=self.safe_toggle_password_visibility
            )

            password_container.add_widget(self.password_field)
            password_container.add_widget(self.toggle_password_btn)
            card_layout.add_widget(password_container)

            # Error label
            self.error_label = MDLabel(
                text='',
                theme_text_color='Error',
                size_hint_y=None,
                height='30dp',
                halign='center'
            )
            card_layout.add_widget(self.error_label)

            # Login button
            self.login_button = MDRaisedButton(
                text='ZALOGUJ',
                size_hint=(1, None),
                height='40dp',
                on_release=self.safe_handle_login
            )
            card_layout.add_widget(self.login_button)

            # Progress bar
            self.progress_bar = MDProgressBar(
                size_hint_y=None,
                height='4dp',
                opacity=0
            )
            card_layout.add_widget(self.progress_bar)

            card.add_widget(card_layout)
            main_layout.add_widget(logo_container)
            main_layout.add_widget(card)
            self.add_widget(main_layout)

        except Exception as e:
            Logger.error(f"UI build error: {e}")
            raise LoginScreenError(f"Failed to build UI: {e}")

    def safe_load_saved_credentials(self, dt):
        """Safely load saved credentials with error handling"""
        try:
            phone = keyring.get_password("taxi_driver", "phone")
            password = keyring.get_password("taxi_driver", "password")

            if phone and password:
                self.phone = phone
                self.password = password
                if hasattr(self, 'phone_field'):
                    self.phone_field.text = phone
                if hasattr(self, 'password_field'):
                    self.password_field.text = password
                Logger.info("Loaded saved credentials successfully")
            else:
                Logger.info("No saved credentials found")

        except Exception as e:
            Logger.error(f"Error loading saved credentials: {e}")
            # Continue without saved credentials

    def on_phone_change(self, instance, value):
        """Handle phone input changes with error handling"""
        try:
            self.phone = value
            self.error_label.text = ""
            # Validate on change for immediate feedback
            if value:
                self.validate_phone(value)
                self.update_validation_ui()
        except Exception as e:
            Logger.error(f"Phone change error: {e}")

    def on_password_change(self, instance, value):
        """Handle password input changes with error handling"""
        try:
            self.password = value
            self.error_label.text = ""
            # Validate on change for immediate feedback
            if value:
                self.validate_password(value)
                self.update_validation_ui()
        except Exception as e:
            Logger.error(f"Password change error: {e}")

    def safe_toggle_password_visibility(self, instance=None):
        """Safely toggle password visibility"""
        try:
            self.update_field_references()
            if hasattr(self, 'password_field'):
                self.secure_text_entry = not self.secure_text_entry
                self.password_field.password = self.secure_text_entry

                if hasattr(self, 'toggle_password_btn'):
                    icon = "eye-off" if self.secure_text_entry else "eye"
                    self.toggle_password_btn.icon = icon

        except Exception as e:
            Logger.error(f"Password visibility toggle error: {e}")

    def set_loading(self, loading: bool):
        """Set loading state with error handling"""
        try:
            self.is_loading = loading
            if hasattr(self, 'login_button'):
                self.login_button.disabled = loading

            if hasattr(self, 'progress_bar'):
                self.progress_bar.opacity = 1 if loading else 0

        except Exception as e:
            Logger.error(f"Loading state error: {e}")

    def set_error(self, error_message: str):
        """Set error message with error handling"""
        try:
            self.error = error_message
            if hasattr(self, 'error_label'):
                self.error_label.text = error_message
            Logger.warning(f"Login error displayed: {error_message}")
        except Exception as e:
            Logger.error(f"Error display error: {e}")

    def safe_handle_login(self, instance=None):
        """Safely handle login with comprehensive error handling"""
        try:
            # Validate form first
            if not self.validate_form():
                return

            # Check login attempts
            if self.login_attempts >= self.max_login_attempts:
                msg = "Zbyt wiele prób logowania. Spróbuj ponownie później."
                self.set_error(msg)
                return

            self.set_error('')
            self.set_loading(True)

            # Run login in thread to prevent UI blocking
            threading.Thread(
                target=self._perform_login,
                daemon=True
            ).start()

        except Exception as e:
            Logger.error(f"Login handling error: {e}")
            self.set_loading(False)
            self.set_error("Błąd podczas logowania")

    def _perform_login(self):
        """Perform actual login with error handling"""
        try:
            # Call API service
            result = asyncio.run(
                self.api_service.login(self.phone, self.password)
            )            # Schedule UI updates on main thread
            if result.get('success'):
                # Save credentials on successful login
                try:
                    keyring.set_password("taxi_driver", "phone", self.phone)
                    keyring.set_password("taxi_driver", "password",
                                         self.password)
                except Exception as save_error:
                    Logger.warning(f"Failed to save credentials: {save_error}")

                Clock.schedule_once(
                    lambda dt: self._handle_login_success(result), 0
                )
            else:
                Clock.schedule_once(
                    lambda dt: self._handle_login_error(result), 0
                )
        
        except Exception as login_error:
            error_message = str(login_error)
            Clock.schedule_once(
                lambda dt: self._handle_login_exception(error_message), 0
            )

        # Always reset loading state
        Clock.schedule_once(lambda dt: self.set_loading(False), 0)

    def _handle_login_success(self, result):
        """Handle successful login"""
        try:
            self.reset_login_attempts()
            self.on_login_success(result)
        except Exception as e:
            Logger.error(f"Login success handling error: {e}")

    def _handle_login_error(self, result):
        """Handle login error response"""
        try:
            self.login_attempts += 1
            default_msg = "Nie udało się zalogować. Sprawdź dane logowania."
            error_message = result.get('message', default_msg)
            Logger.error(f"Login error: {error_message}")
            self.set_error(error_message)
        except Exception as e:
            Logger.error(f"Login error handling error: {e}")
            self.set_error("Błąd podczas przetwarzania odpowiedzi")

    def _handle_login_exception(self, error_message):
        """Handle login exception"""
        try:
            self.login_attempts += 1
            Logger.error(f"Login exception: {error_message}")
            self.set_error(f'Błąd połączenia: {error_message}')
        except Exception as e:
            Logger.error(f"Exception handling error: {e}")
            self.set_error("Nieoczekiwany błąd")

    def reset_login_attempts(self):
        """Reset login attempts counter"""
        try:
            self.login_attempts = 0
        except Exception as e:
            Logger.error(f"Reset login attempts error: {e}")

    def show_error(self, message: str):
        """Show error message with fallback"""
        try:
            self.set_error(message)
        except Exception as e:
            Logger.error(f"Show error failed: {e}")
            # Last resort error display
            print(f"ERROR: {message}")

    def clear_form(self):
        """Clear form data safely"""
        try:
            self.phone = ""
            self.password = ""
            self.validation_errors = {}

            if hasattr(self, 'phone_field'):
                self.phone_field.text = ""
                self.phone_field.error = False
                self.phone_field.helper_text = ""

            if hasattr(self, 'password_field'):
                self.password_field.text = ""
                self.password_field.error = False
                self.password_field.helper_text = ""

            self.set_error("")

        except Exception as e:
            Logger.error(f"Clear form error: {e}")

    def update_field_references(self):
        """Update field references safely"""
        try:
            # Ensure field references are current
            if not hasattr(self, 'phone_field'):
                # Try to find phone field in children
                for child in self.walk():
                    if hasattr(child, 'hint_text'):
                        if 'telefon' in child.hint_text.lower():
                            self.phone_field = child
                            break

            if not hasattr(self, 'password_field'):
                # Try to find password field in children
                for child in self.walk():
                    if hasattr(child, 'hint_text'):
                        if 'hasło' in child.hint_text.lower():
                            self.password_field = child
                            break

        except Exception as e:
            Logger.error(f"Field reference update error: {e}")

    def cleanup(self):
        """Clean up resources safely"""
        try:
            self.clear_form()
            self.reset_login_attempts()
            self.validation_errors = {}
            self.error_count = 0
            Logger.info("LoginScreen cleanup completed")
        except Exception as e:
            Logger.error(f"LoginScreen cleanup error: {e}")
