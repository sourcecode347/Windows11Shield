# ================================================
#   Windows 11 Shield - Enhanced Version (English)
#   SourceCode347 - 2026
# ================================================

import os
import subprocess
import sys
import sqlite3
import time
from pathlib import Path

# ====================== ASCII ART ======================
logo = (r"""
  ___                        ___        _       _____ _ ____          
 / __|___ _  _ _ _ __ ___   / __|___ __| |___  |__ | | |__  |         
 \__ / _ | || | '_/ _/ -_) | (__/ _ / _` / -_)  |_ |_  _|/ /          
  ____\______,_|_| \______|  \___\___\____\___| |___/_|_|/_/    _  _ 
 \ \    / (_)_ _  __| |_____ __ _____ / | / | / __| |_ (_)___| |__| |
  \ \/\/ /| | ' \/ _` / _ \ V  V (_-< | | | | \__ | ' \| / -_| / _` |
   \_/\_/ |_|_||_\__,_\___/\_/\_//__/ |_| |_| |___|_||_|_\___|_\__,_|
                                                                       
               Windows 11 Shield - Enhanced Firewall Tool
""")

# ====================== CHECK ADMIN ======================
def is_admin():
    try:
        return subprocess.run("net session", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
    except:
        return False

if not is_admin():
    print("❌ Error: You must run this program as Administrator!")
    input("Press Enter to exit...")
    sys.exit()

# ====================== DATABASE ======================
def sql_connection():
    return sqlite3.connect('database.db')

def sql_table(con):
    cursor = con.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS AllowedApps 
                      (id INTEGER PRIMARY KEY, name TEXT, path TEXT, direction TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS BlockedIPs 
                      (id INTEGER PRIMARY KEY, name TEXT, ip TEXT, direction TEXT)""")
    con.commit()

# ====================== FIREWALL FUNCTIONS ======================
def setup():
    print("🔒 Applying Strict Block All policy...")
    subprocess.run('netsh advfirewall set allprofiles firewallpolicy blockinbound,blockoutbound', shell=True)
    subprocess.run('netsh advfirewall firewall delete rule name=all', shell=True)
    print("✅ Firewall is now in Strict Block Mode")

def reset():
    print("🔄 Resetting to Default Windows Firewall...")
    subprocess.run('netsh advfirewall reset', shell=True)
    print("✅ Reset completed")

def backup_firewall(filename="MyFirewallBackup.wfw"):
    if not filename.endswith(".wfw"):
        filename += ".wfw"
    path = Path.cwd() / filename
    print(f"💾 Creating backup to: {path}")
    result = subprocess.run(f'netsh advfirewall export "{path}"', shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Backup created successfully!")
    else:
        print("❌ Backup failed:", result.stderr)

def restore_firewall(filename):
    if not filename.endswith(".wfw"):
        filename += ".wfw"
    path = Path.cwd() / filename
    if not path.exists():
        print(f"❌ File not found: {path}")
        return
    print(f"♻️ Restoring from: {path}")
    result = subprocess.run(f'netsh advfirewall import "{path}"', shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Restore completed successfully!")
    else:
        print("❌ Restore failed:", result.stderr)

def allow_app(name, path, direction):
    if direction in ["out", "both"]:
        subprocess.run(f'netsh advfirewall firewall add rule name="{name}" dir=out program="{path}" action=allow profile=any', shell=True)
    if direction in ["in", "both"]:
        subprocess.run(f'netsh advfirewall firewall add rule name="{name}" dir=in program="{path}" action=allow profile=any', shell=True)
    print(f"✅ Allowed: {name}")

def allow_port(name, port, proto, direction):
    if direction in ["out", "both"]:
        subprocess.run(f'netsh advfirewall firewall add rule name="{name}" dir=out protocol={proto} localport={port} action=allow', shell=True)
    if direction in ["in", "both"]:
        subprocess.run(f'netsh advfirewall firewall add rule name="{name}" dir=in protocol={proto} localport={port} action=allow', shell=True)
    print(f"✅ Port opened: {name} ({port}/{proto})")

def block_ip(name, ip, direction):
    if direction in ["out", "both"]:
        subprocess.run(f'netsh advfirewall firewall add rule name="{name}" dir=out action=block remoteip={ip}', shell=True)
    if direction in ["in", "both"]:
        subprocess.run(f'netsh advfirewall firewall add rule name="{name}" dir=in action=block remoteip={ip}', shell=True)
    print(f"🚫 Blocked IP: {name} ({ip})")

def allow_windows_update():
    print("🔄 Adding rules to allow Windows Update...")
    # Main services and executables
    rules = [
        ('Windows Update - svchost Out', r'%SystemRoot%\System32\svchost.exe', 'out'),
        ('Windows Update - wuauclt', r'%SystemRoot%\System32\wuauclt.exe', 'out'),
        ('BITS Service', r'%SystemRoot%\System32\svchost.exe', 'out'),
    ]
    for name, path, direction in rules:
        allow_app(name, path, direction)
    # Common ports for updates (HTTPS)
    allow_port("Windows Update HTTPS", "443", "TCP", "out")
    print("✅ Windows Update should now work")

def disallow_windows_update():
    print("🚫 Blocking Windows Update...")
    subprocess.run('netsh advfirewall firewall add rule name="Block Windows Update" dir=out action=block program="%SystemRoot%\\System32\\svchost.exe" remoteport=80,443', shell=True)
    subprocess.run('netsh advfirewall firewall add rule name="Block Windows Update wuauclt" dir=out action=block program="%SystemRoot%\\System32\\wuauclt.exe"', shell=True)
    print("✅ Windows Update is now blocked")

def delete_rule(name):
    subprocess.run(f'netsh advfirewall firewall delete rule name="{name}"', shell=True)
    print(f"🗑️ Rule deleted: {name}")

# ====================== MAIN MENU ======================
sql_table(sql_connection())

while True:
    os.system('cls')
    print(logo)
    time.sleep(3)
    os.system('cls')
    print("="*85)
    print("              Windows 11 Shield - Enhanced Firewall Manager")
    print("="*85)
    print("1 . Setup (Block All Traffic)")
    print("2 . Reset to Default Windows Firewall")
    print("3 . Allow Application")
    print("4 . Allow Port")
    print("5 . Block IP Address")
    print("6 . Delete Rule")
    print("7 . Allow Windows Update")
    print("8 . Disallow Windows Update")
    print("9 . Backup Current Firewall")
    print("10. Restore Firewall from Backup")
    print("11. Netstat (Active Connections)")
    print("0 . Exit")
    print("="*85)

    choice = input("\nEnter your choice (0-11): ").strip()

    if choice == "1":
        setup()
    elif choice == "2":
        if input("Are you sure you want to reset to default? (y/n): ").lower() == "y":
            reset()
    elif choice == "3":
        name = input("Application name: ")
        path = input("Full path to .exe: ")
        dir_choice = input("Direction (1=Outbound, 2=Inbound, 3=Both): ")
        direction = "both" if dir_choice == "3" else "out" if dir_choice == "1" else "in"
        allow_app(name, path, direction)
    elif choice == "4":
        name = input("Port rule name: ")
        port = input("Port number: ")
        proto = input("Protocol (TCP / UDP / ANY): ").upper()
        dir_choice = input("Direction (1=Outbound, 2=Inbound, 3=Both): ")
        direction = "both" if dir_choice == "3" else "out" if dir_choice == "1" else "in"
        allow_port(name, port, proto, direction)
    elif choice == "5":
        name = input("Block rule name: ")
        ip = input("IP address or range: ")
        dir_choice = input("Direction (1=Outbound, 2=Inbound, 3=Both): ")
        direction = "both" if dir_choice == "3" else "out" if dir_choice == "1" else "in"
        block_ip(name, ip, direction)
    elif choice == "6":
        name = input("Rule name to delete: ")
        delete_rule(name)
    elif choice == "7":
        allow_windows_update()
    elif choice == "8":
        if input("Are you sure you want to block Windows Update? (y/n): ").lower() == "y":
            disallow_windows_update()
    elif choice == "9":
        fname = input("Backup filename (Enter for default): ") or "MyFirewallBackup"
        backup_firewall(fname)
    elif choice == "10":
        fname = input("Backup filename to restore (.wfw): ")
        restore_firewall(fname)
    elif choice == "11":
        print("\nActive Connections:")
        os.system("netstat -ano | findstr ESTABLISHED")
        input("\nPress Enter to continue...")
    elif choice == "0":
        print("👋 Goodbye!")
        break
    else:
        print("❌ Invalid choice!")

    input("\nPress Enter to continue...")