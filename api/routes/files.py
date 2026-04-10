from __future__ import annotations

import mimetypes
import tempfile
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from api.deps import get_file_store, get_open_terminal_api_key, get_open_terminal_base_url
from api.services.file_store import FileStore

router = APIRouter(prefix="/api/files", tags=["files"])


class ContentUpdateRequest(BaseModel):
    content: str


class ImportFromSandboxRequest(BaseModel):
    sandbox_id: str
    path: str
    filename: str | None = None
    content_type: str | None = None


@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    store: FileStore = Depends(get_file_store),
):
    suffix = Path(file.filename or "upload.bin").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(await file.read())
        temp_path = Path(temp.name)

    try:
        record = store.save_upload(
            filename=file.filename or "upload.bin",
            content_type=file.content_type,
            source_path=temp_path,
        )
        return record
    finally:
        temp_path.unlink(missing_ok=True)


@router.get("/")
async def list_files(store: FileStore = Depends(get_file_store)):
    return {"data": store.list_files()}


@router.get("/all")
async def list_all_files(store: FileStore = Depends(get_file_store)):
    return store.list_files()


@router.get("/search")
async def search_files(
    filename: str = Query("*"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1),
    store: FileStore = Depends(get_file_store),
):
    needle = filename.strip("*").lower()
    items = store.list_files()
    if needle:
        items = [item for item in items if needle in item.get("filename", "").lower()]
    return items[skip : skip + limit]


@router.post("/upload/dir")
async def upload_dir():
    return {"status": True}


@router.post("/import-from-sandbox")
async def import_from_sandbox(
    payload: ImportFromSandboxRequest,
    store: FileStore = Depends(get_file_store),
    base_url: str = Depends(get_open_terminal_base_url),
    api_key: str = Depends(get_open_terminal_api_key),
):
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(
            f"{base_url}/files/view",
            params={"path": payload.path},
            headers=headers,
        )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Sandbox file not found")
        response.raise_for_status()
        filename = payload.filename or Path(payload.path).name or "artifact.bin"
        content_type = payload.content_type or response.headers.get("content-type")
        return store.import_bytes(
            filename=filename,
            content=response.content,
            content_type=content_type,
        )


@router.get("/{file_id}")
async def get_file(file_id: str, store: FileStore = Depends(get_file_store)):
    record = store.get_file(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    return record


@router.get("/{file_id}/content")
async def get_file_content(file_id: str, store: FileStore = Depends(get_file_store)):
    record = store.get_file(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    media_type = record.get("meta", {}).get("content_type") or mimetypes.guess_type(record["filename"])[0]
    return FileResponse(path=record["path"], filename=record["filename"], media_type=media_type)


@router.get("/{file_id}/content/html")
async def get_file_content_html(file_id: str, store: FileStore = Depends(get_file_store)):
    return await get_file_content(file_id, store)


@router.get("/{file_id}/process/status")
async def get_process_status(file_id: str):
    async def event_stream():
        yield 'data: {"ok": true}\n\n'
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{file_id}/data/content/update")
async def update_file_content(
    file_id: str,
    payload: ContentUpdateRequest,
    store: FileStore = Depends(get_file_store),
):
    record = store.update_content(file_id, payload.content)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    return record


@router.delete("/{file_id}")
async def delete_file(file_id: str, store: FileStore = Depends(get_file_store)):
    if not store.delete_file(file_id):
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": True}
