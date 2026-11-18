# LearnHarness-Verwaltung und Lernserver (Django + PostgreSQL)

Zentrale Verwaltung aller Kinder, die die LearnHarness-App benutzen, und eingebauter
**Lernserver mit KI-Harness**: Die Lehrkraft pflegt hier Gruppen, Spitznamen, Level und Missionen
und wählt, welche KI antwortet (lokales Modell über vLLM, Claude oder ChatGPT). Die Lern-App
spricht mit demselben Server. Ein eigener, externer Lernserver kann weiterhin über die JSON-API
angebunden werden.

**Datenschutz:** Gespeichert werden nur Spitznamen, Vorkenntnisse, Level und der Stand pro
Fähigkeit, keine echten Namen. Welches Kind hinter welchem Spitznamen steckt, weiß nur die
Lehrkraft. Archivieren statt Löschen behält den Verlauf; echtes Löschen geht im Admin.

## Lokal ausprobieren (SQLite)

```powershell
cd server
$env:DJANGO_DEBUG = "1"
..\.venv\Scripts\python.exe -m pip install -e ".[dev]"
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py createsuperuser
..\.venv\Scripts\python.exe manage.py runserver
```

Danach: <http://localhost:8000/admin/>

## Auf dem Server (Docker, PostgreSQL)

```bash
cp server/.env.example server/.env   # Werte eintragen, v. a. DJANGO_SECRET_KEY und Passwort
docker compose -f server/docker-compose.yml up -d --build
docker compose -f server/docker-compose.yml exec web python manage.py createsuperuser
```

Für HTTPS einen Proxy (z. B. Caddy) davorsetzen und `DJANGO_SECURE=1` sowie
`DJANGO_CSRF_TRUSTED_ORIGINS=https://…` setzen. Im Tailscale-Netz reicht auch HTTP.

## Lernserver und KI-Anbieter

Im Admin unter **Lernserver (KI) › KI-Einstellungen** wählt die Lehrkraft den aktiven Anbieter:

| Anbieter | Einstellungen | Schlüssel in `server/.env` |
|---|---|---|
| Lokales Modell (vLLM) | Adresse (z. B. `http://ki-pc:8001/v1`) und Modellname wie beim Start von vLLM | `VLLM_API_KEY` nur bei `--api-key` |
| Claude (Anthropic) | Modell (Standard `claude-opus-5-5`), Denkaufwand | `ANTHROPIC_API_KEY` |
| ChatGPT (OpenAI) | Modellname | `OPENAI_API_KEY` |

Umschalten wirkt sofort, ohne Neustart und ohne Änderung an der App. „Verbindung testen“ prüft
die gespeicherten Einstellungen (vorher speichern). Bei Claude-Modellen, die es unterstützen, ist
die serverseitige Ausweichlösung bei Ablehnungen eingeschaltet (`fallbacks: "default"`).

**Harness** (`tutor/harness.py`), damit die Kinder keine fertigen Lösungen bekommen:

- Feste Regeln im System-Prompt (kurz, kindgerecht, keine fertigen Lösungen, keine persönlichen
  Daten); Text der Kinder steht in `<kind>…</kind>` und gilt als Inhalt, nicht als Anweisung.
  Eigene Ergänzungen der Lehrkraft werden angehängt, ersetzen die Regeln aber nicht.
- Tutor-Antworten werden beim Streamen zeilenweise geprüft: Code mit mehr als N Zeilen am Stück
  (mit oder ohne ```-Block) wird ersetzt, bevor das Kind ihn sieht (N einstellbar, Standard 3).
- Übungen liefert die KI als JSON mit Aufgabe und Lösung getrennt; das Kind bekommt nur die
  Aufgabe, die Antwort prüft der Server selbst.
- Code nach einer richtigen Antwort (LearnAgent, Missionsschritte „Üben“) bleibt bis dahin auf dem
  Server, darf höchstens N Zeilen der geöffneten Datei ändern (Standard 12) und wird nur in diese
  Datei geschrieben. Bei Verstoß fragt der Server die KI ein zweites Mal, sonst gibt es keinen Code.
- Höchstens N Anfragen pro Kind und Minute (Kostenbremse, Standard 12).

**Überblick über die Prompts:**

- `/ki/prompts/` zeigt die System-Prompts für jeden Zweck (Chat, Hinweis, Code verstehen,
  LearnAgent, Mission, Missionsschritt, Code-Prüfung) bei wählbarer Lernstufe, das verlangte
  JSON-Format und eine Beispielnachricht.
- **KI-Protokoll** im Admin zeigt jede Anfrage: System-Prompt, Nachrichten, Rohantwort der KI, was
  beim Kind ankam, Eingriffe des Harness, Tokens und Dauer. Filter „Harness hat eingegriffen“
  zeigt, wo Lösungen abgefangen wurden.
- Das Protokoll enthält, was die Kinder schreiben. Es wird nach 30 Tagen gelöscht (einstellbar)
  und lässt sich ganz abschalten; Tokens und Dauer werden dann weiter gezählt.

Die App verbindet sich mit diesem Server, wenn in ihren Einstellungen dieselbe Adresse als
Lernserver und unter „Zentrale Verwaltung“ eingetragen ist; dann schickt sie ihren Gerätetoken
mit. Ohne gültigen Token antwortet der Lernserver nicht (`TUTOR_REQUIRE_TOKEN=0` schaltet das ab).
Gestartet wird mit `daphne` (HTTP und WebSocket), im Docker-Image automatisch; lokal reicht
`python manage.py runserver`.

## Übersicht für Lehrkräfte

Unter <http://localhost:8000/uebersicht/> (oben rechts im Admin „Übersicht“, oder in der
Gruppenliste je Gruppe) steht eine Tabelle: eine Zeile pro aktivem Kind, eine Spalte pro
Fähigkeit, dazu Level und „Zuletzt gesehen“. Jede Zelle zeigt den Stand als Text und Farbe
(0 Noch nicht begonnen, 1 Mit Hilfe, 2 Fast selbstständig, 3 Sicher). Oben wählt man die
Gruppe; `/uebersicht/<gruppen-id>/` zeigt eine Gruppe, `/uebersicht/ohne-gruppe/` Kinder ohne
Gruppe. Nur mit Admin-Anmeldung (Mitarbeiter-Status) erreichbar. „Als CSV exportieren“ lädt
die angezeigte Tabelle herunter (Semikolon, UTF-8 – öffnet sich direkt in Excel).

Ein Klick auf den Spitznamen öffnet den **Verlauf** des Kindes (`/uebersicht/kind/<id>/`):
aktueller Stand, Entwicklung jeder Fähigkeit mit Datum, Level-Verlauf und abgeschlossene
Missionen, wahlweise für einen Zeitraum (von/bis). „Drucken / als PDF speichern“ druckt eine
aufgeräumte Fassung ohne Admin-Menü (z. B. fürs Elterngespräch), „Als CSV exportieren“ lädt
alle Einträge. Der Verlauf entsteht automatisch: jede Änderung einer Fähigkeit (vom
Lernserver), jede Level-Änderung (App oder Admin) und jede abgeschlossene Mission wird mit
Zeitpunkt gespeichert. „Fortschritt zurücksetzen“ löscht auch den Verlauf.

## Missionen

Im Admin unter „Missionen“ legt die Lehrkraft Missionen an: Titel, Ziel für das Kind, eine feste
Kennung (z. B. `doppelsprung`) und 1–8 Schritte. Jeder Schritt hat eine Art (Verstehen, Lernen,
Üben, In Godot ausprobieren) und optional einen **Hinweis für den Lernserver** (z. B. welche
Übung, was betont werden soll) – den sieht das Kind nicht. Ohne ausgewählte Gruppen gilt die
Mission für alle, sonst nur für die gewählten Gruppen. Die App zeigt die Missionen im Tab
„Missionen“ unter „Von deiner Lehrkraft“ (auch offline aus der letzten Kopie) und meldet
abgeschlossene Missionen zurück; die Liste zeigt, wie viele Kinder sie geschafft haben.

## Datensicherung (Backups)

Der Dienst `backup` im `docker-compose.yml` sichert die Datenbank einmal täglich um
`BACKUP_TIME` (Standard 02:30, Zeitzone `TZ`) mit `pg_dump -Fc` nach `server/backups/`
(Dateien `learnharness_JJJJ-MM-TT_HHMMSS.dump`). Sicherungen, die älter als
`BACKUP_KEEP_DAYS` Tage sind (Standard 14), werden danach gelöscht. Das Skript dazu ist
`server/scripts/backup.sh`; es läuft im `postgres:17`-Image, es braucht kein weiteres Image.
Den Ordner `server/backups/` zusätzlich regelmäßig auf ein anderes Gerät kopieren, sonst
hilft die Sicherung nicht, wenn die Festplatte ausfällt.

Sofort sichern (z. B. vor einem Update):

```bash
docker compose -f server/docker-compose.yml exec backup sh /usr/local/bin/backup.sh once
```

Protokoll ansehen: `docker compose -f server/docker-compose.yml logs backup`.

Wiederherstellen (überschreibt den aktuellen Stand der Datenbank):

```bash
# 1. Webdienst anhalten, damit niemand während der Wiederherstellung schreibt
docker compose -f server/docker-compose.yml stop web
# 2. Sicherung einspielen (Dateiname anpassen); --clean ersetzt vorhandene Tabellen
docker compose -f server/docker-compose.yml exec backup sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" pg_restore -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
   --clean --if-exists --no-owner /backups/learnharness_2026-01-31_023000.dump'
# 3. Webdienst wieder starten (führt ggf. ausstehende Migrationen aus)
docker compose -f server/docker-compose.yml start web
```

Eine Sicherung lässt sich gefahrlos prüfen, indem man ihren Inhalt auflistet:
`... exec backup pg_restore --list /backups/<datei>.dump`.

## Zugänge (Tokens)

Jeder PC und der Lernserver bekommen einen eigenen Token, entweder im Admin unter
„API-Zugänge“ oder per Befehl:

```bash
python manage.py create_api_token "PC Raum 12"
python manage.py create_api_token "Lernserver" --kind learnserver
```

Der Token wird nur einmal angezeigt und nur als Hash gespeichert. Ein verlorener Token wird im
Admin mit „Neuen Token erzeugen“ ersetzt.

## API (`/api/v1/`, Header `Authorization: Bearer <token>`)

Die Inhalte sind die Pydantic-Modelle aus `protocol/` (`ChildProfile`, `ChildProfileList`,
`ChildProfileUpdate`, `LevelUnlock`, `ProgressUpdate`, `MissionList`, `Mission`, Fehler als
`ErrorMessage`).

| Methode | Pfad | Wer | Zweck |
|---|---|---|---|
| GET | `children/?group=…` | App, Lernserver | aktive Kinder, optional nach Gruppe |
| POST | `children/` | App, Lernserver | Profil anlegen (mehrfach senden ist harmlos) |
| GET, PATCH | `children/<id>/` | App, Lernserver | Profil lesen, Spitzname/Vorkenntnisse ändern |
| POST | `children/<id>/unlock/` | App, Lernserver | Level erhöhen (nie senken) |
| GET | `children/<id>/progress/` | App, Lernserver | Stand pro Fähigkeit |
| PUT | `children/<id>/progress/` | nur Lernserver | Stand pro Fähigkeit eintragen (Änderungen landen im Verlauf) |
| GET | `children/<id>/missions/` | App, Lernserver | Missionen für die Gruppe des Kindes + erledigte IDs (ohne Hinweise) |
| POST | `children/<id>/missions/<mission-id>/done/` | App, Lernserver | Mission als abgeschlossen melden (mehrfach harmlos) |
| GET | `missions/`, `missions/<mission-id>/` | nur Lernserver | aktive Missionen mit Lehrkraft-Hinweisen je Schritt |

Level senken, Fortschritt zurücksetzen und archivieren geht nur im Admin durch die Lehrkraft.

Lernserver-Protokoll für die App (gleicher Token): `GET health`, `POST sessions`,
`WS sessions/<id>/stream`, `POST sessions/<id>/hints`, `GET tasks/<id>`,
`POST tasks/<id>/submissions`, `POST exercises/<id>/submissions`, `GET progress?session_id=…`.

## Tests

```powershell
cd server
..\.venv\Scripts\python.exe -m pytest
```

Ohne `POSTGRES_DB` laufen die Tests mit SQLite, in der CI gegen PostgreSQL 17.
