#!/usr/bin/env bash
# QQ 机器人启动脚本（独立于 Hermes 会话运行）
# 用法: bash ~/ship-tracker/start_qq_bot.sh
set -e

BOT_DIR="$HOME/ship-tracker"
LOG="$BOT_DIR/qq_bot.log"
PIDFILE="$BOT_DIR/.qq_bot.pid"

# 已在运行则跳过
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "✅ QQ机器人已在运行 (PID $(cat $PIDFILE))"
    exit 0
fi

cd "$BOT_DIR"
nohup python3 -u qq_bot.py >> "$LOG" 2>&1 &
echo $! > "$PIDFILE"
echo "🚀 QQ机器人已启动 (PID $(cat $PIDFILE))"
echo "📄 日志: $LOG"

# 等待连接检查
sleep 8
if kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "✅ 进程存活，等待 QQ 网关连接..."
else
    echo "❌ 进程异常退出，查看日志: $LOG"
    tail -5 "$LOG"
fi
