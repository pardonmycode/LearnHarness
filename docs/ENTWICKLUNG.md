# Entwicklung

[← Zur Übersicht](README.md) · [Alle Testdateien](DATEIEN_TESTS.md)

Die Einrichtung und alle Betriebsbefehle stehen im [Haupt-README](../README.md#befehle).

## Prüfen

Vom Hauptordner aus:

```bash
ruff check client protocol server
ruff format --check client protocol server
python -m pytest                 # Client und Protokoll
(cd client && mypy)              # strenge Typprüfung
(cd server && python -m pytest)  # Server
(cd server && python manage.py makemigrations --check --dry-run)
```

## Regeln für den Code

- Eine Python-Datei hat höchstens **250 Zeilen**, besser unter 200.
- Wird eine Datei zu groß, entsteht ein Paket. Das `__init__.py` behält die öffentlichen Namen,
  damit bestehende Importe weiter funktionieren.
- Jede Datei beginnt mit einem Kommentar in einem Satz. Daraus entstehen die Dateilisten.
- Sichtbare Texte stehen nur in `client/src/learnharness_client/texts/`.
- Dateizugriffe auf Projekte laufen immer über den `PathGuard`.
- Nach dem Anlegen oder Verschieben von Dateien gehören die `DATEIEN_*.md` aktualisiert.

## Tests finden

| Bereich | Ordner |
|---|---|
| Projekte, Pfade, Speichern | [`client/tests/domain/`](../client/tests/domain/) |
| Netzwerk und Übungsserver | [`client/tests/net/`](../client/tests/net/) |
| Fenster, Tabs, Editor, Übungen | [`client/tests/ui/`](../client/tests/ui/) |
| Protokoll | [`protocol/tests/`](../protocol/tests/) |
| Server | [`server/tests/`](../server/tests/) |

Gemeinsame Test-Hilfen stehen in `conftest.py` und den `*_helpers.py`-Dateien.

## Bekannter Testfehler

`test_known_projects_are_parsed_filtered_and_deduplicated` schlägt unter macOS fehl. Der Test
erwartet, dass Pfade mit anderer Groß- und Kleinschreibung als gleich erkannt werden, und das
trifft in dieser Form nur unter Windows zu.
