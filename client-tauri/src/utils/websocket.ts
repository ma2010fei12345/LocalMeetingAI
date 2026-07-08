let ws: WebSocket | null = null;

// 连接本地后端服务，仅127.0.0.1内网，禁止公网地址
export function connectServer() {
  if (ws && ws.readyState === WebSocket.OPEN) return;
  ws = new WebSocket("ws://127.0.0.1:8000/ws/meeting");

  ws.onopen = () => {
    console.log("已连接本地会议后端服务");
  };

  ws.onmessage = (event) => {
    // 接收后端推送：转写文本、AI实时观点
    const data = JSON.parse(event.data);
    console.log("后端推送数据：", data);
  };

  ws.onclose = () => {
    console.log("服务断开，3秒后重连");
    setTimeout(() => connectServer(), 3000);
  };

  ws.onerror = (err) => {
    console.error("WebSocket连接异常", err);
  };
}

// 发送音频分片、操作指令给后端
export function sendMsg(msg: object) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify(msg));
}