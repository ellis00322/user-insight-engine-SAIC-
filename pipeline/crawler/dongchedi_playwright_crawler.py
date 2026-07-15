"""
懂车帝车主口碑抓取 —— Playwright 版

口碑页每页有独立 URL：
    https://www.dongchedi.com/auto/series/score/{series_id}-x-S0-x-x-x-{page}
页面首屏数据是 Next.js 服务端直出（嵌在 __NEXT_DATA__ 里），不需要登录会话
持续存活、不需要点击翻页——每页单次打开、解析、关闭浏览器即可，逐页构造
URL 即可批量抓取。

用法：
    python pipeline/crawler/dongchedi_playwright_crawler.py --series_id 9660 --max_pages 20

字段解析逻辑见 dongchedi_parsing.py。
"""

import argparse
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from dongchedi_parsing import extract_next_data_review_list, parse_review_item

load_dotenv()

log = logging.getLogger("dongchedi_playwright_crawler")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def random_delay(min_sec: float = 1.5, max_sec: float = 3.0) -> None:
    time.sleep(random.uniform(min_sec, max_sec))


def try_extract_ssr_page(page, retries: int = 12, interval_ms: int = 1500) -> Optional[list]:
    """
    页面刚 commit 时 __NEXT_DATA__ 里的数据还没渲染齐，需要轮询重试。
    """
    for _ in range(retries):
        page.wait_for_timeout(interval_ms)
        try:
            html = page.content()
        except Exception:
            continue
        items = extract_next_data_review_list(html)
        if items:
            return items
    return None


def cookie_string_to_playwright(cookie_str: str, domain: str = ".dongchedi.com") -> list:
    """把 'k1=v1; k2=v2' 形式的 Cookie 请求头字符串转成 context.add_cookies() 需要的格式。"""
    cookies = []
    for part in cookie_str.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        cookies.append({"name": name.strip(), "value": value.strip(), "domain": domain, "path": "/"})
    return cookies


def load_existing_review_ids(out_path: Path) -> set:
    """读已有输出文件里的 review_id，用于跨批次去重（同一车型分多次抓取时不重复写入）。"""
    existing = set()
    if not out_path.exists():
        return existing
    with out_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rid = json.loads(line).get("review_id")
            except json.JSONDecodeError:
                continue
            if rid:
                existing.add(rid)
    return existing


def append_reviews_deduped(out_path: Path, series_id: str, items_by_page: dict) -> int:
    """按 review_id（懂车帝帖子 ID，非用户 ID）去重后追加写入，返回实际新写入条数。"""
    existing_ids = load_existing_review_ids(out_path)
    written = 0
    with out_path.open("a", encoding="utf-8") as f:
        for page_no in sorted(items_by_page):
            for item in items_by_page[page_no]:
                parsed = parse_review_item(item, series_id)
                rid = parsed.get("review_id")
                if rid and rid in existing_ids:
                    continue
                if rid:
                    existing_ids.add(rid)
                f.write(json.dumps(parsed, ensure_ascii=False) + "\n")
                written += 1
    return written


def fetch_one_page(p, series_id: str, page_no: int, cookie_str: str) -> Optional[list]:
    """
    每一页都开全新浏览器实例单次读取——同一个浏览器里连续导航多次会偶发触发
    懂车帝的 SSO 周期性登出（实测确认与是否点击无关，纯打开页面停留也会触发）。
    全新实例、单次读取就走，是唯一验证稳定的模式。
    """
    url = f"https://www.dongchedi.com/auto/series/score/{series_id}-x-S0-x-x-x-{page_no}"
    browser = p.chromium.launch(headless=True)
    try:
        context = browser.new_context(
            user_agent=USER_AGENT, viewport={"width": 1440, "height": 900}, locale="zh-CN"
        )
        if cookie_str:
            context.add_cookies(cookie_string_to_playwright(cookie_str))
        page = context.new_page()
        try:
            page.goto(url, wait_until="commit", timeout=30000)
        except Exception as e:
            log.warning(f"第 {page_no} 页加载失败：{e}")
            return None
        return try_extract_ssr_page(page)
    finally:
        browser.close()


def run(series_id: str, max_pages: int, out_dir: Path, debug_dir: Optional[Path], dump_raw: bool = False) -> None:
    out_path = out_dir / f"{series_id}_reviews.jsonl"
    out_dir.mkdir(parents=True, exist_ok=True)

    cookie_str = os.environ.get("DONGCHEDI_COOKIE", "").strip()
    if not cookie_str:
        log.warning("未设置 DONGCHEDI_COOKIE，可能会碰到登录墙")

    all_items_by_page: dict[int, list] = {}
    seen_first_gids: set = set()
    consecutive_failures = 0

    with sync_playwright() as p:
        for page_no in range(1, max_pages + 1):
            items = None
            for attempt in range(2):
                log.info(f"抓取第 {page_no} 页（第 {attempt + 1} 次尝试）")
                items = fetch_one_page(p, series_id, page_no, cookie_str)
                if items:
                    break
                random_delay(1.5, 3.0)

            if not items:
                consecutive_failures += 1
                log.warning(f"第 {page_no} 页两次尝试都没拿到数据，跳过（连续失败 {consecutive_failures} 次）")
                if consecutive_failures >= 3:
                    log.error("连续 3 页都没抓到数据，停止（可能已到最后一页，或反爬拦截变严）")
                    break
                random_delay(1.5, 3.0)
                continue

            first_gid = items[0].get("gid_str")
            if first_gid in seen_first_gids:
                log.warning(f"第 {page_no} 页数据和已抓页面重复（可能页码超出范围被回退到最后一页），停止")
                break

            consecutive_failures = 0
            seen_first_gids.add(first_gid)
            all_items_by_page[page_no] = items
            log.info(f"第 {page_no} 页拿到 {len(items)} 条")

            if page_no < max_pages:
                random_delay(1.5, 3.0)

    if dump_raw and debug_dir is not None and all_items_by_page:
        # 按车型名分文件夹存（从数据里的 series_name 取，取不到就退回车系 ID），
        # 抓多个车型时不会把原始 JSON 全堆在一起分不清谁是谁。
        first_page_items = all_items_by_page[min(all_items_by_page)]
        model_name = first_page_items[0].get("series_name") or series_id
        model_dir = debug_dir / model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        for page_no, items in all_items_by_page.items():
            raw_path = model_dir / f"page{page_no}_raw.json"
            with raw_path.open("w", encoding="utf-8") as f:
                json.dump({"data": {"review_list": items}}, f, ensure_ascii=False, indent=2)

    raw_count = sum(len(v) for v in all_items_by_page.values())
    written = append_reviews_deduped(out_path, series_id, all_items_by_page)
    log.info(f"完成，本次抓到 {raw_count} 条，去重后新写入 {written} 条到 {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="懂车帝车主口碑抓取（Playwright 版）")
    parser.add_argument("--series_id", required=True, help="车系 ID，例如智己L6=9660")
    parser.add_argument("--max_pages", type=int, default=20, help="最多抓取页数")
    parser.add_argument("--debug_dir", default="data/debug", help="dump_raw 原始 JSON 存放目录")
    parser.add_argument("--out_dir", default="data/raw", help="输出目录")
    parser.add_argument("--dump_raw", action="store_true", help="额外把每页原始数据存到 debug_dir，用于核对字段解析")
    args = parser.parse_args()

    run(
        series_id=args.series_id,
        max_pages=args.max_pages,
        out_dir=Path(args.out_dir),
        debug_dir=Path(args.debug_dir) if args.debug_dir else None,
        dump_raw=args.dump_raw,
    )


if __name__ == "__main__":
    main()
