# 飞书多维表格 AI 字段配置

> 把 `data/processed/reviews_clean.csv` 导入多维表格后，在表里新增以下 AI 字段。
> 每个字段的"提示词"直接复制粘贴进飞书 AI 字段配置的提示词框。
> 字段定义与 `tagging_prompt.md` 保持一致。

## 设计思路

只有 **1 个字段做真正的推理**（`profile_json`，一次性联合判断所有维度，保证字段间互相自洽），
其余 3 个字段是从这份 JSON 结果里**抽取**关键值，不重新推理——避免"同一条评论被独立问 N 次，
互相矛盾"的问题（比如 life_stage 判断成"已婚有娃"，purchase_motivation 却独立判断成"个人通勤"，
两次独立推理容易前后矛盾；抽取字段直接读第一次推理已经定好的结论，不会有这个问题）。

抽取出 `life_stage`/`city_tier`/`purchase_motivation` 三个单选字段，是因为：
- `life_stage` × `city_tier` 是原题人群地图明确要求的下钻维度
- `purchase_motivation`（购车动机）是产品经理最关心的洞察内容
- 单选字段才能在多维表格里直接分组统计，长文本字段做不到

其余字段（维度情感、亮点、槽点、置信度）留在 `profile_json` 里，Aily 问答时直接读取整段 JSON
作为依据即可，不需要每个都拆成单独的列。

## 建表前提

- 先把 `reviews_clean.csv` 导入为一张多维表格，确认 `content` 列存在（评论原文）
- **先在小样本上跑通再上全量**：建议每个车型分层抽样 20~30 条（共 150~200 条左右），检查输出质量没问题后再对全量 1375 条跑
- 字段建表顺序有先后依赖：先建好 `profile_json`，等它对所有目标行都生成完，再建后面 3 个抽取字段（它们的提示词要引用 `profile_json` 的值，如果这一列还没生成，抽取字段会读到空值）

---

## 1. profile_json（长文本，AI 字段，引用 `{{content}}`）

```
你是一位专注于汽车行业的用户研究专家，擅长从车主评论中提取结构化的用户洞察。

分析下面这条车主口碑原文，严格按照 JSON Schema 输出，不要输出任何 JSON 以外的内容。

严格规则（违反将导致输出无效）：
1. 只能从原文中提取或合理推断信息，禁止编造任何未在原文中提及或暗示的内容
2. 无法从原文推断的字段，必须填写 null，不得猜测
3. evidence 字段必须直接引用原文中的具体片段，不得改写或总结
4. 情感强度（intensity）基于原文措辞力度判断，1=轻微，5=强烈
5. 输出必须是合法的 JSON，不得包含任何注释或额外文字

【输出格式】
{
  "user_profile": {
    "life_stage": {"value": "已婚有娃 | 已婚无娃 | 未婚 | 退休 | null", "evidence": "原文引用或 null"},
    "city_tier": {"value": "一线 | 新一线 | 二线 | 三线及以下 | null", "evidence": "原文引用或 null"},
    "purchase_motivation": {"value": "家用 | 商务接待 | 个人通勤 | 换购升级 | 首次购车 | null", "evidence": "原文引用或 null"},
    "purchase_stage": {"value": "已购车 | 意向中 | 对比选购 | null", "evidence": "原文引用或 null"}
  },
  "dimension_sentiments": [
    {"dimension": "续航 | 智能驾驶 | 内饰 | 充电体验 | 售后服务 | 价格 | 外观 | 空间 | 动力性能 | 其他", "sentiment": "正面 | 负面 | 中性", "intensity": 1, "evidence": "原文引用（必填）"}
  ],
  "key_highlights": ["最多 3 条原文直接引用，无则 []"],
  "key_pain_points": ["最多 3 条原文直接引用，无则 []"],
  "usage_scenarios": ["通勤 | 家庭出行 | 长途自驾 | 商务接送 | 其他"],
  "meta": {"confidence": "high | medium | low", "confidence_reason": "简述可推断程度"}
}

【评论原文】
{{content}}
```

## 2. life_stage（单选，AI 字段，引用 `{{profile_json}}`）

选项：已婚有娃 / 已婚无娃 / 未婚 / 退休 / 无法判断

```
下面是一段结构化 JSON。直接读出 user_profile.life_stage.value 的值并返回对应选项，
不要重新分析原文，也不要输出 JSON 本身。如果值是 null，返回"无法判断"。

【JSON】
{{profile_json}}
```

## 3. city_tier（单选，AI 字段，引用 `{{profile_json}}`）

选项：一线 / 新一线 / 二线 / 三线及以下 / 无法判断

```
下面是一段结构化 JSON。直接读出 user_profile.city_tier.value 的值并返回对应选项，
不要重新分析原文，也不要输出 JSON 本身。如果值是 null，返回"无法判断"。

【JSON】
{{profile_json}}
```

## 4. purchase_motivation（单选，AI 字段，引用 `{{profile_json}}`）

选项：家用 / 商务接待 / 个人通勤 / 换购升级 / 首次购车 / 无法判断

```
下面是一段结构化 JSON。直接读出 user_profile.purchase_motivation.value 的值并返回对应选项，
不要重新分析原文，也不要输出 JSON 本身。如果值是 null，返回"无法判断"。

【JSON】
{{profile_json}}
```

---

## 关于 age / gender

本轮不新增这两个字段。车评文本很难可靠推断精确年龄和性别，强行加字段容易变成模型瞎猜，污染人群地图的可信度。demo 阶段人群地图按 `life_stage × city_tier × purchase_motivation` 三维下钻；age/gender 在方案里标注为"当前数据源（车评文本）覆盖弱，需接入行为数据/交强险数据补全"的规划项。

## 关于以后数据量变大怎么办

现在 1375 条量级，AI 字段够用。以后数据量真的涨上去了（比如接入自动化持续爬取），批量打标这一步可以换成多维表格的"自动化工作流"（记录新增时触发 → HTTP 请求节点调用 LLM 接口 → 写回字段），依然是纯飞书原生能力，不需要跳出飞书生态，只是把"AI 字段"换成"自动化+HTTP节点"，下游 Aily/人群地图/数字人这些消费方完全不受影响。现在数据量没到这个门槛，不需要现在就搭这套。

## 质量检查（跑完小样本后）

- `profile_json` 里各字段 null 占比是否过高（> 60%），过高说明 prompt 或数据质量有问题
- 抽 5~10 条人工核对 `profile_json` 里的 `evidence`/`key_highlights`/`key_pain_points` 是否真的是原文摘录，而不是模型改写或编造
- 抽几条对比 `life_stage`/`city_tier`/`purchase_motivation` 这 3 个抽取字段的值，和 `profile_json` 里对应的 value 是否一致（应该 100% 一致，因为是直接读取不是重新判断；如果不一致，说明抽取字段的提示词没写对，模型在"重新分析"而不是"读取"）
