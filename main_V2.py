import os
import time
import subprocess

def get_current_wifi():
    """Get the current Wi-Fi SSID"""
    try:
        result = subprocess.check_output('netsh wlan show interfaces', shell=True, text=True)
        for line in result.split('\n'):
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(':')[1].strip()
                return ssid if ssid else None
            if "State" in line:
                state = line.split(':')[1].strip()
                if "disconnected" in state.lower():
                    return None
        return None
    except subprocess.CalledProcessError:
        return None

def is_wifi_powered_down():
    """Check if the Wi-Fi interface is powered down"""
    try:
        result = subprocess.check_output('netsh interface show interface "Wi-Fi"', shell=True, text=True)
        for line in result.split('\n'):
            if "Admin State" in line:
                state = line.split(':')[1].strip()
                return "disable" in state.lower()
        return False
    except subprocess.CalledProcessError:
        return True

def toggle_wifi(power_up_only=False):
    """Turn Wi-Fi off and on, or just power up if specified"""
    if is_wifi_powered_down():
        print("Wi-Fi interface is powered down. Powering up...")
        os.system('netsh interface set interface "Wi-Fi" enable')
        time.sleep(5)
    elif not power_up_only:
        print("Toggling Wi-Fi...")
        os.system('netsh interface set interface "Wi-Fi" disable')
        time.sleep(5)
        os.system('netsh interface set interface "Wi-Fi" enable')
        time.sleep(5)

def get_available_wifi():
    """Get list of available Wi-Fi networks with SSID and BSSID"""
    try:
        result = subprocess.check_output('netsh wlan show networks mode=bssid', shell=True, text=True)
        networks = []
        current_ssid = None
        current_bssid = None
        
        for line in result.split('\n'):
            line = line.strip()
            if line.startswith("SSID"):
                current_ssid = line.split(':')[1].strip()
            elif line.startswith("BSSID") and current_ssid:
                current_bssid = line.split(':')[1].strip()
                networks.append((current_ssid, current_bssid))
        return networks
    except subprocess.CalledProcessError:
        return []

def display_wifi_list():
    """Display available Wi-Fi networks and return the list"""
    networks = get_available_wifi()
    if not networks:
        print("No Wi-Fi networks available or scanning failed.")
        return []
    
    print("\nAvailable Wi-Fi Networks:")
    print(f"{'Si No':<6} {'Name':<20} {'BSSID':<17}")
    print("-" * 43)
    for i, (ssid, bssid) in enumerate(networks, 1):
        print(f"{i:<6} {ssid:<20} {bssid:<17}")
    return networks

def connect_to_wifi(ssid):
    """Connect to the specified Wi-Fi"""
    os.system(f'netsh wlan connect name="{ssid}" ssid="{ssid}"')
    time.sleep(5)

def main():
    print("Wi-Fi Connection Manager")
    
    # Ensure Wi-Fi is powered on
    if is_wifi_powered_down():
        toggle_wifi(power_up_only=True)
    
    # Show available networks and get user selection with refresh option
    while True:
        networks = display_wifi_list()
        if not networks:
            print("Waiting for networks to appear...")
            time.sleep(5)
            continue
        
        try:
            choice = input("\nEnter the Si No of the Wi-Fi to connect (or 'r' to refresh): ").strip().lower()
            if choice == 'r':
                print("Refreshing Wi-Fi list...")
                continue  # Refresh the list
            
            choice = int(choice)
            if 1 <= choice <= len(networks):
                selected_ssid = networks[choice - 1][0]
                print(f"Selected {selected_ssid}. Starting connection monitoring...")
                connect_to_wifi(selected_ssid)
                break
            else:
                print("Invalid Si No. Please try again.")
        except ValueError:
            print("Invalid input. Enter a number or 'r' to refresh.")
    
    # Monitor and maintain connection to selected Wi-Fi
    while True:
        if is_wifi_powered_down():
            print(f"Wi-Fi interface is powered down. Attempting to power up and connect to {selected_ssid}...")
            toggle_wifi(power_up_only=True)
            connect_to_wifi(selected_ssid)
        else:
            current_ssid = get_current_wifi()
            
            if current_ssid is None:
                print(f"Disconnected from {selected_ssid}. Reconnecting...")
                toggle_wifi()
                connect_to_wifi(selected_ssid)
            elif current_ssid != selected_ssid:
                print(f"Connected to {current_ssid} instead of {selected_ssid}. Switching back...")
                toggle_wifi()
                connect_to_wifi(selected_ssid)
            else:
                print(f"Connected to {selected_ssid} - All good!")
        
        # Check every 10 seconds
        time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript stopped by user.")
