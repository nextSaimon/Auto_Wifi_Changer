import os
import time
import subprocess

def get_current_wifi():
    """Get the current Wi-Fi SSID"""
    try:
        # Run netsh command to get current wifi info
        result = subprocess.check_output('netsh wlan show interfaces', shell=True, text=True)
        for line in result.split('\n'):
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(':')[1].strip()
                return ssid if ssid else None
        return None
    except subprocess.CalledProcessError:
        return None

def toggle_wifi():
    """Turn Wi-Fi off and on"""
    # Disable Wi-Fi
    os.system('netsh interface set interface "Wi-Fi" disable')
    time.sleep(5)  # Wait for 5 seconds
    
    # Enable Wi-Fi
    os.system('netsh interface set interface "Wi-Fi" enable')
    time.sleep(5)  # Wait for 5 seconds

def connect_to_wifi(ssid):
    """Connect to the specified Wi-Fi"""
    os.system(f'netsh wlan connect name="{ssid}" ssid="{ssid}"')
    time.sleep(5)  # Wait for connection to establish

def main():
    # Ask user for the target Wi-Fi name
    TARGET_SSID = input("Enter the Wi-Fi name you want to stay connected to: ").strip()
    if not TARGET_SSID:
        print("No Wi-Fi name provided. Exiting...")
        return
    
    print(f"Monitoring Wi-Fi connection. Target network: {TARGET_SSID}")
    
    while True:
        current_ssid = get_current_wifi()
        
        if current_ssid is None:
            print("Wi-Fi is disconnected. Attempting to reconnect to target network...")
            toggle_wifi()
            connect_to_wifi(TARGET_SSID)
        elif current_ssid != TARGET_SSID:
            print(f"Connected to {current_ssid} instead of {TARGET_SSID}. Switching back...")
            toggle_wifi()
            connect_to_wifi(TARGET_SSID)
        else:
            print(f"Connected to {TARGET_SSID} - All good!")
        
        # Check every 10 seconds
        time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript stopped by user.")
