"""Lokal web-app for å rette sangtekst-plassering (Fase 4).

Hybrid arbeidsflyt: noter/struktur rettes i MuseScore, sangteksten her. Serveren
gjengir MusicXML med Verovio (server-side) og tilbyr redigering som kun endrer
``<lyric>`` – resten av partituret bevares.

Kjør lokalt:
    choir-omr ui path/til/partitur.musicxml
    # åpne http://127.0.0.1:8000

Alt kjører lokalt; ingenting sendes ut av maskinen.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from lxml import etree
from pydantic import BaseModel

from choir_rehearsal import musicxml
from choir_rehearsal.ui import editor

_STATIC = Path(__file__).parent / "static"


class LoadRequest(BaseModel):
    path: str


class EditRequest(BaseModel):
    op: str  # set_text | shift | clear | set_note
    part_id: str
    text: str | None = None
    offset: int | None = None
    index: int | None = None
    number: int = 1


def _render_svg(root: etree._Element) -> str:
    """Gjengi hele partituret til (én eller flere) Verovio-SVG-er."""
    import verovio

    tk = verovio.toolkit()
    tk.setOptions(
        {"pageWidth": 2100, "pageHeight": 2970, "scale": 40, "adjustPageHeight": False}
    )
    tk.loadData(etree.tostring(root).decode("utf-8"))
    pages = tk.getPageCount() or 1
    return "\n".join(tk.renderToSVG(p) for p in range(1, pages + 1))


def _bytes_to_musicxml(content: bytes, filename: str = "") -> etree._Element:
    """Parse MusicXML fra bytes. Håndterer komprimert .mxl (zip)."""
    if filename.lower().endswith(".mxl") or content[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            inner = None
            # META-INF/container.xml peker på hovedfila; ellers ta første *.xml.
            try:
                container = zf.read("META-INF/container.xml")
                croot = etree.fromstring(container)
                rf = croot.find(".//{*}rootfile")
                if rf is not None:
                    inner = rf.get("full-path")
            except KeyError:
                inner = None
            if inner is None:
                names = [
                    n for n in zf.namelist()
                    if n.lower().endswith((".xml", ".musicxml")) and not n.startswith("META-INF")
                ]
                if not names:
                    raise HTTPException(status_code=400, detail="Fant ingen MusicXML i .mxl-fila")
                inner = names[0]
            content = zf.read(inner)
    try:
        return musicxml.parse(content)
    except musicxml.MusicXMLValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _state(root: etree._Element) -> dict:
    voices = editor.list_voices(root)
    return {
        "voices": [
            {
                "part_id": v.part_id,
                "name": v.name,
                "singable_notes": v.singable_notes,
                "lyric_count": v.lyric_count,
                "syllables": editor.get_syllables(root, v.part_id),
            }
            for v in voices
        ]
    }


def create_app() -> FastAPI:
    app = FastAPI(title="choir-rehearsal – sangtekstretting")
    app.state.root = None
    app.state.source = None

    def _root_or_404() -> etree._Element:
        if app.state.root is None:
            raise HTTPException(status_code=400, detail="Ingen fil lastet")
        return app.state.root

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return (_STATIC / "index.html").read_text(encoding="utf-8")

    @app.post("/api/load")
    def load(req: LoadRequest) -> dict:
        path = Path(req.path)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Finner ikke fil: {path}")
        try:
            app.state.root = musicxml.parse(path)
        except musicxml.MusicXMLValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        app.state.source = path
        return {"loaded": str(path), **_state(app.state.root)}

    @app.post("/api/upload")
    async def upload(file: UploadFile = File(...)) -> dict:
        content = await file.read()
        app.state.root = _bytes_to_musicxml(content, file.filename or "")
        app.state.source = Path(file.filename or "opplastet.musicxml")
        return {"loaded": file.filename, **_state(app.state.root)}

    @app.post("/api/demo")
    def demo() -> dict:
        content = (_STATIC / "demo.musicxml").read_bytes()
        app.state.root = _bytes_to_musicxml(content, "demo.musicxml")
        app.state.source = Path("demo.musicxml")
        return {"loaded": "demo.musicxml", **_state(app.state.root)}

    @app.get("/api/state")
    def state() -> dict:
        return _state(_root_or_404())

    @app.get("/api/svg", response_class=HTMLResponse)
    def svg() -> str:
        return _render_svg(_root_or_404())

    @app.post("/api/edit")
    def edit(req: EditRequest) -> dict:
        root = _root_or_404()
        try:
            if req.op == "set_text":
                editor.set_text(root, req.part_id, req.text or "", number=req.number)
            elif req.op == "shift":
                editor.shift_lyrics(root, req.part_id, req.offset or 0, number=req.number)
            elif req.op == "clear":
                editor.clear_lyrics(root, req.part_id, number=req.number)
            elif req.op == "set_note":
                editor.set_syllable_on_note(
                    root, req.part_id, req.index or 0, req.text or "", number=req.number
                )
            else:
                raise HTTPException(status_code=400, detail=f"Ukjent operasjon: {req.op}")
        except (KeyError, IndexError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _state(root)

    @app.get("/api/export")
    def export() -> Response:
        root = _root_or_404()
        xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)
        name = (app.state.source.stem if app.state.source else "partitur") + "_tekst.musicxml"
        return Response(
            content=xml,
            media_type="application/vnd.recordare.musicxml+xml",
            headers={"Content-Disposition": f'attachment; filename="{name}"'},
        )

    @app.get("/health", response_class=PlainTextResponse)
    def health() -> str:
        return "ok"

    return app


def serve(path: str | None = None, host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start web-serveren, ev. med en fil forhåndslastet."""
    import uvicorn

    app = create_app()
    if path:
        p = Path(path)
        if p.exists():
            app.state.root = musicxml.parse(p)
            app.state.source = p
    uvicorn.run(app, host=host, port=port)
