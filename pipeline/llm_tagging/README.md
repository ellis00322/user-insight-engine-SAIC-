# pipeline/llm_tagging

LLM 结构化打标模块。将原始评论文本转化为结构化用户画像标签。

**当前主路径（v2）**：完全由飞书多维表格 AI 字段完成打标（维度提取 + 情感方向 + 用户画像），不引入 Python 或外部 LLM API 参与打标推理。Python 只在 L3 回测阶段读取飞书产出的结构化数据做计算，不做任何打标。原先的独立全量打标脚本 `tagger.py`（v1，调用智谱 API）已废弃，原因见下方「版本变更记录」。

## 处理流程

```
data/processed/reviews_clean.csv（清洗后的评论，见 pipeline/etl/clean_reviews.py）
    │
    ▼
导入飞书多维表格
    │
    ▼
飞书多维表格 AI 字段（提示词见 prompts/feishu_bitable_fields.md）：
  - profile_json（推理字段，一次性联合判断维度、情感、用户画像，避免多次独立推理互相矛盾）
  - 从 profile_json 抽取的单选/多选字段：life_stage / purchase_motivation / purchase_stage /
    gender / positive_dimensions / negative_dimensions / neutral_dimensions
  - 吞吐/配额限制通过分批次跑解决（一次跑不完就分批跑，不切到代码调用）
    │
    ▼
导出 / 通过飞书开放平台 API 读取结构化结果
    │
    ▼
backtest/compute_metrics.py 计算 POS/DMR/SDA/CBS（纯计算，不调用任何 LLM）
```

产品经理侧只通过飞书多维表格 / Aily 消费最终结果。

## 文件说明

| 文件 | 说明 |
|------|------|
| `prompts/feishu_bitable_fields.md` | **当前主路径**：飞书多维表格 AI 字段配置（维度提取 + 情感方向 + 用户画像，全部由飞书 AI 完成）的字段设计与 Prompt |
| `prompts/tagging_prompt.md` | ~~v1 方案~~，`tagger.py` 的 Prompt/Schema 定义，已废弃，仅作历史参考 |
| `tagger.py` | ~~v1 方案~~，已废弃，不要再用来跑打标，保留仅供参考（见下方「版本变更记录」） |

## 版本变更记录

### v1（已废弃）：`tagger.py` 独立调用智谱 API 全量打标

流程：每条评论从零推理全部字段（维度 + 情感 + 用户画像），维度枚举固定 10 类。

**废弃原因**（人工抽检 `data/reviews tagged.csv` 发现）：

1. **evidence 造假**：`life_stage_evidence`/`purchase_motivation_evidence`/`purchase_stage_evidence` 三个字段里，约 73%（500 条有值记录中 366 条）的内容是 Prompt 模板里的占位说明文字"原文引用或 null"被模型原样抄了回来，不是真实原文引用。`tagger.py` 的校验逻辑只检查 `value` 是否在枚举范围内，没有检查 `evidence` 是否真的来自原文，这个问题一路混进了最终数据。
2. 即便 evidence 不是占位符，也存在编造/张冠李戴的情况——比如用"喜欢运动模式驾驶"作为判断性别为男的证据，逻辑上不成立。
3. 维度枚举固定 10 类，覆盖面不如飞书多维表格 AI 字段跑出来的结果（飞书能识别出"车机智能化""用车成本""故障维修""品牌认知"等更细的维度）。

### v2（当前主路径）：完全由飞书多维表格 AI 字段打标

飞书多维表格 AI 字段规模化跑到 1375 条中的 1286 条时曾一度配额耗尽（情感字段没能跑出结果）。中间短暂考虑过"飞书做维度提取、Python 批量调 LLM API 补情感和画像"的折中方案，但 Python/智谱 API 从始至终只是备选的 Plan B，不作为与飞书并存的正式环节，已放弃这个折中思路。

最终方案：**打标全流程留在飞书里**——用一个推理字段（`profile_json`）联合判断维度、情感、用户画像（避免"同一条评论被独立问 N 次，互相矛盾"的问题），再用抽取字段把需要单选/多选筛选的值拆出来。规模上的吞吐限制通过分批次跑解决：一次配额跑不完，分几次跑完，而不是切换成代码调用 API。

## 打标怎么跑

1. `pipeline/etl/clean_reviews.py` 跑完，产出 `data/processed/reviews_clean.csv`，导入飞书多维表格
2. 在飞书里按 `prompts/feishu_bitable_fields.md` 建 `profile_json` 推理字段，小样本跑通、人工抽查 evidence 是否真的是原文引用之后，再分批对全量跑
3. 全量跑完后建抽取字段（`life_stage`/`purchase_motivation`/`purchase_stage`/`gender`/`positive_dimensions`/`negative_dimensions`/`neutral_dimensions`）
4. 导出 / API 读取结果，供 `backtest/compute_metrics.py` 计算回测指标

## 质量控制要求

- evidence 非 null 时必须是原文的真实子串，不满足直接判该字段为 null，不允许编造
- 对 `null` 比例过高（> 60%）的字段，需检查 prompt 或数据质量
- 建议对 5% 的样本进行人工复核，记录误标类型（v1 的证据造假问题就是靠人工抽检发现的，飞书 AI 字段没有代码层面的自动校验，人工抽检是唯一的质量把关手段，务必执行）
