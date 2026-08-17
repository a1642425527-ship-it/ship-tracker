#!/usr/bin/env python3
"""临时诊断第5轮：YM TOTALITY历史 + 全量船期表扫描（用完即删）"""
import os, requests
from datetime import datetime, timedelta

TOKEN = os.environ.get("NPEDI_TOKEN", "")
BASE = "https://www.npedi.com/onesite-api"
H = {"Ediauthorization": TOKEN, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
today = datetime.now()

def call(label, params, pages=1, grep=None):
    for pg in range(1, pages + 1):
        p = dict(params, page=str(pg))
        try:
            r = requests.get(f"{BASE}/vessel/plan/selectContainerDynamicPlan", params=p, headers=H, timeout=10)
            d = r.json()
            lst = (d.get("data") or {}).get("list") or []
            hits = [it for it in lst if not grep or grep in (it.get('vesselEnName') or '')]
            print(f"== [{label} p{pg}] 条数={len(lst)}" + (f" 命中={len(hits)}" if grep else ""))
            if grep:
                for it in hits[:10]:
                    print(f"   -> {it.get('vesselEnName')} | {it.get('voyage')} | ETA={it.get('eta')} | {it.get('terminal')}")
            elif pg == 1:
                for it in lst[:5]:
                    print(f"   e.g. {it.get('vesselEnName')} | {it.get('voyage')} | ETA={it.get('eta')} | {it.get('terminal')}")
        except Exception as e:
            print(f"== [{label} p{pg}] EXC {e}")

# 1. YM TOTALITY 不带航次，超宽窗（查全部历史）
call("YM TOTALITY 全历史", {"vesselEnName": "YM TOTALITY", "voyage": "", "etaBegin": "2020-01-01", "etaEnd": "2027-12-31", "pageSize": "50"})

# 2. ONE FUTURE 全历史
call("ONE FUTURE 全历史", {"vesselEnName": "ONE FUTURE", "voyage": "", "etaBegin": "2020-01-01", "etaEnd": "2027-12-31", "pageSize": "50"})

# 3. 全量船期表扫描：7月-10月 2026，找这两个船名（任何航次）
for lo, hi in [("2026-07-01", "2026-08-17"), ("2026-08-17", "2026-09-30"), ("2026-09-30", "2026-10-31")]:
    call(f"全量{lo}~{hi}", {"vesselEnName": "", "voyage": "", "etaBegin": lo, "etaEnd": hi, "pageSize": "50"}, pages=3, grep=None)
    # 专门 grep 两个船名
    for nm in ["ONE FUTURE", "YM TOTALITY"]:
        call(f"grep {nm} {lo}~{hi}", {"vesselEnName": "", "voyage": "", "etaBegin": lo, "etaEnd": hi, "pageSize": "50"}, pages=4, grep=nm)
