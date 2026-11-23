"""Which kind of exercise each of the ten LearnAgent levels uses."""

from __future__ import annotations

from .topics import MAX_EXERCISE_CODE_LINES, MISSION_TOPICS

LEVEL_KINDS = {
    1: "multiple_choice",
    2: "multiple_choice",
    3: "fill_blanks",
    4: "fill_blanks",
    5: "ordering",
    6: "text_blanks",
    7: "text_blanks",
    8: "find_bug",
    9: "find_bug",
    10: "find_bug",
}

_FORMATS = {
    "multiple_choice": """Antworte als JSON. "message": kurzer Text ohne Lösung. "kind":
"multiple_choice". "prompt": die Frage. "code": ein kurzes Beispiel (höchstens {max_code} Zeilen)
oder leer, es verrät die Antwort nicht. "choices": 2 bis 4 Möglichkeiten, genau eine mit
correct=true. "blanks" leer.""",
    "fill_blanks": """Antworte als JSON. "message": kurzer Text ohne Lösung. "kind": "fill_blanks".
"prompt": die Aufgabe. "code": Code (höchstens {max_code} Zeilen) mit 1 bis 2 Lücken {{1}}, {{2}}.
Jede Zeile mit einer Lücke steht mit der richtigen Antwort genau so in "new_file_content". "blanks"
in der Reihenfolge der Lücken, je mit 2 bis 4 "options" und der richtigen "answer". Genau eine
Option ist richtig: Die anderen wären im Programm wirklich falsch. Ist die Lücke ein frei wählbarer
Wert, nenne ihn in "prompt", zum Beispiel „Der Fuchs startet mit 5 Münzen“. "choices" leer.""",
    "ordering": """Antworte als JSON. "message": kurzer Text ohne Lösung. "kind": "ordering".
"prompt": was das Kind sortieren soll. "ordered_lines": 3 bis {max_code} verschiedene Codezeilen in
der richtigen Reihenfolge, mit Einrückung. Es darf nur eine richtige Reihenfolge geben. Diese Zeilen
stehen in genau dieser Reihenfolge in "new_file_content".""",
    "text_blanks": """Antworte als JSON. "message": kurzer Text ohne Lösung. "kind": "text_blanks".
"prompt": die Aufgabe, ohne den Code der Lösung zu verraten. Sie hat genau eine Lösung. Ist die
Lücke ein frei wählbarer Wert, nenne ihn in "prompt", zum Beispiel „Der Fuchs startet mit 5 Münzen“.
"code": Code (höchstens {max_code} Zeilen) mit 1 bis 2 Lücken {{1}}, {{2}}, jede nur ein kurzer
Ausdruck. Jede Zeile mit einer Lücke steht mit der richtigen Antwort genau so in
"new_file_content". "blanks" in der Reihenfolge der Lücken, je mit "answer" (höchstens 40 Zeichen)
und in "alternatives" weiteren richtigen Schreibweisen, sonst leer. "choices" leer.""",
    "find_bug": """Antworte als JSON. "message": kurzer Text ohne Lösung. "kind": "find_bug".
"prompt": was der Code tun soll, ohne die falsche Zeile zu nennen. "buggy_lines": 3 bis {max_code}
Codezeilen mit Einrückung, genau eine davon ist falsch. "bug_line": die Nummer der falschen Zeile,
ab 1 gezählt. "new_file_content" enthält die richtige Version und nicht die falsche Zeile.""",
}


def level_instructions(level: int) -> str:
    rule = _FORMATS[LEVEL_KINDS[level]].replace("{max_code}", str(MAX_EXERCISE_CODE_LINES))
    return (
        rule + '\n"skill": das Thema, das die Übung trainiert. "explanation_after_correct": '
        "was das Kind nach der richtigen Antwort liest."
    )


def learn_topics_note(levels: dict[str, int]) -> str:
    """Keeps the released code close to what the child has met so far."""
    known = [topic for topic in MISSION_TOPICS if levels.get(topic, 0) >= 1]
    start = (
        f"Diese Themen kennt das Kind schon: {', '.join(known)}."
        if known
        else "Das Kind hat noch kein Thema begonnen."
    )
    return (
        f"{start} Nutze in Übung und neuem Code nur diese, auch wenn ein Bauplan mehr vorsieht. "
        "Braucht der Wunsch ein weiteres Thema, nimm nur dieses eine und erkläre es einfach. "
        "Vorhandenen Code darfst du weiter nutzen."
    )
