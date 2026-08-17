#!/usr/bin/env python3
"""临时诊断脚本 v2：剩余4艘失败船（用完即删）"""
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
        d = r.json()
        lst = (d.get("data") or {}).get("list") or []
        print(f"== [{label}] code={d.get('code')} 条数={len(lst)}")
        for it in lst[:8]:
            print(f"   -> {it.get('vesselEnName')} | {it.get('voyage')} | ETA={it.get('eta')} | {it.get('lastPortName')}->{it.get('nextPortName')}")
    except Exception as e:
        print(f"== [{label}] EXC {e}")

# 生产窗口(-15/+30)
for n, v in [("MAREN MAERSK","630W"), ("MSC REEF","GJ629W"), ("YM TOPMOST","025W"), ("CMA CGM ADONIS","V.0BEONW")]:
    q(f"{n} {v} 标准窗", n, v, 15, 30)
# 宽窗(-120/+180) 不填航次
for n in ["MAREN MAERSK", "MSC REEF", "YM TOPMOST", "CMA CGM ADONIS"]:
    q(f"{n} 全航次宽窗", n, "", 120, 180)
# 宽窗+航次
for n, v in [("MAREN MAERSK","630W"), ("MSC REEF","GJ629W"), ("YM TOPMOST","025W"), ("CMA CGM ADONIS","V.0BEONW")]:
    q(f"{n} {v} 宽窗", n, v, 120, 180)
