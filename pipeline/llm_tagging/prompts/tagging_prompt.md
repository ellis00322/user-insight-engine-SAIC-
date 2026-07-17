# LLM 结构化打标 Prompt

> **⚠️ 已废弃（v1 方案）**：本文档是 `tagger.py` 的 Prompt/Schema 定义，`tagger.py` 已停用——
> 人工抽检发现约 73% 的 evidence 字段是本文档 Schema 里的占位说明文字被模型抄了回来，不是
> 真实原文引用（详见 `pipeline/llm_tagging/README.md` 的「版本变更记录」）。当前打标主路径见
> [`feishu_bitable_fields.md`](feishu_bitable_fields.md)。本文档保留仅作历史参考。

**版本**：v0.2（与 `pipeline/llm_tagging/tagger.py` 里实际发给 LLM 的 prompt 保持一致，这里是唯一权威定义）  
**适用场景**：对单条车主口碑评论进行结构化用户画像提取  
**模型要求**：支持长上下文（≥ 4K tokens）的指令遵循型模型；当前接入智谱 GLM-4-Flash

**v0.2 相对 v0.1 的变化**：
- `city_tier`（城市线级）从这里移除，不再由 LLM 从评论文本推断——ETL 清洗阶段（`pipeline/etl/clean_reviews.py`）改成直接用懂车帝结构化字段 `buy_place`（购车地点）确定性映射，覆盖率从 LLM 推断的约 15% 提升到 85%，更可靠，见 `data-feasibility/field-schema.md`
- 新增 `gender`（性别）字段。评论文本里"我老婆""作为宝妈"这类间接线索覆盖率约 11%，和已有的 `life_stage` 字段（约 12%）相当，数据支撑得住
- 曾经评估过加 `age_bracket`（年龄段），实测评论文本里能间接推断年龄的线索只有约 2.7%，覆盖率比其他字段低一个数量级，且还要再细分多个档位，分母太小没有统计意义，**最终决定不加**这个字段

---

## System Prompt

```
你是一位专注于汽车行业的用户研究专家，擅长从车主评论中提取结构化的用户洞察。

你的任务是分析一条车主口碑原文，按照指定 JSON 格式输出结构化标签。

严格规则（违反将导致输出无效）：
1. 只能从原文中提取或合理推断信息，禁止编造任何未在原文中提及或暗示的内容
2. 原文完全没有任何相关线索（哪怕是间接线索）时，才填 null；只要原文出现相关的间接线索，
   就应该基于这些线索给出最合理的推断，不要因为线索不是直接明说就默认填 null。
   例如 gender 可以从"我老婆""我老公""作为宝妈""我们男人"这类自称/关系词间接推断，
   这个字段车评原文通常线索较少，大部分情况下会是 null，这是正常的，不要为了填满字段而编造
3. evidence 字段必须直接引用原文中的具体片段，不得改写或总结；value 为 null 时 evidence
   也必须是 null
4. 情感强度（intensity）基于原文措辞力度判断，1=轻微，5=强烈
5. 输出必须是合法的 JSON，不得包含任何注释或额外文字
```

---

## User Prompt 模板

```
请对以下车主评论进行结构化分析，严格按照 JSON Schema 输出，不要输出任何 JSON 以外的内容。

【评论原文】
{review_text}

【输出格式】
{
  "user_profile": {
    "life_stage": {
      "value": "已婚有娃 | 已婚无娃 | 未婚 | 退休 | null",
      "evidence": "支持该判断的原文引用，或 null"
    },
    "purchase_motivation": {
      "value": "家用 | 商务接待 | 个人通勤 | 换购升级 | 首次购车 | null",
      "evidence": "支持该判断的原文引用，或 null"
    },
    "purchase_stage": {
      "value": "已购车 | 意向中 | 对比选购 | null",
      "evidence": "支持该判断的原文引用，或 null"
    },
    "gender": {
      "value": "男 | 女 | null",
      "evidence": "支持该判断的原文引用，或 null"
    }
  },
  "dimension_sentiments": [
    {
      "dimension": "续航 | 智能驾驶 | 内饰 | 充电体验 | 售后服务 | 价格 | 外观 | 空间 | 动力性能 | 其他",
      "sentiment": "正面 | 负面 | 中性",
      "intensity": 1,
      "evidence": "触发该标签的原文引用（必填，不得为 null）"
    }
  ],
  "key_highlights": [
    "直接引用原文中表达满意或称赞的短语，最多 3 条，无则返回空数组 []"
  ],
  "key_pain_points": [
    "直接引用原文中表达不满或抱怨的短语，最多 3 条，无则返回空数组 []"
  ],
  "usage_scenarios": [
    "通勤 | 家庭出行 | 长途自驾 | 商务接送 | 其他"
  ],
  "meta": {
    "confidence": "high | medium | low",
    "confidence_reason": "简述整体可推断程度，如'评论详细，大部分字段可从原文直接推断'"
  }
}
```

---

## 字段说明

### `user_profile`

| 字段 | 说明 | 典型触发词示例 |
|------|------|----------------|
| `life_stage` | 用户当前人生阶段 | "带娃""孩子上学""二宝""老婆""单身" |
| `purchase_motivation` | 主要购车目的 | "接送孩子""公司报销""换掉油车""第一台车" |
| `purchase_stage` | 购车决策阶段 | "提车一个月""还在看""和 XX 对比" |
| `gender` | 用户性别（间接推断，覆盖率约 11%，多数情况为 null） | "我老婆""作为宝妈""我们男人" |

> `city_tier`（城市线级）不在这里——由 ETL 清洗阶段直接从懂车帝结构化字段 `buy_place`（购车地点）映射得出，不经过 LLM 推断，见 `pipeline/etl/clean_reviews.py`。

### `dimension_sentiments`

- 一条评论可包含多个维度，每个维度单独输出一条记录
- `intensity` 参考：1=轻微（"还行"）/ 3=明确（"很好"）/ 5=强烈（"完全无法接受""爱到不行"）
- 若原文同一维度同时有正负面描述，分别输出两条记录

### `meta.confidence`

- `high`：关键字段（life_stage / purchase_motivation）均可推断
- `medium`：主要字段可推断，部分为 null
- `low`：评论过短或信息量不足，大部分字段为 null

---

## 示例

**输入：**
> 提车三个月了，主要用来接送孩子上下学，偶尔周末长途。续航真的很给力，冬天实测也有 520 公里，充电比较慢是唯一遗憾，家里装了慢充桩问题不大。内饰豪华感很强，老婆很满意。

**期望输出（节选）：**
```json
{
  "user_profile": {
    "life_stage": {
      "value": "已婚有娃",
      "evidence": "接送孩子上下学；老婆很满意"
    },
    "purchase_motivation": {
      "value": "家用",
      "evidence": "主要用来接送孩子上下学，偶尔周末长途"
    },
    "purchase_stage": {
      "value": "已购车",
      "evidence": "提车三个月了"
    }
  },
  "dimension_sentiments": [
    {
      "dimension": "续航",
      "sentiment": "正面",
      "intensity": 4,
      "evidence": "续航真的很给力，冬天实测也有 520 公里"
    },
    {
      "dimension": "充电体验",
      "sentiment": "负面",
      "intensity": 2,
      "evidence": "充电比较慢是唯一遗憾"
    },
    {
      "dimension": "内饰",
      "sentiment": "正面",
      "intensity": 3,
      "evidence": "内饰豪华感很强"
    }
  ],
  "key_highlights": ["续航真的很给力", "内饰豪华感很强"],
  "key_pain_points": ["充电比较慢是唯一遗憾"],
  "usage_scenarios": ["家庭出行", "长途自驾"],
  "meta": {
    "confidence": "high",
    "confidence_reason": "评论信息丰富，用户特征、购车动机、主要维度均可从原文直接推断"
  }
}
```

---

## 已知边界情况处理

| 情况 | 处理方式 |
|------|----------|
| 评论极短（< 15 字） | 输出时设 `confidence: low`，大部分字段为 null |
| 评论为转述他人体验 | `purchase_stage` 设 null，不推断 |
| 提及多款竞品对比 | 只提取与目标车型相关的维度评价 |
| 同维度正负并存 | 分两条记录输出，各自标注情感和证据 |
| 评论含广告性质文字 | 可在 meta 中注明，但仍按正常流程处理可用部分 |
