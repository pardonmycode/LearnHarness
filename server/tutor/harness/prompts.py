"""Builds what goes out to the AI."""

from __future__ import annotations

from learnharness_protocol import StudentMessage

from ..models import AiSettings
from .game_blueprint import game_blueprint
from .rules import (
    ACTIVE_TODO_INTENTS,
    ACTIVE_TODO_RULE,
    BASE_RULES,
    EXPERIENCE,
    INTENTS,
    LANGUAGES,
    LEVELS,
    SKILLS,
)


def system_prompt(
    intent: str,
    settings: AiSettings,
    *,
    learning_level: int | None = None,
    experience_level: int = 0,
    hint_level: int = 1,
    language: str = "gdscript",
    game: bool = False,
    active_todo: bool = False,
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
    if active_todo and intent in ACTIVE_TODO_INTENTS:
        parts.append(ACTIVE_TODO_RULE)
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
    if message.intent == "project_plan" or message.project_todos:
        done = set(message.project_done_todos)
        todos = "\n".join(
            f"- [{'x' if todo in done else ' '}] {todo}" for todo in message.project_todos
        )
        parts.append("To-do-Liste des Kindes:\n" + _tag("todos", todos))
    if message.active_todo:
        parts.append(
            "Daran arbeitet das Kind gerade:\n" + _tag("aktuelles_todo", message.active_todo)
        )
    if message.intent == "project_plan" and message.project_question:
        parts.append("Deine letzte Rückfrage:\n" + _tag("frage", message.project_question))
    if message.skill_focus:
        label = SKILLS.get(message.skill_focus, message.skill_focus)
        parts.append(f"Übungsschwerpunkt: {label} (hier braucht das Kind noch Übung)")
    if extra:
        parts.append(extra)
    parts.append("Nachricht des Kindes:\n" + _tag("kind", message.message))
    return "\n\n".join(parts)
