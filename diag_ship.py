#!/usr/bin/env python3
"""临时诊断第11轮：028W全部记录 + 变体航次（用完即删）"""
import os, requests

TOKEN = os.environ.get("NPEDI_TOKEN", "")
BASE = "https://www.npedi.com/onesite-api"
H = {"Ediauthorization": TOKEN, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get(path, params):
    r = requests.get(f"{BASE}{path}", params=params, headers=H, timeout=60)
    return r.json()

def recs(d):
    data = d.get("data")
    if isinstance(data, dict):
        return data.get("list") or []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []

def dump(label, lst, maxn=999):
    print(f"## {label}: {len(lst)}条")
    for it in lst[:maxn]:
        print(f"   {it.get('ctnPlanyearmonth')} | {it.get('vesselNamee')}({it.get('vesselNamec')}) | "
              f"出口{it.get('exportVoyage')}/进口{it.get('importVoyage')} | "
              f"装{it.get('loadDate')} 离{it.get('leaveDate')} | {it.get('operatorcompanyShortname')} | "
              f"{str(it.get('serviceName'))[:30]}")

# 028W 全部记录
d = get("/vessel/plan/getMoonthlyPlanNew", {"voyage": "028W"})
dump("voyage=028W", recs(d))
# 028WA
d = get("/vessel/plan/getMoonthlyPlanNew", {"voyage": "028WA"})
dump("voyage=028WA", recs(d))
# 027W (YM TOTALITY 上一航次)
d = get("/vessel/plan/getMoonthlyPlanNew", {"voyage": "027W"})
dump("voyage=027W", recs(d))
# 009WJ (ONE FUTURE 进口航次)
d = get("/vessel/plan/getMoonthlyPlanNew", {"voyage": "009WJ"})
dump("voyage=009WJ", recs(d))
