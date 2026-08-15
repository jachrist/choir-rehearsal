"""API-tester for web-verktøyet (Fase 4). Hoppes over hvis fastapi ikke er installert."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from choir_rehearsal.ui.server import create_app  # noqa: E402

SCORE = (
    '<score-partwise><part-list>'
    '<score-part id="P1"><part-name>Soprano</part-name></score-part>'
    '<score-part id="P2"><part-name>Alto</part-name></score-part>'
    "</part-list>"
    '<part id="P1"><measure number="1">'
    '<note><pitch><step>C</step><octave>5</octave></pitch><duration>4</duration></note>'
    '<note><pitch><step>D</step><octave>5</octave></pitch><duration>4</duration></note>'
    '<note><pitch><step>E</step><octave>5</octave></pitch><duration>4</duration></note>'
    "</measure></part>"
    '<part id="P2"><measure number="1">'
    '<note><pitch><step>A</step><octave>4</octave></pitch><duration>4</duration></note>'
    "</measure></part></score-partwise>"
)


@pytest.fixture
def client(tmp_path: Path):
    app = create_app()
    return TestClient(app), tmp_path


def _load(client, tmp_path) -> None:
    f = tmp_path / "score.musicxml"
    f.write_text(SCORE, encoding="utf-8")
    r = client.post("/api/load", json={"path": str(f)})
    assert r.status_code == 200


def test_health(client):
    c, _ = client
    assert c.get("/health").text == "ok"


def test_index_served(client):
    c, _ = client
    r = c.get("/")
    assert r.status_code == 200
    assert "Sangtekstretting" in r.text


def test_state_before_load_is_400(client):
    c, _ = client
    assert c.get("/api/state").status_code == 400


def test_load_and_state(client):
    c, tmp = client
    _load(c, tmp)
    data = c.get("/api/state").json()
    assert [v["name"] for v in data["voices"]] == ["Soprano", "Alto"]
    assert data["voices"][0]["singable_notes"] == 3


def test_load_missing_file_404(client):
    c, _ = client
    assert c.post("/api/load", json={"path": "/finnes/ikke.musicxml"}).status_code == 404


def test_edit_set_text_and_shift(client):
    c, tmp = client
    _load(c, tmp)
    r = c.post("/api/edit", json={"op": "set_text", "part_id": "P1", "text": "glo-ri-a"})
    assert r.status_code == 200
    syl = r.json()["voices"][0]["syllables"]
    assert syl == ["glo", "ri", "a"]

    r = c.post("/api/edit", json={"op": "shift", "part_id": "P1", "offset": 1})
    # bare 3 noter: skyv +1 gir plass til 2 stavelser
    assert r.json()["voices"][0]["syllables"][0] == ""


def test_edit_clear(client):
    c, tmp = client
    _load(c, tmp)
    c.post("/api/edit", json={"op": "set_text", "part_id": "P1", "text": "a b c"})
    r = c.post("/api/edit", json={"op": "clear", "part_id": "P1"})
    assert r.json()["voices"][0]["lyric_count"] == 0


def test_edit_unknown_part_400(client):
    c, tmp = client
    _load(c, tmp)
    r = c.post("/api/edit", json={"op": "set_text", "part_id": "P9", "text": "x"})
    assert r.status_code == 400


def test_upload_musicxml(client):
    c, _ = client
    r = c.post(
        "/api/upload",
        files={"file": ("score.musicxml", SCORE.encode("utf-8"), "application/xml")},
    )
    assert r.status_code == 200
    assert [v["name"] for v in r.json()["voices"]] == ["Soprano", "Alto"]


def test_upload_invalid_400(client):
    c, _ = client
    r = c.post(
        "/api/upload",
        files={"file": ("bad.musicxml", b"<html></html>", "application/xml")},
    )
    assert r.status_code == 400


def test_demo_loads(client):
    c, _ = client
    r = c.post("/api/demo")
    assert r.status_code == 200
    names = [v["name"] for v in r.json()["voices"]]
    assert names == ["Soprano", "Alto", "Tenor", "Bass"]
    # demoen har sangtekst på sopranen
    assert r.json()["voices"][0]["lyric_count"] > 0


def test_upload_mxl_zip(client):
    c, _ = client
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("score.musicxml", SCORE)
    r = c.post(
        "/api/upload",
        files={"file": ("score.mxl", buf.getvalue(), "application/vnd.recordare.musicxml")},
    )
    assert r.status_code == 200
    assert len(r.json()["voices"]) == 2


def test_export_returns_musicxml(client):
    c, tmp = client
    _load(c, tmp)
    c.post("/api/edit", json={"op": "set_text", "part_id": "P1", "text": "syng nå"})
    r = c.get("/api/export")
    assert r.status_code == 200
    assert b"<lyric" in r.content
    assert "attachment" in r.headers["content-disposition"]
