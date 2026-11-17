# LearnHarness

LearnHarness verbindet den Godot-Editor für Maps, Szenen und grafische Objekte mit einer separaten
PyQt6-Programmierwerkstatt. Im LearnAgent-Tab beschreiben Kinder ihr gewünschtes Spielfeature. Der
Agent erklärt das Konzept und stellt eine Level-Frage; erst nach einer richtigen Antwort wird der
vollständige, erklärte Code sicher in das Projekt geschrieben.

Beim Start wählt jedes Kind ein lokales Profil mit Spitznamen und Erfahrungsstufe. So kann der
Lernserver Erklärungen und Aufgaben an unterschiedliche Vorkenntnisse anpassen. Das einfache Login
benötigt bewusst kein Passwort und keinen Klarnamen.

## Schnellstart

Die Entwicklungsumgebung ist im Ordner `.venv` eingerichtet. Der Client kann mit dem eingebauten
Fake-Lernserver und dem Beispielprojekt gestartet werden:

```powershell
.\.venv\Scripts\python.exe -m learnharness_client --fake-server --project .\client\tests\fixtures\sample_godot_project
```

Ohne `--project` kann ein beliebiges vorhandenes Godot-Projekt über **Datei → Godot-Projekt
öffnen** ausgewählt werden.

Für einen echten Lernserver im Tailscale-Netz:

```powershell
.\.venv\Scripts\python.exe -m learnharness_client --server http://TAILSCALE-HOST:PORT
```

Die Server-API ist durch die Pydantic-Modelle in `protocol/` und die erzeugten JSON-Schemas in
`protocol/schemas/` beschrieben. Der Server und die vLLM-Konfiguration gehören bewusst nicht zu
diesem Client-Projekt.

## Qualität prüfen

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check client protocol
.\.venv\Scripts\mypy.exe --strict client\src\learnharness_client\domain protocol\src\learnharness_protocol
```

Weitere Details stehen in [client/README.md](client/README.md).
