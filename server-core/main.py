from fastapi import FastAPI
import uvicorn

from core.api import router as api_router
from core.config import ensure_data_dirs
from core.db import init_db
from meeting_stream.ws_server import router as ws_router

app = FastAPI(title="LocalMeetingAI Backend Core")
ensure_data_dirs()
init_db()
app.include_router(api_router)
app.include_router(ws_router)


@app.get("/health")
def health_check():
    return {"status": "running", "mode": "local-offline", "network_required": False}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
