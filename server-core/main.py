from fastapi import FastAPI
import uvicorn

app = FastAPI(title="LocalMeetingAI Backend Core")

@app.get("/health")
def health_check():
    """服务健康检测接口"""
    return {"status": "running", "mode": "local-offline"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)