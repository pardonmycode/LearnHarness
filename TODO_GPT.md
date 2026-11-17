# TODO: Godot-Lernumgebung mit PyQt, Tailscale und vLLM

## Zielbild und verbindliche Entscheidungen

Kinder entwickeln ihr Spiel weiterhin direkt im Godot-Editor. Dort bauen sie Maps und Szenen, platzieren oder verschieben grafische Objekte und testen das Spiel.

Der Programmierteil findet dagegen in einer separaten, in Python geschriebenen PyQt-Anwendung statt. Diese Anwendung öffnet und speichert die Skriptdateien des ausgewählten Godot-Projekts und kommuniziert über Tailscale mit dem Haupt-PC.

Der Haupt-PC stellt die KI-Modelle mit vLLM bereit.

Die KI arbeitet als LearnAgent und Programmierlehrer. Da die Kinder am Anfang noch nicht
textbasiert programmieren können, darf sie vollständigen Code erzeugen und in das Projekt schreiben
– jedoch erst nach einer Erklärung und einer korrekt gelösten, zum Lernlevel passenden Frage. Bei
einer falschen Antwort wird kein Code geschrieben. Normale Tutor-Antworten dürfen weiterhin keine
ungeprüften Dateiänderungen auslösen.

## Zielarchitektur

### Rechner des Kindes

- [x] Eine einfache lokale Profil-Anmeldung mit pseudonymem Spitznamen und Erfahrungsstufe
  bereitstellen, damit mehrere Kinder passende Aufgaben und Hinweise erhalten.
- [ ] Godot dient ausschließlich der visuellen Spielentwicklung, der Szenen- und Map-Bearbeitung, der Platzierung grafischer Objekte und dem Starten des Spiels.
- [ ] Eine eigenständige PyQt6-Anwendung übernimmt Code-Editor, Aufgaben, Tutor-Chat, Hinweise, Übungen, Fehlermeldungen und Lernfortschritt.
- [ ] Die PyQt-Anwendung kann ein vorhandenes Godot-Projekt auswählen und dessen freigegebene Skriptdateien, zunächst `*.gd`, öffnen und speichern.
- [ ] Die PyQt-Anwendung erkennt Änderungen, die währenddessen im Godot-Editor vorgenommen wurden, und verhindert unbemerktes Überschreiben.
- [ ] Godot übernimmt lokal gespeicherte Skriptänderungen wie gewohnt in das Projekt.
- [ ] Die Kommunikation mit dem Lernserver erfolgt ausschließlich über das Tailscale-Netz.

### Haupt-PC / Lernserver

- [ ] Ein Python-Lernserver stellt die API für Sitzungen, Aufgaben, Hinweise, Codeprüfung und Lernfortschritt bereit.
- [ ] Der Lernserver verwendet den OpenAI-kompatiblen API-Endpunkt des vorhandenen vLLM-Servers.
- [ ] Basis-URL, Modellname, Timeouts und maximale Kontextgröße werden konfigurierbar gehalten und nicht im Client fest einprogrammiert.
- [ ] Der PyQt-Client spricht nur mit dem Lernserver. Der vLLM-Endpunkt wird nicht direkt für die Kinder-Clients freigegeben.
- [ ] Der Learning Orchestrator entscheidet, welcher pädagogische Agent verwendet wird, validiert dessen strukturierte Antwort und setzt die Lernregeln unabhängig vom Modell durch.
- [ ] Lösungen, Prüfregeln und sensible Konfiguration bleiben ausschließlich auf dem Server.

### Kommunikation

- [ ] HTTP für Anmeldung, Konfiguration, Projekt- und Sitzungsstatus sowie Aufgabenabruf verwenden.
- [ ] WebSocket oder HTTP-Streaming für laufende Tutor-Antworten verwenden.
- [ ] Alle Nachrichten als versionierte JSON-Strukturen mit Pydantic validieren.
- [ ] Mindestens `session_id`, pseudonyme Schüler-ID, Projekt-ID, aktuelle Aufgabe, relevante Codeauszüge, Godot-Fehler und Lernstand unterstützen.
- [ ] Tailscale-Identität serverseitig prüfen; den Dienst nicht ungeschützt ins öffentliche Internet stellen.
- [ ] Verbindungsabbrüche, Serverausfall und Modell-Timeouts in der PyQt-Oberfläche kindgerecht behandeln, ohne ungespeicherten Code zu verlieren.

## Pädagogische Regeln

- [x] LearnAgent-Level 1–10 mit freiem Prompt-Feld und schrittweiser Freischaltung bereitstellen.
- [x] Level 1 verwendet einfache Verständnisfragen; Level 2 einfache Dropdown-Lücken; Level 3
  schwierigere Dropdown-Lücken; Level 4 freie Textlücken ohne Dropdown.
- [ ] Level 5–10 nach Erprobung der vorläufigen Progression didaktisch finalisieren.
- [ ] Der Teacher stellt nur eine kurze Frage auf einmal und verwendet altersgerechte Sprache.
- [ ] Hilfe wird stufenweise gegeben: Verständnisfrage, kleiner Hinweis, konkreterer Hinweis, Mini-Übung und erst danach eine Erklärung des zugrunde liegenden Konzepts.
- [ ] Wenn ein Kind nach der kompletten Lösung fragt, bietet die KI stattdessen eine Erklärung, einen kleinen Hinweis oder eine einfachere Teilaufgabe an.
- [ ] Der Exercise Creator erzeugt Lückentexte, Auswahlaufgaben, Sortieraufgaben, Fehlersuche und kleine Programmieraufgaben mit eindeutigem Lernziel.
- [ ] Der Reviewer erklärt Auffälligkeiten im selbst geschriebenen Code und stellt eine weiterführende Frage, ohne den vollständig korrigierten Code auszugeben.
- [x] Vollständigen LearnAgent-Code nur in einer `ReviewResult`-Antwort mit `correct=true`
  akzeptieren; Erklärung, Backup, Pfadschutz und Konfliktprüfung sind Pflicht.
- [ ] Richtige Übungslösungen werden vor der Abgabe nie an den Client oder das Modell-Frontend gesendet.
- [ ] Eindeutige Aufgaben wie Multiple Choice oder Lückentext werden deterministisch auf dem Server geprüft.
- [ ] Freier Code wird soweit möglich mit Parser, statischer Analyse und aufgabenspezifischen Tests geprüft; das Modell ergänzt nur pädagogisches Feedback.
- [ ] Fortschritt wird je Fähigkeit gespeichert, zum Beispiel Variablen, Bedingungen, Schleifen, Funktionen, Signale und Godot-Knoten.

## Sicherer Umgang mit dem Godot-Projekt

- [ ] Das Kind wählt den Projektordner ausdrücklich aus; die PyQt-Anwendung prüft das Vorhandensein von `project.godot`.
- [ ] Dateioperationen auf den gewählten Projektordner begrenzen und Pfad-Traversal sowie symbolische Auswege verhindern.
- [ ] Zunächst nur freigegebene Dateitypen bearbeiten, insbesondere `*.gd`; Projektdateien und Assets nur nach späterer ausdrücklicher Freigabe ändern.
- [ ] Die KI erhält standardmäßig nur lesenden Zugriff auf die für die aktuelle Lernrunde nötigen Dateien und Ausschnitte.
- [x] Nur korrekt abgeschlossene LearnAgent-Runden dürfen vollständige Skriptdateien verändern;
  normale Tutor-Antworten bleiben vom Editor getrennt.
- [ ] Vor jedem Speichern externe Dateiänderungen erkennen; bei Konflikten Vergleich und Auswahl anbieten.
- [ ] Lokale Wiederherstellung durch atomisches Speichern, Undo/Redo und begrenzte Sicherungskopien ermöglichen.
- [ ] Tests oder Schüler-Code niemals mit den Rechten des Lernservers ausführen; dafür eine isolierte, ressourcenbegrenzte Umgebung vorsehen.

## PyQt6-Oberfläche

- [ ] Projekt-Auswahl mit Anzeige des aktuell verbundenen Godot-Projekts bauen.
- [ ] Eingeschränkten Projekt- und Skriptbaum bauen.
- [ ] GDScript-Editor mit Syntaxhervorhebung, Zeilennummern, Undo/Redo, Suche und sicherem Speichern bauen.
- [x] Den Aufgaben-Tab durch einen LearnAgent-Tab mit Prompt, Level 1–10, Erklärung und integrierter
  Übung ersetzen.
- [ ] Tutor-Bereich mit einzelnen Fragen und einer klaren Schaltfläche für den nächsten Hinweis bauen.
- [ ] Interaktive Widgets für Auswahlfragen, Lückentexte, Reihenfolgen und Fehlersuche bauen.
- [ ] Godot-Fehler und Prüfergebnisse verständlich anzeigen und zur betroffenen Stelle navigieren.
- [ ] Lernfortschritt je Fähigkeit anzeigen, ohne Druck durch eine einzige Gesamtpunktzahl zu erzeugen.
- [ ] Status für Tailscale-Verbindung, Lernserver und vLLM-Verfügbarkeit anzeigen, technische Details aber nur in einem Diagnosebereich ausgeben.
- [ ] Schriftgröße, Tastaturnavigation, Kontrast und einfache Sprache für Kinder im Alter von ungefähr 9 bis 14 Jahren berücksichtigen.

## Server-Komponenten

- [ ] API-Dienst, zum Beispiel mit FastAPI, für HTTP und WebSocket/Streaming anlegen.
- [ ] Pydantic-Modelle für `StudentMessage`, `LearningResponse`, `Exercise`, `Submission`, `ReviewResult` und `ProgressUpdate` definieren.
- [ ] vLLM-Client mit Streaming, Abbruch, Wiederholungsstrategie und klaren Timeouts implementieren.
- [ ] Strukturierte Modellausgaben strikt validieren; ungültige oder pädagogisch unzulässige Antworten verwerfen oder sicher neu anfordern.
- [ ] Teacher, Exercise Creator und Reviewer als getrennte Rollen mit minimalen Rechten implementieren.
- [ ] Serverseitige Hinweisstufen und Aufgabenlösungen getrennt vom Gesprächskontext speichern.
- [ ] Deterministische Übungsprüfung und aufgabenspezifische Codeprüfungen implementieren.
- [ ] Pseudonyme Nutzer, Projekte, Aufgaben, Abgaben und Lernfortschritt mit möglichst wenigen Daten speichern.
- [ ] Aufbewahrungs- und Löschregeln für Chat- und Codedaten festlegen.
- [ ] Rate-Limits, Größenlimits und Protokollierung ohne sensible Code- oder Gesprächsinhalte einbauen.

## Umsetzungsphasen

### Phase 1 – Lokaler Editor ohne KI

- [ ] PyQt6-Grundgerüst erstellen.
- [ ] Godot-Projekt auswählen, GDScript-Dateien öffnen, bearbeiten und sicher speichern.
- [ ] Gleichzeitige Änderungen durch Godot erkennen und Konflikte behandeln.
- [ ] Mit einem kleinen Beispielprojekt prüfen, dass Godot die gespeicherten Änderungen zuverlässig lädt.

### Phase 2 – Lernserver und vLLM über Tailscale

- [ ] Python-Lernserver auf dem Haupt-PC starten und nur im Tailscale-Netz erreichbar machen.
- [ ] Verbindung vom Lernserver zum vorhandenen vLLM-Endpunkt konfigurieren und testen.
- [ ] Gesundheitsstatus für Client, Lernserver und Modell bereitstellen.
- [ ] PyQt-Client mit dem Lernserver verbinden und Streaming-Antworten anzeigen.

### Phase 3 – Teacher-MVP

- [ ] Aktuelle Aufgabe, ausgewählten Code und optionale Godot-Fehlermeldung an den Server senden.
- [ ] Teacher-Antworten auf Fragen und abgestufte Hinweise begrenzen.
- [x] Ungeschützte `code_changes` weiterhin ignorieren; vollständigen Code nur als validierte
  `generated_files` nach `correct=true` übernehmen.
- [x] Einen durchgängigen Lernfall umsetzen: Das Kind möchte den Spieler nach rechts bewegen,
  beantwortet zuerst eine Level-Frage und erhält nur bei richtiger Antwort vollständigen, erklärten
  Agenten-Code.

### Phase 4 – Interaktive Übungen und Prüfung

- [ ] Lückentext, Multiple Choice, Sortierung und Fehlersuche in PyQt darstellen.
- [ ] Lösungen ausschließlich serverseitig speichern und Abgaben deterministisch prüfen.
- [ ] Syntaxprüfung und erste kleine aufgabenspezifische Tests für GDScript ergänzen.
- [ ] Abgestuftes Feedback und Fortschritt je Fähigkeit speichern.

### Phase 5 – Absicherung und Pilotbetrieb

- [ ] Projektzugriffe, Nachrichtengrößen, Modellantworten und Testausführung sicherheitstechnisch prüfen.
- [ ] Datenschutz, Einwilligung, Betreuung und Löschfristen für den Einsatz mit Minderjährigen klären.
- [ ] Verständlichkeit und Bedienung mit wenigen betreuten Testaufgaben prüfen.
- [ ] Erst nach erfolgreichem Pilotbetrieb weitere Dateitypen, komplexere Übungen oder zusätzliche Modelle freigeben.

## Abnahmekriterien für den ersten Meilenstein

- [ ] Auf dem Kinder-Rechner werden Maps, Szenen und grafische Objekte in Godot bearbeitet.
- [ ] GDScript wird in der PyQt-Anwendung bearbeitet und sicher im selben Godot-Projekt gespeichert.
- [ ] Die PyQt-Anwendung erreicht den Lernserver auf dem Haupt-PC über Tailscale.
- [ ] Der Lernserver nutzt vLLM; für Installation und Betrieb ist kein Ollama erforderlich.
- [x] Bei einer Programmierfrage erklärt die KI zuerst das Konzept und stellt eine Level-Frage;
  fertiger Code wird erst nach richtiger Antwort geschrieben.
- [ ] Nach Bedarf folgen abgestufte Hinweise und eine interaktive Übung.
- [x] Der Server prüft die Lernantwort; nur bei `correct=true` schreibt der Client den vollständigen
  Agenten-Code mit Erklärung, Backup und atomischem Speichern.
- [x] Die KI kann Dateien nur über den eng begrenzten `generated_files`-Pfad einer korrekt
  abgeschlossenen LearnAgent-Runde verändern und niemals Shell-Befehle ausführen.
- [ ] Verbindungs- oder Modellfehler verursachen keinen Verlust des lokal geschriebenen Codes.

## Noch zu konfigurieren

- [ ] Tailscale-Hostname oder Tailscale-IP des Haupt-PCs festlegen.
- [ ] Port und URL des Python-Lernservers festlegen.
- [ ] Interne vLLM-Basis-URL und Modell-ID festlegen.
- [ ] Unterstützte Godot-Version und zunächst unterstützte GDScript-Version festlegen.
- [ ] Speicherort und Sicherungsstrategie für Lernfortschritt festlegen.
- [ ] Festlegen, ob mehrere Kinder gleichzeitig arbeiten und wie ihre Sitzungen getrennt werden.

## Abgrenzung zu den bisherigen PDF-Dokumenten

Die PDFs dienen als fachlicher Hintergrund für Agentenrollen, Übungen, Validierung, Datenschutz und eine schrittweise Roadmap. Folgende ältere Annahmen werden ausdrücklich ersetzt:

- Ollama wird vollständig durch den bereits vorhandenen vLLM-Dienst auf dem Haupt-PC ersetzt.
- Godot enthält nicht mehr den Code-Editor, Tutor-Chat oder die Übungsoberfläche; diese Funktionen liegen in der PyQt-Anwendung.
- Die Verbindung ist nicht nur lokal auf einem Rechner, sondern läuft vom Kinder-Rechner über Tailscale zum Haupt-PC.
- Die frühere ungeprüfte Mentor-Patch-Funktion bleibt deaktiviert. Stattdessen verwendet der
  LearnAgent eine didaktisch gesperrte Freigabe: vollständiger Code erst nach richtiger Antwort,
  anschließend mit Erklärung, Backup und sicherem Speichern.
