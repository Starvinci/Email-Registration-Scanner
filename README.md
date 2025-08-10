# Email Scanner

Eine CLI-basierte Python-Anwendung zum Überprüfen von E-Mail-Adressen auf verschiedenen Websites.

## 🎯 Features

- **ASCII-Art Banner**: Schöner "Email Scanner" Banner mit "RS made by tim ^2"
- **E-Mail-Validierung**: Überprüfung der E-Mail-Adress-Formatierung
- **Website-Scanning**: Überprüfung auf konfigurierten Websites
- **OSINT-Fallback-Tools**: Automatische Nutzung von Holehe, Maigret und Sherlock nach eigener Auswertung
- **Interaktiver Modus**: Benutzerfreundliche CLI-Oberfläche mit klarer Navigation
- **Berichtsexport**: Export in JSON oder TXT-Format
- **Reports-Ordner**: Automatische Speicherung aller Berichte in einem strukturierten Ordner
- **Farbige Ausgabe**: Moderne Terminal-Ausgabe mit Rich-Bibliothek
- **Fortschrittsanzeige**: Visueller Fortschritt während des Scannings

## 🚀 Installation

### Voraussetzungen
- Python 3.7 oder höher
- pip (Python-Paketmanager)

### Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

## 📖 Verwendung

### Interaktiver Modus
```bash
python email_scanner.py
```

### Direkte E-Mail-Überprüfung
```bash
python email_scanner.py -e test@example.com
```

### Mit Berichtsexport
```bash
python email_scanner.py -e test@example.com --export json
python email_scanner.py -e test@example.com --export txt
```

### Banner ausblenden
```bash
python email_scanner.py --no-banner
```

## 🖥️ CLI-Navigation

Die Anwendung bietet eine klare, strukturierte Navigation:

### Hauptmenü
```
============================================================
E-Mail-Scanner - Hauptmenü
============================================================
1. E-Mail-Adresse scannen
2. Verfügbare Websites anzeigen
3. Berichte anzeigen
4. OSINT-Tools Status anzeigen
5. Beenden
============================================================
```

### E-Mail-Scan
```
----------------------------------------
E-Mail-Scan
----------------------------------------
E-Mail-Adresse eingeben (oder 'zurück' für Hauptmenü):
```

### Export-Menü
```
----------------------------------------
Bericht exportieren
----------------------------------------
1. JSON-Format
2. TXT-Format
3. Beide Formate
4. Kein Export
```

## 🖥️ Verfügbare Websites

Die Anwendung überprüft E-Mail-Adressen auf konfigurierten Websites (aktuell: Spotify, OnlyFans).

## 🔍 OSINT-Fallback-Tools

Nach der eigenen E-Mail-Auswertung werden automatisch verfügbare OSINT-Tools als Fallback verwendet:

### Verfügbare Tools
| Tool | Beschreibung | Installation |
|------|--------------|--------------|
| **Holehe** | E-Mail-Überprüfung bei großen Websites (Twitter, Instagram, Spotify, etc.) | `sudo apt install holehe` |
| **Maigret** | Umfassende Suche in hunderten sozialen Netzwerken | `git clone https://github.com/soxoj/maigret && cd maigret && pip install -r requirements.txt` |
| **Sherlock** | Username-Suche (wird aus E-Mail extrahiert) | `git clone https://github.com/sherlock-project/sherlock.git && cd sherlock && pip install -r requirements.txt` |

### Funktionsweise
1. **Eigene Auswertung**: Zuerst wird die E-Mail mit der eigenen Website-Überprüfung gescannt
2. **OSINT-Fallback**: Nach Abschluss der eigenen Auswertung startet automatisch der OSINT-Scan
3. **Kombinierte Ergebnisse**: Alle Ergebnisse werden in einem einheitlichen Format zusammengeführt
4. **Automatische Erkennung**: Verfügbare Tools werden automatisch erkannt und genutzt

### Tool-Status anzeigen
Im Hauptmenü unter "4. OSINT-Tools Status anzeigen" können Sie den Status der verfügbaren Tools einsehen.

## 📁 Reports-Ordner

Alle Berichte werden automatisch im `reports/` Ordner gespeichert:

```
reports/
├── email_scan_test_at_example_com_20240115_143000.json
├── email_scan_test_at_example_com_20240115_143000.txt
├── email_scan_user_at_domain_com_20240115_142500.json
└── email_scan_user_at_domain_com_20240115_142500.txt
```

**Dateinamen-Format**: `email_scan_{E-Mail}_at_{Domain}_{Timestamp}.{Format}`

## 📊 Berichtsformate

### JSON-Export
```json
{
  "email": "test@example.com",
  "scan_timestamp": "2024-01-15T14:30:00",
  "total_websites": 8,
  "results": [
    {
      "website": "GitHub",
      "url": "https://github.com/signup",
      "description": "GitHub - Plattform für Software-Entwicklung...",
      "status": "Verfügbar",
      "message": "E-Mail-Adresse kann für Registrierung verwendet werden",
      "timestamp": "2024-01-15T14:30:00"
    }
  ]
}
```

### TXT-Export
```
E-Mail-Scan Bericht
==================

E-Mail: test@example.com
Scan-Datum: 15.01.2024 14:30:00
Anzahl Websites: 8

Website: GitHub
Status: Verfügbar
Beschreibung: GitHub - Plattform für Software-Entwicklung...
Nachricht: E-Mail-Adresse kann für Registrierung verwendet werden
--------------------------------------------------
```

## ⚙️ Konfiguration

Die Websites können in der `websites_config.json` Datei angepasst werden. Jede Website benötigt:

- `url`: Registrierungs-URL
- `check_url`: URL für die E-Mail-Überprüfung
- `method`: HTTP-Methode (GET/POST)
- `data_field`: Feldname für die E-Mail-Adresse
- `description`: Beschreibung der Website

## 🔧 Entwicklung

### Projektstruktur
```
ESRS/
├── email_scanner.py      # Hauptanwendung
├── websites_config.json  # Website-Konfiguration
├── requirements.txt      # Python-Abhängigkeiten
├── reports/             # Berichte-Ordner (wird automatisch erstellt)
├── test_scanner.py      # Test-Datei
└── README.md            # Diese Datei
```

### Abhängigkeiten
- `requests`: HTTP-Anfragen
- `beautifulsoup4`: HTML-Parsing
- `colorama`: Terminal-Farben
- `tabulate`: Tabellen-Formatierung
- `rich`: Moderne Terminal-Ausgabe
- `art`: ASCII-Art Generierung

## ⚠️ Hinweise

- **Rate Limiting**: Die Anwendung implementiert Pausen zwischen Anfragen
- **User-Agent**: Verwendet einen realistischen Browser-User-Agent
- **Fehlerbehandlung**: Robuste Fehlerbehandlung für Netzwerkprobleme
- **Datenschutz**: Überprüft nur öffentlich verfügbare Informationen
- **Reports-Ordner**: Wird automatisch erstellt, falls nicht vorhanden

## 📝 Lizenz

RS made by tim ^2

## 🤝 Beitragen

Verbesserungsvorschläge und Bug-Reports sind willkommen!

## 🐛 Bekannte Probleme

- Einige Websites blockieren automatisierte Anfragen
- API-Limits können die Überprüfung beeinträchtigen
- Status-Erkennung basiert auf einfachen Heuristiken

## 🔮 Zukünftige Features

- [x] OSINT-Fallback-Tools (Holehe, Maigret, Sherlock)
- [ ] Erweiterte API-Integration
- [ ] Proxy-Unterstützung
- [ ] Batch-Verarbeitung mehrerer E-Mails
- [ ] Webhook-Benachrichtigungen
- [ ] Datenbank-Integration für Verlaufsverfolgung
- [ ] Berichtssuche und -filterung
- [ ] Automatische Berichtslöschung nach Zeitraum
- [ ] Weitere OSINT-Tools integrieren
