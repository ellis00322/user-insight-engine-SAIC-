# pipeline/crawler

数据采集模块。负责从各平台抓取评论原文、评分和车型基础信息，清洗后输出统一格式的 JSON 文件。

## 文件说明

| 文件 | 状态 | 说明 |
|------|------|------|
| `http_utils.py` | ✅ 已就绪 | 通用 HTTP 请求工具：UA 轮换、随机延迟、自动重试。从 AutoPulse 项目请求层提取。 |
| `dongchedi.py` | 待开发 | 懂车帝口碑采集。目标车型确认后实现。 |
| `autohome.py` | 待开发 | 汽车之家口碑采集。 |
| `weibo.py` | 待开发 | 微博话题采集（仅上市前讨论）。 |

## 使用约束

- 所有采集脚本须遵守目标网站 `robots.txt` 规定
- 请求频率：随机延迟 2–5 秒，禁止高频并发
- 采集结果写入 `data/raw/`（已在 .gitignore 中排除，不提交原始数据）
- 样本脱敏后放入 `data-feasibility/sample_data/` 才可提交

## 依赖

```
requests
beautifulsoup4
lxml
```
