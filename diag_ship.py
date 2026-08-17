#!/usr/bin/env python3
"""临时诊断脚本：定位 ONE FUTURE / YM TOTALITY 查不到的原因（用完即删）"""
import os, requests
from datetime import datetime, timedelta

TOKEN = os.environ.get("NPEDI_TOKEN", "")
API = "https://www.npedi.com/onesite-api/vessel/plan/selectContainerDynamicPlan"
H = {"Ediauthorization": TOKEN, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
today = datetime.now()

def q(label, name, voyage, d1, d2):
    params = {
        "vesselEnName": name, "voyage": voyage,
        "etaBegin": (today - timedelta(days=d1)).strftime("%Y-%m-%d"),
        "etaEnd": (today + timedelta(days=d2)).strftime("%Y-%m-%d"),
        "page": "1", "pageSize": "50"
    }
    try:
        r = requests.get(API, params=params, headers=H, timeout=10)
        print(f"== [{label}] HTTP {r.status_code}")
        if r.status_code != 200:
            print("   ", r.text[:300])
            return
        d = r.json()
        lst = (d.get("data") or {}).get("list") or []
        print(f"   code={d.get('code')} msg={d.get('msg')} 条数={len(lst)}")
        for it in lst[:10]:
            print(f"   -> {it.get('vesselEnName')} | {it.get('voyage')} | ETA={it.get('eta')} | {it.get('lastPortName')}->{it.get('nextPortName')}")
    except Exception as e:
        print(f"== [{label}] EXC {e}")

print(">>> 生产窗口(-15/+30)")
q("ONE FUTURE 009WJ", "ONE FUTURE", "009WJ", 15, 30)
q("ONE FUTURE 009W", "ONE FUTURE", "009W", 15, 30)
q("YM TOTALITY 028WA", "YM TOTALITY", "028WA", 15, 30)
q("YM TOTALITY 028W", "YM TOTALITY", "028W", 15, 30)

print(">>> 宽窗(-120/+180) 不填航次: 看数据库里这艘船有哪些航次")
q("ONE FUTURE 全航次", "ONE FUTURE", "", 120, 180)
q("YM TOTALITY 全航次", "YM TOTALITY", "", 120, 180)

print(">>> 宽窗 + 带/不带后缀")
q("ONE FUTURE 009W 宽窗", "ONE FUTURE", "009W", 120, 180)
q("ONE FUTURE 009WJ 宽窗", "ONE FUTURE", "009WJ", 120, 180)
q("YM TOTALITY 028W 宽窗", "YM TOTALITY", "028W", 120, 180)
q("YM TOTALITY 028WA 宽窗", "YM TOTALITY", "028WA", 120, 180)

print(">>> 对照: 已知能查到的船")
q("对照 MSC ELISA XIII FW633W", "MSC ELISA XIII", "FW633W", 15, 30)
q("对照 EVER GOLDEN 033W", "EVER GOLDEN", "033W", 15, 30)

print(">>> 船名前缀/子串: NPEDI 库里有没有近似船")
q("前缀 ONE", "ONE", "", 120, 180)
q("子串 FUTURE", "FUTURE", "", 120, 180)
q("前缀 YM", "YM", "", 120, 180)
q("子串 TOTALITY", "TOTALITY", "", 120, 180)
q("ONE FUTURE 带序号", "ONE FUTURE 2", "", 120, 180)
q("YM TOTALITY 带序号", "YM TOTALITY 2", "", 120, 180)

print(">>> 只按航次查(空船名): 该航次是否在库")
q("航次 028W 空船名", "", "028W", 120, 180)
q("航次 009W 空船名", "", "009W", 120, 180)
q("航次 028WA 空船名", "", "028WA", 120, 180)
q("航次 009WJ 空船名", "", "009WJ", 120, 180)
