"""
【已废弃 v1 方案，不要用来跑打标】

人工抽检 data/reviews tagged.csv 发现：life_stage/purchase_motivation/purchase_stage
的 evidence 字段约 73%（500 条有值记录中 366 条）是 Prompt 模板里的占位说明文字
"原文引用或 null" 被模型原样抄了回来，不是真实原文引用；本文件的校验逻辑（parse_and_validate）
只检查 value 是否在枚举范围内，没有检查 evidence 是否真的来自原文，问题一路混进了最终数据。
当前主路径改为「飞书多维表格 AI 字段做维度提取 + Python 补全脚本补情感/画像」，详见
pipeline/llm_tagging/README.md 的「版本变更记录」。本文件保留仅作历史参考。

---

批量调用智谱 GLM（OpenAI 兼容模式）API，对 data/processed/reviews_clean.csv
里的评论做结构化打标，输出到 data/processed/reviews_tagged.jsonl。

字段定义与 prompts/tagging_prompt.md 保持一致（system prompt / JSON schema 直接照搬）。

用法：
    # ZHIPU_API_KEY 写进项目根目录 .env（不要用 export/贴在命令行里，避免留在 shell 历史）
    python pipeline/llm_tagging/tagger.py --limit 20      # 先跑小样本测试
    python pipeline/llm_tagging/tagger.py                 # 跑全量，支持中断后重跑（跳过已成功的）

依赖：
    pip install openai python-dotenv
"""

import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"

SYSTEM_PROMPT = """你是一位专注于汽车行业的用户研究专家，擅长从车主评论中提取结构化的用户洞察。

你的任务是分析一条车主口碑原文，按照指定 JSON 格式输出结构化标签。

严格规则（违反将导致输出无效）：
1. 只能从原文中提取或合理推断信息，禁止编造任何未在原文中提及或暗示的内容
2. 原文完全没有任何相关线索（哪怕是间接线索）时，才填 null；只要原文出现相关的间接线索，
   就应该基于这些线索给出最合理的推断，不要因为线索不是直接明说就默认填 null。
   例如 life_stage 可以从"孩子""老婆/老公/爱人""接送上学""二胎""父母""退休""一个人"
   "单身"这类家庭角色词汇间接推断；gender 可以从"我老婆""我老公""作为宝妈""我们男人"这类
   自称/关系词间接推断。gender 这个字段车评原文通常线索较少，大部分情况下会是 null，这是
   正常的，不要为了填满字段而编造
3. evidence 字段必须直接引用原文中的具体片段，不得改写或总结；value 为 null 时 evidence
   也必须是 null，不能为了凑格式编一个不存在的引用
4. 情感强度（intensity）基于原文措辞力度判断，1=轻微，5=强烈
5. 输出必须是合法的 JSON，不得包含任何注释或额外文字"""

USER_PROMPT_TEMPLATE = """请对以下车主评论进行结构化分析，严格按照 JSON Schema 输出，不要输出任何 JSON 以外的内容。

【评论原文】
{content}

【输出格式】
{{
  "user_profile": {{
    "life_stage": {{"value": "已婚有娃 | 已婚无娃 | 未婚 | 退休 | null", "evidence": "原文引用或 null"}},
    "purchase_motivation": {{"value": "家用 | 商务接待 | 个人通勤 | 换购升级 | 首次购车 | null", "evidence": "原文引用或 null"}},
    "purchase_stage": {{"value": "已购车 | 意向中 | 对比选购 | null", "evidence": "原文引用或 null"}},
    "gender": {{"value": "男 | 女 | null", "evidence": "原文引用或 null"}}
  }},
  "dimension_sentiments": [
    {{"dimension": "续航 | 智能驾驶 | 内饰 | 充电体验 | 售后服务 | 价格 | 外观 | 空间 | 动力性能 | 其他", "sentiment": "正面 | 负面 | 中性", "intensity": 1, "evidence": "原文引用（必填，不得为 null）"}}
  ],
  "key_highlights": ["直接引用原文中表达满意或称赞的短语，最多 3 条，无则返回空数组 []"],
  "key_pain_points": ["直接引用原文中表达不满或抱怨的短语，最多 3 条，无则返回空数组 []"],
  "usage_scenarios": ["通勤 | 家庭出行 | 长途自驾 | 商务接送 | 其他"],
  "meta": {{"confidence": "high | medium | low", "confidence_reason": "简述整体可推断程度"}}
}}"""

REQUIRED_TOP_KEYS = {
    "user_profile",
    "dimension_sentiments",
    "key_highlights",
    "key_pain_points",
    "usage_scenarios",
    "meta",
}


def call_llm(client, model, content, max_retries=3):
    user_prompt = USER_PROMPT_TEMPLATE.format(content=content)
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            return resp.choices[0].message.content
        except Exception as e:
            last_err = e
            time.sleep(2**attempt)
    raise last_err


ALLOWED_DIMENSIONS = {
    "续航", "智能驾驶", "内饰", "充电体验", "售后服务", "价格", "外观", "空间", "动力性能", "其他",
}

ALLOWED_USER_PROFILE_VALUES = {
    "life_stage": {"已婚有娃", "已婚无娃", "未婚", "退休"},
    "purchase_motivation": {"家用", "商务接待", "个人通勤", "换购升级", "首次购车"},
    "purchase_stage": {"已购车", "意向中", "对比选购"},
    "gender": {"男", "女"},
}


def normalize_string_nulls(obj):
    """模型有时会把 schema 里 "已婚有娃 | ... | null" 这种写法里的 null 当成字符串
    选项照抄，输出字符串 "null" 而不是真正的 JSON null，导致后面判断 value is None
    会漏判。递归把这种字符串 "null" 统一转成真正的 None。"""
    if isinstance(obj, dict):
        return {k: normalize_string_nulls(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize_string_nulls(v) for v in obj]
    if isinstance(obj, str) and obj.strip().lower() == "null":
        return None
    return obj


def normalize_user_profile_enums(data):
    """每个 user_profile 字段现在是 {"value":..., "evidence":...} 结构。模型偶尔会把
    schema 里 "已婚有娃 | 已婚无娃 | null" 这种带竖线的选项说明整段抄进 value，而不是
    选其中一个（不是纯字符串 "null"，normalize_string_nulls 抓不到）。不在预设枚举
    范围内的 value 一律当无效值处理：value 和 evidence 都归 None，不让脏值/对不上号
    的证据进入后续统计（value 为 null 时 evidence 也必须为 null，是硬性一致性要求）。"""
    up = data.get("user_profile") or {}
    for field, allowed in ALLOWED_USER_PROFILE_VALUES.items():
        entry = up.get(field)
        if not isinstance(entry, dict):
            continue
        if entry.get("value") is not None and entry.get("value") not in allowed:
            entry["value"] = None
            entry["evidence"] = None
    return data


def normalize_dimensions(data):
    """维度情感偶尔会出现不在预设 10 个选项里的自造维度（比如"平顺性""底盘"），
    这些数据会在按维度聚合统计时变成统计不进任何一类的孤儿数据，统一归到"其他"。"""
    for item in data.get("dimension_sentiments") or []:
        if item.get("dimension") not in ALLOWED_DIMENSIONS:
            item["dimension"] = "其他"
    return data


def parse_and_validate(raw_text):
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return None, "json_decode_error"
    if not REQUIRED_TOP_KEYS.issubset(data.keys()):
        return None, "schema_missing_keys"
    data = normalize_string_nulls(data)
    data = normalize_user_profile_enums(data)
    data = normalize_dimensions(data)
    return data, None


def load_and_compact_existing(out_path):
    """读已有输出，只保留成功（tag_status=ok）的记录并重写文件；失败的记录本次会
    重新尝试，不保留旧的失败行，避免多次重跑后同一个 review_id 在文件里堆出多条
    不同状态的记录。返回已成功、本次可以跳过的 review_id 集合。"""
    if not os.path.exists(out_path):
        return set()
    ok_lines = []
    done_ids = set()
    with open(out_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("tag_status") == "ok":
                ok_lines.append(line)
                done_ids.add(rec.get("review_id"))
    with open(out_path, "w", encoding="utf-8") as f:
        for line in ok_lines:
            f.write(line + "\n")
    return done_ids


def load_input_rows(in_path):
    with open(in_path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def tag_one(client, model, row):
    review_id = row["review_id"]
    content = row["content"]
    base = {
        "review_id": review_id,
        "source": row.get("source"),
        "series_id": row.get("series_id"),
        "car_name": row.get("car_name"),
    }
    try:
        raw_text = call_llm(client, model, content)
    except Exception as e:
        return {**base, "tag_status": "api_error", "error": str(e), "llm_tags": None}

    tags, err = parse_and_validate(raw_text)
    if err:
        return {**base, "tag_status": err, "raw_response": raw_text[:2000], "llm_tags": None}
    return {**base, "tag_status": "ok", "llm_tags": tags}


def main():
    parser = argparse.ArgumentParser(description="批量调用智谱 GLM API 对清洗后的评论做结构化打标")
    parser.add_argument("--in", dest="in_path", default="data/processed/reviews_clean.csv")
    parser.add_argument("--out", dest="out_path", default="data/processed/reviews_tagged.jsonl")
    parser.add_argument("--model", default="glm-4-flash")
    parser.add_argument("--max_workers", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None, help="只处理前 N 条，用于小样本测试")
    args = parser.parse_args()

    api_key = os.environ.get("ZHIPU_API_KEY")
    if not api_key:
        sys.exit("未设置 ZHIPU_API_KEY（写进项目根目录 .env），无法调用 API")

    client = OpenAI(api_key=api_key, base_url=ZHIPU_BASE_URL)

    rows = load_input_rows(args.in_path)
    done_ids = load_and_compact_existing(args.out_path)
    todo = [r for r in rows if r["review_id"] not in done_ids]
    if args.limit:
        todo = todo[: args.limit]

    print(f"共 {len(rows)} 条，已成功 {len(done_ids)} 条，本次处理 {len(todo)} 条")
    if not todo:
        return

    os.makedirs(os.path.dirname(args.out_path) or ".", exist_ok=True)
    ok_count = 0
    err_count = 0
    with open(args.out_path, "a", encoding="utf-8") as out_f:
        with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
            futures = [pool.submit(tag_one, client, args.model, row) for row in todo]
            for i, future in enumerate(as_completed(futures), 1):
                result = future.result()
                out_f.write(json.dumps(result, ensure_ascii=False) + "\n")
                out_f.flush()
                if result["tag_status"] == "ok":
                    ok_count += 1
                else:
                    err_count += 1
                if i % 20 == 0 or i == len(todo):
                    print(f"进度 {i}/{len(todo)}，成功 {ok_count}，失败 {err_count}")

    print(f"完成。成功 {ok_count} 条，失败 {err_count} 条 -> {args.out_path}")
    if err_count:
        print("失败的条目重跑同一条命令会自动重试，不会重复处理已成功的条目")


if __name__ == "__main__":
    main()
