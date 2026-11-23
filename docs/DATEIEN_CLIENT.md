# Dateien: Client

Die App auf dem Rechner des Kindes. Die Beschreibung ist jeweils der Kopfkommentar der Datei.

[← Zur Übersicht](README.md)

## `client/src/learnharness_client/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/__init__.py) | LearnHarness desktop client. |
| [__main__.py](../client/src/learnharness_client/__main__.py) |  |
| [admin_sync.py](../client/src/learnharness_client/admin_sync.py) | Keep the local child profiles in step with the central administration. |
| [app.py](../client/src/learnharness_client/app.py) | Application startup, logging, and last-resort recovery. |
| [qtcompat.py](../client/src/learnharness_client/qtcompat.py) | Small typing helpers around PyQt6 stubs. |

## `client/src/learnharness_client/config/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/config/__init__.py) | Application settings and writable application-data locations. |
| [admin_settings.py](../client/src/learnharness_client/config/admin_settings.py) | Connection to the central administration. |
| [base.py](../client/src/learnharness_client/config/base.py) | Access to QSettings shared by all settings groups. |
| [plans.py](../client/src/learnharness_client/config/plans.py) | Missions and project plans per profile. |
| [preferences.py](../client/src/learnharness_client/config/preferences.py) | Editor, server and display preferences. |
| [profiles.py](../client/src/learnharness_client/config/profiles.py) | Learning profiles, levels and cached progress. |
| [teacher.py](../client/src/learnharness_client/config/teacher.py) | Password of the teacher area. |

## `client/src/learnharness_client/domain/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/domain/__init__.py) | Non-widget project and file safety logic. |
| [backup.py](../client/src/learnharness_client/domain/backup.py) | Rotating pre-save backups outside the Godot project. |
| [code_questions.py](../client/src/learnharness_client/domain/code_questions.py) | Suggest child-friendly questions about a piece of GDScript or Python. |
| [file_store.py](../client/src/learnharness_client/domain/file_store.py) | Load and atomically save guarded script documents. |
| [learning_focus.py](../client/src/learnharness_client/domain/learning_focus.py) | Choose what a child should practise next, based on the skills already learned. |
| [path_guard.py](../client/src/learnharness_client/domain/path_guard.py) | Centralized project-bound path validation. |
| [profile.py](../client/src/learnharness_client/domain/profile.py) | Local pseudonymous child profiles and experience levels. |
| [project.py](../client/src/learnharness_client/domain/project.py) | Project discovery and metadata for Godot and Python projects. |
| [project_plan.py](../client/src/learnharness_client/domain/project_plan.py) | A child's project idea and to-do list. The child decides what goes on the list. |
| [python_check.py](../client/src/learnharness_client/domain/python_check.py) | Syntax check for Python scripts. The code is only parsed, never executed. |
| [run_target.py](../client/src/learnharness_client/domain/run_target.py) | The programs the terminal may start: a Python script of the project or the Godot game. |
| [terminal_commands.py](../client/src/learnharness_client/domain/terminal_commands.py) | The few commands children can type. Nothing here reaches a system shell. |
| [recovery.py](../client/src/learnharness_client/domain/recovery.py) | Crash-recovery drafts stored outside the Godot project. |
| [script_document.py](../client/src/learnharness_client/domain/script_document.py) | In-memory representation of a GDScript file. |

## `client/src/learnharness_client/godot/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/godot/__init__.py) | Optional helpers that talk to a locally installed Godot. |
| [log_reader.py](../client/src/learnharness_client/godot/log_reader.py) | Read recent errors from Godot's runtime log (only if file logging is enabled). |
| [output_parser.py](../client/src/learnharness_client/godot/output_parser.py) | Parse Godot console and log output into file/line messages. |
| [paths.py](../client/src/learnharness_client/godot/paths.py) | Where Godot 4 keeps its files on Windows, Linux and macOS. |
| [project_list.py](../client/src/learnharness_client/godot/project_list.py) | Projects that the local Godot project manager already knows. |
| [syntax_check.py](../client/src/learnharness_client/godot/syntax_check.py) | Optional syntax check via ``godot --headless --check-only`` without blocking the UI. |

## `client/src/learnharness_client/net/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/net/__init__.py) | Learning-server clients. |
| [admin_client.py](../client/src/learnharness_client/net/admin_client.py) | HTTP client for the central administration (Django server in server/). |
| [connection_monitor.py](../client/src/learnharness_client/net/connection_monitor.py) | Periodic health checks without blocking editor work. |
| [tutor_client.py](../client/src/learnharness_client/net/tutor_client.py) | Qt signal-based interface shared by fake and network tutor clients. |

## `client/src/learnharness_client/net/fake_content/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/net/fake_content/__init__.py) | Demo content for the fake server: code explanations, skill-focused rounds, missions. |
| [explanations.py](../client/src/learnharness_client/net/fake_content/explanations.py) | Demo explanations of code. |
| [focus.py](../client/src/learnharness_client/net/fake_content/focus.py) | Demo rounds for one skill. |
| [mission_parts.py](../client/src/learnharness_client/net/fake_content/mission_parts.py) | Building blocks and code of the demo missions. |
| [missions.py](../client/src/learnharness_client/net/fake_content/missions.py) | The demo missions. |
| [plans.py](../client/src/learnharness_client/net/fake_content/plans.py) | Demo project-plan answers. |

## `client/src/learnharness_client/net/fake_tutor_client/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/net/fake_tutor_client/__init__.py) | In-process pedagogical fake used before the learning server is available. |
| [base.py](../client/src/learnharness_client/net/fake_tutor_client/base.py) | Timing, health, session and streaming of the fake server. |
| [conversation.py](../client/src/learnharness_client/net/fake_tutor_client/conversation.py) | Explanations, project plans, hints, tasks and progress. |
| [learning.py](../client/src/learnharness_client/net/fake_tutor_client/learning.py) | LearnAgent rounds of the fake server. |
| [level_exercises.py](../client/src/learnharness_client/net/fake_tutor_client/level_exercises.py) | Exercises and code of the fake LearnAgent levels. |
| [missions.py](../client/src/learnharness_client/net/fake_tutor_client/missions.py) | Missions of the fake server. |

## `client/src/learnharness_client/net/http_tutor_client/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/net/http_tutor_client/__init__.py) | HTTP and WebSocket implementation for a Tailscale-reachable learning server. |
| [helpers.py](../client/src/learnharness_client/net/http_tutor_client/helpers.py) | Address comparison for the device token. |
| [rest.py](../client/src/learnharness_client/net/http_tutor_client/rest.py) | HTTP requests to the learning server. |

## `client/src/learnharness_client/texts/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/texts/__init__.py) | Central child-facing UI texts (German, simple sentences). |
| [app.py](../client/src/learnharness_client/texts/app.py) | Window title, menus, tabs, status bar and general messages. |
| [editor.py](../client/src/learnharness_client/texts/editor.py) | Editor, conflicts, versions, script tree and problems. |
| [errors.py](../client/src/learnharness_client/texts/errors.py) | Errors from the domain and network layers. |
| [learning.py](../client/src/learnharness_client/texts/learning.py) | Tutor panel, LearnAgent, progress and exercises. |
| [missions.py](../client/src/learnharness_client/texts/missions.py) | Code explainer and missions. |
| [onboarding.py](../client/src/learnharness_client/texts/onboarding.py) | First start, tutorial and login. |
| [projects.py](../client/src/learnharness_client/texts/projects.py) | Project choice, project plan and agent changes. |
| [settings.py](../client/src/learnharness_client/texts/settings.py) | Settings and diagnostics. |
| [teacher.py](../client/src/learnharness_client/texts/teacher.py) | Teacher area and central administration. |
| [terminal.py](../client/src/learnharness_client/texts/terminal.py) | Terminal below the code. |
| [tools.py](../client/src/learnharness_client/texts/tools.py) | Godot and Python tools, tutor basics and progress. |

## `client/src/learnharness_client/ui/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/ui/__init__.py) | Qt widgets for LearnHarness. |
| [markdown.py](../client/src/learnharness_client/ui/markdown.py) | Safe Markdown for tutor answers: formatting yes, links, images and HTML no. |
| [project_picker.py](../client/src/learnharness_client/ui/project_picker.py) | Project selection: known projects first, folder dialog as fallback, new Python projects. |
| [script_tree.py](../client/src/learnharness_client/ui/script_tree.py) | Safe, compact script tree built only from PathGuard-approved files. |

## `client/src/learnharness_client/ui/dialogs/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/ui/dialogs/__init__.py) | Application dialogs. |
| [admin_dialog.py](../client/src/learnharness_client/ui/dialogs/admin_dialog.py) | Connect this PC to the central administration (teacher area only). |
| [backup_dialog.py](../client/src/learnharness_client/ui/dialogs/backup_dialog.py) | Read-only view of pre-save backups with an explicit restore button. |
| [changes_dialog.py](../client/src/learnharness_client/ui/dialogs/changes_dialog.py) | Side-by-side view of what the LearnAgent changed in a file. |
| [conflict_dialog.py](../client/src/learnharness_client/ui/dialogs/conflict_dialog.py) | Child-friendly external-change conflict dialog. |
| [first_start_dialog.py](../client/src/learnharness_client/ui/dialogs/first_start_dialog.py) | First start: enter and test the learning-server address once. |
| [login_dialog.py](../client/src/learnharness_client/ui/dialogs/login_dialog.py) | Passwordless local profile login for different learning levels. |
| [project_choice_dialog.py](../client/src/learnharness_client/ui/dialogs/project_choice_dialog.py) | Pick a project from recent ones and those Godot already knows, or start a new one. |
| [recovery_dialog.py](../client/src/learnharness_client/ui/dialogs/recovery_dialog.py) | Dialog for one recovered unsaved draft. |
| [settings_dialog.py](../client/src/learnharness_client/ui/dialogs/settings_dialog.py) | Small settings dialog; network changes apply after restart. |
| [tutorial_dialog.py](../client/src/learnharness_client/ui/dialogs/tutorial_dialog.py) | Short, skippable introduction shown once per profile. |

## `client/src/learnharness_client/ui/dialogs/teacher_dialog/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/ui/dialogs/teacher_dialog/__init__.py) | Password-protected teacher area for local profiles and LearnAgent levels. |
| [password.py](../client/src/learnharness_client/ui/dialogs/teacher_dialog/password.py) | Password dialog of the teacher area. |

## `client/src/learnharness_client/ui/editor/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/ui/editor/__init__.py) | Code editor widgets. |
| [find_bar.py](../client/src/learnharness_client/ui/editor/find_bar.py) | Compact find/replace bar for the active code editor. |
| [gdscript_highlighter.py](../client/src/learnharness_client/ui/editor/gdscript_highlighter.py) | Godot 4 GDScript syntax highlighter. |
| [highlighters.py](../client/src/learnharness_client/ui/editor/highlighters.py) | Choose the syntax highlighter for a language or file. |
| [python_highlighter.py](../client/src/learnharness_client/ui/editor/python_highlighter.py) | Python syntax highlighter. |

## `client/src/learnharness_client/ui/editor/code_editor/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/ui/editor/code_editor/__init__.py) | QPlainTextEdit with line numbers and editing rules for GDScript and Python. |
| [gutter.py](../client/src/learnharness_client/ui/editor/code_editor/gutter.py) | Line numbers beside the code. |
| [indentation.py](../client/src/learnharness_client/ui/editor/code_editor/indentation.py) | Indenting and outdenting for GDScript and Python. |
| [selections.py](../client/src/learnharness_client/ui/editor/code_editor/selections.py) | Current line, error lines and matching brackets. |

## `client/src/learnharness_client/ui/editor/editor_tabs/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/ui/editor/editor_tabs/__init__.py) | Multi-file editor tabs, atomic saving, watchers, and recovery. |
| [files.py](../client/src/learnharness_client/ui/editor/editor_tabs/files.py) | Opening, creating, closing and generated files. |
| [saving.py](../client/src/learnharness_client/ui/editor/editor_tabs/saving.py) | Saving, autosave and crash recovery. |
| [watching.py](../client/src/learnharness_client/ui/editor/editor_tabs/watching.py) | Noticing and reloading changes made outside the editor. |

## `client/src/learnharness_client/ui/exercises/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/ui/exercises/__init__.py) | Interactive exercise widgets. |
| [base.py](../client/src/learnharness_client/ui/exercises/base.py) | Base class for exercises that never modify project files. |
| [factory.py](../client/src/learnharness_client/ui/exercises/factory.py) | Map validated exercise models to safe widgets. |
| [fill_blanks.py](../client/src/learnharness_client/ui/exercises/fill_blanks.py) | Fill-in-the-blank exercise with the choices embedded directly in the code. |
| [find_bug.py](../client/src/learnharness_client/ui/exercises/find_bug.py) | Select one or more suspicious code lines. |
| [multiple_choice.py](../client/src/learnharness_client/ui/exercises/multiple_choice.py) | Single- or multiple-choice exercise. |
| [ordering.py](../client/src/learnharness_client/ui/exercises/ordering.py) | Keyboard-accessible ordering exercise. |
| [text_blanks.py](../client/src/learnharness_client/ui/exercises/text_blanks.py) | Free-text code blanks used from learning level four onward. |

## `client/src/learnharness_client/ui/main_window/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/ui/main_window/__init__.py) | Main application window tying safe editing and tutoring together. |
| [actions.py](../client/src/learnharness_client/ui/main_window/actions.py) | Menus, signal wiring and the recent-projects menu. |
| [checks.py](../client/src/learnharness_client/ui/main_window/checks.py) | Syntax checks for Godot and Python, and the Godot log. |
| [constants.py](../client/src/learnharness_client/ui/main_window/constants.py) | Shared constants and rules of the main window. |
| [explain_missions.py](../client/src/learnharness_client/ui/main_window/explain_missions.py) | Requests of the tabs Code verstehen and Missionen. |
| [learning.py](../client/src/learnharness_client/ui/main_window/learning.py) | LearnAgent rounds, tutor messages and exercise reviews. |
| [projects.py](../client/src/learnharness_client/ui/main_window/projects.py) | Opening and creating projects and scripts, and the project plan. |
| [responses.py](../client/src/learnharness_client/ui/main_window/responses.py) | Answers, connection state and progress from the learning server. |
| [running.py](../client/src/learnharness_client/ui/main_window/running.py) | What the terminal needs from the main window. |
| [todos.py](../client/src/learnharness_client/ui/main_window/todos.py) | Connects the project's to-do list with LearnAgent, missions and tutor. |
| [window_dialogs.py](../client/src/learnharness_client/ui/main_window/window_dialogs.py) | Dialogs opened from the main window. |

## `client/src/learnharness_client/ui/panels/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/ui/panels/__init__.py) | Task, tutor, problem, progress, and diagnostics panels. |
| [diagnostics_panel.py](../client/src/learnharness_client/ui/panels/diagnostics_panel.py) | Technical details kept out of the main child-facing UI. |
| [exercise_host.py](../client/src/learnharness_client/ui/panels/exercise_host.py) | Shared helper: a place in a panel that shows one exercise at a time. |
| [explain_panel.py](../client/src/learnharness_client/ui/panels/explain_panel.py) | Interactive code explainer: questions about the selected code plus a check question. |
| [problems_panel.py](../client/src/learnharness_client/ui/panels/problems_panel.py) | Problems from Godot, Python or server review. |
| [progress_panel.py](../client/src/learnharness_client/ui/panels/progress_panel.py) | Per-skill progress without scores or rankings. |
| [todo_bar.py](../client/src/learnharness_client/ui/panels/todo_bar.py) | Bar above all tabs: the to-do the child is working on and how to work on it. |
| [terminal_console.py](../client/src/learnharness_client/ui/panels/terminal_console.py) | Text area that behaves like a console: only the current input line can be edited. |
| [terminal_panel.py](../client/src/learnharness_client/ui/panels/terminal_panel.py) | Terminal without buttons: children type commands such as ``python main.py``. |
| [tutor_panel.py](../client/src/learnharness_client/ui/panels/tutor_panel.py) | Tutor conversation without any apply-to-editor action. |

## `client/src/learnharness_client/ui/panels/learn_agent_panel/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/ui/panels/learn_agent_panel/__init__.py) | Level-based LearnAgent that gates generated code behind learning checks. |
| [cards.py](../client/src/learnharness_client/ui/panels/learn_agent_panel/cards.py) | Rounded card used by several panels. |
| [levels.py](../client/src/learnharness_client/ui/panels/learn_agent_panel/levels.py) | Level and skill-focus selection. |
| [rounds.py](../client/src/learnharness_client/ui/panels/learn_agent_panel/rounds.py) | Starting a round and showing its results. |

## `client/src/learnharness_client/ui/panels/mission_panel/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/ui/panels/mission_panel/__init__.py) | Learning missions: a small goal worked through step by step. |
| [choosing.py](../client/src/learnharness_client/ui/panels/mission_panel/choosing.py) | Choosing, restoring and resetting a mission. |
| [steps.py](../client/src/learnharness_client/ui/panels/mission_panel/steps.py) | Working through the steps of a mission. |

## `client/src/learnharness_client/ui/panels/project_panel/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/ui/panels/project_panel/__init__.py) | Describe the project and build its to-do list together with the learning helper. |
| [planning.py](../client/src/learnharness_client/ui/panels/project_panel/planning.py) | Asking the helper and deciding on its suggestions. |
| [rendering.py](../client/src/learnharness_client/ui/panels/project_panel/rendering.py) | Drawing suggestions, the list and the buttons. |
| [todo_list.py](../client/src/learnharness_client/ui/panels/project_panel/todo_list.py) | Adding, editing, moving and removing to-dos. |

## `client/src/learnharness_client/ui/theme/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../client/src/learnharness_client/ui/theme/__init__.py) | Design tokens, palettes and the generated application stylesheet. |
| [palettes.py](../client/src/learnharness_client/ui/theme/palettes.py) | Color sets of the themes. |
| [stylesheet.py](../client/src/learnharness_client/ui/theme/stylesheet.py) | Qt palette and stylesheet built from a color set. |
