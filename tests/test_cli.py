"""Tester for CLI-inngangen (Fase 1). Mocker homr/pipelinen."""

from __future__ import annotations

from pathlib import Path

from choir_rehearsal import cli


def test_missing_pdf_returns_2(capsys):
    rc = cli.main(["fase1", "finnes-ikke.pdf"])
    assert rc == 2
    assert "Finner ikke PDF" in capsys.readouterr().err


def test_homr_unavailable_returns_3(monkeypatch, tmp_path: Path, capsys):
    pdf = tmp_path / "n.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(cli, "homr_available", lambda: False)
    rc = cli.main(["fase1", str(pdf)])
    assert rc == 3
    assert "homr er ikke installert" in capsys.readouterr().err


def test_happy_path_returns_0(monkeypatch, tmp_path: Path, capsys):
    pdf = tmp_path / "n.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(cli, "homr_available", lambda: True)

    from choir_rehearsal.pipeline.phase1 import PageResult, Phase1Result

    fake = Phase1Result(pdf_path=pdf, pages=[PageResult(page_index=0, ok=True, notes=3)])
    monkeypatch.setattr(cli, "process_pdf", lambda *a, **k: fake)

    rc = cli.main(["fase1", str(pdf), "--out-dir", str(tmp_path / "out")])
    assert rc == 0
    assert "Fase 1-rapport" in capsys.readouterr().out


def test_no_ok_pages_returns_1(monkeypatch, tmp_path: Path):
    pdf = tmp_path / "n.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(cli, "homr_available", lambda: True)

    from choir_rehearsal.pipeline.phase1 import PageResult, Phase1Result

    fake = Phase1Result(pdf_path=pdf, pages=[PageResult(page_index=0, ok=False, error="feil")])
    monkeypatch.setattr(cli, "process_pdf", lambda *a, **k: fake)

    rc = cli.main(["fase1", str(pdf)])
    assert rc == 1


def test_parse_pages():
    assert cli._parse_pages(None) is None
    assert cli._parse_pages("") is None
    assert cli._parse_pages("0,2,5") == [0, 2, 5]


def test_fase2_missing_dir_returns_2(capsys):
    rc = cli.main(["fase2", "finnes-ikke-mappe/"])
    assert rc == 2
    assert "Finner ikke mappe" in capsys.readouterr().err


def test_fase2_happy_path(tmp_path: Path, capsys):
    from tests.test_merge import page

    for i, xml in enumerate([page(4, 2), page(4, 2)]):
        (tmp_path / f"side-{i:03d}.musicxml").write_text(xml, encoding="utf-8")
    out = tmp_path / "merged.musicxml"
    rc = cli.main(["fase2", str(tmp_path), "--out", str(out)])
    assert rc == 0
    assert out.exists()
    assert "Sammenslått" in capsys.readouterr().out
