#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Einfacher Test für den E-Mail-Scanner
"""

from email_scanner import EmailScanner

def test_scanner():
    """Testet die grundlegenden Funktionen des E-Mail-Scanners"""
    print("Teste E-Mail-Scanner...")
    
    # Scanner-Instanz erstellen
    scanner = EmailScanner()
    
    # Banner anzeigen
    scanner.show_banner()
    
    # E-Mail-Validierung testen
    test_emails = [
        "test@example.com",
        "invalid-email",
        "user@domain.co.uk",
        "test.email+tag@example.org"
    ]
    
    print("\nTeste E-Mail-Validierung:")
    for email in test_emails:
        is_valid = scanner.validate_email(email)
        status = "Gültig" if is_valid else "Ungültig"
        print(f"  {email}: {status}")
    
    # Websites anzeigen
    print(f"\nVerfügbare Websites: {len(scanner.websites)}")
    for name, config in scanner.websites.items():
        print(f"  • {name}: {config['url']}")
    
    print("\nTest abgeschlossen!")

if __name__ == "__main__":
    test_scanner()
