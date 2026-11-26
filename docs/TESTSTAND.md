# Teststand: Prompts mit Claude oder vLLM ausprobieren

Der Teststand startet einen lokalen Lernserver mit eigener Datenbank und die App dazu. Du
trägst nur einen Claude-Schlüssel oder deine vLLM-Adresse ein und siehst jeden KI-Aufruf mit
Prompt und Antwort. Für einen Schulserver ist er nicht gedacht.

## Einmal einrichten

In einer virtuellen Umgebung im Repository:

```bash
python -m pip install -e ./protocol -e "./client[dev]" -e "./server[dev]"
```

## Starten

```bash
python -m learnharness_client.teststand
```

1. Anbieter wählen: **Claude** (API-Schlüssel, Modell, Denkaufwand) oder **vLLM** (Adresse, Modell).
   Bei vLLM darf das Modell leer bleiben: Der Teststand nimmt immer das erste Modell, das der
   vLLM-Server meldet, und trägt es nach „Verbindung testen“ ins Feld ein.
2. **Verbindung testen** prüft, ob die KI antwortet.
3. **Starten** richtet den Lernserver ein und öffnet die App. Beim ersten Mal legst du dort ein
   Profil an und öffnest ein Projekt.
4. Rechts erscheint jeder KI-Aufruf: System-Prompt, Nachrichten, Antwort der KI, was beim Kind
   ankommt und was der Harness verworfen oder geändert hat.

Die Knöpfe links öffnen das KI-Protokoll im Admin, die Prompt-Übersicht und die Kinderliste.
Dort setzt du zum Beispiel die Stufe eines Themas, um Mission-Stufe 2 oder 3 zu testen.
Die Admin-Anmeldung steht im Fenster.

## Wo die Daten liegen

Alles liegt in `~/.learnharness-teststand/`, getrennt von deinen echten Profilen:

| Datei | Inhalt |
|---|---|
| `teststand.json` | Anbieter und Modell; Schlüssel nur, wenn „merken“ angehakt ist (nur für dich lesbar) |
| `server.sqlite3` | Datenbank des lokalen Lernservers mit dem KI-Protokoll |
| `server.log` | Ausgabe des Lernservers, hilfreich bei Fehlern |
| `client/` | Profile und Einstellungen der App im Teststand |

**Testdaten löschen** entfernt Datenbank und Profile. Deine Projekte bleiben erhalten.

Der Schlüssel geht nur an den lokalen Serverprozess, nie in die Datenbank, auf die
Befehlszeile oder an die App. Der Server ist nur auf diesem Rechner erreichbar (127.0.0.1).
