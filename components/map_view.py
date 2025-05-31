"""
Map View Component for Taxi Driver App
Handles GPS tracking, location display, and order visualization on map
"""

from kivy.clock import Clock
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivy.metrics import dp
from kivy.logger import Logger

try:
    from kivy_garden.mapview import MapView, MapMarker
    MAP_AVAILABLE = True
except ImportError:
    Logger.warning("MapView: kivy-garden.mapview not available, using fallback")
    MAP_AVAILABLE = False
    MapView = None
    MapMarker = None


class TaxiMapMarker(MapMarker if MAP_AVAILABLE else object):
    """Custom marker for taxi locations and orders"""
    
    def __init__(self, marker_type="driver", order_data=None, **kwargs):
        if not MAP_AVAILABLE:
            super().__init__(**kwargs)
            return
            
        super().__init__(**kwargs)
        self.marker_type = marker_type  # "driver", "pickup", "destination", "order"
        self.order_data = order_data
        
        # Set marker appearance based on type
        if marker_type == "driver":
            self.source = "data/images/car_marker.png" if self._image_exists("data/images/car_marker.png") else None
        elif marker_type == "pickup":
            self.source = "data/images/pickup_marker.png" if self._image_exists("data/images/pickup_marker.png") else None
        elif marker_type == "destination":
            self.source = "data/images/destination_marker.png" if self._image_exists("data/images/destination_marker.png") else None
        elif marker_type == "order":
            self.source = "data/images/order_marker.png" if self._image_exists("data/images/order_marker.png") else None
    
    def _image_exists(self, path):
        try:
            import os
            return os.path.exists(path)
        except:
            return False


class MapViewComponent(MDBoxLayout if not MAP_AVAILABLE else MDBoxLayout):
    """Map view component with fallback when MapView is not available"""
    
    def __init__(self, location_service, api_service, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.location_service = location_service
        self.api_service = api_service
        
        self.current_location = None
        self.driver_marker = None
        self.order_markers = []
        self.active_order_markers = []
        
        if MAP_AVAILABLE:
            self._create_map_view()
        else:
            self._create_fallback_view()
        
        self._create_controls()
        self._bind_location_updates()
    
    def _create_map_view(self):
        """Create the actual map view"""
        self.map_view = MapView(
            zoom=15,
            lat=41.311081,  # Default location (Tashkent)
            lon=69.240562,
            map_source="osm"
        )
        self.add_widget(self.map_view)
    
    def _create_fallback_view(self):
        """Create fallback view when MapView is not available"""
        fallback_card = MDCard(
            size_hint=(1, 0.8),
            md_bg_color=(0.9, 0.9, 0.9, 1),
            elevation=2,
            padding=dp(20),
            spacing=dp(10)
        )
        
        fallback_layout = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            spacing=dp(10)
        )
        
        title = MDLabel(
            text="Map View (Demo Mode)",
            theme_text_color="Primary",
            font_style="H6",
            halign="center",
            size_hint_y=None,
            height=dp(40)
        )
        
        self.location_label = MDLabel(
            text="Location: Getting GPS...",
            theme_text_color="Secondary",
            halign="center",
            size_hint_y=None,
            height=dp(30)
        )
        
        self.orders_label = MDLabel(
            text="Orders: Checking for nearby orders...",
            theme_text_color="Secondary",
            halign="center",
            size_hint_y=None,
            height=dp(30)
        )
        
        fallback_layout.add_widget(title)
        fallback_layout.add_widget(self.location_label)
        fallback_layout.add_widget(self.orders_label)
        
        fallback_card.add_widget(fallback_layout)
        self.add_widget(fallback_card)
    
    def _create_controls(self):
        """Create map control buttons"""
        controls_layout = MDBoxLayout(
            size_hint=(1, None),
            height=dp(60),
            spacing=dp(10),
            adaptive_width=True,
            pos_hint={"center_x": 0.5}
        )
        
        # Center on location button
        self.center_button = MDIconButton(
            icon="crosshairs-gps",
            theme_icon_color="Custom",
            icon_color=(0, 0.6, 1, 1),
            on_release=self.center_on_location
        )
        
        # Refresh orders button
        self.refresh_button = MDIconButton(
            icon="refresh",
            theme_icon_color="Custom",
            icon_color=(0.2, 0.7, 0.2, 1),
            on_release=self.refresh_orders
        )
        
        # Toggle driver status button
        self.status_button = MDRaisedButton(
            text="Go Online",
            md_bg_color=(0.2, 0.7, 0.2, 1),
            on_release=self.toggle_driver_status
        )
        
        controls_layout.add_widget(self.center_button)
        controls_layout.add_widget(self.refresh_button)
        controls_layout.add_widget(self.status_button)
        
        self.add_widget(controls_layout)
    
    def _bind_location_updates(self):
        """Bind to location service updates"""
        if self.location_service:
            self.location_service.bind_location_listener(self.on_location_update)
    
    def on_location_update(self, location):
        """Handle location updates"""
        self.current_location = location
        
        if MAP_AVAILABLE and hasattr(self, 'map_view'):
            # Update map center
            self.map_view.center_on(location['lat'], location['lon'])
            
            # Update driver marker
            if self.driver_marker:
                self.map_view.remove_marker(self.driver_marker)
            
            self.driver_marker = TaxiMapMarker(
                lat=location['lat'],
                lon=location['lon'],
                marker_type="driver"
            )
            self.map_view.add_marker(self.driver_marker)
        else:
            # Update fallback view
            if hasattr(self, 'location_label'):
                self.location_label.text = f"Location: {location['lat']:.6f}, {location['lon']:.6f}"
        
        # Send location to server if online
        self._send_location_update(location)
    
    def _send_location_update(self, location):
        """Send location update to server"""
        try:
            if self.api_service and hasattr(self.api_service, 'driver_status') and self.api_service.driver_status.get('is_online'):
                self.api_service.update_location(
                    latitude=location['lat'],
                    longitude=location['lon']
                )
        except Exception as e:
            Logger.error(f"MapView: Failed to send location update: {e}")
    
    def center_on_location(self, *args):
        """Center map on current location"""
        if self.current_location:
            if MAP_AVAILABLE and hasattr(self, 'map_view'):
                self.map_view.center_on(
                    self.current_location['lat'],
                    self.current_location['lon']
                )
        else:
            self.location_service.get_current_location()
    
    def refresh_orders(self, *args):
        """Refresh nearby orders"""
        try:
            # Clear existing order markers
            if MAP_AVAILABLE and hasattr(self, 'map_view'):
                for marker in self.order_markers:
                    self.map_view.remove_marker(marker)
            self.order_markers.clear()
            
            # Get orders from pool
            if self.api_service:
                orders = self.api_service.check_pool()
                self.display_orders(orders)
                
                if not MAP_AVAILABLE and hasattr(self, 'orders_label'):
                    self.orders_label.text = f"Orders: {len(orders)} nearby orders found"
        except Exception as e:
            Logger.error(f"MapView: Failed to refresh orders: {e}")
    
    def display_orders(self, orders):
        """Display orders on map"""
        if not MAP_AVAILABLE:
            return
            
        if not hasattr(self, 'map_view'):
            return
        
        for order in orders:
            try:
                pickup_lat = float(order.get('pickup_latitude', 0))
                pickup_lon = float(order.get('pickup_longitude', 0))
                dest_lat = float(order.get('destination_latitude', 0))
                dest_lon = float(order.get('destination_longitude', 0))
                
                if pickup_lat and pickup_lon:
                    pickup_marker = TaxiMapMarker(
                        lat=pickup_lat,
                        lon=pickup_lon,
                        marker_type="pickup",
                        order_data=order
                    )
                    self.map_view.add_marker(pickup_marker)
                    self.order_markers.append(pickup_marker)
                
                if dest_lat and dest_lon:
                    dest_marker = TaxiMapMarker(
                        lat=dest_lat,
                        lon=dest_lon,
                        marker_type="destination",
                        order_data=order
                    )
                    self.map_view.add_marker(dest_marker)
                    self.order_markers.append(dest_marker)
            except (ValueError, TypeError) as e:
                Logger.warning(f"MapView: Invalid coordinates in order: {e}")
    
    def display_active_order(self, order):
        """Display active order route on map"""
        # Clear previous active order markers
        if MAP_AVAILABLE and hasattr(self, 'map_view'):
            for marker in self.active_order_markers:
                self.map_view.remove_marker(marker)
        self.active_order_markers.clear()
        
        if not order:
            return
        
        if not MAP_AVAILABLE:
            if hasattr(self, 'orders_label'):
                self.orders_label.text = f"Active Order: {order.get('pickup_address', 'Unknown')} → {order.get('destination_address', 'Unknown')}"
            return
        
        if not hasattr(self, 'map_view'):
            return
        
        try:
            pickup_lat = float(order.get('pickup_latitude', 0))
            pickup_lon = float(order.get('pickup_longitude', 0))
            dest_lat = float(order.get('destination_latitude', 0))
            dest_lon = float(order.get('destination_longitude', 0))
            
            if pickup_lat and pickup_lon:
                pickup_marker = TaxiMapMarker(
                    lat=pickup_lat,
                    lon=pickup_lon,
                    marker_type="pickup",
                    order_data=order
                )
                self.map_view.add_marker(pickup_marker)
                self.active_order_markers.append(pickup_marker)
            
            if dest_lat and dest_lon:
                dest_marker = TaxiMapMarker(
                    lat=dest_lat,
                    lon=dest_lon,
                    marker_type="destination",
                    order_data=order
                )
                self.map_view.add_marker(dest_marker)
                self.active_order_markers.append(dest_marker)
            
            # Center map to show both points
            if pickup_lat and pickup_lon and dest_lat and dest_lon:
                center_lat = (pickup_lat + dest_lat) / 2
                center_lon = (pickup_lon + dest_lon) / 2
                self.map_view.center_on(center_lat, center_lon)
        except (ValueError, TypeError) as e:
            Logger.warning(f"MapView: Invalid coordinates in active order: {e}")
    
    def toggle_driver_status(self, *args):
        """Toggle driver online/offline status"""
        try:
            if self.api_service:
                current_status = self.api_service.driver_status.get('is_online', False)
                new_status = not current_status
                
                # Update status on server
                self.api_service.update_driver_status(is_online=new_status)
                
                # Update button text
                if new_status:
                    self.status_button.text = "Go Offline"
                    self.status_button.md_bg_color = (0.8, 0.2, 0.2, 1)
                    if self.location_service:
                        self.location_service.start_tracking()
                else:
                    self.status_button.text = "Go Online"
                    self.status_button.md_bg_color = (0.2, 0.7, 0.2, 1)
                    if self.location_service:
                        self.location_service.stop_tracking()
        except Exception as e:
            Logger.error(f"MapView: Failed to toggle driver status: {e}")
    
    def update_driver_status(self, status):
        """Update driver status from external source"""
        is_online = status.get('is_online', False)
        if is_online:
            self.status_button.text = "Go Offline"
            self.status_button.md_bg_color = (0.8, 0.2, 0.2, 1)
        else:
            self.status_button.text = "Go Online"
            self.status_button.md_bg_color = (0.2, 0.7, 0.2, 1)
