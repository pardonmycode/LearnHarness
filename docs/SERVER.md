# Server

[← Zur Übersicht](README.md) · [Alle Server-Dateien](DATEIEN_SERVER.md)

Der Server ist ein Django-Projekt mit zwei Apps:

| App | Aufgabe |
|---|---|
| [`tutor/`](../server/tutor/) | Lernserver: KI, Harness, Übungen, WebSocket |
| [`children/`](../server/children/) | Verwaltung: Kinder, Gruppen, Fortschritt, Missionen, Geräte |

## Lernlogik: `tutor/engine/`

| Datei | Aufgabe |
|---|---|
| [`__init__.py`](../server/tutor/engine/__init__.py) | Klasse `Tutor`, verteilt Nachrichten nach `intent` |
| [`ai_calls.py`](../server/tutor/engine/ai_calls.py) | KI-Aufrufe, Wiederholung, Protokoll, Anfragebremse |
| [`rounds.py`](../server/tutor/engine/rounds.py) | Chat, Übungsrunden, Erklärungen, Projektplan |
| [`missions.py`](../server/tutor/engine/missions.py) | Missionen planen und durchführen |
| [`reviews.py`](../server/tutor/engine/reviews.py) | Hinweise und Prüfung von Abgaben |
| [`tasks.py`](../server/tutor/engine/tasks.py) | Aufgaben und gemeinsame Fehlertexte |

## Sicherheitsschicht: `tutor/harness/`

| Datei | Aufgabe |
|---|---|
| [`rules.py`](../server/tutor/harness/rules.py) | Feste Regeln, Level, Sprachen, Aufgaben der KI |
| [`prompts.py`](../server/tutor/harness/prompts.py) | Baut System- und Nutzer-Prompt |
| [`stream_guard.py`](../server/tutor/harness/stream_guard.py) | Hält längeren Code beim Streamen zurück |
| [`schemas.py`](../server/tutor/harness/schemas.py) | JSON-Formate der KI-Antworten |
| [`checks.py`](../server/tutor/harness/checks.py) | Prüft Übungen, To-dos und generierten Code |
| [`game_blueprint.py`](../server/tutor/harness/game_blueprint.py) | Grundgerüst und Architektur für Spiele |

## KI-Anbieter: `tutor/providers/`

| Datei | Aufgabe |
|---|---|
| [`__init__.py`](../server/tutor/providers/__init__.py) | Wählt den Anbieter, prüft die Erreichbarkeit |
| [`base.py`](../server/tutor/providers/base.py) | Gemeinsame Schnittstelle, JSON-Auswertung |
| [`openai_provider.py`](../server/tutor/providers/openai_provider.py) | vLLM und ChatGPT |
| [`anthropic_provider.py`](../server/tutor/providers/anthropic_provider.py) | Claude |

## Verwaltung: `children/`

| Ort | Aufgabe |
|---|---|
| [`models/child.py`](../server/children/models/child.py) | Kind, Fähigkeiten, Verlauf |
| [`models/missions.py`](../server/children/models/missions.py) | Missionen der Lehrkraft |
| [`models/devices.py`](../server/children/models/devices.py) | Geräte-Tokens |
| [`models/common.py`](../server/children/models/common.py) | Gruppen, Stufen, Validatoren |
| [`api.py`](../server/children/api.py) | JSON-API für die App |
| [`admin.py`](../server/children/admin.py) | Django-Admin |
| [`views/overview_page.py`](../server/children/views/overview_page.py) | Gruppenübersicht und CSV |
| [`views/history_page.py`](../server/children/views/history_page.py) | Verlauf eines Kindes und CSV |

## Adressen

| Pfad | Zweck | Definiert in |
|---|---|---|
| `/admin/` | Django-Admin | [`urls.py`](../server/learnharness_server/urls.py) |
| `/uebersicht/` | Gruppenübersicht | [`urls.py`](../server/learnharness_server/urls.py) |
| `/ki/prompts/` | Prompt-Übersicht | [`tutor/urls.py`](../server/tutor/urls.py) |
| `/api/v1/health`, `sessions`, `tasks`, `exercises`, `progress` | Lernserver | [`tutor/urls.py`](../server/tutor/urls.py) |
| `/api/v1/children/`, `missions/` | Verwaltung | [`children/urls.py`](../server/children/urls.py) |
| `/api/v1/sessions/<id>/stream` | WebSocket | [`tutor/urls.py`](../server/tutor/urls.py) |
