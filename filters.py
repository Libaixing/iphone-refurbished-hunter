# -*- coding: utf-8 -*-
"""
商品过滤模块
根据 config.py 中的规则筛选出符合条件的商品
"""

from typing import List, Dict
import config
import re

def extract_capacity(name: str) -> str:
    """从商品名称中提取容量（如 256GB、512GB）"""
    match = re.search(r'(\d+GB)', name, re.IGNORECASE)
    return match.group(1) if match else ""

def extract_price(price_str: str) -> float:
    """
    将价格字符串转换为浮点数
    处理 "¥3,299" 或 "3299" 等格式
    """
    if not price_str:
        return 0.0
    cleaned = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def match_model(name: str) -> bool:
    """检查商品名称是否匹配任意目标机型"""
    for model in config.TARGET_MODELS:
        if model.lower() in name.lower():
            return True
    return False

def match_capacity(name: str) -> bool:
    """容量过滤"""
    if not config.CAPACITY_FILTER:
        return True
    cap = extract_capacity(name)
    if not cap:
        return True  # 无法提取容量时默认通过（宽松模式）
    return cap in config.CAPACITY_FILTER

def match_status(description: str) -> bool:
    """状态过滤：根据描述中的关键词判断是否满足偏好"""
    if not config.STATUS_PREFERENCE:
        return True
    desc_lower = description.lower()
    for keyword in config.STATUS_PREFERENCE:
        if keyword.lower() in desc_lower:
            return True
    return False

def filter_products(products: List[Dict]) -> List[Dict]:
    """对商品列表进行综合过滤，返回符合条件的商品列表"""
    filtered = []
    for item in products:
        name = item.get("name", "")
        price_str = item.get("price", "0")
        price = extract_price(price_str)
        description = item.get("description", name)

        if not match_model(name):
            continue
        if price > config.MAX_PRICE:
            continue
        if not match_capacity(name):
            continue
        if not match_status(description):
            continue

        filtered.append(item)

    return filtered
