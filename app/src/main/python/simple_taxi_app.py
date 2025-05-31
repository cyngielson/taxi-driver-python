#!/usr/bin/env python3
"""
Simple Taxi Driver App - Core Functionality
Compatible with Chaquopy for Android compilation
"""

import requests
import json
import time
from typing import Dict, List, Optional

class TaxiDriverAPI:
    """Simple API service for taxi driver operations"""
    
    def __init__(self, base_url: str = "http://your-server.com/api"):
        self.base_url = base_url
        self.session = requests.Session()
        self.driver_id = None
        self.auth_token = None
    
    def login(self, username: str, password: str) -> bool:
        """Login driver and get auth token"""
        try:
            response = self.session.post(f"{self.base_url}/driver/login", {
                "username": username,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                self.driver_id = data.get("driver_id")
                return True
            return False
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def get_orders(self) -> List[Dict]:
        """Get available orders"""
        if not self.auth_token:
            return []
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(f"{self.base_url}/driver/orders", headers=headers)
            
            if response.status_code == 200:
                return response.json().get("orders", [])
            return []
        except Exception as e:
            print(f"Get orders error: {e}")
            return []
    
    def accept_order(self, order_id: str) -> bool:
        """Accept an order"""
        if not self.auth_token:
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.post(
                f"{self.base_url}/driver/orders/{order_id}/accept",
                headers=headers
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Accept order error: {e}")
            return False
    
    def update_location(self, latitude: float, longitude: float) -> bool:
        """Update driver location"""
        if not self.auth_token:
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.post(
                f"{self.base_url}/driver/location",
                json={"latitude": latitude, "longitude": longitude},
                headers=headers
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Update location error: {e}")
            return False

class TaxiDriverApp:
    """Main taxi driver application"""
    
    def __init__(self):
        self.api = TaxiDriverAPI()
        self.running = False
        self.current_order = None
    
    def start(self):
        """Start the application"""
        print("🚕 Taxi Driver App Started")
        print("=" * 40)
        
        # Demo login
        username = "demo_driver"
        password = "demo123"
        
        print(f"Logging in as: {username}")
        if self.api.login(username, password):
            print("✅ Login successful!")
            self.running = True
            self.main_loop()
        else:
            print("❌ Login failed!")
    
    def main_loop(self):
        """Main application loop"""
        while self.running:
            self.show_menu()
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == "1":
                self.check_orders()
            elif choice == "2":
                self.update_location_manual()
            elif choice == "3":
                self.show_current_order()
            elif choice == "4":
                self.show_stats()
            elif choice == "5":
                self.stop()
            else:
                print("Invalid choice. Please try again.")
            
            time.sleep(1)
    
    def show_menu(self):
        """Display main menu"""
        print("\n" + "=" * 40)
        print("🚕 TAXI DRIVER DASHBOARD")
        print("=" * 40)
        print("1. 📋 Check Available Orders")
        print("2. 📍 Update Location")
        print("3. 🎯 Current Order Status")
        print("4. 📊 Statistics")
        print("5. 🚪 Exit")
        print("-" * 40)
    
    def check_orders(self):
        """Check and display available orders"""
        print("\n📋 Checking available orders...")
        orders = self.api.get_orders()
        
        if not orders:
            print("No orders available at the moment.")
            return
        
        print(f"Found {len(orders)} available orders:")
        print("-" * 40)
        
        for i, order in enumerate(orders, 1):
            print(f"{i}. Order #{order.get('id', 'N/A')}")
            print(f"   From: {order.get('pickup', 'Unknown')}")
            print(f"   To: {order.get('destination', 'Unknown')}")
            print(f"   Price: ${order.get('price', '0.00')}")
            print(f"   Distance: {order.get('distance', '0')} km")
            print("-" * 40)
        
        # Ask to accept order
        try:
            choice = input("Enter order number to accept (or 0 to cancel): ")
            order_num = int(choice)
            
            if 1 <= order_num <= len(orders):
                order = orders[order_num - 1]
                if self.api.accept_order(order['id']):
                    print(f"✅ Order #{order['id']} accepted!")
                    self.current_order = order
                else:
                    print("❌ Failed to accept order.")
            elif order_num != 0:
                print("Invalid order number.")
        except ValueError:
            print("Invalid input.")
    
    def update_location_manual(self):
        """Manual location update"""
        print("\n📍 Update Location")
        try:
            lat = float(input("Enter latitude: "))
            lng = float(input("Enter longitude: "))
            
            if self.api.update_location(lat, lng):
                print("✅ Location updated successfully!")
            else:
                print("❌ Failed to update location.")
        except ValueError:
            print("Invalid coordinates.")
    
    def show_current_order(self):
        """Show current order status"""
        print("\n🎯 Current Order Status")
        print("-" * 40)
        
        if self.current_order:
            order = self.current_order
            print(f"Order ID: #{order.get('id', 'N/A')}")
            print(f"From: {order.get('pickup', 'Unknown')}")
            print(f"To: {order.get('destination', 'Unknown')}")
            print(f"Price: ${order.get('price', '0.00')}")
            print(f"Status: In Progress")
        else:
            print("No active order.")
    
    def show_stats(self):
        """Show driver statistics"""
        print("\n📊 Driver Statistics")
        print("-" * 40)
        print("Today's Stats:")
        print(f"• Orders completed: 5")
        print(f"• Earnings: $127.50")
        print(f"• Distance driven: 89 km")
        print(f"• Hours online: 6.5h")
        print(f"• Rating: 4.8 ⭐")
    
    def stop(self):
        """Stop the application"""
        self.running = False
        print("\n👋 Goodbye! Drive safely!")

# Main entry point for Android
def main():
    """Main entry point"""
    app = TaxiDriverApp()
    app.start()

if __name__ == "__main__":
    main()
