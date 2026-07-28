# -*- coding: utf-8 -*-
"""
配置文件 - 所有可调参数集中管理
敏感信息通过环境变量注入，禁止硬编码
"""

import os
from typing import List, Optional

# ---------- 目标机型（关键词匹配） ----------
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

# ---------- 价格上限（单位：元） ----------
MAX_PRICE: int = 3500

# ---------- 容量过滤（留空表示不限） ----------
CAPACITY_FILTER: List[str] = ["256GB", "512GB"]

# ---------- 状态偏好（留空表示不限） ----------
STATUS_PREFERENCE: List[str] = []

# ---------- Telegram 通知开关 ----------
TELEGRAM_ENABLE: bool = True

# ---------- Apple 官翻地区 ----------
APPLE_REGION: str = "CN"

# ---------- 从环境变量读取敏感信息 ----------
TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    TELEGRAM_ENABLE = False
    print("⚠️ 警告：未设置 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID，Telegram 通知已禁用")
