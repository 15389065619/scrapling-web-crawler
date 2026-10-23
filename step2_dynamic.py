"""
第 2 阶段：动态网页 + 反爬

本阶段要理解一件事：
    有些网页的 HTML 里本来没有数据，数据是浏览器执行 JavaScript 之后才"画"上去的。
    纯 HTTP 请求只能拿到"骨架"，拿不到数据；这时必须启动一个真正的浏览器。

脚本分 3 个实验：
    A. 用 Fetcher（纯 HTTP）抓 JS 渲染页面  -> 抓不到数据
    B. 用 StealthyFetcher（无头 Chromium）  -> 抓得到数据
    C. 用 page_action 在浏览器里点击"下一页" -> 抓第二页数据

运行方式（在项目目录下）：
    .venv\\Scripts\\python.exe step2_dynamic.py
"""

from scrapling.fetchers import Fetcher, StealthyFetcher

# 注意这个网址结尾是 /js/：它的名言数据由页面里的 JavaScript 动态插入
JS_URL = "https://quotes.toscrape.com/js/"


# ============ 实验 A：纯 HTTP 请求（对照组） ============
print("=" * 55)
print("实验 A：Fetcher 抓 JS 渲染页面")

# 只发 HTTP 请求，不执行任何 JavaScript
page_a = Fetcher.get(JS_URL, impersonate="chrome")
print("状态码:", page_a.status)
print("找到名言数:", len(page_a.css(".quote")))


# ============ 实验 B：启动真实浏览器 ============
print("=" * 55)
print("实验 B：StealthyFetcher 启动无头浏览器")

page_b = StealthyFetcher.fetch(
    JS_URL,
    headless=True,        # True=不弹出浏览器窗口；False=你能看见浏览器在自动操作
    network_idle=True,    # 等到网络请求安静 500ms 再返回，确保 JS 数据加载完
    disable_resources=True,  # 丢弃图片/字体/样式等无用资源，速度更快（可能影响极少页面）
)

print("状态码:", page_b.status)
print("找到名言数:", len(page_b.css(".quote")))

# 浏览器渲染后，数据就能被正常解析了
for q in page_b.css(".quote")[:2]:
    author = q.css(".author::text").get()
    text = q.css(".text::text").get()
    print(f"{author}: {text}")


# ============ 实验 C：在浏览器里做交互 ============
print("=" * 55)
print("实验 C：点击“下一页”后再抓取")


def click_next(page):
    """
    page_action 接收的参数 page 是 Playwright 的页面对象。
    浏览器打开目标网址后，会先执行这个函数，再返回网页内容。
    所以这里可以点击、滚动、输入、等元素出现，做人类会做的操作。
    """
    page.click("li.next a")            # 点击“Next →”链接，触发跳转到第二页
    page.wait_for_selector(".quote")   # 等第二页的名言卡片出现，防止抓早了


page_c = StealthyFetcher.fetch(
    JS_URL,
    headless=True,
    page_action=click_next,
    wait_selector=".quote",   # 等这个选择器出现后再返回（双保险）
    timeout=60000,            # 单次操作超时 60 秒；默认 30 秒
)

print("状态码:", page_c.status)
# 注意：这里拿到的是"点完下一页之后"的页面内容
print("第二页第一条作者:", page_c.css(".quote .author::text").get())
print("第二页名言总数:", len(page_c.css(".quote")))
