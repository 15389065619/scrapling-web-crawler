"""
新项目:京东商品爬虫 —— 阶段 2:浏览器对抗

阶段 1 侦察结论:京东搜索页是"骨架屏",商品数据由 JS 动态填充。
本阶段用 StealthyFetcher 启动真实浏览器,等 JS 把商品"画"出来再解析。

开发过程中的真实插曲(写进简历都不丢人):
    京东改版了!旧教程里的 li.gl-item / .p-name 选择器已全部失效。
    新版页面的 class 名是"哈希后缀"的(如 _price_9y3st_31),后缀随时会变,
    必须用两类稳定锚点:
      1. 语义化类名:plugin_goodsCardWrapper(商品卡片)
      2. 属性前缀匹配:[class*=_price_](价格,只匹配不变的前缀)

脚本做 3 件事:
    1. 启动无头浏览器打开京东搜索页,主动等商品卡片出现
    2. 截图存证:浏览器看到的画面存成 jd_browser.png
    3. 从渲染后的页面里提取:商品编号、标题、价格

运行方式(在项目目录下):
    .venv\\Scripts\\python.exe step5_jd_browser.py
"""

from scrapling.fetchers import StealthyFetcher

URL = "https://search.jd.com/Search?keyword=python"

# 商品卡片选择器:新版京东每个商品是 <div class="...plugin_goodsCardWrapper" data-sku="...">
CARD = "div.plugin_goodsCardWrapper"


def wait_for_goods(page):
    """
    page_action:浏览器打开网址后、返回页面前,先执行这个函数。
    参数 page 是 Playwright 的页面对象,可以像人一样等待、截图。
    """
    try:
        # 最多等 15 秒,等商品卡片被 JS 填充出来
        page.wait_for_selector(CARD, timeout=15000)
    except Exception:
        # 没等到:可能被拦了,也可能只是慢。不报错,先把现场拍下来
        pass
    # 截图存证:不管成功失败,浏览器"亲眼所见"都留下来
    page.screenshot(path="jd_browser.png")


page = StealthyFetcher.fetch(
    URL,
    headless=True,             # 不弹窗口;调试时可以改成 False 亲眼看浏览器操作
    page_action=wait_for_goods,
    timeout=60000,
    # 注意:这里故意不用 network_idle=True
    # 京东页面会不断向后台发心跳/统计请求,"网络安静"可能永远等不到
)

items = page.css(CARD)
print("状态码:", page.status)
print("商品卡片数:", len(items))

# 打印前 5 个商品,验证数据质量
for it in items[:5]:
    sku = it.attrib.get("data-sku")                      # 商品编号(稳定属性)
    title = it.css("div[title]::attr(title)").get()      # 标题藏在 title 属性里

    # 价格被拆成了多个碎片标签:<i>¥</i><span>59</span><span>.</span><span>33</span>
    # 取价格容器里所有文本碎片,过滤掉 ¥ 和空白,再拼成 "59.33"
    # [class*=_price_] 是"属性包含匹配":class 里只要含 _price_ 就命中,
    # 这样哈希后缀(_9y3st_31)变了也不影响
    parts = [
        t for t in it.css("span[class*=_price_] ::text").getall()
        if t.strip() and t != "¥"
    ]
    price = "".join(parts)

    print(f"[{sku}] ¥{price} | {title}")

# 检查渲染后的页面有没有弹验证(如果弹了,截图里也能看到)
html = page.body
if isinstance(html, bytes):
    html = html.decode("utf-8", errors="ignore")
for word in ["滑块", "安全验证", "拖动下方滑块"]:
    if word in html:
        print("!! 检测到验证特征:", word)

print("\n浏览器画面已存到 jd_browser.png")
