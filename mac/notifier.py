# -*- coding: utf-8 -*-
"""
Telegram 通知模块（MacBook Air 官翻版）。
与 iphone-refurbished-hunter 的 notifier.py 同一套 Secrets：
TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID，仓库 Settings → Secrets 里已配好。
"""

import requests
from typing import Dict

from . import config


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
        "parse_mode": "HTML",
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


def format_notification(item: Dict) -> str:
    """item: {title, price, tier, action, url, time}"""
    title = item.get("title", "未知型号")
    price = item.get("price")
    price_str = f"¥{price:,}" if isinstance(price, int) else "价格未知"
    tier = item.get("tier", "")
    action = item.get("action", "ask")
    url = item.get("url", "")
    when = item.get("time", "")

    lines = []
    if action == "buy":
        lines.append("🚨 <b>MacBook Air 翻新到货（可直接买）</b>")
    else:
        lines.append("💡 <b>MacBook Air 翻新备选（先确认再买）</b>")
    lines.append("")
    lines.append(f"💻 型号：{title}")
    lines.append(f"💰 价格：{price_str}")
    lines.append(f"🏷️ 档位：{tier}")
    if action == "buy":
        lines.append("✅ 状态：在预算内，有货，可以直接下单")
    else:
        if price is None:
            lines.append("⚠️ 状态：有货，但价格没读到，下单前先在官网核对价格")
        else:
            lines.append("⚠️ 状态：有货，是备选档位（M3/M2），买之前先确认")
    lines.append(f"🕒 发现时间：{when}")
    if url:
        lines.append(f"🔗 <a href=\"{url}\">点击查看</a>")
    return "\n".join(lines)
