# 前沿雷达（Frontier Radar）

持续收集 AI / 算法前沿资讯，自动估重要性，做成可以往下钻的简报。

这不是 RSS 阅读器。RSS 只是来源之一。真正在做的是：

1. **不停采集**：arXiv、GitHub 新仓库、Hugging Face 日报/热门模型、Hacker News、Reddit、实验室博客
2. **先打分再露面**：来源权重 + 热度 + 关键词 + 时效，分成「重点突破 / 值得看 / 雷达扫描」
3. **三层阅读**：扫一眼 → 深度介绍 → 全过程讲解
4. **来源可追溯**，觉得好的条目可以 **生成远程试跑任务包**（克隆命令 + 给编码代理的提示词，也可 POST 到你的机器）

> Cursor 云端会话会在空闲后回收，**不能**当永不关机的主机。把本目录用 Docker 丢到 VPS / 云主机上，`worker` 才会 24/7 跑。

## 本地看一眼

默认端口是 **8787**（避开常见的 8080）。

### Windows：双击启动（推荐）

在资源管理器中打开本机的 `free\radar` 文件夹：

1. **第一次**：双击 `setup-once.bat`（装依赖，只需一次）
2. **配置大模型（可选）**：把 `.env.example` 复制为 `.env` 并填入 Key；可用 DeepSeek 等。可先双击 `check-env.bat` 确认是否读到
3. **以后每次**：双击 `start-all.bat`  
   - 会弹出两个黑窗口（网页 + 采集）  
   - 并打开浏览器 http://127.0.0.1:8787  
4. **要停止**：关掉那两个黑窗口，或双击 `stop-all.bat`

### 家里常开 + 手机随时看

完整步骤见 **[HOME-PHONE.md](HOME-PHONE.md)**（防休眠、开机自启、Tailscale）。

短路顺序：

1. `keep-awake-ac.bat` → 电源里确认接通电源不睡眠  
2. `install-autostart.bat` → 登录 Windows 自动启动雷达  
3. 电脑/手机/平板都装 Tailscale，同一账号；家里电脑再运行一次 `allow-firewall-8787.bat`  
4. 其他设备浏览器打开 `http://<家里电脑的Tailscale-IP>:8787`（不要用 127.0.0.1）  
5. 不确定地址时，在家里电脑双击 `show-access-url.bat`

如果 worker 报 `SyntaxError: <<<<<<< HEAD`，说明本地文件还留着合并冲突标记。在仓库根目录执行：

```bat
git checkout master
git pull origin master
```

或双击 `radar\fix-local.bat`，然后再 `start-all.bat`。

也可以单独双击 `start-web.bat` / `start-worker.bat`。

首页「深度解读」若显示「未接通 API Key」，说明 `.env` 没被读到或没重启；显示「已接通」后再点条目里的「生成深度介绍」。

### 命令行方式

```bash
cd radar
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --port 8787
```

另开一个终端：

```bash
cd radar && source .venv/bin/activate
PYTHONPATH=. python -m app.worker
```

打开 http://127.0.0.1:8787

## 一台机器上一直跑（推荐）

在任意 Linux 主机：

```bash
cd radar
cp .env.example .env   # 按需填密钥
docker compose up -d --build
```

- `web`：简报页面，端口 **8787**
- `worker`：按 `COLLECT_INTERVAL_SECONDS`（默认 15 分钟）扫一轮，崩溃会自动重启

只要这台 VPS 不关机，采集就不会停。数据在 Docker volume `radar-data` 里。

单容器也可以（Web 进程里顺带跑采集）：

```bash
docker build -t frontier-radar .
docker run -d --restart unless-stopped -p 8787:8787 \
  -e EMBED_WORKER=1 -e DATA_DIR=/data \
  -v radar-data:/data frontier-radar
```

## 选配

| 环境变量 | 作用 |
| --- | --- |
| `OPENAI_API_KEY` + `OPENAI_BASE_URL` + `OPENAI_MODEL` | 可选。用 API 写介绍会耗 token。也可用本地 Ollama：`BASE_URL=http://127.0.0.1:11434/v1`，`API_KEY=ollama` |
| `ENRICH_TOP_N` | 每轮自动精加工条数，**默认 0=按需** |
| `GITHUB_TOKEN` | 提高 GitHub 搜索限额 |
| `DISPATCH_WEBHOOK_URL` | 点「远程试跑」时把任务包 POST 到你的 GPU 机 / n8n / 自建 agent |
| `COLLECT_INTERVAL_SECONDS` | 采集间隔，默认 900 |
| `PORT` | Web 端口，默认 8787 |

不配大模型也能用：采集、打分、列表、来源、任务包都在。  
**省 token 推荐路径**：条目页「免费解读」→ 复制提示词 → 打开 Kimi / 豆包 / DeepSeek 网页版粘贴；论文还可拉 Semantic Scholar 免费 TLDR。  
只有你点「用 API 生成…」才会消耗已配置接口的 token。

## 阅读层

1. 首页三栏简报，按分数分层
2. 点进条目：优先「免费解读」，需要时再 API 深度介绍 / 全过程
3. 「生成并派发任务包」：给远程机器跑最小复现

## 测试

```bash
cd radar
PYTHONPATH=. pytest -q
```
