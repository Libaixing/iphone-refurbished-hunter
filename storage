# -*- coding: utf-8 -*-
"""
历史记录管理模块
负责保存已发现商品，避免重复通知，并检测价格变动
"""

import json
import os
from typing import List, Dict

# 历史数据文件路径
HISTORY_FILE = "data/history.json"

def _ensure_data_dir() -> None:
    """确保 data 目录存在"""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

def load_history() -> List[Dict]:
    """
    从文件加载历史记录
    若文件不存在或格式错误，返回空列表
    """
    _ensure_data_dir()
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ 读取历史文件失败: {e}，将重新初始化")
        return []

def save_history(history: List[Dict]) -> None:
    """将历史记录写入文件"""
    _ensure_data_dir()
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"❌ 保存历史文件失败: {e}")

def add_record(record: Dict) -> None:
    """
    添加一条新记录到历史，并自动保存
    record 应包含: name, price, url, platform, time
    """
    history = load_history()
    # 避免存储重复（完全相同的 name+price）
    if not any(
        item.get("name") == record.get("name") and
        item.get("price") == record.get("price")
        for item in history
    ):
        history.append(record)
        save_history(history)

def is_duplicate(item: Dict) -> bool:
    """
    检查商品是否已存在且价格未变
    返回 True 表示重复（不通知），False 表示新商品或价格变动
    """
    history = load_history()
    for old in history:
        if old.get("name") == item.get("name"):
            if old.get("price") == item.get("price"):
                return True
            else:
                return False
    return False

def get_price_history(name: str) -> List[float]:
    """获取某个商品的历史价格列表"""
    history = load_history()
    prices = []
    for record in history:
        if record.get("name") == name:
            try:
                prices.append(float(record.get("price", "0").replace("¥", "").replace("$", "").replace(",", "")))
            except (ValueError, AttributeError):
                continue
    return prices
