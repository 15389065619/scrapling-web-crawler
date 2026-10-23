"""
探测 quotes.toscrape.com/js/ —— JS 动态渲染版
确认纯 HTTP 能不能拿到数据
"""
from scrapling.fetchers import Fetcher

URL = "https://quotes.toscrape.com/js-delayed/"

print("=== 纯 HTTP 试 quotes.toscrape.com/js-delayed/ (真·AJAX 动态) ===")
page = Fetcher.get(URL, impersonate="chrome", timeout=30)
html = page.body if isinstance(page.body, str) else page.body.decode("utf-8", "ignore")
print(f"状态码: {page.status}, 长度: {len(html)}")
print(f"quote 卡片(渲染后): {html.count('class=')}")
print(f"内嵌 data 数组: {'data = [' in html}")
print(f"骨架/加载提示: {html.count('loading')}")

with open("probe_quotes_delayed.html", "w", encoding="utf-8") as f:
    f.write(html)
print("\n前 400 字符:")
print(html[:400])
