#!/usr/bin/env python3
"""临时诊断：枚举NPEDI月计划/其他接口 + 参数组合（用完即删）"""
import os, requests
from datetime import datetime, timedelta

TOKEN = os.environ.get("NPEDI_TOKEN", "")
BASE = "https://www.npedi.com/onesite-api"
H = {"Ediauthorization": TOKEN, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
today = datetime.now()
WIDE_B = (today - timedelta(days=400)).strftime("%Y-%m-%d")
WIDE_E = (today + timedelta(days=400)).strftime("%Y-%m-%d")

def call(label, path, params):
    try:
        r = requests.get(f"{BASE}{path}", params=params, headers=H, timeout=10)
        if r.status_code == 404:
            print(f"== [{label}] 404"); return
        if r.status_code == 401:
            print(f"== [{label}] 401 TOKEN EXPIRED"); return
        try:
            d = r.json()
        except Exception:
            print(f"== [{label}] HTTP {r.status_code} 非JSON: {r.text[:80]}"); return
        lst = (d.get("data") or {}).get("list") if isinstance(d.get("data"), dict) else None
        n = len(lst) if lst else 0
        print(f"== [{label}] code={d.get('code')} msg={d.get('msg')} 条数={n}")
        if lst:
            for it in lst[:5]:
                print(f"   -> {it.get('vesselEnName')} | {it.get('voyage')} | ETA={it.get('eta')} | {it.get('terminal')}")
    except Exception as e:
        print(f"== [{label}] EXC {e}")

V = {"vesselEnName": "ONE FUTURE", "voyage": "009W", "etaBegin": WIDE_B, "etaEnd": WIDE_E, "page": "1", "pageSize": "50"}
V2 = {"vesselEnName": "YM TOTALITY", "voyage": "028W", "etaBegin": WIDE_B, "etaEnd": WIDE_E, "page": "1", "pageSize": "50"}

# 1. 已知接口+宽窗400天
call("动态计划 ONE FUTURE 400天", "/vessel/plan/selectContainerDynamicPlan", V)
call("动态计划 YM TOTALITY 400天", "/vessel/plan/selectContainerDynamicPlan", V2)

# 2. 枚举疑似月计划/其他接口
paths = [
    "/vessel/plan/selectContainerMonthPlan",
    "/vessel/plan/selectMonthPlan",
    "/vessel/plan/selectContainerPlan",
    "/vessel/plan/selectVesselPlan",
    "/vessel/plan/selectPlan",
    "/vessel/plan/selectContainerWeekPlan",
    "/vessel/plan/selectContainerAnnualPlan",
    "/vessel/plan/selectContainerPlanList",
    "/vessel/plan/selectVesselMonthPlan",
    "/vessel/monthPlan/selectContainerMonthPlan",
    "/vessel/month/selectContainerMonthPlan",
    "/vessel/plan/monthPlan",
    "/vessel/plan/list",
    "/vessel/plan/selectContainerDynamicPlanList",
    "/vessel/plan/selectContainerBerthPlan",
    "/vessel/plan/selectContainerVoyagePlan",
    "/vessel/plan/selectContainerShipPlan",
    "/vessel/plan/selectContainerPlanPage",
    "/vessel/plan/queryContainerPlan",
    "/vessel/plan/getContainerPlan",
    "/containerPlan/selectContainerMonthPlan",
    "/vesselPlan/selectContainerMonthPlan",
]
for p in paths:
    call(f"{p.split('/')[-1]} ONE", p, V)

# 3. 动态计划+额外参数尝试
extra = [
    ("带portCode", dict(V, portCode="BLCT3")),
    ("带line", dict(V, line="ONE")),
    ("带service", dict(V, service="")),
    ("中文名未来号", dict(V, vesselEnName="未来")),
    ("中文名阳明", dict(V2, vesselEnName="阳明")),
    ("不带voyage", {k: v for k, v in V.items() if k != "voyage"}),
    ("voyage小写", dict(V, voyage="009w")),
    ("voyage去0", dict(V, voyage="9W")),
    ("voyage带连字符", dict(V, voyage="009W-")),
    ("空船名009W", dict(V, vesselEnName="")),
]
for label, params in extra:
    call(label, "/vessel/plan/selectContainerDynamicPlan", params)
