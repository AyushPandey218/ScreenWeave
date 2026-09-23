"""Bounded, stateless reconstruction API for the experimental workspace."""

import base64
import io
import os
import tempfile
import threading
import time
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from . import diagnostics
from starlette.concurrency import run_in_threadpool

from .baseline import MAX_BYTES
from .layout import Layout

job_lock = threading.Lock()

app = FastAPI(title="ScreenWeave API", version="0.1.0")
origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def measure_requests(request: Request, call_next):
    if request.url.path not in {"/reconstruct", "/render", "/extract-text"} or request.method != "POST":
        return await call_next(request)
    start, status = time.monotonic(), 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        diagnostics.record(status, time.monotonic() - start)


@app.get("/", include_in_schema=False)
def dashboard_redirect():
    return RedirectResponse("/dashboard")


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    return HTMLResponse((Path(__file__).parent / "dashboard.html").read_text(encoding="utf-8-sig"))


@app.get("/status")
def service_status():
    return diagnostics.snapshot(job_lock.locked())


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "screenweave-api"}


@app.get("/capabilities")
def capabilities() -> dict:
    return {
        "stage": "experimental-reconstruction",
        "reconstruction_available": True,
        "available_exports": ["html-css", "react-typescript", "react-tailwind"],
        "max_upload_bytes": MAX_BYTES,
    }


def process_image(payload: bytes) -> dict:
    from reconstruct import reconstruct
    return package_layout(reconstruct(payload))


def package_layout(layout: dict) -> dict:
    from reconstruct import export
    from react_export import write_react_project

    document, css = export(layout)
    html_zip = io.BytesIO()
    with ZipFile(html_zip, "w", ZIP_DEFLATED) as archive:
        archive.writestr("index.html", document)
        archive.writestr("styles.css", css)
    with tempfile.TemporaryDirectory(prefix="screenweave-") as temporary:
        folder = Path(temporary) / "react"
        write_react_project(layout, css, folder)
        react_zip = (Path(temporary) / "react.zip").read_bytes()
        write_react_project(layout, css, Path(temporary) / "tailwind", tailwind=True)
        tailwind_zip = (Path(temporary) / "tailwind.zip").read_bytes()
    return {
        "layout": layout,
        "html": document,
        "css": css,
        "exports": {
            "html": base64.b64encode(html_zip.getvalue()).decode("ascii"),
            "react": base64.b64encode(react_zip).decode("ascii"),
            "tailwind": base64.b64encode(tailwind_zip).decode("ascii"),
        },
    }


@app.post('/render')
async def render_layout(request: Request) -> dict:
    from pydantic import ValidationError
    payload = bytearray()
    async for chunk in request.stream():
        if len(payload) + len(chunk) > MAX_BYTES:
            raise HTTPException(413, 'Layout is too large.')
        payload.extend(chunk)
    try:
        layout = Layout.model_validate_json(bytes(payload)).model_dump(exclude_none=True)
    except ValidationError as exc:
        raise HTTPException(422, 'Invalid layout properties. Check sizes, colors, and element IDs.') from exc
    return await run_in_threadpool(package_layout, layout)


@app.post("/reconstruct")
async def reconstruct_image(request: Request) -> dict:
    if not job_lock.acquire(blocking=False):
        raise HTTPException(429, "Another screenshot is being processed. Try again shortly.")
    try:
        payload = bytearray()
        async for chunk in request.stream():
            if len(payload) + len(chunk) > MAX_BYTES:
                raise HTTPException(413, "Please upload an image smaller than 5 MiB.")
            payload.extend(chunk)
        try:
            return await run_in_threadpool(process_image, bytes(payload))
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
    finally:
        job_lock.release()


@app.post('/extract-text')
async def extract_image_text(request: Request):
    from .text_extraction import extract_text
    if not job_lock.acquire(blocking=False):
        raise HTTPException(429, 'Another screenshot is being processed. Try again shortly.')
    try:
        payload=bytearray()
        async for chunk in request.stream():
            if len(payload)+len(chunk)>MAX_BYTES:
                raise HTTPException(413, 'Please upload an image smaller than 5 MiB.')
            payload.extend(chunk)
        try:
            layout=await run_in_threadpool(extract_text,bytes(payload))
            return await run_in_threadpool(package_layout,layout)
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc
    finally:
        job_lock.release()
