import os
import time
import subprocess
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ColorProperty

class WiFiManager(App):
    background_color = ColorProperty([1, 1, 1, 1])  # White background

    def __init__(self):
        super().__init__()
        self.selected_ssid = None
        self.monitoring = False
        self.os_type = None
        self.terminal_text = ""
        Window.clearcolor = self.background_color

    def get_os_commands(self):
        """Return OS-specific commands"""
        if self.os_type == "Windows":
            return {
                "show_interfaces": "netsh wlan show interfaces",
                "show_networks": "netsh wlan show networks mode=bssid",
                "connect": lambda ssid: f'netsh wlan connect name="{ssid}" ssid="{ssid}"',
                "enable": 'netsh interface set interface "Wi-Fi" enable',
                "disable": 'netsh interface set interface "Wi-Fi" disable',
                "interface_state": 'netsh interface show interface "Wi-Fi"'
            }
        elif self.os_type == "macOS":
            return {
                "show_interfaces": "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I",
                "show_networks": "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s",
                "connect": lambda ssid: f'networksetup -setairportnetwork en0 "{ssid}"',
                "enable": "networksetup -setairportpower en0 on",
                "disable": "networksetup -setairportpower en0 off",
                "interface_state": "networksetup -getairportpower en0"
            }
        elif self.os_type == "Linux":
            return {
                "show_interfaces": "nmcli -t -f active,ssid dev wifi",
                "show_networks": "nmcli -t -f ssid,bssid dev wifi",
                "connect": lambda ssid: f'nmcli dev wifi connect "{ssid}"',
                "enable": "nmcli radio wifi on",
                "disable": "nmcli radio wifi off",
                "interface_state": "nmcli radio wifi"
            }
        return None

    def get_current_wifi(self):
        """Get the current Wi-Fi SSID"""
        commands = self.get_os_commands()
        if not commands:
            return None
        try:
            result = subprocess.check_output(commands["show_interfaces"], shell=True, text=True)
            if self.os_type == "Windows":
                for line in result.split('\n'):
                    if "SSID" in line and "BSSID" not in line:
                        ssid = line.split(':')[1].strip()
                        return ssid if ssid else None
                    if "State" in line and "disconnected" in line.lower():
                        return None
            elif self.os_type == "macOS":
                for line in result.split('\n'):
                    if "SSID" in line:
                        return line.split(':')[1].strip()
            elif self.os_type == "Linux":
                for line in result.split('\n'):
                    if "yes" in line:
                        return line.split(':')[1].strip()
            return None
        except subprocess.CalledProcessError:
            return None

    def is_wifi_powered_down(self):
        """Check if Wi-Fi is powered down"""
        commands = self.get_os_commands()
        if not commands:
            return True
        try:
            result = subprocess.check_output(commands["interface_state"], shell=True, text=True)
            if self.os_type == "Windows":
                for line in result.split('\n'):
                    if "Admin State" in line:
                        return "disable" in line.lower()
            elif self.os_type == "macOS":
                return "Off" in result
            elif self.os_type == "Linux":
                return "disabled" in result.lower()
            return False
        except subprocess.CalledProcessError:
            return True

    def toggle_wifi(self, power_up_only=False):
        """Toggle Wi-Fi or power up"""
        commands = self.get_os_commands()
        if not commands:
            return
        if self.is_wifi_powered_down():
            self.update_terminal("Wi-Fi powered down. Powering up...")
            os.system(commands["enable"])
            time.sleep(2)  # Reduced from 5 to 2 seconds
        elif not power_up_only:
            self.update_terminal("Toggling Wi-Fi...")
            os.system(commands["disable"])
            time.sleep(2)  # Reduced from 5 to 2 seconds
            os.system(commands["enable"])
            time.sleep(2)  # Reduced from 5 to 2 seconds

    def get_available_wifi(self):
        """Get list of available Wi-Fi networks"""
        commands = self.get_os_commands()
        if not commands:
            return []
        try:
            result = subprocess.check_output(commands["show_networks"], shell=True, text=True)
            networks = []
            if self.os_type == "Windows":
                current_ssid = None
                for line in result.split('\n'):
                    if line.strip().startswith("SSID"):
                        current_ssid = line.split(':')[1].strip()
                    elif line.strip().startswith("BSSID") and current_ssid:
                        bssid = line.split(':')[1].strip()
                        networks.append((current_ssid, bssid))
            elif self.os_type == "macOS":
                for line in result.split('\n')[1:]:
                    parts = line.split()
                    if len(parts) > 1:
                        ssid = " ".join(parts[1:-6])
                        bssid = parts[0]
                        networks.append((ssid, bssid))
            elif self.os_type == "Linux":
                for line in result.split('\n'):
                    if line.strip():
                        ssid, bssid = line.split(':', 1)
                        networks.append((ssid, bssid))
            return networks
        except subprocess.CalledProcessError:
            return []

    def connect_to_wifi(self, ssid):
        """Connect to the specified Wi-Fi"""
        commands = self.get_os_commands()
        if commands:
            os.system(commands["connect"](ssid))
            time.sleep(2)  # Reduced from 5 to 2 seconds

    def update_terminal(self, message):
        """Update the terminal with new lines at the bottom"""
        self.terminal_text = f"{self.terminal_text}\n{message}"[-500:]
        self.terminal_label.text = self.terminal_text

    def monitor_connection(self, dt):
        """Monitor and maintain connection"""
        if not self.monitoring or not self.selected_ssid:
            return
        if self.is_wifi_powered_down():
            self.update_terminal(f"Wi-Fi powered down. Reconnecting to {self.selected_ssid}...")
            self.toggle_wifi(power_up_only=True)
            self.connect_to_wifi(self.selected_ssid)
        else:
            current_ssid = self.get_current_wifi()
            if current_ssid is None:
                self.update_terminal(f"Disconnected from {self.selected_ssid}. Reconnecting...")
                self.toggle_wifi()
                self.connect_to_wifi(self.selected_ssid)
            elif current_ssid != self.selected_ssid:
                self.update_terminal(f"Connected to {current_ssid}. Switching to {self.selected_ssid}...")
                self.toggle_wifi()
                self.connect_to_wifi(self.selected_ssid)
            else:
                self.update_terminal(f"Connected to {self.selected_ssid} - All good!")

    def refresh_wifi_list(self, instance):
        """Refresh the Wi-Fi list in the table"""
        self.wifi_table.clear_widgets()
        self.wifi_table.add_widget(Label(text="Si No", color=[0, 0, 0, 1], size_hint_x=0.1, bold=True, height=40))
        self.wifi_table.add_widget(Label(text="Radio", color=[0, 0, 0, 1], size_hint_x=0.2, bold=True, height=40))
        self.wifi_table.add_widget(Label(text="WiFi Name", color=[0, 0, 0, 1], size_hint_x=0.4, bold=True, height=40))
        self.wifi_table.add_widget(Label(text="BSSID", color=[0, 0, 0, 1], size_hint_x=0.3, bold=True, height=40))
        networks = self.get_available_wifi()
        if not networks:
            self.update_terminal("No networks found")
            self.wifi_table.add_widget(Label(text="No networks", color=[0, 0, 0, 1], size_hint_x=0.1, height=40))
            self.wifi_table.add_widget(Label(text="", color=[0, 0, 0, 1], size_hint_x=0.2, height=40))
            self.wifi_table.add_widget(Label(text="available", color=[0, 0, 0, 1], size_hint_x=0.4, height=40))
            self.wifi_table.add_widget(Label(text="", color=[0, 0, 0, 1], size_hint_x=0.3, height=40))
            return
        for i, (ssid, bssid) in enumerate(networks, 1):
            si_no = Label(text=str(i), color=[0, 0, 0, 1], size_hint_x=0.1, height=40)
            cb = CheckBox(group='wifi', color=[0, 0, 0, 1], size_hint_x=0.2, height=40)
            cb.bind(active=lambda cb, value, s=ssid: self.on_checkbox_active(s, value))
            wifi_name = Label(text=ssid, color=[0, 0, 0, 1], size_hint_x=0.4, height=40)
            bssid_label = Label(text=bssid, color=[0, 0, 0, 1], size_hint_x=0.3, height=40)
            self.wifi_table.add_widget(si_no)
            self.wifi_table.add_widget(cb)
            self.wifi_table.add_widget(wifi_name)
            self.wifi_table.add_widget(bssid_label)

    def on_checkbox_active(self, ssid, value):
        """Handle checkbox selection"""
        if value:
            self.selected_ssid = ssid

    def start_monitoring(self, instance):
        """Start monitoring the selected Wi-Fi"""
        if self.selected_ssid and self.os_type:
            self.monitoring = True
            self.connect_to_wifi(self.selected_ssid)
            self.update_terminal(f"Connecting to {self.selected_ssid}...")
            Clock.schedule_interval(self.monitor_connection, 5)  # Reduced from 10 to 5 seconds
        else:
            self.update_terminal("Please select a Wi-Fi and OS!")

    def set_os(self, os_name, value):
        """Set the OS type"""
        if value:
            self.os_type = os_name
            self.refresh_wifi_list(None)

    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # OS Selection
        os_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        os_layout.add_widget(Label(text="Select OS:", color=[0, 0, 0, 1]))
        for os_name in ["Windows", "macOS", "Linux"]:
            cb = CheckBox(group='os', color=[0, 0, 0, 1], size_hint_x=0.1)
            cb.bind(active=lambda cb, value, n=os_name: self.set_os(n, value))
            os_layout.add_widget(cb)
            os_layout.add_widget(Label(text=os_name, color=[0, 0, 0, 1], size_hint_x=0.3))
        layout.add_widget(os_layout)

        # Wi-Fi Table
        scroll = ScrollView(size_hint_y=0.5)
        self.wifi_table = GridLayout(cols=4, spacing=5, size_hint_y=None, row_default_height=40)
        self.wifi_table.bind(minimum_height=self.wifi_table.setter('height'))
        scroll.add_widget(self.wifi_table)
        layout.add_widget(scroll)

        # Buttons
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        refresh_btn = Button(text="Refresh Wi-Fi List", color=[0, 0, 0, 1], background_color=[0.9, 0.9, 0.9, 1])
        refresh_btn.bind(on_press=self.refresh_wifi_list)
        connect_btn = Button(text="Connect & Monitor", color=[0, 0, 0, 1], background_color=[0.9, 0.9, 0.9, 1])
        connect_btn.bind(on_press=self.start_monitoring)
        btn_layout.add_widget(refresh_btn)
        btn_layout.add_widget(connect_btn)
        layout.add_widget(btn_layout)

        # Terminal
        terminal_scroll = ScrollView(size_hint_y=0.3)
        self.terminal_label = Label(
            text="Terminal output will appear here\n",
            color=[0, 0, 0, 1],
            size_hint_y=None,
            height=200,
            halign='left',
            valign='bottom',
            text_size=(None, None)
        )
        self.terminal_label.bind(size=self.terminal_label.setter('text_size'))
        terminal_scroll.add_widget(self.terminal_label)
        layout.add_widget(terminal_scroll)

        # Initial refresh
        self.refresh_wifi_list(None)

        return layout

if __name__ == "__main__":
    WiFiManager().run()
