# pipeline/crawler

数据采集模块。负责从各平台抓取评论原文、评分和车型基础信息，清洗后输出统一格式的 JSON 文件。

## 文件说明

| 文件 | 说明 |
|------|------|
| `dongchedi_playwright_crawler.py` | 懂车帝口碑抓取主脚本，已验证可稳定批量抓取。 |
| `dongchedi_parsing.py` | 口碑页 `__NEXT_DATA__` 解析逻辑，字段键名已用真实响应核对。 |

## 使用约束

- 所有采集脚本须遵守目标网站 `robots.txt` 规定
- 请求频率：每页之间随机延迟 1.5–3 秒，禁止高频并发
- 采集结果写入 `data/raw/`（已在 `.gitignore` 中排除，不提交原始数据）
- 样本脱敏后放入 `data-feasibility/sample_data/` 才可提交
- 只保留匿名化的结构化评价内容和评分，不采集用户 ID/昵称/头像/主页链接等可定位到个人的信息；`review_id` 用的是平台帖子 ID（`gid_str`），不是用户 ID

## 懂车帝口碑抓取

### 原理

懂车帝口碑页每一页都有独立 URL：

```
https://www.dongchedi.com/auto/series/score/{series_id}-x-S0-x-x-x-{page}
```

页面数据由 Next.js 服务端直出，内嵌在 HTML 的 `__NEXT_DATA__` script 标签里（`pageProps.reviewListData.review_list`），不需要额外调用签名接口，也不需要维持登录会话——每一页单次打开、解析、关闭浏览器即可，天然规避了长会话可能触发的登录状态异常。

登录态通过 `.env` 里的 `DONGCHEDI_COOKIE` 注入（不登录会被弹到手机验证码登录页，看不到口碑内容）。

### 用法

```
python pipeline/crawler/dongchedi_playwright_crawler.py --series_id 9660 --max_pages 20 --dump_raw
```

- `--series_id`：车系 ID（例如智己 L6 = 9660），在懂车帝车系页 URL 里能找到（`dongchedi.com/auto/series/{id}`）
- `--max_pages`：最多抓取页数，每页约 15 条
- `--dump_raw`：额外把每页原始数据存一份到 `--debug_dir`（默认 `data/debug/`），用于核对/修正 `dongchedi_parsing.py` 里的字段解析
- 每车型的输出按 `review_id` 去重后追加写入 `data/raw/{series_id}_reviews.jsonl`，多次分批抓取会自动跳过已有数据，不会重复
- 单页连续两次尝试都失败、或连续 3 页失败会自动停止（大概率已到最后一页或反爬拦截变严）

### 依赖

```
python-dotenv
playwright
```

首次使用需安装 Chromium 内核：`playwright install chromium`
