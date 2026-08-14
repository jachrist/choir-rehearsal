"""Tester for homr-subprosess-wrapperen. Kjører uten at ekte homr er installert
ved å mocke ``shutil.which`` og ``subprocess.run``."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from choir_rehearsal.omr import homr_runner
from choir_rehearsal.omr.homr_runner import (
    HomrError,
    HomrNotInstalledError,
    homr_available,
    run_homr,
)


def test_homr_available_returns_bool():
    assert isinstance(homr_available(), bool)


def test_run_homr_raises_when_not_installed(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(homr_runner.shutil, "which", lambda _: None)
    img = tmp_path / "side.png"
    img.write_bytes(b"fake")
    with pytest.raises(HomrNotInstalledError):
        run_homr(img)


def test_run_homr_missing_image(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(homr_runner.shutil, "which", lambda _: "/usr/bin/homr")
    with pytest.raises(FileNotFoundError):
        run_homr(tmp_path / "finnes-ikke.png")


def _fake_run_factory(returncode: int, write_output: bool):
    def _fake_run(cmd, **kwargs):
        # Siste argument er bildestien
        image = Path(cmd[-1])
        if write_output:
            image.with_suffix(".musicxml").write_text("<score-partwise/>", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, returncode, stdout="ut", stderr="feil")

    return _fake_run


def test_run_homr_success_returns_output_path(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(homr_runner.shutil, "which", lambda _: "/usr/bin/homr")
    monkeypatch.setattr(homr_runner.subprocess, "run", _fake_run_factory(0, write_output=True))
    img = tmp_path / "side-000.png"
    img.write_bytes(b"fake")
    out = run_homr(img)
    assert out == img.with_suffix(".musicxml")
    assert out.exists()


def test_run_homr_nonzero_exit_raises(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(homr_runner.shutil, "which", lambda _: "/usr/bin/homr")
    monkeypatch.setattr(homr_runner.subprocess, "run", _fake_run_factory(1, write_output=False))
    img = tmp_path / "side.png"
    img.write_bytes(b"fake")
    with pytest.raises(HomrError):
        run_homr(img)


def test_run_homr_missing_output_raises(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(homr_runner.shutil, "which", lambda _: "/usr/bin/homr")
    monkeypatch.setattr(homr_runner.subprocess, "run", _fake_run_factory(0, write_output=False))
    img = tmp_path / "side.png"
    img.write_bytes(b"fake")
    with pytest.raises(HomrError, match="ingen MusicXML"):
        run_homr(img)


def test_run_homr_timeout_raises(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(homr_runner.shutil, "which", lambda _: "/usr/bin/homr")

    def _timeout(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 1))

    monkeypatch.setattr(homr_runner.subprocess, "run", _timeout)
    img = tmp_path / "side.png"
    img.write_bytes(b"fake")
    with pytest.raises(HomrError, match="tidsavbrudd"):
        run_homr(img, timeout=1)
