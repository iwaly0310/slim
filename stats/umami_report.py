# -*- coding: utf-8 -*-
"""Umami Cloud 月報：印出上個月（或指定月份）的流量摘要 Markdown。
用法：py umami_report.py            → 上個月
      py umami_report.py 2026-10    → 指定月份
API key 放在同目錄 umami_key.txt（不進 git）。"""
import sys, os, json, datetime as dt, urllib.request, urllib.parse

WEBSITE_ID = "7cadf1bf-b05b-4c80-a86a-5e7b7192b3e0"
BASE = "https://api.umami.is/v1"
HERE = os.path.dirname(os.path.abspath(__file__))
KEY = open(os.path.join(HERE, "umami_key.txt"), encoding="utf-8").read().strip()
TZ = dt.timezone(dt.timedelta(hours=8))

def month_range(arg):
    today = dt.datetime.now(TZ)
    if arg:
        y, m = map(int, arg.split("-"))
    else:
        first = today.replace(day=1)
        prev = first - dt.timedelta(days=1)
        y, m = prev.year, prev.month
    start = dt.datetime(y, m, 1, tzinfo=TZ)
    end = dt.datetime(y + (m == 12), (m % 12) + 1, 1, tzinfo=TZ)
    return y, m, start, end

def get(path, **params):
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{BASE}{path}?{q}", headers={"x-umami-api-key": KEY, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def val(d, k):
    v = d.get(k, 0)
    return v.get("value", 0) if isinstance(v, dict) else v

def prev(d, k):
    v = d.get(k, 0)
    return v.get("prev", 0) if isinstance(v, dict) else 0

def pct(cur, before):
    if not before:
        return "（上月無資料）"
    d = (cur - before) / before * 100
    return f"（較上月 {'+' if d >= 0 else ''}{d:.0f}%）"

def main():
    y, m, start, end = month_range(sys.argv[1] if len(sys.argv) > 1 else None)
    s, e = int(start.timestamp() * 1000), int(end.timestamp() * 1000)
    stats = get(f"/websites/{WEBSITE_ID}/stats", startAt=s, endAt=e)
    urls = get(f"/websites/{WEBSITE_ID}/metrics", startAt=s, endAt=e, type="url", limit=8)
    refs = get(f"/websites/{WEBSITE_ID}/metrics", startAt=s, endAt=e, type="referrer", limit=6)
    devs = get(f"/websites/{WEBSITE_ID}/metrics", startAt=s, endAt=e, type="device", limit=5)
    pv, vis, visits = val(stats, "pageviews"), val(stats, "visitors"), val(stats, "visits")
    tt = val(stats, "totaltime")
    avg = (tt / visits) if visits else 0
    out = []
    out.append(f"# 宏謙健康減重指南 流量月報 {y} 年 {m} 月")
    out.append("")
    out.append(f"- 瀏覽數：{pv} {pct(pv, prev(stats, 'pageviews'))}")
    out.append(f"- 不重複訪客：{vis} {pct(vis, prev(stats, 'visitors'))}")
    out.append(f"- 造訪次數：{visits}，平均停留 {avg/60:.1f} 分鐘")
    out.append("")
    out.append("## 最多人看的頁面")
    names = {"/": "首頁", "/faq/": "常見問題", "/start/": "開始前", "/during/": "療程中", "/maintain/": "維持期", "/articles/": "全部文章"}
    for r in urls:
        out.append(f"- {names.get(r['x'], r['x'])}：{r['y']}")
    out.append("")
    out.append("## 訪客從哪裡來")
    for r in refs:
        out.append(f"- {r['x'] or '直接輸入／LINE 等 App 內'}：{r['y']}")
    out.append("")
    out.append("## 裝置")
    for r in devs:
        out.append(f"- {r['x']}：{r['y']}")
    text = "\n".join(out)
    os.makedirs(os.path.join(HERE, "reports"), exist_ok=True)
    with open(os.path.join(HERE, "reports", f"{y}-{m:02d}.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)

if __name__ == "__main__":
    main()
