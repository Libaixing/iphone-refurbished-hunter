# -*- coding: utf-8 -*-
"""
平台模块
提供统一的商品获取接口
"""

from .apple import fetch_apple_products
from .jd import fetch_jd_products
from .aihuishou import fetch_aihuishou_products

__all__ = [
    "fetch_apple_products",
    "fetch_jd_products",
    "fetch_aihuishou_products"
]
