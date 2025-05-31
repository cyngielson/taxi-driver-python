"""
LocationService - usługa obsługi lokalizacji
Konwersja z React Native do Python/Kivy z zachowaniem 100% funkcjonalności
Z dodanym lepszym error handlingiem
"""

import asyncio
import traceback
import time
from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.logger import Logger
import json

try:
    from plyer import gps
    HAS_GPS = True
    Logger.info("GPS plyer module available")
except ImportError as e:
    HAS_GPS = False
    Logger.warning(f"Plyer GPS not available: {e}. Using simulated location.")


class LocationServiceError(Exception):
    """Custom exception for location service errors"""
    pass


class LocationService(EventDispatcher):
    """Usługa obsługi lokalizacji GPS z error handlingiem"""

    def __init__(self):
        super().__init__()
        self.last_known_location = None
        self.is_tracking = False
        self.location_listeners = []
        self.gps_event = None
        self.simulation_event = None
        self.error_count = 0
        self.max_errors = 10
        self.last_error = None

        # Symulowana lokalizacja (Warszawa)
        self.simulated_location = {
            'latitude': 52.2297,
            'longitude': 21.0122,
            'accuracy': 10.0,
            'timestamp': time.time()
        }

        # Error handling settings
        self.location_timeout = 30  # seconds
        self.update_interval = 5    # seconds

        try:
            # Rejestruj typ eventu
            self.register_event_type('on_location_update')
            self.register_event_type('on_location_error')
            Logger.info("LocationService initialized successfully")
        except Exception as e:
            Logger.error(f"Failed to initialize LocationService: {e}")
            raise LocationServiceError(f"Initialization failed: {e}")

    def safe_start_location_updates(self):
        """Safely start location tracking"""
        try:
            self.start_location_updates()
        except Exception as e:
            Logger.error(f"Failed to start location updates: {e}")
            self.handle_location_error(e)

    def handle_location_error(self, error: Exception):
        """Handle location service errors"""
        self.error_count += 1
        self.last_error = error
        
        Logger.error(f"Location service error ({self.error_count}): {error}")
        
        if self.error_count >= self.max_errors:
            Logger.error("Too many location errors, stopping tracking")
            self.stop_location_updates()
            return

        # Dispatch error event
        try:
            self.dispatch('on_location_error', error)
        except Exception as e:
            Logger.error(f"Error dispatching location error: {e}")

        # Fall back to simulation if GPS fails
        if HAS_GPS and not self.simulation_event:
            Logger.info("Falling back to simulated location due to GPS errors")
            self.start_simulated_location()

    def validate_location_data(self, location_data: dict) -> bool:
        """Validate location data"""
        try:
            if not isinstance(location_data, dict):
                return False

            required_fields = ['latitude', 'longitude']
            for field in required_fields:
                if field not in location_data:
                    Logger.warning(f"Missing required field: {field}")
                    return False

                value = location_data[field]
                if not isinstance(value, (int, float)):
                    Logger.warning(f"Invalid type for {field}: {type(value)}")
                    return False

            # Validate coordinate ranges
            lat = location_data['latitude']
            lon = location_data['longitude']

            if not (-90 <= lat <= 90):
                Logger.warning(f"Invalid latitude: {lat}")
                return False

            if not (-180 <= lon <= 180):
                Logger.warning(f"Invalid longitude: {lon}")
                return False

            return True

        except Exception as e:
            Logger.error(f"Location validation error: {e}")
            return False
      def start_location_updates(self):
        """Rozpocznij śledzenie lokalizacji z error handlingiem"""
        try:
            if self.is_tracking:
                Logger.info("Location tracking already active")
                return
            
            self.is_tracking = True
            Logger.info("Starting location tracking...")
            
            if HAS_GPS:
                try:
                    # Spróbuj użyć prawdziwego GPS
                    gps.configure(on_location=self._on_gps_location, on_status=self._on_gps_status)
                    gps.start(minTime=1000, minDistance=1)  # Aktualizacja co 1s lub 1m
                    Logger.info("GPS started successfully")
                except Exception as e:
                    Logger.error(f"Failed to start GPS: {e}")
                    self.handle_location_error(e)
                    self._start_location_simulation()
            else:
                Logger.info("GPS not available, using simulation")
                self._start_location_simulation()
                
        except Exception as e:
            Logger.error(f"Critical error starting location updates: {e}")
            self.handle_location_error(e)
            raise LocationServiceError(f"Failed to start location updates: {e}")
      def stop_location_updates(self):
        """Zatrzymaj śledzenie lokalizacji z error handlingiem"""
        try:
            if not self.is_tracking:
                Logger.info("Location tracking not active")
                return
            
            self.is_tracking = False
            Logger.info("Stopping location tracking...")
            
            if HAS_GPS:
                try:
                    gps.stop()
                    Logger.info("GPS stopped successfully")
                except Exception as e:
                    Logger.error(f"Error stopping GPS: {e}")
            
            if self.simulation_event:
                self.simulation_event.cancel()
                self.simulation_event = None
                Logger.info("Location simulation stopped")
                
        except Exception as e:
            Logger.error(f"Error stopping location updates: {e}")
            # Force stop tracking even if error occurred
            self.is_tracking = False
      def _start_location_simulation(self):
        """Uruchom symulację lokalizacji z error handlingiem"""
        try:
            Logger.info("Starting location simulation...")
            
            # Ustaw timestamp dla symulowanej lokalizacji
            self.simulated_location['timestamp'] = time.time()
            
            # Validate simulated location
            if not self.validate_location_data(self.simulated_location):
                Logger.error("Invalid simulated location data")
                raise LocationServiceError("Invalid simulated location data")
            
            # Ustaw jako ostatnią znaną lokalizację
            self.last_known_location = self.simulated_location.copy()
            
            # Powiadom listenery o początkowej lokalizacji
            self._notify_location_listeners(self.simulated_location)
            
            # Uruchom regularne aktualizacje symulacji (co 10 sekund)
            self.simulation_event = Clock.schedule_interval(self._update_simulated_location, 10)
            Logger.info("Location simulation started successfully")
            
        except Exception as e:
            Logger.error(f"Failed to start location simulation: {e}")
            self.handle_location_error(e)
      def _update_simulated_location(self, dt):
        """Aktualizuj symulowaną lokalizację (małe ruchy) z error handlingiem"""
        try:
            import random
            
            # Dodaj małe losowe ruchy (symulacja jazdy)
            lat_offset = random.uniform(-0.001, 0.001)  # ~100m
            lon_offset = random.uniform(-0.001, 0.001)
            
            new_location = {
                'latitude': 52.2297 + lat_offset,
                'longitude': 21.0122 + lon_offset,
                'accuracy': 10.0,
                'timestamp': time.time()
            }
            
            # Validate new location
            if not self.validate_location_data(new_location):
                Logger.warning("Invalid simulated location generated, using last known")
                return
            
            self.simulated_location.update(new_location)
            self.last_known_location = self.simulated_location.copy()
            self._notify_location_listeners(self.simulated_location)
            
        except Exception as e:
            Logger.error(f"Error updating simulated location: {e}")
            self.handle_location_error(e)
      def _on_gps_location(self, **kwargs):
        """Callback dla rzeczywistej lokalizacji GPS z error handlingiem"""
        try:
            location = {
                'latitude': kwargs.get('lat', 0.0),
                'longitude': kwargs.get('lon', 0.0),
                'accuracy': kwargs.get('accuracy', 0.0),
                'timestamp': kwargs.get('timestamp', time.time())
            }
            
            # Validate GPS location
            if not self.validate_location_data(location):
                Logger.warning("Invalid GPS location data received")
                return
            
            Logger.info(f"GPS location received: {location['latitude']}, {location['longitude']}")
            
            self.last_known_location = location
            self.error_count = 0  # Reset error count on successful location
            self._notify_location_listeners(location)
            
        except Exception as e:
            Logger.error(f"Error processing GPS location: {e}")
            self.handle_location_error(e)
      def _on_gps_status(self, stype, status):
        """Callback dla statusu GPS z error handlingiem"""
        try:
            Logger.info(f"GPS status: {stype} - {status}")
            
            # Handle different GPS status types
            if stype == 'provider-enabled':
                Logger.info("GPS provider enabled")
            elif stype == 'provider-disabled':
                Logger.warning("GPS provider disabled")
                self.handle_location_error(Exception("GPS provider disabled"))
            
        except Exception as e:
            Logger.error(f"Error processing GPS status: {e}")

    def _notify_location_listeners(self, location):
        """Powiadom wszystkich listenerów o nowej lokalizacji z error handlingiem"""
        try:
            # Dispatch event
            self.dispatch('on_location_update', location)
            
            # Notify all listeners
            failed_listeners = []
            for listener in self.location_listeners:
                try:
                    listener(location)
                except Exception as e:
                    Logger.error(f"Error in location listener: {e}")
                    failed_listeners.append(listener)
            
            # Remove failed listeners
            for failed_listener in failed_listeners:
                self.location_listeners.remove(failed_listener)
                Logger.warning("Removed failed location listener")
                
        except Exception as e:
            Logger.error(f"Error notifying location listeners: {e}")

    def add_location_listener(self, listener):
        """Dodaj listener lokalizacji z error handlingiem"""
        try:
            if not callable(listener):
                raise ValueError("Listener must be callable")
                
            if listener not in self.location_listeners:
                self.location_listeners.append(listener)
                Logger.info(f"Added location listener. Total: {len(self.location_listeners)}")
            else:
                Logger.warning("Location listener already exists")
                
        except Exception as e:
            Logger.error(f"Error adding location listener: {e}")

    def remove_location_listener(self, listener):
        """Usuń listener lokalizacji z error handlingiem"""
        try:
            if listener in self.location_listeners:
                self.location_listeners.remove(listener)
                Logger.info(f"Removed location listener. Remaining: {len(self.location_listeners)}")
            else:
                Logger.warning("Location listener not found")
                
        except Exception as e:
            Logger.error(f"Error removing location listener: {e}")

    def get_last_known_location(self):
        """Pobierz ostatnią znaną lokalizację z error handlingiem"""
        try:
            if self.last_known_location:
                # Validate before returning
                if self.validate_location_data(self.last_known_location):
                    return self.last_known_location.copy()
                else:
                    Logger.warning("Last known location is invalid")
                    return None
            return None
            
        except Exception as e:
            Logger.error(f"Error getting last known location: {e}")
            return None

    def get_current_location(self):
        """Pobierz aktualną lokalizację z error handlingiem"""
        try:
            # In a real implementation, this would be asynchronous
            current_location = self.get_last_known_location()
            
            if current_location:
                Logger.debug("Returning current location")
                return current_location
            else:
                Logger.warning("No current location available")
                return None
                
        except Exception as e:
            Logger.error(f"Error getting current location: {e}")
            return None

    def request_permissions(self):
        """Poproś o uprawnienia do lokalizacji z error handlingiem"""
        try:
            if HAS_GPS:
                # In Android/iOS this would request permissions
                Logger.info("Checking location permissions...")
                return True
            else:
                Logger.info("GPS not available - using simulation")
                return True
                
        except Exception as e:
            Logger.error(f"Error checking permissions: {e}")
            return False

    def start_simulated_location(self):
        """Start location simulation (fallback method)"""
        try:
            if not self.simulation_event:
                Logger.info("Starting fallback location simulation")
                self._start_location_simulation()
            else:
                Logger.info("Location simulation already running")
                
        except Exception as e:
            Logger.error(f"Error starting simulated location: {e}")
            self.handle_location_error(e)

    def get_location_status(self):
        """Get current location service status"""
        try:
            return {
                "is_tracking": self.is_tracking,
                "has_location": self.last_known_location is not None,
                "error_count": self.error_count,
                "last_error": str(self.last_error) if self.last_error else None,
                "using_simulation": self.simulation_event is not None,
                "listener_count": len(self.location_listeners)
            }
        except Exception as e:
            Logger.error(f"Error getting location status: {e}")
            return {"error": str(e)}

    def on_location_update(self, location):
        """Event handler dla aktualizacji lokalizacji"""
        pass  # Implementowane przez dziedziczące klasy

    def on_location_error(self, error):
        """Event handler dla błędów lokalizacji"""
        pass  # Implementowane przez dziedziczące klasy

    def cleanup(self):
        """Wyczyść zasoby z error handlingiem"""
        try:
            Logger.info("Cleaning up LocationService...")
            self.stop_location_updates()
            self.location_listeners.clear()
            self.last_known_location = None
            self.error_count = 0
            self.last_error = None
            Logger.info("LocationService cleanup completed")
            
        except Exception as e:
            Logger.error(f"Error during LocationService cleanup: {e}")
            # Force cleanup even if error occurred
            self.is_tracking = False
            self.location_listeners = []
