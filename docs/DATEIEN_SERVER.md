# Dateien: Server

Lernserver und zentrale Verwaltung. Die Beschreibung ist jeweils der Kopfkommentar der Datei.

[← Zur Übersicht](README.md)

## `server/`

| Datei | Inhalt |
|---|---|
| [manage.py](../server/manage.py) | Django command-line entry point for the LearnHarness admin server. |

## `server/children/`

| Datei | Inhalt |
|---|---|
| [admin.py](../server/children/admin.py) | Teacher administration: groups, children, skills, missions and API access tokens. |
| [api.py](../server/children/api.py) | JSON API for the learning app and the AI learning server. |
| [device_admin.py](../server/children/device_admin.py) | „Wartende Geräte“: PCs that asked for access, approved or rejected with one click. |
| [device_api.py](../server/children/device_api.py) | A PC asks for access without a token; a teacher approves it under „Wartende Geräte“. |
| [apps.py](../server/children/apps.py) |  |
| [urls.py](../server/children/urls.py) |  |

## `server/children/management/commands/`

| Datei | Inhalt |
|---|---|
| [create_api_token.py](../server/children/management/commands/create_api_token.py) |  |

## `server/children/models/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../server/children/models/__init__.py) | Central data: groups, pseudonymous children, their skills and API access tokens. |
| [child.py](../server/children/models/child.py) | A child with skills and history. |
| [common.py](../server/children/models/common.py) | Levels, ids and validators shared by the models. |
| [devices.py](../server/children/models/devices.py) | Device tokens and PCs waiting for approval. |
| [missions.py](../server/children/models/missions.py) | Missions the teacher assigns. |

## `server/children/views/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../server/children/views/__init__.py) | Teacher pages: group overview, history per child and CSV exports (staff only). |
| [common.py](../server/children/views/common.py) | Tables, group selection and CSV helpers. |
| [history_page.py](../server/children/views/history_page.py) | History of one child and its CSV export. |
| [overview_page.py](../server/children/views/overview_page.py) | Group overview and its CSV export. |

## `server/learnharness_server/`

| Datei | Inhalt |
|---|---|
| [asgi.py](../server/learnharness_server/asgi.py) | ASGI entry point: HTTP (Django) plus the tutor WebSocket (Channels). Run with daphne. |
| [settings.py](../server/learnharness_server/settings.py) | Settings for the LearnHarness admin server. |
| [test_settings.py](../server/learnharness_server/test_settings.py) | Settings for pytest: SQLite unless POSTGRES_DB is set (CI runs against PostgreSQL). |
| [urls.py](../server/learnharness_server/urls.py) |  |
| [wsgi.py](../server/learnharness_server/wsgi.py) |  |

## `server/tutor/`

| Datei | Inhalt |
|---|---|
| [admin.py](../server/tutor/admin.py) | Admin: AI settings (provider switch), prompt log and sessions. |
| [api.py](../server/tutor/api.py) | HTTP part of the learning-server protocol (``/api/v1``); the tutor stream is in consumers.py. |
| [apps.py](../server/tutor/apps.py) |  |
| [consumers.py](../server/tutor/consumers.py) | Tutor stream: ``WS /api/v1/sessions/<id>/stream``. |
| [models.py](../server/tutor/models.py) | The built-in learning server: AI settings, tutor sessions, exercises and the prompt log. |
| [urls.py](../server/tutor/urls.py) |  |
| [views.py](../server/tutor/views.py) | Staff pages: which prompts go out to the AI, and a connection test. |

## `server/tutor/engine/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../server/tutor/engine/__init__.py) | What the learning server does for each request; every AI call goes through the harness. |
| [ai_calls.py](../server/tutor/engine/ai_calls.py) | Calling the AI through the harness, with logging. |
| [missions.py](../server/tutor/engine/missions.py) | Planning and running missions. |
| [reviews.py](../server/tutor/engine/reviews.py) | Hints and checking of submissions. |
| [rounds.py](../server/tutor/engine/rounds.py) | Chat, exercise rounds, explanations and project plans. |
| [tasks.py](../server/tutor/engine/tasks.py) | Tasks, shared texts and error helper. |

## `server/tutor/harness/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../server/tutor/harness/__init__.py) | The harness between children and the AI. |
| [checks.py](../server/tutor/harness/checks.py) | Checks structured AI output; answers stay on the server. |
| [code_fence.py](../server/tutor/harness/code_fence.py) | Markdown code fences belong in chat texts, never into a child's script. |
| [errors.py](../server/tutor/harness/errors.py) | Errors of the harness. |
| [exercise_kinds.py](../server/tutor/harness/exercise_kinds.py) | Ordering and find-the-bug exercises; their solutions stay on the server. |
| [explain.py](../server/tutor/harness/explain.py) | The answer format and checks of the tab "Code verstehen". |
| [learn_levels.py](../server/tutor/harness/learn_levels.py) | Which kind of exercise each of the ten LearnAgent levels uses. |
| [game_blueprint.py](../server/tutor/harness/game_blueprint.py) | Skeleton and architecture the AI follows when a child's project is a game. |
| [mission_code.py](../server/tutor/harness/mission_code.py) | Keeps a mission exercise and the code released after it in line. |
| [mission_plan.py](../server/tutor/harness/mission_plan.py) | Checks the plan of a mission before a child gets to see it. |
| [prompts.py](../server/tutor/harness/prompts.py) | Builds what goes out to the AI. |
| [rules.py](../server/tutor/harness/rules.py) | Fixed rules, levels and tasks of the prompts. |
| [scene_check.py](../server/tutor/harness/scene_check.py) | Checks scene changes from the AI and plays them through on the node list. |
| [scene_code.py](../server/tutor/harness/scene_code.py) | What the code relies on: nodes of the scene, input actions and project files. |
| [scene_prompt.py](../server/tutor/harness/scene_prompt.py) | How the scene of the open script and the input map go out to the AI. |
| [schemas.py](../server/tutor/harness/schemas.py) | JSON formats the AI must answer in. |
| [stream_guard.py](../server/tutor/harness/stream_guard.py) | Filters code out of text while it streams. |
| [topics.py](../server/tutor/harness/topics.py) | The topics missions teach and the three stages every child works through per topic. |
| [teststand_settings.py](../server/learnharness_server/teststand_settings.py) | Settings for the local test stand: SQLite file, no device token, only on this computer. |
| [teststand_prepare.py](../server/tutor/management/commands/teststand_prepare.py) | Sets up the local test stand: which AI answers and an admin login for this computer. |
| [teststand_check.py](../server/tutor/management/commands/teststand_check.py) | Checks whether the AI of the test stand answers; the reason is printed in plain words. |

## `server/tutor/providers/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../server/tutor/providers/__init__.py) | AI providers behind one small interface: local vLLM, ChatGPT (OpenAI) and Claude (Anthropic). |
| [anthropic_provider.py](../server/tutor/providers/anthropic_provider.py) | Claude through the Anthropic API. |
| [base.py](../server/tutor/providers/base.py) | Common provider interface and JSON parsing. |
| [openai_provider.py](../server/tutor/providers/openai_provider.py) | vLLM and ChatGPT through the OpenAI-compatible API. |
