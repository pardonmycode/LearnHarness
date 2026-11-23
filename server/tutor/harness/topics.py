"""The topics missions teach and the three stages every child works through per topic."""

from __future__ import annotations

# Stable ids, shared with the progress in the administration. The order is the learning order.
MISSION_TOPICS: dict[str, str] = {
    "variables": "Variablen speichern Informationen wie Namen, Punkte oder Leben: leben = 100",
    "operators": "Operatoren rechnen und vergleichen: + - * /, == > <, and or not",
    "conditions": "Bedingungen (if/else) treffen Entscheidungen: wenn leben == 0: spiel_ende()",
    "loops": "Schleifen wiederholen Anweisungen: for (5-mal) oder while (solange etwas stimmt)",
    "functions": "Funktionen fassen Anweisungen zusammen, die man wiederverwendet: springen()",
    "arrays": 'Listen und Arrays speichern vieles zusammen: inventar = ["Schwert", "Apfel"]',
    "classes": "Klassen und Objekte sind Baupläne: Klasse Spieler mit Leben und Position",
}
STAGE_UP_AFTER = 3  # mission exercises solved at the first try before the next stage starts
MAX_STAGE = 3
MAX_EXERCISE_CODE_LINES = 6  # what the child sees in the exercise, not the released file
UNLOCK_NEXT_AT = 2  # stage a topic needs before the project button offers the next one
STAGE_KINDS = {1: "multiple_choice", 2: "fill_blanks", 3: "text_blanks"}

MISSION_TOPIC_GUIDE = (
    '"skill": genau das Thema, das diese Mission am meisten braucht. Die ganze Mission übt dieses '
    "eine Thema. Die Themen stehen in Lernreihenfolge:\n"
    + "\n".join(f"- {topic}: {text}" for topic, text in MISSION_TOPICS.items())
    + "\nDie Beispiele sind nur Skizzen: Nutze die Schreibweise der Sprache des Kindes.\n"
    "Wähle ein neues Thema erst, wenn alle Themen davor mindestens Stufe 2 erreicht haben. "
    "Nur wenn das Kind ausdrücklich etwas wünscht, das ein späteres Thema braucht, wähle dieses. "
    "Bleibt das Thema gleich, übe es an einem neuen Teil des Projekts.\n"
    "Nutze außer dem gewählten Thema nur Themen, die das Kind schon begonnen hat. Das gilt auch, "
    "wenn ein Bauplan weiter unten Klassen, Schleifen oder Funktionen vorsieht: Baue dann eine "
    "einfachere Version.\n"
    "Richte die Schritte an der Stufe des Kindes in diesem Thema aus: 1 = erklären und leicht "
    "fragen, 2 = aus Möglichkeiten auswählen, 3 = selbst eintippen. Ein neues Thema beginnt auf "
    "Stufe 1."
)

_STAGE_RULES = {
    1: """Stufe 1 von 3 (Verstehen): Erkläre den Schritt in "message" in 2 bis 4 einfachen Sätzen.
Steht in <mission> noch kein [x], führe das Thema mit einem Bild aus dem Alltag und einem
Mini-Beispiel ein. Sonst erkläre nur, was in diesem Schritt neu ist, und wiederhole nichts.
Stelle danach eine leichte Frage dazu. Ein Beispiel zeigt einen anderen Fall als die Frage:
Weder "message" noch "code" verraten die Antwort.
Antworte als JSON. "kind": "multiple_choice". "prompt": die Frage. "code": ein kurzes Beispiel
(höchstens {max_code} Zeilen) oder leer. "choices": 2 bis 4 Möglichkeiten, genau eine mit
correct=true. "blanks" leer.""",
    2: """Stufe 2 von 3 (Auswählen): Das Kind wählt die richtige Lösung im Dropdown-Menü aus.
Antworte als JSON. "message": kurzer Text ohne Lösung. "kind": "fill_blanks". "prompt": die Aufgabe.
"code": Code (höchstens {max_code} Zeilen) mit 1 bis 2 Lücken {{1}}, {{2}}. "blanks" in der
Reihenfolge der Lücken, je mit 2 bis 4 "options" und der richtigen "answer" (muss in den options
stehen). Genau eine Option ist richtig: Die anderen wären im Programm wirklich falsch und sind keine
andere Schreibweise der Lösung. Ist die Lücke ein frei wählbarer Wert wie eine Zahl oder ein Text,
nenne den Wert in "prompt", zum Beispiel „Der Fuchs startet mit 5 Münzen“. "choices" leer.""",
    3: """Stufe 3 von 3 (Selbst tippen): Das Kind tippt die Lösung selbst ein.
Antworte als JSON. "message": kurzer Text ohne Lösung. "kind": "text_blanks". "prompt": die Aufgabe,
ohne den Code der Lösung zu verraten. Die Aufgabe hat genau eine Lösung. Ist die Lücke ein frei
wählbarer Wert wie eine Zahl oder ein Text, nenne den Wert in "prompt", zum Beispiel „Der Fuchs
startet mit 5 Münzen“. "code": Code (höchstens {max_code} Zeilen) mit 1 bis 2 Lücken {{1}}, {{2}},
jede Lücke nur ein kurzer Ausdruck. "blanks" in der Reihenfolge der Lücken, je mit "answer"
(höchstens 40 Zeichen) und in "alternatives" weiteren richtigen Schreibweisen, sonst leer.
"choices" leer.""",
}


def stage_for(level: int) -> int:
    """A stored skill level as stage; a topic that was never started begins at 1."""
    return max(1, min(MAX_STAGE, level))


def reachable_topics(levels: dict[str, int]) -> list[str]:
    """Topics in learning order, up to and including the first one below the unlock stage."""
    reachable: list[str] = []
    for topic in MISSION_TOPICS:
        reachable.append(topic)
        if levels.get(topic, 0) < UNLOCK_NEXT_AT:
            break
    return reachable


def stage_instructions(topic: str | None, stage: int) -> str:
    about = f"Thema dieser Mission: {MISSION_TOPICS[topic]}\n\n" if topic else ""
    skill = f'"{topic}"' if topic else "das passende Thema"
    rule = _STAGE_RULES[stage].replace("{max_code}", str(MAX_EXERCISE_CODE_LINES))
    done = (
        f'\n"skill": {skill}. "explanation_after_correct": was das Kind nach der richtigen '
        "Antwort liest."
    )
    return about + rule + done


def known_topics_note(levels: dict[str, int], topic: str | None) -> str:
    """Keeps an exercise and its code within what the child has met so far."""
    known = [t for t in MISSION_TOPICS if levels.get(t, 0) >= 1 or t == topic]
    if not known:
        return "Das Kind hat noch kein Thema begonnen: Nutze nur die einfachsten Anweisungen."
    return (
        f"Diese Themen kennt das Kind schon: {', '.join(known)}. Nutze in Übung und neuem Code nur "
        "diese, auch wenn ein Bauplan mehr vorsieht. Vorhandenen Code darfst du weiter nutzen."
    )


def normalize_typed(text: str) -> str:
    """Spaces around symbols and the kind of quotes must not make a typed answer wrong."""
    result: list[str] = []
    quote = ""
    space = False
    for char in text.strip():
        if quote:
            result.append('"' if char == quote else char)
            quote = "" if char == quote else quote
        elif char.isspace():
            space = True
        else:
            word = char.isalnum() or char == "_"
            if space and word and result and (result[-1].isalnum() or result[-1] == "_"):
                result.append(" ")
            space = False
            if char in "\"'":
                quote = char
                result.append('"')
            else:
                result.append(char)
    return "".join(result)
