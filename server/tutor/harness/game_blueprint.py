"""Skeleton and architecture the AI follows when a child's project is a game."""

from __future__ import annotations

import re

# Only these requests plan or change the project; explaining code needs no architecture.
BLUEPRINT_INTENTS = frozenset({"chat", "learn", "mission", "mission_step", "project_plan"})

_WORD = re.compile(r"[a-zäöüß]+(?:-[a-zäöüß]+)*")
_GAME_WORDS = frozenset(
    {"arcade", "game", "games", "platformer", "pong", "rpg", "shooter", "snake", "tetris"}
)
_GAME_PHRASES = ("jump and run", "jump-and-run", "jump 'n' run", "jump'n'run", "jump n run")
_GAME_PREFIXES = ("spielfeld", "spielfigur", "spielstand", "spielwelt")
# "Beispiel" and "abspielen" contain "spiel" but say nothing about a game.
_NOT_GAME_PREFIXES = ("beispiel", "abspiel", "vorspiel", "zusammenspiel")

_SHARED = """Dieses Projekt ist ein Spiel. Nutze dafür das Grundgerüst unten als deinen eigenen
Bauplan. Es ändert keine der festen Regeln:
- Zeige das Grundgerüst nie als Ganzes und liefere daraus keine fertigen Dateien.
- Passe es an die Idee des Kindes an und lass weg, was dieses Spiel nicht braucht.
- Baue von innen nach außen: erst etwas Spielbares, dann Regeln, dann Verschönerung.
- Nach jedem Schritt muss sich das Spiel starten und ausprobieren lassen.
- Benenne Bausteine in Kinderworten. Fachbegriffe nur, wenn das Level dazu passt.
- Geschriebener Code geht nur in die aktuelle Datei. Fehlt ein Baustein in einer anderen Datei,
  nenne den genauen Pfad aus der Ordnerstruktur und schlage ihn als nächsten Schritt vor.
- To-dos für neue Dateien nennen den Pfad, z. B. „Spielfigur in entities/player/ anlegen“.
- Passt der vorhandene Code nicht zum Bauplan, baue darauf auf, statt alles umzustellen."""

_GODOT = """Grundgerüst für Godot 4:
res://
  main/                     main.tscn + main.gd: setzt Spieler, Level und Anzeige zusammen
  autoload/                 game_state.gd: Punkte, Leben, aktuelles Level
  entities/
    player/                 player.tscn + player.gd (nur Steuerung und Bewegung)
    enemies/slime/          slime.tscn + slime.gd, je Gegner ein eigener Ordner
    items/coin/             coin.tscn + coin.gd, je Gegenstand ein eigener Ordner
  components/               wiederverwendbare Teile, z. B. health_component.tscn + .gd
  levels/                   level_01.tscn, level_02.tscn
  ui/
    hud/                    hud.tscn + hud.gd (Punkte und Leben)
    menus/                  main_menu.tscn, game_over.tscn
  resources/                eigene .tres-Daten, z. B. Gegnerwerte
  assets/
    sprites/  audio/  fonts/  Bilder, Töne und Schriften ohne Code

Ordnerregeln:
- Szene, Skript und nur dort genutzte Bilder liegen zusammen im Ordner ihres Bausteins.
- Was mehrere Bausteine nutzen, kommt nach components/ oder assets/.
- Datei- und Ordnernamen klein_mit_unterstrich, Skript heißt wie seine Szene.
- Ordner erst anlegen, wenn der erste Baustein dafür entsteht.
- Vorhandene Dateien nur im Godot-Dateisystem verschieben, damit Verweise heil bleiben.
- addons/ und .godot/ bleiben unberührt.

Architektur:
- Eine Szene, eine Aufgabe. Jede Szene lässt sich allein mit F6 testen.
- „Call down, signal up“: Eltern rufen Kinder direkt auf, Kinder melden sich per Signal.
- Bewegung in _physics_process mit move_and_slide, Anzeige und Effekte in _process.
- Tasten über die Eingabe-Aktionen (Input Map), nie fest im Code.
- Einstellbare Werte als @export statt Zahlen im Code.
- Nur Daten, die das ganze Spiel braucht, gehören in game_state.gd.
- Die Anzeige liest nichts aus dem Spieler, sondern reagiert auf Signale.
- Gruppen wie „enemies“ und Kollisionsebenen statt Abfragen nach Namen.
- Szenen, Knoten und Eingabe-Aktionen legt das Kind in Godot an. Sag ihm genau, was dort zu tun
  ist, denn die App bearbeitet nur Skripte.

Reihenfolge: Hauptszene → Figur bewegen → Welt und Kollision → Ziel oder Gegner → Punkte und
Anzeige → Gewinnen und Verlieren → Töne und Feinschliff."""

_PYTHON = """Grundgerüst für ein Python-Spiel:
main.py                 startet nur das Spiel
game/
  __init__.py
  settings.py           feste Werte wie Größe, Tempo und Farben
  game.py               Klasse Game mit der Spielschleife
  states/               menu.py, playing.py, game_over.py
  entities/             player.py, enemy.py, coin.py
  systems/              Regeln über mehrere Figuren, z. B. collisions.py, score.py
  ui/                   hud.py, menu_view.py
assets/
  images/  sounds/  fonts/   nur bei Grafik oder Ton
(states/, entities/, systems/ und ui/ enthalten je eine __init__.py.)

Ordnerregeln:
- Gestartet wird über den Starten-Knopf im Terminal der App (F5). Er führt main.py aus.
- Importe immer vom Projektordner aus, z. B. from game.entities.player import Player.
- Eine Datei, eine Aufgabe. Datei- und Ordnernamen klein_mit_unterstrich.
- Keine Datei so nennen wie ein Python-Modul, also nicht random.py, math.py oder pygame.py.
- Abhängigkeiten zeigen nach innen: entities/ und systems/ kennen weder ui/ noch states/.
- Ein kleines Textspiel startet mit main.py und game/game.py. Weitere Ordner erst anlegen,
  wenn der erste Baustein dafür entsteht.

Architektur:
- Die Spielschleife hat immer drei getrennte Schritte: Eingabe, Aktualisieren, Zeichnen.
- Spielregeln rechnen nur mit Daten. Eingabe und Anzeige bleiben davon getrennt.
- Jede Spielfigur ist ein Objekt mit update() und draw().
- Zustände wie Menü, Spiel und Spielende klar benennen, statt viele True/False-Variablen.
- Feste Werte stehen in game/settings.py, nicht verstreut im Code.
- Nur main.py startet etwas: if __name__ == "__main__".
- Beginne als Textspiel in der Konsole ohne Zusatzpakete. pygame nur, wenn das Kind Grafik will
  oder pygame schon im Projekt nutzt. Die Installation macht das Kind mit seiner Lehrkraft.

Reihenfolge: Start und Schleife → Figur oder Eingabe → eine Spielregel → Punkte → Gewinnen und
Verlieren → Menü oder Neustart → Feinschliff."""

_BLUEPRINTS = {"gdscript": _GODOT, "python": _PYTHON}


def is_game_project(language: str, description: str | None) -> bool:
    """Godot projects are games; a Python project is one when the child's idea says so."""
    if language == "gdscript":
        return True
    text = (description or "").casefold()
    if any(phrase in text for phrase in _GAME_PHRASES):
        return True
    return any(_is_game_word(word) for word in _WORD.findall(text))


def _is_game_word(word: str) -> bool:
    if word in _GAME_WORDS or word.startswith(_GAME_PREFIXES):
        return True
    if word.startswith(_NOT_GAME_PREFIXES):
        return False
    # Spiel, Spiele, Rennspiel, Quizspiels, but not the verb "spielen".
    return word.endswith(("spiel", "spiele", "spiels"))


def game_blueprint(intent: str, language: str) -> str:
    if intent not in BLUEPRINT_INTENTS or language not in _BLUEPRINTS:
        return ""
    return f"{_SHARED}\n\n{_BLUEPRINTS[language]}"
