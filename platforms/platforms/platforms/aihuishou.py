# -*- coding: utf-8 -*-
"""
爱回收数据获取（V1.0 增强版）
定位：辅助备用数据源
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import re
import random
import time

AIHUISHOU_SEARCH_URL = "https://www.aihuishou.com/search"

AIHUISHOU_KEYWORDS = [
    "iPhone 14 Pro Max",
    "iPhone 15 Pro Max",
    "iPhone 16 Pro Max",
    "iPhone 官翻",
]

def fetch_aihuishou_products() -> List[Dict]:
    """获取爱回收 iPhone 商品信息"""
    all_products = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.aihuishou.com/",
    }

    for keyword in AIHUISHOU_KEYWORDS:
        time.sleep(random.uniform(1, 2))

        params = {
            "keyword": keyword,
            "page": 1,
        }

        try:
            resp = requests.get(AIHUISHOU_SEARCH_URL, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            html = resp.text
        except requests.RequestException as e:
            print(f"⚠️ 爱回收网络请求失败（关键词：{keyword}）: {e}")
            continue

        # 验证码检测
        if "验证" in html or "security" in html.lower():
            print(f"⚠️ 爱回收触发验证（关键词：{keyword}），跳过")
            continue

        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception as e:
            print(f"⚠️ 爱回收页面解析异常（关键词：{keyword}）: {e}")
            continue

        # 多选择器备用
        items = soup.select(".product-item")
        if not items:
            items = soup.select(".goods-item")
        if not items:
            items = soup.select(".item")
        if not items:
            items = soup.select(".product")
        if not items:
            items = soup.select(".goods")
        if not items:
            print(f"⚠️ 爱回收未找到商品列表（关键词：{keyword}）")
            continue

        for item in items:
            try:
                name_elem = item.select_one(".product-name") or item.select_one(".goods-name") or item.select_one(".name") or item.select_one(".title")
                price_elem = item.select_one(".product-price") or item.select_one(".price") or item.select_one(".sale-price")
                url_elem = item.select_one("a")

                if not name_elem or not price_elem:
                    continue

                name = name_elem.get_text(strip=True)
                price_text = price_elem.get_text(strip=True)
                price_clean = re.sub(r'[^\d.]', '', price_text)
                if price_clean:
                    try:
                        price_value = float(price_clean)
                        if price_value.is_integer():
                            price = f"¥{int(price_value):,}"
                        else:
                            price = f"¥{price_value:,.2f}"
                    except ValueError:
                        price = f"¥{price_text}"
                else:
                    price = f"¥{price_text}"

                url = ""
                if url_elem:
                    href = url_elem.get("href")
                    if href:
                        if href.startswith("//"):
                            url = "https:" + href
                        elif href.startswith("/"):
                            url = "https://www.aihuishou.com" + href
                        elif not href.startswith("http"):
                            url = "https://www.aihuishou.com/" + href.lstrip("/")
                        else:
                            url = href

                time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                capacity_match = re.search(r'(\d+GB)', name)
                capacity = capacity_match.group(1) if capacity_match else ""

                all_products.append({
                    "platform": "爱回收",
                    "name": name,
                    "price": price,
                    "url": url,
                    "time": time_now,
                    "capacity": capacity,
                    "description": name,
                })
            except Exception as e:
                print(f"⚠️ 爱回收解析单个商品出错: {e}")
                continue

    # 去重
    seen = set()
    unique_products = []
    for p in all_products:
        key = (p.get("name"), p.get("price"))
        if key not in seen:
            seen.add(key)
            unique_products.append(p)

    print(f"✅ 爱回收总计抓取到 {len(unique_products)} 个去重商品")
    return unique_products
