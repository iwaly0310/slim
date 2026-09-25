# -*- coding: utf-8 -*-
"""Umami Cloud 月報：透過「分享連結」讀取上個月（或指定月份）的流量，印出 Markdown 摘要。
用法：py umami_report.py            → 上個月
      py umami_report.py 2026-10    → 指定月份
不需要 API key；只要 Umami 後台的 Share 連結還存在就能用。"""
import sys, os, json, datetime as dt, urllib.request, urllib.parse
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

WEBSITE_ID = "7cadf1bf-b05b-4c80-a86a-5e7b7192b3e0"
SHARE_ID = "8VOWMkwpFYp1fzl1"
BASE = "https://cloud.umami.is/analytics/us/api"
HERE = os.path.dirname(os.path.abspath(__file__))
TZ = dt.timezone(dt.timedelta(hours=8))

def month_range(arg):
    today = dt.datetime.now(TZ)
    if arg:
        y, m = map(int, arg.split("-"))
    else:
        prev = today.replace(day=1) - dt.timedelta(days=1)
        y, m = prev.year, prev.month
    start = dt.datetime(y, m, 1, tzinfo=TZ)
    end = dt.datetime(y + (m == 12), (m % 12) + 1, 1, tzinfo=TZ)
    return y, m, start, min(end, today)

def fetch(path, headers=None, **params):
    url = f"{BASE}{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) monthly-report", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def pct(cur, before):
    if not before:
        return "（上月無資料）"
    d = (cur - before) / before * 100
    return f"（較上月 {'+' if d >= 0 else ''}{d:.0f}%）"

def main():
    y, m, start, end = month_range(sys.argv[1] if len(sys.argv) > 1 else None)
    s, e = int(start.timestamp() * 1000), int(end.timestamp() * 1000)
    token = fetch(f"/share/{SHARE_ID}")["token"]
    H = {"x-umami-share-token": token, "x-umami-share-context": "1"}
    W = f"/websites/{WEBSITE_ID}"
    stats = fetch(f"{W}/stats", H, startAt=s, endAt=e)
    paths = fetch(f"{W}/metrics", H, startAt=s, endAt=e, type="path", limit=8)
    refs = fetch(f"{W}/metrics", H, startAt=s, endAt=e, type="referrer", limit=6)
    devs = fetch(f"{W}/metrics", H, startAt=s, endAt=e, type="device", limit=5)
    cmp_ = stats.get("comparison", {})
    pv, vis, visits, tt = (stats.get(k, 0) for k in ("pageviews", "visitors", "visits", "totaltime"))
    avg = (tt / visits) if visits else 0
    names = {"/": "首頁", "/faq/": "常見問題", "/start/": "開始前", "/during/": "療程中", "/maintain/": "維持期", "/articles/": "全部文章"}
    out = [f"# 宏謙健康減重指南 流量月報 {y} 年 {m} 月", "",
           f"- 瀏覽數：{pv} {pct(pv, cmp_.get('pageviews', 0))}",
           f"- 不重複訪客：{vis} {pct(vis, cmp_.get('visitors', 0))}",
           f"- 造訪次數：{visits}，平均每次停留 {avg/60:.1f} 分鐘", "",
           "## 最多人看的頁面"]
    out += [f"- {names.get(r['x'], r['x'])}：{r['y']}" for r in paths] or ["- （無資料）"]
    out += ["", "## 訪客從哪裡來"]
    out += [f"- {r['x'] or '直接輸入／LINE 等 App 內'}：{r['y']}" for r in refs] or ["- （無資料）"]
    out += ["", "## 裝置"]
    out += [f"- {r['x']}：{r['y']}" for r in devs] or ["- （無資料）"]
    text = "\n".join(out)
    os.makedirs(os.path.join(HERE, "reports"), exist_ok=True)
    with open(os.path.join(HERE, "reports", f"{y}-{m:02d}.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)

if __name__ == "__main__":
    main()
