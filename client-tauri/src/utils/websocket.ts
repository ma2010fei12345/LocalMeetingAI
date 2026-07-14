let ws: WebSocket | null = null;

export function connectServer(onMessage?: (data: unknown) => void) {
  if (ws && ws.readyState === WebSocket.OPEN) return ws;
  ws = new WebSocket("ws://127.0.0.1:8000/ws/meeting");
  ws.onmessage = (event) => onMessage?.(JSON.parse(event.data));
  ws.onclose = () => {
    setTimeout(() => connectServer(onMessage), 3000);
  };
  return ws;
}

export function sendMsg(msg: object | ArrayBuffer) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  if (msg instanceof ArrayBuffer) {
    ws.send(msg);
    return;
  }
  ws.send(JSON.stringify(msg));
}
