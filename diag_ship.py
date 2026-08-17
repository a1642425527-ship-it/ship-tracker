#!/usr/bin/env python3
"""临时诊断第10轮：精确匹配查两船全部月计划记录（用完即删）"""
import os, requests

TOKEN = os.environ.get("NPEDI_TOKEN", "")
BASE = "https://www.npedi.com/onesite-api"
H = {"Ediauthorization": TOKEN, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get(path, params):
    r = requests.get(f"{BASE}{path}", params=params, headers=H, timeout=60)
    return r.json()

def dump(label, lst):
    print(f"## {label}: 共{len(lst)}条")
    for it in lst:
        print(f"   {it.get('ctnPlanyearmonth')} | {it.get('vesselNamee')}({it.get('vesselNamec')}) | "
              f"出口{it.get('exportVoyage')}/进口{it.get('importVoyage')} | "
              f"装{it.get('loadDate')} 离{it.get('leaveDate')} | {it.get('operatorcompanyShortname')} | "
              f"{it.get('serviceName')} | {it.get('shipagentshipcompany')} | IMO={it.get('vesselImono')}")

# 全量月计划里精确找 YM TOTALITY / ONE FUTURE（vesselEnName参数似乎不生效, 只能全量拉取后本地精确匹配）
d = get("/vessel/plan/getMoonthlyPlanNew", {})
lst = d.get("data") or []
print("全量月计划条数:", len(lst))
dump("YM TOTALITY 精确", [it for it in lst if (it.get("vesselNamee") or "").strip() == "YM TOTALITY" or (it.get("vesselNamec") or "").strip() == "共明"])
dump("ONE FUTURE 精确", [it for it in lst if (it.get("vesselNamee") or "").strip() == "ONE FUTURE" or (it.get("vesselNamec") or "").strip() == "第一展望"])

# 按航次变体查
for voy in ["028W", "028WA", "028", "027W", "009W", "009WJ"]:
    d = get("/vessel/plan/getMoonthlyPlanNew", {"voyage": voy})
    l = (d.get("data") or {}).get("list") or []
    hits = [it for it in l if "TOTALITY" in (it.get("vesselNamee") or "").upper() or "共明" in (it.get("vesselNamec") or "") or "FUTURE" in (it.get("vesselNamee") or "").upper() or "第一展望" in (it.get("vesselNamec") or "")]
    dump(f"voyage={voy} 命中", hits)
