# -*- coding: utf-8 -*-
"""
腾讯云函数 - QQ机器人中转（替代Cloudflare Worker，国内可访问）
===============================================================
功能：
  1. 接收 QQ 开放平台 Webhook 回调验证 (GET?ticket=xxx -> {"ticket":"xxx"})
  2. 接收 QQ 事件推送 (POST)，解析命令，触发 GitHub Actions
  3. 回复"收到"给 QQ 用户

部署：
  - 腾讯云 → 云函数 SCF → 新建函数（Python 3.9+，事件函数）
  - 粘贴本代码，环境变量填 GITHUB_PAT / QQ_APPID / QQ_SECRET
  - 创建 API 网关触发器（默认响应集成关闭），获取公网 URL
  - 把 URL 填到 QQ 开放平台回调地址

依赖：requests（腾讯云函数默认已内置）
"""
import os
import json
import time
import hashlib
import hmac
import random

import requests

GITHUB_REPO = "a1642425527-ship-it/ship-tracker"

# ---------------- 命令解析 ----------------

import re

_VOYAGE_RE = re.compile(r"^[A-Za-z0-9]{1,12}$")


def _find_voyage(tokens):
    """从右往左找航次 token（纯字母数字，长度<=12，如 025W / GJ629W / 0MEOFW1MA）"""
    for i in range(len(tokens) - 1, -1, -1):
        if _VOYAGE_RE.match(tokens[i]):
            return i, tokens[i]
    return None, None


def parse_command(content):
    content = (content or "").replace("<@!?\\d+>", "").strip()

    if content in ("帮助", "help", "菜单", "?"):
        return {"help": True, "text": (
            "📖 船舶跟踪机器人可用命令：\n\n"
            "📤 推送 —— 手动推送船期到钉钉\n"
            "➕ 添加 船名 航次 [备注] —— 添加船舶\n"
            "  例：添加 YM TOPMOST 025W 周超群\n"
            "➖ 删除 船名 —— 删除船舶\n"
            "📝 备注 船名 内容 —— 设置备注\n"
            "📋 列表 —— 查看所有船舶\n"
            "📊 状态 —— 查看系统状态\n"
            "❓ 帮助 —— 显示本菜单"
        )}

    if content in ("推送", "push", "强制推送"):
        return {"args": ["--push"]}
    if content in ("列表", "船列表", "list", "船"):
        return {"args": ["--list"]}
    if content in ("状态", "status", "系统状态"):
        return {"args": ["--status"]}

    # 添加: 添加 船名 航次 [备注]
    m = re.match(r"^(?:添加|新增|add)\s+(.+)$", content, re.I)
    if m:
        rest = m.group(1).strip()
        tokens = rest.split()
        idx, voyage = _find_voyage(tokens)
        if idx is not None:
            name = " ".join(tokens[:idx])
            remark = " ".join(tokens[idx + 1:])
            args = ["--add", name, voyage]
            if remark:
                args.append(remark)
            return {"args": args}
        return {"args": ["--add", rest]}

    # 删除: 删除 船名
    m = re.match(r"^(?:删除|移除|删掉|remove|del)\s+(.+)$", content, re.I)
    if m:
        return {"args": ["--remove", m.group(1).strip()]}

    # 备注: 备注 船名 内容（最后一段为备注，前面全部是船名——避免船名词被误判为航次）
    m = re.match(r"^(?:备注|remark)\s+(.+)$", content, re.I)
    if m:
        rest = m.group(1).strip()
        tokens = rest.split()
        if len(tokens) >= 2:
            name = " ".join(tokens[:-1])
            remark = tokens[-1]
        else:
            name = rest
            remark = ""
        if remark:
            return {"args": ["--remark", name, remark]}
        return {"args": ["--remark", name, ""]}

    return {"unknown": True}

# ---------------- QQ 消息发送 ----------------

def send_qq_msg(openid, msg_type, group_openid, text):
    appid = os.environ.get("QQ_APPID", "")
    secret = os.environ.get("QQ_SECRET", "")
    if not appid or not secret:
        return
    try:
        r = requests.post(
            "https://bots.qq.com/app/getAppAccessToken",
            json={"appId": appid, "clientSecret": secret}, timeout=10
        )
        token = r.json().get("access_token")
        if not token:
            return
        payload = {
            "content": [{"type": "text", "data": text[:1500]}],
            "msg_type": 0,
            "msg_seq": random.randint(0, 999999)
        }
        headers = {"Authorization": f"QQBot {token}", "Content-Type": "application/json"}
        if msg_type == "group" and group_openid:
            url = f"https://api.sgroup.qq.com/v2/groups/{group_openid}/messages"
        else:
            url = f"https://api.sgroup.qq.com/v2/users/{openid}/messages"
        requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception:
        pass

# ---------------- 触发 GitHub Actions ----------------

def trigger_github(args, openid, msg_type, group_openid):
    pat = os.environ.get("GITHUB_PAT", "")
    if not pat:
        return
    try:
        requests.post(
            f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/ship-track.yml/dispatches",
            headers={
                "Authorization": f"Bearer {pat}",
                "Accept": "application/vnd.github.v3+json"
            },
            json={
                "ref": "main",
                "inputs": {
                    "qq_command": json.dumps(args, ensure_ascii=False),
                    "qq_openid": openid,
                    "qq_msg_type": msg_type,
                    "qq_group_openid": group_openid
                }
            },
            timeout=15
        )
    except Exception:
        pass

# ---------------- 主入口 ----------------

def main_handler(event, context):
    try:
        # API 网关触发器: 事件里带 httpMethod/body/queryString
        method = event.get("httpMethod", event.get("requestContext", {}).get("http", {}).get("method", "GET"))
        body = event.get("body", "") or ""
        if event.get("isBase64Encoded"):
            import base64
            body = base64.b64decode(body).decode("utf-8", errors="ignore")

        # ===== GET: 回调地址验证 =====
        if method.upper() == "GET":
            query = event.get("queryString", event.get("queryStringParameters", {})) or {}
            if isinstance(query, str):
                try:
                    query = json.loads(query)
                except Exception:
                    query = {}
            ticket = query.get("ticket", "")
            if ticket:
                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"ticket": ticket}, ensure_ascii=False)
                }
            return {"statusCode": 200, "body": "OK"}

        # ===== POST: 事件推送 =====
        if method.upper() == "POST":
            try:
                event_data = json.loads(body)
            except Exception:
                event_data = {}
            d = event_data.get("d", {}) or {}
            content = (d.get("content") or "").replace("<@!?\\d+>", "").strip()
            openid = (d.get("author") or {}).get("id", "")
            msg_type = d.get("msg_type", "c2c") or ("group" if d.get("group_openid") else "c2c")
            group_openid = d.get("group_openid", "")

            if not content:
                return {"statusCode": 200, "body": '{"code":0}'}

            parsed = parse_command(content)

            if parsed.get("help"):
                send_qq_msg(openid, msg_type, group_openid, parsed["text"])
                return {"statusCode": 200, "body": '{"code":0}'}

            if parsed.get("unknown"):
                send_qq_msg(openid, msg_type, group_openid, "🤔 看不懂这条指令，发送 帮助 查看可用命令")
                return {"statusCode": 200, "body": '{"code":0}'}

            trigger_github(parsed["args"], openid, msg_type, group_openid)
            send_qq_msg(openid, msg_type, group_openid, "⏳ 收到指令，正在执行，请稍候...")

            return {"statusCode": 200, "body": '{"code":0}'}

    except Exception:
        pass

    return {"statusCode": 200, "body": "OK"}
