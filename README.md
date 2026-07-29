# 🚢 船舶动态跟踪系统

自动查询 NPEDI 船舶排期数据，推送钉钉通知，生成 Excel 报表。

## 📋 目录

- [功能](#功能)
- [运行模式](#运行模式)
- [部署到 GitHub Actions](#部署到-github-actions)
- [本地使用](#本地使用)
- [修改链接](#修改链接)

---

## 功能

- 定时查询指定船舶的排期信息（ETA/ETD/ATA/ATD/进箱时间/截单截关等）
- 通过钉钉机器人推送 Markdown 格式通知
- 自动生成 Excel 报表（支持增量追加）
- 支持 GitHub Actions 定时调度和本地守护进程双模式

## 运行模式

| 模式 | 命令 | 说明 |
|------|------|------|
| 单次查询 | `python ship_tracker.py` | 查一次就退出（GitHub Actions 默认模式） |
| 守护进程 | `python ship_tracker.py --daemon` | 每2小时自动查，按回车键手动触发 |
| 抓取 Token | `python ship_tracker.py --grab-token` | 打开浏览器登录 NPEDI，抓取 Token |

## 部署到 GitHub Actions

### 第 1 步：在 GitHub 创建仓库

```bash
# 在 GitHub 网页上新建一个空仓库（不要勾选 README/.gitignore/LICENSE）
# 仓库名建议: ship-tracker

# 然后在本地执行：
cd /path/to/ship-tracker
git init
git add .
git commit -m "init: 船舶动态跟踪系统"
git remote add origin https://github.com/你的用户名/ship-tracker.git
git branch -M main
git push -u origin main
```

### 第 2 步：配置 GitHub Secrets

1. 进入仓库 Settings → Secrets and variables → Actions
2. 点击 **New repository secret**
3. Name: `NPEDI_TOKEN`
4. Value: 你的 NPEDI Token（用下面"本地使用"的方法获取）
5. 点击 **Add secret**

### 第 3 步：验证

- 进入仓库 Actions 页面
- 点击左侧 **🚢 船舶动态跟踪**
- 点击 **Run workflow** → **Run workflow**（手动触发一次测试）

### 定时调度

默认每 2 小时执行一次（cron: `0 */2 * * *`），如需修改请编辑：

`.github/workflows/ship-track.yml` 中的 `schedule` 字段。

## 本地使用

### 安装依赖

```bash
pip install requests openpyxl
```

### 抓取 Token（首次必须）

```bash
python ship_tracker.py --grab-token
```

这会打开浏览器跳到 NPEDI 登录页面，登录后自动拦截到 Token 并保存到 `token.txt`。

### 手动推送 Token 到 GitHub

抓取 Token 后，脚本会自动 `git add && git commit && git push` 将 token.txt 推送到仓库，
触发 GitHub Actions 重新运行（workflow 配置了 `push` 触发）。

如果自动推送失败，请手动执行：

```bash
git add token.txt
git commit -m "update NPEDI token"
git push
```

### 单次查询测试

```bash
python ship_tracker.py
```

### 本地守护进程（每隔 2 小时自动跑）

```bash
python ship_tracker.py --daemon
```

随时按 **回车键 (Enter)** 强制立即查询。

## 修改链接

所有需要修改的 URL 都在 `ship_tracker.py` 顶部 **"可修改链接区"**：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_URL` | `https://www.npedi.com/onesite-api/vessel/plan/selectContainerDynamicPlan` | 船舶排期查询 API |
| `TOKEN_PAGE_URL` | `https://www.npedi.com/onesite/vessel/plan` | 浏览器抓 Token 时打开的页面 |
| `DINGTALK_WEBHOOK` | 你的钉钉机器人地址 | 钉钉通知推送地址（**保持不变**） |

要修改船舶列表，编辑 `VESSELS_TO_QUERY` 数组：

```python
VESSELS_TO_QUERY = [
    {"name": "AL MURAYKH", "voyage": "622W"},
    {"name": "另一艘船名", "voyage": "航次号"},
]
```

---

> 如有问题，提 Issue 或联系脚本维护者。
