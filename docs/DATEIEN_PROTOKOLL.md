# Dateien: Protokoll

Das gemeinsame Paket von Client und Server. Die Beschreibung ist jeweils der Kopfkommentar der Datei.

[← Zur Übersicht](README.md)

## `protocol/src/learnharness_protocol/`

| Datei | Inhalt |
|---|---|
| [__init__.py](../protocol/src/learnharness_protocol/__init__.py) | Validated messages shared by the LearnHarness client and server. |
| [base.py](../protocol/src/learnharness_protocol/base.py) | Base types and protocol-version checks. |
| [exercises.py](../protocol/src/learnharness_protocol/exercises.py) | Exercise payloads never include the correct solution. |
| [export_schema.py](../protocol/src/learnharness_protocol/export_schema.py) | Write the public JSON schemas for server implementers. |
| [health.py](../protocol/src/learnharness_protocol/health.py) | Health information exposed by the learning server. |
| [messages.py](../protocol/src/learnharness_protocol/messages.py) | Session, tutor, task, and error messages. |
| [missions.py](../protocol/src/learnharness_protocol/missions.py) | Learning missions: a small goal split into steps the child works through. |
| [profiles.py](../protocol/src/learnharness_protocol/profiles.py) | Central child profiles managed by the LearnHarness admin server (Django). |
| [progress.py](../protocol/src/learnharness_protocol/progress.py) | Learning progress by skill, deliberately without a total score. |
