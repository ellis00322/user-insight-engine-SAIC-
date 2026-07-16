"""
将 data/raw/*.jsonl（懂车帝口碑原始数据）清洗为统一 schema，输出到
data/processed/reviews_clean.csv，供导入飞书多维表格 / 后续 LLM 打标与回测流程使用。

用法：
    python pipeline/etl/clean_reviews.py
    python pipeline/etl/clean_reviews.py --raw_dir data/raw --out data/processed/reviews_clean.csv
"""

import argparse
import csv
import glob
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone

SERIES_NAMES_OVERRIDE_PATH = os.path.join(os.path.dirname(__file__), "series_names.json")

# 回测以智己 L6 首次上市日为 T0（2024-05-13，北京时间；已用网络搜索核对，
# 见 backtest/design.md 第 2/3 节）。注意智己 L6 2025 年还有一次改款上市
# （同样是 5 月 13 日，巧合），但方案叙事里"新车立项"对应的是首次上市，
# 这里的 phase 划分只认最初这次，改款款型的评论仍按首次上市日切分，
# 一律落在 T0 之后（post）。全部 7 款车的 phase 都按同一个 T0 计算——
# 这不是各车型自己的上市日，是"相对智己 L6 这次回测的时间锚点"。
T0_BEIJING = datetime(2024, 5, 13, 0, 0, 0, tzinfo=timezone(timedelta(hours=8)))
T0_TIMESTAMP = T0_BEIJING.timestamp()


def resolve_phase(review_time):
    if review_time is None:
        return None
    return "pre" if review_time < T0_TIMESTAMP else "post"


def load_series_names_override(path):
    """series_id -> 车型名 的手工兜底表，只在原始记录里没有 series_name 字段时才用
    （老爬虫版本抓的数据）。新数据统一从 raw["series_name"] 读取，不用维护这张表。"""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


# 与 pipeline/crawler/dongchedi_parsing.py 保持一致的中文标签 -> 英文字段名映射
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

SHORT_CONTENT_THRESHOLD = 15  # 对应 tagging_prompt.md 里"评论极短"的边界处理规则

# buy_place（购车地点，懂车帝结构化字段，非评论正文）-> 城市线级。这是确定性映射，
# 不依赖 LLM 从评论文本里猜——覆盖率（85% 有 buy_place）远高于靠文本间接线索推断
# city_tier（早期测试只有 15% 左右能推断出来）。名单不在下面的城市默认归"三线及以下"。
FIRST_TIER_CITIES = {"北京", "上海", "广州", "深圳"}
NEW_FIRST_TIER_CITIES = {
    "成都", "重庆", "杭州", "武汉", "西安", "苏州", "郑州", "南京",
    "天津", "长沙", "东莞", "宁波", "佛山", "合肥", "青岛",
}
SECOND_TIER_CITIES = {
    "昆明", "无锡", "济南", "大连", "福州", "厦门", "哈尔滨", "温州",
    "南宁", "长春", "泉州", "石家庄", "贵阳", "南昌", "金华", "常州",
    "南通", "嘉兴", "太原", "徐州", "惠州", "珠海", "中山", "台州",
    "烟台", "兰州", "绍兴", "海口", "扬州", "洛阳", "潍坊", "盐城",
}


def resolve_city_tier(buy_place):
    if not buy_place:
        return None
    if buy_place in FIRST_TIER_CITIES:
        return "一线"
    if buy_place in NEW_FIRST_TIER_CITIES:
        return "新一线"
    if buy_place in SECOND_TIER_CITIES:
        return "二线"
    return "三线及以下"


def normalize_score(raw, *, zero_is_null=False):
    """0-500 刻度转 0-5。zero_is_null=True 时把 0 当作"未评分"而非"评了 0 分"
    （sub_scores 里 0 出现频率远高于 50/100/150/200/250，明显是占位值）。"""
    if raw is None:
        return None
    if zero_is_null and raw == 0:
        return None
    return round(raw / 100, 2)


def parse_price_wan(raw):
    if not raw:
        return None
    try:
        return float(raw.replace("万", "").strip())
    except ValueError:
        return None


def parse_range_km(raw):
    if not raw:
        return None
    try:
        return float(raw.replace("km", "").strip())
    except ValueError:
        return None


def make_review_id(series_id, existing_id, review_time, content):
    """优先用爬虫已生成的 review_id（dcd_{series_id}_{gid_str}）；gid_str 缺失
    导致 review_id 为空时，用 series_id+review_time+content 的哈希兜底，保证去重可用。"""
    if existing_id:
        return existing_id
    digest = hashlib.sha1(f"{series_id}|{review_time}|{content}".encode("utf-8")).hexdigest()[:10]
    return f"dcd_{series_id}_h{digest}"


def to_pub_date(review_time):
    if not review_time:
        return None
    return datetime.fromtimestamp(review_time, tz=timezone.utc).astimezone().strftime("%Y-%m-%d")


def resolve_car_name(series_id, raw_series_name, override_map):
    """优先用原始数据自带的 series_name（新版爬虫已单独落这个字段）；
    缺失时退回 series_names.json 手工兜底表；再没有就返回 None，
    由调用方决定怎么处理（不静默瞎猜）。"""
    return raw_series_name or override_map.get(series_id)


def clean_record(raw, override_map):
    series_id = raw.get("series_id")
    car_name = resolve_car_name(series_id, raw.get("series_name"), override_map)

    car_config = raw.get("car_config")
    # 老版本爬虫在 buy_car_info 缺失时会把 car_config 兜底填成 series_name，
    # 导致这个字段里混进了车型名而不是真实配置/trim——通用判断规则：
    # car_config 等于已解析出的车型名，就说明是这种兜底填充，清空。
    if car_config and car_name and car_config == car_name:
        car_config = None

    content = (raw.get("content") or "").strip()
    review_time = raw.get("review_time")

    record = {
        "review_id": make_review_id(series_id, raw.get("review_id"), review_time, content),
        "source": "dongchedi",
        "series_id": series_id,
        "car_name": car_name,
        "car_config": car_config,
        "content": content,
        "content_len": len(content),
        "is_short_content": len(content) < SHORT_CONTENT_THRESHOLD,
        "review_time": review_time,
        "pub_date": to_pub_date(review_time),
        "phase": resolve_phase(review_time),
        "buy_place": raw.get("buy_place"),
        "city_tier": resolve_city_tier(raw.get("buy_place")),
        "car_price_wan": parse_price_wan(raw.get("car_price")),
        "range_km": parse_range_km(raw.get("range_km")),
        "overall_score_5": normalize_score(raw.get("overall_score")),
    }
    sub_scores = raw.get("sub_scores") or {}
    for label, key in SUB_SCORE_KEYS.items():
        record[key] = normalize_score(sub_scores.get(label), zero_is_null=True)
    return record


def load_raw(raw_dir):
    for path in sorted(glob.glob(os.path.join(raw_dir, "*_reviews.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)


def main():
    parser = argparse.ArgumentParser(description="清洗 data/raw 下的懂车帝口碑原始数据")
    parser.add_argument("--raw_dir", default="data/raw")
    parser.add_argument("--out", default="data/processed/reviews_clean.csv")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    override_map = load_series_names_override(SERIES_NAMES_OVERRIDE_PATH)

    seen_ids = set()
    rows = []
    dup_count = 0
    empty_count = 0
    unresolved_series = set()

    for raw in load_raw(args.raw_dir):
        if not (raw.get("content") or "").strip():
            empty_count += 1
            continue
        record = clean_record(raw, override_map)
        if record["car_name"] is None:
            unresolved_series.add(record["series_id"])
        if record["review_id"] in seen_ids:
            dup_count += 1
            continue
        seen_ids.add(record["review_id"])
        rows.append(record)

    rows.sort(key=lambda r: (r["series_id"], r["review_time"] or 0))

    fieldnames = list(rows[0].keys()) if rows else []
    # utf-8-sig 带 BOM，Excel / 飞书多维表格导入中文 CSV 更稳
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"清洗完成，写入 {len(rows)} 条 -> {args.out}")
    print(f"去重丢弃 {dup_count} 条，空内容丢弃 {empty_count} 条")

    by_car = {}
    for r in rows:
        label = r["car_name"] or f"未知车型({r['series_id']})"
        by_car[label] = by_car.get(label, 0) + 1
    for name, n in sorted(by_car.items(), key=lambda x: -x[1]):
        print(f"  {name}: {n}")

    if unresolved_series:
        print(
            f"\n[警告] {len(unresolved_series)} 个 series_id 解析不出车型名："
            f"{sorted(unresolved_series)}\n"
            f"  原始数据里没有 series_name 字段，也不在 {SERIES_NAMES_OVERRIDE_PATH} 里。"
            f"要么用当前版本爬虫重新抓一遍（会自动带上 series_name），"
            f"要么手动在 series_names.json 里补一行 \"series_id\": \"车型名\"。"
        )


if __name__ == "__main__":
    main()
