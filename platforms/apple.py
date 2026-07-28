# -*- coding: utf-8 -*-
"""
Apple 官方翻新商城数据获取 - V1.1.0
支持多地区（US/CN/JP/HK），当前以 US 为测试源
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import re
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

def _parse_product_from_markdown(text: str, domain: str, region: str) -> List[Dict]:
    """解析 Apple 美国站 Markdown 风格的 ### 商品标题"""
    products = []
    blocks = re.split(r'###\s*', text)

    for block in blocks:
        if not block.strip():
            continue
        try:
            name_match = re.search(r'\[(.*?)\]', block)
            if not name_match:
                continue
            name = name_match.group(1).strip()

            if "..." in name:
                continue

            url_match = re.search(r'\((https?://[^\)]+)\)', block)
            if not url_match:
                continue
            url = url_match.group(1)
            if url and not url.startswith("http"):
                url = domain + url

            price_match = re.search(r'Now\s*\$([\d,]+(?:\.\d{2})?)', block)
            if not price_match:
                continue
            price_value = float(price_match.group(1).replace(',', ''))
            price = f"${int(price_value):,}" if price_value.is_integer() else f"${price_value:,.2f}"

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
            print(f"⚠️ Apple Markdown解析单个商品出错: {e}")
            continue

    return products

def _parse_product_from_html(html: str, domain: str, region: str) -> List[Dict]:
    """HTML 备用解析，当 Markdown 解析失败或不完整时使用"""
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
                    price = f"${int(price_value):,}" if price_value.is_integer() else f"${price_value:,.2f}"
                except ValueError:
                    price = f"${price_text}"
            else:
                price = f"${price_text}"

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
            print(f"⚠️ Apple HTML解析单个商品出错: {e}")
            continue

    return products

def fetch_apple_products() -> List[Dict]:
    """获取 Apple 官翻 iPhone 商品列表（支持多地区）"""
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

        # 1. 先尝试 Markdown 解析
        soup = BeautifulSoup(html, "lxml")
        page_text = soup.get_text()
        products = _parse_product_from_markdown(page_text, domain, region)

        # 2. 如果 Markdown 解析结果为空，尝试 HTML 解析
        if not products:
            print(f"ℹ️ Apple {region.upper()} Markdown解析无结果，尝试HTML解析...")
            products = _parse_product_from_html(html, domain, region)

        if products:
            print(f"✅ Apple {region.upper()} 抓取到 {len(products)} 个商品")
            all_products.extend(products)
        else:
            print(f"ℹ️ Apple {region.upper()} 未找到商品")

    return all_products
