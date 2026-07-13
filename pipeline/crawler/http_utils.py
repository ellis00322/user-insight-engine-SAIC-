"""
通用 HTTP 请求工具
提取自 AutoPulse 项目（D:/Download/AutoPulse）的请求层，去除业务逻辑后保留：
- User-Agent 池与随机轮换
- 随机延迟
- 带指数退避的自动重试
"""

import time
import random
import logging
from typing import Optional

import requests

log = logging.getLogger(__name__)

# ── User-Agent 池 ────────────────────────────────────────────────
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

BASE_HEADERS = {
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
}


def build_headers(referer: Optional[str] = None) -> dict:
    """随机选取 UA，可选注入 Referer"""
    h = dict(BASE_HEADERS)
    h["User-Agent"] = random.choice(UA_POOL)
    if referer:
        h["Referer"] = referer
    return h


def random_delay(min_sec: float = 2.0, max_sec: float = 5.0) -> None:
    """随机等待，降低被识别为爬虫的概率"""
    time.sleep(random.uniform(min_sec, max_sec))


def get(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    retries: int = 3,
    timeout: int = 15,
    delay_between_retries: float = 3.0,
) -> Optional[requests.Response]:
    """
    带自动重试的 GET 请求。
    失败时间隔 delay_between_retries * attempt 秒重试。
    全部失败返回 None（不抛出），由调用方决定如何处理。
    """
    _headers = headers or build_headers()
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=_headers, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            wait = delay_between_retries * attempt
            log.warning(f"[重试 {attempt}/{retries}] {url} → {e}，{wait:.0f}s 后重试")
            if attempt < retries:
                time.sleep(wait)
    log.error(f"[放弃] {url} 经 {retries} 次重试仍失败")
    return None


def post(
    url: str,
    json_data: Optional[dict] = None,
    headers: Optional[dict] = None,
    retries: int = 3,
    timeout: int = 15,
) -> Optional[requests.Response]:
    """带重试的 POST 请求，同 get() 逻辑"""
    _headers = headers or build_headers()
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(url, headers=_headers, json=json_data, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            wait = 3.0 * attempt
            log.warning(f"[重试 {attempt}/{retries}] POST {url} → {e}，{wait:.0f}s 后重试")
            if attempt < retries:
                time.sleep(wait)
    log.error(f"[放弃] POST {url} 经 {retries} 次重试仍失败")
    return None
