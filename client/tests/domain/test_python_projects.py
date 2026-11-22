"""Python projects: discovery, creation, path protection and the syntax check."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from learnharness_client.domain.backup import BackupManager
from learnharness_client.domain.file_store import FileStore
from learnharness_client.domain.path_guard import PathNotAllowed
from learnharness_client.domain.project import Project, create_python_project, is_project_folder
from learnharness_client.domain.python_check import check_python


def _python_project(tmp_path: Path) -> Project:
    root = tmp_path / "rechner"
    root.mkdir()
    (root / "main.py").write_text("print('hi')\n", encoding="utf-8")
    return Project.open(root)


def test_folder_with_script_opens_as_python(tmp_path: Path) -> None:
    project = _python_project(tmp_path)
    assert project.language == "python"
    assert project.name == "rechner"
    assert [path.name for path in project.guard.iter_scripts()] == ["main.py"]


def test_godot_wins_when_both_exist(tmp_path: Path) -> None:
    (tmp_path / "project.godot").write_text('config/name="Spiel"\n', encoding="utf-8")
    (tmp_path / "tool.py").write_text("x = 1\n", encoding="utf-8")
    project = Project.open(tmp_path)
    assert project.language == "gdscript"
    with pytest.raises(PathNotAllowed):
        project.guard.ensure_allowed(tmp_path / "tool.py")


def test_empty_folder_is_no_project(tmp_path: Path) -> None:
    assert not is_project_folder(tmp_path)
    with pytest.raises(PathNotAllowed):
        Project.open(tmp_path)


def test_home_folder_is_refused(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "stray.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    with pytest.raises(PathNotAllowed):
        Project.open(tmp_path)


def test_installed_and_hidden_code_is_invisible(tmp_path: Path) -> None:
    project = _python_project(tmp_path)
    for folder in ("__pycache__", ".venv/lib", "meinenv/lib", "app"):
        (project.root / folder).mkdir(parents=True)
        (project.root / folder / "mod.py").write_text("x = 1\n", encoding="utf-8")
    (project.root / "meinenv" / "pyvenv.cfg").write_text("home = /usr\n", encoding="utf-8")
    names = [p.relative_to(project.root).as_posix() for p in project.guard.iter_scripts()]
    assert names == ["app/mod.py", "main.py"]
    with pytest.raises(PathNotAllowed):
        project.guard.ensure_allowed(project.root / "meinenv" / "lib" / "mod.py")


def test_guard_rejects_other_files_and_escapes(tmp_path: Path) -> None:
    project = _python_project(tmp_path)
    (project.root / "notes.txt").write_text("x", encoding="utf-8")
    (tmp_path / "outside.py").write_text("x = 1\n", encoding="utf-8")
    for path in (project.root / "notes.txt", "../outside.py", tmp_path / "outside.py"):
        with pytest.raises(PathNotAllowed):
            project.guard.ensure_allowed(path)


def test_create_project_writes_valid_files(tmp_path: Path) -> None:
    project = create_python_project(tmp_path, "Mein Übungs-Spiel")
    assert project.language == "python"
    assert project.name == "Mein Übungs-Spiel"
    assert check_python((project.root / "main.py").read_text(encoding="utf-8"), "main.py") == []
    settings = tomllib.loads((project.root / "pyproject.toml").read_text(encoding="utf-8"))
    assert settings["project"]["name"] == "mein-uebungs-spiel"


@pytest.mark.parametrize("name", ["", "..", "a/b", "a\\b", ".hidden", "CON", "x" * 61, "name."])
def test_create_project_rejects_bad_names(tmp_path: Path, name: str) -> None:
    with pytest.raises(PathNotAllowed):
        create_python_project(tmp_path, name)
    assert list(tmp_path.iterdir()) == []


def test_create_project_never_touches_existing_folder(tmp_path: Path) -> None:
    existing = tmp_path / "Spiel"
    existing.mkdir()
    (existing / "main.py").write_text("# meins\n", encoding="utf-8")
    with pytest.raises(PathNotAllowed):
        create_python_project(tmp_path, "Spiel")
    assert (existing / "main.py").read_text(encoding="utf-8") == "# meins\n"


def test_new_script_uses_python_template(tmp_path: Path) -> None:
    project = _python_project(tmp_path)
    store = FileStore(project.guard, BackupManager(tmp_path / "data", project.project_id))
    document = store.create("neu.py")
    assert document.path.read_text(encoding="utf-8") == 'print("Hallo!")\n'


def test_check_finds_error_line_and_never_runs_code(tmp_path: Path) -> None:
    marker = tmp_path / "ran.txt"
    code = f"open({str(marker)!r}, 'w').write('x')\n"
    assert check_python(code, "main.py") == []
    assert not marker.exists()
    problems = check_python("x = 1\nif x\n    print(x)\n", "main.py")
    assert [problem.line for problem in problems] == [2]
