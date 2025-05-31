"""
🔗 API Service - Dokładna konwersja z React Native
Zachowuje 100% kompatybilności z endpointami
Dodany lepszy error handling żeby się nie wykładała
"""

import aiohttp
import asyncio
import base64
import json
import keyring
import traceback
import time
from kivy.logger import Logger
from typing import Dict, Optional, Any


class APIConnectionError(Exception):
    """Custom exception for API connection errors"""
    pass


class APIAuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass


class APIService:
    """
    Serwis API - identyczna funkcjonalność jak apiService.js
    Z dodanym lepszym error handlingiem
    """
    
    def __init__(self):
        # Stan początkowy - dokładnie jak w React Native
        self.is_logged_in = False
        self.base_url = (
            'https://e6db2f06-15c4-4633-bd30-7fbd9c8200b1-00-'
            'l2xqyupphiyt.riker.replit.dev'
        )
        self.auth_header = None
        self.phone = None
        self.password = None
        self.driver_id = None
        self.last_endpoint = None
        
        # Error handling settings
        self.max_retries = 3
        self.retry_delay = 1.0
        self.timeout = 30
        self.last_error = None
        self.error_count = 0
        
        Logger.info(f'APIService initialized with baseUrl: {self.base_url}')
    
    def _handle_error(self, error: Exception, 
                     endpoint: str = "unknown") -> Dict[str, Any]:
        """Centralized error handling"""
        self.last_error = error
        self.error_count += 1
        
        error_msg = str(error)
        Logger.error(f'API Error at {endpoint}: {error_msg}')
        # Log stack trace for debugging
        Logger.debug(f'Stack trace: {traceback.format_exc()}')
        
        # Return consistent error format
        return {
            'success': False,
            'error': error_msg,
            'endpoint': endpoint,
            'timestamp': time.time()
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        retries: int = None
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling and retries"""
        
        if retries is None:
            retries = self.max_retries
        
        self.last_endpoint = endpoint
        url = f"{self.base_url}{endpoint}"
        
        # Prepare headers
        request_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.auth_header:
            request_headers['Authorization'] = self.auth_header
        
        if headers:
            request_headers.update(headers)
        
        for attempt in range(retries + 1):
            try:
                Logger.info(f'API Request: {method} {url} '
                           f'(attempt {attempt + 1})')
                
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.request(
                        method=method,
                        url=url,
                        json=data,
                        headers=request_headers
                    ) as response:
                        
                        # Log response details
                        Logger.info(f'API Response: {response.status} '
                                   f'from {endpoint}')
                        
                        try:
                            response_data = await response.json()
                        except json.JSONDecodeError:
                            response_text = await response.text()
                            Logger.error(f'Invalid JSON response: '
                                        f'{response_text}')
                            raise APIConnectionError(
                                f"Invalid JSON response from {endpoint}"
                            )
                        
                        if response.status >= 400:
                            error_msg = response_data.get(
                                'error', f'HTTP {response.status}'
                            )
                            
                            if response.status == 401:
                                raise APIAuthenticationError(
                                    f"Authentication failed: {error_msg}"
                                )
                            else:
                                raise APIConnectionError(
                                    f"API error {response.status}: "
                                    f"{error_msg}"
                                )
                        
                        return response_data
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                Logger.warning(f'Request failed (attempt {attempt + 1}): {e}')
                
                if attempt < retries:
                    # Exponential backoff
                    wait_time = self.retry_delay * (2 ** attempt)
                    Logger.info(f'Retrying in {wait_time} seconds...')
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise APIConnectionError(
                        f"Failed after {retries + 1} attempts: {str(e)}"
                    )
            
            except Exception as e:
                Logger.error(f'Unexpected error in request: {e}')
                raise APIConnectionError(f"Unexpected error: {str(e)}")
        
        # Should not reach here
        raise APIConnectionError("Request failed for unknown reason")

    # === MODERN HTTP METHODS ===
    async def get(self, endpoint: str, 
                 params: Optional[Dict] = None) -> Dict[str, Any]:
        """Modern GET request with error handling"""
        try:
            return await self._make_request('GET', endpoint, headers=params)
        except Exception as e:
            return self._handle_error(e, endpoint)

    async def post(self, endpoint: str, 
                  data: Optional[Dict] = None) -> Dict[str, Any]:
        """Modern POST request with error handling"""
        try:
            return await self._make_request('POST', endpoint, data=data)
        except Exception as e:
            return self._handle_error(e, endpoint)

    async def put(self, endpoint: str, 
                 data: Optional[Dict] = None) -> Dict[str, Any]:
        """Modern PUT request with error handling"""
        try:
            return await self._make_request('PUT', endpoint, data=data)
        except Exception as e:
            return self._handle_error(e, endpoint)

    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Modern DELETE request with error handling"""
        try:
            return await self._make_request('DELETE', endpoint)
        except Exception as e:
            return self._handle_error(e, endpoint)

    # === HEALTH CHECK ===
    async def check_api_status(self) -> bool:
        """Check if API is available"""
        try:
            await self._make_request('GET', '/api/health', retries=1)
            return True
        except Exception as e:
            Logger.warning(f'API health check failed: {e}')
            return False

    async def check_connection(self) -> Dict[str, Any]:
        """Check API connection status"""
        try:
            if await self.check_api_status():
                return {"success": True, "status": "connected"}
            else:
                return {"success": False, "status": "disconnected"}
        except Exception as e:
            return self._handle_error(e, "connection_check")
    
    async def load_saved_credentials(self) -> Optional[Dict[str, str]]:
        """Ładowanie zapisanych danych logowania - jak w React Native"""
        try:
            saved_phone = keyring.get_password("taxi_driver", "phone")
            saved_password = keyring.get_password("taxi_driver", "password")
            
            if saved_phone and saved_password:
                Logger.info('Znaleziono zapisane dane logowania, '
                           'inicjalizacja sesji...')
                self.initialize(saved_phone, saved_password)
                return {"phone": saved_phone, "password": saved_password}
            return None
        except Exception as error:
            Logger.error(f'Błąd podczas ładowania zapisanych danych '
                        f'logowania: {error}')
            return None
    
    async def auto_login(self) -> Dict[str, Any]:
        """Automatyczne logowanie przy użyciu zapisanych danych"""
        try:
            credentials = await self.load_saved_credentials()
            
            if credentials:
                Logger.info('Autologowanie z zapisanymi danymi...')
                return await self.login(
                    credentials["phone"], credentials["password"]
                )
            return {
                "success": False, 
                "message": "Brak zapisanych danych logowania"
            }
        except Exception as error:
            Logger.error(f'Błąd podczas autologowania: {error}')
            return {
                "success": False, 
                "message": f"Błąd podczas autologowania: {error}"
            }
    
    async def save_credentials(self, phone: str, password: str, 
                              base_url: str = None):
        """Zapisywanie danych logowania i adresu URL"""
        try:
            keyring.set_password("taxi_driver", "phone", phone)
            keyring.set_password("taxi_driver", "password", password)
            
            # Zapisz adres URL, jeśli podany
            url_to_save = base_url or self.base_url
            if url_to_save:
                keyring.set_password("taxi_driver", "api_url", url_to_save)
                Logger.info(f'Zapisano adres API: {url_to_save}')
            
            Logger.info('Dane logowania zostały zapisane')
        except Exception as error:
            Logger.error(f'Błąd podczas zapisywania danych logowania: '
                        f'{error}')
    
    async def load_saved_api_url(self) -> Optional[str]:
        """Wczytywanie zapisanego adresu URL"""
        try:
            saved_url = keyring.get_password("taxi_driver", "api_url")
            if saved_url:
                Logger.info(f'Wczytano zapisany adres API: {saved_url}')
                self.base_url = saved_url
                return saved_url
            return None
        except Exception as error:
            Logger.error(f'Błąd podczas wczytywania zapisanego adresu '
                        f'API: {error}')
            return None
    
    async def change_base_url(self, new_base_url: str) -> bool:
        """Zmiana bazowego adresu URL API"""
        try:
            if not new_base_url or new_base_url.strip() == '':
                raise ValueError('Nowy adres URL nie może być pusty')
            
            # Formatujemy URL
            formatted_url = new_base_url.strip()
            
            # Sprawdzamy czy URL kończy się na ukośniku
            if formatted_url.endswith('/'):
                formatted_url = formatted_url[:-1]
            
            # Sprawdzamy czy URL zawiera protokół
            if (not formatted_url.startswith('http://') and 
                not formatted_url.startswith('https://')):
                formatted_url = 'https://' + formatted_url
            
            Logger.info(f'Zmiana adresu bazowego API na: {formatted_url}')
            
            # Zapisujemy nowy URL
            keyring.set_password("taxi_driver", "api_url", formatted_url)
            
            # Aktualizujemy lokalny URL
            self.base_url = formatted_url
            
            return True
        except Exception as error:
            Logger.error(f'Błąd podczas zmiany adresu URL: {error}')
            raise error
    
    def initialize(self, phone: str, password: str, base_url: str = None):
        """Inicjalizacja API z danymi logowania - uproszczona wersja"""
        self.phone = phone
        self.password = password
        
        # Używamy podanego URL lub domyślnego
        self.base_url = base_url or (
            'https://e6db2f06-15c4-4633-bd30-7fbd9c8200b1-00-'
            'l2xqyupphiyt.riker.replit.dev'
        )
        
        # Tworzymy nagłówek autoryzacji
        credentials = f"{phone}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f'Basic {encoded_credentials}'
        
        Logger.info(f'API Service initialized with phone: {phone} '
                   f'and baseUrl: {self.base_url}')
    
    def get_base_url(self) -> str:
        """Pobieranie bazowego adresu URL API"""
        if not self.base_url:
            Logger.warning('baseUrl nie jest zdefiniowany, używam domyślnego')
            return (
                'https://e6db2f06-15c4-4633-bd30-7fbd9c8200b1-00-'
                'l2xqyupphiyt.riker.replit.dev'
            )
        
        # Usuwamy ewentualny końcowy slash
        if self.base_url.endswith('/'):
            return self.base_url[:-1]
        
        return self.base_url
    
    def reset(self):
        """Resetowanie stanu serwisu"""
        self.is_logged_in = False
        self.base_url = None
        self.auth_header = None
        self.phone = None
        self.password = None
        self.driver_id = None
        self.last_endpoint = None
    
    async def _fetch_with_logging(self, url: str, options: Dict) -> Dict:
        """Podstawowe zapytanie HTTP z obsługą błędów i logowaniem"""
        method = options.get('method', 'GET')
        Logger.info(f'API Request: {method} {url}')
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **options) as response:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'application/json' in content_type:
                        data = await response.json()
                        Logger.info(f'API Response (json): {data}')
                        return {"response": response, "data": data}
                    else:
                        text = await response.text()
                        Logger.info(f'API Response (text): {text}')
                        return {
                            "response": response,
                            "data": {"success": response.ok, "message": text}
                        }
        except Exception as error:
            Logger.error(f'API Error: {error}')
            raise error
    
    async def _auth_fetch(self, endpoint: str, 
                         options: Dict = None) -> Dict:
        """Podstawowe zapytanie z autoryzacją"""
        if options is None:
            options = {}
            
        try:
            if not self.is_logged_in:
                Logger.warning('Użytkownik nie jest zalogowany. '
                              'Próba użycia _auth_fetch bez logowania.')
                return {"success": False, "message": "Nie zalogowano"}
            
            if not self.base_url:
                Logger.warning('Brak baseUrl. Używam adresu awaryjnego.')
                self.base_url = (
                    'https://e6db2f06-15c4-4633-bd30-7fbd9c8200b1-00-'
                    'l2xqyupphiyt.riker.replit.dev'
                )
            
            # Pełny URL
            url = f"{self.base_url}{endpoint}"
            
            # Dodaj nagłówki autoryzacji
            headers = options.get('headers', {})
            headers['Authorization'] = self.auth_header
            headers['Content-Type'] = 'application/json'
            options['headers'] = headers
            
            # Konwertuj dane na JSON jeśli są
            if 'json' in options:
                options['data'] = json.dumps(options.pop('json'))
            
            result = await self._fetch_with_logging(url, options)
            return result.get('data', {})
            
        except Exception as error:
            Logger.error(f'Błąd w _auth_fetch: {error}')
            return {"success": False, "message": str(error)}
    
    # === LOGOWANIE ===
    async def login(self, phone: str, password: str, 
                   base_url: str = None) -> Dict[str, Any]:
        """
        Logowanie kierowcy - DOKŁADNIE jak w React Native
        Endpoint: /api/driver2/status/check
        """
        try:
            # Używamy podanego URL lub tego z serwisu
            login_base_url = base_url or self.base_url
            
            if not login_base_url:
                login_base_url = (
                    'https://e6db2f06-15c4-4633-bd30-7fbd9c8200b1-00-'
                    'l2xqyupphiyt.riker.replit.dev'
                )
            
            # Inicjalizujemy serwis z danymi logowania
            self.initialize(phone, password, login_base_url)
            
            # Endpoint dokładnie jak w React Native
            login_url = f"{login_base_url}/api/driver2/status/check"
            
            Logger.info(f'Próba logowania kierowcy: {phone} na {login_url}')
            
            # Zapytanie z autoryzacją Basic
            headers = {
                'Authorization': self.auth_header,
                'Content-Type': 'application/json'
            }
            
            result = await self._fetch_with_logging(login_url, {
                'method': 'GET',
                'headers': headers
            })
            
            response_data = result.get('data', {})
            
            if response_data.get('success'):
                # Udane logowanie
                self.is_logged_in = True
                self.driver_id = 15  # Stałe ID testowego kierowcy jak w RN
                
                # Zapisz dane logowania
                await self.save_credentials(phone, password, login_base_url)
                
                Logger.info(f'Pomyślnie zalogowano kierowcy: {phone}')
                
                return {
                    "success": True,
                    "message": "Logowanie pomyślne",
                    "data": {
                        "driver_id": self.driver_id,
                        "phone": phone,
                        "base_url": login_base_url
                    }
                }
            else:
                Logger.error(f'Błąd logowania: {response_data}')
                return {
                    "success": False,
                    "message": response_data.get('message', 'Błąd logowania')
                }
                
        except Exception as error:
            Logger.error(f'Wyjątek podczas logowania: {error}')
            return {
                "success": False,
                "message": f"Błąd połączenia: {error}"
            }
    
    async def logout(self) -> Dict[str, Any]:
        """Wylogowanie kierowcy"""
        try:
            if self.is_logged_in:
                await self._auth_fetch('/api/driver2/logout', 
                                     {'method': 'POST'})
            
            # Wyczyść dane logowania
            try:
                keyring.delete_password("taxi_driver", "phone")
                keyring.delete_password("taxi_driver", "password")
            except Exception:
                pass
            
            # Resetuj stan
            self.reset()
            
            Logger.info('Pomyślnie wylogowano')
            return {"success": True, "message": "Wylogowano pomyślnie"}
        except Exception as error:
            Logger.error(f'Logout error: {error}')
            return {"success": True, "message": "Wylogowano lokalnie"}
    
    # === PROFIL KIEROWCY ===
    async def get_driver_profile(self) -> Dict[str, Any]:
        """
        Pobieranie profilu kierowcy
        Endpoint: /api/driver2/profile
        """
        try:
            response = await self._auth_fetch('/api/driver2/profile')
            
            if response.get('success') and response.get('data'):
                return {"success": True, "data": response['data']}
            elif response.get('status') == "success" and response.get('data'):
                return {"success": True, "data": response['data']}
            elif response.get('driver'):
                return {"success": True, "data": response['driver']}
            else:
                Logger.info('Brak danych profilu, używam danych z logowania')
                # Fallback data jak w React Native
                return {
                    "success": True,
                    "data": {
                        "id": self.driver_id,
                        "phone": self.phone,
                        "name": f"Kierowca {self.phone}",
                        "status": 'online',
                        "email": '',
                        "vehicle_model": 'Nieznany',
                        "vehicle_plate": 'Nieznany',
                        "vehicle_type": 'Standardowy',
                        "license_number": 'Nieznany',
                        "license_expiry": 'Nieznany',
                        "total_orders": 0,
                        "average_rating": 0,
                        "experience_years": 0
                    }
                }
        except Exception as error:
            Logger.error(f'Błąd podczas pobierania profilu: {error}')
            return {"success": False, "message": str(error)}
    
    # Alias dla kompatybilności
    async def get_profile(self) -> Dict[str, Any]:
        return await self.get_driver_profile()
    
    # === PULA ZLECEŃ ===
    async def check_order_pool(self) -> Dict[str, Any]:
        """
        Sprawdzanie puli zleceń przypisanych do kierowcy
        Endpoint: /api/driver2/15/pool
        """
        try:
            Logger.info('Sprawdzanie puli zleceń dla testowego '
                       'kierowcy (ID: 15)...')
            
            response = await self._auth_fetch('/api/driver2/15/pool')
            
            Logger.info(f'Odpowiedź API dla puli zleceń: {response}')
            
            if (response.get('success') and 
                isinstance(response.get('data'), list)):
                Logger.info(f'Znaleziono {len(response["data"])} '
                           f'zleceń w puli kierowcy')
                return {"success": True, "data": response['data']}
            elif (response.get('status') == "success" and 
                  isinstance(response.get('orders'), list)):
                Logger.info(f'Znaleziono {len(response["orders"])} '
                           f'zleceń w puli kierowcy')
                return {"success": True, "data": response['orders']}
            elif response.get('success') and response.get('orders'):
                Logger.info('Format alternatywny - znaleziono zlecenia '
                           'w puli kierowcy')
                return {"success": True, "data": response['orders']}
            else:
                Logger.info('Brak zleceń w puli lub nieobsługiwany '
                           'format odpowiedzi')
                return {"success": True, "data": []}
        except Exception as error:
            Logger.error(f'Błąd podczas sprawdzania puli zleceń: {error}')
            return {"success": False, "message": str(error), "data": []}
    
    # === AKTUALNE ZLECENIA ===
    async def get_current_orders(self) -> Dict[str, Any]:
        """
        Pobieranie aktualnych zleceń kierowcy
        Endpoint: /api/driver2/orders/current
        """
        try:
            response = await self._auth_fetch('/api/driver2/orders/current')
            
            if (response.get('success') and 
                isinstance(response.get('data'), list)):
                return {"success": True, "data": response['data']}
            elif (response.get('status') == "success" and 
                  isinstance(response.get('orders'), list)):
                return {"success": True, "data": response['orders']}
            else:
                Logger.info('Brak aktualnych zleceń lub nieobsługiwany '
                           'format odpowiedzi')
                return {"success": True, "data": []}
        except Exception as error:
            Logger.error(f'Błąd podczas pobierania aktualnych zleceń: '
                        f'{error}')
            return {"success": False, "message": str(error), "data": []}
    
    # === AKCJE NA ZLECENIACH ===
    async def accept_order(self, order_id: int) -> Dict[str, Any]:
        """
        Akceptacja zlecenia
        Endpoint: /api/driver2/orders/{order_id}/accept
        """
        try:
            response = await self._auth_fetch(
                f'/api/driver2/orders/{order_id}/accept', 
                {'method': 'POST'}
            )
            
            if response.get('success'):
                Logger.info(f'Pomyślnie zaakceptowano zlecenie {order_id}')
                return {"success": True, "order_id": order_id}
            else:
                return {
                    "success": False, 
                    "message": response.get('message', 'Błąd akceptacji')
                }
        except Exception as error:
            Logger.error(f'Błąd akceptacji zlecenia {order_id}: {error}')
            return {"success": False, "message": str(error)}
    
    async def start_order(self, order_id: int) -> Dict[str, Any]:
        """
        Rozpoczęcie zlecenia
        Endpoint: /api/driver2/orders/{order_id}/start
        """
        try:
            response = await self._auth_fetch(
                f'/api/driver2/orders/{order_id}/start', 
                {'method': 'POST'}
            )
            
            if response.get('success'):
                return {"success": True}
            else:
                return {
                    "success": False, 
                    "message": response.get('message', 'Błąd rozpoczęcia')
                }
        except Exception as error:
            Logger.error(f'Błąd rozpoczęcia zlecenia {order_id}: {error}')
            return {"success": False, "message": str(error)}
    
    async def complete_order(self, order_id: int) -> Dict[str, Any]:
        """
        Zakończenie zlecenia
        Endpoint: /api/driver2/orders/{order_id}/complete
        """
        try:
            response = await self._auth_fetch(
                f'/api/driver2/orders/{order_id}/complete', 
                {'method': 'POST'}
            )
            
            if response.get('success'):
                return {"success": True}
            else:
                return {
                    "success": False, 
                    "message": response.get('message', 'Błąd zakończenia')
                }
        except Exception as error:
            Logger.error(f'Błąd zakończenia zlecenia {order_id}: {error}')
            return {"success": False, "message": str(error)}
    
    async def cancel_order(self, order_id: int, 
                          reason: str = "") -> Dict[str, Any]:
        """
        Anulowanie zlecenia
        Endpoint: /api/driver2/orders/{order_id}/cancel
        """
        try:
            response = await self._auth_fetch(
                f'/api/driver2/orders/{order_id}/cancel', 
                {
                    'method': 'POST',
                    'json': {"reason": reason}
                }
            )
            
            if response.get('success'):
                return {"success": True, "reason": reason}
            else:
                return {
                    "success": False, 
                    "message": response.get('message', 'Błąd anulowania')
                }
        except Exception as error:
            Logger.error(f'Błąd anulowania zlecenia {order_id}: {error}')
            return {"success": False, "message": str(error)}
    
    # === SZCZEGÓŁY ZLECENIA ===
    async def get_order_details(self, order_id: int) -> Dict[str, Any]:
        """
        Pobieranie szczegółów zlecenia
        Endpoint: /api/driver2/orders/{order_id}
        """
        try:
            response = await self._auth_fetch(
                f'/api/driver2/orders/{order_id}'
            )
            
            if response.get('success'):
                return {"success": True, "data": response.get('data')}
            else:
                return {"success": False, "message": "Zlecenie nie znalezione"}
        except Exception as error:
            Logger.error(f'Błąd pobierania szczegółów zlecenia '
                        f'{order_id}: {error}')
            return {"success": False, "message": str(error)}
    
    async def get_order_storage_details(self, order_id: int) -> Dict[str, Any]:
        """
        Pobieranie szczegółów zlecenia z magazynu
        Endpoint: /api/driver2/order_storage/{order_id}
        """
        try:
            response = await self._auth_fetch(
                f'/api/driver2/order_storage/{order_id}'
            )
            
            if response.get('success'):
                return {"success": True, "data": response.get('data')}
            else:
                # Fallback data jak w React Native
                order_details = {
                    "id": order_id,
                    "pickup_address": "ul. Magazynowa 1",
                    "destination_address": "ul. Docelowa 2",
                    "price": "30.00",
                    "distance": 7.5,
                    "estimated_time": 20,
                    "created_at": "2024-05-20T12:00:00Z",
                    "order_type": "VIP",
                    "pickup_latitude": 51.1,
                    "pickup_longitude": 22.2,
                    "destination_latitude": 51.2,
                    "destination_longitude": 22.3,
                    "notes": "Uwagi do zlecenia",
                    "payment_method": "card",
                    "customer_name": "Anna Nowak",
                    "customer_phone": "987654321"
                }
                return {"success": True, "data": order_details}
        except Exception as error:
            Logger.error(f'Błąd pobierania szczegółów zlecenia z magazynu '
                        f'{order_id}: {error}')
            return {"success": False, "message": str(error)}
    
    # === STATUS KIEROWCY ===
    async def update_driver_status(self, status: str) -> Dict[str, Any]:
        """
        Aktualizacja statusu kierowcy
        Endpoint: /api/driver2/status
        """
        try:
            response = await self._auth_fetch('/api/driver2/status', {
                'method': 'POST',
                'json': {"status": status}
            })
            
            if response.get('success'):
                return {"success": True}
            else:
                return {
                    "success": False, 
                    "message": response.get('message', 
                                         'Błąd aktualizacji statusu')
                }
        except Exception as error:
            Logger.error(f'Błąd aktualizacji statusu: {error}')
            return {"success": False, "message": str(error)}
    
    # === LOKALIZACJA ===
    async def update_location(self, latitude: float, 
                             longitude: float) -> Dict[str, Any]:
        """
        Aktualizacja lokalizacji kierowcy
        Endpoint: /api/driver2/location
        """
        try:
            response = await self._auth_fetch('/api/driver2/location', {
                'method': 'POST',
                'json': {
                    "latitude": latitude,
                    "longitude": longitude
                }
            })
            
            if response.get('success'):
                return {"success": True}
            else:                return {
                    "success": False, 
                    "message": response.get('message', 
                                         'Błąd aktualizacji lokalizacji')
                }
        except Exception as error:
            Logger.error(f'Błąd aktualizacji lokalizacji: {error}')
            return {"success": False, "message": str(error)}