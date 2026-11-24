# Wo ändere ich was?

[← Zur Übersicht](README.md)

`C` steht für `client/src/learnharness_client`.

## Oberfläche

| Ich will … | Datei |
|---|---|
| einen sichtbaren Text ändern | [`C/texts/`](../client/src/learnharness_client/texts/) |
| einen Menüpunkt ergänzen | [`C/ui/main_window/actions.py`](../client/src/learnharness_client/ui/main_window/actions.py) |
| einen neuen Tab ergänzen | [`C/ui/panels/`](../client/src/learnharness_client/ui/panels/), eingehängt in [`main_window/__init__.py`](../client/src/learnharness_client/ui/main_window/__init__.py) |
| Farben oder Stil ändern | [`palettes.py`](../client/src/learnharness_client/ui/theme/palettes.py), [`stylesheet.py`](../client/src/learnharness_client/ui/theme/stylesheet.py) |
| den Projekt-Tab ändern | [`C/ui/panels/project_panel/`](../client/src/learnharness_client/ui/panels/project_panel/) |
| eine neue Übungsart anzeigen | [`C/ui/exercises/`](../client/src/learnharness_client/ui/exercises/), registriert in [`factory.py`](../client/src/learnharness_client/ui/exercises/factory.py) |
| den Ablauf im Projekt-Tab ändern | [`project_panel/`](../client/src/learnharness_client/ui/panels/project_panel/), [`main_window/project_flow.py`](../client/src/learnharness_client/ui/main_window/project_flow.py) |
| Schriftgrößen, Farben, Abstände oder Fenstergrößen ändern | [`design.py`](../client/src/learnharness_client/design.py) |
| das Terminal ändern | [`terminal_panel.py`](../client/src/learnharness_client/ui/panels/terminal_panel.py), Befehle in [`terminal_commands.py`](../client/src/learnharness_client/domain/terminal_commands.py) |
| eine Einstellung ergänzen | [`C/config/preferences.py`](../client/src/learnharness_client/config/preferences.py), Dialog in [`settings_dialog.py`](../client/src/learnharness_client/ui/dialogs/settings_dialog.py) |

## Editor und Dateien

| Ich will … | Datei |
|---|---|
| Einrückung ändern | [`code_editor/indentation.py`](../client/src/learnharness_client/ui/editor/code_editor/indentation.py) |
| Tastenkürzel im Editor ändern | [`code_editor/__init__.py`](../client/src/learnharness_client/ui/editor/code_editor/__init__.py) |
| Syntaxfarben für Python ändern | [`python_highlighter.py`](../client/src/learnharness_client/ui/editor/python_highlighter.py) |
| Speichern oder Autosave ändern | [`editor_tabs/saving.py`](../client/src/learnharness_client/ui/editor/editor_tabs/saving.py) |
| ändern, welche Dateien erlaubt sind | [`path_guard.py`](../client/src/learnharness_client/domain/path_guard.py) |
| die Vorlage neuer Skripte ändern | [`file_store.py`](../client/src/learnharness_client/domain/file_store.py) |
| die Vorlage neuer Python-Projekte ändern | [`project.py`](../client/src/learnharness_client/domain/project.py) |

## Lernen und KI

| Ich will … | Datei |
|---|---|
| die festen KI-Regeln ändern | [`harness/rules.py`](../server/tutor/harness/rules.py) |
| eine neue Sprache ergänzen | `LANGUAGES` in [`rules.py`](../server/tutor/harness/rules.py), `ProjectLanguage` in [`path_guard.py`](../client/src/learnharness_client/domain/path_guard.py), `language` in [`messages.py`](../protocol/src/learnharness_protocol/messages.py) |
| Grundgerüst und Architektur für Spiele ändern | [`harness/game_blueprint.py`](../server/tutor/harness/game_blueprint.py) |
| Missionsthemen und die 3 Stufen ändern | [`topics.py`](../server/tutor/harness/topics.py) |
| die 10 LearnAgent-Level und ihre Aufgabentypen ändern | [`learn_levels.py`](../server/tutor/harness/learn_levels.py) |
| den Teststand für Prompts ändern | [`teststand/`](../client/src/learnharness_client/teststand/), [`teststand_settings.py`](../server/learnharness_server/teststand_settings.py) |
| ändern, was die KI zum Projekt fragt | `INTENTS["project_plan"]` in [`rules.py`](../server/tutor/harness/rules.py) |
| den Code-Filter ändern | [`harness/stream_guard.py`](../server/tutor/harness/stream_guard.py) |
| den Projektplan der KI ändern | `project_plan` in [`rules.py`](../server/tutor/harness/rules.py), Ablauf in [`engine/rounds.py`](../server/tutor/engine/rounds.py) |
| eine feste Aufgabe ergänzen | [`engine/tasks.py`](../server/tutor/engine/tasks.py) |
| einen KI-Anbieter ergänzen | [`tutor/providers/`](../server/tutor/providers/) |
| Inhalte des Übungsservers ändern | [`net/fake_content/`](../client/src/learnharness_client/net/fake_content/) |

## Verwaltung

| Ich will … | Datei |
|---|---|
| Daten eines Kindes erweitern | [`models/child.py`](../server/children/models/child.py), danach `makemigrations` |
| die Gruppenübersicht ändern | [`views/overview_page.py`](../server/children/views/overview_page.py) |
| den Verlauf eines Kindes ändern | [`views/history_page.py`](../server/children/views/history_page.py) |
| den Django-Admin ändern | [`children/admin.py`](../server/children/admin.py), [`tutor/admin.py`](../server/tutor/admin.py) |
| die App-Synchronisierung ändern | [`admin_sync.py`](../client/src/learnharness_client/admin_sync.py) |
