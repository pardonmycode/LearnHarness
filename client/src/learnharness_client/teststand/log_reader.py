"""Reads the AI calls the local server logged, straight from its SQLite file."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_COLUMNS = (
    "id, created_at, intent, provider, model, ok, duration_ms, input_tokens, output_tokens, "
    "intervened, system_prompt, messages, response_text, delivered_text, harness_notes, error"
)


@dataclass(frozen=True)
class AiCallRow:
    id: int
    created_at: str
    intent: str
    provider: str
    model: str
    ok: bool
    duration_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    intervened: bool
    system_prompt: str
    messages: list[dict[str, Any]]
    response_text: str
    delivered_text: str
    harness_notes: list[str]
    error: str


def _json_list(value: Any) -> list[Any]:
    try:
        data = json.loads(value) if isinstance(value, str) else value
    except ValueError:
        return []
    return data if isinstance(data, list) else []


def read_calls(database: Path, after_id: int = 0, limit: int = 200) -> list[AiCallRow]:
    """New calls after ``after_id``; empty while the server has not created its tables yet."""
    if not database.is_file():
        return []
    try:
        connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=1)
    except sqlite3.Error:
        return []
    try:
        rows = connection.execute(
            f"SELECT {_COLUMNS} FROM tutor_aicall WHERE id > ? ORDER BY id LIMIT ?",  # noqa: S608
            (after_id, limit),
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        connection.close()
    return [
        AiCallRow(
            id=row[0],
            created_at=str(row[1])[:19].replace("T", " "),
            intent=row[2],
            provider=row[3],
            model=row[4],
            ok=bool(row[5]),
            duration_ms=row[6],
            input_tokens=row[7],
            output_tokens=row[8],
            intervened=bool(row[9]),
            system_prompt=row[10] or "",
            messages=[item for item in _json_list(row[11]) if isinstance(item, dict)],
            response_text=row[12] or "",
            delivered_text=row[13] or "",
            harness_notes=[str(item) for item in _json_list(row[14])],
            error=row[15] or "",
        )
        for row in rows
    ]


def format_messages(messages: list[dict[str, Any]]) -> str:
    """The conversation as the AI got it, one block per message."""
    return "\n\n".join(
        f"── {item.get('role', '?')} ──\n{item.get('content', '')}" for item in messages
    )
