# 前沿雷达（Frontier Radar）工作交接文档

> 面向对象：接手后续改动的 Cursor Agent / 其他 IDE / 其他平台同事。  
> 仓库：https://github.com/tomcat333/free  
> 服务根目录：`radar/`  
> 文档日期：按当前 `master`（已含 PR #2–#13）整理。

---

## 1. 一句话目标

做一个**常开的外部简报服务**：持续收集「AI/算法前沿」和「用户专业方向（X 射线表征 / 半导体量测）」资讯，自动打分分层，网页可下钻阅读；可选大模型解读；手机/平板/办公室电脑可通过 Tailscale 远程访问。

它**不是**单纯 RSS 阅读器，也**不是** Cursor 云端常驻机。

---

## 2. 要解决什么问题（背景与决策）

| 问题 | 结论 |
| --- | --- |
| Cursor Cloud Agent 能否当「永不关机主机」？ | **不能**。空闲会休眠/回收，不能当 24/7 服务主机。 |
| 要不要上 VPS？ | 用户**更倾向家里电脑常开**，不爱自己运维公网 VPS；代码仍希望能在本机 Cursor 里改。 |
| 实际部署方案 | **家里 Windows 电脑常开** + `start-all.bat` + Tailscale，手机/Surface/办公室浏览器访问。 |
| Token 成本 | 怕失控烧几千；可接受每月十几/几十元。因此默认 **按需生成**（`ENRICH_TOP_N=0`），并做「免费解读桥」。 |
| 办公室怎么用 | 办公室只装 **Tailscale 客户端**访问家里服务；**不要**两边各开一套雷达。 |

---

## 3. 当前做到哪一步（状态摘要）

### 已完成（代码已合入 `master`）

1. **核心服务**：FastAPI Web + 独立 Worker 采集循环（默认约 15 分钟一轮）
2. **双轨采集**
   - AI/算法：arXiv（CS/ML 类）、GitHub、Hugging Face、HN、Reddit、实验室博客
   - 专业·X射线：arXiv CD-SAXS/HRXRD 等检索；厂商理学（Rigaku）、科磊（KLA）
3. **打分分层**：breakthrough / notable / signal
4. **阅读层**：首页三栏简报 → 条目页深度介绍 / 全过程 / 来源 / 远程试跑任务包
5. **省 token**：默认不自动 LLM；条目页「免费解读」（复制提示词 → Kimi/豆包/DeepSeek 网页；论文可拉 Semantic Scholar TLDR）
6. **Windows 双击启动**一整套 bat
7. **家里常开 + Tailscale 远程访问**文档与辅助脚本（防火墙、诊断、开机自启、防休眠）
8. **Docker Compose** 备选（若以后改上 VPS 可用）
9. **测试**：`radar/tests/` 下有采集解析、打分、API、免费桥、专业轨等用例

### 已落地但不等于「用户本机一定在跑」

- 代码在 GitHub `master` 已齐。
- **运行态**取决于用户家里电脑是否已：`git pull` → `start-all.bat` → Tailscale Connected → 防火墙放行。
- 接手方若改代码：改完开 PR → 用户合并 → 本机 `git pull` 并重启两个黑窗口。

### 明确未做 / 可后续做

- 推送通知（邮件 / 微信 / Telegram）
- 登录鉴权（当前依赖 Tailscale 网络隔离；服务本身无账号体系）
- 更多厂商（如 Bruker、Malvern 等）与会议/期刊源
- 专业轨更细的主题过滤（理学新闻里仍含部分非半导体条目）
- 自动把 PDF 塞进豆包/Kimi（登录墙与网页协议不可靠，**不建议**作为默认方案）
- 本地大模型默认部署（用户环境不现实；仅 `.env` 留了 Ollama 示例）
- `docker-compose.yml` 里 worker 的 `ENRICH_TOP_N` 默认仍是 `12`，与 `.env.example` 的 `0` 不一致——改 Docker 部署时要注意

---

## 4. 架构速览

```
┌──────────────── Windows 家里电脑（常开） ────────────────┐
│  start-web.bat   →  uvicorn :8787  (0.0.0.0)            │
│  start-worker.bat→  python -m app.worker  (周期采集)     │
│  SQLite          →  radar/data/frontier.db               │
│  .env            →  DeepSeek 等可选 API Key              │
└───────────────────────┬──────────────────────────────────┘
                        │ Tailscale (100.x.y.z:8787)
        ┌───────────────┼────────────────┐
   手机浏览器      Surface/办公室      本机 127.0.0.1:8787
```

**进程职责**

| 进程 | 作用 |
| --- | --- |
| Web (`app.main:app`) | 简报页、条目页、手动「立刻扫一轮」、按需 LLM、免费桥、任务包 |
| Worker (`app.worker`) | 定时 `collect_all` → `ingest` →（可选）`enrich` |

**数据**

- SQLite：`DATA_DIR/frontier.db`（默认 `radar/data/frontier.db`）
- 表：`items` / `dispatches` / `collector_runs`（见 `app/models.py`）

---

## 5. 目录地图（接手先看这些）

```
radar/
  README.md              # 使用说明（启动、配置、Docker）
  HOME-PHONE.md          # 家里常开 + Tailscale + 排障
  HANDOVER.md            # 本交接文档
  .env.example           # 环境变量模板（复制为 .env）
  docker-compose.yml     # VPS/容器备选
  requirements.txt
  *.bat                  # Windows 双击脚本（见下表）
  app/
    main.py              # FastAPI 路由与页面
    worker.py            # 采集循环
    config.py            # pydantic-settings，固定从 radar/.env 读
    models.py / db.py
    free_bridge.py       # 免费解读桥
    dispatch.py          # 远程试跑任务包
    collectors/
      run.py             # 注册所有采集器
      arxiv.py           # AI 类 arXiv
      pro_xray.py        # 专业 arXiv + Rigaku/KLA
      github.py / huggingface.py / hn.py / reddit.py / blogs.py
    pipeline/
      score.py / ingest.py / briefing.py / enrich.py
    templates/ / static/
  tests/
```

### Windows 脚本一览

| 脚本 | 用途 |
| --- | --- |
| `setup-once.bat` | 首次建 venv、装依赖 |
| `start-all.bat` | 启动 web + worker，并打开本机浏览器 |
| `start-web.bat` / `start-worker.bat` | 单独启动 |
| `stop-all.bat` | 结束相关进程 |
| `check-env.bat` | 检查是否读到 API Key |
| `fix-local.bat` | 清理本地 git 冲突残留后对齐 remote |
| `keep-awake-ac.bat` | 接通电源时尽量不休眠 |
| `install-autostart.bat` / `remove-autostart.bat` | 登录自启 / 取消 |
| `allow-firewall-8787.bat` | 放行 8787 给 Tailscale 客户端 |
| `show-access-url.bat` | 打印本机 Tailscale 访问地址 |
| `diagnose-tailscale.bat` | 监听/防火墙/IP 诊断 |

---

## 6. 双轨内容说明

### 轨 A：AI / 算法前沿

- 来源：`arxiv`、`github`、`huggingface`、`hn`、`blogs`、`reddit`
- 条目 `kind`：`paper` / `repo` / `model` / `news` / `discussion`
- 打分：来源权重 + 热度（stars/points 等）+ 通用 AI 关键词 + 时效

### 轨 B：专业·X射线（用户本业）

用户专业关注：

- **CD-SAXS**、关键尺寸、X 射线小角散射
- 半导体相关 **XRD / HRXRD**
- X 射线表征、半导体器件量测
- 厂商：**日本理学（Rigaku）**、**美国科磊（KLA）**

实现：

- 采集器：`app/collectors/pro_xray.py`
  - `collect_arxiv_pro` → `source=arxiv_pro`，`kind=pro_paper`
  - `collect_vendors` → `source=vendor`，`kind=vendor`（Rigaku HTML + KLA RSS）
- 首页过滤：`/?track=xray`、`/?kind=pro_paper`、`/?kind=vendor`
- 打分：`score.py` 增加 CD-SAXS / HRXRD / GISAXS / semiconductor metrology / Rigaku / KLA 等权重

扩源时优先改 `pro_xray.py` 的查询串与厂商列表，并补 `tests/test_pro_xray.py`。

---

## 7. 配置要点

文件：`radar/.env`（由 `.env.example` 复制；**不要**存成 `.env.txt`）。

| 变量 | 现状建议 |
| --- | --- |
| `PORT` | `8787`（避开本机其他 8080 服务） |
| `HOST` | `0.0.0.0`（Tailscale 外机才能进） |
| `ENRICH_TOP_N` | **`0`**（按需；省 token） |
| `OPENAI_*` | 可选；用户常用 DeepSeek 兼容接口 |
| `COLLECT_INTERVAL_SECONDS` | 默认 `900` |
| `DISPATCH_WEBHOOK_URL` | 可选远程试跑回调 |

`config.py` 会从 `radar/.env`（及少数候选路径）加载，**不依赖**你从哪个 cwd 启动——但 bat 仍建议在 `radar/` 下双击。

---

## 8. 已合并 PR 时间线（#2–#13）

| PR | 内容 |
| --- | --- |
| #2 | 前沿雷达初版：采集 / 打分 / Web / Worker / Docker |
| #3 | Windows BAT 启动器 |
| #4 | LLM 默认按需，避免每条烧 token |
| #5 | 修复 `.env` 加载，DeepSeek 等可真正接通 |
| #6 | BAT 编码修复 + `fix-local.bat` 清理冲突残留 |
| #7 | 澄清「材料不足」文案与按需 LLM UX |
| #8 | 免费解读桥（网页粘贴 + Semantic Scholar TLDR） |
| #9 | 家里常开 + Tailscale 手机访问指南与脚本 |
| #10 | 防火墙放行：任意 Tailscale 客户端访问 8787 |
| #11 | `diagnose-tailscale.bat` + 文档排障（ping 分层） |
| #12 | 文档强调：翻墙/系统代理会劫持 `100.x` 导致「连着但打不开」 |
| #13 | 专业·X射线采集轨（CD-SAXS/HRXRD + Rigaku/KLA） |

（#1 是仓库里无关的 TIFF 堆栈脚本，不属于雷达服务。）

---

## 9. 已知排障经验（交接必读）

1. **合并冲突残留**：worker 报 `SyntaxError: <<<<<<< HEAD` → `fix-local.bat` 或 `git reset --hard origin/master`。
2. **Surface 连不上 Tailscale 雷达**：优先关 **Clash / V2Ray / 系统代理**；`100.64` 与 `100.112` 都属合法 Tailscale 网段。
3. **只监听 127.0.0.1**：外机进不来 → 用最新 `start-web.bat`（应绑 `0.0.0.0`），跑 `diagnose-tailscale.bat`。
4. **首页显示未接通 API Key**：`.env` 路径/文件名错误，或改完没重启两个黑窗口；用 `check-env.bat`。
5. **Defender 报 Chrome 缓存 Trojan**：与雷达无关；不要为雷达去解除隔离。
6. **办公室**：只当客户端，不要再部署第二套雷达。

详细步骤见 `HOME-PHONE.md`。

---

## 10. 本地开发 / 测试 / 发布流程

```bash
cd radar
python3 -m venv .venv && source .venv/bin/activate   # Windows 用 setup-once.bat
pip install -r requirements.txt
PYTHONPATH=. pytest -q
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8787
# 另开终端
PYTHONPATH=. python -m app.worker
```

发布约定（本仓库 Cloud Agent 习惯）：

1. 从 `master` 拉功能分支：`cursor/<name>-1d32`
2. 改代码 + 测通 → commit → push
3. 用 PR 合入 `master`（不要直接推 master）
4. 用户本机：`git pull origin master`，重启 `start-all.bat`

---

## 11. 给接手方的建议起点

按目标选切入点：

| 若要… | 先看 |
| --- | --- |
| 加采集源 / 厂商 | `app/collectors/pro_xray.py`、`run.py`、`score.py`、对应 tests |
| 改打分策略 | `app/pipeline/score.py` |
| 改网页/过滤 | `templates/index.html`、`item.html`、`main.py`、`briefing.py` |
| 改 LLM / 省 token | `pipeline/enrich.py`、`free_bridge.py`、`.env.example` |
| 改远程访问/运维体验 | `HOME-PHONE.md`、各类 `*.bat` |
| 改 Docker 部署 | `Dockerfile`、`docker-compose.yml`（注意 `ENRICH_TOP_N`） |

---

## 12. 用户偏好备忘（避免走回头路）

- 中文沟通与中文 UI 文案
- 家里常开优先于 VPS
- 控制 token；默认按需；优先免费网页解读路径
- 不把 Cursor 云会话当常驻主机
- 专业内容要「算法前沿 + X 射线表征/厂商」双轨，而不是只做 AI 资讯
- 前端若大改落地页，遵循用户前端设计规则；**雷达现有简报页是工具型列表**，小改时保持现有视觉语言即可

---

## 13. 快速验收清单（接手后自测）

1. `cd radar && PYTHONPATH=. pytest -q` 通过  
2. `start-all.bat`（或命令行）后打开 `http://127.0.0.1:8787`  
3. 点「立刻扫一轮」，库存数字增加  
4. 过滤器「专业·X射线」能看到 `pro_paper` / `vendor`  
5. 条目页能看到「免费解读」；配置 Key 后「生成深度介绍」可用  
6. （远程）`diagnose-tailscale.bat` + 他机 `http://100.x.y.z:8787`  

---

**交接完成标志**：接手方能在本机跑通采集+网页，理解双轨与 Tailscale 部署，并能独立开 PR 改采集/打分/UI/运维脚本。
