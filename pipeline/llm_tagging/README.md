# pipeline/llm_tagging

LLM 结构化打标模块。将原始评论文本转化为结构化用户画像标签。

## 处理流程

```
data/processed/reviews_clean.csv（清洗后的评论，见 pipeline/etl/clean_reviews.py）
    │
    ▼
tagging_prompt.md 中的提示词模板（system + user prompt）
    │
    ▼
tagger.py 批量调用 LLM API（智谱 GLM-4-Flash）
    │
    ▼
结构化 JSON 输出（用户特征 + 关注维度 + 情感极性）
    │
    ▼
data/processed/reviews_tagged.jsonl（按 review_id 存 llm_tags，支持中断重跑）
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `prompts/tagging_prompt.md` | 打标 prompt 模板与字段说明（system prompt / JSON schema 的唯一权威定义，`tagger.py` 里的提示词照搬这里） |
| `tagger.py` | 批量调用 LLM API 的执行脚本，输出到 `data/processed/reviews_tagged.jsonl`；内置 JSON 合法性 + schema 校验（`tag_status`：`ok` / `json_decode_error` / `schema_missing_keys` / `api_error`），失败条目重跑会自动重试，不会重复处理已成功的 |
| `prompts/feishu_bitable_fields.md` | 飞书多维表格 AI 字段配置（备选方案，见下） |

## 打标怎么跑

先跑完 `pipeline/etl/clean_reviews.py`，产出 `data/processed/reviews_clean.csv`，再跑：

```
# ZHIPU_API_KEY 写进项目根目录 .env
python pipeline/llm_tagging/tagger.py --limit 20   # 先跑小样本，检查输出质量
python pipeline/llm_tagging/tagger.py              # 确认没问题后跑全量
```

## 关于飞书多维表格 AI 字段（备选，非当前主路径）

`feishu_bitable_fields.md` 里记录了一版用飞书多维表格 AI 字段做打标的方案（把 `tagging_prompt.md` 拆成"1 个推理字段 + 3 个抽取字段"，避免每个字段独立推理导致互相矛盾）。这是此前命题"借助飞书 AI 工具"要求下探索过的路径，但存在明显短板：AI 字段生成配额/吞吐量有限、没有断点续传和重试机制、字段配置只能在 UI 里手动一个个建。当前打标直接用 `tagger.py` 调 API——更快、更稳定、可重复执行、能处理失败重试。打好的结果之后可以通过飞书开放平台 API 批量写回多维表格，供 Aily 问答 / 人群地图下钻使用——飞书依然是最终的存储和应用层，只是打标这一步的计算不再依赖飞书自带的 AI 字段。

## 质量控制要求

- LLM 输出必须严格为 JSON，不通过 schema 校验的条目 `tagger.py` 会标记为 `json_decode_error`（不是合法 JSON）或 `schema_missing_keys`（JSON 合法但缺关键字段）
- 对 `null` 比例过高（> 60%）的字段，需检查 prompt 或数据质量
- 建议对 5% 的样本进行人工复核，记录误标类型
