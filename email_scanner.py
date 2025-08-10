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
                                result["status"] = "Registriert"
                                result["message"] = "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                return result
                            elif 'e-mail-adresse' in response_text and 'bereits' in response_text:
                                result["status"] = "Registriert"
                                result["message"] = "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                return result
                            elif 'email' in response_text and ('taken' in response_text or 'exists' in response_text):
                                result["status"] = "Registriert"
                                result["message"] = "E-Mail-Adresse ist bereits bei OnlyFans registriert"
                                return result
                            # Wenn keine Fehlermeldung über bereits existierende E-Mail
                            elif 'password' in response_text or 'passwort' in response_text:
                                result["status"] = "Verfügbar"
                                result["message"] = "E-Mail wurde akzeptiert, Passwort-Fehler zeigt Verfügbarkeit"
                                return result
                            elif 'success' in response_text or 'erfolgreich' in response_text:
                                result["status"] = "Verfügbar"
                                result["message"] = "E-Mail-Adresse wurde erfolgreich bei OnlyFans registriert"
                                return result
                            else:
                                result["status"] = "Verfügbar"
                                result["message"] = "E-Mail wurde akzeptiert, Status unklar"
                                return result
                        else:
                            result["status"] = "Fehler"
                            result["message"] = f"OnlyFans antwortete mit Status {response.status_code}"
                            return result
                    else:
                        result["status"] = "Fehler"
                        result["message"] = f"OnlyFans-Hauptseite nicht erreichbar: Status {response.status_code}"
                        return result
                        
                except Exception as e:
                    result["message"] = f"OnlyFans-Formular-Test fehlgeschlagen: {str(e)}"
                    
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
            else:
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
