"""
MessagesScreen - ekran wiadomości
Konwersja z React Native do Python/Kivy z zachowaniem 100% funkcjonalności API
"""

import asyncio
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.refreshlayout import MDSwipeToRefresh
from kivymd.toast import toast
from kivy.clock import Clock
import json
from datetime import datetime

class MessageCard(MDCard):
    """Karta pojedynczej wiadomości"""
    
    def __init__(self, message_data, mark_read_callback, reply_callback, **kwargs):
        super().__init__(**kwargs)
        self.message_data = message_data
        self.mark_read_callback = mark_read_callback
        self.reply_callback = reply_callback
        
        self.size_hint_y = None
        self.height = "120dp"
        self.elevation = 2
        self.padding = "10dp"
        
        # Sprawdź czy wiadomość jest przeczytana
        is_read = message_data.get('is_read', False)
        
        # Różne kolory dla przeczytanych/nieprzeczytanych
        if not is_read:
            self.md_bg_color = [0.95, 0.95, 1.0, 1.0]  # Jasny niebieski dla nieprzeczytanych
        
        # Layout główny karty
        card_layout = MDBoxLayout(
            orientation='vertical',
            spacing="5dp"
        )
        
        # Header z nadawcą i datą
        header_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height="25dp"
        )
        
        sender_label = MDLabel(
            text=f"Od: {message_data.get('sender', 'System')}",
            theme_text_color="Primary",
            font_style="Subtitle2",
            size_hint_x=0.7
        )
        
        status_icon = "📧" if not is_read else "📖"
        status_label = MDLabel(
            text=status_icon,
            size_hint_x=0.1,
            halign="center"
        )
        
        date_label = MDLabel(
            text=self.format_date(message_data.get('created_at', '')),
            theme_text_color="Secondary",
            font_style="Caption",
            size_hint_x=0.2,
            halign="right"
        )
        
        header_layout.add_widget(sender_label)
        header_layout.add_widget(status_label)
        header_layout.add_widget(date_label)
        card_layout.add_widget(header_layout)
        
        # Temat wiadomości (jeśli dostępny)
        subject = message_data.get('subject')
        if subject:
            subject_label = MDLabel(
                text=f"Temat: {subject}",
                theme_text_color="Primary",
                font_style="Body2",
                size_hint_y=None,
                height="20dp"
            )
            card_layout.add_widget(subject_label)
        
        # Treść wiadomości
        content = message_data.get('content', message_data.get('message', 'Brak treści'))
        content_label = MDLabel(
            text=content[:100] + "..." if len(content) > 100 else content,
            theme_text_color="Secondary",
            font_style="Body2",
            text_size=(None, None)
        )
        card_layout.add_widget(content_label)
        
        # Przyciski akcji
        buttons_layout = MDBoxLayout(
            orientation='horizontal',
            spacing="5dp",
            size_hint_y=None,
            height="35dp"
        )
        
        if not is_read:
            read_button = MDFlatButton(
                text="Oznacz jako przeczytane",
                size_hint_x=0.6,
                on_release=lambda x: self.mark_as_read()
            )
            buttons_layout.add_widget(read_button)
        
        reply_button = MDFlatButton(
            text="Odpowiedz",
            size_hint_x=0.4,
            on_release=lambda x: self.reply_to_message()
        )
        buttons_layout.add_widget(reply_button)
        
        card_layout.add_widget(buttons_layout)
        self.add_widget(card_layout)
    
    def format_date(self, date_string):
        """Formatuj datę dla wyświetlenia"""
        if not date_string:
            return ""
        try:
            if 'T' in date_string:
                dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d.%m %H:%M')
        except:
            return date_string
    
    def mark_as_read(self):
        """Oznacz wiadomość jako przeczytaną"""
        if self.mark_read_callback:
            self.mark_read_callback(self.message_data)
    
    def reply_to_message(self):
        """Odpowiedz na wiadomość"""
        if self.reply_callback:
            self.reply_callback(self.message_data)

class MessagesScreen(Screen):
    """Ekran wiadomości"""
    
    def __init__(self, api_service, **kwargs):
        super().__init__(**kwargs)
        self.api_service = api_service
        self.messages = []
        self.is_loading = False
        
        # Layout główny
        main_layout = BoxLayout(orientation='vertical')
        
        # Toolbar
        self.toolbar = MDTopAppBar(
            title="Moje wiadomości",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[
                ["refresh", lambda x: self.refresh_messages()],
                ["plus", lambda x: self.compose_message()]
            ]
        )
        main_layout.add_widget(self.toolbar)
        
        # SwipeToRefresh wrapper
        self.refresh_layout = MDSwipeToRefresh(
            on_refresh=self.on_refresh
        )
        
        # ScrollView dla listy wiadomości
        scroll = ScrollView()
        
        # Layout dla wiadomości
        self.messages_layout = MDBoxLayout(
            orientation='vertical',
            adaptive_height=True,
            spacing="10dp",
            padding="10dp"
        )
        
        # Placeholder
        self.empty_label = MDLabel(
            text="Ładowanie wiadomości...",
            halign="center",
            size_hint_y=None,
            height="50dp"
        )
        self.messages_layout.add_widget(self.empty_label)
        
        scroll.add_widget(self.messages_layout)
        self.refresh_layout.add_widget(scroll)
        main_layout.add_widget(self.refresh_layout)
        
        self.add_widget(main_layout)
        
        # Załaduj wiadomości po utworzeniu ekranu
        Clock.schedule_once(lambda dt: asyncio.create_task(self.load_messages()), 0.1)
        
        # Automatyczne odświeżanie co 60 sekund
        self.refresh_event = Clock.schedule_interval(
            lambda dt: asyncio.create_task(self.load_messages(silent=True)), 
            60
        )
    
    def on_refresh(self, *args):
        """Obsługa swipe to refresh"""
        asyncio.create_task(self.refresh_complete())
    
    async def refresh_complete(self):
        """Zakończ odświeżanie"""
        await self.load_messages()
        self.refresh_layout.refresh_done()
    
    async def load_messages(self, silent=False):
        """Załaduj wiadomości"""
        try:
            if not silent:
                self.is_loading = True
                self.update_empty_state("Ładowanie wiadomości...")
            
            print("Ładowanie wiadomości...")
            response = await self.api_service.get_messages()
            
            if response.get('success'):
                new_messages = response.get('data', [])
                print(f"Załadowano {len(new_messages)} wiadomości")
                
                # Sprawdź czy są nowe wiadomości
                if len(new_messages) > len(self.messages) and not silent:
                    unread_count = sum(1 for msg in new_messages if not msg.get('is_read', False))
                    if unread_count > 0:
                        toast(f"Masz {unread_count} nieprzeczytanych wiadomości")
                
                self.messages = new_messages
                self.build_messages_list()
            else:
                self.show_error("Nie udało się załadować wiadomości")
                
        except Exception as error:
            print(f"Błąd podczas ładowania wiadomości: {error}")
            if not silent:
                self.show_error(f"Błąd: {error}")
        finally:
            self.is_loading = False
    
    def build_messages_list(self):
        """Zbuduj listę wiadomości"""
        # Usuń stare elementy
        self.messages_layout.clear_widgets()
        
        if not self.messages:
            self.update_empty_state("📭 Brak wiadomości")
            return
        
        # Posortuj wiadomości po dacie (najnowsze na górze)
        sorted_messages = sorted(
            self.messages, 
            key=lambda x: x.get('created_at', ''), 
            reverse=True
        )
        
        # Dodaj karty wiadomości
        unread_count = 0
        for message in sorted_messages:
            if not message.get('is_read', False):
                unread_count += 1
                
            message_card = MessageCard(
                message_data=message,
                mark_read_callback=self.mark_message_as_read,
                reply_callback=self.reply_to_message
            )
            self.messages_layout.add_widget(message_card)
        
        # Dodaj podsumowanie
        summary_text = f"Łącznie: {len(self.messages)} wiadomości"
        if unread_count > 0:
            summary_text += f" | Nieprzeczytane: {unread_count}"
        
        summary_label = MDLabel(
            text=summary_text,
            halign="center",
            theme_text_color="Hint",
            size_hint_y=None,
            height="30dp"
        )
        self.messages_layout.add_widget(summary_label)
    
    def update_empty_state(self, message):
        """Aktualizuj stan pustej listy"""
        self.messages_layout.clear_widgets()
        self.empty_label.text = message
        self.messages_layout.add_widget(self.empty_label)
    
    def show_error(self, message):
        """Pokaż błąd"""
        self.messages_layout.clear_widgets()
        
        error_label = MDLabel(
            text=f"❌ {message}",
            halign="center",
            theme_text_color="Error"
        )
        
        retry_button = MDRaisedButton(
            text="Spróbuj ponownie",
            size_hint=(None, None),
            size=("200dp", "40dp"),
            pos_hint={'center_x': 0.5},
            on_release=lambda x: asyncio.create_task(self.load_messages())
        )
        
        self.messages_layout.add_widget(error_label)
        self.messages_layout.add_widget(retry_button)
    
    def mark_message_as_read(self, message_data):
        """Oznacz wiadomość jako przeczytaną"""
        message_id = message_data.get('id')
        if not message_id:
            return
        
        print(f"Oznaczam wiadomość {message_id} jako przeczytaną")
        asyncio.create_task(self._mark_read_async(message_id))
    
    async def _mark_read_async(self, message_id):
        """Asynchronicznie oznacz jako przeczytaną"""
        try:
            response = await self.api_service.update_message_status(message_id, True)
            
            if response.get('success'):
                toast("Oznaczono jako przeczytane")
                # Odśwież listę wiadomości
                await self.load_messages()
            else:
                toast("Nie udało się oznaczyć wiadomości")
                
        except Exception as error:
            print(f"Błąd podczas oznaczania wiadomości: {error}")
            toast("Błąd przy oznaczaniu wiadomości")
    
    def reply_to_message(self, message_data):
        """Odpowiedz na wiadomość"""
        sender = message_data.get('sender', 'System')
        subject = message_data.get('subject', '')
        reply_subject = f"Re: {subject}" if subject else "Odpowiedź"
        
        self.show_compose_dialog(
            recipient=sender,
            subject=reply_subject,
            is_reply=True
        )
    
    def compose_message(self):
        """Napisz nową wiadomość"""
        self.show_compose_dialog()
    
    def show_compose_dialog(self, recipient="", subject="", is_reply=False):
        """Pokaż dialog tworzenia wiadomości"""
        # Layout dla formularza
        form_layout = MDBoxLayout(
            orientation='vertical',
            spacing="10dp",
            size_hint_y=None,
            height="200dp"
        )
        
        # Pole odbiorcy
        recipient_field = MDTextField(
            hint_text="Odbiorca",
            text=recipient,
            size_hint_y=None,
            height="40dp"
        )
        form_layout.add_widget(recipient_field)
        
        # Pole tematu
        subject_field = MDTextField(
            hint_text="Temat",
            text=subject,
            size_hint_y=None,
            height="40dp"
        )
        form_layout.add_widget(subject_field)
        
        # Pole treści
        content_field = MDTextField(
            hint_text="Treść wiadomości...",
            multiline=True,
            size_hint_y=None,
            height="100dp"
        )
        form_layout.add_widget(content_field)
        
        # Dialog
        dialog = MDDialog(
            title="Nowa wiadomość" if not is_reply else "Odpowiedź",
            type="custom",
            content_cls=form_layout,
            buttons=[
                MDFlatButton(
                    text="ANULUJ",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="WYŚLIJ",
                    on_release=lambda x: self.send_message(
                        dialog, 
                        recipient_field.text,
                        subject_field.text,
                        content_field.text
                    )
                )
            ]
        )
        dialog.open()
    
    def send_message(self, dialog, recipient, subject, content):
        """Wyślij wiadomość"""
        if not content.strip():
            toast("Wpisz treść wiadomości")
            return
        
        dialog.dismiss()
        asyncio.create_task(self._send_message_async(recipient, subject, content))
    
    async def _send_message_async(self, recipient, subject, content):
        """Asynchronicznie wyślij wiadomość"""
        try:
            toast("Wysyłanie wiadomości...")
            
            message_data = {
                'recipient': recipient,
                'subject': subject,
                'content': content
            }
            
            response = await self.api_service.send_message(message_data)
            
            if response.get('success'):
                toast("Wiadomość wysłana!")
                # Odśwież listę wiadomości
                await self.load_messages()
            else:
                toast("Nie udało się wysłać wiadomości")
                
        except Exception as error:
            print(f"Błąd podczas wysyłania wiadomości: {error}")
            toast("Błąd przy wysyłaniu wiadomości")
    
    def refresh_messages(self):
        """Odśwież wiadomości"""
        toast("Odświeżanie wiadomości...")
        asyncio.create_task(self.load_messages())
    
    def go_back(self):
        """Wróć do poprzedniego ekranu"""
        if self.manager:
            self.manager.current = 'home'
    
    def on_leave(self):
        """Anuluj automatyczne odświeżanie przy opuszczeniu ekranu"""
        if hasattr(self, 'refresh_event'):
            self.refresh_event.cancel()
