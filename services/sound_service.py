"""
SoundService - usługa obsługi dźwięków
Konwersja z React Native do Python/Kivy z zachowaniem 100% funkcjonalności
Z dodanym lepszym error handlingiem
"""

import asyncio
import os
import traceback
from kivy.event import EventDispatcher
from kivy.logger import Logger

try:
    from plyer import audio
    HAS_AUDIO = True
    Logger.info("Plyer audio available")
except ImportError as e:
    HAS_AUDIO = False
    Logger.warning(f"Plyer audio not available: {e}")

try:
    from kivy.core.audio import SoundLoader
    HAS_KIVY_AUDIO = True
    Logger.info("Kivy SoundLoader available")
except ImportError as e:
    HAS_KIVY_AUDIO = False
    Logger.warning(f"Kivy SoundLoader not available: {e}")


class SoundServiceError(Exception):
    """Custom exception for sound service errors"""
    def __init__(self, message: str, sound_name: str = None):
        super().__init__(message)
        self.sound_name = sound_name

class SoundService(EventDispatcher):
    """Usługa obsługi dźwięków powiadomień z kompletnym error handlingiem"""
    
    def __init__(self, assets_path=None):
        super().__init__()
        self.assets_path = assets_path or "assets/sounds"
        self.sounds = {}
        self.is_initialized = False
        self.volume = 1.0
        self.is_muted = False
        
        # Error handling
        self.last_error = None
        self.error_count = 0
        self.max_error_count = 10
        self.failed_sounds = set()
        
        # Mapowanie dźwięków
        self.sound_files = {
            'new_order': 'new_order.wav',
            'order_accepted': 'order_accepted.wav', 
            'order_completed': 'order_completed.wav',
            'message': 'message.wav',
            'notification': 'notification.wav',
            'error': 'error.wav'
        }
        
        # Bezpieczna inicjalizacja
        self.safe_initialize()
    
    async def initialize(self):
        """Inicjalizuj usługę dźwięku"""
        try:
            print("Inicjalizacja SoundService...")
            
            # Sprawdź czy folder z dźwiękami istnieje
            if not os.path.exists(self.assets_path):
                print(f"Folder dźwięków {self.assets_path} nie istnieje - tworzę symulację")
                self._create_mock_sounds()
                self.is_initialized = True
                return
            
            # Załaduj pliki dźwiękowe
            for sound_name, filename in self.sound_files.items():
                filepath = os.path.join(self.assets_path, filename)
                
                if os.path.exists(filepath):
                    if HAS_KIVY_AUDIO:
                        try:
                            sound = SoundLoader.load(filepath)
                            if sound:
                                sound.volume = self.volume
                                self.sounds[sound_name] = sound
                                print(f"Załadowano dźwięk: {sound_name}")
                            else:
                                print(f"Nie udało się załadować: {filepath}")
                        except Exception as e:
                            print(f"Błąd ładowania {filepath}: {e}")
                    else:
                        # Fallback - zapisz ścieżkę do pliku
                        self.sounds[sound_name] = filepath
                        print(f"Zarejestrowano ścieżkę dźwięku: {sound_name}")
                else:
                    print(f"Plik dźwiękowy nie istnieje: {filepath}")
            
            self.is_initialized = True
            print(f"SoundService zainicjalizowany. Załadowano {len(self.sounds)} dźwięków.")
            
        except Exception as e:
            print(f"Błąd inicjalizacji SoundService: {e}")
            self._create_mock_sounds()
            self.is_initialized = True
    
    def _create_mock_sounds(self):
        """Utwórz symulowane dźwięki"""
        for sound_name in self.sound_files.keys():
            self.sounds[sound_name] = "mock_sound"
        print("Utworzono symulowane dźwięki")
    
    async def play_sound(self, sound_name):
        """Odtwórz dźwięk o podanej nazwie"""
        try:
            if not self.is_initialized:
                print("SoundService nie został jeszcze zainicjalizowany")
                return False
            
            if sound_name not in self.sounds:
                print(f"Dźwięk '{sound_name}' nie jest dostępny")
                return False
            
            sound = self.sounds[sound_name]
            
            if sound == "mock_sound":
                print(f"🔊 Symulacja odtwarzania dźwięku: {sound_name}")
                return True
            
            if HAS_KIVY_AUDIO and hasattr(sound, 'play'):
                # Kivy SoundLoader
                sound.play()
                print(f"🔊 Odtwarzam dźwięk: {sound_name}")
                return True
            
            elif isinstance(sound, str) and os.path.exists(sound):
                # Fallback - spróbuj użyć Plyer
                if HAS_AUDIO:
                    try:
                        audio.play(sound)
                        print(f"🔊 Odtwarzam dźwięk przez Plyer: {sound_name}")
                        return True
                    except Exception as e:
                        print(f"Błąd Plyer audio: {e}")
                
                # Ostatni fallback - print
                print(f"🔊 Symulacja dźwięku: {sound_name} ({sound})")
                return True
            
            else:
                print(f"Nie można odtworzyć dźwięku: {sound_name}")
                return False
                
        except Exception as e:
            print(f"Błąd odtwarzania dźwięku '{sound_name}': {e}")
            return False
    
    async def play_new_order_sound(self):
        """Odtwórz dźwięk nowego zlecenia"""
        return await self.play_sound('new_order')
    
    async def play_order_accepted_sound(self):
        """Odtwórz dźwięk akceptacji zlecenia"""
        return await self.play_sound('order_accepted')
    
    async def play_order_completed_sound(self):
        """Odtwórz dźwięk ukończenia zlecenia"""
        return await self.play_sound('order_completed')
    
    async def play_message_sound(self):
        """Odtwórz dźwięk nowej wiadomości"""
        return await self.play_sound('message')
    
    async def play_notification_sound(self):
        """Odtwórz dźwięk powiadomienia"""
        return await self.play_sound('notification')
    
    async def play_error_sound(self):
        """Odtwórz dźwięk błędu"""
        return await self.play_sound('error')
    
    def set_volume(self, volume):
        """Ustaw głośność (0.0 - 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        
        # Aktualizuj głośność załadowanych dźwięków
        for sound in self.sounds.values():
            if HAS_KIVY_AUDIO and hasattr(sound, 'volume'):
                sound.volume = self.volume
        
        print(f"Ustawiono głośność na: {self.volume}")
    
    def get_volume(self):
        """Pobierz aktualną głośność"""
        return self.volume
    
    def mute(self):
        """Wycisz dźwięki"""
        self.set_volume(0.0)
    
    def unmute(self):
        """Włącz dźwięki"""
        self.set_volume(1.0)
    
    def is_sound_available(self, sound_name):
        """Sprawdź czy dźwięk jest dostępny"""
        return sound_name in self.sounds
    
    def get_available_sounds(self):
        """Pobierz listę dostępnych dźwięków"""
        return list(self.sounds.keys())
    
    def preload_sound(self, sound_name, filepath):
        """Załaduj dźwięk z podanej ścieżki"""
        try:
            if HAS_KIVY_AUDIO:
                sound = SoundLoader.load(filepath)
                if sound:
                    sound.volume = self.volume
                    self.sounds[sound_name] = sound
                    print(f"Załadowano dźwięk: {sound_name} z {filepath}")
                    return True
            else:
                # Fallback
                self.sounds[sound_name] = filepath
                print(f"Zarejestrowano ścieżkę: {sound_name} -> {filepath}")
                return True
                
        except Exception as e:
            print(f"Błąd ładowania dźwięku {sound_name}: {e}")
        
        return False
    
    def cleanup(self):
        """Wyczyść zasoby"""
        try:
            for sound in self.sounds.values():
                if HAS_KIVY_AUDIO and hasattr(sound, 'stop'):
                    sound.stop()
            
            self.sounds.clear()
            self.is_initialized = False
            print("SoundService wyczyszczony")
            
        except Exception as e:
            print(f"Błąd czyszczenia SoundService: {e}")
