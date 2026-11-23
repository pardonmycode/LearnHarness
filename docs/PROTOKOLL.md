# Protokoll

[← Zur Übersicht](README.md) · [Alle Protokoll-Dateien](DATEIEN_PROTOKOLL.md)

Das Paket `learnharness_protocol` definiert alle Nachrichten mit Pydantic. Client und Server
nutzen dieselben Modelle. Die aktuelle Version ist **1.6**
([`base.py`](../protocol/src/learnharness_protocol/base.py)). Unbekannte Felder werden abgelehnt,
deshalb sollten Client und Server immer zusammen aktualisiert werden.

## Dateien

| Datei | Inhalt |
|---|---|
| [`messages.py`](../protocol/src/learnharness_protocol/messages.py) | `StudentMessage`, `LearningResponse`, Sitzung, Aufgaben |
| [`exercises.py`](../protocol/src/learnharness_protocol/exercises.py) | Übungen, Abgaben, `ReviewResult` |
| [`missions.py`](../protocol/src/learnharness_protocol/missions.py) | Missionen und Schritte |
| [`progress.py`](../protocol/src/learnharness_protocol/progress.py) | Fähigkeiten und Fortschritt |
| [`profiles.py`](../protocol/src/learnharness_protocol/profiles.py) | Kinderprofile der Verwaltung |
| [`health.py`](../protocol/src/learnharness_protocol/health.py) | Serverstatus |
| [`export_schema.py`](../protocol/src/learnharness_protocol/export_schema.py) | Schreibt die JSON-Schemas |

Die erzeugten Schemas liegen in [`protocol/schemas/`](../protocol/schemas/).

## Absichten einer `StudentMessage`

| `intent` | Bedeutung | Server-Methode |
|---|---|---|
| `chat` | Frage an den Tutor | `_chat` |
| `learn` | LearnAgent-Runde | `_learn` |
| `explain` | Code erklären | `_explain` |
| `mission` | Mission aus einem Wunsch planen | `_plan_mission` |
| `mission_step` | Einen Missionsschritt bearbeiten | `_mission_step` |
| `project_plan` | Fragen zum Projekt stellen, Beschreibung vorschlagen | `_plan_project` |

`language` ist `gdscript` oder `python`.

Die Felder `project_description` und `project_done_missions` geben jeder Anfrage das Projekt mit.
`project_turns`, `project_question` und `project_skipped_questions` tragen das Fragegespräch. Die Antwort kann
`description_suggestion` und `project_ready` enthalten. Die Beschreibung ändert sich erst, wenn das
Kind den Vorschlag übernimmt.

`mission_from_project` markiert eine Mission, die das Kind ohne eigenen Wunsch über den
Projekt-Knopf startet. Dann gilt die Lernreihenfolge der Themen verbindlich.

## Protokoll ändern

1. Modell in `protocol/src/learnharness_protocol/` anpassen.
2. `PROTOCOL_VERSION` erhöhen. Eine neue Hauptversion macht alte Clients inkompatibel.
3. Schemas neu erzeugen:

   ```bash
   cd protocol
   python -m learnharness_protocol.export_schema
   ```

4. Server, echten Client und Übungsserver anpassen.
