# Scrapling 网页采集实战

基于 [Scrapling](https://github.com/D4Vinci/Scrapling) 0.5 的渐进式爬虫实践，覆盖从静态页面到 JS 动态渲染、再到真实站点（京东）反爬对抗的完整学习路径。

Scrapling 的核心优势是**浏览器指纹伪装**：`Fetcher` 底层基于 curl_cffi，可以模仿真实 Chrome 的 TLS 指纹；`StealthyFetcher` 内置 Chrome，针对反爬做了大量规避处理。

## 脚本一览

| 脚本 | 阶段 | 内容 |
|---|---|---|
| `step1_static.py` | 静态页面 | `Fetcher` 抓取 quotes.toscrape.com，提取书名 / 作者 / 标签 |
| `step2_dynamic.py` | 动态页面 | 三组对照实验：纯 HTTP 抓 JS 页面失败 → `StealthyFetcher` 成功 → `page_action` 点击下一页 |
| `step3_spider.py` | 工程化批量 | `Spider` 引擎自动翻页抓取 10 页 100 条名言，导出 JSON / CSV |
| `step4_jd_recon.py` | 真实站点侦察 | 京东搜索页：通过状态码、商品元素、拦截关键词三个信号判断是否被拦 |
| `step5_jd_browser.py` | 浏览器对抗 | 启动无头浏览器渲染京东搜索页，截图存证并提取 SKU / 标题 / 价格 |
| `step6_jd_spider.py` | 工程化批量 | 注入登录 Cookie 绕过登录墙，多页抓取 + SKU 去重 + 限速，导出 JSON / CSV |
| `step7_xhs_recon.py` | 侦察 | 小红书搜索页反爬强度探测 |
| `step8_shein_recon.py` | 侦察 | Shein 香港站页面结构探测 |
| `probe_js.py` | 侦察 | JS 动态渲染页面（js-delayed）的纯 HTTP 可达性探测 |

## 快速开始

```bash
pip install -r requirements.txt
scrapling install          # 安装浏览器与依赖

python step1_static.py
python step2_dynamic.py
python step3_spider.py
python step4_jd_recon.py
python step5_jd_browser.py
python step6_jd_spider.py
```

## 运行效果

`step1_static.py`（单页静态抓取）：

```text
HTTP 状态码: 200
网页标题: Quotes to Scrape
共找到 10 条名言

作者: Albert Einstein
名言: “The world as we have created it is a process of our thinking. ...”
标签: ['change', 'deep-thoughts', 'thinking', 'world']
```

`step3_spider.py`（自动翻页批量抓取）：

```text
[INFO] Saved 100 items to quotes.json
[INFO] Saved 100 items to quotes.csv

===== 抓取统计 =====
成功抓取条目: 100
发出的请求数: 10
失败请求数: 0
耗时(秒): 8.16
是否完整跑完: True
```

## 京东爬虫的登录 Cookie 配置

京东搜索页要求登录才返回商品数据，未登录请求会被重定向到登录页。`step6_jd_spider.py` 从项目根目录的 `jd_cookies.txt` 读取 Cookie：

```bash
# 1. 浏览器打开 https://search.jd.com 并登录
# 2. F12 -> Network -> 刷新页面 -> 点击任意 search.jd.com 请求
# 3. 复制 Request Headers 中 Cookie 的值（不要带 "Cookie: " 前缀）
# 4. 粘贴到 jd_cookies.txt（单行）
```

`jd_cookies.txt` 属于个人凭据，已在 `.gitignore` 中排除，不会被提交。

Cookie 会被解析为 `[{name, value, domain, path}]` 结构后注入浏览器上下文 —— 直接写在请求头里对真实浏览器无效。

## 关键实现要点

**1. 京东改版导致选择器失效**

旧教程中的 `li.gl-item` / `.p-name` 已全部失效，新版页面的 class 带哈希后缀（如 `_price_9y3st_31`），后缀会随版本变化。因此改用两类稳定锚点：

- 语义化类名：`div.plugin_goodsCardWrapper`（商品卡片）
- 属性前缀匹配：`[class*=_price_]`（价格，只匹配不变的前缀）

**2. 跨页 SKU 去重**

翻页时京东会重复返回部分商品，因此在业务层按 `data-sku` 去重，而不是只依赖 URL 去重。

**3. 翻页策略**

京东的「下一页」按钮是 JS 绑定且没有 `href`，因此直接按 `page` 参数构造 URL 列表（`&page=1,3,5...`）。

**4. 侦察先行**

真实站点第一步不是写解析代码，而是发一次请求确认对方返回了什么：状态码、是否存在商品元素、是否出现验证/拦截关键词。原始响应统一存盘留档，避免误判。

## 抓取结果

`step6_jd_spider.py` 默认抓取 3 页、每页约 30 条，SKU 去重后输出 `jd_goods.json` 与 `jd_goods.csv`，字段包含：SKU、标题、价格、店铺、评论数、商品链接。

## 合规说明

- quotes.toscrape.com 为官方公开的爬虫练习站点
- 京东相关脚本仅用于个人技术学习，默认低频抓取（3 页）；实际使用请遵守目标站点的 robots.txt 与服务条款，控制请求频率，不要用于大规模商业采集
