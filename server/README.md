# LearnHarness-Verwaltung (Django + PostgreSQL)

Zentrale Verwaltung aller Kinder, die die LearnHarness-App benutzen. Sie läuft **neben** dem
KI-Lernserver: Die Lehrkraft pflegt hier Gruppen, Spitznamen und Level. Die Lern-App und der
Lernserver lesen und schreiben über eine kleine JSON-API.

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
`ChildProfileUpdate`, `LevelUnlock`, `ProgressUpdate`, Fehler als `ErrorMessage`).

| Methode | Pfad | Wer | Zweck |
|---|---|---|---|
| GET | `children/?group=…` | App, Lernserver | aktive Kinder, optional nach Gruppe |
| POST | `children/` | App, Lernserver | Profil anlegen (mehrfach senden ist harmlos) |
| GET, PATCH | `children/<id>/` | App, Lernserver | Profil lesen, Spitzname/Vorkenntnisse ändern |
| POST | `children/<id>/unlock/` | App, Lernserver | Level erhöhen (nie senken) |
| GET | `children/<id>/progress/` | App, Lernserver | Stand pro Fähigkeit |
| PUT | `children/<id>/progress/` | nur Lernserver | Stand pro Fähigkeit eintragen |

Level senken, Fortschritt zurücksetzen und archivieren geht nur im Admin durch die Lehrkraft.

## Tests

```powershell
cd server
..\.venv\Scripts\python.exe -m pytest
```

Ohne `POSTGRES_DB` laufen die Tests mit SQLite, in der CI gegen PostgreSQL 17.
