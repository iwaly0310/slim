"""用 Google PageSpeed Insights（Lighthouse）幫官網與衛教站打分數。
用法：python psi_audit.py            -> 手機版，印出 Markdown 並存 stats/reports/psi-YYYY-MM-DD.md
      python psi_audit.py desktop    -> 電腦版
"""
import json, sys, datetime, pathlib, urllib.request, urllib.parse

sys.stdout.reconfigure(encoding="utf-8")
STRATEGY = sys.argv[1] if len(sys.argv) > 1 else "mobile"
SITES = [
    ("官網首頁", "https://hongchienclinic.com.tw/"),
    ("官網脂肪肝頁", "https://hongchienclinic.com.tw/fattyliver/"),
    ("衛教站首頁", "https://slim.hongchienclinic.com.tw/"),
    ("衛教站文章", "https://slim.hongchienclinic.com.tw/articles/protein-portions/"),
]
CATS = ["performance", "accessibility", "best-practices", "seo"]
NAMES = {"performance": "效能", "accessibility": "無障礙", "best-practices": "最佳做法", "seo": "SEO"}
METRICS = [("first-contentful-paint", "首次內容繪製"), ("largest-contentful-paint", "最大內容繪製"),
           ("total-blocking-time", "總阻塞時間"), ("cumulative-layout-shift", "版面位移")]


def run(url):
    import time, urllib.error
    q = urllib.parse.urlencode([("url", url), ("strategy", STRATEGY)] + [("category", c) for c in CATS])
    req = urllib.request.Request("https://www.googleapis.com/pagespeedonline/v5/runPagespeed?" + q,
                                 headers={"User-Agent": "Mozilla/5.0"})
    for wait in (0, 30, 60, 90):
        if wait:
            time.sleep(wait)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.load(r)
            time.sleep(8)  # 免費額度：頁面之間留點間隔
            return data
        except urllib.error.HTTPError as ex:
            if ex.code != 429:
                raise
    raise RuntimeError("PageSpeed API 額度暫時用完（429），請稍後再試")


def main():
    today = datetime.date.today().isoformat()
    lines = [f"# 網站 Lighthouse 評分（{'手機版' if STRATEGY == 'mobile' else '電腦版'}）{today}", ""]
    lines.append("| 頁面 | 效能 | 無障礙 | 最佳做法 | SEO |")
    lines.append("|---|---|---|---|---|")
    details = []
    for name, url in SITES:
        try:
            d = run(url)
        except Exception as ex:
            lines.append(f"| {name} | 失敗：{ex} | | | |")
            continue
        lr = d["lighthouseResult"]
        scores = {c: round(lr["categories"][c]["score"] * 100) for c in CATS}
        lines.append(f"| {name} | {scores['performance']} | {scores['accessibility']} | {scores['best-practices']} | {scores['seo']} |")
        aud = lr["audits"]
        m = "、".join(f"{label} {aud[k]['displayValue']}" for k, label in METRICS if k in aud and aud[k].get("displayValue"))
        fails = []
        for c in CATS:
            for ref in lr["categories"][c]["auditRefs"]:
                a = aud.get(ref["id"], {})
                sc = a.get("score")
                if sc is not None and sc < 0.9 and a.get("scoreDisplayMode") in ("binary", "numeric", "metricSavings"):
                    fails.append((NAMES[c], a.get("title", ref["id"]), a.get("displayValue", "")))
        details.append((name, m, fails[:12]))
    lines.append("")
    for name, m, fails in details:
        lines.append(f"## {name}")
        lines.append(f"- 指標：{m}")
        if fails:
            lines.append("- 需改善：")
            for c, t, v in fails:
                lines.append(f"  - [{c}] {t}{'：' + v if v else ''}")
        else:
            lines.append("- 沒有未達標的項目")
        lines.append("")
    out = "\n".join(lines)
    print(out)
    rep = pathlib.Path(__file__).parent / "reports"
    rep.mkdir(exist_ok=True)
    (rep / f"psi-{STRATEGY}-{today}.md").write_text(out, encoding="utf-8")


if __name__ == "__main__":
    main()
