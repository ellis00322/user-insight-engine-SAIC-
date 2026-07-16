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
| 13 | 市场数据 | 中国汽车工业协会 / AP | China’s 2022 auto sales rise 9.5% but growth weakening | https://apnews.com/article/83fae6485077278a093321c9830e5219 | 引用中汽协数据说明 2022 年新能源汽车销量占汽车总销量的 25.6%，用于建立 2022—2025 年渗透率趋势基线。 |
| 14 | 市场数据 | 中国汽车工业协会 / 新华社 | 2023 年我国汽车产销量首次突破 3000 万辆 | https://www.news.cn/fortune/20240111/7d37a6ae40f6423286ad2e783d6fa6d9/c.html | 说明 2023 年新能源汽车销量为 949.5 万辆，市场占有率达到 31.6%。 |
| 15 | 市场数据 | 中国汽车工业协会 / 新华社 | 2024 年我国新能源汽车产销量均超 1200 万辆 | https://www.news.cn/fortune/20250113/815a44be04094bb6a1c770f0cff5daaf/c.html | 说明 2024 年新能源汽车销量为 1286.6 万辆，新车销量占比达到 40.9%。 |
| 16 | 市场数据 | 中国汽车工业协会 / 浙江省经信厅转载 | 两条主线支撑 2025 年汽车产销规模再创新高 | https://zjic.zj.gov.cn/ywdh/cyfz/202601/t20260115_23903518.shtml | 说明 2025 年新能源汽车销量为 1649 万辆，新车销量占比达到 47.9%。 |
| 17 | 数字化购车链路 | J.D. Power | 2025 China Sales Satisfaction Index (SSI) Study | https://china.jdpower.com/press-releases/2025-china-sales-satisfaction-index-ssi-study | 研究将线上体验和到店前沟通纳入购车与流失用户满意度评价，支持购车决策链路数字化的判断。 |
| 18 | 新能源用户变化 | J.D. Power | 2024 中国汽车市场年度洞察 | https://china.jdpower.com/zh-hans/press-releases/2024-China-Market-Insight | 指出 95 后在新能源汽车客户体验研究样本中的占比达到 30%，并强调线上线下无缝体验需求。 |
| 19 | 传统消费者研究 | McKinsey & Company | 2024 麦肯锡中国汽车消费者洞察 | https://www.mckinsey.com.cn/wp-content/uploads/2024/03/2024%E9%BA%A6%E8%82%AF%E9%94%A1%E4%B8%AD%E5%9B%BD%E6%B1%BD%E8%BD%A6%E6%B6%88%E8%B4%B9%E8%80%85%E6%B4%9E%E5%AF%9F%E6%8A%A5%E5%91%8A.pdf | 报告基于近 2500 名汽车消费者调研，可作为传统问卷、消费者分群和趋势研究方法的代表案例。 |
| 20 | 舆情与社交聆听 | 慧科讯业 | AI 舆情监测与全媒体分析产品 | https://www.wisers.com.cn/product/qqyqgljfx/20.html | 展示全媒体监测、社交聆听、情感分析、危机预警和自动报告能力，用于分析现有数字化舆情工具的边界。 |
| 21 | 新媒体矩阵管理 | 新榜 | 矩阵通：多平台新媒体矩阵管理系统 | https://matrix.newrank.cn/ | 展示跨平台账号管理、内容数据统计和运营效果评估能力，用于分析多平台数据管理工具。 |
| 22 | 汽车数据中台 | 中国信息通信研究院 | 车联网蓝皮书（数据赋能） | https://www.caict.ac.cn/kxyj/qwfb/bps/202501/P020250123581914886500.pdf | 说明车联网数据经过汇聚、处理和加工后可以支撑业务贯通、数智决策和产业服务创新。 |
| 23 | 用户反馈与产品迭代 | 中国信息通信研究院 | 车联网白皮书 | https://www.caict.ac.cn/english/research/whitepapers/202404/P020240430455753543361.pdf | 说明汽车厂商可持续收集车辆使用与用户反馈数据，并据此快速迭代产品功能。 |
| 24 | 企业知识问答 | 飞书 Aily | 欢迎使用飞书 Aily | https://aily.feishu.cn/hc/1u7kleqg/4q7o7as7 | 说明 Aily 可连接云文档、聊天记录、PDF、Excel 等企业知识，解决知识分散和利用率低的问题。 |
| 25 | 企业知识问答 | 飞书 | 飞书智能伙伴 Aily：了解知识问答 | https://www.feishu.cn/content/euuvns8t | 说明 Aily 可连接本地文件、飞书套件、企业业务系统和数据库，并以自然语言进行检索与总结。 |
| 26 | 汽车大模型案例 | 广汽集团 / 新华网 | 广汽集团以创新之力布局智能化下半场 | https://www.news.cn/auto/20240429/636a165e89d64f45982ab60235b59837/c.html | 展示广汽 AI 大模型平台、电子电气架构和智能网联大数据平台的产业应用方向。 |
| 27 | 汽车数字化案例 | 华为 / 广汽集团 | 广汽集团与华为签署数字化战略合作备忘录 | https://www.huawei.com/cn/news/2024/9/gac-strategy-mou | 说明双方在数字化转型、AI 大模型、智慧服务和智能生产等方向开展合作。 |

---

## 资料与项目模块的对应关系

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
| 新能源市场趋势 | 中汽协 2022—2025 年度数据 | 使用统一的新车销量占比口径，分析新能源汽车市场结构变化。 |
| 数字化购车链路 | J.D. Power 2025 SSI、2024 市场洞察 | 支撑线上体验、到店前沟通和年轻新能源用户增长的判断。 |
| 传统调研方法 | 2024 麦肯锡中国汽车消费者洞察 | 作为问卷调研和消费者分群方法的代表案例。 |
| 舆情与平台工具 | 慧科讯业、新榜矩阵通 | 分析全媒体监测、多平台管理与本方案画像回测能力之间的差异。 |
| 主机厂数据实践 | 中国信通院车联网白皮书 | 支撑车联网数据汇聚、数智决策和用户反馈驱动产品迭代的判断。 |
| 企业知识应用 | 飞书 Aily 官方资料 | 支撑结构化画像、企业知识连接和自然语言问答的应用设计。 |
| 汽车大模型趋势 | 广汽 AI 大模型平台、广汽与华为合作 | 说明大模型正进入汽车产品、服务和企业数字化流程。 |

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
质谱LLM 结构化标签
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
