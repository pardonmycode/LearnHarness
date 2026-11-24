"""Only the real error of a program reaches the tutor, without private paths."""

from __future__ import annotations

from pathlib import Path

from learnharness_client.domain.run_error import find_run_error, hide_private_paths

TRACE = """Hallo Mia
Traceback (most recent call last):
  File "/x/main.py", line 2, in <module>
    print(punkte)
NameError: name 'punkte' is not defined"""
SYNTAX = """  File "/x/main.py", line 1
    for
       ^
SyntaxError: invalid syntax"""


def test_python_error_without_the_normal_output() -> None:
    found = find_run_error(TRACE, is_python=True, exit_code=1)
    assert found is not None and found.startswith("Traceback") and "Mia" not in found


def test_syntax_error_has_no_traceback_header() -> None:
    assert find_run_error(SYNTAX, is_python=True, exit_code=1) == SYNTAX.strip()


def test_no_error_is_invented() -> None:
    assert find_run_error(TRACE, is_python=True, exit_code=0) is None
    assert find_run_error("Mein Name ist Mia", is_python=True, exit_code=1) is None
    assert find_run_error("Alles gut", is_python=False, exit_code=0) is None


def test_godot_errors_only() -> None:
    output = "Godot Engine\nSCRIPT ERROR: Invalid call\n   at: _ready (res://a.gd:3)\nFertig"
    assert find_run_error(output, is_python=False, exit_code=0) == (
        "SCRIPT ERROR: Invalid call\n   at: _ready (res://a.gd:3)"
    )


def test_private_paths_are_hidden(tmp_path: Path) -> None:
    root = tmp_path / "Mia Mustermann" / "Spiel"
    text = f'File "{root}/main.py"; File "{Path.home()}/lib/x.py"'
    clean = hide_private_paths(text, root)
    assert "Mustermann" not in clean and str(Path.home()) not in clean
    assert 'File "./main.py"' in clean and 'File "~/lib/x.py"' in clean
