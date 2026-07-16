# 参考资料列表（References）

本项目调研主要围绕汽车用户洞察、消费者研究、用户社区运营以及 LLM + UGC 分析方法展开。以下资料用于支持「画像准确率引擎」方案中的数据来源设计、用户画像方法论以及 AI 洞察技术路线。

| 序号 | 类别 | 来源 | 资料标题 | 链接 | 与本项目的关系 |
|---|---|---|---|---|---|
| 1 | 汽车 UGC 数据 | 汽车之家 | 汽车之家口碑发表规范 | https://club.autohome.com.cn/bbs/thread/5f8da636ec59df8e/73843875-1.html | 该规范要求车主口碑基于真实用车体验，并鼓励结合个人情况、用车场景和选车理由进行详细表达。它支持我将汽车口碑作为用户画像、购车动机和使用场景分析的数据来源。 |
| 2 | 汽车 UGC 数据 | 汽车之家 | 汽车之家汽车口碑页面 | https://k.m.autohome.com.cn/ | 该页面展示按车型组织的车主评价和产品优缺点，可作为汽车垂直 UGC 数据结构、车型对比和关注维度设计的参考。 |
| 3 | 消费者洞察 | NielsenIQ | Automotive | https://nielseniq.com/global/en/insights/automotive/ | NielsenIQ 的汽车行业洞察将市场趋势、消费者信息和业务决策结合。本项目参考其消费者细分思路，但使用持续采集的 UGC 和自动化标签降低传统研究的周期与成本。 |
| 4 | 用户反馈与产品迭代 | Tesla | Software Updates | https://www.tesla.com/support/software-updates | Tesla 通过 OTA 软件更新持续向车辆提供功能和体验改进。该资料用于说明汽车产品能够在上市后持续迭代，为本项目的用户反馈追踪和画像漂移分析提供案例参考。 |
| 5 | 用户反馈与服务入口 | Tesla | Customer and Product Support | https://www.tesla.com/support | Tesla 为车主提供应用内个性化支持和问题反馈入口。该资料用于说明车企可在车辆生命周期内持续接收用户问题和服务需求。 |
| 6 | 数据合规 | Tesla | Customer Privacy Notice | https://www.tesla.com/legal/privacy | 该隐私说明介绍 Tesla 对用户和车辆相关数据的收集、使用、共享与保护原则。本项目参考其透明化思路，在企业数据接入时区分公开 UGC、内部数据和个人敏感信息。 |
| 7 | 实际模型与 API | 智谱 AI | 智谱 AI 开放平台：平台介绍 | https://docs.bigmodel.cn/cn/guide/start/introduction | 该文档介绍 GLM 系列模型、自然语言指令处理和 API 集成能力，是本项目使用智谱 LLM 进行汽车 UGC 标签提取的主要官方技术来源。 |
| 8 | 实际模型与 API | 智谱 AI | 智谱 AI 开放平台：API 使用概述 | https://docs.bigmodel.cn/cn/api/introduction | 该文档说明智谱开放平台的 API 端点、身份验证和调用方式，可支持项目技术文档中的模型接入和密钥管理说明。 |
| 9 | 模型技术背景 | Team GLM | ChatGLM: A Family of Large Language Models from GLM-130B to GLM-4 All Tools | https://arxiv.org/abs/2406.12793 | 论文介绍 ChatGLM 到 GLM-4 系列的发展、中文与英文训练、长文本和工具调用能力，为智谱 GLM 系列的技术背景提供依据。 |
| 10 | 模型技术背景 | Zeng et al. | GLM-130B: An Open Bilingual Pre-trained Model | https://arxiv.org/abs/2210.02414 | 论文介绍 GLM-130B 的中英双语预训练与工程方法，可作为 GLM 模型体系早期技术基础的参考。 |
| 11 | LLM 任务评估 | Chang et al. | A Survey on Evaluation of Large Language Models | https://arxiv.org/abs/2307.03109 | 论文总结 LLM 应评估什么、在哪里评估和如何评估。本项目据此强调不能只依赖模型生成结果，而要增加人工抽检、字段可提取率、证据完整率和历史车型回测。 |
| 12 | UGC 属性与情感分析 | Simmering and Huoviala | Large Language Models for Aspect-Based Sentiment Analysis | https://arxiv.org/abs/2310.18025 | 论文研究 LLM 在属性级情感分析中的表现，并讨论提示设计、微调和成本之间的权衡。它支持本项目从评论中同时提取“产品维度 + 情感倾向”。 |

---

## 3. 资料与项目模块的对应关系

| 项目模块 | 主要参考资料 | 使用方式 |
|---|---|---|
| UGC 数据采集与清洗 | 汽车之家口碑规范、汽车口碑页面 | 确认车主评价中可包含用车场景、选车理由和产品优缺点，并据此设计清洗规则和字段结构。 |
| 消费者分群与人群地图 | NielsenIQ Automotive | 参考消费者细分和市场洞察框架，将传统调研维度转化为可自动聚合的标签。 |
| 用户反馈与动态追踪 | Tesla Software Updates、Tesla Support | 参考车辆上市后持续收集问题、更新功能和管理用户生命周期的思路。 |
| 模型接入 | 智谱 AI 平台介绍、API 使用概述 | 说明项目实际调用的模型来源、API 接入方式和密钥管理要求。 |
| 中文 UGC 理解 | ChatGLM / GLM 系列论文 | 支持使用智谱 LLM 处理中文汽车评论和结构化信息抽取。 |
| 产品关注点与情感分析 | Large Language Models for Aspect-Based Sentiment Analysis | 支持从同一条评论中识别产品属性、用户态度和对应证据。 |
| 模型输出验证 | A Survey on Evaluation of Large Language Models | 支持人工抽检、任务级评价和回测校准，而不是把模型输出直接视为事实。 |
| 数据合规 | Tesla Customer Privacy Notice | 参考公开说明、用途限定和数据保护原则；正式接入企业数据时仍需遵循上汽内部制度和适用法律。 |

---

## Research Summary

通过以上资料调研可以发现：

目前行业已经具备：

- 汽车用户数据采集能力；
- 消费者画像分析方法；
- 用户反馈驱动产品优化流程；
- LLM 自动化文本理解能力。

但是现有方案普遍缺少：

> 对 AI 生成用户画像准确性的量化验证。

因此，本项目提出的「画像准确率引擎」进一步建立：
UGC 数据采集
↓
LLM 结构化标签
↓
用户画像生成
↓
历史车型回测
↓
准确率评估
↓
方法校准
↓
支持新车立项预测


通过回测机制，使 AI 用户洞察从“生成结果”升级为“可验证、可解释、可持续优化的决策系统”。
