"""本機 Lighthouse（用 Edge 無頭模式）幫官網與衛教站打分數，標準與 Google PageSpeed 相同。
用法：python lh_audit.py            -> 手機版，印出 Markdown 並存 stats/reports/lh-mobile-YYYY-MM-DD.md
      python lh_audit.py desktop    -> 電腦版
需要 Node.js（會用 npx 自動下載 lighthouse）與 Microsoft Edge。
"""
import json, os, sys, datetime, pathlib, subprocess, shutil

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
           ("total-blocking-time", "總阻塞時間"), ("cumulative-layout-shift", "版面位移"), ("speed-index", "速度指數")]
REPORTS = pathlib.Path(__file__).parent / "reports"
TMP = REPORTS / "lh-json"


def edge_path():
    for p in [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]:
        if os.path.exists(p):
            return p
    return None


def run(url, out):
    env = dict(os.environ)
    e = edge_path()
    if e:
        env["CHROME_PATH"] = e
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    cmd = [npx, "-y", "lighthouse", url, "--output=json", f"--output-path={out}", "--quiet",
           "--only-categories=" + ",".join(CATS), "--chrome-flags=--headless=new --no-sandbox"]
    if STRATEGY == "mobile":
        cmd += ["--form-factor=mobile", "--screenEmulation.mobile", "--throttling-method=simulate"]
    else:
        cmd += ["--preset=desktop"]
    subprocess.run(cmd, env=env, check=True, timeout=400, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return json.load(open(out, encoding="utf-8"))


def main():
    today = datetime.date.today().isoformat()
    REPORTS.mkdir(exist_ok=True); TMP.mkdir(exist_ok=True)
    lines = [f"# 網站 Lighthouse 評分（{'手機版' if STRATEGY == 'mobile' else '電腦版'}）{today}", "",
             "| 頁面 | 效能 | 無障礙 | 最佳做法 | SEO |", "|---|---|---|---|---|"]
    details = []
    for i, (name, url) in enumerate(SITES):
        try:
            lr = run(url, TMP / f"{STRATEGY}-{i}.json")
        except Exception as ex:
            lines.append(f"| {name} | 失敗：{ex} | | | |")
            continue
        scores = {c: round((lr["categories"][c]["score"] or 0) * 100) for c in CATS}
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
    (REPORTS / f"lh-{STRATEGY}-{today}.md").write_text(out, encoding="utf-8")


if __name__ == "__main__":
    main()
