"""Errors of the harness."""

from __future__ import annotations


class HarnessRejected(Exception):
    """The AI output breaks a rule; the reason goes to the log."""
