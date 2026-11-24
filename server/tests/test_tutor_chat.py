"""The tutor chat works on the child's project and keeps its history small."""

from __future__ import annotations

import pytest
from learnharness_protocol import LearningResponse, StudentMessage
from tutor_helpers import ScriptedProvider

from tutor import engine, harness
from tutor.models import AiSettings, TutorSession

pytestmark = pytest.mark.django_db


def _message(session: TutorSession, **fields: object) -> StudentMessage:
    data = {
        "language": "python",
        "session_id": session.id,
        "project_id": "spiel",
        "current_task": "python_first_program",
        "file": "main.py",
        "code_excerpt": "geheimer_alter_code = 1",
        "excerpt_start_line": 1,
        "last_error": "NameError: alter_fehler",
        "project_description": "Ein Fuchs sammelt Münzen",
        "message": "Warum geht das nicht?",
    }
    return StudentMessage(**(data | fields))


def _ask(session: TutorSession, scripted: dict[str, ScriptedProvider], **fields: object):
    scripted["provider"] = ScriptedProvider(chunks=["Was denkst du?"])
    return engine.Tutor(session).handle(_message(session, **fields))


def test_project_replaces_the_example_task(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    _ask(session, scripted)
    assert "Aktuelle Aufgabe" not in scripted["provider"].calls[0][1][-1]["content"]


def test_without_a_project_the_example_task_stays(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    _ask(session, scripted, project_description=None)
    assert "Aktuelle Aufgabe" in scripted["provider"].calls[0][1][-1]["content"]


def test_history_keeps_only_what_the_child_said(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    _ask(session, scripted)
    _ask(session, scripted, code_excerpt="neuer_code = 2", last_error=None, message="Und jetzt?")
    messages = scripted["provider"].calls[0][1]
    old = "".join(item["content"] for item in messages[:-1])
    assert "Warum geht das nicht?" in old and "Was denkst du?" in old
    assert "geheimer_alter_code" not in old and "alter_fehler" not in old
    assert "neuer_code" in messages[-1]["content"]


def test_project_hint_uses_its_level_without_a_fake_child_message(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    response = _ask(session, scripted, project_hint_level=3, message="Ich brauche Hinweis 3 von 4.")
    assert isinstance(response, LearningResponse)
    assert response.mode == "hint" and response.hint_level == 3
    system, messages = scripted["provider"].calls[0]
    assert "Hinweis der Stufe 3 von 4" in system and "<projekt>" in system
    assert "<kind>" not in messages[-1]["content"]
    assert session.history[-2]["content"] == "(Das Kind bittet um Hinweis 3 von 4.)"


def test_chat_knows_the_childs_topics(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    session.child.set_skill("variables", "Variablen", 2)
    _ask(session, scripted)
    assert "kennt das Kind schon: variables." in scripted["provider"].calls[0][1][-1]["content"]


def test_error_text_counts_as_content() -> None:
    system = harness.system_prompt("chat", AiSettings.load())
    assert "<fehler>" in system[: system.index("7. Wenn")]


def test_chat_wording_and_possibly_old_error(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    _ask(session, scripted)
    prompt = scripted["provider"].calls[0][1][-1]["content"]
    assert "Sie kann schon behoben sein" in prompt
    assert "Braucht die Frage" in prompt and "Übung" not in prompt
