"""
第 1 阶段：用 Scrapling 抓取一个静态网页（不需要 JS 渲染的普通 HTML 页面）

本脚本做 3 件事：
1. 用 Fetcher 发起一次 HTTP GET 请求，拿到网页内容
2. 用 CSS 选择器从网页里提取书名、作者、标签
3. 打印结果，验证环境部署成功

运行方式（在项目目录下）：
    .venv\\Scripts\\python.exe step1_static.py
"""

# 从 scrapling.fetchers 导入 Fetcher
# Fetcher 底层用的是 curl_cffi（可以理解为"会伪装成真实浏览器的 requests"）
from scrapling.fetchers import Fetcher

# 目标网址：quotes.toscrape.com 是官方专门给爬虫练习用的网站，允许随便抓
URL = "https://quotes.toscrape.com/"

# 发起 GET 请求
# impersonate="chrome" 表示让请求的 TLS 指纹伪装成 Chrome 浏览器
# （很多网站会检查这个指纹，普通 requests 容易被识别成爬虫）
page = Fetcher.get(URL, impersonate="chrome")

# page.status 是 HTTP 状态码，200 表示请求成功
print("HTTP 状态码:", page.status)

# page.css() 用 CSS 选择器定位元素
# "title::text" 中的 ::text 是 Scrapling 的语法，表示"取这个标签里的纯文本"
print("网页标题:", page.css("title::text").get())

# .quote 选中页面上所有"名言卡片"，返回一个列表
quotes = page.css(".quote")
print(f"共找到 {len(quotes)} 条名言\n")

# 遍历前 3 条，演示最常用的取值方法
for q in quotes[:3]:
    text = q.css(".text::text").get()        # 名言正文
    author = q.css(".author::text").get()    # 作者
    tags = q.css(".tag::text").getall()      # 标签（可能有多个，用 getall 取全部）
    print(f"作者: {author}")
    print(f"名言: {text}")
    print(f"标签: {tags}")
    print("-" * 40)
