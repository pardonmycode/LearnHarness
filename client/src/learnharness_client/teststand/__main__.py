"""Entry point of the test stand window."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .window import TeststandWindow


def main() -> int:
    app = QApplication(sys.argv[:1])
    window = TeststandWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
