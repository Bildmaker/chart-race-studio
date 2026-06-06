# chart-race-studio

Animierte **Bar-Chart-Race-Videos** (9:16) für Instagram Reels, TikTok & YouTube Shorts –
mit einer einfachen Benutzeroberfläche selbst rendern.

Du wählst Assets (Gold, Bitcoin, Nvidia, Aktien, Krypto …), einen Startzeitpunkt und
einen Investbetrag. Das Tool berechnet die Wertentwicklung und rendert daraus ein
schickes, animiertes Balken-Rennen als fertiges MP4 – inkl. lizenzfreier Musik,
Endstand der einige Sekunden stehen bleibt und blinkendem Sieger.

## Features
- 📱 Hochformat **1080×1920 (9:16)** – direkt hochladbar
- 🎨 Zwei Looks: **Dark Neon** und **Clean Light**
- 🏆 Endstand-Haltedauer + **blinkender Sieger** ("Beste Performance")
- 🎵 Selbst erzeugte, **lizenzfreie Musik** (an/aus)
- 🌐 **Live-Kurse** via `yfinance` mit **Offline-Fallback** (Gold/Bitcoin/Nvidia)
- 🧮 Logarithmische Balkenlängen, damit auch sehr unterschiedlich große Assets sichtbar bleiben
- 🖱️ **GUI** (kein Programmierwissen nötig) + gebündeltes `ffmpeg` (über `imageio-ffmpeg`)

## Installation
1. **Python 3.10+** installieren (https://www.python.org/downloads/, Haken bei *Add to PATH*)
2. Abhängigkeiten installieren:
   - Windows: Doppelklick auf `install.bat`
   - oder: `pip install -r requirements.txt`

## Benutzung
- Windows: Doppelklick auf `start.bat`
- oder: `python chartrace_studio.py`

Assets wählen (2–6), Parameter einstellen, **„Video rendern"** klicken. Fertig.

Eigene Yahoo-Finance-Ticker (Internet nötig), z. B.:
`AAPL`, `MSFT`, `TSLA`, `AMZN`, `META`, `GOOGL`, `^GSPC` (S&P 500), `^NDX`, `^GDAXI` (DAX),
`BTC-USD`, `ETH-USD`, `SOL-USD`, `GC=F` (Gold), `SI=F` (Silber).

## Projektdateien
| Datei | Zweck |
|---|---|
| `chartrace_studio.py` | Benutzeroberfläche (GUI) |
| `engine.py` | Render-Engine: Daten, Frames, Video, Musik |
| `data.py` | eingebaute Offline-Kursdaten |
| `install.bat` / `start.bat` | Windows-Helfer |
| `requirements.txt` | Python-Pakete |
| `ANLEITUNG.txt` | ausführliche Anleitung (Deutsch) |

## Hinweise / Haftung
Werte basieren auf Monats-/Jahres-Schlusskursen, nominal, USD-basiert (keine
Währungsumrechnung, keine Gebühren/Steuern). Nvidia ist split-/dividendenbereinigt.
Dies ist eine Veranschaulichung, **keine Anlageberatung**.
Datenquellen Offline-Fallback: macrotrends.net, officialdata.org.

## Lizenz
MIT – siehe `LICENSE`.
