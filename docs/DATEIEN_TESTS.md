# Dateien: Tests

Alle Testdateien. Die Beschreibung ist jeweils der Kopfkommentar der Datei.

[← Zur Übersicht](README.md)

## `client/tests/`

| Datei | Inhalt |
|---|---|
| [conftest.py](../client/tests/conftest.py) | Shared test setup: headless Qt with real system fonts. |

## `client/tests/domain/`

| Datei | Inhalt |
|---|---|
| [test_file_store.py](../client/tests/domain/test_file_store.py) |  |
| [test_learning_helpers.py](../client/tests/domain/test_learning_helpers.py) |  |
| [test_path_guard.py](../client/tests/domain/test_path_guard.py) |  |
| [test_platform_paths.py](../client/tests/domain/test_platform_paths.py) | Godot folders and path comparisons on Windows, Linux and macOS. |
| [test_profile.py](../client/tests/domain/test_profile.py) |  |
| [test_python_projects.py](../client/tests/domain/test_python_projects.py) | Python projects: discovery, creation, path protection and the syntax check. |

## `client/tests/net/`

| Datei | Inhalt |
|---|---|
| [admin_sync_helpers.py](../client/tests/net/admin_sync_helpers.py) | Fake administration server for the sync tests. |
| [conftest.py](../client/tests/net/conftest.py) | Fixtures of the network tests. |
| [test_admin_sync.py](../client/tests/net/test_admin_sync.py) | Syncing profiles and level unlocks. |
| [test_admin_sync_missions.py](../client/tests/net/test_admin_sync_missions.py) | Assigned missions from the administration. |
| [test_fake_tutor_client.py](../client/tests/net/test_fake_tutor_client.py) |  |
| [test_http_token.py](../client/tests/net/test_http_token.py) | The device token only goes to the learning server when it is the administration itself. |
| [test_reconnect.py](../client/tests/net/test_reconnect.py) | WebSocket reconnect backoff and adaptive health-check interval. |

## `client/tests/ui/`

| Datei | Inhalt |
|---|---|
| [exercise_helpers.py](../client/tests/ui/exercise_helpers.py) | Helpers of the exercise widget tests. |
| [test_code_editor.py](../client/tests/ui/test_code_editor.py) |  |
| [test_exercises.py](../client/tests/ui/test_exercises.py) | Submissions, factory and fill-blank layout. |
| [test_exercises_answers.py](../client/tests/ui/test_exercises_answers.py) | What each exercise type emits. |
| [test_explain_and_missions.py](../client/tests/ui/test_explain_and_missions.py) | End-to-end through the main window with the built-in fake server. |
| [test_gdscript_highlighter.py](../client/tests/ui/test_gdscript_highlighter.py) | The highlighter colors example GDScript lines in the expected ranges. |
| [test_generated_code_gate.py](../client/tests/ui/test_generated_code_gate.py) |  |
| [test_learn_agent_panel.py](../client/tests/ui/test_learn_agent_panel.py) |  |
| [test_login_dialog.py](../client/tests/ui/test_login_dialog.py) |  |
| [test_open_items.py](../client/tests/ui/test_open_items.py) | Tests for the formerly open TODO items: Markdown chat, backups, Godot helpers, startup. |
| [test_project_choice.py](../client/tests/ui/test_project_choice.py) | Finding Godot's known projects and choosing one at first start. |
| [test_project_panel.py](../client/tests/ui/test_project_panel.py) | The Projekt tab: idea, suggestions the child decides on, and a saved to-do list. |
| [test_python_editor.py](../client/tests/ui/test_python_editor.py) | Editing Python: indentation, highlighting, and the LearnAgent writing Python only. |
| [test_review_fixes.py](../client/tests/ui/test_review_fixes.py) | Regression tests for fixes from the TODO_CLAUDE review. |
| [test_teacher_and_changes.py](../client/tests/ui/test_teacher_and_changes.py) | Teacher area, LearnAgent changes view and optional autosave. |

## `protocol/tests/`

| Datei | Inhalt |
|---|---|
| [test_profiles.py](../protocol/tests/test_profiles.py) |  |
| [test_protocol.py](../protocol/tests/test_protocol.py) |  |

## `server/tests/`

| Datei | Inhalt |
|---|---|
| [conftest.py](../server/tests/conftest.py) | Fixtures shared by the server tests. |
| [test_admin.py](../server/tests/test_admin.py) | Smoke tests for the teacher administration. |
| [test_api.py](../server/tests/test_api.py) | API contract tests: bodies are validated with the shared protocol models. |
| [test_missions_and_history.py](../server/tests/test_missions_and_history.py) | Missions maintained by teachers, the progress history and the CSV/print exports. |
| [test_overview.py](../server/tests/test_overview.py) | Group overview for teachers (/uebersicht/). |
| [test_tutor_channels.py](../server/tests/test_tutor_channels.py) | WebSocket, admin pages and prompt logging. |
| [test_tutor_harness.py](../server/tests/test_tutor_harness.py) | Rules of the harness: filters, prompts, exercises. |
| [test_tutor_project_plan.py](../server/tests/test_tutor_project_plan.py) | Planning a project with the helper. |
| [test_tutor_providers.py](../server/tests/test_tutor_providers.py) | Provider switch, health and session access. |
| [test_tutor_rounds.py](../server/tests/test_tutor_rounds.py) | Learning rounds and missions. |
| [tutor_helpers.py](../server/tests/tutor_helpers.py) | Shared helpers of the tutor tests. |
