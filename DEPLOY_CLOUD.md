# ☁️ 云端部署指南（QQ 机器人 24 小时在线）

把 QQ 机器人部署到云服务器后，你的电脑关机/离线也能在 QQ 上操作船舶系统。

## 一、买服务器

任选一家（推荐按顺序）：

| 平台 | 价格 | 说明 |
|------|------|------|
| 腾讯云轻量应用服务器 | ~¥30-60/月 | 国内快、稳定，选 Ubuntu 22.04 |
| 阿里云轻量应用服务器 | ~¥30-60/月 | 同上 |
| Oracle 甲骨文免费服务器 | ¥0 | 免费永久 ARM 机，注册繁琐可能被拒 |

**配置要求极低**：1核1G 足够，选 Ubuntu 系统即可。

## 二、部署（3 条命令）

登录服务器（SSH）后执行：

```bash
# 1. 安装 Docker
curl -fsSL https://get.docker.com | sh

# 2. 克隆项目
git clone https://github.com/a1642425527-ship-it/ship-tracker.git
cd ship-tracker

# 3. 放入敏感配置文件（本地的这些文件，用 scp 传上来）
#    GITHUB_PAT.txt、.smtp.txt、token.txt、.webhook.txt、.vessels.json

# 4. 启动（自动开机运行 + 崩溃自动重启）
docker compose up -d --build
```

## 三、本地传配置到服务器（在你自己电脑上执行）

```bash
# Windows PowerShell 里：
scp C:\Users\a1642\ship-tracker\GITHUB_PAT.txt  ubuntu@服务器IP:~/ship-tracker/
scp C:\Users\a1642\ship-tracker\.smtp.txt      ubuntu@服务器IP:~/ship-tracker/
scp C:\Users\a1642\ship-tracker\token.txt      ubuntu@服务器IP:~/ship-tracker/
scp C:\Users\a1642\ship-tracker\.webhook.txt   ubuntu@服务器IP:~/ship-tracker/
scp C:\Users\a1642\ship-tracker\.vessels.json  ubuntu@服务器IP:~/ship-tracker/
```

## 四、验证

```bash
docker logs -f qq-ship-bot
# 看到 "机器人「查传奇」启动成功" 就 OK 了
```

然后 QQ 上发 `帮助` 测试。

## 五、常用命令

```bash
docker logs -f qq-ship-bot      # 看日志
docker restart qq-ship-bot      # 重启机器人
docker compose down             # 停止
docker compose up -d --build    # 更新代码后重启
```

## 说明

- `restart: always` 保证崩溃自动重启、服务器重启自动启动
- 机器人内部调用 `ship_tracker.py --push` 时通过 GitHub API 触发 GitHub Actions 查询（用 GITHUB_PAT.txt），所以即使服务器上没有 NPEDI Token 也能正常推送
- 本地电脑的机器人可以停掉了（`bash ~/ship-tracker/stop_qq_bot.sh`），或留着备用
