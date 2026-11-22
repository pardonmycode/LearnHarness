# Client

[← Zur Übersicht](README.md) · [Alle Client-Dateien](DATEIEN_CLIENT.md)

Alle Pfade liegen unter `client/src/learnharness_client/`.

## Ordner

| Ordner | Aufgabe |
|---|---|
| [`domain/`](../client/src/learnharness_client/domain/) | Projekte, Pfadschutz, Laden, Speichern, Sicherungen, Pläne |
| [`net/`](../client/src/learnharness_client/net/) | Verbindung zum Lernserver und eingebauter Übungsserver |
| [`godot/`](../client/src/learnharness_client/godot/) | Godot finden, prüfen und sein Log lesen |
| [`config/`](../client/src/learnharness_client/config/) | Einstellungen, nach Themen getrennt |
| [`texts/`](../client/src/learnharness_client/texts/) | Alle Texte, die Kinder sehen |
| [`ui/`](../client/src/learnharness_client/ui/) | Fenster, Tabs, Editor, Dialoge und Übungen |

## Hauptfenster: `ui/main_window/`

| Datei | Aufgabe |
|---|---|
| [`__init__.py`](../client/src/learnharness_client/ui/main_window/__init__.py) | Fensteraufbau, Layout, Beenden |
| [`actions.py`](../client/src/learnharness_client/ui/main_window/actions.py) | Menüs und Signalverbindungen |
| [`projects.py`](../client/src/learnharness_client/ui/main_window/projects.py) | Projekte öffnen und anlegen, Projektplan |
| [`learning.py`](../client/src/learnharness_client/ui/main_window/learning.py) | LearnAgent, Tutor, Übungsauswertung |
| [`explain_missions.py`](../client/src/learnharness_client/ui/main_window/explain_missions.py) | Code verstehen und Missionen |
| [`responses.py`](../client/src/learnharness_client/ui/main_window/responses.py) | Serverantworten und Verbindungsstatus |
| [`checks.py`](../client/src/learnharness_client/ui/main_window/checks.py) | Syntaxprüfung und Godot-Log |
| [`window_dialogs.py`](../client/src/learnharness_client/ui/main_window/window_dialogs.py) | Einstellungen, Lehrkraft, ältere Versionen |

## Tabs: `ui/panels/`

| Tab | Ort |
|---|---|
| LearnAgent | [`learn_agent_panel/`](../client/src/learnharness_client/ui/panels/learn_agent_panel/) |
| Projekt | [`project_panel/`](../client/src/learnharness_client/ui/panels/project_panel/) |
| Missionen | [`mission_panel/`](../client/src/learnharness_client/ui/panels/mission_panel/) |
| Code verstehen | [`explain_panel.py`](../client/src/learnharness_client/ui/panels/explain_panel.py) |
| Tutor | [`tutor_panel.py`](../client/src/learnharness_client/ui/panels/tutor_panel.py) |
| Fortschritt | [`progress_panel.py`](../client/src/learnharness_client/ui/panels/progress_panel.py) |
| Probleme (unten) | [`problems_panel.py`](../client/src/learnharness_client/ui/panels/problems_panel.py) |

## Editor: `ui/editor/`

| Ort | Aufgabe |
|---|---|
| [`code_editor/`](../client/src/learnharness_client/ui/editor/code_editor/) | Eingabe, Zeilennummern, Markierungen, Einrückung |
| [`editor_tabs/`](../client/src/learnharness_client/ui/editor/editor_tabs/) | Dateien in Tabs, Speichern, externe Änderungen |
| [`highlighters.py`](../client/src/learnharness_client/ui/editor/highlighters.py) | Wählt die Syntaxfarben nach Sprache |
| [`gdscript_highlighter.py`](../client/src/learnharness_client/ui/editor/gdscript_highlighter.py) | Farben für GDScript |
| [`python_highlighter.py`](../client/src/learnharness_client/ui/editor/python_highlighter.py) | Farben für Python |

## Projekte und Dateien: `domain/`

| Datei | Aufgabe |
|---|---|
| [`project.py`](../client/src/learnharness_client/domain/project.py) | Godot oder Python erkennen, Python-Projekt anlegen |
| [`path_guard.py`](../client/src/learnharness_client/domain/path_guard.py) | Erlaubt nur Skripte innerhalb des Projekts |
| [`file_store.py`](../client/src/learnharness_client/domain/file_store.py) | Laden und atomisches Speichern |
| [`backup.py`](../client/src/learnharness_client/domain/backup.py) | Sicherungen vor dem Speichern |
| [`recovery.py`](../client/src/learnharness_client/domain/recovery.py) | Entwürfe für den Absturzfall |
| [`python_check.py`](../client/src/learnharness_client/domain/python_check.py) | Python-Syntaxprüfung ohne Ausführung |
| [`project_plan.py`](../client/src/learnharness_client/domain/project_plan.py) | Projektidee und To-do-Liste |

## Netzwerk: `net/`

| Ort | Aufgabe |
|---|---|
| [`tutor_client.py`](../client/src/learnharness_client/net/tutor_client.py) | Gemeinsame Schnittstelle |
| [`http_tutor_client/`](../client/src/learnharness_client/net/http_tutor_client/) | Echter Server über HTTP und WebSocket |
| [`fake_tutor_client/`](../client/src/learnharness_client/net/fake_tutor_client/) | Eingebauter Übungsserver |
| [`fake_content/`](../client/src/learnharness_client/net/fake_content/) | Inhalte des Übungsservers |
| [`connection_monitor.py`](../client/src/learnharness_client/net/connection_monitor.py) | Regelmäßige Verbindungsprüfung |
| [`admin_client.py`](../client/src/learnharness_client/net/admin_client.py) | Zugriff auf die zentrale Verwaltung |

## Wo Daten liegen

| Daten | Ort |
|---|---|
| Einstellungen, Profile, Projektpläne | `QSettings` über `config/` |
| Sicherungen und Entwürfe | App-Datenordner, außerhalb des Projekts |
| Skripte des Kindes | Im Projektordner |
