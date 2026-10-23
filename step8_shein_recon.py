"""
Shein 侦察 - 改用香港站 shein.com.hk(根据 IP 自动跳转的区域站)
"""
from scrapling.fetchers import StealthyFetcher

URL = "https://www.shein.com.hk/pdsearch/dress/"

page = StealthyFetcher.fetch(
    URL,
    headless=False,
    network_idle=True,
    timeout=60000,
)

print("状态码:", page.status)
print("最终 URL:", page.url)

html = page.body
if isinstance(html, bytes):
    html = html.decode("utf-8", "ignore")
print("网页长度:", len(html))

for kw in ["product", "goods", "price", "SHEIN", "System Updating", "captcha", "J_31"]:
    print(f"  '{kw}': {html.count(kw)} 次")

with open("shein_recon_hk.html", "w", encoding="utf-8") as f:
    f.write(html)
print("\n已存到 shein_recon_hk.html")
