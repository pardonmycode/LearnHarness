# TODO: PyQt6-Lernclient für die Godot-Lernumgebung

Dieses Dokument beschreibt die Umsetzung der **PyQt6-Anwendung auf dem Rechner des Kindes**.
Lernserver, vLLM, Tailscale-Einrichtung, Prompts und Agentenlogik sind **nicht** Teil dieses Dokuments – sie werden separat erstellt. Wo der Client davon abhängt, ist die Schnittstelle unter [Schnittstelle zum Lernserver](#schnittstelle-zum-lernserver) festgehalten.

Grundlage: [TODO_GPT.md](TODO_GPT.md) (Zielbild) und die drei PDFs (Agentenrollen, Nachrichtenbeispiele, Sicherheitsregeln).

## Stand nach Review (18.11.2026)

Abgehakt ist, was im Code umgesetzt und durch Tests oder Ansicht geprüft ist. Bewusste Abweichungen:

- Skriptbaum nutzt `QTreeWidget` aus `PathGuard.iter_scripts()` statt `QFileSystemModel` – so
  entscheidet allein der PathGuard, was sichtbar ist. Ein `QFileSystemWatcher` auf den Ordnern
  aktualisiert den Baum automatisch, wenn in Godot Skripte angelegt oder gelöscht werden.
- UI-Texte: alle für Kinder sichtbaren Texte stehen in `learnharness_client/texts.py`
  (auch Fehlermeldungen aus `domain/`, `net/` und `godot/`). Nicht zentral sind nur
  Log-Meldungen, CLI-Hilfe und die Inhalte des eingebauten Übungsservers – diese
  simulieren Serverantworten.
- Barrierefreiheit: Fokusrahmen, Tab-Reihenfolge in Übungen und Accessible Names für die
  Hauptbedienelemente sind da; eine vollständige Prüfung mit Screenreader steht aus → offen.
- Punkte unter „Fertig, wenn“ mit echtem Godot (Phase 1) und der Build-Test auf einem PC ohne
  Python sind erst nach einem manuellen Test abhakbar. Die Godot-Syntaxprüfung (F6) ist gegen
  die echte Godot-Version noch nicht getestet; der Ausgabe-Parser folgt dem Godot-4-Format.

Beim Review behoben: Schriftgröße wirkte nicht (Stylesheet überschrieb sie), Dunkelmodus unlesbar,
fehlgeschlagener Health-Check schrieb alle 15 s Fehler in den Chat und brach Lernrunden ab,
Übungsabgaben ohne `session_id`, Problem-Links bei Unterordnern, LearnAgent-Antworten landeten
zusätzlich im Tutor-Chat, Agenten-Code war nicht per Strg+Z rückgängig zu machen.

---

## Leitplanken für den Client

Diese Regeln gelten für jede Aufgabe unten und werden nicht pro Punkt wiederholt.

1. **LearnAgent-Code erst nach Lernerfolg.** Der LearnAgent darf vollständigen Code schreiben, aber
   niemals direkt nach einem Prompt. Zuerst folgen Erklärung und eine zum Level passende Lernfrage.
   Nur eine serverseitig als richtig bestätigte Antwort darf `generated_files` freigeben. Bei einer
   falschen Antwort bleibt das Projekt unverändert. Schreiben erfolgt mit Pfadschutz,
   Konfliktprüfung, Sicherung und atomischem Speichern. Ungeschützte `code_changes` aus normalen
   Tutor-Antworten werden weiterhin ignoriert.
2. **Kein Codeverlust.** Server-, Netz- oder Modellfehler dürfen niemals ungespeicherten Code gefährden. Der Editor funktioniert vollständig offline.
3. **Kein unbemerktes Überschreiben.** Änderungen, die Godot (oder ein anderes Programm) an einer Datei vorgenommen hat, werden vor jedem Speichern erkannt.
4. **Zugriff nur innerhalb des gewählten Projekts** und zunächst nur auf `*.gd`.
5. **Client kennt nur den Lernserver.** Keine vLLM-URL, keine Modell-IDs, keine Lösungen im Client.
6. **Kindgerecht.** Zielgruppe ca. 9–14 Jahre: einfache Sprache, große Schrift, klare Fehlermeldungen, technische Details nur im Diagnosebereich.

---

## Technische Grundentscheidungen

| Thema | Entscheidung | Begründung |
|---|---|---|
| Python | 3.12+ (lokal vorhanden: 3.13) | aktuelle Typisierung, `Path.is_relative_to` |
| GUI | PyQt6 | Vorgabe |
| Netzwerk | `QNetworkAccessManager` (HTTP) + `QWebSocket` aus `PyQt6.QtWebSockets` | läuft im Qt-Eventloop, keine Thread- oder asyncio-Brücke nötig |
| Datenmodelle | Pydantic v2, gemeinsames Paket `learnharness_protocol` | Client und Server validieren dieselben Strukturen |
| Speichern | `QSaveFile` (atomisch) | kein halb geschriebenes Skript bei Absturz |
| Dateibeobachtung | `QFileSystemWatcher` + Hash-Vergleich beim Speichern | Watcher allein ist unter Windows unzuverlässig |
| Einstellungen | `QSettings` (Benutzer-Ebene) | Serveradresse, Schriftgröße, letztes Projekt |
| App-Daten | `QStandardPaths.AppDataLocation` | Sicherungen und Wiederherstellungsdateien **außerhalb** des Godot-Projekts, damit Godot sie nicht importiert |
| Tests | `pytest`, `pytest-qt` | Widget-Tests ohne manuelle Klicks |
| Qualität | `ruff`, `mypy --strict` für `domain/` und `protocol/` | |
| Verteilung | PyInstaller (Windows, eine Ordner-Distribution) | Kinder-PCs ohne Python-Installation |

---

## Projektstruktur (Vorschlag)

```
LearnHarness/
├─ protocol/                         # gemeinsames Paket – wird auch vom Server importiert
│  ├─ pyproject.toml
│  └─ src/learnharness_protocol/
│     ├─ __init__.py                 # PROTOCOL_VERSION
│     ├─ messages.py                 # StudentMessage, LearningResponse, StreamChunk, ErrorMessage
│     ├─ exercises.py                # Exercise, Blank, Choice, OrderItem, Submission, ReviewResult
│     ├─ progress.py                 # Skill, SkillLevel (0–3), ProgressUpdate
│     └─ health.py                   # HealthStatus
├─ client/
│  ├─ pyproject.toml
│  ├─ src/learnharness_client/
│  │  ├─ __main__.py                 # Einstiegspunkt: python -m learnharness_client
│  │  ├─ app.py                      # QApplication, Logging, Theme, Hauptfenster
│  │  ├─ config.py                   # QSettings-Wrapper, Standardwerte
│  │  ├─ domain/                     # ohne Qt-Widgets, gut testbar
│  │  │  ├─ project.py               # GodotProject: Wurzel prüfen, Skripte auflisten
│  │  │  ├─ path_guard.py            # Pfadprüfung, Symlink-/Junction-Schutz, Dateityp-Whitelist
│  │  │  ├─ script_document.py       # Inhalt, Hash beim Laden, Zeilenenden, Dirty-Status
│  │  │  ├─ file_store.py            # Laden/Speichern mit QSaveFile, Konfliktprüfung
│  │  │  ├─ backup.py                # rotierende Sicherungen
│  │  │  └─ recovery.py              # Autosave-Entwürfe für Absturzwiederherstellung
│  │  ├─ net/
│  │  │  ├─ tutor_client.py          # abstrakte Schnittstelle (Signale + Methoden)
│  │  │  ├─ http_tutor_client.py     # echte Implementierung (HTTP + WebSocket)
│  │  │  ├─ fake_tutor_client.py     # In-Process-Fake für Entwicklung und Tests
│  │  │  └─ connection_monitor.py    # periodischer Health-Check, Statusmodell
│  │  ├─ godot/
│  │  │  ├─ syntax_check.py          # optional: godot --headless --check-only
│  │  │  └─ log_reader.py            # optional: letzte Fehler aus godot.log
│  │  └─ ui/
│  │     ├─ main_window.py
│  │     ├─ theme.py                 # Schriftgrößen, Kontrastmodus
│  │     ├─ project_picker.py
│  │     ├─ script_tree.py
│  │     ├─ editor/
│  │     │  ├─ code_editor.py        # QPlainTextEdit + Zeilennummern + Markierungen
│  │     │  ├─ gdscript_highlighter.py
│  │     │  ├─ find_bar.py
│  │     │  └─ editor_tabs.py
│  │     ├─ panels/
│  │     │  ├─ learn_agent_panel.py
│  │     │  ├─ tutor_panel.py
│  │     │  ├─ problems_panel.py
│  │     │  ├─ progress_panel.py
│  │     │  └─ diagnostics_panel.py
│  │     ├─ exercises/
│  │     │  ├─ base.py               # ExerciseWidget: answers() -> Submission
│  │     │  ├─ factory.py            # Exercise.type -> Widget
│  │     │  ├─ fill_blanks.py
│  │     │  ├─ multiple_choice.py
│  │     │  ├─ ordering.py
│  │     │  ├─ find_bug.py
│  │     │  └─ text_blanks.py
│  │     └─ dialogs/
│  │        ├─ conflict_dialog.py
│  │        └─ recovery_dialog.py
│  └─ tests/
│     ├─ domain/
│     ├─ net/
│     ├─ ui/
│     └─ fixtures/sample_godot_project/   # minimales Projekt mit project.godot + player.gd
└─ TODO_CLAUDE.md
```

---

## Phase 0 – Grundgerüst

- [x] `protocol/` und `client/` als eigenständige Pakete mit `pyproject.toml` anlegen; Client hängt von `learnharness_protocol` ab (lokal per `pip install -e`).
- [x] Abhängigkeiten festlegen und pinnen: `PyQt6`, `pydantic>=2`; Dev: `pytest`, `pytest-qt`, `ruff`, `mypy`, `pyinstaller`.
- [x] `python -m learnharness_client` startet ein leeres Hauptfenster.
- [x] Logging einrichten: rotierende Logdatei in AppData; **keine Code- oder Chatinhalte** im Log, nur Ereignisse, Dateinamen relativ zum Projekt, Fehlertypen.
- [x] Globalen Exception-Hook (`sys.excepthook`) setzen: Fehler loggen, kindgerechten Dialog zeigen, vorher Recovery-Entwürfe schreiben.
- [x] Testfixture `sample_godot_project` anlegen.
- [x] `ruff` und `pytest` laufen lokal ohne Fehler.

**Fertig, wenn:** Fenster startet, Tests laufen grün, Log wird geschrieben.

---

## Phase 0.5 – Einfache Profil-Anmeldung

Die Anmeldung dient der Auswahl des passenden Lernniveaus, nicht als Sicherheits- oder
Passwortsystem. Kinder verwenden einen lokalen Spitznamen statt ihres vollständigen Namens.

- [x] Beim Start einen Anmeldedialog „Wer programmiert heute?“ anzeigen.
- [x] Vorhandenes Profil auswählen oder ein neues Profil mit Spitznamen anlegen.
- [x] Vier Erfahrungsstufen anbieten: erste Schritte, Grundlagen, kleine Projekte und
  selbstständiges Programmieren.
- [x] Profile lokal mit `QSettings` speichern und das zuletzt verwendete Profil vorauswählen.
- [x] Profil-ID, Spitzname und Erfahrungsstufe getrennt von Godot-Projekten verwalten.
- [x] Spitznamen validieren; keine Klarnamen oder Passwörter verlangen.
- [x] Pseudonyme Profil-ID, Spitzname und Erfahrungsstufe beim Start einer
  Lernserver-Sitzung übermitteln.
- [x] Erfahrungsstufe in Tutor-Nachrichten mitsenden, damit der Server Fragen, Sprache und
  Hinweisstufen passend wählen kann.
- [x] Aktives Profil und Erfahrungsstufe in der Statusleiste anzeigen.
- [ ] Lernfortschritt serverseitig dauerhaft der pseudonymen Profil-ID zuordnen. Dies benötigt
  Unterstützung durch den separat entwickelten Lernserver.

**Fertig, wenn:** Mehrere Kinder können am selben Rechner jeweils ihr Profil wählen und der
Lernserver erhält ihre unterschiedliche Erfahrungsstufe, ohne dass ein Passwort oder Klarname nötig
ist.

---

## Phase 1 – Lokaler Editor ohne KI (höchste Priorität)

### 1.1 Projekt auswählen

- [x] `ProjectPicker`: Ordnerdialog, Prüfung auf `project.godot` im gewählten Ordner, klare Meldung falls nicht vorhanden.
- [x] Projektname aus `project.godot` (`config/name`) lesen und in Titelleiste und Statusleiste anzeigen.
- [x] Zuletzt verwendete Projekte (max. 5) in `QSettings` merken; beim Start letztes Projekt öffnen.
- [x] Projektwurzel einmalig mit `Path.resolve()` normalisieren und danach nicht mehr ändern.

### 1.2 Pfadschutz (`path_guard.py`)

- [x] Jeder Dateizugriff läuft über eine zentrale Funktion `ensure_allowed(path) -> Path`.
- [x] Prüfen: `resolve()`-Ergebnis liegt innerhalb der Projektwurzel (`is_relative_to`).
- [x] Symlinks und Windows-Junctions/Reparse-Points ablehnen (`os.lstat` + `st_file_attributes & FILE_ATTRIBUTE_REPARSE_POINT`).
- [x] Whitelist der Dateiendungen, zunächst nur `.gd`.
- [x] Ordner ausschließen: `.godot/`, `.import/`, `.git/`, Ordner mit `.gdignore`; `addons/` standardmäßig ausblenden (konfigurierbar).
- [x] Unit-Tests: `../`-Traversal, absolute Pfade außerhalb, Symlink, Junction, falsche Endung, Groß-/Kleinschreibung unter Windows.

### 1.3 Skriptbaum

- [ ] `ScriptTree` auf Basis von `QFileSystemModel` mit `QSortFilterProxyModel`, das nur erlaubte Dateien und Ordner mit erlaubten Dateien zeigt.
- [x] Doppelklick öffnet Datei im Editor; bereits offene Datei wird nur fokussiert.
- [x] Neue `.gd`-Datei anlegen (Name prüfen, Vorlage `extends Node`); Löschen und Umbenennen zunächst **nicht** anbieten.

### 1.4 Laden und Speichern (`file_store.py`, `script_document.py`)

- [x] Laden: Bytes lesen, als UTF-8 dekodieren (BOM erkennen und beim Speichern beibehalten), Zeilenende (LF/CRLF) erkennen und beibehalten, SHA-256 und `mtime` des geladenen Stands merken.
- [x] Dateigrößenlimit (z. B. 512 KB) – größere Dateien schreibgeschützt öffnen oder ablehnen.
- [x] Speichern:
  1. Aktuellen Datei-Hash auf der Platte mit dem gemerkten Hash vergleichen.
  2. Bei Abweichung → Konfliktdialog (siehe 1.5), **kein** Speichern.
  3. Vorherigen Stand als Sicherung ablegen (siehe 1.6).
  4. Mit `QSaveFile` atomisch schreiben, `commit()` prüfen.
  5. Neuen Hash merken, Dirty-Status zurücksetzen.
- [x] Fehler beim Speichern (gesperrte Datei, keine Rechte, Platte voll) verständlich anzeigen; Inhalt bleibt im Editor und im Recovery-Entwurf.
- [x] Tests: Roundtrip erhält Bytes exakt (BOM, CRLF, Tabs, Umlaute); Speichern bei geänderter Platte schlägt kontrolliert fehl.

### 1.5 Externe Änderungen und Konflikte

- [x] `QFileSystemWatcher` für alle offenen Dateien; nach jedem Signal Pfad neu hinzufügen (atomisches Ersetzen durch Godot entfernt ihn sonst unter Windows aus dem Watcher).
- [x] Signale entprellen (ca. 300 ms), danach Hash vergleichen – nur echte Inhaltsänderungen zählen.
- [x] Datei extern geändert, Editor **nicht** dirty → still neu laden, Cursorposition und Scrollposition möglichst erhalten, kurzer Hinweis in der Statusleiste.
- [x] Datei extern geändert, Editor **dirty** → Konfliktdialog mit drei Optionen: „Meine Version behalten“, „Version aus Godot laden“, „Vergleichen“. Vergleich als einfache Zeilen-Diff-Ansicht (`difflib`), kindgerecht beschriftet.
- [x] Datei extern gelöscht → Hinweis, Inhalt bleibt im Editor, „Erneut speichern“ möglich.
- [x] Beim Wechsel zurück ins Fenster (`QApplication.applicationStateChanged`) alle offenen Dateien prüfen.

### 1.6 Sicherungen und Wiederherstellung

- [x] Vor jedem Speichern alten Stand nach `AppData/backups/<projekt-hash>/<relpfad>/<zeitstempel>.gd` kopieren; je Datei die letzten 20 behalten.
- [x] Autosave-Entwurf aller dirty Dokumente alle 30 s nach `AppData/recovery/`; Entwurf nach erfolgreichem Speichern löschen.
- [x] Beim Start vorhandene Entwürfe erkennen und `RecoveryDialog` anbieten (wiederherstellen / verwerfen / anzeigen).
- [x] Menüpunkt „Ältere Version ansehen“ zeigt Sicherungen einer Datei schreibgeschützt; Übernahme nur durch Kopieren des Kindes oder explizites „Diese Version wiederherstellen“.

### 1.7 Code-Editor

- [x] `CodeEditor(QPlainTextEdit)` mit Zeilennummernbereich (Muster „Code Editor Example“ aus der Qt-Doku).
- [x] Hervorhebung der aktuellen Zeile; Markierungen für Fehlerzeilen (`ExtraSelection` + Symbol im Rand).
- [x] Monospace-Schrift, einstellbare Größe (Strg + Mausrad, Strg +/-), Standard ≥ 14 pt.
- [x] Einrückung mit **Tabs** (GDScript-Standard), Tab-Breite 4; Auto-Einrückung nach Zeilen mit `:`; Umschalt+Tab rückt aus; Blockeinrückung bei Mehrfachauswahl.
- [x] Klammerpaar-Hervorhebung für `()[]{}`.
- [x] Undo/Redo (eingebaut), Speichern mit Strg+S, Dirty-Markierung `•` im Tab-Titel.
- [x] Suchleiste (Strg+F) und Ersetzen (Strg+H), Gehe zu Zeile (Strg+G).
- [x] Einfügen aus der Zwischenablage nur als Klartext (`insertFromMimeData` überschreiben).
- [x] Tabs für mehrere Dateien; Schließen mit Rückfrage bei ungespeicherten Änderungen; beim Beenden alle prüfen.

### 1.8 GDScript-Syntaxhervorhebung

- [x] `QSyntaxHighlighter` mit Regeln für Godot-4-Schlüsselwörter (`func`, `var`, `const`, `if`, `elif`, `else`, `for`, `while`, `match`, `return`, `extends`, `class_name`, `signal`, `enum`, `static`, `await`, `@export`, `@onready` …), eingebaute Typen (`int`, `float`, `Vector2`, `Node2D` …), Zahlen, Strings, `$NodePath`, `%UniqueName`, Kommentare (`#`), Annotationen.
- [x] Mehrzeilige Strings (`"""`) über Blockzustände.
- [x] Farbschema aus `theme.py`, damit Kontrastmodus greift.
- [x] Tests: Beispielzeilen liefern erwartete Formatbereiche.

### 1.9 Hauptfenster-Layout

- [x] `QSplitter`: links Skriptbaum, Mitte Editor-Tabs, rechts Lernbereich (`QTabWidget`:
  LearnAgent · Tutor · Fortschritt), unten einklappbarer Problembereich.
- [x] Den bisherigen Tab „Aufgabe“ entfernen und durch „LearnAgent“ ersetzen.
- [x] Statusleiste: Projektname, Datei, Zeile/Spalte, Verbindungsampel.
- [x] Fenstergeometrie und Splitterpositionen in `QSettings` speichern.

**Fertig, wenn:** Mit dem Beispielprojekt und einem echten Godot-Editor parallel gilt:
- [ ] In PyQt gespeicherte Änderungen erscheinen in Godot, das Spiel läuft mit dem neuen Code.
- [ ] In Godot gespeicherte Änderungen werden im Client erkannt (still neu geladen oder Konfliktdialog).
- [ ] Hartes Beenden des Clients (Task-Manager) verliert höchstens 30 s Arbeit; Wiederherstellung wird angeboten.
- [x] Kein Zugriff außerhalb des Projektordners möglich (Tests grün).

---

## Phase 2 – Anbindung an den Lernserver

Damit die Clientarbeit nicht auf den Server warten muss, wird zuerst gegen `FakeTutorClient` entwickelt.

### 2.1 Gemeinsames Protokollpaket

- [x] Pydantic-Modelle gemäß [Schnittstelle zum Lernserver](#schnittstelle-zum-lernserver) anlegen; `model_config = ConfigDict(extra="forbid")`.
- [x] Feld `protocol_version` in allen Nachrichten; Client lehnt inkompatible Hauptversion mit verständlicher Meldung ab.
- [x] Diskriminierte Unions über `type` (Nachrichten) und `kind` (Übungen).
- [x] JSON-Schema-Export (`model_json_schema()`) als Datei erzeugen, damit der Server-Teil denselben Vertrag sieht.
- [x] Tests: Beispielnachrichten aus den PDFs parsen; Übungen **ohne** Lösungsfeld; unbekannte Felder werden abgelehnt.

### 2.2 Tutor-Client-Schnittstelle

- [x] `TutorClient(QObject)` mit Methoden `check_health()`, `start_session(project_id)`, `send_message(StudentMessage)`, `cancel()`, `request_next_hint(task_id)`, `fetch_task(task_id)`, `submit_exercise(Submission)`, `fetch_progress()`.
- [x] Signale: `health_changed`, `stream_started`, `stream_chunk(str)`, `stream_finished(LearningResponse)`, `exercise_received(Exercise)`, `review_received(ReviewResult)`, `progress_received(ProgressUpdate)`, `error(ClientError)`.
- [x] `FakeTutorClient`: liefert zeitverzögerte, gestreamte Antworten (`QTimer`) inkl. Beispiel-Lückentext aus dem PDF; simuliert auf Wunsch Timeout und Serverausfall.
- [x] Auswahl per Einstellung bzw. Startparameter `--fake-server`.

### 2.3 Echte Implementierung

- [x] `HttpTutorClient` mit `QNetworkAccessManager`; Basis-URL aus `QSettings` (z. B. `http://<tailscale-host>:<port>`), Timeouts pro Anfrage (`setTransferTimeout`).
- [x] Streaming über `QWebSocket`; automatische Wiederverbindung mit Backoff (1 s, 2 s, 5 s, 10 s, max. 30 s).
- [x] Jede eingehende Nachricht mit Pydantic validieren; ungültige Nachrichten verwerfen, Diagnose-Eintrag schreiben, Kind sieht nur „Der Lernhelfer hat gerade Schwierigkeiten“.
- [x] Größenlimits clientseitig: ausgehender Code-Ausschnitt max. N Zeilen bzw. KB (konfigurierbar, mit Server abstimmen); eingehende Nachrichten max. Größe.
- [x] Laufende Anfrage abbrechbar (Schaltfläche „Stopp“ → `cancel()`).
- [x] Keine Zugangsdaten im Client speichern; Identität ergibt sich serverseitig aus Tailscale.

### 2.4 Verbindungsstatus

- [x] `ConnectionMonitor`: Health-Check alle 15 s (bei Fehler häufiger), drei Zustände je Komponente: Lernserver erreichbar · Modell verfügbar · Sitzung aktiv.
- [x] Ampel in der Statusleiste mit kindgerechtem Tooltip („Der Lernhelfer ist da“ / „Der Lernhelfer macht gerade Pause“).
- [x] `DiagnosticsPanel` (über Menü „Hilfe → Technische Details“): URL, letzte Fehler, Latenz, Protokollversion, optional Ausgabe von `tailscale status` falls verfügbar.
- [x] Bei Verbindungsverlust: Tutor- und Übungsbereich deaktivieren, Editor bleibt voll nutzbar, Eingaben im Chatfeld bleiben erhalten.

**Fertig, wenn:** Client arbeitet gegen den Fake vollständig, und gegen den echten Server laufen Health-Check und eine gestreamte Antwort; Server stoppen während einer Antwort führt zu sauberer Meldung ohne Datenverlust.

---

## Phase 3 – LearnAgent und Tutor

### 3.1 LearnAgent mit Level 1–10

- [x] Freies Prompt-Feld anbieten, in dem das Kind ein gewünschtes Spielfeature beschreibt.
- [x] Level 1–10 anzeigen und höhere Level erst nach einer korrekt abgeschlossenen Lernrunde
  freischalten.
- [x] **Level 1:** einfache Verständnisfrage ohne textbasiertes Programmieren; vollständigen Code
  nur nach richtiger Antwort schreiben.
- [x] **Level 2:** einfache Code-Lücken mit Dropdown-Menü.
- [x] **Level 3:** schwierigere Code-Lücken mit mehreren Dropdown-Menüs.
- [x] **Level 4:** Code-Lücken ohne Dropdown-Menü als kurze freie Texteingaben.
- [x] **Level 5 (vorläufig):** fertige Code-Bausteine in die richtige Reihenfolge bringen.
- [x] **Level 6 (vorläufig):** Fehler in einem kurzen Code-Beispiel finden.
- [x] **Level 7 (vorläufig):** wichtige Ausdrücke mit kleinen Hinweisen selbst ergänzen.
- [x] **Level 8 (vorläufig):** Funktionsname und zusammenhängende Codebestandteile ergänzen.
- [x] **Level 9 (vorläufig):** Lösungsweg auswählen und begründen.
- [x] **Level 10 (vorläufig):** eigenes Feature beschreiben und den Plan des Agenten prüfen.
- [x] Bei falscher Antwort keinerlei Dateiänderung zulassen.
- [x] Bei richtiger Antwort vollständige `*.gd`-Datei mit Erklärung übernehmen – nur die Datei der
  aktuellen Lernrunde, andere Pfade werden abgewiesen; vorher Backup,
  Pfadschutz und Konfliktprüfung ausführen.
- [x] Ungespeicherten eigenen Code niemals durch Agenten-Code überschreiben.
- [ ] Die genaue Didaktik der vorläufigen Level 5–10 nach einem Test mit Kindern festlegen.

### 3.2 Tutor-Chat

- [x] Verlauf als `QTextBrowser` (nur lesen), Nachrichten des Kindes und des Tutors klar unterscheidbar, Markdown-Darstellung (`setMarkdown`) mit Bereinigung (keine Links nach außen, keine Bilder, kein HTML).
- [x] Codeschnipsel in Tutor-Antworten als schreibgeschützter Block ohne „Übernehmen“-Funktion.
- [x] Eingabefeld mehrzeilig, Senden mit Strg+Enter; Zeichenlimit mit Anzeige.
- [x] Kontext automatisch mitsenden: aktuelle Aufgabe, Dateiname, **markierter** Code oder Umgebung des Cursors (±N Zeilen), letzte Fehlermeldung aus dem Problembereich. Vor dem Senden sichtbar machen, was mitgeschickt wird („Ich zeige dem Lernhelfer: player.gd, Zeilen 10–24“).
- [x] Schaltfläche „Nächster Hinweis“ (fordert die nächste Hinweisstufe an); aktuelle Stufe sichtbar, z. B. als Punkte ●●○○.
- [x] Gestreamte Antwort wird live angezeigt; Tippen-Indikator; „Stopp“-Schaltfläche.
- [x] Verlauf je Sitzung lokal nur im Speicher; beim Schließen verworfen (Speicherung ist Sache des Servers).

### 3.3 Problembereich und Godot-Fehler

- [x] Liste mit Einträgen (Datei, Zeile, Meldung, Quelle: Server-Prüfung / Godot / manuell); Doppelklick springt zur Stelle.
- [x] Feld „Fehlermeldung aus Godot einfügen“: Kind kopiert Fehler aus dem Godot-Ausgabefenster; Client erkennt `res://pfad.gd:zeile` und verlinkt die Stelle.
- [x] Optional: `godot/syntax_check.py` ruft `godot --headless --path <projekt> --check-only --script <datei>` auf (Godot-Pfad in Einstellungen), parst Ausgabe, Timeout 10 s, läuft per `QProcess` ohne UI-Blockade. Vor Umsetzung mit der festgelegten Godot-Version prüfen.
- [x] Optional: `godot/log_reader.py` liest die letzten Fehler aus dem Godot-Laufzeitlog (`%APPDATA%/Godot/app_userdata/<Projektname>/logs/godot.log`), falls Datei-Logging aktiv ist.

**Fertig, wenn:** Der Lernfall „Spieler nach rechts bewegen“ funktioniert durchgängig: Kind gibt
einen Prompt ein → erhält Erklärung und Level-Frage → falsche Antwort ändert keine Datei → richtige
Antwort gibt den vollständigen, erklärten Code frei → der Client sichert und schreibt ihn atomisch.

---

## Phase 4 – Interaktive Übungen

- [x] `ExerciseWidget` als Basisklasse: `load(exercise)`, `answers() -> Submission`, `show_result(ReviewResult)`, `reset()`; Signal `submitted`.
- [x] `ExerciseFactory` wählt Widget anhand `exercise.kind`; unbekannte Art → freundliche Meldung statt Absturz.
- [x] **Lückentext** (`fill_blanks`): Code schreibgeschützt dargestellt, `{{blank_id}}`-Platzhalter als eingebettete `QComboBox` bzw. `QLineEdit`; Tab springt zur nächsten Lücke.
- [x] **Auswahl** (`multiple_choice`): `QRadioButton`/`QCheckBox`-Gruppe, optional mit Codeausschnitt.
- [x] **Reihenfolge** (`ordering`): `QListWidget` mit Drag & Drop (`InternalMove`) **und** Tastatursteuerung (Alt+↑/↓).
- [x] **Fehler finden** (`find_bug`): schreibgeschützter Code mit Zeilennummern; Kind wählt Zeile(n) aus und kann optional eine Erklärung tippen.
- [x] Nach Abgabe: richtige/falsche Teile farblich **und** mit Symbol markieren (nicht nur Farbe), Erklärung vom Server anzeigen, „Nochmal versuchen“ bzw. „Weiter“.
- [x] Übungen ändern niemals Projektdateien.
- [x] Widget-Tests mit `pytest-qt` für jede Übungsart (Eingabe → erwartete `Submission`).

---

## Phase 5 – Fortschritt, Barrierefreiheit, Verteilung

### 5.1 Fortschrittsanzeige

- [x] Fähigkeiten (Variablen, Bedingungen, Schleifen, Funktionen, Signale, Godot-Knoten …) mit Stufe 0–3 als Symbolreihe, Beschriftung in Worten („mit Hilfe“, „fast allein“, „sicher“).
- [x] Keine Gesamtpunktzahl, keine Ranglisten.
- [x] Daten kommen ausschließlich vom Server (`ProgressUpdate`); Client cached nur für die Anzeige offline.

### 5.2 Barrierefreiheit und Bedienung

- [x] Globale Schriftgröße (klein/mittel/groß) wirkt auf alle Bereiche.
- [x] Kontrastmodus (hell, dunkel, hoher Kontrast) über `theme.py`.
- [ ] Vollständige Tastaturbedienung, sinnvolle Tab-Reihenfolge, sichtbarer Fokus, `setAccessibleName` für alle Bedienelemente.
- [x] Alle UI-Texte zentral (Vorbereitung für `QTranslator`); Sprache zunächst Deutsch, einfache Sätze.
- [x] Kurzanleitung beim ersten Start (3–4 Schritte, überspringbar).

### 5.3 Verteilung

- [x] PyInstaller-Spec für Windows (Ordner-Build), Icon, Versionsinfo.
- [x] Erststart-Dialog: Serveradresse eintragen und testen.
- [ ] Prüfen, dass der Build auf einem PC ohne Python startet und Projekte öffnen/speichern kann.
- [x] Kurze Installationsanleitung `client/README.md`.

---

## Schnittstelle zum Lernserver

**Vorschlag aus Client-Sicht – mit dem Server-Teil abstimmen.** Alle Pfade unter `/api/v1`.

| Zweck | Methode / Pfad | Anfrage | Antwort |
|---|---|---|---|
| Gesundheit | `GET /health` | – | `HealthStatus { server_ok, model_ok, protocol_version }` |
| Sitzung starten | `POST /sessions` | `{ project_id, client_version, student_profile_id, student_pseudonym, experience_level }` | `{ session_id, student_pseudonym, current_task_id? }` |
| Aufgabe holen | `GET /tasks/{task_id}` | – | `Task { id, title, skill, instructions, files[] }` |
| Tutor-Stream | `WS /sessions/{session_id}/stream` | `StudentMessage` | `StreamChunk*` dann `LearningResponse` |
| Nächster Hinweis | `POST /sessions/{session_id}/hints` | `{ task_id }` | `LearningResponse` |
| Übung abgeben | `POST /exercises/{exercise_id}/submissions` | `Submission` | `ReviewResult` |
| Code abgeben | `POST /tasks/{task_id}/submissions` | `CodeSubmission { file, content }` | `ReviewResult` |
| Fortschritt | `GET /progress` | – | `ProgressUpdate` |

Wichtige Felder (aus den PDFs übernommen, erweitert):

- `StudentMessage`: `type`, `protocol_version`, `session_id`, `project_id`, `experience_level` (0–3), `learning_level` (1–10), `language="gdscript"`, `current_task`, `file`, `code_excerpt`, `excerpt_start_line`, `last_error`, `message`.
- `LearningResponse`: `type`, `mode` (`socratic` | `hint` | `exercise` | `explanation` | `review`), `message`, `hint_level`, `hints[]`, `exercise?`, `code_changes` (für den normalen Tutor weiterhin ignoriert).
- `Exercise`: `id`, `kind`, `skill`, `difficulty`, `prompt`, artspezifische Felder (`code`, `blanks[]`, `choices[]`, `items[]`, `lines[]`) – **niemals** Lösungen.
- `ReviewResult`: `correct?`, `per_item[]` (richtig/falsch je Lücke/Antwort), `feedback`, `follow_up_question?`, `marked_lines[]`, `generated_files[]`. `generated_files` ist nur bei `correct=true` schema-valide und enthält Pfad, vollständigen Dateiinhalt und Erklärung.
- `ErrorMessage`: `code` (maschinenlesbar), `message_for_child`, `retry_after?`.

---

## Was der Client von deinem Teil braucht

Diese Punkte erstellst du; der Client ist so gebaut, dass er bis dahin mit dem Fake läuft.

- [ ] Lernserver mit den Endpunkten oben (oder angepasster Vertrag → dann `protocol/` anpassen).
- [ ] Tailscale-Hostname/IP und Port des Lernservers.
- [ ] Health-Endpunkt, der vLLM-Verfügbarkeit mit meldet.
- [ ] Festgelegte Godot-Version (für Highlighter-Schlüsselwörter und `--check-only`).
- [ ] Erste Aufgabe „Spieler nach rechts bewegen“ inkl. Prüfregel auf dem Server.
- [ ] Festgelegte Größenlimits für Code-Ausschnitte und Nachrichten.
- [ ] Serverseitige Zuordnung von Profil-ID, Erfahrungsstufe und Lernfortschritt; der Client
  übermittelt Profil-ID, Spitzname und Erfahrungsstufe beim Sitzungsstart.

---

## Offene Entscheidungen

- [ ] Soll das Kind Tutor-Text überhaupt markieren/kopieren dürfen? (Vorschlag: ja, Kopieren aus Erklärtexten erlaubt, aber kein Übernehmen-Knopf und keine fertigen Lösungen vom Server.)
- [ ] Sollen neue `.gd`-Dateien im Client angelegt werden oder nur in Godot (wegen Verknüpfung mit Szenen)? (Vorschlag: Anlegen erlauben, Anhängen an Knoten bleibt in Godot.)
- [ ] Dürfen mehrere Projekte gleichzeitig offen sein? (Vorschlag: nein, ein Projekt pro Fenster.)
- [ ] Pflicht-Speichern vor „Prüfen“ oder Abgabe des ungespeicherten Editorinhalts? (Vorschlag: Speichern erzwingen, damit Godot und Prüfung denselben Stand sehen.)
- [ ] Wie viel Kontext wird automatisch mitgeschickt – nur Auswahl oder ganze Datei?

---

## Definition of Done für den ersten Meilenstein (Client)

- [ ] GDScript wird in der PyQt-Anwendung bearbeitet und atomisch im Godot-Projekt gespeichert; Godot übernimmt die Änderungen.
- [ ] Parallele Änderungen in Godot werden erkannt, nichts wird unbemerkt überschrieben.
- [x] Kein Dateizugriff außerhalb des Projekts, nur `*.gd`.
- [ ] Verbindung zum Lernserver über die konfigurierte Tailscale-Adresse; Status sichtbar.
- [ ] Tutor-Antworten werden gestreamt angezeigt; Hinweise stufenweise abrufbar.
- [ ] Mindestens Lückentext und Auswahlübung funktionieren mit serverseitiger Prüfung.
- [x] Der LearnAgent kann vollständigen Code ausschließlich nach einer korrekt beantworteten
  Level-Prüfung schreiben; falsche Antworten und normale Tutor-Nachrichten ändern keine Dateien.
- [ ] Server-/Netz-/Modellausfall führt zu keinem Codeverlust; Absturz-Wiederherstellung funktioniert.
- [x] Lokale Profil-Anmeldung erlaubt unterschiedliche Erfahrungsstufen für mehrere Kinder.
- [x] Alle Tests (`pytest`) grün, `ruff` ohne Befund.
