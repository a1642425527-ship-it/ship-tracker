#!/usr/bin/env python3
"""
QQ 机器人控制端 —— 通过 QQ 消息控制船舶跟踪系统
================================================================
支持命令（私聊或群里@机器人）：
  推送                     手动推送船舶排期到钉钉
  添加 船名 航次 [备注]      添加船舶
  删除 船名                 删除船舶
  备注 船名 内容             设置船舶备注
  列表                     查看船舶列表
  状态                     查看系统状态
  帮助                     显示命令说明
================================================================
运行: python qq_bot.py
"""

import os
import re
import sys
import asyncio
import subprocess

import botpy
from botpy.message import GroupMessage, C2CMessage

# ==========================================
# ⚙️ 配置区（换成你自己的机器人信息）
# ==========================================
APPID = "1905322972"
SECRET = "Ts43pNgjdLq8C1bv"

# 允许操作的 QQ 号（填你自己的 QQ，其他 QQ 发的命令忽略）
# 留空 = 允许所有 QQ 操作（有风险）
ALLOWED_USERS = []

WORK_DIR = os.path.dirname(os.path.abspath(__file__))


def run_script(*args):
    """调用 ship_tracker.py 并返回输出"""
    try:
        result = subprocess.run(
            [sys.executable, os.path.join(WORK_DIR, "ship_tracker.py"), *args],
            capture_output=True, text=True, timeout=180,
            cwd=WORK_DIR
        )
        out = (result.stdout or "") + (result.stderr or "")
        return out.strip() or "（无输出）"
    except subprocess.TimeoutExpired:
        return "⏱️ 命令执行超时"
    except Exception as e:
        return f"❌ 执行出错: {e}"


def parse_command(content):
    """解析 QQ 消息并返回回复内容"""
    # 去掉 @机器人 部分（群消息里机器人名会在内容里）
    content = re.sub(r"<@!?\d+>", "", content).strip()

    if not content:
        return "📖 发送 帮助 查看可用命令"

    # 推送
    if content in ("推送", "push", "强制推送"):
        return run_script("--push")

    # 添加: 添加 船名 航次 [备注]
    m = re.match(r"^(?:添加|新增|add)\s+(.+?)\s+(\S+)(?:\s+(.+))?$", content, re.I)
    if m:
        name, voyage = m.group(1).strip(), m.group(2).strip()
        remark = (m.group(3) or "").strip()
        if remark:
            return run_script("--add", name, voyage, remark)
        return run_script("--add", name, voyage)

    # 删除: 删除 船名
    m = re.match(r"^(?:删除|移除|删掉|remove|del)\s+(.+)$", content, re.I)
    if m:
        return run_script("--remove", m.group(1).strip())

    # 备注: 备注 船名 内容
    m = re.match(r"^(?:备注|remark)\s+(.+?)\s+(.+)$", content, re.I)
    if m:
        return run_script("--remark", m.group(1).strip(), m.group(2).strip())

    # 列表
    if content in ("列表", "船列表", "list", "船"):
        return run_script("--list")

    # 状态
    if content in ("状态", "status", "系统状态"):
        return run_script("--status")

    # 帮助
    if content in ("帮助", "help", "菜单", "?"):
        return (
            "📖 船舶跟踪机器人可用命令：\n\n"
            "📤 推送 —— 手动推送船期到钉钉\n"
            "➕ 添加 船名 航次 [备注] —— 添加船舶\n"
            "  例：添加 YM TOPMOST 025W 周超群\n"
            "➖ 删除 船名 —— 删除船舶\n"
            "📝 备注 船名 内容 —— 设置备注\n"
            "📋 列表 —— 查看所有船舶\n"
            "📊 状态 —— 查看系统状态\n"
            "❓ 帮助 —— 显示本菜单"
        )

    return "🤔 看不懂这条指令，发送 帮助 查看可用命令"


class ShipBot(botpy.Client):
    async def on_ready(self):
        print("✅ QQ 机器人已上线！")

    async def _handle(self, message, user_openid):
        # 权限检查
        if ALLOWED_USERS and user_openid not in ALLOWED_USERS:
            await message.reply(content="⛔ 你没有操作权限")
            return

        content = getattr(message, "content", "") or ""
        print(f"📩 收到消息: {content}")
        reply_text = parse_command(content)
        try:
            await message.reply(content=reply_text[:2000])
            print(f"📤 已回复: {reply_text[:80]}...")
        except Exception as e:
            print(f"⚠️ 回复失败: {e}")

    async def on_c2c_message_create(self, message: C2CMessage):
        await self._handle(message, getattr(message.author, "user_openid", ""))

    async def on_group_at_message_create(self, message: GroupMessage):
        await self._handle(message, getattr(message.author, "user_openid", ""))


if __name__ == "__main__":
    # public_messages 包含 群@消息 和 C2C私聊消息
    intents = botpy.Intents(public_messages=True)
    client = ShipBot(intents=intents)
    client.run(appid=APPID, secret=SECRET)
