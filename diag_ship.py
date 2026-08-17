#!/usr/bin/env python3
"""临时诊断第6轮：打印两船全部历史记录（用完即删）"""
import os, requests

TOKEN = os.environ.get("NPEDI_TOKEN", "")
BASE = "https://www.npedi.com/onesite-api"
H = {"Ediauthorization": TOKEN, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def dump(label, name):
    p = {"vesselEnName": name, "voyage": "", "etaBegin": "2020-01-01", "etaEnd": "2027-12-31", "page": "1", "pageSize": "50"}
    d = requests.get(f"{BASE}/vessel/plan/selectContainerDynamicPlan", params=p, headers=H, timeout=10).json()
    lst = (d.get("data") or {}).get("list") or []
    print(f"== {label} 共{len(lst)}条:")
    for it in sorted(lst, key=lambda x: x.get('eta') or ''):
        print(f"   {it.get('voyage')} | ETA={it.get('eta')} | 码头={it.get('terminal')} | 中文名={it.get('vesselCnName')} | {it.get('lastPortName')}->{it.get('nextPortName')}")

dump("ONE FUTURE", "ONE FUTURE")
dump("YM TOTALITY", "YM TOTALITY")

# 全量8-9月表里找中文名含 未来/阳明/圆满/海洋 的
p = {"vesselEnName": "", "voyage": "", "etaBegin": "2026-08-01", "etaEnd": "2026-09-30", "page": "1", "pageSize": "50"}
for pg in [1, 2, 3, 4]:
    pp = dict(p, page=str(pg))
    d = requests.get(f"{BASE}/vessel/plan/selectContainerDynamicPlan", params=pp, headers=H, timeout=10).json()
    lst = (d.get("data") or {}).get("list") or []
    for it in lst:
        cn = it.get('vesselCnName') or ''
        en = it.get('vesselEnName') or ''
        if any(k in cn for k in ["未来", "阳明", "圆满", "海洋"]) or any(k in en for k in ["FUTURE", "TOTALITY", "ONE", "YM "]):
            print(f"   [CN命中] {en} ({cn}) | {it.get('voyage')} | ETA={it.get('eta')} | {it.get('terminal')}")
