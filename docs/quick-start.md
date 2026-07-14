# LocalMeetingAI 单机快速启动

## 1. 启动后端

Windows:

```powershell
scripts\start-single.bat
```

macOS / Linux:

```bash
bash scripts/start-single.sh
```

后端默认监听 `http://127.0.0.1:8000`，健康检查：

```bash
curl http://127.0.0.1:8000/health
```

## 2. 启动 Tauri 客户端

```bash
cd client-tauri
npm install
npm run tauri dev
```

## 3. 自测流程

1. 在客户端创建或选择项目。
2. 上传 `txt/md/pdf/docx` 文档，后端会本地 AES 加密保存，并按项目切片入库。
3. 点击“连接后端”。
4. 点击“开始收音”，或在底部输入测试会议片段：

```text
这个方案有延期风险，预算也不确定，大家对负责人还有分歧。
```

5. 观察实时字幕、项目检索结果和 AI 悬浮观点。

## 4. 模型接入

默认安装 `server-core/requirements.txt`，可跑通项目、文档、SQLite、加密、WebSocket 和规则触发。重模型依赖放在：

```bash
server-core/requirements-models.txt
```

按机器环境单独安装：

```bash
cd server-core
pip install -r requirements-models.txt
```

可选环境变量：

```bash
set LOCALMEETINGAI_WHISPER_MODEL=base
set LOCALMEETINGAI_USE_CHROMA=1
set LOCALMEETINGAI_VLLM_ENDPOINT=http://127.0.0.1:8001/v1/chat/completions
```

未配置模型时，系统使用本地降级适配器输出可验证结果，不需要外网。

## 5. Docker Compose

```bash
cd server-core/deploy-scripts
docker compose up --build
```
