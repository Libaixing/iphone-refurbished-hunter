# -*- coding: utf-8 -*-
"""
京东二手/拍拍数据获取（V1.0 增强版）
定位：辅助数据源
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import re
import random
import time

JD_SEARCH_BASE = "https://search.jd.com/Search"

# 精简关键词，减少请求压力
JD_KEYWORDS = [
    "iPhone 14 Pro Max 二手",
    "iPhone 15 Pro Max 二手",
    "iPhone 16 Pro Max 二手",
    "iPhone 官翻",
]

def fetch_jd_products() -> List[Dict]:
    """获取京东二手 iPhone 商品信息"""
    all_products = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.jd.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    for keyword in JD_KEYWORDS:
        time.sleep(random.uniform(1, 3))

        params = {
            "keyword": keyword,
            "enc": "utf-8",
            "wq": keyword,
            "page": 1,
            "s": "1",
            "click": "0",
        }

        try:
            resp = requests.get(JD_SEARCH_BASE, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
            html = resp.text
        except requests.RequestException as e:
            print(f"⚠️ 京东网络请求失败（关键词：{keyword}）: {e}")
            continue

        # 验证码检测
        if "验证码" in html or "verify" in html.lower() or "请打开京东" in html:
            print(f"⚠️ 京东触发验证码（关键词：{keyword}），跳过")
            continue

        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception as e:
            print(f"⚠️ 京东页面解析异常（关键词：{keyword}）: {e}")
            continue

        items = soup.select("#J_goodsList .gl-item")
        if not items:
            items = soup.select(".gl-item")
        if not items:
            print(f"⚠️ 京东未找到商品列表（关键词：{keyword}）")
            continue

        for item in items:
            try:
                name_elem = item.select_one(".p-name em")
                if not name_elem:
                    name_elem = item.select_one(".p-name a")
                if not name_elem:
                    continue
                name = name_elem.get_text(strip=True)

                # 价格解析：优先 .price，其次 strong，最后父节点
                price_elem = item.select_one(".p-price .price")
                if not price_elem:
                    price_elem = item.select_one(".p-price strong")
                if not price_elem:
                    price_parent = item.select_one(".p-price")
                    if price_parent:
                        price_elem = price_parent
                if not price_elem:
                    continue

                price_text = price_elem.get_text(strip=True)
                price_clean = re.sub(r'[^\d.]', '', price_text)
                if not price_clean:
                    continue
                try:
                    price_value = float(price_clean)
                    if price_value.is_integer():
                        price = f"¥{int(price_value):,}"
                    else:
                        price = f"¥{price_value:,.2f}"
                except ValueError:
                    price = f"¥{price_text}"

                url_elem = item.select_one(".p-name a")
                url = ""
                if url_elem:
                    href = url_elem.get("href")
                    if href:
                        if href.startswith("//"):
                            url = "https:" + href
                        elif href.startswith("/"):
                            url = "https://item.jd.com" + href
                        elif not href.startswith("http"):
                            url = "https://item.jd.com/" + href.lstrip("/")
                        else:
                            url = href

                time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                capacity_match = re.search(r'(\d+GB)', name)
                capacity = capacity_match.group(1) if capacity_match else ""

                all_products.append({
                    "platform": "京东二手",
                    "name": name,
                    "price": price,
                    "url": url,
                    "time": time_now,
                    "capacity": capacity,
                    "description": name,
                })
            except Exception as e:
                print(f"⚠️ 京东解析单个商品出错: {e}")
                continue

    # 去重
    seen = set()
    unique_products = []
    for p in all_products:
        key = (p.get("name"), p.get("price"))
        if key not in seen:
            seen.add(key)
            unique_products.append(p)

    print(f"✅ 京东总计抓取到 {len(unique_products)} 个去重商品")
    return unique_products
