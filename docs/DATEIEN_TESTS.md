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
| [test_device_pairing.py](../client/tests/net/test_device_pairing.py) | This PC asks for access, shows the code and gets its token once a teacher approves. |
| [test_admin_sync_missions.py](../client/tests/net/test_admin_sync_missions.py) | Assigned missions from the administration. |
| [test_fake_tutor_client.py](../client/tests/net/test_fake_tutor_client.py) |  |
| [test_fake_levels.py](../client/tests/net/test_fake_levels.py) | The offline helper uses the same kind of exercise per level as the learning server. |
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
| [test_generated_code_base.py](../client/tests/ui/test_generated_code_base.py) | Generated code is only written into the script it was made from. |
| [test_learn_agent_panel.py](../client/tests/ui/test_learn_agent_panel.py) |  |
| [test_login_dialog.py](../client/tests/ui/test_login_dialog.py) |  |
| [test_open_items.py](../client/tests/ui/test_open_items.py) | Tests for the formerly open TODO items: Markdown chat, backups, Godot helpers, startup. |
| [test_project_choice.py](../client/tests/ui/test_project_choice.py) | Finding Godot's known projects and choosing one at first start. |
| [test_project_panel.py](../client/tests/ui/test_project_panel.py) | The Projekt tab: description, saved state and the way into the other tabs. |
| [test_project_talk.py](../client/tests/ui/test_project_talk.py) | The helper's questions make the project description clearer. |
| [test_tutor_hints.py](../client/tests/ui/test_tutor_hints.py) | The hint button works on the child's project. |
| [test_code_review.py](../client/tests/ui/test_code_review.py) | The button "Code prüfen lassen" sends the open script and marks the lines. |
| [test_teststand_config.py](../client/tests/teststand/test_teststand_config.py) | The test stand keeps keys out of files unless asked and never puts them on a command line. |
| [test_teststand_log.py](../client/tests/teststand/test_teststand_log.py) | The test stand reads the prompt log of the local server and shows it. |
| [test_teststand_window.py](../client/tests/teststand/test_teststand_window.py) | The test stand window reads its form and refuses to start without the essentials. |
| [test_teststand_commands.py](../server/tests/test_teststand_commands.py) | The commands that set up and check the local test stand. |
| [test_run_error.py](../client/tests/domain/test_run_error.py) | Only the real error of a program reaches the tutor, without private paths. |
| [test_scene_files.py](../client/tests/domain/test_scene_files.py) | Godot 4 scenes: read, found for a script and changed without touching anything else. |
| [test_scene_flow.py](../client/tests/ui/test_scene_flow.py) | The scene goes along with a request and changes only after a correct answer. |
| [test_terminal_errors.py](../client/tests/ui/test_terminal_errors.py) | The tutor knows the latest error from the terminal and forgets it once it is fixed. |
| [project_tab_helpers.py](../client/tests/ui/project_tab_helpers.py) | Shared helpers for the tests of the Projekt tab. |
| [test_python_editor.py](../client/tests/ui/test_python_editor.py) | Editing Python: indentation, highlighting, and the LearnAgent writing Python only. |
| [test_review_fixes.py](../client/tests/ui/test_review_fixes.py) | Regression tests for fixes from the TODO_CLAUDE review. |
| [test_teacher_and_changes.py](../client/tests/ui/test_teacher_and_changes.py) | Teacher area, LearnAgent changes view and optional autosave. |

## `protocol/tests/`

| Datei | Inhalt |
|---|---|
| [test_profiles.py](../protocol/tests/test_profiles.py) |  |
| [test_protocol.py](../protocol/tests/test_protocol.py) |  |
| [test_scenes.py](../protocol/tests/test_scenes.py) | Scene changes: only simple, checked values and known node types. |

## `server/tests/`

| Datei | Inhalt |
|---|---|
| [conftest.py](../server/tests/conftest.py) | Fixtures shared by the server tests. |
| [test_admin.py](../server/tests/test_admin.py) | Smoke tests for the teacher administration. |
| [test_api.py](../server/tests/test_api.py) | API contract tests: bodies are validated with the shared protocol models. |
| [test_device_requests.py](../server/tests/test_device_requests.py) | A PC asks for access; a teacher approves it under „Wartende Geräte“ without any token typing. |
| [test_missions_and_history.py](../server/tests/test_missions_and_history.py) | Missions maintained by teachers, the progress history and the CSV/print exports. |
| [test_overview.py](../server/tests/test_overview.py) | Group overview for teachers (/uebersicht/). |
| [test_tutor_channels.py](../server/tests/test_tutor_channels.py) | WebSocket, admin pages and prompt logging. |
| [test_tutor_harness.py](../server/tests/test_tutor_harness.py) | Rules of the harness: filters, prompts, exercises. |
| [test_tutor_project_plan.py](../server/tests/test_tutor_project_plan.py) | The helper asks about the project and proposes a clearer description. |
| [test_tutor_mission_topics.py](../server/tests/test_tutor_mission_topics.py) | Missions adapt the exercise to the child's stage in the mission's topic. |
| [test_tutor_mission_order.py](../server/tests/test_tutor_mission_order.py) | Missions pick a topic and follow the learning order. |
| [test_tutor_mission_plan.py](../server/tests/test_tutor_mission_plan.py) | A mission plan has a clear structure before a child gets to see it. |
| [test_tutor_mission_code.py](../server/tests/test_tutor_mission_code.py) | The code released after a mission exercise matches the exercise and the child. |
| [test_tutor_mission_blanks.py](../server/tests/test_tutor_mission_blanks.py) | Mission exercises must not mark a right answer as wrong. |
| [test_tutor_mission_safety.py](../server/tests/test_tutor_mission_safety.py) | Mission exercises stay small, do not give the answer away and keep Python runnable. |
| [test_tutor_scene_checks.py](../server/tests/test_tutor_scene_checks.py) | Scene changes from the AI: parsed strictly and played through on the node list. |
| [test_tutor_scene_rounds.py](../server/tests/test_tutor_scene_rounds.py) | Scene changes travel with an exercise and go out only after a correct answer. |
| [test_tutor_scene_missions.py](../server/tests/test_tutor_scene_missions.py) | Planning a mission in a Godot project: right script, missing scenes and keys. |
| [test_tutor_scene_chat.py](../server/tests/test_tutor_scene_chat.py) | Chat, hints and reviews read the scene too, without being able to change it. |
| [test_tutor_scene_review.py](../server/tests/test_tutor_scene_review.py) | Code review in a Godot project: sure findings from the app, checked against the scene. |
| [test_tutor_code_fence.py](../server/tests/test_tutor_code_fence.py) | Markdown fences never end up in a child's script. |
| [test_tutor_learn_levels.py](../server/tests/test_tutor_learn_levels.py) | Each LearnAgent level has its own kind of exercise, checked by the server. |
| [test_tutor_learn_prompt.py](../server/tests/test_tutor_learn_prompt.py) | The LearnAgent prompt has no contradicting rules. |
| [test_tutor_explain.py](../server/tests/test_tutor_explain.py) | The tab "Code verstehen" explains openly and asks a question that cannot be copied. |
| [test_tutor_chat.py](../server/tests/test_tutor_chat.py) | The tutor chat works on the child's project and keeps its history small. |
| [test_tutor_code_review.py](../server/tests/test_tutor_code_review.py) | Feedback on the open script: about the project, without progress or a fake message. |
| [mission_helpers.py](../server/tests/mission_helpers.py) | Shared helpers for the tests of mission topics and stages. |
| [test_tutor_providers.py](../server/tests/test_tutor_providers.py) | Provider switch, health and session access. |
| [test_tutor_rounds.py](../server/tests/test_tutor_rounds.py) | Learning rounds and missions. |
| [tutor_helpers.py](../server/tests/tutor_helpers.py) | Shared helpers of the tutor tests. |
