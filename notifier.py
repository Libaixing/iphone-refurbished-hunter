# -*- coding: utf-8 -*-
"""
Telegram 通知模块 - V1.1.0
"""

import requests
import config
from typing import Dict

def send_telegram_message(text: str) -> bool:
    if not config.TELEGRAM_ENABLE:
        print("ℹ️ Telegram 通知已禁用，消息未发送")
        return False

    token = config.TELEGRAM_BOT_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        print("❌ Telegram 配置缺失，无法发送")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            return True
        print(f"❌ Telegram 发送失败: {resp.status_code} - {resp.text}")
        return False
    except requests.RequestException as e:
        print(f"❌ Telegram 网络异常: {e}")
        return False

def format_notification(item: Dict, price_changed: bool = False) -> str:
    """
    格式化通知消息
    如果 item 包含 test_mode=True，自动添加测试标记
    """
    platform = item.get("platform", "未知平台")
    name = item.get("name", "未知型号")
    price = item.get("price", "未知价格")
    url = item.get("url", "")
    time = item.get("time", "")
    is_test = item.get("test_mode", False)

    lines = []

    if is_test:
        lines.append("🧪 <b>测试数据源 - iPhone 价格提醒</b>")
    else:
        lines.append("🚨 <b>iPhone 价格提醒</b>")

    lines.append("")
    lines.append(f"📱 型号：{name}")
    lines.append(f"💰 价格：{price}")
    lines.append(f"🏷️ 来源：{platform}")
    lines.append(f"🕒 发现时间：{time}")

    if price_changed:
        lines.append("📉 状态：价格下降！")

    if url:
        lines.append(f"🔗 点击查看")

    return "\n".join(lines)
