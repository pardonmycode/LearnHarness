# Architektur

[← Zur Übersicht](README.md)

## Die drei Teile

| Teil | Ordner | Aufgabe |
|---|---|---|
| Client | [`client/`](../client/) | PyQt6-App auf dem Rechner des Kindes |
| Protokoll | [`protocol/`](../protocol/) | Gemeinsame Datenmodelle von App und Server |
| Server | [`server/`](../server/) | Django: Lernserver, KI-Anbindung und Verwaltung |

```text
Kind → Client ──HTTP / WebSocket──→ Server → Harness → KI-Anbieter
          │                            │
    Projektdateien                 PostgreSQL
```

## Feste Regeln

1. **Code erst nach Lernerfolg.** Generierter Code wird erst nach einer vom Server als richtig
   geprüften Antwort freigegeben.
2. **Kein Codeverlust.** Der Editor funktioniert ohne Server. Vor jedem Speichern entsteht eine
   Sicherung, ungespeicherte Arbeit landet in Wiederherstellungsentwürfen.
3. **Nur im Projekt.** Jeder Dateizugriff läuft über den `PathGuard`.
4. **Code läuft nur auf Befehl.** Die Syntaxprüfung liest den Code nur. Ausgeführt wird er, wenn
   das Kind im Terminal `python datei.py` tippt. Das Terminal kennt nur wenige Lernbefehle und
   erreicht keine System-Shell. Die gestarteten Skripte laufen aber ohne Sandbox.
5. **Lösungen bleiben auf dem Server.** Der Client bekommt Übungen ohne richtige Antworten.
6. **Kindgerecht.** Alle sichtbaren Texte stehen zentral in `texts/`.

## Weg einer Lernrunde

1. Das Kind startet im Tab **LearnAgent** eine Runde
   ([`rounds.py`](../client/src/learnharness_client/ui/panels/learn_agent_panel/rounds.py)).
2. Das Hauptfenster baut eine `StudentMessage`
   ([`learning.py`](../client/src/learnharness_client/ui/main_window/learning.py)).
3. Der Tutor-Client sendet sie über den WebSocket
   ([`http_tutor_client`](../client/src/learnharness_client/net/http_tutor_client/__init__.py)).
4. Der Server verteilt sie nach `intent`
   ([`engine`](../server/tutor/engine/__init__.py)).
5. Die KI antwortet im festen JSON-Format, die [Harness](../server/tutor/harness/__init__.py)
   prüft das Ergebnis und hält Antworten und Code zurück.
6. Das Kind beantwortet die Übung. Nur bei einer richtigen Antwort liefert der Server den Code
   ([`reviews.py`](../server/tutor/engine/reviews.py)).
7. Der Client schreibt nur in die Zieldatei der Runde, mit Pfadschutz, Konfliktprüfung und
   Sicherung ([`files.py`](../client/src/learnharness_client/ui/editor/editor_tabs/files.py)).

## Aufbau großer Klassen

Große Klassen sind auf Dateien verteilt. Das `__init__.py` eines Pakets enthält die Hauptklasse
und bietet weiter denselben Import an:

```python
from learnharness_client.ui.main_window import MainWindow
```

Die Teildateien enthalten Mixins, also Klassen mit einem abgegrenzten Teil der Methoden:

```python
class MainWindow(WindowActions, ProjectActions, LearningActions, QMainWindow):
    ...
```

In Paketen, die `mypy --strict` prüft (`config`, `net`), erben die Teile von einer gemeinsamen
Basisklasse. Qt-Ereignisse wie `closeEvent` und `keyPressEvent` bleiben in der Hauptklasse.
