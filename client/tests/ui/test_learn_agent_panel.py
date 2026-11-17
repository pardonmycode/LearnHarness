from __future__ import annotations

from pytestqt.qtbot import QtBot

from learnharness_client.ui.panels.learn_agent_panel import LearnAgentPanel


def test_levels_are_locked_until_unlocked(qtbot: QtBot) -> None:
    panel = LearnAgentPanel(max_unlocked_level=1)
    qtbot.addWidget(panel)
    model = panel.level_choice.model()
    assert model.item(0).isEnabled()
    assert not model.item(1).isEnabled()
    panel.set_max_unlocked(2)
    assert model.item(1).isEnabled()


def test_prompt_emits_selected_level(qtbot: QtBot) -> None:
    panel = LearnAgentPanel(max_unlocked_level=4)
    qtbot.addWidget(panel)
    panel.level_choice.setCurrentIndex(3)
    panel.prompt.setPlainText("Meine Figur soll laufen")
    with qtbot.waitSignal(panel.start_requested, timeout=1000) as signal:
        panel._start()
    assert signal.args == ["Meine Figur soll laufen", 4]
