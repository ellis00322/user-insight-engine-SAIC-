# 统一字段说明

> **状态：内容待填**

本文档定义各数据源清洗后的统一字段 Schema，作为 L1 数据层输出的标准格式。

## 评论记录（review）字段

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| review_id | string | 全局唯一 ID | `dcd_3982_00001` |
| source | string | 来源平台 | `dongchedi` |
| car_name | string | 车型名称（标准化） | `蔚来ET7` |
| series_id | string | 平台内车系 ID | `3982` |
| content | string | 评论全文（已脱敏） | - |
| rating_overall | float | 综合评分（归一化至 1–5） | `4.2` |
| rating_dims | dict | 各维度评分 | `{"续航": 4.5, "内饰": 4.0}` |
| pub_date | date | 发布日期 | `2024-03-15` |
| phase | string | 相对上市日的阶段 | `pre` / `post` |
| llm_tags | dict | LLM 打标结果（见打标 prompt） | - |

## 用户画像标签体系（待定义）

> 待 LLM 打标方案验证后补充
