#!/usr/bin/env python3
"""
船舶动态跟踪系统 —— 支持 GitHub Actions 定时调度 + 本地运行双模式
========================================================================
使用方式:
  python ship_tracker.py           # 单次查询（GitHub Actions 默认用此模式）
  python ship_tracker.py --daemon  # 本地守护进程模式（每2小时自动查）
  python ship_tracker.py --grab-token  # 本地抓取新 Token 并保存
"""

import os
import sys
import time
import random
import json
import subprocess
import requests
from datetime import datetime, timedelta
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

# ==========================================
# 🔗 可修改链接区 — 你需要修改的链接都在这里
# ==========================================

# 【API 接口地址】NPEDI 船舶排期查询接口
API_URL = "https://www.npedi.com/onesite-api/vessel/plan/selectContainerDynamicPlan"

# 【网页地址】浏览器抓取 Token 时打开的页面
TOKEN_PAGE_URL = "https://www.npedi.com/onesite/vessel/plan"

# 【钉钉 Webhook】保持不变即可（消息会发到你的钉钉机器人）
DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=db0a14f83c676fbf67399ab0e633dd2c30af9a85593a2b2c27bc7775d4891124"

# ==========================================
# ⚙️ 配置区
# ==========================================

TOKEN_FILE = "token.txt"
EXCEL_FILE = "船舶动态跟踪.xlsx"
UPDATE_INTERVAL_HOURS = 2  # 自动更新间隔（小时）

# 你追踪的船舶列表（可自行增删）
VESSELS_TO_QUERY = [
    {"name": "AL MURAYKH", "voyage": "622W"},
]

# ==========================================
# Token 管理
# ==========================================

def load_token():
    """加载 Token：优先环境变量（GitHub Actions），其次本地文件"""
    token = os.environ.get("NPEDI_TOKEN")
    if token:
        return token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return None


def save_token(token):
    """保存 Token 到本地文件"""
    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        f.write(token)
    print(f"✅ Token 已保存至 {TOKEN_FILE}")


def grab_token_via_browser():
    """启动 Playwright 浏览器抓取 Token（仅本地运行有效）"""
    print("\n[系统提示] 正在启动浏览器环境以获取新 Token...")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 请先安装 Playwright: pip install playwright && playwright install chromium")
        return None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        token_container = []

        def on_request(request):
            try:
                for key, value in request.headers.items():
                    if key.lower() == "ediauthorization" and not token_container:
                        token_container.append(value)
                        print("🎉 成功拦截到底层请求，已捕获 Token！")
            except:
                pass

        context.on("request", on_request)
        print(f"👉 正在打开网页 {TOKEN_PAGE_URL}，请在浏览器中完成登录...")

        try:
            page.goto(TOKEN_PAGE_URL, timeout=90000, wait_until="domcontentloaded")
        except:
            pass

        for _ in range(300):
            if token_container:
                break
            page.wait_for_timeout(1000)

        if not token_container:
            print("\n❌ 抓取超时：未能获取到 Token。")
            browser.close()
            return None

        final_token = token_container[0]
        browser.close()
        return final_token

# ==========================================
# 数据查询核心
# ==========================================

def fetch_and_parse(vessel_name, voyage, current_token):
    """调用 API 并返回解析后的字典"""
    today = datetime.now()
    eta_begin = (today - timedelta(days=15)).strftime("%Y-%m-%d")
    eta_end = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    params = {
        "vesselEnName": vessel_name, "voyage": voyage,
        "etaBegin": eta_begin, "etaEnd": eta_end,
        "page": "1", "pageSize": "50"
    }
    headers = {
        "Ediauthorization": current_token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(API_URL, params=params, headers=headers, timeout=10)
        if response.status_code == 401:
            return "EXPIRED"
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 200 or not data.get('data') or not data['data'].get('list'):
            print(f"\n⚠️ 未查询到 [{vessel_name}] 航次 [{voyage}] 的排期信息。")
            return "NO_DATA"

        item = data['data']['list'][0]

        parsed_data = {
            'update_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'cn_name': item.get('vesselCnName') or '-',
            'en_name': item.get('vesselEnName') or '-',
            'voyage': item.get('voyage') or '-',
            'terminal': item.get('terminal') or '-',
            'eta': item.get('eta') or '暂无',
            'etd': item.get('etd') or '暂无',
            'ata': item.get('ata') or '【尚未靠泊】',
            'atd': item.get('atd') or '【尚未离泊】',
            'ctn_start': item.get('ctnStartTime') or '-',
            'ctn_end': item.get('ctnEndTime') or '-',
            'port_close': item.get('portCloseTime') or '-',
            'custom_close': item.get('customCloseTime') or '-',
            'last_port': item.get('lastPortName') or '-',
            'next_port': item.get('nextPortName') or '-'
        }

        # 控制台打印
        print(f"\n📌 船名: {parsed_data['cn_name']} ({parsed_data['en_name']}) | 🔖 航次: {parsed_data['voyage']} | 🏗️ 码头: {parsed_data['terminal']}")
        print("-" * 45)
        print(f"⏳ 计划靠泊 (ETA): {parsed_data['eta']} | 计划离泊 (ETD): {parsed_data['etd']}")
        print(f"⚓ 实际靠泊 (ATA): {parsed_data['ata']} | 实际离泊 (ATD): {parsed_data['atd']}")
        print(f"📦 进箱时间: {parsed_data['ctn_start']} 至 {parsed_data['ctn_end']}")
        print(f"🛑 码头截单: {parsed_data['port_close']} | 海关截关: {parsed_data['custom_close']}")
        print(f"🗺️ 航线轨迹: 上一港 [{parsed_data['last_port']}] ➔ 下一港 [{parsed_data['next_port']}]\n")

        return parsed_data

    except Exception as e:
        print(f"\n❌ 网络请求异常: {e}")
        return "ERROR"

# ==========================================
# 钉钉推送 & Excel 写入
# ==========================================

def send_dingtalk_msg(data_list):
    """将数据排版为 Markdown 并推送到钉钉"""
    if not data_list:
        return

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"### 🚢 船舶排期自动更新\n*{current_time}*\n\n---\n\n"

    for item in data_list:
        content += f"**📌 船名**: {item['cn_name']} ({item['en_name']}) | **🔖 航次**: {item['voyage']} | **🏗️ 码头**: {item['terminal']}\n\n"
        content += f"**⏳ 计划靠泊 (ETA)**: <font color=#008000>{item['eta']}</font> | **计划离泊 (ETD)**: {item['etd']}\n\n"
        content += f"**⚓ 实际靠泊 (ATA)**: {item['ata']} | **实际离泊 (ATD)**: {item['atd']}\n\n"
        content += f"**📦 进箱时间**: {item['ctn_start']} 至 {item['ctn_end']}\n\n"
        content += f"**🛑 码头截单**: <font color=#FF0000>{item['port_close']}</font> | **海关截关**: {item['custom_close']}\n\n"
        content += f"**🗺️ 航线轨迹**: 上一港 [{item['last_port']}] ➔ 下一港 [{item['next_port']}]\n\n"
        content += "---\n\n"

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "🚢 船舶动态更新",
            "text": content
        }
    }

    try:
        response = requests.post(DINGTALK_WEBHOOK, json=payload)
        if response.status_code == 200:
            print("📣 钉钉消息推送成功！")
        else:
            print(f"⚠️ 钉钉推送失败: {response.text}")
    except Exception as e:
        print(f"⚠️ 钉钉推送出现异常: {e}")


def save_to_excel(data_list):
    """将数据写入 Excel 并进行简单排版"""
    if not data_list:
        return

    file_exists = os.path.exists(EXCEL_FILE)

    try:
        if file_exists:
            wb = load_workbook(EXCEL_FILE)
            ws = wb.active
        else:
            wb = Workbook()
            ws = wb.active
            ws.title = "船舶排期"
            headers = ["更新时间", "船名 (英文)", "航次", "码头", "计划靠泊(ETA)", "计划离泊(ETD)",
                       "实际靠泊(ATA)", "实际离泊(ATD)", "进箱开始", "进箱结束",
                       "码头截单", "海关截关", "航线预告"]
            ws.append(headers)

            header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            ws.column_dimensions['A'].width = 22
            ws.column_dimensions['B'].width = 25
            ws.column_dimensions['C'].width = 12
            ws.column_dimensions['M'].width = 30

        for item in data_list:
            row = [
                item['update_time'],
                f"{item['cn_name']} ({item['en_name']})",
                item['voyage'],
                item['terminal'],
                item['eta'], item['etd'],
                item['ata'], item['atd'],
                item['ctn_start'], item['ctn_end'],
                item['port_close'], item['custom_close'],
                f"上港:{item['last_port']} -> 下港:{item['next_port']}"
            ]
            ws.append(row)

        wb.save(EXCEL_FILE)
        print(f"📁 数据已成功保存至 Excel 文档: {EXCEL_FILE}")

    except PermissionError:
        print(f"❌ 写入 Excel 失败！请确认 `{EXCEL_FILE}` 没有被其他软件(如 Office) 打开。")
    except Exception as e:
        print(f"❌ 保存 Excel 发生异常: {e}")

# ==========================================
# Token 推送至 GitHub
# ==========================================

def push_token_to_github(new_token):
    """将新 Token 通过 gh CLI 写入 GitHub Secret（首选方法）"""
    print("\n🔄 正在将新 Token 推送到 GitHub Secrets...")
    try:
        # 检查是否已登录 gh
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print("⚠️ gh CLI 未登录，跳过 GitHub Secret 自动更新。")
            print(f"\n💡 请手动完成以下两步：")
            print(f"   ① 在浏览器打开你的 GitHub 仓库 → Settings → Secrets and variables → Actions")
            print(f"   ② 点击 New repository secret → Name: NPEDI_TOKEN → Value: {new_token}")
            return False

        # 获取当前仓库的 owner/name
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print("⚠️ 无法获取仓库信息，跳过自动更新。")
            return False

        repo_full = result.stdout.strip()
        print(f"   检测到仓库: {repo_full}")

        # 写入 Secret
        result = subprocess.run(
            ["gh", "secret", "set", "NPEDI_TOKEN", "--repo", repo_full],
            input=new_token,
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(f"✅ Token 已成功推送至 GitHub Secrets！（后续 Action 将自动使用新 Token）")
            return True
        else:
            print(f"⚠️ 设置 Secret 失败: {result.stderr.strip()}")
            return False

    except Exception as e:
        print(f"⚠️ 推送 Token 到 GitHub 失败: {e}")
        return False

# ==========================================
# 执行器
# ==========================================

def run_once():
    """单次查询（GitHub Actions + 本地单次运行）"""
    print(f"\n🚀 开始查询船舶动态... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")

    api_token = load_token()
    if not api_token:
        print("❌ 未找到 Token！")
        print("💡 请先本地运行: python ship_tracker.py --grab-token")
        print("   或者设置环境变量: export NPEDI_TOKEN=你的Token")
        sys.exit(1)

    results_to_save = []

    for index, vessel in enumerate(VESSELS_TO_QUERY):
        target_name = vessel.get("name")
        target_voyage = vessel.get("voyage")

        while True:
            result = fetch_and_parse(target_name, target_voyage, api_token)

            if result == "EXPIRED":
                print("⚠️ Token 已过期！请重新抓取。")
                print(f"💡 本地运行: python ship_tracker.py --grab-token")
                return False
            elif isinstance(result, dict):
                results_to_save.append(result)
                break
            else:
                break

        if index < len(VESSELS_TO_QUERY) - 1:
            time.sleep(round(random.uniform(1.5, 3.5), 2))

    if results_to_save:
        save_to_excel(results_to_save)
        send_dingtalk_msg(results_to_save)
        print(f"\n✅ 本轮查询完成！数据已保存并推送至钉钉。")
        return True

    print(f"\n⚠️ 未查询到任何数据。")
    return False


def run_daemon():
    """本地守护进程模式（每2小时自动查询）"""
    import threading

    force_run_event = threading.Event()

    def input_listener():
        while True:
            try:
                input()
                print("\n⚡ 检测到回车指令，立即触发手动查询！")
                force_run_event.set()
            except:
                break

    print(f"🌟 港口船舶自动化跟踪系统已启动！")
    print(f"⏲️ 当前设置：每 {UPDATE_INTERVAL_HOURS} 小时自动更新一次数据至 Excel 并推送钉钉。")
    print(f"💡 随时按【回车键 (Enter)】即可立即强制拉取最新数据。")
    print("=" * 60)

    listener_thread = threading.Thread(target=input_listener, daemon=True)
    listener_thread.start()

    while True:
        run_once()

        next_run_time = datetime.now() + timedelta(hours=UPDATE_INTERVAL_HOURS)
        print(f"⏳ 下一次自动执行时间为: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")

        force_run_event.clear()
        while datetime.now() < next_run_time:
            if force_run_event.is_set():
                break
            time.sleep(1)

# ==========================================
# 入口
# ==========================================

if __name__ == "__main__":
    if "--grab-token" in sys.argv:
        # 本地抓取 Token 模式
        new_token = grab_token_via_browser()
        if new_token:
            save_token(new_token)
            print(f"\n🔑 新 Token: {new_token[:20]}...{new_token[-10:]}")
            # 尝试推送到 GitHub Secrets
            push_token_to_github(new_token)
    elif "--daemon" in sys.argv:
        # 本地守护进程模式
        run_daemon()
    else:
        # 默认：单次查询模式（GitHub Actions 使用此模式）
        run_once()
