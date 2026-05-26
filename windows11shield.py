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
    cursor.execute("""CREATE TABLE IF NOT EXISTS AllowedPorts 
                      (id INTEGER PRIMARY KEY, name TEXT, port TEXT, proto TEXT, direction TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS BlockedIPs 
                      (id INTEGER PRIMARY KEY, name TEXT, ip TEXT, direction TEXT)""")
    con.commit()

# ====================== SAFE COMMAND ======================
def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

# ====================== KILL ALL CONNECTIONS ======================
def kill_all_connections():
    print("⚠️  WARNING: This will kill ALL active network connections!")
    print("This may disconnect you from the internet, remote sessions, downloads, etc.")
    confirm = input("\nAre you ABSOLUTELY sure? (type YES to continue): ").strip().upper()
    
    if confirm != "YES":
        print("Operation cancelled.")
        return

    print("\n🔍 Reading active connections...")
    try:
        result = subprocess.run("netstat -ano", shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        lines = result.stdout.splitlines()
        
        pids_to_kill = set()
        for line in lines:
            if "ESTABLISHED" in line or "TIME_WAIT" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1].strip()
                    if pid.isdigit() and int(pid) > 100:  # Protect system critical PIDs
                        pids_to_kill.add(pid)
        
        if not pids_to_kill:
            print("No active connections found to kill.")
            return

        print(f"Found {len(pids_to_kill)} active connections to terminate...")
        
        killed = 0
        for pid in pids_to_kill:
            code, _, _ = run_command(f"taskkill /F /PID {pid}")
            if code == 0:
                killed += 1
            # Small delay to avoid overwhelming the system
            time.sleep(0.05)  # uncomment if needed
        
        print(f"✅ Successfully killed {killed} connections.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

# ====================== CORE FUNCTIONS ======================
def setup():
    print("🔒 Applying Strict Block All policy...")
    run_command('netsh advfirewall set allprofiles firewallpolicy blockinbound,blockoutbound')
    run_command('netsh advfirewall firewall delete rule name=all')
    print("✅ Firewall is now in Strict Block Mode")

def reset():
    print("🔄 Resetting to Default Windows Firewall...")
    run_command('netsh advfirewall reset')
    print("✅ Reset completed")

def backup_firewall(filename="MyFirewallBackup.wfw"):
    if not filename.endswith(".wfw"):
        filename += ".wfw"
    path = Path.cwd() / filename
    print(f"💾 Creating backup to: {path}")
    code, _, _ = run_command(f'netsh advfirewall export "{path}"')
    if code == 0 or path.exists():
        print("✅ Backup created successfully!")
    else:
        print("❌ Backup failed")

def restore_firewall(filename):
    if not filename.endswith(".wfw"):
        filename += ".wfw"
    path = Path.cwd() / filename
    if not path.exists():
        print(f"❌ File not found: {path}")
        return
    print(f"♻️ Restoring from: {path}")
    code, _, _ = run_command(f'netsh advfirewall import "{path}"')
    if code == 0:
        print("✅ Restore completed successfully!")
    else:
        print("❌ Restore failed")

def allow_app(name, path, direction):
    if direction in ["out", "both"]:
        run_command(f'netsh advfirewall firewall add rule name="{name}" dir=out program="{path}" action=allow profile=any')
    if direction in ["in", "both"]:
        run_command(f'netsh advfirewall firewall add rule name="{name}" dir=in program="{path}" action=allow profile=any')
    con = sql_connection()
    con.execute("INSERT INTO AllowedApps (name, path, direction) VALUES (?,?,?)", (name, path, direction))
    con.commit()
    print(f"✅ Allowed: {name}")

def allow_port(name, port, proto, direction):
    if direction in ["out", "both"]:
        run_command(f'netsh advfirewall firewall add rule name="{name}" dir=out protocol={proto} localport={port} action=allow')
    if direction in ["in", "both"]:
        run_command(f'netsh advfirewall firewall add rule name="{name}" dir=in protocol={proto} localport={port} action=allow')
    con = sql_connection()
    con.execute("INSERT INTO AllowedPorts (name, port, proto, direction) VALUES (?,?,?,?)", (name, port, proto, direction))
    con.commit()
    print(f"✅ Port opened: {name} ({port}/{proto})")

def block_ip(name, ip, direction):
    if direction in ["out", "both"]:
        run_command(f'netsh advfirewall firewall add rule name="{name}" dir=out action=block remoteip={ip}')
    if direction in ["in", "both"]:
        run_command(f'netsh advfirewall firewall add rule name="{name}" dir=in action=block remoteip={ip}')
    con = sql_connection()
    con.execute("INSERT INTO BlockedIPs (name, ip, direction) VALUES (?,?,?)", (name, ip, direction))
    con.commit()
    print(f"🚫 Blocked IP: {name} ({ip})")

def allow_windows_update():
    print("🔄 Adding rules to allow Windows Update...")
    rules = [
        ('Windows Update - svchost', r'%SystemRoot%\System32\svchost.exe', 'out'),
        ('Windows Update - wuauclt', r'%SystemRoot%\System32\wuauclt.exe', 'out'),
    ]
    for name, path, direction in rules:
        allow_app(name, path, direction)
    allow_port("Windows Update HTTPS", "443", "TCP", "out")
    print("✅ Windows Update allowed")

def disallow_windows_update():
    print("🚫 Blocking Windows Update...")
    run_command('netsh advfirewall firewall add rule name="Block Windows Update" dir=out action=block program="%SystemRoot%\\System32\\svchost.exe" remoteport=80,443')
    print("✅ Windows Update blocked")

def delete_rule(name):
    run_command(f'netsh advfirewall firewall delete rule name="{name}"')
    print(f"🗑️ Rule deleted: {name}")

# ====================== STATUS & MANAGEMENT ======================
def show_status():
    con = sql_connection()
    print("\n" + "="*90)
    print("                     FIREWALL STATUS")
    print("="*90)

    print("\n📌 ALLOWED APPLICATIONS:")
    apps = con.execute("SELECT id, name, direction FROM AllowedApps").fetchall()
    if apps:
        for i, (id_, name, dir_) in enumerate(apps, 1):
            print(f"   {i:2d}. {name:<40} [{dir_.upper()}]")
    else:
        print("   (None)")

    print("\n📌 ALLOWED PORTS:")
    ports = con.execute("SELECT id, name, port, proto, direction FROM AllowedPorts").fetchall()
    if ports:
        for i, (id_, name, port, proto, dir_) in enumerate(ports, 1):
            print(f"   {i:2d}. {name:<30} Port: {port:<6} {proto} [{dir_.upper()}]")
    else:
        print("   (None)")

    print("\n🚫 BLOCKED IPs:")
    ips = con.execute("SELECT id, name, ip, direction FROM BlockedIPs").fetchall()
    if ips:
        for i, (id_, name, ip, dir_) in enumerate(ips, 1):
            print(f"   {i:2d}. {name:<30} IP: {ip:<18} [{dir_.upper()}]")
    else:
        print("   (None)")

    print("="*90)

def unallow_app():
    con = sql_connection()
    apps = con.execute("SELECT id, name FROM AllowedApps").fetchall()
    if not apps:
        print("No allowed applications found.")
        return
    for i, (id_, name) in enumerate(apps, 1):
        print(f"{i:2d}. {name}")
    try:
        choice = int(input("\nEnter number to unallow: ")) - 1
        if 0 <= choice < len(apps):
            name = apps[choice][1]
            delete_rule(name)
            con.execute("DELETE FROM AllowedApps WHERE name=?", (name,))
            con.commit()
    except:
        print("Invalid selection.")

def unallow_port():
    con = sql_connection()
    ports = con.execute("SELECT id, name FROM AllowedPorts").fetchall()
    if not ports:
        print("No allowed ports found.")
        return
    for i, (id_, name) in enumerate(ports, 1):
        print(f"{i:2d}. {name}")
    try:
        choice = int(input("\nEnter number to unallow: ")) - 1
        if 0 <= choice < len(ports):
            name = ports[choice][1]
            delete_rule(name)
            con.execute("DELETE FROM AllowedPorts WHERE name=?", (name,))
            con.commit()
    except:
        print("Invalid selection.")

def unblock_ip():
    con = sql_connection()
    ips = con.execute("SELECT id, name FROM BlockedIPs").fetchall()
    if not ips:
        print("No blocked IPs found.")
        return
    for i, (id_, name) in enumerate(ips, 1):
        print(f"{i:2d}. {name}")
    try:
        choice = int(input("\nEnter number to unblock: ")) - 1
        if 0 <= choice < len(ips):
            name = ips[choice][1]
            delete_rule(name)
            con.execute("DELETE FROM BlockedIPs WHERE name=?", (name,))
            con.commit()
    except:
        print("Invalid selection.")

# ====================== MAIN MENU ======================
sql_table(sql_connection())

while True:
    os.system('cls')
    print(logo)
    time.sleep(3)
    os.system('cls')
    print("="*90)
    print("              Windows 11 Shield - Enhanced Firewall Manager")
    print("="*90)
    print("1 .  Setup (Block All Traffic)")
    print("2 .  Reset to Default Windows Firewall")
    print("3 .  Allow Application")
    print("4 .  Allow Port")
    print("5 .  Block IP Address")
    print("6 .  Allow Windows Update")
    print("7 .  Disallow Windows Update")
    print("8 .  Delete Rule (by name)")
    print("9 .  Backup Current Firewall")
    print("10.  Restore Firewall from Backup")
    print("11.  Netstat (Active Connections)")
    print("12.  Status (Allowed Apps / Ports / Blocked IPs)")
    print("13.  Unallow Application")
    print("14.  Unallow Port")
    print("15.  Unblock IP")
    print("16.  Kill All Active Connections")
    print("17.  Run CMD")
    print("0 .  Exit")
    print("="*90)

    choice = input("\nEnter your choice (0-17): ").strip()

    if choice == "1":
        setup()
        kill_all_connections()
    elif choice == "2":
        if input("Are you sure? (y/n): ").lower() == "y":
            reset()
    elif choice == "3":
        name = input("Application name: ")
        path = input("Full path to .exe: ")
        d = input("Direction (1=Out, 2=In, 3=Both): ")
        direction = "both" if d == "3" else "out" if d == "1" else "in"
        allow_app(name, path, direction)
    elif choice == "4":
        name = input("Port rule name: ")
        port = input("Port number: ")
        proto = input("Protocol (TCP/UDP/ANY): ").upper()
        d = input("Direction (1=Out, 2=In, 3=Both): ")
        direction = "both" if d == "3" else "out" if d == "1" else "in"
        allow_port(name, port, proto, direction)
    elif choice == "5":
        name = input("Block rule name: ")
        ip = input("IP or range: ")
        d = input("Direction (1=Out, 2=In, 3=Both): ")
        direction = "both" if d == "3" else "out" if d == "1" else "in"
        block_ip(name, ip, direction)
    elif choice == "6":
        allow_windows_update()
    elif choice == "7":
        if input("Block Windows Update? (y/n): ").lower() == "y":
            disallow_windows_update()
    elif choice == "8":
        name = input("Rule name to delete: ")
        delete_rule(name)
    elif choice == "9":
        fname = input("Backup filename (Enter for default): ") or "MyFirewallBackup"
        backup_firewall(fname)
    elif choice == "10":
        fname = input("Backup filename to restore: ")
        restore_firewall(fname)
    elif choice == "11":
        os.system("netstat -aon | findstr ESTABLISHED")
        input("\nPress Enter...")
    elif choice == "12":
        show_status()
        input("\nPress Enter...")
    elif choice == "13":
        unallow_app()
    elif choice == "14":
        unallow_port()
    elif choice == "15":
        unblock_ip()
    elif choice == "16":
        kill_all_connections()
    elif choice == "17":
        cmd = input("SourceCode347 >: ")
        output = run_command(cmd)
        print(output[1])
    elif choice == "0":
        print("👋 Goodbye!")
        break
    else:
        print("❌ Invalid choice!")

    input("\nPress Enter to continue...")