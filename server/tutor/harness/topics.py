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
UNLOCK_NEXT_AT = 2  # stage a topic needs before the project button offers the next one
STAGE_KINDS = {1: "multiple_choice", 2: "fill_blanks", 3: "text_blanks"}

MISSION_TOPIC_GUIDE = (
    'Wähle in "skill" genau das Thema, das diese Mission am meisten braucht. '
    "Die Themen stehen in Lernreihenfolge:\n"
    + "\n".join(f"- {topic}: {text}" for topic, text in MISSION_TOPICS.items())
    + "\nWähle ein neues Thema erst, wenn alle Themen davor mindestens Stufe 2 erreicht haben. "
    "Nur wenn das Kind ausdrücklich etwas wünscht, das ein späteres Thema braucht, wähle dieses. "
    "Bleibt das Thema gleich, übe es an einem neuen Teil des Projekts.\n"
    "Die ganze Mission übt dieses eine Thema. Richte die Schritte an der Stufe des Kindes "
    "in diesem Thema aus: 1 = erklären und leicht fragen, 2 = aus Möglichkeiten auswählen, "
    "3 = selbst eintippen."
)

_STAGE_RULES = {
    1: """Stufe 1 von 3 (Verstehen): Erkläre das Thema in "message" in 2 bis 4 einfachen Sätzen mit
einem Bild aus dem Alltag und einem Mini-Beispiel. Stelle danach eine leichte Frage dazu. Das
Beispiel zeigt einen anderen Fall als die Frage: Weder "message" noch "code" verraten die Antwort.
Antworte als JSON. "kind": "multiple_choice". "prompt": die Frage. "code": ein kurzes Beispiel oder
leer. "choices": 2 bis 4 Möglichkeiten, genau eine mit correct=true. "blanks" leer.""",
    2: """Stufe 2 von 3 (Auswählen): Das Kind wählt die richtige Lösung im Dropdown-Menü aus.
Antworte als JSON. "message": kurzer Text ohne Lösung. "kind": "fill_blanks". "prompt": die Aufgabe.
"code": Code mit 1 bis 2 Lücken {{1}}, {{2}}. "blanks" in der Reihenfolge der Lücken, je mit 2 bis 4
"options" und der richtigen "answer" (muss in den options stehen). "choices" leer.""",
    3: """Stufe 3 von 3 (Selbst tippen): Das Kind tippt die Lösung selbst ein.
Antworte als JSON. "message": kurzer Text ohne Lösung. "kind": "text_blanks". "prompt": die Aufgabe,
ohne die Lösung zu verraten. "code": Code mit 1 bis 2 Lücken {{1}}, {{2}}, jede Lücke nur ein kurzer
Ausdruck. "blanks" in der Reihenfolge der Lücken, je mit "answer" (höchstens 40 Zeichen) und in
"alternatives" weiteren richtigen Schreibweisen, sonst leer. "choices" leer.""",
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
    done = '\n"explanation_after_correct": was das Kind nach der richtigen Antwort liest.'
    return about + _STAGE_RULES[stage] + done


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
