#!/usr/bin/env bash
# QQ 机器人停止脚本
set -e

BOT_DIR="$HOME/ship-tracker"
PIDFILE="$BOT_DIR/.qq_bot.pid"

if [ -f "$PIDFILE" ]; then
    pid=$(cat "$PIDFILE")
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" && echo "🛑 已停止 QQ机器人 (PID $pid)"
    fi
    rm -f "$PIDFILE"
else
    echo "ℹ️ 机器人未在运行"
fi
