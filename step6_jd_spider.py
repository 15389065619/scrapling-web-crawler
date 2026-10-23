"""
新项目:京东商品爬虫 —— 阶段 3:工程化批量抓取

前两阶段是"单页抓取":发一次请求、解析一次。
本阶段把它们组装成真正能交付的爬虫:
    1. 用 Spider 引擎并发翻页(每页约 30 条,默认抓 3 页)
    2. 每页用浏览器渲染(京东是 JS 动态页,复用阶段 2 的能力)
    3. 注入登录 Cookie 绕过京东的登录墙(真实站点必经之路)
    4. 按 sku 去重(翻页会有重复商品)
    5. 限速、并发控制,避免被封
    6. 结果导出 jd_goods.json / jd_goods.csv

关于京东登录墙:
    京东搜索现在要求登录才能看结果,会把未登录请求 302 到登录页。
    标准解法:把你浏览器里的登录 Cookie 拿出来,放进请求头。
    Cookie 获取方法(在 Chrome 里):
      1. 打开 https://search.jd.com 并登录你的京东账号
      2. 按 F12 打开开发者工具 → Network 标签
      3. 刷新页面,点任意一个 search.jd.com 的请求
      4. 在 Headers 里找到 Request Headers → Cookie,复制整行值
      5. 粘贴到本目录下的 jd_cookie.txt(只放 Cookie 那一行,不要 "Cookie: ")
    注意:Cookie 会过期,失效了重新复制即可。

运行方式(在项目目录下):
    .venv\\Scripts\\python.exe step6_jd_spider.py
"""

from pathlib import Path

from scrapling.spiders import Spider, Response, Request
from scrapling.fetchers import AsyncStealthySession

# 商品卡片选择器(阶段 2 反复验证过的稳定锚点)
CARD = "div.plugin_goodsCardWrapper"
KEYWORD = "python"       # 搜索关键词
MAX_PAGES = 3            # 抓几页。每页约 30 条;先小批量验证,调大前请确保频率合规
COOKIE_FILE = Path(__file__).parent / "jd_cookies.txt"


def load_cookie() -> str:
    """从 jd_cookies.txt 读取登录 Cookie;没有就返回空串"""
    if not COOKIE_FILE.exists():
        return ""
    return COOKIE_FILE.read_text(encoding="utf-8").strip()


def parse_cookies(cookie_str: str) -> list[dict]:
    """
    把 "name1=val1; name2=val2" 格式的 Cookie 字符串,
    转成 Playwright 需要的 [{name, value, domain, path}] 列表。
    这是浏览器会话注入 Cookie 的正确方式(直接塞 Cookie 头在浏览器里会失效)。
    """
    cookies = []
    for pair in cookie_str.split(";"):
        pair = pair.strip()
        if not pair or "=" not in pair:
            continue
        name, value = pair.split("=", 1)
        cookies.append({
            "name": name.strip(),
            "value": value.strip(),
            "domain": ".jd.com",   # 京东主域,覆盖 search.jd.com / passport.jd.com 等子域
            "path": "/",
        })
    return cookies


async def wait_for_goods(page):
    """
    浏览器打开搜索页后先执行这里:等商品卡片被 JS 渲染出来。
    注意:AsyncStealthySession 里的 page 是异步对象,所有操作都要 await。
    """
    try:
        await page.wait_for_selector(CARD, timeout=20000)
    except Exception:
        # 没等到也不崩溃,交给 parse 判断抓到 0 条
        pass


class JDSpider(Spider):
    name = "jd_goods"

    # 浏览器页很吃资源,并发只开 2;每次请求间隔 2 秒(礼貌爬取)
    concurrent_requests = 2
    download_delay = 2.0

    def configure_sessions(self, manager):
        """
        重写这个方法,把 Spider 默认的"纯 HTTP 会话"换成"浏览器会话"。
        这是让 Spider 能抓 JS 动态页的关键一步。
        同时把登录 Cookie 注入浏览器上下文,绕过登录墙。
        """
        cookie = load_cookie()
        cookies = parse_cookies(cookie) if cookie else []

        manager.add(
            "jd_browser",
            AsyncStealthySession(
                headless=True,        # 无头模式;调试时改 False 能看到浏览器在跑
                page_action=wait_for_goods,
                wait_selector=CARD,   # 等商品卡片出现再返回
                timeout=60000,
                cookies=cookies,      # 正确方式:把 Cookie 注入浏览器上下文
            ),
            default=True,           # 设为默认会话,所有请求都用它
        )

    async def on_start(self, resuming: bool = False):
        """爬虫启动时执行:初始化去重集合,并检查 Cookie"""
        self.seen_skus = set()
        if not load_cookie():
            print("!! 未找到 jd_cookie.txt,京东会把请求重定向到登录页。")
            print("   请按文件开头的说明把登录 Cookie 存到 jd_cookie.txt")

    async def start_requests(self):
        """
        入口:生成所有要抓的页面请求。
        京东 page 参数取奇数:1=第1页,3=第2页,5=第3页...
        没有 Cookie 时不发请求,直接结束(京东会重定向到登录页,抓了也白抓)。
        """
        if not load_cookie():
            return
        for i in range(MAX_PAGES):
            page_no = i * 2 + 1  # 1, 3, 5...
            url = f"https://search.jd.com/Search?keyword={KEYWORD}&page={page_no}"
            # meta 是请求的"便签",把页码带过去
            yield Request(url, meta={"page": i + 1})

    async def parse(self, response: Response):
        """
        每个页面渲染完后调用一次。
        yield 字典 = 产出一条数据;这里不再 yield Request(因为页面列表已在 start_requests 里给全了)。
        """
        page_label = response.meta.get("page", "?")

        # 如果被重定向到了登录页,说明 Cookie 失效了
        if "passport.jd.com" in response.url:
            print(f"第 {page_label} 页被重定向到登录页,Cookie 可能已失效")
            return

        items = response.css(CARD)
        print(f"第 {page_label} 页抓到 {len(items)} 个商品")

        new_count = 0
        for it in items:
            # data-sku 是京东商品的唯一编号,用它去重
            sku = it.attrib.get("data-sku")
            if not sku or sku in self.seen_skus:
                continue
            self.seen_skus.add(sku)
            new_count += 1

            # 标题在 title 属性里(阶段 2 踩坑结论)
            title = it.css("div[title]::attr(title)").get()

            # 价格被拆成多个碎片:¥ 整数 . 小数,过滤掉 ¥ 再拼起来
            parts = [
                t for t in it.css("span[class*=_price_] ::text").getall()
                if t.strip() and t != "¥"
            ]
            price = "".join(parts)

            yield {
                "sku": sku,
                "title": title,
                "price": price,
                "page": page_label,
            }

        print(f"  去重后新增 {new_count} 个")


# ============ 运行并导出 ============
result = JDSpider().start()

print("\n===== 抓取统计 =====")
print("去重后商品数:", result.stats.items_scraped)
print("请求总数:", result.stats.requests_count)
print("失败请求数:", result.stats.failed_requests_count)
print("耗时(秒):", round(result.stats.elapsed_seconds, 2))

result.items.to_json("jd_goods.json", indent=True)
result.items.to_csv("jd_goods.csv", fields=["sku", "title", "price", "page"])
print("\n已导出 jd_goods.json / jd_goods.csv")
if result.items:
    print("第一条:", result.items[0])
else:
    print("没有抓到数据,请检查 Cookie 是否有效")
