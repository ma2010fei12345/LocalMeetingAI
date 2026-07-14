import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.asr import WhisperTranscriber
from core.db import db, utc_now
from core.llm import LocalLLM
from core.speaker import SpeakerDiarizer
from core.triggers import build_prompt, detect_triggers
from core.vector_store import ProjectVectorStore

router = APIRouter()
active_connections: list[WebSocket] = []
transcriber = WhisperTranscriber()
diarizer = SpeakerDiarizer()
vector_store = ProjectVectorStore()
llm = LocalLLM()


@router.websocket("/ws/meeting")
async def meeting_websocket(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    project_id = 1
    try:
        await websocket.send_text(json.dumps({"type": "connected", "offline": True}, ensure_ascii=False))
        while True:
            data = await websocket.receive()
            if "text" in data and data["text"]:
                payload = json.loads(data["text"])
                project_id = int(payload.get("project_id") or project_id)
                if payload.get("type") == "manual_transcript":
                    await handle_transcript(project_id, payload.get("text", ""), payload.get("speaker", "Speaker 1"), 1.0)
                continue
            if "bytes" in data and data["bytes"]:
                audio_bytes = data["bytes"]
                result = transcriber.transcribe_chunk(audio_bytes)
                await send(websocket, {"type": "audio_received", "size": len(audio_bytes)})
                if result:
                    speaker = diarizer.identify(audio_bytes)
                    await handle_transcript(project_id, result.text, speaker, result.confidence)
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)


async def handle_transcript(project_id: int, text: str, speaker: str, confidence: float) -> None:
    text = text.strip()
    if not text:
        return
    with db() as conn:
        conn.execute(
            "insert into transcript_events(project_id, speaker, text, confidence, created_at) values (?, ?, ?, ?, ?)",
            (project_id, speaker, text, confidence, utc_now()),
        )
        project = conn.execute("select * from projects where id = ?", (project_id,)).fetchone()
    await broadcast({"type": "transcript", "project_id": project_id, "speaker": speaker, "text": text, "confidence": confidence})

    triggers = detect_triggers(text)
    if not triggers:
        return
    project_name = project["name"] if project else f"Project {project_id}"
    contexts = vector_store.search(project_id, text, limit=4)
    for trigger_type in triggers:
        prompt = build_prompt(project_name, text, contexts, trigger_type)
        parts: list[str] = []
        async for token in llm.stream_opinion(prompt):
            parts.append(token)
            await broadcast(
                {
                    "type": "ai_delta",
                    "project_id": project_id,
                    "trigger_type": trigger_type,
                    "content": token,
                    "sources": contexts,
                }
            )
        content = "\n".join(parts)
        with db() as conn:
            conn.execute(
                "insert into ai_events(project_id, trigger_type, content, sources, created_at) values (?, ?, ?, ?, ?)",
                (project_id, trigger_type, content, json.dumps(contexts, ensure_ascii=False), utc_now()),
            )
        await broadcast(
            {
                "type": "ai_complete",
                "project_id": project_id,
                "trigger_type": trigger_type,
                "content": content,
                "sources": contexts,
            }
        )


async def send(conn: WebSocket, message: dict) -> None:
    await conn.send_text(json.dumps(message, ensure_ascii=False))


async def broadcast(message: dict) -> None:
    stale: list[WebSocket] = []
    for conn in active_connections:
        try:
            await send(conn, message)
        except RuntimeError:
            stale.append(conn)
    for conn in stale:
        if conn in active_connections:
            active_connections.remove(conn)
