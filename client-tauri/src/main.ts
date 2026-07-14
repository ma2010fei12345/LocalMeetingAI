type Project = {
  id: number;
  name: string;
  description: string;
};

type DocumentRow = {
  id: number;
  filename: string;
  chunk_count: number;
  size_bytes: number;
};

type FeedItem = {
  type: "transcript" | "ai" | "system";
  title: string;
  body: string;
  meta?: string;
};

const API = "http://127.0.0.1:8000";
let ws: WebSocket | null = null;
let selectedProjectId = 1;
let mediaRecorder: MediaRecorder | null = null;
let feed: FeedItem[] = [];

const app = document.querySelector<HTMLDivElement>("#app")!;

app.innerHTML = `
  <aside class="sidebar">
    <div class="brand">
      <span class="brand-mark">LM</span>
      <div>
        <strong>LocalMeetingAI</strong>
        <small>单机离线会议助手</small>
      </div>
    </div>
    <section class="panel compact">
      <div class="panel-title">项目</div>
      <div id="project-list" class="project-list"></div>
      <form id="project-form" class="inline-form">
        <input id="project-name" placeholder="新项目名称" />
        <button title="创建项目" type="submit">+</button>
      </form>
    </section>
    <section class="panel compact">
      <div class="panel-title">本地文档</div>
      <input id="doc-file" type="file" />
      <button id="upload-doc">上传并向量化</button>
      <div id="doc-list" class="doc-list"></div>
    </section>
  </aside>
  <main class="workspace">
    <header class="topbar">
      <div>
        <h1 id="project-title">会议工作台</h1>
        <p>实时收音、项目检索、风险和分歧自动提示</p>
      </div>
      <div class="actions">
        <button id="connect">连接后端</button>
        <button id="record">开始收音</button>
      </div>
    </header>
    <section class="meeting-grid">
      <div class="panel live-panel">
        <div class="panel-title">实时字幕</div>
        <div id="feed" class="feed"></div>
        <form id="manual-form" class="manual-form">
          <input id="manual-text" placeholder="输入测试会议片段，例如：这个方案有延期风险，预算也不确定" />
          <button type="submit">发送</button>
        </form>
      </div>
      <div class="panel insight-panel">
        <div class="panel-title">项目检索</div>
        <form id="search-form" class="search-form">
          <input id="search-query" placeholder="检索项目资料" />
          <button type="submit">检索</button>
        </form>
        <div id="search-results" class="search-results"></div>
      </div>
    </section>
    <section id="float-window" class="float-window">
      <strong>AI 悬浮观点</strong>
      <span id="float-content">等待会议触发分歧、信息缺失或风险。</span>
    </section>
  </main>
`;

function el<T extends HTMLElement>(selector: string): T {
  return document.querySelector<T>(selector)!;
}

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    headers: init?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

async function loadProjects() {
  const projects = await api<Project[]>("/api/projects");
  if (projects.length && !projects.some((project) => project.id === selectedProjectId)) {
    selectedProjectId = projects[0].id;
  }
  el("#project-list").innerHTML = projects
    .map(
      (project) => `
        <button class="project-item ${project.id === selectedProjectId ? "active" : ""}" data-id="${project.id}">
          <span>${project.name}</span>
          <small>${project.description || "本地隔离知识库"}</small>
        </button>
      `,
    )
    .join("");
  const current = projects.find((project) => project.id === selectedProjectId);
  el("#project-title").textContent = current ? current.name : "会议工作台";
  document.querySelectorAll<HTMLButtonElement>(".project-item").forEach((button) => {
    button.addEventListener("click", () => {
      selectedProjectId = Number(button.dataset.id);
      sendControl();
      loadProjects();
      loadDocuments();
    });
  });
}

async function loadDocuments() {
  const docs = await api<DocumentRow[]>(`/api/projects/${selectedProjectId}/documents`);
  el("#doc-list").innerHTML = docs
    .map((doc) => `<div class="doc-row"><span>${doc.filename}</span><small>${doc.chunk_count} 片</small></div>`)
    .join("");
}

function connect() {
  if (ws?.readyState === WebSocket.OPEN) return;
  ws = new WebSocket("ws://127.0.0.1:8000/ws/meeting");
  ws.onopen = () => {
    pushFeed({ type: "system", title: "系统", body: "已连接本地后端" });
    sendControl();
  };
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "transcript") {
      pushFeed({ type: "transcript", title: message.speaker, body: message.text, meta: `置信度 ${message.confidence}` });
    }
    if (message.type === "ai_delta" || message.type === "ai_complete") {
      pushFeed({ type: "ai", title: `AI · ${message.trigger_type}`, body: message.content });
      el("#float-content").textContent = message.content;
    }
  };
  ws.onclose = () => pushFeed({ type: "system", title: "系统", body: "后端连接已断开" });
}

function sendControl() {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "select_project", project_id: selectedProjectId }));
  }
}

function pushFeed(item: FeedItem) {
  feed = [item, ...feed].slice(0, 80);
  el("#feed").innerHTML = feed
    .map(
      (entry) => `
        <article class="feed-item ${entry.type}">
          <div><strong>${entry.title}</strong>${entry.meta ? `<small>${entry.meta}</small>` : ""}</div>
          <p>${entry.body}</p>
        </article>
      `,
    )
    .join("");
}

async function toggleRecording() {
  connect();
  if (mediaRecorder?.state === "recording") {
    mediaRecorder.stop();
    el<HTMLButtonElement>("#record").textContent = "开始收音";
    return;
  }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
  mediaRecorder.ondataavailable = async (event) => {
    if (event.data.size && ws?.readyState === WebSocket.OPEN) {
      ws.send(await event.data.arrayBuffer());
    }
  };
  mediaRecorder.start(1000);
  el<HTMLButtonElement>("#record").textContent = "停止收音";
}

el("#connect").addEventListener("click", connect);
el("#record").addEventListener("click", () => {
  toggleRecording().catch((error) => pushFeed({ type: "system", title: "麦克风", body: error.message }));
});

el<HTMLFormElement>("#project-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = el<HTMLInputElement>("#project-name");
  if (!input.value.trim()) return;
  const project = await api<Project>("/api/projects", { method: "POST", body: JSON.stringify({ name: input.value }) });
  selectedProjectId = project.id;
  input.value = "";
  await loadProjects();
  await loadDocuments();
});

el("#upload-doc").addEventListener("click", async () => {
  const file = el<HTMLInputElement>("#doc-file").files?.[0];
  if (!file) return;
  const body = new FormData();
  body.append("file", file);
  await api(`/api/projects/${selectedProjectId}/documents`, { method: "POST", body });
  await loadDocuments();
});

el<HTMLFormElement>("#manual-form").addEventListener("submit", (event) => {
  event.preventDefault();
  connect();
  const input = el<HTMLInputElement>("#manual-text");
  if (input.value.trim() && ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "manual_transcript", project_id: selectedProjectId, text: input.value, speaker: "Manual" }));
    input.value = "";
  }
});

el<HTMLFormElement>("#search-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = el<HTMLInputElement>("#search-query").value;
  const results = await api<Array<{ filename: string; text: string; score: number }>>(`/api/projects/${selectedProjectId}/search`, {
    method: "POST",
    body: JSON.stringify({ query }),
  });
  el("#search-results").innerHTML = results
    .map((item) => `<article><strong>${item.filename}</strong><small>${item.score.toFixed(2)}</small><p>${item.text}</p></article>`)
    .join("");
});

loadProjects().then(loadDocuments).catch((error) => {
  pushFeed({ type: "system", title: "后端", body: `请先启动本地服务：${error.message}` });
});
