# pipeline/llm_tagging

LLM 结构化打标模块。将原始评论文本转化为结构化用户画像标签。

## 处理流程

```
原始评论文本
    │
    ▼
tagging_prompt.md 中的提示词模板
    │
    ▼
LLM API（Qwen / GPT-4o）
    │
    ▼
结构化 JSON 输出（用户特征 + 关注维度 + 情感极性）
    │
    ▼
写入数据库 / 用于人群聚类
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `prompts/tagging_prompt.md` | 打标 prompt 模板与字段说明 |
| `tagger.py` | 待开发：批量调用 LLM API 的执行脚本 |
| `validator.py` | 待开发：对 LLM 输出进行格式校验和质量抽检 |

## 质量控制要求

- LLM 输出必须严格为 JSON，不通过 schema 校验的条目标记为 `parse_error`
- 对 `null` 比例过高（> 60%）的字段，需检查 prompt 或数据质量
- 建议对 5% 的样本进行人工复核，记录误标类型
