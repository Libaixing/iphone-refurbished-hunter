# -*- coding: utf-8 -*-
"""
Apple 官方翻新商城数据获取（V1.0.1 修正版）
"""

import requests
import re
import json
from datetime import datetime
from typing import List, Dict
import config

def _get_apple_domain() -> str:
    region = getattr(config, "APPLE_REGION", "CN").upper()
    domains = {
        "CN": "https://www.apple.com.cn",
        "US": "https://www.apple.com",
        "HK": "https://www.apple.com/hk",
        "JP": "https://www.apple.com/jp",
    }
    return domains.get(region, "https://www.apple.com.cn")

def _get_apple_refurb_url() -> str:
    region = getattr(config, "APPLE_REGION", "CN").upper()
    if region == "CN":
        return "https://www.apple.com.cn/shop/refurbished/iphone"
    elif region == "US":
        return "https://www.apple.com/shop/refurbished/iphone"
    elif region == "HK":
        return "https://www.apple.com/hk/shop/refurbished/iphone"
    elif region == "JP":
        return "https://www.apple.com/jp/shop/refurbished/iphone"
    return "https://www.apple.com/shop/refurbished/iphone"

def _parse_initial_state(html: str) -> List[Dict]:
    pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    product_list = data.get("products", [])
    if not product_list:
        product_list = data.get("refurbished", {}).get("products", [])
    return product_list

def _parse_static_html(html: str, domain: str) -> List[Dict]:
    from bs4 import BeautifulSoup
    products = []
    soup = BeautifulSoup(html, "lxml")
    items = soup.select(".product-item")
    if not items:
        items = soup.select(".rf-refurbished-product")
    if not items:
        items = soup.select("[data-product-id]")
    if not items:
        items = soup.select(".product-card")
    for item in items:
        try:
            name_elem = item.select_one(".product-title") or item.select_one(".title") or item.select_one("h3")
            if not name_elem:
                continue
            name = name_elem.get_text(strip=True)
            price_elem = item.select_one(".price") or item.select_one(".product-price") or item.select_one(".amount")
            if not price_elem:
                continue
            price_text = price_elem.get_text(strip=True)
            price_clean = re.sub(r'[^\d.]', '', price_text)
            if price_clean:
                try:
                    price_value = float(price_clean)
                    price = f"¥{int(price_value):,}" if price_value.is_integer() else f"¥{price_value:,.2f}"
                except ValueError:
                    price = f"¥{price_text}"
            else:
                price = f"¥{price_text}"
            url_elem = item.select_one("a")
            url = ""
            if url_elem:
                href = url_elem.get("href")
                if href:
                    if href.startswith("//"):
                        url = "https:" + href
                    elif href.startswith("/"):
                        url = domain + href
                    elif not href.startswith("http"):
                        url = domain + "/" + href.lstrip("/")
                    else:
                        url = href
            capacity_match = re.search(r'(\d+GB)', name)
            capacity = capacity_match.group(1) if capacity_match else ""
            time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            products.append({
                "platform": "Apple官方翻新",
                "name": name,
                "price": price,
                "url": url,
                "time": time_now,
                "capacity": capacity,
                "description": name,
            })
        except Exception as e:
            print(f"⚠️ Apple HTML解析单个商品出错: {e}")
            continue
    return products

def fetch_apple_products() -> List[Dict]:
    url = _get_apple_refurb_url()
    domain = _get_apple_domain()
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text
    except requests.RequestException as e:
        print(f"⚠️ Apple 网络请求失败: {e}")
        return []
    product_list = _parse_initial_state(html)
    if product_list:
        print("✅ Apple 使用 __INITIAL_STATE__ 解析成功")
        products = []
        for prod in product_list:
            try:
                name = prod.get("productTitle", "") or prod.get("title", "")
                price_info = prod.get("price", {})
                price_amount = price_info.get("amount", "0")
                currency = price_info.get("currency", "")
                if currency.upper() == "CNY":
                    symbol = "¥"
                elif currency.upper() == "USD":
                    symbol = "$"
                elif currency.upper() == "HKD":
                    symbol = "HK$"
                else:
                    symbol = ""
                try:
                    price_value = float(price_amount)
                    price = f"{symbol}{int(price_value):,}" if price_value.is_integer() else f"{symbol}{price_value:,.2f}"
                except (ValueError, TypeError):
                    price = f"{symbol}{price_amount}"
                prod_url = prod.get("url", "")
                if prod_url and not prod_url.startswith("http"):
                    prod_url = domain + prod_url
                time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                capacity_match = re.search(r'(\d+GB)', name)
                capacity = capacity_match.group(1) if capacity_match else ""
                products.append({
                    "platform": "Apple官方翻新",
                    "name": name,
                    "price": price,
                    "url": prod_url,
                    "time": time_now,
                    "capacity": capacity,
                    "description": name,
                })
            except Exception as e:
                print(f"⚠️ Apple JSON解析单个商品出错: {e}")
                continue
        print(f"✅ Apple 抓取到 {len(products)} 个商品")
        return products
    print("ℹ️ __INITIAL_STATE__ 未找到，尝试 HTML 静态解析...")
    products = _parse_static_html(html, domain)
    if products:
        print(f"✅ Apple 通过 HTML 静态解析抓取到 {len(products)} 个商品")
    else:
        print("⚠️ Apple 官翻页面解析失败，可能页面结构已变化")
        print(f"💡 提示：请手动访问验证：{url}")
    return products
