# 统一字段说明

本文档定义各数据源清洗后的统一字段 Schema，分两部分：**ETL 清洗字段**（`pipeline/etl/clean_reviews.py` 产出，确定性映射，不经过 LLM）和 **LLM 打标字段**（完全由飞书多维表格 AI 字段产出，不引入 Python/外部 LLM API，详见 [`pipeline/llm_tagging/README.md`](../pipeline/llm_tagging/README.md)）。两部分按 `review_id` 关联成一条完整记录。

## 一、评论记录（review）基础字段——ETL 清洗产出

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `review_id` | string | 全局唯一 ID，`{来源}_{series_id}_{平台内评论ID}` | `dcd_9660_7434046568942014526` |
| `source` | string | 来源平台 | `dongchedi` |
| `series_id` | string | 平台内车系 ID | `9660` |
| `car_name` | string | 车型名称（标准化，见 `pipeline/etl/series_names.json`） | `智己L6` |
| `car_config` | string | 具体配置项（可为空） | - |
| `content` | string | 评论全文（已脱敏） | - |
| `content_len` | int | 评论字数 | `604` |
| `is_short_content` | bool | 是否短评论（< 15 字，影响打标 confidence 判断） | `否` |
| `review_time` | datetime | 评论发布的完整时间戳 | `2020-09-16 17:49:19` |
| `pub_date` | date | 发布日期（按平台时区归一化） | `2020-09-16` |
| `phase` | string | 相对车系 T0（回测目标车型上市日）的阶段，由 `backtest/design.md` 的时间切分规则确定性判定 | `pre` / `post` |
| `buy_place` | string | 购车地点（懂车帝结构化字段，非 LLM 推断） | `上海` |
| `city_tier` | string | 城市线级，由 `buy_place` 确定性映射得出，**不经过 LLM**，覆盖率约 85%（比早期评估的 LLM 文本推断约 15% 可靠得多） | `一线` / `新一线` / `二线` / `三线及以下` |
| `car_price_wan` | float | 购车价格（万元，结构化字段） | `23.5` |
| `range_km` | float | 续航里程（km，结构化字段） | `620` |
| `overall_score_5` | float | 综合评分（懂车帝原始评分，归一化至 1–5） | `4.36` |
| `appearance_score` | float | 外观评分 | `4.5` |
| `interiors_score` | float | 内饰评分 | `4.5` |
| `configuration_score` | float | 配置评分 | `4` |
| `space_score` | float | 空间评分 | `4.5` |
| `continuation_score` | float | 续航评分 | `4` |
| `comfort_score` | float | 舒适性评分 | `4` |
| `control_score` | float | 操控评分 | `4` |
| `power_score` | float | 动力评分 | `4.5` |

> 上述评分字段（除 `overall_score_5`）覆盖率不均——`comfort_score`/`control_score`/`power_score` 只有约 15% 的评论带有该项细分评分（懂车帝并非每条评论都填全部子项），使用时需注意样本量。

## 二、LLM 打标字段——完全由飞书多维表格 AI 字段产出

一个推理字段（`profile_json`）联合判断全部内容，其余字段从中抽取，详见 [`pipeline/llm_tagging/prompts/feishu_bitable_fields.md`](../pipeline/llm_tagging/prompts/feishu_bitable_fields.md)。

### 2.1 维度提取（抽取字段，「评论打标」/ `positive_dimensions` 等）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `dimensions` | list[string] | 评论涉及的方面，闭集枚举（17 类），见下 |

**维度闭集枚举**：

```
续航表现 / 辅助驾驶 / 车机智能化 / 内饰质感 / 外观设计 / 空间表现 / 底盘操控 / 舒适性 /
动力性能 / 充电体验 / 配置丰富度 / 性价比 / 用车成本 / 售后权益 / 故障维修 / 品牌认知 / 其他
```

这套枚举比早期 v1 方案（`tagger.py`，固定 10 类）覆盖面更广，是飞书 AI 字段实测跑出来的结果整理成闭集后的版本——闭集是为了保证 DMR/SDA 回测指标里"同一维度前后统计口径一致"。

### 2.2 情感方向 + 用户画像（抽取字段，同样来自 `profile_json`）

| 字段名 | 类型 | 说明 | 覆盖率参考值 |
|--------|------|------|------|
| `dimension_sentiments` | list[{dimension, sentiment, intensity, evidence}] | 针对 2.1 里每个已识别维度，给出情感方向、强度（1~5）与原文证据 | 待飞书全量跑完后统计 |
| `positive_dimensions` / `negative_dimensions` / `neutral_dimensions` | list[string] | 从 `dimension_sentiments` 按情感方向拆出的三个多选字段，方便飞书多维表格分组统计和回测脚本直接读取，不用解析嵌套 JSON | 同上 |
| `life_stage` | enum + evidence | 已婚有娃 / 已婚无娃 / 未婚 / 退休 / null | v1（`tagger.py`，已废弃）跑出的参考值约 36%，飞书全量跑完后需重新统计 |
| `purchase_motivation` | enum + evidence | 家用 / 商务接待 / 个人通勤 / 换购升级 / 首次购车 / null | v1 参考值约 98%，飞书全量跑完后需重新统计 |
| `purchase_stage` | enum + evidence | 已购车 / 意向中 / 对比选购 / null | 待飞书全量跑完后统计（v1 数据因 evidence 造假问题作废，不可参考） |
| `gender` | enum + evidence | 男 / 女 / null | v1 参考值约 11%（样本偏薄，只作人群地图辅助下钻维度，不计入 POS 核心回测指标，见 `backtest/design.md` 6.1 节），飞书全量跑完后需重新统计 |

**`evidence` 强约束**：Prompt 明确要求非 null 时必须是 `content` 的真实子串，不允许编造或抄写 Prompt 模板里的占位说明文字——这条规则是 v1 方案（`tagger.py`）暴露 73% evidence 造假问题后新增的，详见 [`pipeline/llm_tagging/README.md`](../pipeline/llm_tagging/README.md) 的「版本变更记录」。飞书 AI 字段没有代码层面的自动校验，这条约束只能靠 Prompt 措辞 + 人工抽检来把关，务必执行人工复核。

### 2.3 未纳入的字段

**`age`（年龄段）不纳入**：评论文本里能推断年龄的间接线索覆盖率实测仅约 2.7%，且还需再细分多个年龄段，每个分档样本量没有统计意义，强行加入容易变成模型瞎猜，与"每个标签强制挂原文证据"的核心原则冲突。规划后续接入交强险/车联网行为数据等其他数据源补全。

## 三、合并后的完整记录（供回测 / 人群地图使用）

`review_id` 是关联键，两部分字段本就在同一张飞书多维表格里（ETL 字段导入时写入，LLM 打标字段由飞书 AI 字段生成），导出/API 读取后按 `review_id` 拼成 `data/processed/reviews_tagged.jsonl`（`backtest/compute_metrics.py` 直接读取的格式）；飞书多维表格本身同时供 Aily 问答与人群地图（`life_stage × city_tier × purchase_motivation` 分组下钻）使用。
