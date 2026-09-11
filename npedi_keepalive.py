#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NPEDI 会话保活 (GitHub Actions 每 20 分钟)

原理：NPEDI 是若依(RuoYi)框架，token 是服务端会话 token，服务端会因每次
带 token 的请求而「滑动续期」。本脚本用 NPEDI_TOKEN 调一次接口，给会话续命；
若会话已失效(HTTP 401 / body code=401)，推钉钉告警提示重新登录。

退出码：0=保活成功或网络抖动；1=会话失效或异常。
"""
import os
import sys
from datetime import datetime, timedelta

import requests

API_URL = "https://www.npedi.com/onesite-api/vessel/plan/selectContainerDynamicPlan"
WEBHOOK_FILE = ".webhook.txt"


def load_token():
    """优先环境变量（GitHub Actions Secret），其次本地 token.txt"""
    t = os.environ.get("NPEDI_TOKEN")
    if t:
        return t.strip()
    if os.path.exists("token.txt"):
        with open("token.txt", encoding="utf-8") as f:
            return f.read().strip()
    return None


def get_webhook():
    if os.path.exists(WEBHOOK_FILE):
        try:
            with open(WEBHOOK_FILE, encoding="utf-8") as f:
                u = f.read().strip()
                if u:
                    return u
        except Exception:
            pass
    return ""


def dingtalk_alert(text):
    """发送钉钉告警。

    ⚠️ 两个坑(2026-09-11 血泪):
    1. 机器人开启了「关键词过滤」, 文本必须包含关键词(如 "船舶"), 否则被拒;
    2. HTTP 200 != 发送成功 —— 关键词不匹配时钉钉仍返回 200 但 body 是
       {"errcode":310000,...}。必须解析 errcode, 否则会假报"已发送"。
    """
    url = get_webhook()
    if not url:
        print("(未配置 webhook，跳过告警)")
        return
    try:
        r = requests.post(url, json={"msgtype": "text", "text": {"content": text}}, timeout=10)
        ok = False
        try:
            ok = (r.json().get("errcode") == 0)
        except Exception:
            ok = (r.status_code == 200)
        if ok:
            print(f"钉钉告警已发送: HTTP {r.status_code}")
        else:
            print(f"❌ 钉钉告警被拒(未送达): HTTP {r.status_code} | {r.text[:160]}")
    except Exception as e:
        print(f"钉钉告警发送异常: {e}")


def main():
    tok = load_token()
    if not tok:
        print("ALERT: 未找到 NPEDI_TOKEN（Secret/文件都为空）")
        return 1

    now = datetime.now()
    params = {
        "vesselEnName": "",
        "voyage": "",
        "etaBegin": (now - timedelta(days=15)).strftime("%Y-%m-%d"),
        "etaEnd": (now + timedelta(days=30)).strftime("%Y-%m-%d"),
        "page": "1",
        "pageSize": "1",
    }
    headers = {
        "Ediauthorization": tok,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }

    try:
        r = requests.get(API_URL, params=params, headers=headers, timeout=15)
    except Exception as e:
        # 网络抖动/超时不算会话失效，避免误报
        print(f"⚠️ 网络异常（按非失效处理）: {e}")
        return 0

    try:
        j = r.json()
    except Exception:
        j = {}

    if r.status_code == 200 and j.get("code") == 200:
        total = (j.get("data") or {}).get("total")
        print(f"✅ NPEDI 会话保活成功 (code=200, total={total})")
        return 0

    if r.status_code == 401 or j.get("code") == 401:
        print("❌ NPEDI 会话已失效 (code=401)")
        # ⚠️ 文本必须含关键词"船舶", 否则钉钉关键词过滤会拒收(errcode 310000)
        dingtalk_alert(
            "⚠️ 【船舶跟踪】NPEDI 船期会话已失效，token 需要重新登录一次。\n"
            "登录 www.npedi.com 后会话会自动恢复（云保活会接着续期）。"
        )
        return 1

    print(f"⚠️ 未知响应: HTTP {r.status_code} | {str(j)[:200]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
