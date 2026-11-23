"""WebSocket, admin pages and prompt logging."""

from __future__ import annotations

import json
from typing import Any

import pytest
from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.test import Client
from learnharness_protocol import LearningResponse, StudentMessage
from tutor_helpers import ScriptedProvider

from tutor import engine
from tutor.models import AiCall, AiSettings, TutorSession

pytestmark = pytest.mark.django_db


# Channels closes "old" connections around each step, which would end a test transaction on
# PostgreSQL. SQLite in memory ignores that, so only a real commit behaves the same on both.
@pytest.mark.django_db(transaction=True)
def test_websocket_streams_filtered_chat(
    token: str, session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    from learnharness_server.asgi import application

    scripted["provider"] = ScriptedProvider(
        chunks=[
            "Gute Frage!\n```gdscript\nfunc _process(d):\n\tposition.x += 1\n\tposition.y += 1\n",
            "\tprint(1)\n```\nWas denkst du?",
        ]
    )

    async def talk() -> list[dict[str, Any]]:
        communicator = WebsocketCommunicator(
            application,
            f"/api/v1/sessions/{session.id}/stream",
            headers=[(b"authorization", f"Bearer {token}".encode())],
        )
        connected, _ = await communicator.connect()
        assert connected
        message = StudentMessage(session_id=session.id, project_id="spiel", message="Wie geht's?")
        await communicator.send_to(text_data=message.model_dump_json())
        received = []
        while True:
            data = json.loads(await communicator.receive_from(timeout=5))
            received.append(data)
            if data["type"] != "stream_chunk":
                break
        await communicator.disconnect()
        return received

    received = async_to_sync(talk)()
    final = LearningResponse.model_validate(received[-1])
    streamed = "".join(item["text"] for item in received[:-1])
    assert streamed.strip() == final.message
    assert "position.x" not in streamed and "Was denkst du?" in streamed
    call = AiCall.objects.get()
    assert call.intervened and "position.x" in call.response_text
    assert "position.x" not in call.delivered_text


def test_websocket_rejects_missing_token(session: TutorSession) -> None:
    from learnharness_server.asgi import application

    async def connect() -> bool:
        communicator = WebsocketCommunicator(application, f"/api/v1/sessions/{session.id}/stream")
        connected, _ = await communicator.connect()
        return connected

    assert async_to_sync(connect)() is False


def test_admin_settings_prompts_and_log(
    teacher: Client, session: TutorSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    listing = teacher.get("/admin/tutor/aisettings/")
    assert listing.status_code == 302 and listing["Location"].endswith("/1/change/")
    page = teacher.get("/admin/tutor/aisettings/1/change/")
    assert page.status_code == 200 and "Verbindung testen" in page.content.decode()

    prompts = teacher.get("/ki/prompts/?stufe=7&erfahrung=2")
    html = prompts.content.decode()
    assert prompts.status_code == 200
    assert "Lernstufe 7 von 10" in html and "LearnAgent-Runde" in html

    monkeypatch.setattr("tutor.views.model_available", lambda force=False: (False, 5))
    tested = teacher.post("/ki/verbindung-testen/", follow=True)
    assert "nicht erreichbar" in tested.content.decode()

    call = AiCall.objects.create(
        session=session,
        intent="chat",
        provider="vllm",
        model="m",
        system_prompt="REGELN",
        messages=[{"role": "user", "content": "<kind>Hallo</kind>"}],
        response_text="roh",
        delivered_text="gefiltert",
        harness_notes=["Codeblock ersetzt"],
        intervened=True,
    )
    detail = teacher.get(f"/admin/tutor/aicall/{call.pk}/change/").content.decode()
    assert "REGELN" in detail and "&lt;kind&gt;Hallo" in detail and "Codeblock ersetzt" in detail
    assert teacher.get("/admin/tutor/aicall/?intervened__exact=1").status_code == 200
    assert teacher.get("/admin/tutor/tutorsession/").status_code == 200


def test_prompt_logging_can_be_switched_off(
    session: TutorSession, scripted: dict[str, ScriptedProvider]
) -> None:
    settings = AiSettings.load()
    settings.log_prompts = False
    settings.save()
    scripted["provider"] = ScriptedProvider(chunks=["Hallo!"])
    engine.Tutor(session).handle(
        StudentMessage(session_id=session.id, project_id="spiel", message="geheim")
    )
    call = AiCall.objects.get()
    assert call.messages == [] and call.system_prompt == "" and call.output_tokens == 5
