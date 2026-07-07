# 单机快速启动指南
## 环境依赖
1. Git
2. Docker Desktop
3. NVIDIA显卡驱动（可选，GPU加速推理）

## 启动步骤
1. 克隆仓库
git clone https://github.com/xxx/LocalMeetingAI.git
cd LocalMeetingAI

2. 一键启动后端服务
cd scripts
bash start-single.sh # Mac/Linux
start-single.bat # Windows

3. 启动Tauri客户端
cd client-tauri
npm install
npm run tauri dev

## 模型下载
离线模型自动拉取脚本：models-download/download-models.py