#!/usr/bin/env python3
"""临时诊断第8轮：月计划接口里搜 ONE FUTURE / YM TOTALITY（用完即删）"""
import os, requests, json

TOKEN = os.environ.get("NPEDI_TOKEN", "")
BASE = "https://www.npedi.com/onesite-api"
H = {"Ediauthorization": TOKEN, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get(path, params):
    r = requests.get(f"{BASE}{path}", params=params, headers=H, timeout=60)
    return r.json()

def show(label, hits, maxn=8):
    print(f"== [{label}] 命中 {len(hits)} 条:")
    for it in hits[:maxn]:
        print("   ", json.dumps({k: it.get(k) for k in
              ["ctnPlanyearmonth", "vesselNamec", "vesselNamee", "exportVoyage", "importVoyage",
               "loadDate", "leaveDate", "serviceName", "serviceCode", "operatorcompanyShortname",
               "shipagentshipcompany", "vesselImono"]}, ensure_ascii=False))

# 1. 月计划: 船名+航次精确查
for name, voy in [("ONE FUTURE", "009W"), ("YM TOTALITY", "028W"), ("ONE FUTURE", ""), ("YM TOTALITY", "")]:
    d = get("/vessel/plan/getMoonthlyPlanNew", {"vesselEnName": name, "voyage": voy})
    lst = (d.get("data") or {}).get("list") or []
    print(f"--- 月计划 vesselEnName={name} voyage={voy} total={d.get('data',{}).get('total')}")
    # 搜名字
    hits = [it for it in lst if "FUTURE" in (it.get("vesselNamee") or "").upper() or "TOTALITY" in (it.get("vesselNamee") or "").upper() or "未来" in (it.get("vesselNamec") or "") or "共明" in (it.get("vesselNamec") or "")]
    show(f"月计划 {name} {voy} 命中船名", hits)
    if not hits and lst:
        show(f"月计划 {name} {voy} 前几条", lst)

# 2. 按船动态: 全量202KB里搜
d = get("/vessel/plan/getDynamicPlanVessel", {})
lst = d.get("data") or []
print(f"--- 按船动态 全量 {len(lst)} 条")
hits = [it for it in lst if "FUTURE" in (it.get("vesselNamee") or "").upper() or "TOTALITY" in (it.get("vesselNamee") or "").upper() or "未来" in (it.get("vesselNamec") or "") or "共明" in (it.get("vesselNamec") or "")]
show("按船动态 命中", hits)
if not hits:
    # 打印所有唯一船名看看有没有类似
    names = sorted(set((it.get("vesselNamee") or "") for it in lst))
    print("   唯一船名数:", len(names))
    print("   含ONE/YM的:", [n for n in names if "ONE" in n.upper() or n.startswith("YM")][:20])

# 3. 动态新: 全量里搜
d = get("/vessel/plan/getDynamicPlanNew", {})
lst = (d.get("data") or {}).get("list") or d.get("data") or []
print(f"--- 动态新 全量 {len(lst)} 条")
hits = [it for it in lst if "FUTURE" in (it.get("vesselNamee") or "").upper() or "TOTALITY" in (it.get("vesselNamee") or "").upper() or "未来" in (it.get("vesselNamec") or "") or "共明" in (it.get("vesselNamec") or "")]
show("动态新 命中", hits)

# 4. 月计划全量(39MB太大, 用2026年月份参数缩小) 试yearmonth参数
for ym in ["202608", "202609"]:
    d = get("/vessel/plan/getMoonthlyPlanNew", {"yearmonth": ym, "voyage": "009W"})
    lst = (d.get("data") or {}).get("list") or []
    print(f"--- 月计划 yearmonth={ym} voyage=009W total={d.get('data',{}).get('total')}")
    hits = [it for it in lst if "FUTURE" in (it.get("vesselNamee") or "").upper() or "未来" in (it.get("vesselNamec") or "")]
    show(f"月计划 {ym} 命中", hits)
