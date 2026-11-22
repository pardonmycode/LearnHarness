# LearnHarness

LearnHarness ist eine Programmierwerkstatt für Kinder, die mit **Godot 4** Spiele bauen. Godot
bleibt für Szenen, Maps und Grafik zuständig; die LearnHarness-App ist ein sicherer Editor für
GDScript mit KI-Lernbegleiter. Die KI gibt **keine fertigen Lösungen**: Code wird erst nach
einer richtig gelösten Übung geschrieben, klein und mit erklärenden Kommentaren.

Das Repository besteht aus drei Teilen:

| Ordner | Inhalt |
|---|---|
| `client/` | Die App für die Kinder-PCs (PyQt6) |
| `server/` | Zentrale Verwaltung für Lehrkräfte **und** eingebauter Lernserver mit KI-Harness (Django, PostgreSQL, Channels) |
| `protocol/` | Gemeinsame Nachrichtenmodelle (Pydantic) und JSON-Schemas, die App und Server austauschen |

```
Kinder-PC (App) ──HTTP/WebSocket + Gerätetoken──► Server (Django)
                                                   ├─ Verwaltung: Kinder, Gruppen, Missionen, Verlauf
                                                   ├─ Lernserver: Harness, Übungen, Prompt-Protokoll
                                                   └─► KI: lokales Modell (vLLM) · Claude · ChatGPT
```

---

## Inhalt

- [Funktionen der App](#funktionen-der-app)
- [Funktionen für Lehrkräfte (Server)](#funktionen-für-lehrkräfte-server)
- [KI-Anbieter und Harness](#ki-anbieter-und-harness)
- [Datenschutz](#datenschutz)
- [Befehle](#befehle)
- [Einrichtung im Klassenraum](#einrichtung-im-klassenraum)
- [Entwicklung und Qualität](#entwicklung-und-qualität)
- [Weitere Dokumentation](#weitere-dokumentation)

---

## Funktionen der App

### Anmeldung und Profile
- Anmeldung mit **Spitznamen** und Vorkenntnissen, ohne Passwort und ohne echten Namen.
- Mehrere Kinder können einen PC nutzen; jedes Profil hat eigenes Level, Fortschritt und Missionen.
- Mit verbundener Verwaltung werden Profile und Level beim Start abgeglichen (siehe unten).

### Editor für GDScript
- Öffnet nur ein ausdrücklich gewähltes Godot-Projekt und darin nur `*.gd`-Dateien
  (Pfadschutz gegen Dateien außerhalb des Projekts).
- Projektauswahl auch aus Godots eigener Projektliste und „Zuletzt verwendete Projekte“.
- Skriptbaum, der sich automatisch aktualisiert, wenn in Godot Skripte angelegt oder gelöscht
  werden.
- Syntaxhervorhebung für GDScript, Zeilennummern, Suchen/Ersetzen, „Gehe zu Zeile“.
- Atomisches Speichern, Erkennung von Änderungen aus Godot (Konfliktdialog statt Überschreiben),
  optional automatisches Speichern.
- Sicherungen und Wiederherstellung nach einem Absturz; ältere Versionen ansehen.
- „Skript mit Godot prüfen“ (F6) und „Fehler aus dem Godot-Log holen“ → Problembereich mit
  Sprung zur Zeile.

### Lern-Tabs (rechts)

| Tab | Was das Kind dort tut |
|---|---|
| **LearnAgent** | Wünscht sich ein Feature („Meine Figur soll springen“). Der Agent stellt eine Übung (Auswahl oder Lücken) passend zu Level 1–10; erst nach der richtigen Antwort wird kleiner, kommentierter Code in die offene Datei geschrieben. Schwerpunkt wählbar oder automatisch die schwächste Fähigkeit. „Änderungen anzeigen“ zeigt, was geschrieben wurde. |
| **Missionen** | Größere Ziele in Schritten (z. B. „Baue einen Doppelsprung!“, Fortschritt „2 von 4“). Missionen der Lehrkraft stehen unter „Von deiner Lehrkraft“, eigene Wünsche plant die KI. Der letzte Schritt ist immer: in Godot ausprobieren. |
| **Code verstehen** | Code markieren → „Diesen Code erklären“ oder Rechtsklick „Erklär mir das“. Vorgeschlagene Fragen wie „Was macht `velocity.x = speed`?“, kindgerechte Erklärung, danach eine Verständnisfrage. |
| **Tutor** | Chat mit dem Lernbegleiter; antwortet mit Fragen und Hinweisen statt Lösungen, gestaffelte Hinweise zur Aufgabe. |
| **Fortschritt** | Stand je Fähigkeit (Noch nicht begonnen · Mit Hilfe · Fast selbstständig · Sicher), ohne Punktestand. |

### Lehrkraft-Bereich in der App
**Bearbeiten → Lehrkraft-Bereich …** (mit Passwort):
- Level setzen oder senken, Fortschritt zurücksetzen, Profile löschen (nur ohne zentrale
  Verwaltung – sonst passiert das im Admin).
- **Zentrale Verwaltung …**: Serveradresse, Gerätetoken und optional die Gruppe dieses PCs.

### Weitere Bedienung
- Einstellungen: Lernserver-Adresse, Schriftgröße, helles/dunkles Design, automatisches Speichern,
  Änderungsansicht nach dem LearnAgent.
- Kurzanleitung (F1), technische Details (Verbindung, Protokollversion, Sitzung).
- Verbindungsstatus mit automatischem Wiederverbinden; ohne Server bleibt der Editor voll
  nutzbar, es geht kein Code verloren.
- Eingebauter **Übungsserver** (`--fake-server`), um alles ohne Server und ohne KI auszuprobieren.

### Tastenkürzel

| Kürzel | Aktion |
|---|---|
| Strg+O | Godot-Projekt öffnen |
| Strg+Umschalt+N | Neues GDScript |
| Strg+S | Speichern |
| Strg+F / Strg+H | Suchen / Suchen und ersetzen |
| Strg+G | Gehe zu Zeile |
| F6 | Skript mit Godot prüfen |
| F1 | Kurzanleitung |

---

## Funktionen für Lehrkräfte (Server)

Alles im Browser unter `http://SERVER:8000/admin/` (Anmeldung als Mitarbeiter).

- **Kinder und Gruppen:** Spitzname, Vorkenntnisse, freigeschaltetes Level (auch senken),
  Gruppe, archivieren/reaktivieren, „Nächstes Level freischalten“, „Fortschritt zurücksetzen“.
- **Gruppenübersicht** `/uebersicht/`: Tabelle Kinder × Fähigkeiten mit Farbe und Text, Level,
  „Zuletzt gesehen“; Filter nach Gruppe; **CSV-Export**.
- **Verlauf pro Kind** `/uebersicht/kind/<id>/`: Entwicklung jeder Fähigkeit mit Datum,
  Level-Verlauf, abgeschlossene Missionen, Zeitraumfilter, **Drucken / als PDF speichern**
  (z. B. fürs Elterngespräch) und **CSV-Export**.
- **Missionen:** anlegen mit Titel, Ziel, 1–8 Schritten (Verstehen, Lernen, Üben, In Godot
  ausprobieren) und je Schritt einem **Hinweis für die KI**, den das Kind nicht sieht; Gruppen
  zuweisen (leer = alle); Anzeige, wie viele Kinder sie geschafft haben.
- **API-Zugänge:** ein Gerätetoken pro PC (wird nur einmal angezeigt, nur als Hash gespeichert),
  Token erneuern, Zugang sperren.
- **KI-Einstellungen**, **Prompt-Übersicht** und **KI-Protokoll** – siehe nächster Abschnitt.
- **Lernsitzungen:** wer wann mit welchem Projekt gelernt hat, mit Link zu den KI-Anfragen.
- **Datensicherung:** täglicher `pg_dump` mit Aufbewahrungsfrist (Docker-Dienst `backup`).

### Abgleich mit der App
- Beim Start der App (vor der Anmeldung): ausstehende Level-Freischaltungen und erledigte
  Missionen senden, neue lokale Profile hochladen, Profile und Level vom Server übernehmen,
  gelöschte/archivierte Kinder entfernen.
- Ohne Netz lernt das Kind mit dem Stand auf dem PC weiter; Ausstehendes wird später gesendet.

---

## KI-Anbieter und Harness

### Anbieter umschalten
Im Admin unter **Lernserver (KI) › KI-Einstellungen** – wirkt sofort, ohne Neustart und ohne
Änderung an den Kinder-PCs.

| Anbieter | Einstellung im Admin | Schlüssel in `server/.env` |
|---|---|---|
| Lokales Modell (vLLM) | Adresse, z. B. `http://ki-pc:8001/v1`, und Modellname wie beim vLLM-Start | `VLLM_API_KEY` nur bei `--api-key` |
| Claude (Anthropic) | Modell (Standard `claude-opus-5-5`), Denkaufwand (Standard niedrig) | `ANTHROPIC_API_KEY` |
| ChatGPT (OpenAI) | Modellname | `OPENAI_API_KEY` |

„Verbindung testen“ prüft die **gespeicherten** Einstellungen. Bei Claude-Modellen, die es
unterstützen, leitet der Server abgelehnte Anfragen automatisch an ein Ersatzmodell weiter.

### Harness: keine fertigen Lösungen
- **Feste Regeln** im System-Prompt: kurz, kindgerecht, auf Deutsch, Fragen statt Lösungen, keine
  persönlichen Daten. Eigene Anweisungen der Lehrkraft werden angehängt, heben die Regeln nicht auf.
- **Eingaben der Kinder** stehen in `<kind>…</kind>`, Projektcode in `<code>…</code>`; die KI
  behandelt sie als Inhalt, nicht als Anweisung.
- **Code-Filter beim Streamen:** Code mit mehr als N Zeilen am Stück (mit oder ohne Codeblock)
  wird ersetzt, bevor das Kind ihn sieht (Standard 3).
- **Übungen** liefert die KI als JSON mit Aufgabe und Lösung getrennt; das Kind bekommt nur die
  Aufgabe, die Antwort prüft der Server selbst.
- **Code nach richtiger Antwort** bleibt bis dahin auf dem Server, ändert höchstens N Zeilen der
  geöffneten Datei (Standard 12) und nur diese Datei. Bei Verstoß ein zweiter Versuch, sonst kein Code.
- **Kostenbremse:** höchstens N Anfragen pro Kind und Minute (Standard 12).
- Alle Grenzen sind in den KI-Einstellungen einstellbar.

### Überblick über die Prompts
- **`/ki/prompts/`** zeigt für jeden Zweck (Chat, Hinweis, Code verstehen, LearnAgent, Mission,
  Missionsschritt, Code-Prüfung) den vollständigen System-Prompt bei wählbarer Lernstufe und
  Vorkenntnissen, das verlangte JSON-Format und eine Beispielnachricht.
- **KI-Protokoll** (Admin): jede Anfrage mit System-Prompt, Nachrichten, Rohantwort der KI,
  dem, was beim Kind ankam, Eingriffen des Harness, Tokens und Dauer. Filter „Harness hat
  eingegriffen“ zeigt abgefangene Lösungen.

---

## Datenschutz

- Gespeichert werden nur **Spitznamen**, Vorkenntnisse, Level, Stand je Fähigkeit und Verlauf –
  keine echten Namen. Die Zuordnung Spitzname → Kind kennt nur die Lehrkraft.
- Das KI-Protokoll enthält, was die Kinder schreiben. Es wird nach 30 Tagen gelöscht
  (einstellbar) und lässt sich ganz abschalten; dann werden nur Tokens und Dauer gezählt.
- Bei Claude oder ChatGPT gehen Nachrichten und Code-Ausschnitte an den jeweiligen Anbieter; mit
  vLLM bleibt alles im eigenen Netz.
- API-Schlüssel liegen nur in `server/.env`, nie auf den Kinder-PCs.
- „Fortschritt zurücksetzen“ löscht auch den Verlauf. Die App protokolliert keine Code- oder
  Chatinhalte; Logs und Sicherungen liegen im AppData-Ordner des Windows-Benutzers.

---

## Befehle

Die App läuft unter **Windows und Linux** (macOS sollte ebenso gehen, ist aber nicht getestet).
Die Befehle stehen im Repository-Stamm zuerst für Windows PowerShell; unter Linux steht statt
`.\.venv\Scripts\python.exe` einfach `.venv/bin/python` (Abschnitt [Linux](#linux)).

### Einmalig: Umgebung einrichten

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .\protocol -e ".\client[dev]" -e ".\server[dev]"
```

### App starten

```powershell
# Mit eingebautem Übungsserver und Beispielprojekt (ohne Server, ohne KI)
.\.venv\Scripts\python.exe -m learnharness_client --fake-server --project .\client\tests\fixtures\sample_godot_project

# Mit einem Lernserver
.\.venv\Scripts\python.exe -m learnharness_client --server http://SERVER:8000

# Ohne Optionen: Adresse und Projekt aus den Einstellungen (Erststart-Dialog fragt danach)
.\.venv\Scripts\python.exe -m learnharness_client
```

| Option | Bedeutung |
|---|---|
| `--project PFAD` | Godot-Projekt direkt öffnen |
| `--server URL` | Lernserver-Adresse für diesen Start |
| `--fake-server` | Eingebauten Übungsserver verwenden |

Nach `pip install` gibt es dafür auch den Befehl `learnharness`.

### App bauen (Windows: Ordner mit EXE; Linux: siehe [Linux](#linux))

```powershell
cd client
..\.venv\Scripts\pyinstaller.exe learnharness.spec
cd ..
```

### Linux

Einmal die Systembibliotheken für Qt installieren (Debian/Ubuntu; auf einem normalen Desktop
sind sie meist schon da):

```bash
sudo apt install python3-venv libegl1 libgl1 libxkbcommon0 libfontconfig1 libglib2.0-0 \
  libdbus-1-3 libgssapi-krb5-2
```

Dann wie unter Windows, nur mit Linux-Pfaden:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ./protocol -e "./client[dev]" -e "./server[dev]"

# App mit Übungsserver und Beispielprojekt
.venv/bin/python -m learnharness_client --fake-server --project ./client/tests/fixtures/sample_godot_project

# Tests und Prüfungen
.venv/bin/python -m pytest
(cd server && ../.venv/bin/python -m pytest)
.venv/bin/ruff check client protocol server
(cd client && ../.venv/bin/mypy)

# App bauen (Ordner dist/LearnHarness mit ausführbarer Datei LearnHarness)
(cd client && ../.venv/bin/pyinstaller learnharness.spec)

# Server lokal
cd server && DJANGO_DEBUG=1 ../.venv/bin/python manage.py migrate && DJANGO_DEBUG=1 ../.venv/bin/python manage.py runserver 0.0.0.0:8000
```

Unterschiede zu Windows, die die App selbst berücksichtigt:

| | Windows | Linux |
|---|---|---|
| Godot-Projektliste (`projects.cfg`) | `%APPDATA%\Godot` | `~/.config/godot` (bzw. `$XDG_CONFIG_HOME/godot`) |
| Godot-Log eines Spiels | `%APPDATA%\Godot\app_userdata\<Projekt>\logs` | `~/.local/share/godot/app_userdata/<Projekt>/logs` |
| Godot-Programm für F6 | Einstellungen, sonst `godot` aus dem PATH | Einstellungen, sonst automatisch `godot4`/`godot` aus dem PATH |
| Groß-/Kleinschreibung in Dateinamen | egal (`Player.gd` = `player.gd`) | zählt (`Player.gd` ≠ `player.gd`) |
| Einstellungen der App | Registry (`HKCU\Software\LearnHarness`) | `~/.config/LearnHarness/` |
| Sicherungen, Logs, Wiederherstellung | `%APPDATA%\LearnHarness\LearnHarnessClient` | `~/.local/share/LearnHarness/LearnHarnessClient/` |

Pfade vom Server oder von einem Windows-PC (`scripts\player.gd`) versteht die App auf beiden
Systemen; `..\` gilt auch unter Linux als Versuch, das Projekt zu verlassen.

### Server lokal (SQLite, zum Ausprobieren)

```powershell
cd server
$env:DJANGO_DEBUG = "1"
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py createsuperuser
..\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

Danach: Admin `http://localhost:8000/admin/`, Übersicht `http://localhost:8000/uebersicht/`,
Prompts `http://localhost:8000/ki/prompts/`.

### Server im Betrieb (Docker, PostgreSQL)

```bash
cp server/.env.example server/.env          # Werte eintragen: Secret Key, Passwort, KI-Schlüssel
docker compose -f server/docker-compose.yml up -d --build
docker compose -f server/docker-compose.yml exec web python manage.py createsuperuser
docker compose -f server/docker-compose.yml logs -f web       # Protokoll ansehen
git pull && docker compose -f server/docker-compose.yml up -d --build   # Update (Migrationen laufen beim Start)
```

### Gerätetokens

```powershell
# Token für einen Kinder-PC (wird einmal angezeigt)
..\.venv\Scripts\python.exe manage.py create_api_token "PC Raum 12"
# Token für einen externen Lernserver (darf Fortschritt schreiben)
..\.venv\Scripts\python.exe manage.py create_api_token "Lernserver" --kind learnserver
```

Im Docker-Betrieb: `docker compose -f server/docker-compose.yml exec web python manage.py create_api_token "PC Raum 12"`.
Alternativ im Admin unter „API-Zugänge“.

### Datensicherung

```bash
# Sofort sichern (z. B. vor einem Update)
docker compose -f server/docker-compose.yml exec backup sh /usr/local/bin/backup.sh once
# Inhalt einer Sicherung prüfen
docker compose -f server/docker-compose.yml exec backup pg_restore --list /backups/<datei>.dump
# Wiederherstellen (überschreibt die Datenbank)
docker compose -f server/docker-compose.yml stop web
docker compose -f server/docker-compose.yml exec backup sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" pg_restore -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner /backups/<datei>.dump'
docker compose -f server/docker-compose.yml start web
```

Den Ordner `server/backups/` zusätzlich auf ein anderes Gerät kopieren.

### Tests und Prüfungen

```powershell
# App und Protokoll
.\.venv\Scripts\python.exe -m pytest
# Server
cd server; ..\.venv\Scripts\python.exe -m pytest; cd ..
# Stil und Formatierung
.\.venv\Scripts\ruff.exe check client protocol server
.\.venv\Scripts\ruff.exe format --check client protocol server
# Typprüfung (strict)
cd client; ..\.venv\Scripts\mypy.exe; cd ..
# Fehlende Datenbank-Migrationen?
cd server; $env:DJANGO_SETTINGS_MODULE = "learnharness_server.test_settings"; ..\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run; cd ..
```

### Protokoll-Schemas neu erzeugen (nach Änderungen in `protocol/`)

```powershell
cd protocol
..\.venv\Scripts\python.exe -m learnharness_protocol.export_schema
cd ..
```

---

## Einrichtung im Klassenraum

1. **Server starten** (Docker, siehe oben) und in `server/.env` die nötigen KI-Schlüssel eintragen.
2. Im Admin **KI-Einstellungen** öffnen: Anbieter und Modell wählen, speichern, „Verbindung testen“.
3. **Gruppen** und optional **Missionen** anlegen.
4. Für jeden Kinder-PC einen **Gerätetoken** erzeugen.
5. In der App auf jedem PC:
   - Einstellungen → Lernserver: `http://SERVER:8000`
   - Bearbeiten → Lehrkraft-Bereich → Zentrale Verwaltung: **dieselbe** Adresse, Token, Gruppe.

   Nur wenn beide Adressen gleich sind, schickt die App ihren Token auch an den Lernserver.
6. Kinder melden sich mit ihrem Spitznamen an und öffnen ihr Godot-Projekt.

Für den Zugriff übers Netz eignet sich Tailscale; für HTTPS einen Proxy (z. B. Caddy) vor den
Server setzen und `DJANGO_SECURE=1` setzen.

### Wichtige Einstellungen in `server/.env`

| Variable | Bedeutung |
|---|---|
| `DJANGO_SECRET_KEY` | Langer Zufallswert (Pflicht) |
| `DJANGO_ALLOWED_HOSTS` | Hostnamen des Servers, z. B. `learnserver,localhost` |
| `DJANGO_SECURE`, `DJANGO_CSRF_TRUSTED_ORIGINS` | Hinter HTTPS-Proxy |
| `POSTGRES_*` | Datenbank |
| `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `VLLM_API_KEY` | KI-Schlüssel (nur die benötigten) |
| `TUTOR_REQUIRE_TOKEN` | `1` = Lernserver nur mit Gerätetoken (empfohlen) |
| `BACKUP_TIME`, `BACKUP_KEEP_DAYS`, `TZ` | Datensicherung |

---

## Entwicklung und Qualität

- Python 3.12+, PyQt6, Pydantic 2, Django 5.2, Channels/daphne, `anthropic`- und `openai`-SDK.
- Alle Texte, die Kinder sehen, stehen zentral in `client/src/learnharness_client/texts/`.
- Tests laufen ohne Fenster (`QT_QPA_PLATFORM=offscreen`); der Server testet mit SQLite, die CI
  zusätzlich mit PostgreSQL.
- GitHub Actions (`.github/workflows/ci.yml`) führt bei jedem Push ruff, mypy und alle Tests aus
  (App unter Windows, Server unter Linux mit PostgreSQL 17).
- Offene Punkte und Entscheidungen: `TODO_CLAUDE.md`.

## Weitere Dokumentation

- **[docs/README.md](docs/README.md) – Wegweiser durch den Code: Was liegt wo?**
- [client/README.md](client/README.md) – Details zur App
- [server/README.md](server/README.md) – Verwaltung, Lernserver, API, Sicherung im Detail
- `protocol/schemas/` – JSON-Schemas aller Nachrichten
