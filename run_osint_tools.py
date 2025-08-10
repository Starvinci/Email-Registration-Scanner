#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSINT-Tools CLI - Direkter Start der OSINT-Tools
"""

import sys
import os
import subprocess
import argparse
from typing import Optional

def run_maigret(query: str, options: list = None) -> None:
    """Startet Maigret mit der angegebenen Abfrage"""
    print(f"🔍 Starte Maigret-Scan für: {query}")
    
    # Standard-Optionen
    default_options = ["--timeout", "10", "--print-found"]
    if options:
        default_options.extend(options)
    
    # Prüfe verschiedene mögliche Pfade für Maigret
    maigret_paths = [
        os.path.join(os.getcwd(), "maigret", "maigret", "__main__.py"),
        os.path.join(os.getcwd(), "maigret", "pyinstaller", "maigret_standalone.py"),
        os.path.join(os.getcwd(), "maigret", "__main__.py")
    ]
    
    maigret_path = None
    for path in maigret_paths:
        if os.path.exists(path):
            maigret_path = path
            break
    
    if maigret_path:
        cmd = [sys.executable, maigret_path, query] + default_options
        print(f"🚀 Befehl: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=False, text=True)
            if result.returncode != 0:
                print(f"❌ Maigret beendet mit Code: {result.returncode}")
        except KeyboardInterrupt:
            print("\n⏹️  Maigret-Scan abgebrochen")
        except Exception as e:
            print(f"❌ Fehler beim Starten von Maigret: {e}")
    else:
        print("❌ Maigret nicht gefunden. Führe install_osint_tools.sh aus.")

def run_sherlock(username: str, options: list = None) -> None:
    """Startet Sherlock mit dem angegebenen Username"""
    print(f"🕵️ Starte Sherlock-Scan für Username: {username}")
    
    # Standard-Optionen
    default_options = ["--timeout", "10"]
    if options:
        default_options.extend(options)
    
    # Prüfe verschiedene mögliche Pfade für Sherlock
    sherlock_paths = [
        os.path.join(os.getcwd(), "sherlock", "sherlock_project", "__main__.py"),
        os.path.join(os.getcwd(), "sherlock", "__main__.py"),
        os.path.join(os.getcwd(), "sherlock", "sherlock_project", "sherlock.py")
    ]
    
    sherlock_path = None
    for path in sherlock_paths:
        if os.path.exists(path):
            sherlock_path = path
            break
    
    if sherlock_path:
        cmd = [sys.executable, sherlock_path, username] + default_options
        print(f"🚀 Befehl: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=False, text=True)
            if result.returncode != 0:
                print(f"❌ Sherlock beendet mit Code: {result.returncode}")
        except KeyboardInterrupt:
            print("\n⏹️  Sherlock-Scan abgebrochen")
        except Exception as e:
            print(f"❌ Fehler beim Starten von Sherlock: {e}")
    else:
        print("❌ Sherlock nicht gefunden. Führe install_osint_tools.sh aus.")

def run_holehe(email: str, options: list = None) -> None:
    """Startet Holehe mit der angegebenen E-Mail"""
    print(f"📧 Starte Holehe-Scan für: {email}")
    
    # Standard-Optionen
    default_options = []
    if options:
        default_options.extend(options)
    
    try:
        cmd = ["holehe", email] + default_options
        print(f"🚀 Befehl: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=False, text=True)
        if result.returncode != 0:
            print(f"❌ Holehe beendet mit Code: {result.returncode}")
    except FileNotFoundError:
        print("❌ Holehe nicht gefunden. Installiere es mit: pip install holehe")
    except KeyboardInterrupt:
        print("\n⏹️  Holehe-Scan abgebrochen")
    except Exception as e:
        print(f"❌ Fehler beim Starten von Holehe: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="OSINT-Tools CLI - Starte OSINT-Tools direkt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python run_osint_tools.py maigret "test@example.com"
  python run_osint_tools.py sherlock "testuser"
  python run_osint_tools.py holehe "test@example.com"
  python run_osint_tools.py maigret "test@example.com" -- --verbose
        """
    )
    
    parser.add_argument(
        "tool",
        choices=["maigret", "sherlock", "holehe"],
        help="Das zu startende OSINT-Tool"
    )
    
    parser.add_argument(
        "query",
        help="Abfrage für das Tool (E-Mail für Maigret/Holehe, Username für Sherlock)"
    )
    
    parser.add_argument(
        "--options",
        nargs="*",
        help="Zusätzliche Optionen für das Tool"
    )
    
    args = parser.parse_args()
    
    print("🚀 OSINT-Tools CLI")
    print("=" * 50)
    
    if args.tool == "maigret":
        run_maigret(args.query, args.options)
    elif args.tool == "sherlock":
        run_sherlock(args.query, args.options)
    elif args.tool == "holehe":
        run_holehe(args.query, args.options)

if __name__ == "__main__":
    main()
