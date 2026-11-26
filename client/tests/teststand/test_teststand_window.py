"""The test stand window reads its form and refuses to start without the essentials."""

from __future__ import annotations

from pathlib import Path

from pytestqt.qtbot import QtBot

from learnharness_client.teststand import window as window_module
from learnharness_client.teststand.window import TeststandWindow


def test_form_switches_provider_and_reports_missing_model(
    qtbot: QtBot, tmp_path: Path, monkeypatch
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(window_module, "setup_problem", lambda: None)
    window = TeststandWindow(tmp_path)
    qtbot.addWidget(window)
    window.provider.setCurrentIndex(window.provider.findData("anthropic"))
    window.anthropic_model.setText("")
    started: list[object] = []
    monkeypatch.setattr(window.runner, "start", started.append)
    window.start_button.click()
    assert started == [] and "Modellnamen" in window.status.text()
    window.provider.setCurrentIndex(window.provider.findData("vllm"))
    assert window.pages.currentIndex() == 1
    window.vllm_model.setText("")  # vLLM: the first model of the server is taken
    window.start_button.click()
    assert len(started) == 1 and window.read_form().provider == "vllm"
    window.runner.check_done.emit(True, "migriert\nVerbindung klappt: qwen")
    assert (
        window.vllm_model.text() == "qwen" and window.status.text() == "✓ Verbindung klappt: qwen"
    )
    window.close()
    assert window_module.stand_config.load(tmp_path).vllm_model == "qwen"
