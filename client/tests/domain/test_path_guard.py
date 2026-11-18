from __future__ import annotations

import os
import subprocess
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


@pytest.mark.parametrize(
    "candidate",
    [
        "scripts/../../outside.gd",
        "scripts/../../../etc/passwd.gd",
        "..\\outside.gd",
        "scripts/player.gd.txt",
        "scripts/player",
        "scripts/scene.tscn",
        "project.godot",
        ".godot/cache.gd",
        ".git/hooks/hook.gd",
        "addons/plugin/tool.gd",
    ],
)
def test_rejects_escapes_wrong_types_and_protected_folders(project: Path, candidate: str) -> None:
    with pytest.raises(PathNotAllowed):
        PathGuard(project).ensure_allowed(candidate, must_exist=False)


def test_rejects_project_root_itself(project: Path) -> None:
    with pytest.raises(PathNotAllowed):
        PathGuard(project).ensure_allowed(project, must_exist=False)


def test_traversal_that_stays_inside_is_allowed(project: Path) -> None:
    guard = PathGuard(project)
    assert (
        guard.ensure_allowed("scripts/../scripts/player.gd")
        == (project / "scripts" / "player.gd").resolve()
    )


@pytest.mark.skipif(os.name != "nt", reason="Windows file names are case-insensitive")
def test_case_insensitive_on_windows(project: Path) -> None:
    guard = PathGuard(project)
    expected = (project / "scripts" / "player.gd").resolve()
    assert guard.ensure_allowed("SCRIPTS/Player.GD") == expected
    assert guard.ensure_allowed(str(project).upper() + "\\scripts\\player.gd") == expected
    with pytest.raises(PathNotAllowed):
        guard.ensure_allowed(".GODOT/x.gd", must_exist=False)
    with pytest.raises(PathNotAllowed):
        guard.ensure_allowed("Addons/x.gd", must_exist=False)


def _make_junction(link: Path, target: Path) -> bool:
    if os.name != "nt":
        return False
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0 and link.exists()


def test_rejects_junction_to_outside_folder(
    project: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    outside = tmp_path_factory.mktemp("junction_target")
    (outside / "evil.gd").write_text("extends Node\n")
    link = project / "linked"
    if not _make_junction(link, outside):
        pytest.skip("Junctions are only available on Windows")
    guard = PathGuard(project)
    with pytest.raises(PathNotAllowed):
        guard.ensure_allowed(link / "evil.gd")
    with pytest.raises(PathNotAllowed):
        guard.ensure_allowed("linked/new.gd", must_exist=False)
    assert all("linked" not in path.parts for path in guard.iter_scripts())


def test_rejects_junction_back_into_project(project: Path) -> None:
    link = project / "alias_dir"
    if not _make_junction(link, project / "scripts"):
        pytest.skip("Junctions are only available on Windows")
    with pytest.raises(PathNotAllowed):
        PathGuard(project).ensure_allowed(link / "player.gd")


def test_rejects_symlink_to_file_inside_project_when_supported(project: Path) -> None:
    target = project / "scripts" / "player.gd"
    link = project / "scripts" / "alias.gd"
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks are unavailable for this test user")
    with pytest.raises(PathNotAllowed):
        PathGuard(project).ensure_allowed(link)
