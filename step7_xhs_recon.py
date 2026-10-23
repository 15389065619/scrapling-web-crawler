"""
新项目:小红书笔记爬虫 —— 阶段 1:侦察

目标:搞清楚小红书搜索页的反爬强度和数据结构。
方法:先用纯 HTTP 请求试探,再根据结果决定要不要上浏览器/Cookie。

运行方式:
    .venv\\Scripts\\python.exe step7_xhs_recon.py
"""

from scrapling.fetchers import Fetcher

# 小红书搜索页,关键词 python
URL = "https://www.xiaohongshu.com/search_result?keyword=python"

# 纯 HTTP 请求,伪装 Chrome
page = Fetcher.get(URL, impersonate="chrome", timeout=30)
html = page.body if isinstance(page.body, str) else page.body.decode("utf-8", "ignore")

print("HTTP 状态码:", page.status)
print("网页长度:", len(html))

# 小红书常见标记
for kw in ["笔记", "xhs", "note", "小红书", "login", "登录", "captcha", "验证"]:
    print(f"  '{kw}': {html.count(kw)} 次")

# 存下来人工看
with open("xhs_recon.html", "w", encoding="utf-8") as f:
    f.write(html)
print("\n已存到 xhs_recon.html")
