#!/bin/bash

echo "🚀 Installiere OSINT-Tools für den E-Mail-Scanner..."
echo "=================================================="

# Prüfe ob Python3 verfügbar ist
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 ist nicht installiert. Bitte installiere es zuerst."
    exit 1
fi

# Erstelle virtuelles Environment falls es nicht existiert
if [ ! -d "venv" ]; then
    echo "📦 Erstelle virtuelles Python-Environment..."
    python3 -m venv venv
fi

# Aktiviere virtuelles Environment
echo "🔧 Aktiviere virtuelles Environment..."
source venv/bin/activate

# Installiere Python-Abhängigkeiten
echo "📥 Installiere Python-Abhängigkeiten..."
pip install -r requirements.txt

# Installiere Maigret
echo "🔍 Installiere Maigret..."
if [ ! -d "maigret" ]; then
    git clone https://github.com/soxoj/maigret.git
    cd maigret/pyinstaller
    pip install -r requirements.txt
    cd ../../
else
    echo "✅ Maigret ist bereits installiert"
fi

# Installiere Sherlock
echo "🕵️ Installiere Sherlock..."
if [ ! -d "sherlock" ]; then
    git clone https://github.com/sherlock-project/sherlock.git
    cd sherlock
    pip install -r requirements.txt
    cd ../../
else
    echo "✅ Sherlock ist bereits installiert"
fi

# Installiere Holehe (falls verfügbar)
echo "📧 Versuche Holehe zu installieren..."
if command -v pip &> /dev/null; then
    pip install holehe
else
    echo "⚠️  Holehe konnte nicht installiert werden (pip nicht verfügbar)"
fi

echo ""
echo "✅ Installation abgeschlossen!"
echo ""
echo "📋 Verfügbare Befehle:"
echo "  python email_scanner.py                    # Starte den Scanner"
echo "  python run_osint_tools.py maigret \"test@example.com\"  # Starte Maigret direkt"
echo "  python run_osint_tools.py sherlock \"testuser\"        # Starte Sherlock direkt"
echo "  python run_osint_tools.py holehe \"test@example.com\"  # Starte Holehe direkt"
echo ""
echo "🔧 Tools werden automatisch beim Start des Scanners geladen."
