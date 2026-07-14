from fastapi import APIRouter, File, HTTPException, UploadFile

from .db import db, row_to_dict, utc_now
from .documents import chunk_text, extract_text
from .security import encrypted_project_path, encrypt_bytes
from .vector_store import ProjectVectorStore

router = APIRouter(prefix="/api")
vector_store = ProjectVectorStore()


@router.get("/projects")
def list_projects():
    with db() as conn:
        rows = conn.execute("select * from projects order by id desc").fetchall()
    return [row_to_dict(row) for row in rows]


@router.post("/projects")
def create_project(payload: dict):
    name = str(payload.get("name", "")).strip()
    description = str(payload.get("description", "")).strip()
    if not name:
        raise HTTPException(status_code=400, detail="项目名称不能为空")
    with db() as conn:
        cursor = conn.execute(
            "insert into projects(name, description, created_at) values (?, ?, ?)",
            (name, description, utc_now()),
        )
    return {"id": cursor.lastrowid, "name": name, "description": description}


@router.get("/projects/{project_id}/documents")
def list_documents(project_id: int):
    with db() as conn:
        rows = conn.execute(
            "select * from documents where project_id = ? order by id desc",
            (project_id,),
        ).fetchall()
    return [row_to_dict(row) for row in rows]


@router.post("/projects/{project_id}/documents")
async def upload_document(project_id: int, file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件为空")
    filename = file.filename or "document.txt"
    encrypted_path = encrypted_project_path(project_id, filename)
    encrypted_path.write_bytes(encrypt_bytes(content))
    text = extract_text(filename, content)
    chunks = chunk_text(text)
    with db() as conn:
        project = conn.execute("select id from projects where id = ?", (project_id,)).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        cursor = conn.execute(
            """
            insert into documents(project_id, filename, encrypted_path, size_bytes, chunk_count, created_at)
            values (?, ?, ?, ?, ?, ?)
            """,
            (project_id, filename, str(encrypted_path), len(content), len(chunks), utc_now()),
        )
        document_id = cursor.lastrowid
    vector_store.add_chunks(project_id, document_id, filename, chunks)
    return {"id": document_id, "filename": filename, "chunk_count": len(chunks)}


@router.post("/projects/{project_id}/search")
def search_project(project_id: int, payload: dict):
    query = str(payload.get("query", "")).strip()
    return vector_store.search(project_id, query)


@router.get("/projects/{project_id}/events")
def list_events(project_id: int):
    with db() as conn:
        transcripts = conn.execute(
            "select * from transcript_events where project_id = ? order by id desc limit 100",
            (project_id,),
        ).fetchall()
        ai_events = conn.execute(
            "select * from ai_events where project_id = ? order by id desc limit 100",
            (project_id,),
        ).fetchall()
    return {
        "transcripts": [row_to_dict(row) for row in transcripts],
        "ai_events": [row_to_dict(row) for row in ai_events],
    }
