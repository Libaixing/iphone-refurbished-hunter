# -*- coding: utf-8 -*-
"""
iPhone Refurbished Hunter 主程序
负责协调各模块，完成监控、过滤、通知、存储
"""

import time
from datetime import datetime
import config
from storage import load_history, add_record, is_duplicate
from filters import filter_products, extract_price
from notifier import send_telegram_message, format_notification
from platforms import fetch_apple_products, fetch_jd_products, fetch_aihuishou_products

def main():
    print("=" * 50)
    print(f"🕒 iPhone Refurbished Hunter 启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 1. 从所有平台抓取商品
    all_products = []
    fetch_functions = [
        ("Apple", fetch_apple_products),
        ("京东", fetch_jd_products),
        ("爱回收", fetch_aihuishou_products),
    ]

    for name, func in fetch_functions:
        try:
            print(f"⏳ 正在抓取 {name}...")
            products = func()
            if products:
                all_products.extend(products)
                print(f"✅ {name} 获取 {len(products)} 条")
            else:
                print(f"ℹ️ {name} 未返回商品")
        except Exception as e:
            print(f"❌ {name} 抓取异常: {e}")

    if not all_products:
        print("⚠️ 所有平台均未获取到商品，程序结束")
        return

    print(f"📦 总计获取商品数: {len(all_products)}")

    # 2. 过滤商品
    filtered = filter_products(all_products)
    print(f"🔍 过滤后符合条件商品数: {len(filtered)}")

    if not filtered:
        print("ℹ️ 无符合过滤条件的商品")
        return

    # 3. 检查历史并准备通知
    new_items = []
    price_drop_items = []
    for item in filtered:
        name = item.get("name", "")
        price = item.get("price", "")
        if not name:
            continue

        if is_duplicate(item):
            # 检查是否为价格下降
            history = load_history()
            old_prices = []
            for h in history:
                if h.get("name") == name:
                    try:
                        old_prices.append(float(h.get("price", "0").replace("¥", "").replace("$", "").replace(",", "")))
                    except (ValueError, AttributeError):
                        continue
            if old_prices:
                old_min = min(old_prices)
                current_price = extract_price(price)
                if current_price < old_min:
                    price_drop_items.append(item)
        else:
            new_items.append(item)

    notify_items = new_items + price_drop_items
    seen = set()
    unique_notify = []
    for item in notify_items:
        key = (item.get("name"), item.get("price"))
        if key not in seen:
            seen.add(key)
            unique_notify.append(item)

    if not unique_notify:
        print("ℹ️ 没有需要通知的新商品或价格变动")
        for item in filtered:
            add_record(item)
        return

    # 4. 发送 Telegram 通知
    print(f"📨 准备发送 {len(unique_notify)} 条通知")
    for item in unique_notify:
        price_drop = item in price_drop_items
        msg = format_notification(item, price_changed=price_drop)
        success = send_telegram_message(msg)
        if success:
            print(f"✅ 已通知: {item.get('name')} - {item.get('price')}")
        else:
            print(f"❌ 通知失败: {item.get('name')}")
        time.sleep(1)

    # 5. 保存历史
    for item in filtered:
        add_record(item)

    print("🎉 任务执行完毕")

if __name__ == "__main__":
    main()


