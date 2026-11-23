"""Builds what goes out to the AI."""

from __future__ import annotations

from learnharness_protocol import Mission, MissionStep, StudentMessage

from ..models import AiSettings
from .game_blueprint import game_blueprint
from .rules import (
    BASE_RULES,
    EXPERIENCE,
    INTENTS,
    LANGUAGES,
    LEVELS,
    SKILLS,
)
from .topics import MISSION_TOPIC_GUIDE, MISSION_TOPICS, stage_for


def system_prompt(
    intent: str,
    settings: AiSettings,
    *,
    learning_level: int | None = None,
    experience_level: int = 0,
    hint_level: int = 1,
    language: str = "gdscript",
    game: bool = False,
) -> str:
    words = LANGUAGES.get(language, LANGUAGES["gdscript"])
    parts = [
        BASE_RULES.format(
            max_lines=settings.max_code_lines_in_chat,
            subject=words["subject"],
            fence=words["fence"],
            topic=words["topic"],
        )
    ]
    parts.append(f"Das Kind {EXPERIENCE.get(experience_level, EXPERIENCE[0])}.")
    if learning_level:
        parts.append(f"Lernstufe {learning_level} von 10: {LEVELS.get(learning_level, '')}")
    template = INTENTS.get(intent, INTENTS["chat"])
    parts.append(
        template.format(
            hint_level=hint_level,
            max_changed=settings.max_changed_lines,
            work=words["work"],
            try_step=words["try"],
        )
    )
    if intent == "mission":
        parts.append(MISSION_TOPIC_GUIDE)
    blueprint = game_blueprint(intent, language) if game else ""
    if blueprint:
        parts.append(blueprint)
    if settings.teacher_instructions.strip():
        parts.append(
            "Zusätzliche Hinweise der Lehrkraft (die festen Regeln oben gelten trotzdem):\n"
            + settings.teacher_instructions.strip()
        )
    return "\n\n".join(parts)


def _tag(name: str, text: str) -> str:
    # The closing tag inside the child's text must not end the block early.
    return f"<{name}>\n{text.replace(f'</{name}>', f'</ {name}>')}\n</{name}>"


def topic_levels(levels: dict[str, int]) -> str:
    """Server-side stages per topic, for planning a mission that fits the child."""
    lines = [f"- {topic}: Stufe {stage_for(levels.get(topic, 1))}" for topic in MISSION_TOPICS]
    return "Stufen des Kindes je Thema:\n" + "\n".join(lines)


def mission_step_context(mission: Mission, step: MissionStep) -> str:
    """The whole plan, so a step builds on earlier ones and leaves later ones alone."""
    current = mission.steps.index(step)
    lines = [f"Titel: {mission.title}", f"Ziel: {mission.goal}", "Schritte:"]
    for index, item in enumerate(mission.steps):
        mark = "x" if index < current else (">" if index == current else " ")
        lines.append(f"- [{mark}] {item.title} (Art: {item.kind})")
    return "Die Mission:\n" + _tag("mission", "\n".join(lines))


def user_prompt(message: StudentMessage, *, task: str | None = None, extra: str = "") -> str:
    parts = []
    if task:
        parts.append(f"Aktuelle Aufgabe: {task}")
    if message.file:
        parts.append(f"Datei: {message.file}")
    if message.code_excerpt:
        start = message.excerpt_start_line or 1
        parts.append(f"Code ab Zeile {start}:\n" + _tag("code", message.code_excerpt))
    elif message.intent in ("learn", "mission_step"):
        parts.append("Code der Datei:\n" + _tag("code", ""))
    if message.last_error:
        source = LANGUAGES[message.language]["error_source"]
        parts.append(f"Letzte Fehlermeldung aus {source}:\n" + _tag("fehler", message.last_error))
    if message.project_description:
        parts.append("Projektidee des Kindes:\n" + _tag("projekt", message.project_description))
    if message.project_done_missions:
        finished = "\n".join(f"- {title}" for title in message.project_done_missions)
        parts.append("Schon geschaffte Missionen:\n" + _tag("fertige_missionen", finished))
    if message.intent == "project_plan" and message.project_turns:
        talk = "\n".join(
            f"Frage: {turn.question}\nAntwort: {turn.answer}" for turn in message.project_turns
        )
        parts.append("Bisheriges Gespräch über das Projekt:\n" + _tag("gespraech", talk))
    if message.intent == "project_plan" and message.project_skipped_questions:
        skipped = "\n".join(f"- {question}" for question in message.project_skipped_questions)
        parts.append(
            "Diese Fragen wollte das Kind nicht beantworten:\n" + _tag("uebersprungen", skipped)
        )
    if message.intent == "project_plan" and message.project_question:
        parts.append("Deine letzte Rückfrage:\n" + _tag("frage", message.project_question))
    if message.skill_focus:
        label = SKILLS.get(message.skill_focus, message.skill_focus)
        parts.append(f"Übungsschwerpunkt: {label} (hier braucht das Kind noch Übung)")
    if extra:
        parts.append(extra)
    # Started by a button: the message is only a step id or repeats the description.
    by_button = message.intent == "mission_step" or (
        message.intent == "project_plan" and not message.project_question
    )
    if not by_button:
        parts.append("Nachricht des Kindes:\n" + _tag("kind", message.message))
    return "\n\n".join(parts)
