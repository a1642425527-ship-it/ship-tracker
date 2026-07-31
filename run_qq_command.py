#!/usr/bin/env python3
"""
GitHub Actions 执行 QQ 命令并回复结果
由 ship-track.yml 的 workflow_dispatch 触发
"""
import json
import os
import random
import subprocess
import sys

import requests

SELF_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    # 读取 workflow_dispatch 传入的命令
    qq_cmd_raw = os.environ.get("QQ_CMD", "[]")
    openid = os.environ.get("QQ_OPENID", "")
    msg_type = os.environ.get("QQ_MSG_TYPE", "c2c")
    group_openid = os.environ.get("QQ_GROUP_OPENID", "")
    appid = os.environ.get("QQ_APPID", "")
    secret = os.environ.get("QQ_SECRET", "")

    try:
        cmd = json.loads(qq_cmd_raw) if qq_cmd_raw else []
    except Exception:
        cmd = []

    # 执行 ship_tracker.py
    if cmd:
        print(f"🚀 执行QQ命令: {cmd}")
        result = subprocess.run(
            [sys.executable, os.path.join(SELF_DIR, "ship_tracker.py"), *cmd],
            capture_output=True, text=True, timeout=300, cwd=SELF_DIR
        )
    else:
        print("🚀 正常查询模式")
        result = subprocess.run(
            [sys.executable, os.path.join(SELF_DIR, "ship_tracker.py")],
            capture_output=True, text=True, timeout=300, cwd=SELF_DIR
        )

    output = ((result.stdout or "") + (result.stderr or "")).strip()
    print(output)

    # 发回 QQ
    if openid and appid and secret:
        reply = output[-1500:] if output else "（命令执行无输出）"
        _send_qq(appid, secret, openid, msg_type, group_openid, reply)
    else:
        print("⚠️ 缺少 QQ 回复参数，跳过")


def _send_qq(appid, secret, openid, msg_type, group_openid, text):
    try:
        # 获取 access_token
        r = requests.post(
            "https://bots.qq.com/app/getAppAccessToken",
            json={"appId": appid, "clientSecret": secret}, timeout=15
        )
        token = r.json().get("access_token")
        if not token:
            print(f"⚠️ QQ token 获取失败: {r.text[:100]}")
            return

        payload = {
            "content": [{"type": "text", "data": text}],
            "msg_type": 0,
            "msg_seq": random.randint(0, 999999)
        }
        headers = {"Authorization": f"QQBot {token}", "Content-Type": "application/json"}

        if msg_type == "group" and group_openid:
            url = f"https://api.sgroup.qq.com/v2/groups/{group_openid}/messages"
        else:
            url = f"https://api.sgroup.qq.com/v2/users/{openid}/messages"

        r = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"📤 QQ回复发送: HTTP {r.status_code}")
    except Exception as e:
        print(f"⚠️ QQ回复发送失败: {e}")


if __name__ == "__main__":
    main()
