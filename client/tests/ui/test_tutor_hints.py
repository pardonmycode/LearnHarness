"""The hint button works on the child's project."""

from __future__ import annotations

from pathlib import Path

import pytest
from learnharness_protocol import StudentMessage
from project_tab_helpers import _record, make_window
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot

from learnharness_client.domain.project import create_python_project
from learnharness_client.net.tutor_client import ClientError
from learnharness_client.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot: QtBot, tmp_path: Path, monkeypatch: MonkeyPatch) -> MainWindow:
    return make_window(qtbot, tmp_path, monkeypatch)


def _hint(qtbot: QtBot, window: MainWindow) -> None:
    with qtbot.waitSignal(window.tutor_client.stream_finished, timeout=3000):
        window.tutor_panel.hint_button.click()


def _levels(sent: list[StudentMessage]) -> list[int | None]:
    return [message.project_hint_level for message in sent]


def test_project_hints_count_up_and_stop_at_four(qtbot: QtBot, window: MainWindow) -> None:
    sent = _record(window)
    window.project_panel.description.setPlainText("Ein Quiz")
    for _ in range(5):
        _hint(qtbot, window)
    assert _levels(sent) == [1, 2, 3, 4, 4]
    assert window.tutor_panel.hint_progress.value() == 4


def test_new_question_starts_hints_again(qtbot: QtBot, window: MainWindow) -> None:
    sent = _record(window)
    window.project_panel.description.setPlainText("Ein Quiz")
    _hint(qtbot, window)
    with qtbot.waitSignal(window.tutor_client.stream_finished, timeout=3000):
        window.send_tutor_message("Neue Frage")
    assert window.tutor_panel.hint_progress.value() == 0
    qtbot.waitUntil(window.tutor_panel.hint_button.isEnabled)
    _hint(qtbot, window)
    assert _levels(sent) == [1, None, 1]


def test_failed_hint_can_be_asked_again(qtbot: QtBot, window: MainWindow) -> None:
    sent = _record(window)
    window.project_panel.description.setPlainText("Ein Quiz")
    _hint(qtbot, window)
    window.tutor_panel.hint_button.setEnabled(True)
    window._pending_hint = 2
    window._client_error(ClientError("Pause", "fake_timeout"))
    _hint(qtbot, window)
    assert _levels(sent) == [1, 2]


def test_without_a_project_the_example_task_hint_stays(
    qtbot: QtBot, window: MainWindow, monkeypatch: MonkeyPatch
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(window.tutor_client, "request_next_hint", calls.append)
    window.tutor_panel.hint_button.click()
    assert calls == [window.current_task_id]


def test_opening_another_project_resets_hints(
    qtbot: QtBot, window: MainWindow, tmp_path: Path
) -> None:
    window.project_panel.description.setPlainText("Ein Quiz")
    _hint(qtbot, window)
    window.open_project(create_python_project(tmp_path, "Anderes"))
    assert window._project_hint_level == 0 and window.tutor_panel.hint_progress.value() == 0
