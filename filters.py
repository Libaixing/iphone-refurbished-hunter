# -*- coding: utf-8 -*-
"""
商品过滤模块 - V1.1.0
"""

from typing import List, Dict
import config
import re

def extract_capacity(name: str) -> str:
    match = re.search(r'(\d+GB)', name, re.IGNORECASE)
    return match.group(1) if match else ""

def extract_price(price_str: str) -> float:
    if not price_str:
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def match_model(name: str) -> bool:
    for model in config.TARGET_MODELS:
        if model.lower() in name.lower():
            return True
    return False

def match_capacity(name: str) -> bool:
    if not config.CAPACITY_FILTER:
        return True
    cap = extract_capacity(name)
    if not cap:
        return True
    return cap in config.CAPACITY_FILTER

def match_status(description: str) -> bool:
    if not config.STATUS_PREFERENCE:
        return True
    desc_lower = description.lower()
    for keyword in config.STATUS_PREFERENCE:
        if keyword.lower() in desc_lower:
            return True
    return False

def filter_products(products: List[Dict]) -> List[Dict]:
    """
    对商品列表进行综合过滤
    测试模式下跳过价格过滤（$ 价格不受 MAX_PRICE 限制）
    """
    filtered = []
    for item in products:
        name = item.get("name", "")
        price_str = item.get("price", "0")
        price = extract_price(price_str)
        description = item.get("description", name)
        is_test = item.get("test_mode", False)

        if not match_model(name):
            continue

        # 价格过滤：测试模式跳过（或由 TEST_MODE_PRICE_LIMIT 控制）
        if config.TEST_MODE and not config.TEST_MODE_PRICE_LIMIT:
            pass  # 测试模式下跳过价格过滤
        elif price > config.MAX_PRICE:
            continue

        if not match_capacity(name):
            continue
        if not match_status(description):
            continue

        filtered.append(item)

    return filtered
