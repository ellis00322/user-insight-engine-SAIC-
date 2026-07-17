"""
计算回测指标：POS / DMR / SDA / CBS，公式定义见 backtest/design.md 第 6 节。

输入：
    data/processed/reviews_clean.csv    （series_id / phase / city_tier 等结构化字段，
                                          pipeline/etl/clean_reviews.py 产出）
    data/processed/reviews_tagged.jsonl （review_id -> llm_tags，
                                          pipeline/llm_tagging/tagger.py 产出）

"预测画像"取竞品车型里 phase=pre 的记录（目标车型上市前发布的评论，模拟"上市前只能
看到竞品口碑"这个真实场景）；"实际画像"取目标车型自己的记录（车主评论必然在自己
上市之后，天然全是 phase=post，见 pipeline/etl/clean_reviews.py 里 9660 那组验证）。

用法：
    python backtest/compute_metrics.py \
        --target_series 9660 \
        --competitor_series 6187,4980,9128,3352,4736,5306

    # 用手造的小样本自检公式实现是否正确（不需要真实打标数据）
    python backtest/compute_metrics.py --selftest
"""

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict

POS_WEIGHTS = {
    "purchase_motivation": 0.4,
    "life_stage": 0.3,
    "city_tier": 0.3,
}
CBS_WEIGHTS = {"pos": 0.5, "dmr5": 0.3, "sda": 0.2}


def load_clean(path):
    with open(path, encoding="utf-8-sig") as f:
        return {row["review_id"]: row for row in csv.DictReader(f)}


def load_tagged(path):
    """只保留 tag_status == ok 的记录，parse_error/api_error 的行不参与统计。"""
    tagged = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("tag_status") == "ok":
                tagged[rec["review_id"]] = rec["llm_tags"]
    return tagged


def join_records(clean_rows, tagged_by_id):
    """按 review_id 关联清洗数据（结构化字段）和打标数据（llm_tags），
    只保留两边都有的记录。"""
    records = []
    for review_id, row in clean_rows.items():
        llm_tags = tagged_by_id.get(review_id)
        if llm_tags is None:
            continue
        records.append({**row, "llm_tags": llm_tags})
    return records


def filter_records(records, series_ids=None, phase=None):
    out = records
    if series_ids is not None:
        out = [r for r in out if r["series_id"] in series_ids]
    if phase is not None:
        out = [r for r in out if r["phase"] == phase]
    return out


# ---------------------------------------------------------------------------
# 6.1 POS
# ---------------------------------------------------------------------------

def get_field_value(record, field):
    """人生阶段/购车动机来自 llm_tags（LLM 打标产出，{value, evidence} 结构）；
    城市线级来自清洗阶段的结构化字段（纯字符串，不经过 LLM），两种取值方式不同。"""
    if field == "city_tier":
        value = record.get("city_tier")
    else:
        value = (record.get("llm_tags", {}).get("user_profile", {}) or {}).get(field)
        value = value.get("value") if isinstance(value, dict) else None
    return value or None


def build_distribution(records, field):
    """统计某个字段的分布，忽略 null（缺失信息不代表某个"类别"，不参与相似度比较）。"""
    counter = Counter(v for r in records if (v := get_field_value(r, field)) is not None)
    total = sum(counter.values())
    if total == 0:
        return {}
    return {k: v / total for k, v in counter.items()}


def kl_divergence(p, q):
    """KL(P||Q)，要求 q[k] > 0 的地方 p[k] 才可能 > 0（用 JS 的 M 分布保证这一点）。"""
    total = 0.0
    for k, pk in p.items():
        if pk == 0:
            continue
        qk = q.get(k, 0.0)
        if qk == 0:
            continue  # 理论上不会发生：M = (P+Q)/2，P[k]>0 时 M[k] 必然 >0
        total += pk * math.log2(pk / qk)
    return total


def js_divergence(p_dist, q_dist):
    """Jensen-Shannon 散度，log 底数为 2，取值范围 [0, 1]。"""
    keys = set(p_dist) | set(q_dist)
    p = {k: p_dist.get(k, 0.0) for k in keys}
    q = {k: q_dist.get(k, 0.0) for k in keys}
    m = {k: (p[k] + q[k]) / 2 for k in keys}
    return 0.5 * kl_divergence(p, m) + 0.5 * kl_divergence(q, m)


def compute_pos(pred_records, actual_records):
    """返回 (POS_total, 各维度明细)。样本量为 0 的维度跳过，剩余维度按原权重比例重新
    归一化（不让某个维度因为数据缺失被静默计成 0 分拖累总分）。"""
    dim_scores = {}
    for field in POS_WEIGHTS:
        p = build_distribution(pred_records, field)
        q = build_distribution(actual_records, field)
        if not p or not q:
            dim_scores[field] = None  # 样本不足，不计入
            continue
        dim_scores[field] = 1 - js_divergence(p, q)

    available = {f: w for f, w in POS_WEIGHTS.items() if dim_scores[f] is not None}
    if not available:
        return None, dim_scores
    weight_sum = sum(available.values())
    pos_total = sum(dim_scores[f] * w / weight_sum for f, w in available.items())
    return pos_total, dim_scores


# ---------------------------------------------------------------------------
# 6.2 DMR（卖点匹配率）
# ---------------------------------------------------------------------------

def positive_dimension_counts(records):
    counter = Counter()
    for r in records:
        for ds in r.get("llm_tags", {}).get("dimension_sentiments") or []:
            if ds.get("sentiment") == "正面":
                counter[ds.get("dimension")] += 1
    return counter


def compute_dmr(pred_records, actual_records, k):
    pred_top = {d for d, _ in positive_dimension_counts(pred_records).most_common(k)}
    actual_top = {d for d, _ in positive_dimension_counts(actual_records).most_common(k)}
    if not pred_top or not actual_top:
        return None, pred_top, actual_top
    return len(pred_top & actual_top) / k, pred_top, actual_top


# ---------------------------------------------------------------------------
# 6.3 SDA（情感方向一致率）
# ---------------------------------------------------------------------------

def majority_sentiment_per_dimension(records):
    """每个维度出现次数最多的情感方向（正面/负面/中性），作为该维度的"代表情感"。"""
    counts = defaultdict(Counter)
    for r in records:
        for ds in r.get("llm_tags", {}).get("dimension_sentiments") or []:
            counts[ds.get("dimension")][ds.get("sentiment")] += 1
    return {dim: c.most_common(1)[0][0] for dim, c in counts.items()}


def compute_sda(pred_records, actual_records):
    pred_majority = majority_sentiment_per_dimension(pred_records)
    actual_majority = majority_sentiment_per_dimension(actual_records)
    common_dims = set(pred_majority) & set(actual_majority)
    if not common_dims:
        return None, 0
    matches = sum(1 for d in common_dims if pred_majority[d] == actual_majority[d])
    return matches / len(common_dims), len(common_dims)


# ---------------------------------------------------------------------------
# 6.4 CBS
# ---------------------------------------------------------------------------

def compute_cbs(pos_total, dmr5, sda):
    """三项里任意一项样本不足算不出来（None），CBS 也算不出来，不能只拿剩下两项
    凑一个看似完整的分数——那样会误导，不如老实说"数据不够，算不出"。"""
    if pos_total is None or dmr5 is None or sda is None:
        return None
    return CBS_WEIGHTS["pos"] * pos_total + CBS_WEIGHTS["dmr5"] * dmr5 + CBS_WEIGHTS["sda"] * sda


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def run(clean_path, tagged_path, target_series, competitor_series):
    clean_rows = load_clean(clean_path)
    tagged = load_tagged(tagged_path)
    records = join_records(clean_rows, tagged)

    pred_records = filter_records(records, series_ids=set(competitor_series), phase="pre")
    actual_records = filter_records(records, series_ids={target_series})

    print(f"预测输入（竞品 pre 阶段）：{len(pred_records)} 条")
    print(f"验证基准（目标车型全部记录）：{len(actual_records)} 条")
    if not pred_records or not actual_records:
        sys.exit("预测输入或验证基准样本为 0，无法计算，先确认打标结果和 series_id/phase 是否正确")

    pos_total, pos_dims = compute_pos(pred_records, actual_records)
    dmr3, pred_top3, actual_top3 = compute_dmr(pred_records, actual_records, 3)
    dmr5, pred_top5, actual_top5 = compute_dmr(pred_records, actual_records, 5)
    sda, sda_dim_count = compute_sda(pred_records, actual_records)
    cbs = compute_cbs(pos_total, dmr5, sda)

    def fmt(x):
        return "N/A（样本不足）" if x is None else f"{x:.3f}"

    print("\n=== POS（画像人群重合度）===")
    for field, score in pos_dims.items():
        print(f"  {field}: {fmt(score)}  (权重 {POS_WEIGHTS[field]})")
    print(f"  POS_total: {fmt(pos_total)}")

    print("\n=== DMR（卖点匹配率）===")
    print(f"  预测 Top3: {pred_top3}  实际 Top3: {actual_top3}  DMR@3: {fmt(dmr3)}")
    print(f"  预测 Top5: {pred_top5}  实际 Top5: {actual_top5}  DMR@5: {fmt(dmr5)}")

    print("\n=== SDA（情感方向一致率）===")
    print(f"  参与对比的维度数: {sda_dim_count}  SDA: {fmt(sda)}")

    print("\n=== CBS（综合评分）===")
    print(f"  CBS: {fmt(cbs)}")


# ---------------------------------------------------------------------------
# 自检：不依赖真实打标数据，用手造的小样本验证公式实现对不对
# ---------------------------------------------------------------------------

def _fake_record(series_id, phase, city_tier, life_stage, motivation, dims):
    return {
        "series_id": series_id,
        "phase": phase,
        "city_tier": city_tier,
        "llm_tags": {
            "user_profile": {
                "life_stage": {"value": life_stage, "evidence": None},
                "purchase_motivation": {"value": motivation, "evidence": None},
            },
            "dimension_sentiments": [
                {"dimension": d, "sentiment": s, "intensity": 3, "evidence": None} for d, s in dims
            ],
        },
    }


def _selftest():
    # 预测组和验证组分布完全一致 -> POS 应该是 1
    identical = [
        _fake_record("A", "pre", "一线", "已婚有娃", "家用", [("续航", "正面")]),
        _fake_record("A", "pre", "二线", "未婚", "个人通勤", [("外观", "正面")]),
    ]
    p = build_distribution(identical, "life_stage")
    q = build_distribution(identical, "life_stage")
    js = js_divergence(p, q)
    assert abs(js) < 1e-9, f"相同分布 JS 散度应为 0，实际 {js}"
    assert abs((1 - js) - 1.0) < 1e-9, "相同分布 POS 应为 1"

    # 完全不重叠的分布 -> JS 散度应为 1（POS 为 0）
    p2 = {"已婚有娃": 1.0}
    q2 = {"未婚": 1.0}
    js2 = js_divergence(p2, q2)
    assert abs(js2 - 1.0) < 1e-9, f"完全不重叠分布 JS 散度应为 1，实际 {js2}"

    # DMR：预测 top3 和实际 top3 完全一致 -> DMR@3 应为 1
    pred = [_fake_record("B", "pre", "一线", "未婚", "家用", [("续航", "正面"), ("外观", "正面")])]
    actual = [_fake_record("T", "post", "一线", "未婚", "家用", [("续航", "正面"), ("外观", "正面")])]
    dmr, pred_top, actual_top = compute_dmr(pred, actual, 2)
    assert dmr == 1.0, f"DMR 应为 1.0，实际 {dmr}"

    # SDA：同一维度情感方向相反 -> SDA 应为 0
    pred2 = [_fake_record("B", "pre", "一线", "未婚", "家用", [("续航", "正面")])]
    actual2 = [_fake_record("T", "post", "一线", "未婚", "家用", [("续航", "负面")])]
    sda, n = compute_sda(pred2, actual2)
    assert sda == 0.0 and n == 1, f"SDA 应为 0.0（1 个维度都不一致），实际 sda={sda} n={n}"

    print("自检全部通过：JS 散度 / POS / DMR / SDA 公式实现符合预期")


def main():
    parser = argparse.ArgumentParser(description="计算回测指标 POS/DMR/SDA/CBS")
    parser.add_argument("--clean", default="data/processed/reviews_clean.csv")
    parser.add_argument("--tagged", default="data/processed/reviews_tagged.jsonl")
    parser.add_argument("--target_series", default="9660", help="回测目标车型 series_id，默认智己L6")
    parser.add_argument(
        "--competitor_series",
        default="6187,4980,9128,3352,4736,5306",
        help="竞品参照系 series_id，逗号分隔，默认除目标车型外的其余6款",
    )
    parser.add_argument("--selftest", action="store_true", help="用手造小样本自检公式实现，不需要真实数据")
    args = parser.parse_args()

    if args.selftest:
        _selftest()
        return

    run(
        clean_path=args.clean,
        tagged_path=args.tagged,
        target_series=args.target_series,
        competitor_series=args.competitor_series.split(","),
    )


if __name__ == "__main__":
    main()
