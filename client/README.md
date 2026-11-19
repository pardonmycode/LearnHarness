# LearnHarness Client

Der PyQt6-Client ist ein sicherer GDScript-Editor und Programmierlernhelfer für Godot-Projekte.
Godot bleibt für Szenen, Maps und grafische Objekte zuständig. LearnHarness bearbeitet zunächst nur
`*.gd`-Dateien innerhalb eines ausdrücklich ausgewählten Projekts.

Der Tab **LearnAgent** bietet Level 1–10. Kinder geben einen Prompt ein, erhalten eine Erklärung und
lösen eine passende Frage oder Code-Lücke. Nur eine richtige Antwort darf vollständigen Agenten-Code
freigeben; bei einer falschen Antwort bleibt das Projekt unverändert.

Beim Start erscheint eine lokale Profil-Anmeldung. Jedes Kind verwendet einen Spitznamen und wählt
seine Erfahrungsstufe. Profil-ID und Erfahrungsstufe werden beim Sitzungsstart an den Lernserver
übermittelt; Passwörter und Klarnamen werden nicht benötigt.

## Entwicklung starten

Die App läuft unter Windows und Linux. Unter Linux die Befehle mit `.venv/bin/python` statt
`.\.venv\Scripts\python.exe` ausführen; nötige Systempakete und die Unterschiede (Godot-Ordner,
Groß-/Kleinschreibung) stehen in der [README im Repository-Stamm](../README.md#linux).

Im Repository-Stamm unter Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .\protocol -e ".\client[dev]"
.\.venv\Scripts\python.exe -m learnharness_client --fake-server
```

Ein Beispielprojekt kann direkt geöffnet werden:

```powershell
.\.venv\Scripts\python.exe -m learnharness_client --fake-server --project .\client\tests\fixtures\sample_godot_project
```

Der Fake-Lernserver demonstriert den Ablauf „Spieler nach rechts bewegen“, ohne vLLM oder einen
laufenden Server zu benötigen. Für den echten, über Tailscale erreichbaren Lernserver:

```powershell
.\.venv\Scripts\python.exe -m learnharness_client --server http://TAILSCALE-HOST:PORT
```

## Prüfen

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check client protocol
```

Logs, Backups und Recovery-Entwürfe liegen im benutzerspezifischen AppData-Ordner, nicht im
Godot-Projekt. Code- und Chatinhalte werden nicht protokolliert.

