"""Fake administration server for the sync tests."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from typing import Any
from uuid import uuid4

TOKEN = "geheim"


class FakeAdmin:
    def __init__(self) -> None:
        self.children: dict[str, dict[str, Any]] = {}
        self.archived: set[str] = set()
        self.requests: list[tuple[str, str, Any]] = []
        self.missions: list[dict[str, Any]] = []
        self.completed: dict[str, set[str]] = {}

    def mission_list(self, profile_id: str) -> dict[str, Any]:
        return {
            "type": "mission_list",
            "missions": self.missions,
            "completed": sorted(self.completed.get(profile_id, set())),
        }


def _handler(admin: FakeAdmin) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args: object) -> None:
            pass

        def _reply(self, status: int, body: object) -> None:
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _handle(self, method: str) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"null") if length else None
            admin.requests.append((method, self.path, body))
            if self.headers.get("Authorization") != f"Bearer {TOKEN}":
                self._reply(
                    401, {"type": "error", "code": "unauthorized", "message_for_child": "x"}
                )
                return
            parts = self.path.split("?")[0].strip("/").split("/")  # api v1 children [id] [...]
            if parts[3:] == [] and method == "GET":
                profiles = [c for c in admin.children.values()]
                self._reply(200, {"type": "child_profile_list", "profiles": profiles})
            elif parts[3:] == [] and method == "POST":
                if body["profile_id"] in admin.archived:
                    self._reply(
                        409, {"type": "error", "code": "archived", "message_for_child": "x"}
                    )
                    return
                admin.children.setdefault(body["profile_id"], body)
                self._reply(201, admin.children[body["profile_id"]])
            elif len(parts) >= 4 and parts[3] in admin.children:
                child = admin.children[parts[3]]
                if parts[4:] == ["missions"]:
                    self._reply(200, admin.mission_list(parts[3]))
                    return
                if parts[4:5] == ["missions"] and parts[6:] == ["done"]:
                    if parts[5] not in {m["id"] for m in admin.missions}:
                        self._reply(
                            404,
                            {"type": "error", "code": "unknown_mission", "message_for_child": "x"},
                        )
                        return
                    admin.completed.setdefault(parts[3], set()).add(parts[5])
                    self._reply(200, admin.mission_list(parts[3]))
                    return
                if parts[4:] == ["unlock"]:
                    child["max_level"] = max(child["max_level"], body["level"])
                self._reply(200, child)
            else:
                self._reply(
                    404, {"type": "error", "code": "unknown_child", "message_for_child": "x"}
                )

        def do_GET(self) -> None:  # noqa: N802
            self._handle("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._handle("POST")

    return Handler


def _server_child(pseudonym: str, level: int) -> dict[str, Any]:
    return {
        "type": "child_profile",
        "protocol_version": "1.2",
        "profile_id": uuid4().hex,
        "pseudonym": pseudonym,
        "experience_level": 1,
        "max_level": level,
        "group": None,
    }


def _assigned_mission(mission_id: str) -> dict[str, Any]:
    return {
        "type": "mission",
        "protocol_version": "1.3",
        "id": mission_id,
        "title": "Schatzsuche",
        "goal": "Baue eine Schatzkiste!",
        "skill": None,
        "steps": [
            {"id": "verstehen", "title": "Verstehen", "kind": "understand", "note": None},
            {"id": "testen", "title": "In Godot testen", "kind": "try", "note": None},
        ],
    }
