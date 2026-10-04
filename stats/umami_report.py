# -*- coding: utf-8 -*-
"""Umami Cloud 流量報表：透過「分享連結」讀取流量，印出 Markdown 摘要（衛教站 + 官網）。
用法：py umami_report.py week             → 本週（週一 00:00 到現在；週日晚上跑就是整週）
      py umami_report.py week 2026-10-11  → 該日期所在的那一週（週一到週日）
      py umami_report.py                  → 上個月
      py umami_report.py 2026-10          → 指定月份
不需要 API key；只要 Umami 後台的 Share 連結還存在就能用。"""
import sys, os, json, datetime as dt, urllib.request, urllib.parse
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

WEBSITE_ID = "7cadf1bf-b05b-4c80-a86a-5e7b7192b3e0"
SHARE_ID = "8VOWMkwpFYp1fzl1"
SLIM_HOST = "slim.hongchienclinic.com.tw"
OFFICIAL_HOST = "hongchienclinic.com.tw"
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

def week_range(arg):
    now = dt.datetime.now(TZ)
    day = dt.datetime.strptime(arg, "%Y-%m-%d").replace(tzinfo=TZ) if arg else now
    start = (day - dt.timedelta(days=day.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, min(start + dt.timedelta(days=7), now)

def fetch(path, headers=None, **params):
    url = f"{BASE}{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) monthly-report", **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def pct(cur, before, prev="上月"):
    if not before:
        return f"（{prev}無資料）"
    d = (cur - before) / before * 100
    return f"（較{prev} {'+' if d >= 0 else ''}{d:.0f}%）"

NAMES = {"/": "首頁", "/faq/": "常見問題", "/start/": "開始前", "/during/": "療程中", "/maintain/": "維持期", "/articles/": "全部文章", "/fattyliver/": "脂肪肝篩檢活動"}

def site_block(title, host, H, s, e, prev):
    W = f"/websites/{WEBSITE_ID}"
    stats = fetch(f"{W}/stats", H, startAt=s, endAt=e, hostname=host)
    paths = fetch(f"{W}/metrics", H, startAt=s, endAt=e, type="path", limit=8, hostname=host)
    refs = fetch(f"{W}/metrics", H, startAt=s, endAt=e, type="referrer", limit=6, hostname=host)
    devs = fetch(f"{W}/metrics", H, startAt=s, endAt=e, type="device", limit=5, hostname=host)
    cmp_ = stats.get("comparison", {})
    pv, vis, visits, tt = (stats.get(k, 0) for k in ("pageviews", "visitors", "visits", "totaltime"))
    avg = (tt / visits) if visits else 0
    out = [f"## {title}", "",
           f"- 瀏覽數：{pv} {pct(pv, cmp_.get('pageviews', 0), prev)}",
           f"- 不重複訪客：{vis} {pct(vis, cmp_.get('visitors', 0), prev)}",
           f"- 造訪次數：{visits}，平均每次停留 {avg/60:.1f} 分鐘", "",
           "### 最多人看的頁面"]
    out += [f"- {NAMES.get(r['x'], r['x'])}：{r['y']}" for r in paths] or ["- （無資料）"]
    out += ["", "### 訪客從哪裡來（有記錄到來源的）"]
    out += [f"- {r['x'] or '直接輸入／LINE 等 App 內'}：{r['y']}" for r in refs] or ["- （無資料）"]
    out += ["", "### 裝置"]
    out += [f"- {r['x']}：{r['y']}" for r in devs] or ["- （無資料）"]
    return out

def ad_clicks(H, s, e):
    """官網網址帶 OpenAI 廣告參數（oppref= 為廣告點擊自動附加；utm_source=openai 為手動設定）的瀏覽數。"""
    rows = fetch(f"/websites/{WEBSITE_ID}/metrics", H, startAt=s, endAt=e, type="query", limit=500, hostname=OFFICIAL_HOST)
    return sum(r["y"] for r in rows if "oppref=" in r["x"] or "utm_source=openai" in r["x"])

def main():
    args = sys.argv[1:]
    if args and args[0] == "week":
        start, end = week_range(args[1] if len(args) > 1 else None)
        last = start + dt.timedelta(days=6)
        head = f"# 宏謙網站流量週報 {start:%Y/%m/%d}–{last:%m/%d}"
        prev, name = "上週", f"week-{start:%Y-%m-%d}"
    else:
        y, m, start, end = month_range(args[0] if args else None)
        head = f"# 宏謙網站流量月報 {y} 年 {m} 月"
        prev, name = "上月", f"{y}-{m:02d}"
    s, e = int(start.timestamp() * 1000), int(end.timestamp() * 1000)
    token = fetch(f"/share/{SHARE_ID}")["token"]
    H = {"x-umami-share-token": token, "x-umami-share-context": "1"}
    # 官網與衛教站共用同一個 Umami 網站 ID，用 hostname 區分
    out = [head, f"（統計區間：{start:%m/%d %H:%M} – {end:%m/%d %H:%M}）", ""]
    out += site_block("官網 hongchienclinic.com.tw（2026-10-04 起統計）", OFFICIAL_HOST, H, s, e, prev)
    out += ["", "### OpenAI 廣告", f"- 帶廣告參數進站的瀏覽數：{ad_clicks(H, s, e)}", ""]
    out += site_block("衛教站 slim.hongchienclinic.com.tw", SLIM_HOST, H, s, e, prev)
    text = "\n".join(out)
    os.makedirs(os.path.join(HERE, "reports"), exist_ok=True)
    with open(os.path.join(HERE, "reports", f"{name}.md"), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)

if __name__ == "__main__":
    main()
