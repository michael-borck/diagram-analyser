"""FastAPI service — diagram-analyser."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from lens_contract import add_contract_routes, add_cors, upload_tempfile

from .analyser import DiagramAnalyser
from .exceptions import DiagramAnalyserError
from .manifest import MANIFEST
from .schemas import DiagramAnalysis

_lens = DiagramAnalyser()

app = FastAPI(
    title="diagram-analyser",
    description="Structural analysis of mermaid / PlantUML / Graphviz / drawio diagrams (plus image diagrams via optional vision)",
    version=MANIFEST["version"],
    docs_url="/docs",
    redoc_url="/redoc",
)

add_contract_routes(app, MANIFEST)
add_cors(app, env_prefix="DIAGRAM_ANALYSER")


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "service": "diagram-analyser",
        "version": MANIFEST["version"],
        "status": "running",
        "endpoints": {"health": "/health", "manifest": "/manifest", "analyse": "/analyse"},
    }


@app.post("/analyse", response_model=DiagramAnalysis)
async def analyse(
    file: UploadFile = File(..., description="Diagram file: .mmd/.puml/.dot/.drawio or .png/.jpg (with [vision])"),
) -> DiagramAnalysis:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=422, detail="Empty file")
    with upload_tempfile(content, file.filename) as tmp_path:
        try:
            return _lens.analyse(tmp_path)
        except DiagramAnalyserError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
