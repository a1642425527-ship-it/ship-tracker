FROM python:3.11-slim

WORKDIR /app

# 安装依赖
RUN pip install --no-cache-dir qq-botpy requests openpyxl

# 复制项目文件
COPY ship_tracker.py qq_bot.py requirements.txt ./
COPY start_qq_bot.sh ./
RUN chmod +x start_qq_bot.sh

# 复制敏感配置文件（本地存在才复制）
COPY GITHUB_PAT.txt .smtp.txt token.txt .webhook.txt .vessels.json .last_vessel_state.json ./ 2>/dev/null || true

# 启动 QQ 机器人
CMD ["python3", "-u", "qq_bot.py"]
