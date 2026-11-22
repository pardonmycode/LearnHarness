"""Password of the teacher area."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from .base import SettingsBase

_PBKDF2_ITERATIONS = 200_000


def _hash_password(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


class TeacherSettings(SettingsBase):
    """Teacher password."""

    def has_teacher_password(self) -> bool:
        return bool(self._settings.value("teacher/password", ""))

    def set_teacher_password(self, password: str) -> None:
        salt = secrets.token_bytes(16)
        digest = _hash_password(password, salt, _PBKDF2_ITERATIONS)
        self._settings.setValue(
            "teacher/password", f"{_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"
        )

    def check_teacher_password(self, password: str) -> bool:
        stored = str(self._settings.value("teacher/password", ""))
        try:
            iterations_text, salt_hex, digest_hex = stored.split("$")
            expected = bytes.fromhex(digest_hex)
            actual = _hash_password(password, bytes.fromhex(salt_hex), int(iterations_text))
        except ValueError:
            return False
        return hmac.compare_digest(actual, expected)
