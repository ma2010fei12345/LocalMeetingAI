import json
from fastapi import WebSocket, WebSocketDisconnect, APIRouter

router = APIRouter()
# 存储所有在线客户端连接
active_connections: list[WebSocket] = []

@router.websocket("/ws/meeting")
async def meeting_websocket(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # 接收客户端：音频二进制 / 控制指令
            data = await websocket.receive()
            if "text" in data:
                text_msg = json.loads(data["text"])
                print("收到客户端指令：", text_msg)
            if "bytes" in data:
                audio_bytes = data["bytes"]
                # 音频分片送入ASR处理队列（后续开发完善）
                await broadcast({"type": "audio_received", "size": len(audio_bytes)})
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# 广播消息给所有客户端（推送字幕、AI观点）
async def broadcast(message: dict):
    for conn in active_connections:
        await conn.send_text(json.dumps(message))