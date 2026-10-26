# -*- coding: utf-8 -*-
"""
MacBook Air 官方翻新监控主程序。
流程：列表页发现候选 → 逐个查产品页确认有货（buyNowButton）→ 按档位/价格过滤
→ 对照状态文件去重 → 有货发 Telegram 通知 → 状态写回仓库。

与本地 watch_air.py 的区别：这里是 GitHub Actions 定时跑（每 10 分钟），
状态靠 git 提交持久化；不常驻、不占 token，通知直接走 Telegram。
"""

import time
from datetime import datetime

from . import config
from .apple_mac import FetchError, analyze_product, classify, fetch, parse_list
from .notifier import format_notification, send_telegram_message
from .storage import load_state, save_state


def _tier_for(chip):
    return next((t for t in config.TIERS if t["chip"] == chip), None)


def main():
    print("=" * 50)
    print(f"🕒 MacBook Air Refurb Hunter 启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    state = load_state()

    # 1. 列表页发现候选
    try:
        page, _ = fetch(config.LIST_URL)
    except FetchError as e:
        print(f"❌ 列表页抓取失败: {e}，本轮结束（下轮重试）")
        return
    discovered = parse_list(page)
    print(f"📦 列表页共 {len(discovered)} 个产品")

    watch = {}
    for pid, info in discovered.items():
        if not info.get("air_hint"):
            continue
        tier = _tier_for(info.get("chip"))
        if not tier:
            continue
        watch[pid] = {"list_price": info.get("price"), "chip": info.get("chip"),
                      "size": info.get("size"), "tier": tier}
    # 种子产品：列表页万一漏掉也能直接盯
    for pid in config.SEED_IDS:
        if pid not in watch:
            watch[pid] = {"list_price": config.SEED_PRICES.get(pid),
                          "chip": None, "size": None, "tier": None}
    print(f"🔍 待查候选: {len(watch)} 台（Air + M2/M3/M4）")

    # 2. 逐个查产品页，确认有货
    notify_items = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for pid, info in watch.items():
        url = config.PRODUCT_URL_TEMPLATE.format(pid=pid)
        try:
            page, final_url = fetch(url)
        except FetchError as e:
            print(f"⚠️ [{pid}] 产品页抓取失败: {e}")
            continue
        result = analyze_product(pid, page, final_url)
        if result["state"] == "gone":
            print(f"ℹ️ [{pid}] 已下架，从状态里删掉")
            state.pop(pid, None)
            continue
        title = result.get("title") or ""
        tier_name, chip, size, reason = classify(title)
        tier = _tier_for(chip) if chip else info.get("tier")
        if tier is None:
            print(f"ℹ️ [{pid}] {reason}，跳过")
            continue
        # 价格：产品页 > 列表页 > 种子价
        price = result.get("price") or info.get("list_price") or config.SEED_PRICES.get(pid)
        in_stock = result["state"] == "in_stock"
        prev = state.get(pid, {})
        if not in_stock:
            if prev.get("in_stock"):
                print(f"📉 [{pid}] {title} 已卖出")
            state[pid] = {"title": title, "price": price, "tier": tier["name"],
                          "in_stock": False, "updated_at": now}
            print(f"ℹ️ [{pid}] {title} 脱销")
            time.sleep(1)
            continue
        # 有货：先看价格是否在档位预算内
        if price is not None and price > tier["max_price"]:
            print(f"ℹ️ [{pid}] {title} 有货但超预算 ¥{price:,} > ¥{tier['max_price']:,}，不通知")
            state[pid] = {"title": title, "price": price, "tier": tier["name"],
                          "in_stock": True, "updated_at": now}
            time.sleep(1)
            continue
        # 价格未知按 ask 处理（下单前先核对）
        action = tier["action"] if price is not None else "ask"
        # 去重：同一台有货期间只通知一次；卖出后再上架、或价格变了才再通知
        if prev.get("in_stock") and prev.get("price") == price:
            print(f"ℹ️ [{pid}] {title} 已通知过，跳过")
            state[pid] = {"title": title, "price": price, "tier": tier["name"],
                          "in_stock": True, "updated_at": now}
            time.sleep(1)
            continue
        print(f"🚨 [{pid}] {title} 有货 ¥{price if price else '未知'}（{tier['name']}，{action}）")
        notify_items.append({"title": title, "price": price, "tier": tier["name"],
                             "action": action, "url": url, "time": now})
        state[pid] = {"title": title, "price": price, "tier": tier["name"],
                      "in_stock": True, "updated_at": now}
        time.sleep(1)

    # 3. 发 Telegram 通知
    if notify_items:
        print(f"📨 准备发送 {len(notify_items)} 条通知")
        for item in notify_items:
            msg = format_notification(item)
            ok = send_telegram_message(msg)
            print(f"{'✅ 已通知' if ok else '❌ 通知失败'}: {item.get('title')} - {item.get('price')}")
            time.sleep(1)
    else:
        print("ℹ️ 本轮没有需要通知的有货商品")

    # 4. 状态写回
    save_state(state)
    print("🎉 任务执行完毕")


if __name__ == "__main__":
    main()
