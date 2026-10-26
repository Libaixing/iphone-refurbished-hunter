# -*- coding: utf-8 -*-
"""
MacBook Air 官方翻新监控 - 配置
盯苹果中国官网翻新店的 MacBook Air（M4 / M3 / M2），有货发 Telegram 通知。
模式与 iphone-refurbished-hunter 一致：GitHub Actions 定时跑，跑完把状态写回仓库。
"""

import os
from typing import List, Optional

# ---------- 官翻列表页 ----------
LIST_URL = "https://www.apple.com.cn/shop/refurbished/mac"
PRODUCT_URL_TEMPLATE = "https://www.apple.com.cn/shop/product/{pid}/a"

# ---------- 档位：芯片 -> 价格上限（元）与动作 ----------
# buy: 在预算内，可直接买；ask: 备选，先问用户再决定
TIERS = [
    {"chip": "M4", "name": "M4", "max_price": 6499, "action": "buy"},
    {"chip": "M3", "name": "M3", "max_price": 5500, "action": "ask"},
    {"chip": "M2", "name": "M2", "max_price": 4500, "action": "ask"},
]

# 只盯 13 / 15 英寸（Air 只有这两个尺寸，写死防误伤）
ALLOWED_SIZES = {"13", "15"}

# ---------- 种子产品（列表页万一漏掉也能直接盯） ----------
# fc6t4ch: 翻新 13 英寸 MacBook Air M4，天蓝色，¥6,499
SEED_IDS = ["fc6t4ch"]
SEED_PRICES = {"fc6t4ch": 6499}

# ---------- 状态文件（跑完写回仓库，跨轮去重用） ----------
STATE_FILE = "data/mac_state.json"

# ---------- Telegram ----------
TELEGRAM_ENABLE = True

# ---------- 环境变量（GitHub Secrets 注入） ----------
TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    TELEGRAM_ENABLE = False
    print("⚠️ 未设置 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID，Telegram 通知已禁用")
