#!/usr/bin/env python3
"""临时诊断第7轮：实测 月计划/周计划/按船动态 接口（用完即删）"""
import os, requests

TOKEN = os.environ.get("NPEDI_TOKEN", "")
BASE = "https://www.npedi.com/onesite-api"
H = {"Ediauthorization": TOKEN, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def call(label, path, params):
    try:
        r = requests.get(f"{BASE}{path}", params=params, headers=H, timeout=15)
        txt = r.text
        print(f"== [{label}] HTTP {r.status_code} len={len(txt)}")
        print("   ", txt[:600].replace("\n", " "))
    except Exception as e:
        print(f"== [{label}] EXC {e}")

# 1. 月计划接口 - 各种参数组合
call("月计划 空参", "/vessel/plan/getMoonthlyPlanNew", {})
call("月计划 船+航次", "/vessel/plan/getMoonthlyPlanNew", {"vesselEnName": "ONE FUTURE", "voyage": "009W"})
call("月计划 船+日期", "/vessel/plan/getMoonthlyPlanNew", {"vesselEnName": "ONE FUTURE", "beginDate": "2026-07-01", "endDate": "2026-12-31"})
call("月计划 日期范围", "/vessel/plan/getMoonthlyPlanNew", {"beginDate": "2026-07-01", "endDate": "2026-12-31"})
call("月计划 月份", "/vessel/plan/getMoonthlyPlanNew", {"month": "2026-08"})

# 2. 按船动态计划
call("按船动态 船+航次", "/vessel/plan/getDynamicPlanVessel", {"vesselEnName": "ONE FUTURE", "voyage": "009W"})
call("按船动态 船", "/vessel/plan/getDynamicPlanVessel", {"vesselEnName": "ONE FUTURE"})
call("按船动态 船+航次 YM", "/vessel/plan/getDynamicPlanVessel", {"vesselEnName": "YM TOTALITY", "voyage": "028W"})

# 3. 动态计划新
call("动态新 船+航次", "/vessel/plan/getDynamicPlanNew", {"vesselEnName": "ONE FUTURE", "voyage": "009W"})
call("动态新 空参", "/vessel/plan/getDynamicPlanNew", {})

# 4. 周计划
call("周计划 船+航次", "/vessel/plan/getWeeklylyPlan", {"vesselEnName": "ONE FUTURE", "voyage": "009W"})
