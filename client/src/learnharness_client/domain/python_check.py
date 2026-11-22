"""Syntax check for Python scripts. The code is only parsed, never executed."""

from __future__ import annotations

import ast
import warnings
from dataclasses import dataclass

from ..texts import T


@dataclass(frozen=True, slots=True)
class PythonProblem:
    line: int
    message: str


def check_python(text: str, file_name: str) -> list[PythonProblem]:
    """Return the first syntax error; Python's parser stops there."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ast.parse(text, filename=file_name)
    except SyntaxError as exc:
        return [PythonProblem(max(1, exc.lineno or 1), exc.msg)]
    except (ValueError, RecursionError, MemoryError):
        # Null bytes or code nested too deeply for the parser.
        return [PythonProblem(1, T.PYTHON_CHECK_UNREADABLE)]
    return []
