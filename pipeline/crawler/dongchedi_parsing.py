"""
懂车帝口碑页 __NEXT_DATA__ 解析（Playwright 爬虫用）。

字段键名已用真实响应核对（series_id=9660 智己L6）：购车信息在
item["buy_car_info"] 里，评分在 item["score_info"] 里，均为嵌套子对象。

口碑页（/auto/series/score/{series_id}-x-S0-x-x-x-{page}）数据是服务端
直出在 HTML 的 __NEXT_DATA__ 里，不走 XHR 接口，需要从 HTML 里解析。
"""

import json
import re

NEXT_DATA_PATTERN = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S
)

SUB_SCORE_KEYS = {
    "外观": "appearance_score",
    "内饰": "interiors_score",
    "配置": "configuration_score",
    "空间": "space_score",
    "续航": "continuation_score",
    "舒适性": "comfort_score",
    "操控": "control_score",
    "动力": "power_score",
}


def _first(d: dict, *keys, default=None):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def parse_sub_scores(item: dict) -> dict:
    score_info = item.get("score_info") or {}
    return {label: score_info.get(key) for label, key in SUB_SCORE_KEYS.items()}


def parse_review_item(item: dict, series_id: str) -> dict:
    """
    只保留匿名化的结构化评价内容，不提取 user_id/昵称/头像/主页链接等可定位到个人的字段。
    review_id 用平台的帖子 ID（gid_str）而非用户 ID，用于跨批次去重，不涉及个人身份。
    """
    buy_info = item.get("buy_car_info") or {}
    score_info = item.get("score_info") or {}
    gid_str = _first(item, "gid_str")
    return {
        "review_id": f"dcd_{series_id}_{gid_str}" if gid_str else None,
        "series_id": series_id,
        "series_name": _first(item, "series_name"),
        "car_config": _first(buy_info, "car_name"),
        "review_time": _first(item, "create_time", "publish_time", "time"),
        "buy_place": _first(buy_info, "location"),
        "car_price": _first(buy_info, "price"),
        "range_km": _first(buy_info, "continuation"),
        "overall_score": _first(score_info, "score"),
        "sub_scores": parse_sub_scores(item),
        "content": _first(item, "content", "text", "review_text"),
    }


def extract_next_data_review_list(html: str) -> list:
    """从口碑页 HTML 里解析 __NEXT_DATA__，取出 pageProps.reviewListData.review_list。"""
    m = NEXT_DATA_PATTERN.search(html)
    if not m:
        return []
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return []
    review_list = (
        data.get("props", {})
        .get("pageProps", {})
        .get("reviewListData", {})
        .get("review_list")
    )
    return review_list if isinstance(review_list, list) else []
