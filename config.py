# -*- coding: utf-8 -*-
"""
配置文件 - V1.1.0
"""

import os
from typing import List, Optional

# ---------- 目标机型 ----------
TARGET_MODELS: List[str] = [
    "iPhone 14 Pro",
    "iPhone 14 Pro Max",
    "iPhone 15 Pro",
    "iPhone 15 Pro Max",
    "iPhone 16 Pro",
    "iPhone 16 Pro Max",
    "iPhone 17",
    "iPhone 17 Pro",
    "iPhone 17 Pro Max"
]

# ---------- 价格上限（元） ----------
MAX_PRICE: int = 3500

# ---------- 容量过滤 ----------
CAPACITY_FILTER: List[str] = ["256GB", "512GB"]

# ---------- 状态偏好（留空表示不限） ----------
STATUS_PREFERENCE: List[str] = []

# ---------- Apple 官翻配置 ----------
APPLE_REGIONS: List[str] = ["US"]           # 支持: US, CN, JP, HK
TEST_MODE: bool = True                      # True: 通知带测试标记
TEST_MODE_PRICE_LIMIT: bool = False         # True: 测试模式也应用价格过滤

# ---------- 京东直链监控 ----------
JD_MONITOR_URLS: List[str] = [
    # 用户在此粘贴京东商品详情页链接
    # 示例: "https://item.jd.com/100000000000.html"
]

# ---------- Telegram ----------
TELEGRAM_ENABLE: bool = True

# ---------- 环境变量 ----------
TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    TELEGRAM_ENABLE = False
    print("⚠️ 未设置 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID，Telegram 通知已禁用")
