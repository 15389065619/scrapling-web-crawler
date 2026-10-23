"""
第 3 阶段：用 Spider 做工程化批量抓取

前两个阶段是"单页抓取"：一次请求、一次解析。
真实项目要的是：自动翻页、并发请求、失败重试、限速、结果落盘。
Spider 就是把这一整套流程封装好的"爬虫骨架"。

本脚本抓取 quotes.toscrape.com 全部 10 页、共 100 条名言，
并导出 quotes.json 和 quotes.csv。

运行方式（在项目目录下，产物也会写在项目目录）：
    .venv\\Scripts\\python.exe step3_spider.py
"""

from scrapling.spiders import Spider, Response, Request


class QuotesSpider(Spider):
    # name 是爬虫的唯一标识，用于日志和暂停/恢复
    name = "quotes"

    # 入口地址：爬虫从这里开始
    start_urls = ["https://quotes.toscrape.com/"]

    # 并发数：同时最多有 4 个请求在跑
    # 注意：并发不是越大越好，太大容易被封，也会给目标站造成压力
    concurrent_requests = 4

    # 每次请求之间至少间隔 0.5 秒（礼貌爬取，降低被封风险）
    download_delay = 0.5

    async def parse(self, response: Response):
        """
        parse 是回调函数：每拿到一个页面，就执行一次。
        它是一个"异步生成器"：yield 字典 = 产出一条数据；yield Request = 排队一个新请求。
        """
        # meta 是随请求携带的"便签"，用来记录当前是第几页
        page_no = response.meta.get("page", 1)

        # 解析当前页的每一条名言，产出一条结构化数据
        for q in response.css(".quote"):
            yield {
                "page": page_no,                                  # 第几页
                "author": q.css(".author::text").get(),           # 作者
                "text": q.css(".text::text").get(),               # 名言正文
                "tags": q.css(".tag::text").getall(),             # 标签列表
            }

        # 找"下一页"的链接；最后一页没有这个元素，get() 会返回 None
        next_link = response.css("li.next a::attr(href)").get()
        if next_link:
            # urljoin 把相对路径 /page/2/ 拼成完整网址
            # 把新请求排进队列，callback 指定由谁处理它（还是 self.parse）
            yield Request(
                response.urljoin(next_link),
                callback=self.parse,
                meta={"page": page_no + 1},   # 便签带到下一页
            )


# ============ 运行爬虫 ============
# start() 内部会自己起事件循环，所以外面不用写 asyncio.run
result = QuotesSpider().start()

# stats 是本次抓取的统计信息
print("\n===== 抓取统计 =====")
print("成功抓取条目:", result.stats.items_scraped)
print("发出的请求数:", result.stats.requests_count)
print("失败请求数:", result.stats.failed_requests_count)
print("耗时(秒):", round(result.stats.elapsed_seconds, 2))
print("是否完整跑完:", result.completed)

# items 是结果列表，自带导出方法
result.items.to_json("quotes.json", indent=True)
result.items.to_csv("quotes.csv", fields=["page", "author", "text", "tags"])

print("\n已导出 quotes.json / quotes.csv")
print("第一条数据预览:", result.items[0])
