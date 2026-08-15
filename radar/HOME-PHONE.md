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

## 3. 让手机能连上（Tailscale）

网页服务已监听 `0.0.0.0:8787`（不只本机），手机可通过 Tailscale 访问。

### 3.1 电脑

1. 打开 https://tailscale.com/download 安装 Windows 版
2. 登录（Google / Microsoft 等均可）
3. 托盘图标显示 Connected
4. 右键托盘 → 看本机的 Tailscale IP（一般是 `100.x.y.z`）

也可在 PowerShell 里看：

```bat
tailscale ip -4
```

### 3.2 手机

1. 应用商店安装 **Tailscale**
2. 用**同一个账号**登录
3. 打开开关，等到 Connected
4. 浏览器访问：

```text
http://100.x.y.z:8787
```

把 `100.x.y.z` 换成电脑那台的 Tailscale IP。

### 3.3 连不上时

- 电脑上 `start-all.bat` 是否还在跑（两个黑窗口）
- 手机 Tailscale 是否 Connected、是否同一账号
- 电脑防火墙若拦截，可允许 Python/`8787`（Tailscale 虚拟网卡一般较省事）
- 先在电脑浏览器试：`http://127.0.0.1:8787` 是否正常

## 4. 日常怎么用

| 场景 | 做法 |
|------|------|
| 在家电脑前 | http://127.0.0.1:8787 |
| 出门用手机 | Tailscale 连上后打开 http://100.x.y.z:8787 |
| 停止服务 | 关黑窗口，或 `stop-all.bat` |
| 改代码 | 仍在本机 Cursor 里改，我可以继续帮你 |

## 5. 安全提醒

- Tailscale 比“把 8787 直接暴露到公网”安全得多
- 不要随意做端口映射把雷达挂到公网
- API Key 只放在 `radar\.env`，不要发到聊天里

## 6. 和“内网穿透”的关系

对你这个需求，**Tailscale 就是更省心的远程回家方式**（组网），通常不必再单独折腾 frp/花生壳。  
以后若还要远程桌面、远程让本机跑任务，也可以走同一套 Tailscale。
