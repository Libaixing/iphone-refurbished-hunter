# -*- coding: utf-8 -*-
"""
Mac 监控状态管理：{product_id: {title, price, tier, action, in_stock, updated_at}}
- 同一台在有货期间只通知一次（避免每 10 分钟重复发）。
- 卖出后 in_stock 记为 False，之后重新上架会再次通知。
- 下架（gone）的产品从状态里删掉，之后再出现当新的处理。
状态文件跑完写回仓库，跨轮持久化。
"""

import json
import os
from typing import Dict

from . import config

STATE_FILE = config.STATE_FILE


def _ensure_data_dir() -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)


def load_state() -> Dict:
    _ensure_data_dir()
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ 读取状态文件失败: {e}，将重新初始化")
        return {}


def save_state(state: Dict) -> None:
    _ensure_data_dir()
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"❌ 保存状态文件失败: {e}")
