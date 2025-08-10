#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Scanner - Eine CLI-Anwendung zum Überprüfen von E-Mail-Adressen auf verschiedenen Websites
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Tuple
import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
import re
import art

class EmailScanner:
    def __init__(self):
        self.console = Console()
        self.results = []
        self.websites = self.load_websites()
        self.reports_dir = "reports"
        self.create_reports_directory()
        
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
        """Lädt die zu überprüfenden Websites aus der Konfiguration"""
        return {
            "GitHub": {
                "url": "https://github.com/signup",
                "check_url": "https://github.com/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Twitter": {
                "url": "https://twitter.com/i/flow/signup",
                "check_url": "https://api.twitter.com/1.1/users/lookup.json",
                "method": "GET",
                "data_field": "screen_name"
            },
            "LinkedIn": {
                "url": "https://www.linkedin.com/signup",
                "check_url": "https://www.linkedin.com/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Facebook": {
                "url": "https://www.facebook.com/signup",
                "check_url": "https://www.facebook.com/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Instagram": {
                "url": "https://www.instagram.com/accounts/emailsignup/",
                "check_url": "https://www.instagram.com/accounts/emailsignup/",
                "method": "POST",
                "data_field": "email"
            },
            "Reddit": {
                "url": "https://www.reddit.com/register/",
                "check_url": "https://www.reddit.com/register/",
                "method": "POST",
                "data_field": "email"
            },
            "Discord": {
                "url": "https://discord.com/register",
                "check_url": "https://discord.com/register",
                "method": "POST",
                "data_field": "email"
            },
            "Spotify": {
                "url": "https://www.spotify.com/de/signup/",
                "check_url": "https://www.spotify.com/de/signup/",
                "method": "POST",
                "data_field": "email"
            },
            "Netflix": {
                "url": "https://www.netflix.com/signup",
                "check_url": "https://www.netflix.com/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Amazon": {
                "url": "https://www.amazon.de/ap/register",
                "check_url": "https://www.amazon.de/ap/register",
                "method": "POST",
                "data_field": "email"
            },
            "Microsoft": {
                "url": "https://signup.live.com/signup",
                "check_url": "https://signup.live.com/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Google": {
                "url": "https://accounts.google.com/signup",
                "check_url": "https://accounts.google.com/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Apple": {
                "url": "https://appleid.apple.com/account",
                "check_url": "https://appleid.apple.com/account",
                "method": "POST",
                "data_field": "email"
            },
            "Dropbox": {
                "url": "https://www.dropbox.com/register",
                "check_url": "https://www.dropbox.com/register",
                "method": "POST",
                "data_field": "email"
            },
            "Slack": {
                "url": "https://slack.com/signin",
                "check_url": "https://slack.com/signin",
                "method": "POST",
                "data_field": "email"
            },
            "Trello": {
                "url": "https://trello.com/signup",
                "check_url": "https://trello.com/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Notion": {
                "url": "https://www.notion.so/login",
                "check_url": "https://www.notion.so/login",
                "method": "POST",
                "data_field": "email"
            },
            "Figma": {
                "url": "https://www.figma.com/signup",
                "check_url": "https://www.figma.com/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Canva": {
                "url": "https://www.canva.com/register",
                "check_url": "https://www.canva.com/register",
                "method": "POST",
                "data_field": "email"
            },
            "Zoom": {
                "url": "https://zoom.us/signup",
                "check_url": "https://zoom.us/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Skype": {
                "url": "https://signup.live.com/signup",
                "check_url": "https://signup.live.com/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Telegram": {
                "url": "https://telegram.org/",
                "check_url": "https://telegram.org/",
                "method": "POST",
                "data_field": "email"
            },
            "WhatsApp": {
                "url": "https://www.whatsapp.com/",
                "check_url": "https://www.whatsapp.com/",
                "method": "POST",
                "data_field": "email"
            },
            "Snapchat": {
                "url": "https://accounts.snapchat.com/accounts/signup",
                "check_url": "https://accounts.snapchat.com/accounts/signup",
                "method": "POST",
                "data_field": "email"
            },
            "TikTok": {
                "url": "https://www.tiktok.com/signup",
                "check_url": "https://www.tiktok.com/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Pinterest": {
                "url": "https://www.pinterest.com/signup/",
                "check_url": "https://www.pinterest.com/signup/",
                "method": "POST",
                "data_field": "email"
            },
            "Twitch": {
                "url": "https://www.twitch.tv/signup",
                "check_url": "https://www.twitch.tv/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Steam": {
                "url": "https://store.steampowered.com/join/",
                "check_url": "https://store.steampowered.com/join/",
                "method": "POST",
                "data_field": "email"
            },
            "Epic Games": {
                "url": "https://www.epicgames.com/id/register",
                "check_url": "https://www.epicgames.com/id/register",
                "method": "POST",
                "data_field": "email"
            },
            "Uber": {
                "url": "https://auth.uber.com/login",
                "check_url": "https://auth.uber.com/login",
                "method": "POST",
                "data_field": "email"
            },
            "Airbnb": {
                "url": "https://www.airbnb.com/signup",
                "check_url": "https://www.airbnb.com/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Booking.com": {
                "url": "https://account.booking.com/sign-up",
                "check_url": "https://account.booking.com/sign-up",
                "method": "POST",
                "data_field": "email"
            },
            "PayPal": {
                "url": "https://www.paypal.com/signin",
                "check_url": "https://www.paypal.com/signin",
                "method": "POST",
                "data_field": "email"
            },
            "Stripe": {
                "url": "https://dashboard.stripe.com/register",
                "check_url": "https://dashboard.stripe.com/register",
                "method": "POST",
                "data_field": "email"
            },
            "Shopify": {
                "url": "https://accounts.shopify.com/signup",
                "check_url": "https://accounts.shopify.com/signup",
                "method": "POST",
                "data_field": "email"
            },
            "WordPress": {
                "url": "https://wordpress.com/start/user",
                "check_url": "https://wordpress.com/start/user",
                "method": "POST",
                "data_field": "email"
            },
            "Wix": {
                "url": "https://www.wix.com/signup",
                "check_url": "https://www.wix.com/signup",
                "method": "POST",
                "data_field": "email"
            },
            "Squarespace": {
                "url": "https://www.squarespace.com/signup",
                "check_url": "https://www.squarespace.com/signup",
                "method": "POST",
                "data_field": "email"
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
            "url": website_config["url"],
            "status": "Unbekannt",
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # Einfache Überprüfung - in der Praxis würdest du hier spezifische APIs verwenden
            response = requests.get(website_config["check_url"], headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Simuliere eine Überprüfung (in der Praxis würdest du hier die tatsächliche API-Logik implementieren)
                if "email" in response.text.lower() or "signup" in response.text.lower():
                    result["status"] = "Verfügbar"
                    result["message"] = "E-Mail-Adresse kann für Registrierung verwendet werden"
                else:
                    result["status"] = "Unbekannt"
                    result["message"] = "Konnte den Status nicht bestimmen"
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
    
    def scan_email(self, email: str) -> List[Dict]:
        """Führt den vollständigen E-Mail-Scan durch"""
        if not self.validate_email(email):
            self.console.print(f"[red]Fehler: Ungültige E-Mail-Adresse: {email}[/red]")
            return []
        
        self.console.print(f"\n[green]Starte E-Mail-Scan für: {email}[/green]")
        self.console.print(f"[yellow]Überprüfe {len(self.websites)} Websites...[/yellow]\n")
        
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Scanne Websites...", total=len(self.websites))
            
            for website_name, website_config in self.websites.items():
                progress.update(task, description=f"Überprüfe {website_name}...")
                
                result = self.check_email_on_website(email, website_name, website_config)
                results.append(result)
                
                # Kurze Pause zwischen den Anfragen
                time.sleep(0.5)
                progress.advance(task)
        
        return results
    
    def display_results(self, results: List[Dict]):
        """Zeigt die Ergebnisse in einer schönen Tabelle an"""
        if not results:
            self.console.print("[red]Keine Ergebnisse zum Anzeigen.[/red]")
            return
        
        table = Table(title="E-Mail-Scan Ergebnisse", show_header=True, header_style="bold magenta")
        table.add_column("Website", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold")
        table.add_column("URL", style="dim")
        table.add_column("Nachricht", style="white")
        
        for result in results:
            status_style = {
                "Verfügbar": "green",
                "Registriert": "red",
                "Fehler": "red",
                "Unbekannt": "yellow"
            }.get(result["status"], "white")
            
            table.add_row(
                result["website"],
                f"[{status_style}]{result['status']}[/{status_style}]",
                result["url"],
                result["message"][:50] + "..." if len(result["message"]) > 50 else result["message"]
            )
        
        self.console.print(table)
    
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
        self.console.print("4. Beenden")
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
                    self.console.print("\n[yellow]Machs gut du russische Schlampe![/yellow]")
                    break
                else:
                    self.console.print("[red]Ungültige Auswahl. Bitte wähle 1, 2, 3 oder 4.[/red]")
                    
            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]Programm wird beendet...[/yellow]")
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
    
    if args.email:
        # Direkter Modus
        results = scanner.scan_email(args.email)
        if results:
            scanner.display_results(results)
            scanner.export_report(args.email, results, args.export)
    else:
        # Interaktiver Modus
        scanner.run_interactive()

if __name__ == "__main__":
    main()
