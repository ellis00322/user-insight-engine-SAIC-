# pipeline/llm_tagging

LLM 结构化打标模块。将原始评论文本转化为结构化用户画像标签。

**当前主路径（v2）**：飞书多维表格 AI 字段做维度提取 + Python 批量调用 LLM API 补全情感方向与用户画像。原先的独立全量打标脚本 `tagger.py`（v1）已废弃，原因见下方「版本变更记录」。

## 处理流程

```
data/processed/reviews_clean.csv（清洗后的评论，见 pipeline/etl/clean_reviews.py）
    │
    ▼
导入飞书多维表格
    │
    ▼
飞书多维表格 AI 字段：「评论打标」（维度提取，提示词见 prompts/feishu_bitable_fields.md）
    │
    ▼
导出 / 通过飞书开放平台 API 读取（review_id + content + 评论打标）
    │
    ▼
补全脚本（待实现，替代 tagger.py）批量调用 LLM API：
  - 对飞书已提取的每个维度，判断情感方向（正/负/中）+ evidence
  - 补 user_profile：life_stage / purchase_motivation / purchase_stage / gender + evidence
  - 对飞书未覆盖到的记录（AI 字段配额耗尽前没跑到的部分），从头完整打标
  - 强校验：evidence 非 null 时必须是 content 的真实子串，否则该字段整体判 null
    （这条校验是 v1 暴露问题后新加的，见下方「版本变更记录」）
    │
    ▼
合并飞书结果 + 补全结果 → data/processed/reviews_tagged.jsonl
    │
    ▼
一份写回飞书多维表格（供 Aily 问答 / 人群地图使用），一份供 backtest/compute_metrics.py 计算回测指标
```

产品经理侧只通过飞书多维表格 / Aily 消费最终结果，不接触打标环节内部的工具分工——不管某一列是飞书 AI 字段生成的还是 Python 补的，最终都合并进同一张表。

## 文件说明

| 文件 | 说明 |
|------|------|
| `prompts/feishu_bitable_fields.md` | **当前主路径**：飞书多维表格 AI 字段配置（维度提取）+ Python 补全脚本的字段定义与 Prompt |
| `prompts/tagging_prompt.md` | ~~v1 方案~~，`tagger.py` 的 Prompt/Schema 定义，已废弃，仅作历史参考 |
| `tagger.py` | ~~v1 方案~~，已废弃，不要再用来跑打标，保留仅供参考（见下方「版本变更记录」） |

## 版本变更记录

### v1（已废弃）：`tagger.py` 独立调用智谱 API 全量打标

流程：每条评论从零推理全部字段（维度 + 情感 + 用户画像），维度枚举固定 10 类。

**废弃原因**（人工抽检 `data/reviews tagged.csv` 发现）：

1. **evidence 造假**：`life_stage_evidence`/`purchase_motivation_evidence`/`purchase_stage_evidence` 三个字段里，约 73%（500 条有值记录中 366 条）的内容是 Prompt 模板里的占位说明文字"原文引用或 null"被模型原样抄了回来，不是真实原文引用。`tagger.py` 的校验逻辑只检查 `value` 是否在枚举范围内，没有检查 `evidence` 是否真的来自原文，这个问题一路混进了最终数据。
2. 即便 evidence 不是占位符，也存在编造/张冠李戴的情况——比如用"喜欢运动模式驾驶"作为判断性别为男的证据，逻辑上不成立。
3. 维度枚举固定 10 类，覆盖面不如飞书多维表格 AI 字段跑出来的结果（飞书能识别出"车机智能化""用车成本""故障维修""品牌认知"等更细的维度）。

### v2（当前主路径）：飞书维度提取 + Python 补全

**分工依据**：

- 维度提取交给飞书多维表格 AI 字段——已验证覆盖面比 v1 固定枚举广，且直接满足命题"借助飞书 AI 工具"的要求
- 情感方向、用户画像交给 Python 批量调用 LLM API——这两块飞书 AI 字段规模化跑不完（实测跑到 1375 条中的 1286 条时配额耗尽，情感字段甚至完全没跑出结果），Python 侧没有这个吞吐限制，且加了 evidence 原文子串强校验，堵住 v1 暴露的证据造假问题
- 两部分结果最终合并写回同一张飞书多维表格，不影响下游 Aily / 人群地图 / 回测的消费方式

## 打标怎么跑

1. `pipeline/etl/clean_reviews.py` 跑完，产出 `data/processed/reviews_clean.csv`，导入飞书多维表格
2. 在飞书里按 `prompts/feishu_bitable_fields.md` 建「评论打标」AI 字段，小样本跑通后再上全量
3. 导出 / API 读取飞书打标结果
4. 跑补全脚本（待实现）把情感方向与用户画像补齐，输出 `data/processed/reviews_tagged.jsonl`
5. 结果写回飞书多维表格

## 质量控制要求

- evidence 非 null 时必须是原文的真实子串，不满足直接判该字段为 null，不允许编造
- 对 `null` 比例过高（> 60%）的字段，需检查 prompt 或数据质量
- 建议对 5% 的样本进行人工复核，记录误标类型（v1 的证据造假问题就是靠人工抽检发现的，自动校验不能完全替代人工抽查）
