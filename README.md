# 可回测的汽车用户画像引擎

> 面向上汽乘用车「AI 驱动用户洞察引擎」命题的开题调研与原型仓库

---

## 痛点摘要

当前汽车行业用户洞察存在三个核心缺陷：

1. **知识不沉淀**：洞察报告以 PPT 形式存在，分析结论无法检索、复用和追踪，每次决策都在重新出发
2. **画像无验证闭环**：用户画像的预测准确率从未被量化——没有人知道上个季度的洞察到底对了多少
3. **竞品追踪不可规模化**：跨车型、跨平台的系统性竞品监测依赖人工阅读，无法响应市场变化速度

---

## 核心创新：画像回测机制

本方案的核心创新是引入**可量化的画像回测闭环**：以新车上市日为时间锚点，利用上市前公开数据（竞品口碑、预热讨论、媒体评测）生成预测用户画像快照，在上市后与真实车主口碑进行量化对比，输出画像准确率得分并归因偏差来源。

```mermaid
flowchart LR
    A["📊 上市前公开数据\n竞品口碑 / 预热讨论\n媒体评测报告"]
    B["🤖 LLM 结构化打标\n用户特征提取\n关注维度识别"]
    C[("🗄️ 预测画像快照\n存档 · 锁定时间戳")]
    D["📝 上市后真实口碑\n车主评价 / 晒单\n公开销量结构"]
    E["📐 量化回测比对\nPOS · DMR · SDA"]
    F["📈 偏差归因\n数据偏差 / 产品变化\n市场扰动 / 模型局限"]

    A --> B --> C
    D --> E
    C --> E
    E --> F
    F -->|"迭代优化"| B
```

**五步闭环**：  
① 采集上市前竞品口碑与预热讨论  
② LLM 结构化提取用户画像标签，生成预测分布并存档快照  
③ 上市后采集真实车主口碑，同样经 LLM 打标  
④ 以 Jensen-Shannon 散度、维度匹配率等指标量化两侧画像重合度  
⑤ 对低分维度逐一归因，反馈优化打标策略与数据源选择

---

## 四层架构

```mermaid
graph TB
    subgraph L1["L1 数据层 · 多源采集融合"]
        A1["懂车帝 / 汽车之家\n车主口碑"]
        A2["微博 / 小红书 / 抖音\nUGC 讨论"]
        A3["媒体评测 / 试驾报告"]
        A4["竞品车型历史数据\n（上市前参照系）"]
    end

    subgraph L2["L2 洞察层 · LLM 结构化 + 动态人群地图"]
        B1["LLM 结构化打标\n用户画像字段提取"]
        B2["人群聚类\n标签体系构建"]
        B3["动态人群地图\n时序变化追踪"]
    end

    subgraph L3["L3 验证层 · 回测校准（核心创新）"]
        C1["上市前预测画像\n快照存档"]
        C2["上市后真实口碑\n采集解析"]
        C3["重合度量化\n+ 偏差归因"]
    end

    subgraph L4["L4 应用层 · Aily RAG 问答 + 数字人"]
        D1["飞书 Aily\nRAG 知识库问答"]
        D2["数字人\n用户模拟对话"]
        D3["洞察报告\n自动生成"]
    end

    L1 --> L2
    L2 --> L3
    L3 -->|"偏差反馈"| L2
    L3 --> L4
```

---

## 仓库导航

| 目录 / 文件 | 说明 |
|-------------|------|
| [`docs/proposal.md`](docs/proposal.md) | 开题报告正文（内容待填） |
| [`docs/architecture.md`](docs/architecture.md) | 四层架构详细说明 |
| [`research/industry-landscape.md`](research/industry-landscape.md) | 行业调研：现有洞察工具的不足与机会点 |
| [`research/benchmark-cases.md`](research/benchmark-cases.md) | 对标案例研究与竞品矩阵 |
| [`research/ugc-analysis.md`](research/ugc-analysis.md) | UGC 样本分析框架与质量评估 |
| [`research/references.md`](research/references.md) | 参考资料清单 |
| [`data-feasibility/feasibility-report.md`](data-feasibility/feasibility-report.md) | 各数据源可行性评估表 |
| [`data-feasibility/field-schema.md`](data-feasibility/field-schema.md) | 统一字段 Schema 说明 |
| [`pipeline/crawler/`](pipeline/crawler/) | 数据采集模块（含通用 HTTP 工具） |
| [`pipeline/llm_tagging/prompts/tagging_prompt.md`](pipeline/llm_tagging/prompts/tagging_prompt.md) | **LLM 结构化打标 Prompt 初稿**（含字段说明与示例） |
| [`backtest/design.md`](backtest/design.md) | **回测实验设计**（指标公式 / 数据源规划 / 偏差归因框架） |

---

## MVP Demo 范围与飞书工具链

比赛演示阶段采用小规模、可在有限时间内跑通的简化版闭环，正式规模的爬虫自动化与完整回测留待赛后放大（见"当前进度"）。demo 阶段各层对应的执行工具：

| 架构层 | 生产方案（长期目标） | Demo 阶段执行方式 |
|--------|----------------------|--------------------|
| L1 数据层 | 爬虫自动采集，≥ 300 条 / 车型 | 手动收集单一竞品车型的 50–100 条公开评论 |
| L2 洞察层 | Python 脚本批量调用 LLM API 打标 | **飞书多维表格 AI 字段/公式**，复用 [`tagging_prompt.md`](pipeline/llm_tagging/prompts/tagging_prompt.md) 的字段定义与 evidence 要求，做人群筛选看板 |
| L3 验证层 | 严格按 T0 时间戳切分的上市前 / 后 ≥ 6 个月窗口回测 | 将 50–100 条样本人为切分为两组模拟"预测组 / 真实组"，跑通一次完整 POS / DMR / SDA 计算，验证链路可行性 |
| L4 应用层 | 飞书 Aily RAG 问答 + 数字人对话 | **飞书 Aily** 基于多维表格结构化结果回答，回答必须注明依据的样本 / 聚类与置信度；数字人在 demo 阶段做静态"用户人物卡"视觉设计，暂不做对话式 AI |

demo 验证的是"文本进 → 结构化画像出 → 可筛选查询 → 带依据的 AI 问答 → 回测评分"这条完整链路能跑通，而不是最终样本规模。

---

## 当前进度

- [x] 仓库搭建与目录结构初始化
- [x] README 与架构文档完成
- [x] 数据可行性评估框架建立
- [x] LLM 打标 Prompt 初稿完成
- [x] 回测实验设计提纲完成
- [ ] 目标车型确认（上汽乘用车产品线）
- [ ] MVP Demo：手动采集 50–100 条评论并导入飞书多维表格
- [ ] 飞书多维表格 AI 字段结构化打标（复用 tagging_prompt.md）
- [ ] 简化版回测演示（demo 样本切分模拟预测组/真实组）
- [ ] 飞书 Aily 问答原型接入
- [ ] 正式规模样本数据采集（上市前 + 上市后各 ≥ 300 条 / 车型）
- [ ] 完整回测指标计算与偏差归因

---

## 评估指标说明

| 指标 | 名称 | 含义 |
|------|------|------|
| **POS** | Profile Overlap Score | 预测画像与真实画像的分布相似度（JS 散度转化，越高越好） |
| **DMR@K** | Dimension Match Rate | Top-K 关注维度预测命中率 |
| **SDA** | Sentiment Direction Accuracy | 维度情感方向（正/负/中）预测准确率 |
| **CBS** | Composite Backtesting Score | 综合回测得分 = 0.5×POS + 0.3×DMR@5 + 0.2×SDA |

---

## 免责声明

- 所有数据均来源于公开渠道（懂车帝、汽车之家、微博、小红书等平台的公开内容）
- 数据仅用于本次竞赛研究目的，不用于商业用途
- 纳入分析的样本已完成脱敏处理，不含任何用户个人身份信息
- 本仓库不存储任何原始采集数据（`data/raw/` 已加入 `.gitignore`）
