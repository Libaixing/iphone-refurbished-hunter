# -*- coding: utf-8 -*-
"""
MacBook Air 官翻页面抓取与解析。
逻辑直接取自本地验证过的 watch_air.py（2026-10-27 实测通过），只做结构适配：

- 有货信号只认产品页 buyNowButton 的 "disabled" 值：
  "disabled":false = 有货，"disabled":true = 脱销。
  按钮文字、页面别处的 "disabled":false 都不作数。
- 列表页只用来发现新产品 ID：靠 imageName（如 refurb-mba15-m4-skyblue-202503）
  判断是不是 Air、什么芯片，绝不用列表页判有货（列表更新慢，23:48 列表有、
  00:07 产品页已脱销的教训）。
"""

import gzip
import html as htmllib
import json
import re
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

from . import config

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

MIN_HTML_LEN = 2000
MIN_SANE_PRICE = 1000
MAX_SANE_PRICE = 50000


class FetchError(Exception):
    def __init__(self, msg, code=None):
        super().__init__(msg)
        self.code = code


def fetch(url: str) -> Tuple[str, str]:
    """Return (html, final_url). Raises FetchError unless we got a clean 200."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status, final_url = resp.status, resp.geturl()
            raw, enc = resp.read(), resp.headers.get("Content-Encoding", "")
    except urllib.error.HTTPError as e:
        raise FetchError(f"HTTP {e.code}", e.code)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise FetchError(f"network error: {e}")
    if status != 200:
        raise FetchError(f"HTTP {status}", status)
    if "gzip" in enc.lower():
        try:
            raw = gzip.decompress(raw)
        except OSError as e:
            raise FetchError(f"gzip decode failed: {e}")
    text = raw.decode("utf-8", errors="replace")
    if len(text) < MIN_HTML_LEN:
        raise FetchError(f"page too short ({len(text)} bytes), blocked/captcha?")
    return text, final_url


# ---------- buyNowButton 解析 ----------

def extract_balanced(s: str, start: int, limit: int = 20000) -> Optional[str]:
    """s[start] must be '{'. Return the balanced {...} text (string-aware) or None."""
    depth, in_str, esc = 0, False, False
    for i in range(start, min(len(s), start + limit)):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start:i + 1]
    return None


BUY_KEY_RE = re.compile(r'"buyNowButton"\s*:\s*\{')

def find_button_objects(page: str) -> List[str]:
    """All buyNowButton {...} objects. Also tries a backslash-unescaped copy."""
    for text in (page, page.replace('\\"', '"')):
        objs = []
        for m in BUY_KEY_RE.finditer(text):
            raw = extract_balanced(text, m.end() - 1)
            if raw:
                objs.append(raw)
        if objs:
            return objs
    return []


def parse_buy_state(page: str):
    """Return (state, detail, raw_objects). state: in_stock | sold_out | unknown."""
    objs = find_button_objects(page)
    if not objs:
        return "unknown", "buyNowButton JSON not found", []
    vals, fallback = [], False
    for raw in objs:
        v = None
        try:
            d = json.loads(raw)
            if isinstance(d, dict) and isinstance(d.get("disabled"), bool):
                v = d["disabled"]
        except ValueError:
            pass
        if v is None:
            m = re.search(r'"disabled"\s*:\s*(true|false)', raw)
            if m:
                v, fallback = (m.group(1) == "true"), True
        vals.append(v)
    tag = " (regex fallback)" if fallback else ""
    if any(v is None for v in vals):
        return "unknown", f"buyNowButton has no readable disabled flag{tag}", objs
    if all(v is False for v in vals):
        return "in_stock", f'buyNowButton "disabled":false x{len(vals)}{tag}', objs
    if all(v is True for v in vals):
        return "sold_out", f'buyNowButton "disabled":true x{len(vals)}{tag}', objs
    return "unknown", f"buyNowButton objects disagree: {vals}", objs


def parse_title(page: str) -> Optional[str]:
    m = re.search(r"<title[^>]*>(.*?)</title>", page, re.S | re.I)
    if not m:
        m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)', page, re.I)
    if not m:
        return None
    return htmllib.unescape(re.sub(r"\s+", " ", m.group(1))).strip()


PAGE_PRICE_PATTERNS = [
    r'"currentPrice"\s*:\s*\{[^{}]*?"amount"\s*:\s*"?([\d,]+(?:\.\d+)?)',
    r'"priceCurrency"\s*:\s*"CNY"\s*,\s*"price"\s*:\s*"?([\d.]+)',
    r'"price"\s*:\s*"?([\d.]+)"?\s*,\s*"priceCurrency"\s*:\s*"CNY"',
]

def parse_page_price(page: str):
    """Return (price:int|None, pattern_index|None). JSON fields only, never free text."""
    for text in (page, page.replace('\\"', '"')):
        for i, pat in enumerate(PAGE_PRICE_PATTERNS):
            m = re.search(pat, text)
            if m:
                try:
                    v = int(float(m.group(1).replace(",", "")))
                except ValueError:
                    continue
                if MIN_SANE_PRICE <= v <= MAX_SANE_PRICE:
                    return v, i
    return None, None


def classify(title: Optional[str]):
    """Return (tier_name|None, chip|None, size|None, reason)."""
    if not title or "MacBook Air" not in title:
        return None, None, None, "not a MacBook Air"
    m = re.search(r"Apple\s+(M\d+)\b", title)
    chip = m.group(1) if m else None
    size = re.search(r"(\d+)\s*英寸", title)
    size = size.group(1) if size else None
    tier = next((t for t in config.TIERS if t["chip"] == chip), None)
    if tier is None:
        return None, chip, size, f"chip {chip} not tracked"
    if config.ALLOWED_SIZES and size not in config.ALLOWED_SIZES:
        return None, chip, size, f"size {size} not allowed"
    return tier["name"], chip, size, ""


# ---------- 列表页解析（只用来发现新产品 ID） ----------

PID_RE = re.compile(r"/shop/product/([A-Za-z0-9]+)/a")
LIST_PRICE_RE = re.compile(r"RMB\s*([\d,]+(?:\.\d+)?)")
IMG_RE = re.compile(r'"imageName"\s*:\s*"([^"]+)"')
MBA_IMG_RE = re.compile(r"refurb-mba(\d+)-(m\d+)-", re.I)

def parse_list(page: str) -> Dict[str, Dict]:
    """Return {pid: {"price": int|None, "air_hint": bool, "chip": str|None,
    "size": str|None}}. Used for DISCOVERY only, never for stock status."""
    firsts = {}
    for m in PID_RE.finditer(page):
        firsts.setdefault(m.group(1), m.start())
    ordered = sorted(firsts.items(), key=lambda kv: kv[1])
    imgs = [(m.start(), m.group(1)) for m in IMG_RE.finditer(page)]
    out = {}
    for i, (pid, pos) in enumerate(ordered):
        end = ordered[i + 1][1] if i + 1 < len(ordered) else len(page)
        pm = LIST_PRICE_RE.search(page[pos:min(end, pos + 3000)])
        price = int(float(pm.group(1).replace(",", ""))) if pm else None
        img = None
        for ipos, name in reversed(imgs):
            if ipos < pos:
                img = name
                break
        hint = chip = size = None
        if img:
            mm = MBA_IMG_RE.search(img)
            if mm:
                hint, size, chip = True, mm.group(1), mm.group(2).upper()
        if hint is None:
            hint = "MacBook Air" in page[max(0, pos - 600):pos + 600]
        out[pid] = {"price": price, "air_hint": bool(hint), "chip": chip, "size": size}
    return out


def analyze_product(pid: str, page: str, final_url: str) -> Dict:
    """Pure analysis of one product page."""
    if pid not in final_url:
        return {"state": "gone", "detail": f"redirected to {final_url}", "title": None,
                "price": None, "price_pat": None, "objs": []}
    state, detail, objs = parse_buy_state(page)
    price, pat = parse_page_price(page)
    title = parse_title(page)
    return {"state": state, "detail": detail, "title": title,
            "price": price, "price_pat": pat, "objs": objs}
