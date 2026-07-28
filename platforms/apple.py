# -*- coding: utf-8 -*-
"""
Apple 官方翻新商城数据获取 - V1.1.1
改用 JSON 解析方案（适配当前 Apple 页面结构）
"""

import requests
import re
import json
from datetime import datetime
from typing import List, Dict
import config

def _get_apple_domain(region: str) -> str:
    domains = {
        "CN": "https://www.apple.com.cn",
        "US": "https://www.apple.com",
        "HK": "https://www.apple.com/hk",
        "JP": "https://www.apple.com/jp",
    }
    return domains.get(region.upper(), "https://www.apple.com")

def _get_apple_refurb_url(region: str) -> str:
    if region.upper() == "CN":
        return "https://www.apple.com.cn/shop/refurbished/iphone"
    elif region.upper() == "US":
        return "https://www.apple.com/shop/refurbished/iphone"
    elif region.upper() == "HK":
        return "https://www.apple.com/hk/shop/refurbished/iphone"
    elif region.upper() == "JP":
        return "https://www.apple.com/jp/shop/refurbished/iphone"
    return "https://www.apple.com/shop/refurbished/iphone"

def _parse_initial_state(html: str) -> List[Dict]:
    """解析 __INITIAL_STATE__ JSON"""
    pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(1))
        products = data.get("products", [])
        if not products:
            products = data.get("refurbished", {}).get("products", [])
        return products
    except json.JSONDecodeError:
        return []

def _parse_next_data(html: str) -> List[Dict]:
    """解析 __NEXT_DATA__ JSON（Next.js 页面备用）"""
    pattern = r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>'
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(1))
        # 遍历查找商品数据
        def find_products(obj):
            if isinstance(obj, dict):
                if "products" in obj and isinstance(obj["products"], list):
                    return obj["products"]
                for value in obj.values():
                    result = find_products(value)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_products(item)
                    if result:
                        return result
            return None

        products = find_products(data)
        return products if products else []
    except json.JSONDecodeError:
        return []

def _extract_products_from_json(prod_list: List[Dict], domain: str, region: str) -> List[Dict]:
    """从 JSON 商品列表中提取统一格式"""
    products = []
    for prod in prod_list:
        try:
            name = prod.get("productTitle", "") or prod.get("title", "")
            if not name:
                continue

            price_info = prod.get("price", {})
            price_amount = price_info.get("amount", "0")
            currency = price_info.get("currency", "USD")

            if currency == "CNY":
                symbol = "¥"
            elif currency == "USD":
                symbol = "$"
            elif currency == "HKD":
                symbol = "HK$"
            else:
                symbol = "$"

            try:
                price_value = float(price_amount)
                price = f"{symbol}{int(price_value):,}" if price_value.is_integer() else f"{symbol}{price_value:,.2f}"
            except (ValueError, TypeError):
                price = f"{symbol}{price_amount}"

            url = prod.get("url", "")
            if url and not url.startswith("http"):
                url = domain + url

            capacity_match = re.search(r'(\d+GB)', name)
            capacity = capacity_match.group(1) if capacity_match else ""

            platform_name = "Apple官方翻新"
            if config.TEST_MODE:
                platform_name = "🧪 Apple官方翻新(测试)"

            products.append({
                "platform": platform_name,
                "name": name,
                "price": price,
                "url": url,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "capacity": capacity,
                "description": name,
                "region": region,
                "test_mode": config.TEST_MODE,
            })
        except Exception as e:
            print(f"⚠️ Apple JSON解析单个商品出错: {e}")
            continue
    return products

def fetch_apple_products() -> List[Dict]:
    """获取 Apple 官翻 iPhone 商品列表"""
    all_products = []
    regions = getattr(config, "APPLE_REGIONS", ["US"])

    for region in regions:
        url = _get_apple_refurb_url(region)
        domain = _get_apple_domain(region)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }

        try:
            print(f"⏳ 正在抓取 Apple {region.upper()} 站...")
            resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            resp.raise_for_status()
            html = resp.text
        except requests.RequestException as e:
            print(f"⚠️ Apple {region.upper()} 网络请求失败: {e}")
            continue

        # 1. 尝试 __INITIAL_STATE__ 解析
        prod_list = _parse_initial_state(html)
        if prod_list:
            print(f"✅ Apple {region.upper()} 使用 __INITIAL_STATE__ 解析成功")
            products = _extract_products_from_json(prod_list, domain, region)
            if products:
                print(f"✅ Apple {region.upper()} 抓取到 {len(products)} 个商品")
                all_products.extend(products)
                continue

        # 2. 尝试 __NEXT_DATA__ 解析
        prod_list = _parse_next_data(html)
        if prod_list:
            print(f"✅ Apple {region.upper()} 使用 __NEXT_DATA__ 解析成功")
            products = _extract_products_from_json(prod_list, domain, region)
            if products:
                print(f"✅ Apple {region.upper()} 抓取到 {len(products)} 个商品")
                all_products.extend(products)
                continue

        print(f"ℹ️ Apple {region.upper()} 未找到商品数据")

    return all_products
            
