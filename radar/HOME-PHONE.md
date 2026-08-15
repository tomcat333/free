# 家里电脑常开 + 手机随时看（Tailscale）

目标：电脑放在家里一直跑雷达，手机浏览器随时打开简报。  
不折腾 VPS；配置仍可在本机 Cursor 里改。

## 0. 先保证本机能用

```bat
cd radar
setup-once.bat
start-all.bat
```

本机浏览器打开：http://127.0.0.1:8787

## 1. 别让电脑自己睡着

1. 双击 `keep-awake-ac.bat`（接通电源时尽量不休眠）
2. 再手动确认一次：  
   **设置 → 系统 → 电源 → 屏幕和睡眠**  
   接通电源时：屏幕/睡眠都调成 **从不**
3. 笔记本建议：**合盖不要睡眠**（电源选项里改“合上盖子”为不采取行动），或干脆别合盖、接电常开

## 2. 开机自动启动雷达

登录 Windows 后自动跑 `start-all.bat`：

1. 双击 `install-autostart.bat`
2. 注销或重启试一次，应自动弹出两个黑窗口
3. 不想要了：双击 `remove-autostart.bat`

## 3. 让手机 / 平板 / 办公室电脑都能连（Tailscale）

服务**不是只给手机用**。同一 Tailscale 账号下的手机、Surface、办公室电脑都可以访问。  
网页监听 `0.0.0.0:8787`（不只本机浏览器）。

### 3.1 家里这台（跑雷达的电脑）

1. 打开 https://tailscale.com/download 安装 Windows 版  
2. 登录，托盘显示 Connected  
3. 双击一次 **`allow-firewall-8787.bat`**（允许防火墙放行 8787，需点“是”）  
4. 确认 `start-all.bat` 在跑  
5. 双击 **`show-access-url.bat`**，记下本机 `100.x.y.z`

也可在 PowerShell：

```bat
tailscale ip -4
```

### 3.2 手机 / Surface / 办公室电脑

1. 安装 Tailscale，**同一个账号**登录并 Connected  
2. 浏览器打开（把 IP 换成家里那台的）：

```text
http://100.x.y.z:8787
```

注意：

- 在 Surface 上不要用 `http://127.0.0.1:8787`（那是 Surface 自己，不是家里电脑）  
- 必须用**家里跑雷达那台**的 Tailscale IP  

### 3.3 连不上时（先看 IP，再 ping）

**`100.64` 和 `100.112` 开头都正常**，都在 Tailscale 网段 `100.64.0.0/10` 里，前缀不同本身不会导致连不上。

在**家里电脑**双击 `diagnose-tailscale.bat`，看：

1. 是否有 `0.0.0.0:8787` 在 LISTENING（只有 `127.0.0.1:8787` 则外机进不来，需重启最新 `start-all.bat`）  
2. 防火墙规则是否存在  
3. 本机 Tailscale IP 是多少  

在 **Surface** 上打开 PowerShell，对**家里电脑**的 IP 测试：

```bat
ping -n 4 100.x.y.z
```

- **ping 都不通**：是 Tailscale/账号/网络问题，还没轮到雷达  
  - 确认两边同一账号、都 Connected  
  - 打开 https://login.tailscale.com/admin/machines 看两台是否在线、是否被禁用  
- **ping 通但浏览器打不开**：再开 `http://100.x.y.z:8787`，并在家里重跑 `allow-firewall-8787.bat` / `diagnose-tailscale.bat` 后重启 `start-all.bat`  
- Surface 上 **不要**用 `127.0.0.1`

### 3.4 日常怎么用

| 场景 | 做法 |
|------|------|
| 在家电脑前 | http://127.0.0.1:8787 |
| 手机 / Surface / 办公室 | Tailscale 连上后打开 http://100.x.y.z:8787 |
| 停止服务 | 关黑窗口，或 `stop-all.bat` |
| 改代码 | 仍在本机 Cursor 里改 |

## 4. 安全提醒

- Tailscale 比“把 8787 直接暴露到公网”安全得多
- 不要随意做端口映射把雷达挂到公网
- API Key 只放在 `radar\.env`，不要发到聊天里

## 5. 和“内网穿透”的关系

对你这个需求，**Tailscale 就是更省心的远程回家方式**（组网），通常不必再单独折腾 frp/花生壳。  
以后若还要远程桌面、远程让本机跑任务，也可以走同一套 Tailscale。
