from __future__ import annotations

import os
from pathlib import Path

import pytest

from learnharness_client.domain.path_guard import PathGuard, PathNotAllowed


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    (tmp_path / "project.godot").write_text('[application]\nconfig/name="Test"\n')
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "player.gd").write_text("extends Node\n")
    return tmp_path


def test_allows_gd_inside_project(project: Path) -> None:
    guard = PathGuard(project)
    assert guard.ensure_allowed("scripts/player.gd") == (project / "scripts/player.gd").resolve()


@pytest.mark.parametrize("candidate", ["../outside.gd", "scripts/readme.txt"])
def test_rejects_traversal_and_wrong_extension(project: Path, candidate: str) -> None:
    with pytest.raises(PathNotAllowed):
        PathGuard(project).ensure_allowed(candidate, must_exist=False)


def test_rejects_absolute_path_outside(
    project: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("outside") / "bad.gd"
    outside.write_text("extends Node\n")
    with pytest.raises(PathNotAllowed):
        PathGuard(project).ensure_allowed(outside)


def test_rejects_gdignore(project: Path) -> None:
    ignored = project / "ignored"
    ignored.mkdir()
    (ignored / ".gdignore").touch()
    (ignored / "hidden.gd").write_text("extends Node\n")
    with pytest.raises(PathNotAllowed):
        PathGuard(project).ensure_allowed(ignored / "hidden.gd")


def test_rejects_symlink_when_supported(project: Path, tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside_link_target.gd"
    outside.write_text("extends Node\n")
    link = project / "scripts" / "linked.gd"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are unavailable for this test user")
    with pytest.raises(PathNotAllowed):
        PathGuard(project).ensure_allowed(link)


def test_rejects_symlink_to_file_inside_project_when_supported(project: Path) -> None:
    target = project / "scripts" / "player.gd"
    link = project / "scripts" / "alias.gd"
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are unavailable for this test user")
    with pytest.raises(PathNotAllowed):
        PathGuard(project).ensure_allowed(link)
