"""The device token only goes to the learning server when it is the administration itself."""

from __future__ import annotations

from PyQt6.QtNetwork import QNetworkRequest
from pytestqt.qtbot import QtBot

from learnharness_client.net.http_tutor_client import HttpTutorClient, same_server


def test_same_server() -> None:
    assert same_server("http://schule:8000", "http://SCHULE:8000/")
    assert not same_server("http://schule:8000", "http://schule:8001")
    assert not same_server("http://schule:8000", "https://schule:8000")
    assert not same_server("http://lernserver:8000", "http://verwaltung:8000")
    assert not same_server("http://schule:8000", "")


def test_token_header_only_when_given(qtbot: QtBot) -> None:
    with_token = HttpTutorClient("http://schule:8000", token=" geheim ")
    request = with_token._authorize(QNetworkRequest())
    assert bytes(request.rawHeader(b"Authorization")) == b"Bearer geheim"
    without = HttpTutorClient("http://schule:8000")
    assert not without._authorize(QNetworkRequest()).hasRawHeader(b"Authorization")
