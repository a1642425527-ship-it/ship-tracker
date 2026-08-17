#!/usr/bin/env python3
"""临时诊断第9轮：打印命中记录关键字段（用完即删）"""
import os, requests, json

TOKEN = os.environ.get("NPEDI_TOKEN", "")
BASE = "https://www.npedi.com/onesite-api"
H = {"Ediauthorization": TOKEN, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get(path, params):
    r = requests.get(f"{BASE}{path}", params=params, headers=H, timeout=60)
    return r.json()

KEYS = ["ctnPlanyearmonth", "ctnVesselSysid", "vesselNamec", "vesselNamee", "exportVoyage",
        "importVoyage", "loadDate", "leaveDate", "serviceName", "serviceCode",
        "operatorcompanyShortname", "shipagentshipcompany", "vesselImono", "vesselCallno"]

def dump(label, lst, names):
    hits = [it for it in lst if any(n in (it.get("vesselNamee") or "").upper() or n in (it.get("vesselNamec") or "") for n in names)]
    print(f"## {label}: 共{len(lst)}条, 命中{len(hits)}条")
    for it in hits:
        for k in KEYS:
            v = it.get(k)
            if v is not None and str(v) != "":
                print(f"   {k}={v}")
        print("   ----")

# 精确查询
for name, voy in [("ONE FUTURE", "009W"), ("YM TOTALITY", "028W")]:
    d = get("/vessel/plan/getMoonthlyPlanNew", {"vesselEnName": name, "voyage": voy})
    lst = (d.get("data") or {}).get("list") or []
    dump(f"月计划 {name} {voy}", lst, ["FUTURE", "TOTALITY", "未来", "共明"])

# 只按船名（不带航次）
d = get("/vessel/plan/getMoonthlyPlanNew", {"vesselEnName": "ONE FUTURE"})
lst = (d.get("data") or {}).get("list") or []
dump("月计划 ONE FUTURE 不带航次", lst, ["FUTURE", "未来"])

d = get("/vessel/plan/getMoonthlyPlanNew", {"vesselEnName": "YM TOTALITY"})
lst = (d.get("data") or {}).get("list") or []
dump("月计划 YM TOTALITY 不带航次", lst, ["TOTALITY", "共明"])
