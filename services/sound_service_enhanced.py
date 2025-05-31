"""
Enhanced SoundService - usługa obsługi dźwięków
Kompletny error handling i funkcjonalność
"""

import asyncio
import os
import time
import traceback
from typing import Dict, List, Optional, Any
from kivy.event import EventDispatcher
from kivy.logger import Logger

try:
    from plyer import audio
    HAS_PLYER_AUDIO = True
    Logger.info("Plyer audio available")
except ImportError as e:
    HAS_PLYER_AUDIO = False
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
        self.timestamp = time.time()


class SafeSoundService(EventDispatcher):
    """Enhanced SoundService with comprehensive error handling"""
    
    def __init__(self, assets_path: str = None):
        super().__init__()
        
        # Core settings
        self.assets_path = assets_path or "assets/sounds"
        self.sounds: Dict[str, Any] = {}
        self.is_initialized = False
        self.volume = 1.0
        self.is_muted = False
        
        # Error handling
        self.last_error: Optional[Exception] = None
        self.error_count = 0
        self.max_error_count = 10
        self.failed_sounds: set = set()
        self.initialization_attempts = 0
        self.max_init_attempts = 3
        
        # Performance tracking
        self.play_count = 0
        self.success_count = 0
        self.last_play_time = 0
        
        # Sound file mapping
        self.sound_files = {
            'new_order': 'new_order.wav',
            'order_accepted': 'order_accepted.wav',
            'order_completed': 'order_completed.wav',
            'message': 'message.wav',
            'notification': 'notification.wav',
            'error': 'error.wav',
            'startup': 'startup.wav',
            'shutdown': 'shutdown.wav'
        }
        
        Logger.info("SafeSoundService created, starting initialization...")
        self.safe_initialize()
    
    def safe_initialize(self) -> None:
        """Safe initialization wrapper"""
        try:
            asyncio.create_task(self.initialize())
        except Exception as error:
            self._handle_initialization_error(error)
    
    def _handle_initialization_error(self, error: Exception) -> None:
        """Handle initialization errors"""
        self.initialization_attempts += 1
        self.last_error = error
        self.error_count += 1
        
        Logger.error(f"SoundService init error (attempt {self.initialization_attempts}): {error}")
        
        if self.initialization_attempts < self.max_init_attempts:
            Logger.info("Retrying initialization with fallback...")
            self._create_mock_sounds()
            self.is_initialized = True
        else:
            Logger.error("Max initialization attempts reached, using silent mode")
            self._create_silent_mode()
    
    async def initialize(self) -> bool:
        """Initialize sound service with comprehensive error handling"""
        try:
            Logger.info("Initializing SafeSoundService...")
            
            # Validate assets path
            if not self._validate_assets_path():
                Logger.warning("Assets path invalid, creating mock sounds")
                self._create_mock_sounds()
                self.is_initialized = True
                return True
            
            # Load sound files
            loaded_count = await self._load_sound_files()
            
            self.is_initialized = True
            
            Logger.info(f"SoundService initialized successfully. "
                       f"Loaded {loaded_count}/{len(self.sound_files)} sounds")
            
            return True
            
        except Exception as error:
            self._handle_initialization_error(error)
            return False
    
    def _validate_assets_path(self) -> bool:
        """Validate assets path exists and is accessible"""
        try:
            if not self.assets_path:
                return False
                
            if not os.path.exists(self.assets_path):
                Logger.warning(f"Assets path does not exist: {self.assets_path}")
                return False
                
            if not os.path.isdir(self.assets_path):
                Logger.warning(f"Assets path is not a directory: {self.assets_path}")
                return False
                
            return True
            
        except Exception as error:
            Logger.error(f"Error validating assets path: {error}")
            return False
    
    async def _load_sound_files(self) -> int:
        """Load sound files with error handling"""
        loaded_count = 0
        
        for sound_name, filename in self.sound_files.items():
            try:
                if await self._load_single_sound(sound_name, filename):
                    loaded_count += 1
                else:
                    self.failed_sounds.add(sound_name)
                    
            except Exception as error:
                Logger.error(f"Error loading sound {sound_name}: {error}")
                self.failed_sounds.add(sound_name)
        
        # Create fallbacks for failed sounds
        for failed_sound in self.failed_sounds:
            self.sounds[failed_sound] = "mock_sound"
            Logger.info(f"Created mock fallback for: {failed_sound}")
        
        return loaded_count
    
    async def _load_single_sound(self, sound_name: str, filename: str) -> bool:
        """Load a single sound file"""
        try:
            filepath = os.path.join(self.assets_path, filename)
            
            if not os.path.exists(filepath):
                Logger.warning(f"Sound file does not exist: {filepath}")
                return False
            
            # Try Kivy SoundLoader first
            if HAS_KIVY_AUDIO:
                sound = await self._load_with_kivy(filepath)
                if sound:
                    self.sounds[sound_name] = sound
                    Logger.info(f"Loaded with Kivy: {sound_name}")
                    return True
            
            # Fallback to file path storage
            self.sounds[sound_name] = filepath
            Logger.info(f"Stored file path: {sound_name}")
            return True
            
        except Exception as error:
            Logger.error(f"Error loading {sound_name}: {error}")
            return False
    
    async def _load_with_kivy(self, filepath: str):
        """Load sound with Kivy SoundLoader"""
        try:
            sound = SoundLoader.load(filepath)
            if sound:
                sound.volume = self.volume
                return sound
            return None
            
        except Exception as error:
            Logger.error(f"Kivy SoundLoader error: {error}")
            return None
    
    def _create_mock_sounds(self) -> None:
        """Create mock sounds for testing"""
        for sound_name in self.sound_files.keys():
            self.sounds[sound_name] = "mock_sound"
        Logger.info("Created mock sounds for all sound types")
    
    def _create_silent_mode(self) -> None:
        """Create silent mode when all else fails"""
        for sound_name in self.sound_files.keys():
            self.sounds[sound_name] = "silent"
        self.is_initialized = True
        Logger.info("Initialized in silent mode")
    
    async def safe_play_sound(self, sound_name: str) -> bool:
        """Safe sound playing with comprehensive error handling"""
        try:
            # Validation
            if not self._validate_play_request(sound_name):
                return False
            
            # Check mute status
            if self.is_muted:
                Logger.debug(f"Sound muted: {sound_name}")
                return True
            
            # Track attempt
            self.play_count += 1
            self.last_play_time = time.time()
            
            # Play sound
            result = await self._execute_sound_play(sound_name)
            
            if result:
                self.success_count += 1
                Logger.debug(f"Successfully played: {sound_name}")
            else:
                Logger.warning(f"Failed to play: {sound_name}")
            
            return result
            
        except Exception as error:
            return self._handle_play_error(error, sound_name)
    
    def _validate_play_request(self, sound_name: str) -> bool:
        """Validate sound play request"""
        if not self.is_initialized:
            Logger.warning("SoundService not initialized")
            return False
        
        if not sound_name:
            Logger.warning("Empty sound name provided")
            return False
        
        if sound_name not in self.sounds:
            Logger.warning(f"Sound not available: {sound_name}")
            return False
        
        if self.error_count >= self.max_error_count:
            Logger.warning("Too many errors, sound disabled")
            return False
        
        return True
    
    async def _execute_sound_play(self, sound_name: str) -> bool:
        """Execute the actual sound playing"""
        try:
            sound = self.sounds[sound_name]
            
            # Handle different sound types
            if sound == "mock_sound":
                Logger.info(f"🔊 Mock sound: {sound_name}")
                return True
            
            if sound == "silent":
                Logger.debug(f"🔇 Silent mode: {sound_name}")
                return True
            
            # Try Kivy audio
            if HAS_KIVY_AUDIO and hasattr(sound, 'play'):
                sound.play()
                Logger.info(f"🔊 Kivy audio: {sound_name}")
                return True
            
            # Try Plyer audio
            if HAS_PLYER_AUDIO and isinstance(sound, str) and os.path.exists(sound):
                audio.play(sound)
                Logger.info(f"🔊 Plyer audio: {sound_name}")
                return True
            
            # Fallback to simulation
            Logger.info(f"🔊 Simulated: {sound_name}")
            return True
            
        except Exception as error:
            Logger.error(f"Sound execution error: {error}")
            return False
    
    def _handle_play_error(self, error: Exception, sound_name: str) -> bool:
        """Handle sound playing errors"""
        self.last_error = error
        self.error_count += 1
        
        Logger.error(f"Sound play error ({self.error_count}): {error}")
        
        # Add to failed sounds
        self.failed_sounds.add(sound_name)
        
        # Create fallback
        self.sounds[sound_name] = "mock_sound"
        
        return False
    
    # === PUBLIC API METHODS ===
    
    async def play_new_order_sound(self) -> bool:
        """Play new order notification sound"""
        return await self.safe_play_sound('new_order')
    
    async def play_order_accepted_sound(self) -> bool:
        """Play order accepted sound"""
        return await self.safe_play_sound('order_accepted')
    
    async def play_order_completed_sound(self) -> bool:
        """Play order completed sound"""
        return await self.safe_play_sound('order_completed')
    
    async def play_message_sound(self) -> bool:
        """Play message notification sound"""
        return await self.safe_play_sound('message')
    
    async def play_notification_sound(self) -> bool:
        """Play general notification sound"""
        return await self.safe_play_sound('notification')
    
    async def play_error_sound(self) -> bool:
        """Play error sound"""
        return await self.safe_play_sound('error')
    
    def set_volume(self, volume: float) -> bool:
        """Set volume with validation"""
        try:
            # Validate volume
            if not isinstance(volume, (int, float)):
                Logger.warning("Invalid volume type")
                return False
            
            volume = max(0.0, min(1.0, float(volume)))
            self.volume = volume
            
            # Update loaded sounds
            self._update_sounds_volume()
            
            Logger.info(f"Volume set to: {self.volume}")
            return True
            
        except Exception as error:
            Logger.error(f"Error setting volume: {error}")
            return False
    
    def _update_sounds_volume(self) -> None:
        """Update volume for all loaded sounds"""
        try:
            for sound in self.sounds.values():
                if HAS_KIVY_AUDIO and hasattr(sound, 'volume'):
                    sound.volume = self.volume
        except Exception as error:
            Logger.error(f"Error updating sound volumes: {error}")
    
    def mute(self) -> None:
        """Mute all sounds"""
        self.is_muted = True
        Logger.info("Sound muted")
    
    def unmute(self) -> None:
        """Unmute all sounds"""
        self.is_muted = False
        Logger.info("Sound unmuted")
    
    def toggle_mute(self) -> bool:
        """Toggle mute status"""
        if self.is_muted:
            self.unmute()
        else:
            self.mute()
        return self.is_muted
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            'is_initialized': self.is_initialized,
            'is_muted': self.is_muted,
            'volume': self.volume,
            'sounds_loaded': len(self.sounds),
            'failed_sounds': list(self.failed_sounds),
            'error_count': self.error_count,
            'play_count': self.play_count,
            'success_rate': (self.success_count / max(1, self.play_count)) * 100,
            'has_kivy_audio': HAS_KIVY_AUDIO,
            'has_plyer_audio': HAS_PLYER_AUDIO
        }
    
    def reset_error_count(self) -> None:
        """Reset error counter"""
        self.error_count = 0
        self.failed_sounds.clear()
        Logger.info("Error count reset")
    
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            # Stop all sounds
            for sound in self.sounds.values():
                if HAS_KIVY_AUDIO and hasattr(sound, 'stop'):
                    try:
                        sound.stop()
                    except Exception:
                        pass
            
            # Clear data
            self.sounds.clear()
            self.failed_sounds.clear()
            self.is_initialized = False
            
            Logger.info("SoundService cleaned up")
            
        except Exception as error:
            Logger.error(f"Cleanup error: {error}")


# Alias for backward compatibility
SoundService = SafeSoundService
