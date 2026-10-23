"""
新项目:京东商品爬虫 —— 阶段 1:侦察

真实网站和练习网站最大的区别是:你永远不知道服务器会返回什么。
可能是真数据,也可能是拦截页。所以真实项目的第一步不是写解析代码,
而是"侦察":发一个请求,看看对面到底给了什么。

本脚本只做一件事:回答"京东给不给我们数据?"
判断依据是 3 个信号:
    信号 1:HTTP 状态码(200 = 请求被接受;403/跳转 = 可能被拦)
    信号 2:页面里有没有商品元素(京东搜索结果的商品卡片是 li.gl-item)
    信号 3:页面里有没有拦截关键词(出现"验证""风险"等字样 = 被反爬识别了)

运行方式(在项目目录下):
    .venv\\Scripts\\python.exe step4_jd_recon.py
"""

from scrapling.fetchers import Fetcher

# 京东搜索页,关键词 python(英文关键词不需要转码,先保持简单)
URL = "https://search.jd.com/Search?keyword=python"

# 发起 GET 请求,TLS 指纹伪装成 Chrome(和之前学的一样)
# timeout=30 表示最多等 30 秒,等不到就放弃,不让程序干等
page = Fetcher.get(URL, impersonate="chrome", timeout=30)

# ============ 信号 1:状态码 ============
print("HTTP 状态码:", page.status)

# page.body 是服务器返回的原始内容(可能是 str 或 bytes,统一转成 str)
html = page.body
if isinstance(html, bytes):
    html = html.decode("utf-8", errors="ignore")
print("网页总长度:", len(html), "字符")

# ============ 信号 2:有没有商品卡片 ============
# 在浏览器里按 F12 观察过京东搜索页就会知道:
# 每个商品都是一个 <li class="gl-item">,这叫"侦察先行"——选择器不是猜的,是看的
items = page.css("li.gl-item")
print("找到商品卡片数:", len(items))

# ============ 信号 3:有没有拦截特征 ============
# 被反爬拦截时,页面里通常会出现验证相关的字眼
for word in ["验证", "风险", "captcha", "robot"]:
    if word in html:
        print("!! 页面里出现可疑关键词:", word)

# 如果抓到了商品,打印第一个商品的标题和编号,确认数据是真的
if items:
    # .p-name em 是商品标题所在的标签
    first_title = items[0].css(".p-name em::text").get()
    # attrib 是这个 HTML 标签上的属性字典;data-sku 是京东给每个商品编的号
    first_sku = items[0].attrib.get("data-sku")
    print("\n第一个商品标题:", first_title)
    print("第一个商品编号(sku):", first_sku)

# 把原始网页存成文件,可以双击用浏览器打开,亲眼看看服务器到底给了什么
with open("jd_recon.html", "w", encoding="utf-8") as f:
    f.write(html)
print("\n原始网页已存到 jd_recon.html")
