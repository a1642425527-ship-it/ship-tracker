#!/usr/bin/env python3
"""临时诊断：CMA CGM ADONIS 月计划航次（用完即删）"""
import os, requests

TOKEN = os.environ.get("NPEDI_TOKEN", "")
BASE = "https://www.npedi.com/onesite-api"
H = {"Ediauthorization": TOKEN, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get(path, params):
    r = requests.get(f"{BASE}{path}", params=params, headers=H, timeout=60)
    return r.json()

# 1. 月计划: 按候选航次查
for voy in ["0BEONW", "0BENVW", "0BENVE", "0BEONE", "0BEON", "0BEONWE"]:
    d = get("/vessel/plan/getMoonthlyPlanNew", {"voyage": voy})
    data = d.get("data")
    lst = data.get("list") if isinstance(data, dict) else []
    hits = [it for it in lst if "ADONIS" in (it.get("vesselNamee") or "").upper() or "多尼斯" in (it.get("vesselNamec") or "")]
    print(f"## voyage={voy} total={data.get('total') if isinstance(data, dict) else '?'} ADONIS命中={len(hits)}")
    for it in hits:
        print(f"   {it.get('ctnPlanyearmonth')} | {it.get('vesselNamee')}({it.get('vesselNamec')}) | 出口{it.get('exportVoyage')}/进口{it.get('importVoyage')} | 装{it.get('loadDate')} 离{it.get('leaveDate')} | {it.get('operatorcompanyShortname')} | {str(it.get('serviceName'))[:30]}")

# 2. 动态计划: 0BEONW / 0BENVW
for voy in ["0BEONW", "0BENVW"]:
    d = get("/vessel/plan/selectContainerDynamicPlan", {"vesselEnName": "CMA CGM ADONIS", "voyage": voy, "etaBegin": "2026-01-01", "etaEnd": "2027-12-31"})
    lst = (d.get("data") or {}).get("list") or []
    print(f"## 动态 {voy}: {len(lst)}条")
    for it in lst[:5]:
        print(f"   {it.get('voyage')} | ETA={it.get('eta')} | {it.get('terminal')}")

# 3. 动态计划: 不带航次看全部
d = get("/vessel/plan/selectContainerDynamicPlan", {"vesselEnName": "CMA CGM ADONIS", "voyage": "", "etaBegin": "2020-01-01", "etaEnd": "2027-12-31"})
lst = (d.get("data") or {}).get("list") or []
print(f"## 动态 全部航次: {len(lst)}条")
for it in sorted(lst, key=lambda x: x.get('eta') or ''):
    print(f"   {it.get('voyage')} | ETA={it.get('eta')} | {it.get('terminal')} | {it.get('lastPortName')}->{it.get('nextPortName')}")
