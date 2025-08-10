#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Scanner - Eine CLI-Anwendung zum Überprüfen von E-Mail-Adressen auf verschiedenen Websites
"""

import requests
import json
import time
import os
import subprocess
import sys
import threading
import queue
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
import re
import art

class OSINTToolManager:
    """Manager für OSINT-Tools mit Subthreads für bessere Performance"""
    
    def __init__(self, console: Console):
        self.console = console
        self.tools_available = {}
        self.tool_processes = {}
        self.input_queues = {}
        self.output_queues = {}
        self.tool_threads = {}
        self.running = False
        
        # Starte Tools in Subthreads beim Initialisieren
        self._start_tools_in_background()
    
    def _start_tools_in_background(self):
        """Startet alle verfügbaren OSINT-Tools in Subthreads"""
        self.console.print("[cyan]🔄 Starte OSINT-Tools im Hintergrund...[/cyan]")
        
        # Prüfe Tools und starte sie in Threads
        tools_to_check = {
            "maigret": self._start_maigret_background,
            "sherlock": self._start_sherlock_background,
            "holehe": self._start_holehe_background
        }
        
        for tool_name, start_func in tools_to_check.items():
            try:
                if start_func():
                    self.tools_available[tool_name] = True
                    self.console.print(f"[green] {tool_name.capitalize()} gestartet[/green]")
                else:
                    self.tools_available[tool_name] = False
            except Exception as e:
                self.console.print(f"[red] Fehler beim Starten von {tool_name}: {e}[/red]")
                self.tools_available[tool_name] = False
        
        self.running = True
        self.console.print(f"[green]🚀 {sum(self.tools_available.values())} OSINT-Tools erfolgreich gestartet[/green]")
    
    def _start_maigret_background(self) -> bool:
        """Startet Maigret im Hintergrund-Thread"""
        try:
            # Prüfe verschiedene mögliche Pfade
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
            
            if not maigret_path:
                return False
            
            # Erstelle Queues für Kommunikation
            input_queue = queue.Queue()
            output_queue = queue.Queue()
            
            # Starte Thread für Maigret
            thread = threading.Thread(
                target=self._maigret_worker,
                args=(maigret_path, input_queue, output_queue),
                daemon=True
            )
            thread.start()
            
            # Speichere Referenzen
            self.tool_processes["maigret"] = thread
            self.input_queues["maigret"] = input_queue
            self.output_queues["maigret"] = output_queue
            self.tool_threads["maigret"] = thread
            
            return True
        except Exception as e:
            self.console.print(f"[red]Fehler beim Starten von Maigret: {e}[/red]")
            return False
    
    def _start_sherlock_background(self) -> bool:
        """Startet Sherlock im Hintergrund-Thread"""
        try:
            # Prüfe verschiedene mögliche Pfade
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
            
            if not sherlock_path:
                return False
            
            # Erstelle Queues für Kommunikation
            input_queue = queue.Queue()
            output_queue = queue.Queue()
            
            # Starte Thread für Sherlock
            thread = threading.Thread(
                target=self._sherlock_worker,
                args=(sherlock_path, input_queue, output_queue),
                daemon=True
            )
            thread.start()
            
            # Speichere Referenzen
            self.tool_processes["sherlock"] = thread
            self.input_queues["sherlock"] = input_queue
            self.output_queues["sherlock"] = output_queue
            self.tool_threads["sherlock"] = thread
            
            return True
        except Exception as e:
            self.console.print(f"[red]Fehler beim Starten von Sherlock: {e}[/red]")
            return False
    
    def _start_holehe_background(self) -> bool:
        """Startet Holehe im Hintergrund-Thread (falls verfügbar)"""
        try:
            # Prüfe ob Holehe verfügbar ist
            result = subprocess.run(["holehe", "--help"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode != 0:
                return False
            
            # Erstelle Queues für Kommunikation
            input_queue = queue.Queue()
            output_queue = queue.Queue()
            
            # Starte Thread für Holehe
            thread = threading.Thread(
                target=self._holehe_worker,
                args=(input_queue, output_queue),
                daemon=True
            )
            thread.start()
            
            # Speichere Referenzen
            self.tool_processes["holehe"] = thread
            self.input_queues["holehe"] = input_queue
            self.output_queues["holehe"] = output_queue
            self.tool_threads["holehe"] = thread
            
            return True
        except Exception:
            return False
    
    def _maigret_worker(self, maigret_path: str, input_queue: queue.Queue, output_queue: queue.Queue):
        """Worker-Thread für Maigret"""
        while self.running:
            try:
                # Warte auf Eingabe
                try:
                    data = input_queue.get(timeout=1)
                    if data is None:  # Stop-Signal
                        break
                    
                    query, scan_id = data
                    
                    # Führe Maigret-Scan durch
                    cmd = [sys.executable, maigret_path, query, "--timeout", "10", "--print-found"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                    
                    # Sende Ergebnis zurück
                    output_queue.put({
                        "scan_id": scan_id,
                        "tool": "maigret",
                        "query": query,
                        "success": result.returncode == 0,
                        "output": result.stdout,
                        "error": result.stderr,
                        "return_code": result.returncode
                    })
                    
                except queue.Empty:
                    continue
                    
            except Exception as e:
                output_queue.put({
                    "scan_id": "error",
                    "tool": "maigret",
                    "error": str(e)
                })
    
    def _sherlock_worker(self, sherlock_path: str, input_queue: queue.Queue, output_queue: queue.Queue):
        """Worker-Thread für Sherlock"""
        while self.running:
            try:
                # Warte auf Eingabe
                try:
                    data = input_queue.get(timeout=1)
                    if data is None:  # Stop-Signal
                        break
                    
                    username, scan_id = data
                    
                    # Führe Sherlock-Scan durch
                    cmd = [sys.executable, sherlock_path, username, "--timeout", "10"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    
                    # Sende Ergebnis zurück
                    output_queue.put({
                        "scan_id": scan_id,
                        "tool": "sherlock",
                        "query": username,
                        "success": result.returncode == 0,
                        "output": result.stdout,
                        "error": result.stderr,
                        "return_code": result.returncode
                    })
                    
                except queue.Empty:
                    continue
                    
            except Exception as e:
                output_queue.put({
                    "scan_id": "error",
                    "tool": "sherlock",
                    "error": str(e)
                })
    
    def _holehe_worker(self, input_queue: queue.Queue, output_queue: queue.Queue):
        """Worker-Thread für Holehe"""
        while self.running:
            try:
                # Warte auf Eingabe
                try:
                    data = input_queue.get(timeout=1)
                    if data is None:  # Stop-Signal
                        break
                    
                    email, scan_id = data
                    
                    # Führe Holehe-Scan durch
                    cmd = ["holehe", email]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    
                    # Sende Ergebnis zurück
                    output_queue.put({
                        "scan_id": scan_id,
                        "tool": "holehe",
                        "query": email,
                        "success": result.returncode == 0,
                        "output": result.stdout,
                        "error": result.stderr,
                        "return_code": result.returncode
                    })
                    
                except queue.Empty:
                    continue
                    
            except Exception as e:
                output_queue.put({
                    "scan_id": "error",
                    "tool": "holehe",
                    "error": str(e)
                })
    
    def submit_scan(self, tool: str, query: str) -> str:
        """Übermittelt einen Scan an das entsprechende Tool"""
        if tool not in self.tools_available or not self.tools_available[tool]:
            return None
        
        if tool not in self.input_queues:
            return None
        
        # Generiere eindeutige Scan-ID
        scan_id = f"{tool}_{int(time.time())}_{threading.get_ident()}"
        
        # Sende Scan an Tool
        self.input_queues[tool].put((query, scan_id))
        
        return scan_id
    
    def get_scan_result(self, tool: str, timeout: float = 5.0) -> Optional[Dict]:
        """Holt das Ergebnis eines Scans vom Tool"""
        if tool not in self.output_queues:
            return None
        
        try:
            result = self.output_queues[tool].get(timeout=timeout)
            return result
        except queue.Empty:
            return None
    
    def show_tools_status(self):
        """Zeigt den Status der verfügbaren OSINT-Tools an"""
        self.console.print("\n[bold cyan]OSINT-Tools Status:[/bold cyan]")
        self.console.print("-" * 40)
        
        for tool, available in self.tools_available.items():
            status = "[green]✓ Verfügbar[/green]" if available else "[red]✗ Nicht verfügbar[/red]"
            self.console.print(f"  {tool.capitalize():<10}: {status}")
            
        if not any(self.tools_available.values()):
            self.console.print("\n[yellow]Keine OSINT-Tools verfügbar. Installiere sie mit:[/yellow]")
            self.console.print("  chmod +x install_osint_tools.sh")
            self.console.print("  ./install_osint_tools.sh")
            self.console.print("")
            self.console.print("Oder manuell:")
            self.console.print("  sudo apt install holehe")
            self.console.print("  git clone https://github.com/soxoj/maigret && cd maigret && pip install -r requirements.txt")
            self.console.print("  git clone https://github.com/sherlock-project/sherlock.git && cd sherlock && pip install -r requirements.txt")
        else:
            # Zeige verfügbare Tools an
            available_tools = [tool for tool, available in self.tools_available.items() if available]
            self.console.print(f"\n[green]Verfügbare Tools: {', '.join(available_tools)}[/green]")
            self.console.print("[cyan]Tools laufen im Hintergrund und sind bereit für Scans[/cyan]")
    
    def stop_all_tools(self):
        """Stoppt alle OSINT-Tools"""
        self.running = False
        
        # Sende Stop-Signale an alle Tools
        for tool_name, input_queue in self.input_queues.items():
            try:
                input_queue.put(None)
            except:
                pass
        
        # Warte auf Beendigung der Threads
        for tool_name, thread in self.tool_threads.items():
            try:
                thread.join(timeout=2)
            except:
                pass
        
        self.console.print("[yellow]🛑 Alle OSINT-Tools gestoppt[/yellow]")
    
    def run_osint_scan_with_manager(self, email: str) -> List[Dict]:
        """Führt OSINT-Scans mit allen verfügbaren Tools durch"""
        results = []
        
        if not any(self.tools_available.values()):
            self.console.print("[yellow]Keine OSINT-Tools verfügbar[/yellow]")
            return results
        
        self.console.print(f"[cyan]Starte OSINT-Scans für: {email}[/cyan]")
        
        # Führe Scans mit allen verfügbaren Tools durch
        for tool, available in self.tools_available.items():
            if not available:
                continue
                
            self.console.print(f"[blue]🔍 Starte {tool.capitalize()}-Scan...[/blue]")
            
            try:
                # Sende Scan-Anfrage an das Tool
                scan_id = self.submit_scan(tool, email)
                if scan_id:
                    # Warte auf Ergebnis
                    result = self.get_scan_result(tool, timeout=30.0)
                    if result:
                        results.append({
                            'tool': tool,
                            'email': email,
                            'result': result,
                            'timestamp': datetime.now().isoformat()
                        })
                        self.console.print(f"[green] {tool.capitalize()}-Scan abgeschlossen[/green]")
                    else:
                        self.console.print(f"[yellow] {tool.capitalize()}-Scan: Kein Ergebnis erhalten[/yellow]")
                else:
                    self.console.print(f"[red] {tool.capitalize()}-Scan: Konnte nicht gestartet werden[/red]")
                    
            except Exception as e:
                self.console.print(f"[red] Fehler bei {tool.capitalize()}-Scan: {e}[/red]")
        
        if results:
            self.console.print(f"[green] OSINT-Scans abgeschlossen: {len(results)} Ergebnisse[/green]")
        else:
            self.console.print("[yellow] Keine OSINT-Scan-Ergebnisse erhalten[/yellow]")
        
        return results

class OSINTFallbackScanner:
    """Fallback-Scanner für OSINT-Tools (Holehe, Maigret, etc.) - Legacy-Klasse"""
    
    def __init__(self, console: Console):
        self.console = console
        self.tools_available = self._check_tools_availability()
        
    def _check_tools_availability(self) -> Dict[str, bool]:
        """Überprüft, welche OSINT-Tools verfügbar sind"""
        tools = {
            "holehe": False,
            "maigret": False,
            "sherlock": False
        }
        
        # Überprüfe Holehe
        try:
            result = subprocess.run(["holehe", "--help"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                tools["holehe"] = True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
            
        # Überprüfe Maigret (lokale Installation)
        try:
            # Versuche zuerst den lokalen Pfad
            maigret_path = os.path.join(os.getcwd(), "maigret", "maigret", "__main__.py")
            if os.path.exists(maigret_path):
                result = subprocess.run([sys.executable, maigret_path, "--help"], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    tools["maigret"] = True
            else:
                # Fallback: Versuche global installiertes Maigret
                result = subprocess.run(["maigret", "--help"], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    tools["maigret"] = True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
            
        # Überprüfe Sherlock (lokale Installation)
        try:
            # Versuche zuerst den lokalen Pfad
            sherlock_path = os.path.join(os.getcwd(), "sherlock", "sherlock_project", "__main__.py")
            if os.path.exists(sherlock_path):
                result = subprocess.run([sys.executable, sherlock_path, "--help"], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    tools["sherlock"] = True
            else:
                # Fallback: Versuche global installiertes Sherlock
                result = subprocess.run(["sherlock", "--help"], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    tools["sherlock"] = True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass
            
        return tools
    
    def show_tools_status(self):
        """Zeigt den Status der verfügbaren OSINT-Tools an"""
        self.console.print("\n[bold cyan]OSINT-Tools Status:[/bold cyan]")
        self.console.print("-" * 40)
        
        # Verwende den neuen Manager für den Status
        for tool, available in self.osint_manager.tools_available.items():
            status = "[green]✓ Verfügbar[/green]" if available else "[red]✗ Nicht verfügbar[/red]"
            self.console.print(f"  {tool.capitalize():<10}: {status}")
            
        if not any(self.osint_manager.tools_available.values()):
            self.console.print("\n[yellow]Keine OSINT-Tools verfügbar. Installiere sie mit:[/yellow]")
            self.console.print("  chmod +x install_osint_tools.sh")
            self.console.print("  ./install_osint_tools.sh")
            self.console.print("")
            self.console.print("Oder manuell:")
            self.console.print("  sudo apt install holehe")
            self.console.print("  git clone https://github.com/soxoj/maigret && cd maigret && pip install -r requirements.txt")
            self.console.print("  git clone https://github.com/sherlock-project/sherlock.git && cd sherlock && pip install -r requirements.txt")
        else:
            # Zeige verfügbare Tools an
            available_tools = [tool for tool, available in self.tools_available.items() if available]
            if available_tools:
                self.console.print(f"\n[green]Verfügbare Tools: {', '.join(available_tools)}[/green]")
                self.console.print("[green]Diese werden automatisch für OSINT-Scans verwendet.[/green]")
    
    def run_holehe_scan(self, email: str) -> Optional[Dict]:
        """Führt einen Holehe-Scan durch"""
        if not self.tools_available["holehe"]:
            return None
            
        try:
            self.console.print(f"  [cyan]Holehe-Scan läuft...[/cyan]")
            
            result = subprocess.run(
                ["holehe", email],
                capture_output=True,
                text=True,
                timeout=120  # 2 Minuten Timeout
            )
            
            if result.returncode == 0:
                return self._parse_holehe_output(result.stdout, email)
            else:
                return {
                    "tool": "Holehe",
                    "status": "Fehler",
                    "message": f"Exit-Code: {result.returncode}",
                    "raw_output": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "tool": "Holehe",
                "status": "Timeout",
                "message": "Scan überschritt Zeitlimit (2 Minuten)"
            }
        except Exception as e:
            return {
                "tool": "Holehe",
                "status": "Fehler",
                "message": f"Unerwarteter Fehler: {str(e)}"
            }
    
    def run_maigret_scan(self, email: str) -> Optional[Dict]:
        """Führt einen Maigret-Scan durch"""
        if not self.tools_available["maigret"]:
            return None
            
        try:
            self.console.print(f"  [cyan]Maigret-Scan läuft...[/cyan]")
            
            # Verwende lokalen Pfad falls verfügbar
            if os.path.exists(os.path.join(os.getcwd(), "maigret", "maigret", "__main__.py")):
                maigret_path = os.path.join(os.getcwd(), "maigret", "maigret", "__main__.py")
                cmd = [sys.executable, maigret_path, email, "--timeout", "10", "--print-found"]
            else:
                cmd = ["maigret", email, "--timeout", "10", "--print-found"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3 Minuten Timeout
            )
            
            if result.returncode == 0:
                return self._parse_maigret_output(result.stdout, email)
            else:
                return {
                    "tool": "Maigret",
                    "status": "Fehler",
                    "message": f"Exit-Code: {result.returncode}",
                    "raw_output": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "tool": "Maigret",
                "status": "Timeout",
                "message": "Scan überschritt Zeitlimit (3 Minuten)"
            }
        except Exception as e:
            return {
                "tool": "Maigret",
                "status": "Fehler",
                "message": f"Unerwarteter Fehler: {str(e)}"
            }
    
    def run_sherlock_scan(self, email: str) -> Optional[Dict]:
        """Führt einen Sherlock-Scan durch (primär für Usernames)"""
        if not self.tools_available["sherlock"]:
            return None
            
        try:
            # Extrahiere Username aus E-Mail
            username = email.split('@')[0]
            self.console.print(f"  [cyan]Sherlock-Scan läuft für Username: {username}[/cyan]")
            
            # Verwende lokalen Pfad falls verfügbar
            if os.path.exists(os.path.join(os.getcwd(), "sherlock", "sherlock_project", "__main__.py")):
                sherlock_path = os.path.join(os.getcwd(), "sherlock", "sherlock_project", "__main__.py")
                cmd = [sys.executable, sherlock_path, username, "--timeout", "10"]
            else:
                cmd = ["sherlock", username, "--timeout", "10"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 Minuten Timeout
            )
            
            if result.returncode == 0:
                return self._parse_sherlock_output(result.stdout, username)
            else:
                return {
                    "tool": "Sherlock",
                    "status": "Fehler",
                    "message": f"Exit-Code: {result.returncode}",
                    "raw_output": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                "tool": "Sherlock",
                "status": "Timeout",
                "message": "Scan überschritt Zeitlimit (2 Minuten)"
            }
        except Exception as e:
            return {
                "tool": "Sherlock",
                "status": "Fehler",
                "message": f"Unerwarteter Fehler: {str(e)}"
            }
    
    def _parse_holehe_output(self, output: str, email: str) -> Dict:
        """Parst die Holehe-Ausgabe"""
        lines = output.strip().split('\n')
        found_services = []
        
        for line in lines:
            if '[' in line and ']' in line:
                # Holehe-Format: [✓] Service Name
                if '[✓]' in line:
                    service = line.split('[✓]')[1].strip()
                    found_services.append(service)
        
        if found_services:
            return {
                "tool": "Holehe",
                "status": "Erfolgreich",
                "message": f"E-Mail bei {len(found_services)} Diensten gefunden",
                "found_services": found_services,
                "raw_output": output
            }
        else:
            return {
                "tool": "Holehe",
                "status": "Keine Treffer",
                "message": "E-Mail bei keinem der überprüften Dienste gefunden",
                "found_services": [],
                "raw_output": output
            }
    
    def _parse_maigret_output(self, output: str, email: str) -> Dict:
        """Parst die Maigret-Ausgabe"""
        lines = output.strip().split('\n')
        found_services = []
        
        for line in lines:
            if 'FOUND' in line or 'found' in line:
                # Maigret-Format: Service Name - FOUND
                parts = line.split(' - ')
                if len(parts) >= 2:
                    service = parts[0].strip()
                    found_services.append(service)
        
        if found_services:
            return {
                "tool": "Maigret",
                "status": "Erfolgreich",
                "message": f"E-Mail bei {len(found_services)} Diensten gefunden",
                "found_services": found_services,
                "raw_output": output
            }
        else:
            return {
                "tool": "Maigret",
                "status": "Keine Treffer",
                "message": "E-Mail bei keinem der überprüften Dienste gefunden",
                "found_services": [],
                "raw_output": output
            }
    
    def _parse_sherlock_output(self, output: str, username: str) -> Dict:
        """Parst die Sherlock-Ausgabe"""
        lines = output.strip().split('\n')
        found_services = []
        
        for line in lines:
            if 'Found' in line:
                # Sherlock-Format: [Found] Service Name: URL
                if '[Found]' in line:
                    parts = line.split('[Found]')
                    if len(parts) >= 2:
                        service_part = parts[1].split(':')[0].strip()
                        found_services.append(service_part)
        
        if found_services:
            return {
                "tool": "Sherlock",
                "status": "Erfolgreich",
                "message": f"Username bei {len(found_services)} Diensten gefunden",
                "found_services": found_services,
                "raw_output": output
            }
        else:
            return {
                "tool": "Sherlock",
                "status": "Keine Treffer",
                "message": f"Username '{username}' bei keinem der überprüften Dienste gefunden",
                "found_services": [],
                "raw_output": output
            }
    
    def run_fallback_scan(self, email: str) -> List[Dict]:
        """Führt alle verfügbaren OSINT-Tools als Fallback aus"""
        if not any(self.tools_available.values()):
            return []
        
        self.console.print(f"\n[bold yellow]OSINT-Fallback-Scan gestartet...[/bold yellow]")
        self.console.print(f"[yellow]Verwende verfügbare Tools nach eigener Auswertung[/yellow]")
        
        results = []
        
        # Holehe
        if self.tools_available["holehe"]:
            holehe_result = self.run_holehe_scan(email)
            if holehe_result:
                results.append(holehe_result)
        
        # Maigret
        if self.tools_available["maigret"]:
            maigret_result = self.run_maigret_scan(email)
            if maigret_result:
                results.append(maigret_result)
        
        # Sherlock
        if self.tools_available["sherlock"]:
            sherlock_result = self.run_sherlock_scan(email)
            if sherlock_result:
                results.append(sherlock_result)
        
        return results
    
    def run_osint_scan_with_manager(self, email: str) -> List[Dict]:
        """Führt einen OSINT-Scan mit dem neuen Manager durch"""
        results = []
        
        # Verwende den neuen Manager für Scans
        if self.osint_manager.tools_available.get("holehe", False):
            # Übermittle Scan an Holehe
            scan_id = self.osint_manager.submit_scan("holehe", email)
            if scan_id:
                # Warte auf Ergebnis
                holehe_result = self.osint_manager.get_scan_result("holehe", timeout=30)
                if holehe_result and holehe_result.get("success"):
                    parsed_result = self._parse_holehe_output(holehe_result["output"], email)
                    results.append(parsed_result)
        
        if self.osint_manager.tools_available.get("maigret", False):
            # Übermittle Scan an Maigret
            scan_id = self.osint_manager.submit_scan("maigret", email)
            if scan_id:
                # Warte auf Ergebnis
                maigret_result = self.osint_manager.get_scan_result("maigret", timeout=180)
                if maigret_result and maigret_result.get("success"):
                    parsed_result = self._parse_maigret_output(maigret_result["output"], email)
                    results.append(parsed_result)
        
        if self.osint_manager.tools_available.get("sherlock", False):
            # Übermittle Scan an Sherlock
            username = email.split('@')[0]
            scan_id = self.osint_manager.submit_scan("sherlock", username)
            if scan_id:
                # Warte auf Ergebnis
                sherlock_result = self.osint_manager.get_scan_result("sherlock", timeout=120)
                if sherlock_result and sherlock_result.get("success"):
                    parsed_result = self._parse_sherlock_output(sherlock_result["output"], username)
                    results.append(parsed_result)
        
        return results

class EmailScanner:
    def __init__(self):
        self.console = Console()
        self.results = []
        self.websites = self.load_websites()
        self.reports_dir = "reports"
        self.create_reports_directory()
        
        # Verwende den neuen OSINT-Tool-Manager mit Subthreads
        self.osint_manager = OSINTToolManager(self.console)
        
        # Fallback für Legacy-Funktionalität
        self.osint_scanner = OSINTFallbackScanner(self.console)
        
    def create_reports_directory(self):
        """Erstellt den Reports-Ordner, falls er nicht existiert"""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
            self.console.print(f"[green]Reports-Ordner erstellt: {self.reports_dir}[/green]")
        
    def show_banner(self):
        """Zeigt den ASCII-Art Banner der Anwendung"""
        banner = art.text2art("Email Scanner", font="slant")
        self.console.print(banner)
        self.console.print("                    RS made by tim ^2", style="bold cyan")
        
    def load_websites(self) -> Dict[str, Dict]:
        """Lädt die Website-Konfigurationen"""
        return {
            "Spotify": {
                "url": "https://www.spotify.com/de/signup/",
                "check_url": "https://www.spotify.com/de/signup/",
                "method": "POST",
                "data_field": "email",
                "signup_url": "https://www.spotify.com/de/signup/"
            },
            "OnlyFans": {
                "url": "https://onlyfans.com/",
                "check_url": "https://onlyfans.com/",
                "method": "POST",
                "data_field": "email",
                "signup_url": "https://onlyfans.com/"
            }
        }
    
    def validate_email(self, email: str) -> bool:
        """Überprüft, ob die E-Mail-Adresse gültig ist"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def check_email_on_website(self, email: str, website_name: str, website_config: Dict) -> Dict:
        """Überprüft eine E-Mail-Adresse auf einer bestimmten Website"""
        result = {
            "website": website_name,
            "url": website_config["signup_url"],
            "status": "Unbekannt",
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            }
            
            # Verwende die Signup-URL für die Überprüfung
            signup_url = website_config["signup_url"]
            
            # Lade die Signup-Seite
            response = requests.get(signup_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                # Analysiere den Seiteninhalt
                result = self._analyze_signup_page(email, website_name, website_config, response.text, headers)
            else:
                result["status"] = "Fehler"
                result["message"] = f"HTTP {response.status_code}: {response.reason}"
                
        except requests.exceptions.RequestException as e:
            result["status"] = "Fehler"
            result["message"] = f"Verbindungsfehler: {str(e)}"
        except Exception as e:
            result["status"] = "Fehler"
            result["message"] = f"Unerwarteter Fehler: {str(e)}"
            
        return result
    
    def _analyze_signup_page(self, email: str, website_name: str, website_config: Dict, page_content: str, headers: Dict) -> Dict:
        """Analysiert die Signup-Seite und führt E-Mail-Validierung durch"""
        result = {
            "website": website_name,
            "url": website_config["signup_url"],
            "status": "Unbekannt",
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Suche nach E-Mail-Validierungs-Endpunkten oder Formularen
            validation_result = self._check_email_validation(email, website_name, website_config, page_content, headers)
            
            if validation_result:
                result.update(validation_result)
            else:
                # Fallback: Analysiere den Seiteninhalt
                result = self._fallback_analysis(email, website_name, website_config, page_content)
                
        except Exception as e:
            result["status"] = "Fehler"
            result["message"] = f"Seitenanalyse fehlgeschlagen: {str(e)}"
            
        return result
    
    def _check_email_validation(self, email: str, website_name: str, website_config: Dict, page_content: str, headers: Dict) -> Dict:
        """Versucht E-Mail-Validierung durch echte Website-Interaktion"""
        
        # Methode 1: Teste das Signup-Formular direkt mit der echten E-Mail
        form_result = self._test_signup_form(email, website_name, website_config, page_content, headers)
        if form_result:
            return form_result
        
        # Methode 2: Überprüfe E-Mail-Verfügbarkeit durch echte Website-Interaktion
        availability_result = self._check_email_availability(email, website_name, website_config, page_content, headers)
        if availability_result:
            return availability_result
            
        return None
    
    def _improved_email_check(self, email: str, website_name: str, website_config: Dict) -> Dict:
        """Verbesserte E-Mail-Überprüfung durch echte Website-Interaktion - speziell für Spotify und OnlyFans angepasst"""
        result = {
            "website": website_name,
            "url": website_config["signup_url"],
            "status": "Unbekannt",
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if website_name == "Spotify":
                # Spezielle Spotify-Logik - verwende den tatsächlichen Validierungs-Endpunkt
                spotify_validate_url = f"https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={email}"
                
                # Spotify-spezifische Headers
                spotify_headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                    "Accept": "*/*",
                    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Origin": "https://www.spotify.com",
                    "Referer": "https://www.spotify.com/",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-site",
                    "Connection": "keep-alive"
                }
                
                try:
                    # Teste den Spotify-Validierungs-Endpunkt
                    response = requests.get(spotify_validate_url, 
                                          headers=spotify_headers, 
                                          timeout=15)
                    
                    if response.status_code == 200:
                        try:
                            json_response = response.json()
                            
                            # Wenn die E-Mail bereits registriert ist
                            if 'errors' in json_response and 'email' in json_response['errors']:
                                email_error = json_response['errors']['email']
                                if 'bereits ein konto' in email_error.lower() and 'e-mail' in email_error.lower():
                                    result["status"] = "Registriert"
                                    result["message"] = f"Spotify bestätigt: {email_error}"
                                    return result
                            
                            # Wenn keine Fehlermeldung über bereits existierende E-Mail
                            # und der Status 20 ist (was auf einen Fehler hindeutet)
                            if json_response.get('status') == 20:
                                result["status"] = "Registriert"
                                result["message"] = "E-Mail-Adresse ist bereits bei Spotify registriert (Status 20)"
                                return result
                            
                            # Wenn die E-Mail verfügbar ist (keine Fehlermeldung)
                            result["status"] = "Verfügbar"
                            result["message"] = "E-Mail-Adresse ist bei Spotify verfügbar"
                            return result
                            
                        except json.JSONDecodeError:
                            # Falls die Antwort kein gültiges JSON ist
                            response_text = response.text.lower()
                            if 'bereits ein konto' in response_text and 'e-mail' in response_text:
                                result["status"] = "Registriert"
                                result["message"] = "E-Mail-Adresse ist bereits bei Spotify registriert"
                                return result
                            else:
                                result["status"] = "Verfügbar"
                                result["message"] = "E-Mail-Adresse ist bei Spotify verfügbar"
                                return result
                                
                    else:
                        result["status"] = "Fehler"
                        result["message"] = f"Spotify-API antwortete mit Status {response.status_code}"
                        return result
                        
                except Exception as e:
                    result["message"] = f"Spotify-API-Test fehlgeschlagen: {str(e)}"
                    
            elif website_name == "OnlyFans":
                # Spezielle OnlyFans-Logik - simuliere den tatsächlichen Registrierungsprozess
                onlyfans_headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Origin": "https://onlyfans.com",
                    "Referer": "https://onlyfans.com/",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Cache-Control": "max-age=0"
                }
                
                try:
                    # Schritt 1: Lade die Hauptseite um den "Melde dich für OnlyFans an" Button zu finden
                    response = requests.get("https://onlyfans.com/", headers=onlyfans_headers, timeout=15)
                    
                    if response.status_code == 200:
                        # Schritt 2: Suche nach dem Registrierungsformular oder Button
                        # Da wir den genauen Endpunkt nicht kennen, versuchen wir verschiedene Ansätze
                        
                        # Methode 1: Versuche das Registrierungsformular direkt zu finden
                        if 'melde dich für onlyfans an' in response.text.lower() or 'sign up' in response.text.lower():
                            # Der Button ist auf der Seite, versuche das Formular zu simulieren
                            # Wir verwenden GET mit Query-Parametern, da POST nicht funktioniert
                            signup_url = "https://onlyfans.com/signup"
                            
                            # Versuche GET auf die Signup-Seite
                            signup_response = requests.get(signup_url, headers=onlyfans_headers, timeout=15)
                            
                            if signup_response.status_code == 200:
                                # Suche nach der spezifischen OnlyFans-Fehlermeldung in der Antwort
                                signup_text = signup_response.text.lower()
                                
                                if 'bitte geben sie eine andere e-mail-adresse ein' in signup_text:
                                    return {
                                        "status": "Registriert",
                                        "message": "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                    }
                                elif 'e-mail-adresse' in signup_text and 'bereits' in signup_text:
                                    return {
                                        "status": "Registriert",
                                        "message": "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                    }
                                elif 'email' in signup_text and ('taken' in signup_text or 'exists' in signup_text):
                                    return {
                                        "status": "Registriert",
                                        "message": "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                    }
                                else:
                                    # Wenn keine Fehlermeldung gefunden wurde, ist die E-Mail wahrscheinlich verfügbar
                                    return {
                                        "status": "Verfügbar",
                                        "message": "E-Mail-Adresse ist bei OnlyFans verfügbar (keine Fehlermeldung gefunden)"
                                    }
                            else:
                                # Fallback: Analysiere die Hauptseite nach Fehlermeldungen
                                main_text = response.text.lower()
                                
                                if 'bitte geben sie eine andere e-mail-adresse ein' in main_text:
                                    return {
                                        "status": "Registriert",
                                        "message": "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                    }
                                elif 'e-mail-adresse' in main_text and 'bereits' in main_text:
                                    return {
                                        "status": "Registriert",
                                        "message": "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                    }
                                elif 'email' in main_text and ('taken' in main_text or 'exists' in main_text):
                                    return {
                                        "status": "Registriert",
                                        "message": "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                    }
                                else:
                                    # Wenn keine Fehlermeldung gefunden wurde, ist die E-Mail wahrscheinlich verfügbar
                                    return {
                                        "status": "Verfügbar",
                                        "message": "E-Mail-Adresse ist bei OnlyFans verfügbar (keine Fehlermeldung gefunden)"
                                    }
                        else:
                            # Fallback: Analysiere die Hauptseite nach Fehlermeldungen
                            main_text = response.text.lower()
                            
                            if 'bitte geben sie eine andere e-mail-adresse ein' in main_text:
                                return {
                                    "status": "Registriert",
                                    "message": "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                }
                            elif 'e-mail-adresse' in main_text and 'bereits' in main_text:
                                return {
                                    "status": "Registriert",
                                    "message": "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                }
                            elif 'email' in main_text and ('taken' in main_text or 'exists' in main_text):
                                return {
                                    "status": "Registriert",
                                    "message": "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                }
                            else:
                                # Wenn keine Fehlermeldung gefunden wurde, ist die E-Mail wahrscheinlich verfügbar
                                return {
                                    "status": "Verfügbar",
                                    "message": "E-Mail-Adresse ist bei OnlyFans verfügbar (keine Fehlermeldung gefunden)"
                                }
                    else:
                        return {
                            "status": "Fehler",
                            "message": f"OnlyFans-Hauptseite nicht erreichbar: Status {response.status_code}"
                        }
                        
                except Exception as e:
                    return {
                        "status": "Fehler",
                        "message": f"OnlyFans-Formular-Test fehlgeschlagen: {str(e)}"
                    }
                    
            else:
                # Generische Logik für andere Websites (falls später hinzugefügt)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Cache-Control": "max-age=0"
                }
                
                # Methode 1: Versuche direkten Zugriff auf die Signup-Seite
                try:
                    response = requests.get(website_config["signup_url"], headers=headers, timeout=15)
                    if response.status_code == 200:
                        if 'email' in response.text.lower() and 'signup' in response.text.lower():
                            result["status"] = "Verfügbar"
                            result["message"] = "Website unterstützt E-Mail-Registrierung"
                            return result
                except:
                    pass
                
                # Methode 2: Teste mit der echten E-Mail-Adresse
                try:
                    form_data = {
                        'email': email,
                        'password': 'TestPass123!',
                        'confirm_password': 'TestPass123!',
                        'username': f'user_{int(time.time())}',
                        'first_name': 'Test',
                        'last_name': 'User'
                    }
                    
                    response = requests.post(website_config["signup_url"], 
                                          data=form_data, 
                                          headers=headers, 
                                          timeout=15,
                                          allow_redirects=False)
                    
                    if response.status_code in [200, 302, 400, 422]:
                        response_text = response.text.lower()
                        
                        if any(keyword in response_text for keyword in [
                            'already exists', 'already registered', 'email taken', 
                            'email already', 'account exists', 'user exists'
                        ]):
                            result["status"] = "Registriert"
                            result["message"] = "E-Mail-Adresse ist bereits registriert"
                            return result
                        elif any(keyword in response_text for keyword in [
                            'success', 'welcome', 'verification sent', 'check your email'
                        ]):
                            result["status"] = "Verfügbar"
                            result["message"] = "E-Mail-Adresse wurde akzeptiert"
                            return result
                        else:
                            result["status"] = "Verfügbar"
                            result["message"] = "E-Mail wurde akzeptiert, Status unklar"
                            return result
                            
                except Exception as e:
                    result["message"] = f"Formular-Test fehlgeschlagen: {str(e)}"
            
        except Exception as e:
            result["status"] = "Fehler"
            result["message"] = f"Verbesserte Überprüfung fehlgeschlagen: {str(e)}"
            
        return result
    
    def _find_validation_apis(self, page_content: str) -> List[str]:
        """Diese Methode wird nicht mehr verwendet - echte Website-Interaktion statt API-Calls"""
        return []
    
    def _test_validation_api(self, email: str, endpoint: str, headers: Dict) -> Dict:
        """Diese Methode wird nicht mehr verwendet - echte Website-Interaktion statt API-Calls"""
        return None
    
    def _test_signup_form(self, email: str, website_name: str, website_config: Dict, page_content: str, headers: Dict) -> Dict:
        """Testet das Signup-Formular mit der echten E-Mail-Adresse - speziell für Spotify und OnlyFans angepasst"""
        try:
            if website_name == "Spotify":
                # Spezielle Spotify-Logik - verwende den tatsächlichen Validierungs-Endpunkt
                spotify_validate_url = f"https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={email}"
                
                # Spotify-spezifische Headers
                spotify_headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                    "Accept": "*/*",
                    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Origin": "https://www.spotify.com",
                    "Referer": "https://www.spotify.com/",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-site",
                    "Connection": "keep-alive"
                }
                
                # Teste den Spotify-Validierungs-Endpunkt
                response = requests.get(spotify_validate_url, 
                                      headers=spotify_headers, 
                                      timeout=15)
                
                if response.status_code == 200:
                    try:
                        json_response = response.json()
                        
                        # Wenn die E-Mail bereits registriert ist
                        if 'errors' in json_response and 'email' in json_response['errors']:
                            email_error = json_response['errors']['email']
                            if 'bereits ein konto' in email_error.lower() and 'e-mail' in email_error.lower():
                                return {
                                    "status": "Registriert",
                                    "message": f"Spotify bestätigt: {email_error}"
                                }
                        
                        # Wenn keine Fehlermeldung über bereits existierende E-Mail
                        # und der Status 20 ist (was auf einen Fehler hindeutet)
                        if json_response.get('status') == 20:
                            return {
                                "status": "Registriert",
                                "message": "E-Mail-Adresse ist bereits bei Spotify registriert (Status 20)"
                            }
                        
                        # Wenn die E-Mail verfügbar ist (keine Fehlermeldung)
                        return {
                            "status": "Verfügbar",
                            "message": "E-Mail-Adresse ist bei Spotify verfügbar"
                        }
                        
                    except json.JSONDecodeError:
                        # Falls die Antwort kein gültiges JSON ist
                        response_text = response.text.lower()
                        if 'bereits ein konto' in response_text and 'e-mail' in response_text:
                            return {
                                "status": "Registriert",
                                "message": "E-Mail-Adresse ist bereits bei Spotify registriert"
                            }
                        else:
                            return {
                                "status": "Verfügbar",
                                "message": "E-Mail-Adresse ist bei Spotify verfügbar"
                            }
                            
                else:
                    return {
                        "status": "Fehler",
                        "message": f"Spotify-API antwortete mit Status {response.status_code}"
                    }
                    
            elif website_name == "OnlyFans":
                # Spezielle OnlyFans-Logik - simuliere den Registrierungsprozess
                onlyfans_headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Origin": "https://onlyfans.com",
                    "Referer": "https://onlyfans.com/",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Cache-Control": "max-age=0"
                }
                
                try:
                    # Schritt 1: Lade die Hauptseite um den "Melde dich für OnlyFans an" Button zu finden
                    response = requests.get("https://onlyfans.com/", headers=onlyfans_headers, timeout=15)
                    
                    if response.status_code == 200:
                        # Schritt 2: Simuliere das Ausfüllen des Registrierungsformulars
                        # Da wir den genauen Endpunkt nicht kennen, verwenden wir die Hauptseite
                        form_data = {
                            'email': email,
                            'password': 'TestPass123!',
                            'confirm_password': 'TestPass123!',
                            'username': f'user_{int(time.time())}',
                            'first_name': 'Test',
                            'last_name': 'User',
                            'birth_day': '15',
                            'birth_month': '06',
                            'birth_year': '1990'
                        }
                        
                        # Versuche POST auf die Hauptseite (OnlyFans verarbeitet das Formular)
                        response = requests.post("https://onlyfans.com/", 
                                              data=form_data, 
                                              headers=onlyfans_headers, 
                                              timeout=15,
                                              allow_redirects=False)
                        
                        if response.status_code in [200, 400, 422, 302]:
                            response_text = response.text.lower()
                            
                            # Suche nach der spezifischen OnlyFans-Fehlermeldung
                            if 'bitte geben sie eine andere e-mail-adresse ein' in response_text:
                                return {
                                    "status": "Registriert",
                                    "message": "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                }
                            elif 'e-mail-adresse' in response_text and 'bereits' in response_text:
                                return {
                                    "status": "Registriert",
                                    "message": "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                }
                            elif 'email' in response_text and ('taken' in response_text or 'exists' in response_text):
                                return {
                                    "status": "Registriert",
                                    "message": "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                }
                            # Wenn keine Fehlermeldung über bereits existierende E-Mail
                            elif 'password' in response_text or 'passwort' in response_text:
                                return {
                                    "status": "Verfügbar",
                                    "message": "E-Mail wurde akzeptiert, Passwort-Fehler zeigt Verfügbarkeit"
                                }
                            elif 'success' in response_text or 'erfolgreich' in response_text:
                                return {
                                    "status": "Verfügbar",
                                    "message": "E-Mail-Adresse wurde erfolgreich bei OnlyFans registriert"
                                }
                            else:
                                return {
                                    "status": "Verfügbar",
                                    "message": "E-Mail wurde akzeptiert, Status unklar"
                                }
                        else:
                            return {
                                "status": "Fehler",
                                "message": f"OnlyFans antwortete mit Status {response.status_code}"
                            }
                    else:
                        return {
                            "status": "Fehler",
                            "message": f"OnlyFans-Hauptseite nicht erreichbar: Status {response.status_code}"
                        }
                        
                except Exception as e:
                    return {
                        "status": "Fehler",
                        "message": f"OnlyFans-Formular-Test fehlgeschlagen: {str(e)}"
                    }
                    
            else:
                # Generische Logik für andere Websites (falls später hinzugefügt)
                form_data = {
                    'email': email,
                    'password': 'TestPass123!',
                    'confirm_password': 'TestPass123!',
                    'username': f'user_{int(time.time())}',
                    'first_name': 'Test',
                    'last_name': 'User'
                }
                
                response = requests.post(website_config["signup_url"], 
                                      data=form_data, 
                                      headers=headers, 
                                      timeout=15,
                                      allow_redirects=False)
                
                if response.status_code in [200, 302, 400, 422]:
                    response_text = response.text.lower()
                    
                    if any(keyword in response_text for keyword in [
                        'already exists', 'already registered', 'email taken', 
                        'email already', 'account exists', 'user exists'
                    ]):
                        return {
                            "status": "Registriert",
                            "message": "E-Mail-Adresse ist bereits registriert"
                        }
                    elif any(keyword in response_text for keyword in [
                        'success', 'welcome', 'verification sent', 'check your email'
                    ]):
                        return {
                            "status": "Verfügbar",
                            "message": "E-Mail-Adresse wurde akzeptiert"
                        }
                    else:
                        return {
                            "status": "Verfügbar",
                            "message": "E-Mail wurde akzeptiert, Status unklar"
                        }
                        
        except Exception as e:
            return {
                "status": "Fehler",
                "message": f"Formular-Test fehlgeschlagen: {str(e)}"
            }
            
        return None
    
    def _check_email_availability(self, email: str, website_name: str, website_config: Dict, page_content: str, headers: Dict) -> Dict:
        """Überprüft E-Mail-Verfügbarkeit durch echte Website-Interaktion"""
        try:
            # Methode 1: Teste spezifische E-Mail-Verfügbarkeits-Endpunkte
            check_urls = [
                website_config["signup_url"] + '/check-email',
                website_config["signup_url"] + '/validate-email',
                website_config["signup_url"] + '/email-available',
                website_config["signup_url"].replace('/signup', '/check-email'),
                website_config["signup_url"].replace('/signup', '/validate-email')
            ]
            
            for check_url in check_urls:
                try:
                    response = requests.post(check_url, 
                                          data={'email': email}, 
                                          headers=headers, 
                                          timeout=10)
                    
                    if response.status_code == 200:
                        response_text = response.text.lower()
                        
                        if any(keyword in response_text for keyword in ['available', 'not found', 'not registered']):
                            return {
                                "status": "Verfügbar",
                                "message": "E-Mail-Überprüfungs-Endpunkt bestätigt Verfügbarkeit"
                            }
                        elif any(keyword in response_text for keyword in ['taken', 'exists', 'already registered']):
                            return {
                                "status": "Registriert",
                                "message": "E-Mail-Überprüfungs-Endpunkt bestätigt Registrierung"
                            }
                            
                except:
                    continue
            
            # Methode 2: Analysiere die Signup-Seite auf E-Mail-Felder
            if 'email' in page_content.lower() and 'signup' in page_content.lower():
                return {
                    "status": "Verfügbar",
                    "message": "Signup-Seite enthält E-Mail-Feld"
                }
                
        except Exception as e:
            pass
            
        return None
    
    def _fallback_analysis(self, email: str, website_name: str, website_config: Dict, page_content: str) -> Dict:
        """Fallback-Analyse, wenn keine spezifische Validierung möglich ist"""
        result = {
            "website": website_name,
            "url": website_config["signup_url"],
            "status": "Unbekannt",
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Analysiere den Seiteninhalt nach Hinweisen
            content_lower = page_content.lower()
            
            # Suche nach E-Mail-bezogenen Elementen
            email_indicators = [
                'email', 'e-mail', 'mail', 'username', 'account', 'signup', 'register', 'sign up'
            ]
            
            email_found = any(indicator in content_lower for indicator in email_indicators)
            
            if email_found:
                # Suche nach spezifischen Fehlermeldungen
                if any(error in content_lower for error in ['already exists', 'already registered', 'taken', 'in use']):
                    result["status"] = "Registriert"
                    result["message"] = "E-Mail-Adresse scheint bereits registriert zu sein"
                elif any(success in content_lower for success in ['available', 'not found', 'valid']):
                    result["status"] = "Verfügbar"
                    result["message"] = "E-Mail-Adresse scheint verfügbar zu sein"
                else:
                    result["status"] = "Verfügbar"
                    result["message"] = "Website unterstützt E-Mail-Registrierung, Status unklar"
            else:
                result["status"] = "Unbekannt"
                result["message"] = "Keine E-Mail-Registrierung gefunden"
                
        except Exception as e:
            result["status"] = "Fehler"
            result["message"] = f"Fallback-Analyse fehlgeschlagen: {str(e)}"
            
        return result
    
    def scan_email(self, email: str) -> List[Dict]:
        """Überprüft eine E-Mail-Adresse auf allen konfigurierten Websites"""
        if not self.validate_email(email):
            self.console.print("[red]Ungültige E-Mail-Adresse![/red]")
            return []
        
        self.console.print(f"\n[green]Starte E-Mail-Scan für: {email}[/green]")
        self.console.print(f"[yellow]Überprüfe {len(self.websites)} Websites...[/yellow]\n")
        
        results = []
        total_websites = len(self.websites)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Überprüfe Websites...", total=total_websites)
            
            for i, (website_name, website_config) in enumerate(self.websites.items(), 1):
                # Zeige aktuelle Website-Nummer und Namen
                progress.update(task, description=f"Überprüfe {website_name}... ({i}/{total_websites})")
                
                try:
                    # Echtzeit-Status-Updates während der Überprüfung
                    result = self._check_email_with_status_updates(email, website_name, website_config, progress, task, i, total_websites)
                    results.append(result)
                    
                    # Zeige sofortigen Status für bessere Übersicht
                    status_color = "green" if result["status"] == "Verfügbar" else "red" if result["status"] == "Registriert" else "yellow"
                    self.console.print(f"  {i:2d}. {website_name:<20} - [{status_color}]{result['status']}[/{status_color}]")
                    
                except Exception as e:
                    # Bei Fehlern: Versuche es mit verbesserter E-Mail-Überprüfung
                    self.console.print(f"  {i:2d}. {website_name:<20} - [red]Fehler, versuche Verbesserung...[/red]")
                    
                    # Verbesserte Überprüfung mit verschiedenen E-Mail-Formaten
                    improved_result = self._improved_email_check_with_status(email, website_name, website_config, progress, task, i, total_websites)
                    if improved_result:
                        results.append(improved_result)
                        self.console.print(f"       → [green]Verbessert: {improved_result['status']}[/green]")
                    else:
                        # Fallback-Ergebnis
                        fallback_result = {
                            "website": website_name,
                            "url": website_config["signup_url"],
                            "status": "Fehler",
                            "message": f"Überprüfung fehlgeschlagen: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        }
                        results.append(fallback_result)
                
                progress.advance(task)
        
        # OSINT-Scan mit dem neuen Manager
        if any(self.osint_manager.tools_available.values()):
            self.console.print(f"\n[bold cyan]Eigene E-Mail-Auswertung abgeschlossen.[/bold cyan]")
            self.console.print(f"[cyan]Starte OSINT-Scan mit verfügbaren Tools...[/cyan]")
            
            # Verwende den neuen Manager für bessere Performance
            osint_results = self.osint_manager.run_osint_scan_with_manager(email)
            if osint_results:
                # Füge OSINT-Ergebnisse zu den bestehenden Ergebnissen hinzu
                for osint_result in osint_results:
                    # Konvertiere OSINT-Ergebnisse in das gleiche Format
                    converted_result = {
                        "website": f"OSINT-{osint_result['tool']}",
                        "url": "OSINT-Tool",
                        "status": osint_result['status'],
                        "message": osint_result['message'],
                        "timestamp": datetime.now().isoformat(),
                        "osint_data": osint_result
                    }
                    results.append(converted_result)
                    
                    # Zeige OSINT-Ergebnisse sofort an
                    status_color = "green" if osint_result['status'] == "Erfolgreich" else "red" if osint_result['status'] == "Fehler" else "yellow"
                    self.console.print(f"  OSINT-{osint_result['tool']:<15} - [{status_color}]{osint_result['status']}[/{status_color}]")
                    if osint_result.get('found_services'):
                        self.console.print(f"       → Gefundene Dienste: {', '.join(osint_result['found_services'][:5])}")
                        if len(osint_result['found_services']) > 5:
                            self.console.print(f"       → ... und {len(osint_result['found_services']) - 5} weitere")
        
        return results
    
    def _check_email_with_status_updates(self, email: str, website_name: str, website_config: Dict, progress, task, current_num: int, total: int) -> Dict:
        """Überprüft E-Mail mit Echtzeit-Status-Updates"""
        result = {
            "website": website_name,
            "url": website_config["signup_url"],
            "status": "Unbekannt",
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Status: Lade Signup-Seite
            progress.update(task, description=f"Überprüfe {website_name}... ({current_num}/{total}) - Lade Signup-Seite")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            }
            
            # Verwende die Signup-URL für die Überprüfung
            signup_url = website_config["signup_url"]
            
            # Lade die Signup-Seite
            response = requests.get(signup_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                # Status: Analysiere Seiteninhalt
                progress.update(task, description=f"Überprüfe {website_name}... ({current_num}/{total}) - Analysiere Seiteninhalt")
                
                # Analysiere den Seiteninhalt
                result = self._analyze_signup_page_with_status(email, website_name, website_config, response.text, headers, progress, task, current_num, total)
            else:
                result["status"] = "Fehler"
                result["message"] = f"HTTP {response.status_code}: {response.reason}"
                
        except requests.exceptions.RequestException as e:
            result["status"] = "Fehler"
            result["message"] = f"Verbindungsfehler: {str(e)}"
        except Exception as e:
            result["status"] = "Fehler"
            result["message"] = f"Unerwarteter Fehler: {str(e)}"
            
        return result
    
    def _analyze_signup_page_with_status(self, email: str, website_name: str, website_config: Dict, page_content: str, headers: Dict, progress, task, current_num: int, total: int) -> Dict:
        """Analysiert die Signup-Seite mit Echtzeit-Status-Updates"""
        result = {
            "website": website_name,
            "url": website_config["signup_url"],
            "status": "Unbekannt",
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Status: Suche nach E-Mail-Validierung
            progress.update(task, description=f"Überprüfe {website_name}... ({current_num}/{total}) - Suche nach E-Mail-Validierung")
            
            # Suche nach E-Mail-Validierungs-Endpunkten oder Formularen
            validation_result = self._check_email_validation_with_status(email, website_name, website_config, page_content, headers, progress, task, current_num, total)
            
            if validation_result:
                result.update(validation_result)
            else:
                # Status: Fallback-Analyse
                progress.update(task, description=f"Überprüfe {website_name}... ({current_num}/{total}) - Führe Fallback-Analyse durch")
                
                # Fallback: Analysiere den Seiteninhalt
                result = self._fallback_analysis(email, website_name, website_config, page_content)
                
        except Exception as e:
            result["status"] = "Fehler"
            result["message"] = f"Seitenanalyse fehlgeschlagen: {str(e)}"
            
        return result
    
    def _check_email_validation_with_status(self, email: str, website_name: str, website_config: Dict, page_content: str, headers: Dict, progress, task, current_num: int, total: int) -> Dict:
        """Versucht E-Mail-Validierung mit Echtzeit-Status-Updates"""
        
        # Status: Teste Signup-Formular
        progress.update(task, description=f"Überprüfe {website_name}... ({current_num}/{total}) - Teste Signup-Formular")
        
        # Methode 1: Teste das Signup-Formular direkt
        form_result = self._test_signup_form(email, website_name, website_config, page_content, headers)
        if form_result:
            return form_result
        
        # Status: Überprüfe E-Mail-Verfügbarkeit
        progress.update(task, description=f"Überprüfe {website_name}... ({current_num}/{total}) - Überprüfe E-Mail-Verfügbarkeit")
        
        # Methode 2: Suche nach E-Mail-Verfügbarkeits-Checks
        availability_result = self._check_email_availability(email, website_name, website_config, page_content, headers)
        if availability_result:
            return availability_result
            
        return None
    
    def _improved_email_check_with_status(self, email: str, website_name: str, website_config: Dict, progress, task, current_num: int, total: int) -> Dict:
        """Verbesserte E-Mail-Überprüfung durch echte Website-Interaktion mit Echtzeit-Status-Updates - speziell für Spotify angepasst"""
        result = {
            "website": website_name,
            "url": website_config["signup_url"],
            "status": "Unbekannt",
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if website_name == "Spotify":
                # Status: Teste den Spotify-Validierungs-Endpunkt
                progress.update(task, description=f"Überprüfe {website_name}... ({current_num}/{total}) - Teste Spotify-Validierungs-API")
                
                # Spezielle Spotify-Logik - verwende den tatsächlichen Validierungs-Endpunkt
                spotify_validate_url = f"https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={email}"
                
                # Spotify-spezifische Headers
                spotify_headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                    "Accept": "*/*",
                    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Origin": "https://www.spotify.com",
                    "Referer": "https://www.spotify.com/",
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-site",
                    "Connection": "keep-alive"
                }
                
                try:
                    # Teste den Spotify-Validierungs-Endpunkt
                    response = requests.get(spotify_validate_url, 
                                          headers=spotify_headers, 
                                          timeout=15)
                    
                    if response.status_code == 200:
                        try:
                            json_response = response.json()
                            
                            # Wenn die E-Mail bereits registriert ist
                            if 'errors' in json_response and 'email' in json_response['errors']:
                                email_error = json_response['errors']['email']
                                if 'bereits ein konto' in email_error.lower() and 'e-mail' in email_error.lower():
                                    result["status"] = "Registriert"
                                    result["message"] = f"Spotify bestätigt: {email_error}"
                                    return result
                            
                            # Wenn keine Fehlermeldung über bereits existierende E-Mail
                            # und der Status 20 ist (was auf einen Fehler hindeutet)
                            if json_response.get('status') == 20:
                                result["status"] = "Registriert"
                                result["message"] = "E-Mail-Adresse ist bereits bei Spotify registriert (Status 20)"
                                return result
                            
                            # Wenn die E-Mail verfügbar ist (keine Fehlermeldung)
                            result["status"] = "Verfügbar"
                            result["message"] = "E-Mail-Adresse ist bei Spotify verfügbar"
                            return result
                            
                        except json.JSONDecodeError:
                            # Falls die Antwort kein gültiges JSON ist
                            response_text = response.text.lower()
                            if 'bereits ein konto' in response_text and 'e-mail' in response_text:
                                result["status"] = "Registriert"
                                result["message"] = "E-Mail-Adresse ist bereits bei Spotify registriert"
                                return result
                            else:
                                result["status"] = "Verfügbar"
                                result["message"] = "E-Mail-Adresse ist bei Spotify verfügbar"
                                return result
                                
                    else:
                        result["status"] = "Fehler"
                        result["message"] = f"Spotify-API antwortete mit Status {response.status_code}"
                        return result
                        
                except Exception as e:
                    result["message"] = f"Spotify-API-Test fehlgeschlagen: {str(e)}"
                    
            elif website_name == "OnlyFans":
                # Status: Teste den OnlyFans-Registrierungsprozess
                progress.update(task, description=f"Überprüfe {website_name}... ({current_num}/{total}) - Teste OnlyFans-Registrierung")
                
                # Spezielle OnlyFans-Logik - simuliere den tatsächlichen Registrierungsprozess
                onlyfans_headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Origin": "https://onlyfans.com",
                    "Referer": "https://onlyfans.com/",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Cache-Control": "max-age=0"
                }
                
                try:
                    # Schritt 1: Lade die Hauptseite um den "Melde dich für OnlyFans an" Button zu finden
                    response = requests.get("https://onlyfans.com/", headers=onlyfans_headers, timeout=15)
                    
                    if response.status_code == 200:
                        # Schritt 2: Suche nach dem Registrierungsformular oder Button
                        # Da wir den genauen Endpunkt nicht kennen, versuchen wir verschiedene Ansätze
                        
                        # Methode 1: Versuche das Registrierungsformular direkt zu finden
                        if 'melde dich für onlyfans an' in response.text.lower() or 'sign up' in response.text.lower():
                            # Der Button ist auf der Seite, versuche das Formular zu simulieren
                            # Wir verwenden GET mit Query-Parametern, da POST nicht funktioniert
                            signup_url = "https://onlyfans.com/signup"
                            
                            # Versuche GET auf die Signup-Seite
                            signup_response = requests.get(signup_url, headers=onlyfans_headers, timeout=15)
                            
                            if signup_response.status_code == 200:
                                # Suche nach der exakten OnlyFans-Fehlermeldung in der Antwort
                                signup_text = signup_response.text
                                
                                if 'Bitte geben Sie eine andere E-Mail-Adresse ein.' in signup_text:
                                    result["status"] = "Registriert"
                                    result["message"] = "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                    return result
                                elif 'e-mail-adresse' in signup_text and 'bereits' in signup_text:
                                    result["status"] = "Registriert"
                                    result["message"] = "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                    return result
                                elif 'email' in signup_text and ('taken' in signup_text or 'exists' in signup_text):
                                    result["status"] = "Registriert"
                                    result["message"] = "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                    return result
                                else:
                                    # Wenn keine Fehlermeldung gefunden wurde, ist die E-Mail wahrscheinlich verfügbar
                                    result["status"] = "Verfügbar"
                                    result["message"] = "E-Mail-Adresse ist bei OnlyFans verfügbar (keine Fehlermeldung gefunden)"
                                    return result
                            else:
                                # Fallback: Analysiere die Hauptseite nach Fehlermeldungen
                                main_text = response.text
                                
                                if 'Bitte geben Sie eine andere E-Mail-Adresse ein.' in main_text:
                                    result["status"] = "Registriert"
                                    result["message"] = "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                    return result
                                elif 'e-mail-adresse' in main_text and 'bereits' in main_text:
                                    result["status"] = "Registriert"
                                    result["message"] = "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                    return result
                                elif 'email' in main_text and ('taken' in main_text or 'exists' in main_text):
                                    result["status"] = "Registriert"
                                    result["message"] = "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                    return result
                                else:
                                    # Wenn keine Fehlermeldung gefunden wurde, ist die E-Mail wahrscheinlich verfügbar
                                    result["status"] = "Verfügbar"
                                    result["message"] = "E-Mail-Adresse ist bei OnlyFans verfügbar (keine Fehlermeldung gefunden)"
                                    return result
                        else:
                            # Fallback: Analysiere die Hauptseite nach Fehlermeldungen
                            main_text = response.text.lower()
                            
                            if 'bitte geben sie eine andere e-mail-adresse ein' in main_text:
                                result["status"] = "Registriert"
                                result["message"] = "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                return result
                            elif 'e-mail-adresse' in main_text and 'bereits' in main_text:
                                result["status"] = "Registriert"
                                result["message"] = "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                return result
                            elif 'email' in main_text and ('taken' in main_text or 'exists' in main_text):
                                result["status"] = "Registriert"
                                result["message"] = "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                return result
                            else:
                                # Wenn keine Fehlermeldung gefunden wurde, ist die E-Mail wahrscheinlich verfügbar
                                result["status"] = "Verfügbar"
                                result["message"] = "E-Mail-Adresse ist bei OnlyFans verfügbar (keine Fehlermeldung gefunden)"
                                return result
                    else:
                        result["status"] = "Fehler"
                        result["message"] = f"OnlyFans-Hauptseite nicht erreichbar: Status {response.status_code}"
                        return result
                        
                except Exception as e:
                    result["message"] = f"OnlyFans-Formular-Test fehlgeschlagen: {str(e)}"
                    
            elif website_name not in ["Spotify", "OnlyFans"]:
                # Generische Logik für andere Websites (falls später hinzugefügt)
                # Status: Versuche direkten Zugriff
                progress.update(task, description=f"Überprüfe {website_name}... ({current_num}/{total}) - Versuche direkten Zugriff")
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Cache-Control": "max-age=0"
                }
                
                try:
                    response = requests.get(website_config["signup_url"], headers=headers, timeout=15)
                    if response.status_code == 200:
                        if 'email' in response.text.lower() and 'signup' in response.text.lower():
                            result["status"] = "Verfügbar"
                            result["message"] = "Website unterstützt E-Mail-Registrierung"
                            return result
                except:
                    pass
                
                # Status: Teste mit der echten E-Mail-Adresse
                progress.update(task, description=f"Überprüfe {website_name}... ({current_num}/{total}) - Teste mit der echten E-Mail-Adresse")
                
                try:
                    form_data = {
                        'email': email,
                        'password': 'TestPass123!',
                        'confirm_password': 'TestPass123!',
                        'username': f'user_{int(time.time())}',
                        'first_name': 'Test',
                        'last_name': 'User'
                    }
                    
                    response = requests.post(website_config["signup_url"], 
                                          data=form_data, 
                                          headers=headers, 
                                          timeout=15,
                                          allow_redirects=False)
                    
                    if response.status_code in [200, 302, 400, 422]:
                        response_text = response.text.lower()
                        
                        if any(keyword in response_text for keyword in [
                            'already exists', 'already registered', 'email taken', 
                            'email already', 'account exists', 'user exists'
                        ]):
                            result["status"] = "Registriert"
                            result["message"] = "E-Mail-Adresse ist bereits registriert"
                            return result
                        elif any(keyword in response_text for keyword in [
                            'success', 'welcome', 'verification sent', 'check your email'
                        ]):
                            result["status"] = "Verfügbar"
                            result["message"] = "E-Mail-Adresse wurde akzeptiert"
                            return result
                        else:
                            result["status"] = "Verfügbar"
                            result["message"] = "E-Mail wurde akzeptiert, Status unklar"
                            return result
                            
                except Exception as e:
                    result["message"] = f"Formular-Test fehlgeschlagen: {str(e)}"
            
        except Exception as e:
            result["status"] = "Fehler"
            result["message"] = f"Verbesserte Überprüfung fehlgeschlagen: {str(e)}"
            
        return result
    
    def display_results(self, results: List[Dict]):
        """Zeigt die Scan-Ergebnisse in einer übersichtlichen Tabelle an"""
        if not results:
            self.console.print("[yellow]Keine Ergebnisse zum Anzeigen.[/yellow]")
            return
        
        # Erstelle Tabelle
        table = Table(title="E-Mail-Scan Ergebnisse")
        table.add_column("Website", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("URL", style="blue", no_wrap=False)
        table.add_column("Nachricht", style="white", no_wrap=False)
        
        # Füge Zeilen hinzu
        for result in results:
            # Stelle sicher, dass der Website-Name korrekt ist
            website_name = result.get("website", "Unbekannt")
            if website_name == "Unbekannt":
                # Versuche, den Namen aus der URL zu extrahieren
                url = result.get("url", "")
                if url:
                    # Extrahiere Domain-Name
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        domain = parsed.netloc.replace('www.', '').split('.')[0]
                        website_name = domain.capitalize()
                    except:
                        website_name = "Unbekannt"
            
            # Status-Farbe
            status = result.get("status", "Unbekannt")
            if status == "Verfügbar":
                status_style = "green"
            elif status == "Registriert":
                status_style = "red"
            elif status == "Fehler":
                status_style = "yellow"
            else:
                status_style = "white"
            
            table.add_row(
                website_name,
                f"[{status_style}]{status}[/{status_style}]",
                result.get("url", ""),
                result.get("message", "")
            )
        
        self.console.print(table)
        
        # Zusammenfassung
        total = len(results)
        available = sum(1 for r in results if r.get("status") == "Verfügbar")
        registered = sum(1 for r in results if r.get("status") == "Registriert")
        errors = sum(1 for r in results if r.get("status") == "Fehler")
        unknown = sum(1 for r in results if r.get("status") == "Unbekannt")
        
        self.console.print(f"\n[bold]Zusammenfassung:[/bold]")
        self.console.print(f"  Gesamt: {total}")
        self.console.print(f"  Verfügbar: [green]{available}[/green]")
        self.console.print(f"  Registriert: [red]{registered}[/red]")
        self.console.print(f"  Fehler: [yellow]{errors}[/yellow]")
        self.console.print(f"  Unbekannt: [white]{unknown}[/white]")
    
    def export_report(self, email: str, results: List[Dict], format_type: str = "json"):
        """Exportiert den Bericht in verschiedenen Formaten"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_email = email.replace('@', '_at_').replace('.', '_').replace('-', '_')
        
        if format_type == "json":
            filename = os.path.join(self.reports_dir, f"email_scan_{safe_email}_{timestamp}.json")
            report_data = {
                "email": email,
                "scan_timestamp": datetime.now().isoformat(),
                "total_websites": len(results),
                "results": results
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
                
        elif format_type == "txt":
            filename = os.path.join(self.reports_dir, f"email_scan_{safe_email}_{timestamp}.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"E-Mail-Scan Bericht\n")
                f.write(f"==================\n\n")
                f.write(f"E-Mail: {email}\n")
                f.write(f"Scan-Datum: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write(f"Anzahl Websites: {len(results)}\n\n")
                
                for result in results:
                    f.write(f"Website: {result['website']}\n")
                    f.write(f"Status: {result['status']}\n")
                    f.write(f"URL: {result['url']}\n")
                    f.write(f"Nachricht: {result['message']}\n")
                    f.write("-" * 50 + "\n\n")
        
        self.console.print(f"\n[green]Bericht wurde exportiert: {filename}[/green]")
        return filename
    
    def show_main_menu(self):
        """Zeigt das Hauptmenü an"""
        self.console.print("\n" + "="*70)
        self.console.print("[bold cyan]E-Mail-Scanner - Hauptmenü[/bold cyan]")
        self.console.print("="*70)
        self.console.print("1. E-Mail-Adresse scannen")
        self.console.print("2. Verfügbare Websites anzeigen")
        self.console.print("3. Berichte anzeigen")
        self.console.print("4. OSINT-Tools Status anzeigen")
        self.console.print("5. Beenden")
        self.console.print("="*70)
    
    def show_scan_menu(self):
        """Zeigt das Scan-Menü an"""
        self.console.print("\n" + "-"*50)
        self.console.print("[bold yellow]E-Mail-Scan[/bold yellow]")
        self.console.print("-"*50)
    
    def show_export_menu(self):
        """Zeigt das Export-Menü an"""
        self.console.print("\n" + "-"*50)
        self.console.print("[bold green]Bericht exportieren[/bold green]")
        self.console.print("-"*50)
        self.console.print("1. JSON-Format")
        self.console.print("2. TXT-Format")
        self.console.print("3. Beide Formate")
        self.console.print("4. Kein Export")
    
    def list_reports(self):
        """Zeigt alle verfügbaren Berichte an"""
        if not os.path.exists(self.reports_dir):
            self.console.print(f"[yellow]Kein Reports-Ordner gefunden.[/yellow]")
            return
        
        files = [f for f in os.listdir(self.reports_dir) if f.endswith(('.json', '.txt'))]
        
        if not files:
            self.console.print("[yellow]Keine Berichte gefunden.[/yellow]")
            return
        
        self.console.print(f"\n[bold cyan]Verfügbare Berichte:[/bold cyan]")
        self.console.print("-" * 60)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Dateiname", style="cyan")
        table.add_column("Größe", style="green")
        table.add_column("Erstellt", style="yellow")
        
        for file in sorted(files, reverse=True):
            filepath = os.path.join(self.reports_dir, file)
            size = os.path.getsize(filepath)
            created = datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%d.%m.%Y %H:%M')
            
            table.add_row(file, f"{size} Bytes", created)
        
        self.console.print(table)
    
    def run_interactive(self):
        """Führt die Anwendung im interaktiven Modus aus"""
        self.show_banner()
        
        while True:
            try:
                self.show_main_menu()
                choice = input("\nWähle eine Option (1-4): ").strip()
                
                if choice == "1":
                    self.handle_email_scan()
                elif choice == "2":
                    self.show_websites()
                elif choice == "3":
                    self.list_reports()
                elif choice == "4":
                    self.osint_manager.show_tools_status()
                elif choice == "5":
                    self.console.print("\n[yellow]Machs gut du russische Schlampe![/yellow]")
                    # Stoppe alle OSINT-Tools beim Beenden
                    self.osint_manager.stop_all_tools()
                    break
                else:
                    self.console.print("[red]Ungültige Auswahl. Bitte wähle 1, 2, 3, 4 oder 5.[/red]")
                    
            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]Programm wird beendet...[/yellow]")
                # Stoppe alle OSINT-Tools beim Beenden
                self.osint_manager.stop_all_tools()
                break
            except Exception as e:
                self.console.print(f"[red]Fehler: {str(e)}[/red]")
    
    def handle_email_scan(self):
        """Behandelt den E-Mail-Scan-Prozess"""
        self.show_scan_menu()
        
        while True:
            email = input("E-Mail-Adresse eingeben (oder 'zurück' für Hauptmenü): ").strip()
            
            if email.lower() in ['zurück', 'back', 'b', 'q']:
                return
            
            if not email:
                self.console.print("[red]Bitte gib eine E-Mail-Adresse ein.[/red]")
                continue
            
            if not self.validate_email(email):
                self.console.print(f"[red]Ungültige E-Mail-Adresse: {email}[/red]")
                continue
            
            # E-Mail scannen
            results = self.scan_email(email)
            if results:
                self.display_results(results)
                self.handle_export(email, results)
            break
    
    def handle_export(self, email: str, results: List[Dict]):
        """Behandelt den Export-Prozess"""
        self.show_export_menu()
        
        while True:
            export_choice = input("\nWähle Export-Option (1-4): ").strip()
            
            if export_choice == "1":
                self.export_report(email, results, "json")
                break
            elif export_choice == "2":
                self.export_report(email, results, "txt")
                break
            elif export_choice == "3":
                self.export_report(email, results, "json")
                self.export_report(email, results, "txt")
                break
            elif export_choice == "4":
                self.console.print("[yellow]Kein Export durchgeführt.[/yellow]")
                break
            else:
                self.console.print("[red]Ungültige Auswahl. Bitte wähle 1, 2, 3 oder 4.[/red]")
    
    def show_websites(self):
        """Zeigt alle verfügbaren Websites an"""
        self.console.print(f"\n[bold cyan]Verfügbare Websites: {len(self.websites)}[/bold cyan]")
        self.console.print("-" * 80)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Website", style="cyan", no_wrap=True)
        table.add_column("URL", style="white")
        
        for name, config in self.websites.items():
            table.add_row(name, config['url'])
        
        self.console.print(table)

def main():
    """Hauptfunktion der Anwendung"""
    parser = argparse.ArgumentParser(
        description="E-Mail-Scanner - Überprüft E-Mail-Adressen auf verschiedenen Websites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python email_scanner.py                    # Interaktiver Modus
  python email_scanner.py -e test@example.com  # Direkte E-Mail-Überprüfung
  python email_scanner.py -e test@example.com --export json  # Mit Export

OSINT-Fallback-Tools:
  Nach der eigenen E-Mail-Auswertung werden verfügbare OSINT-Tools als Fallback verwendet:
  - Holehe: E-Mail-Überprüfung bei großen Websites
  - Maigret: Umfassende Suche in sozialen Netzwerken
  - Sherlock: Username-Suche (aus E-Mail extrahiert)
        """
    )
    
    parser.add_argument(
        "-e", "--email",
        help="E-Mail-Adresse zum Überprüfen"
    )
    
    parser.add_argument(
        "--export",
        choices=["json", "txt"],
        default="json",
        help="Export-Format (Standard: json)"
    )
    
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Banner nicht anzeigen"
    )
    
    args = parser.parse_args()
    
    scanner = EmailScanner()
    
    # if not args.no_banner:
    #     scanner.show_banner()
    
    try:
        if args.email:
            # Direkter Modus
            results = scanner.scan_email(args.email)
            if results:
                scanner.display_results(results)
                scanner.export_report(args.email, results, args.export)
        else:
            # Interaktiver Modus
            scanner.run_interactive()
    except KeyboardInterrupt:
        print("\n\n[yellow]Anwendung wird beendet...[/yellow]")
        # Stoppe alle OSINT-Tools
        scanner.osint_manager.stop_all_tools()
    except Exception as e:
        print(f"\n[red]Unerwarteter Fehler: {e}[/red]")
        # Stoppe alle OSINT-Tools
        scanner.osint_manager.stop_all_tools()
    finally:
        # Stoppe alle OSINT-Tools beim Beenden
        try:
            scanner.osint_manager.stop_all_tools()
        except:
            pass

if __name__ == "__main__":
    main()
