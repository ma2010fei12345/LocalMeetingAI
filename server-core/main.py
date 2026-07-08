from fastapi import FastAPI
import uvicorn
from meeting-stream.ws_server import router as ws_router

app = FastAPI(title="LocalMeetingAI Backend Core")
# 注册实时会议websocket路由
app.include_router(ws_router)

@app.get("/health")
def health_check():
    """服务健康检测接口"""
    return {"status": "running", "mode": "local-offline"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)