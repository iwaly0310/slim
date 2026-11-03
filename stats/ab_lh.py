"""改版前後 A/B：本機同時架起舊版與新版 docs，各跑 N 次 Lighthouse（手機版）取中位數。
用法：python ab_lh.py [runs]   （預設 3）
舊版來源：stats/reports/ab/old-official/docs、stats/reports/ab/old-slim/docs（用 git archive 先放好）
"""
import json, os, sys, time, pathlib, subprocess, shutil, statistics, urllib.request

sys.stdout.reconfigure(encoding="utf-8")
RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
HERE = pathlib.Path(__file__).parent
AB = HERE / "reports" / "ab"
SET = sys.argv[2] if len(sys.argv) > 2 else "home"
OFF_OLD, OFF_NEW = AB / "old-official" / "docs", pathlib.Path("C:/MYproject/宏謙官網/official/docs")
SLIM_OLD, SLIM_NEW = AB / "old-slim" / "docs", pathlib.Path("C:/MYproject/宏謙官網/slim/docs")
TARGETS = {  # name, directory, port, path
    "home": [("官網首頁 舊", OFF_OLD, 5181, "/"), ("官網首頁 新", OFF_NEW, 5182, "/"),
             ("衛教站首頁 舊", SLIM_OLD, 5183, "/"), ("衛教站首頁 新", SLIM_NEW, 5184, "/")],
    "official": [("官網首頁 舊", OFF_OLD, 5181, "/"), ("官網首頁 新", OFF_NEW, 5182, "/"),
                 ("脂肪肝頁 舊", OFF_OLD, 5181, "/fattyliver/"), ("脂肪肝頁 新", OFF_NEW, 5182, "/fattyliver/")],
}[SET]
CATS = "performance,accessibility,best-practices,seo"
EDGE = next((p for p in [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                         r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"] if os.path.exists(p)), None)
NPX = shutil.which("npx.cmd") or shutil.which("npx")


def lighthouse(url, out):
    env = dict(os.environ)
    if EDGE:
        env["CHROME_PATH"] = EDGE
    cmd = [NPX, "-y", "lighthouse", url, "--output=json", f"--output-path={out}", "--quiet",
           "--only-categories=" + CATS, "--chrome-flags=--headless=new --no-sandbox",
           "--form-factor=mobile", "--screenEmulation.mobile", "--throttling-method=simulate"]
    subprocess.run(cmd, env=env, check=True, timeout=400, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    d = json.load(open(out, encoding="utf-8"))
    a = d["audits"]
    g = lambda k: a[k].get("numericValue", float("nan"))
    return {"perf": round(d["categories"]["performance"]["score"] * 100), "fcp": g("first-contentful-paint") / 1000,
            "lcp": g("largest-contentful-paint") / 1000, "si": g("speed-index") / 1000, "tbt": g("total-blocking-time"),
            "cls": g("cumulative-layout-shift"), "bench": d.get("environment", {}).get("benchmarkIndex", 0)}


def main():
    servers = []
    for name, d, port, _ in TARGETS:
        servers.append(subprocess.Popen([sys.executable, "-m", "http.server", str(port), "-d", str(d), "--bind", "127.0.0.1"],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    time.sleep(2)
    try:
        for _, _, port, p in TARGETS:
            urllib.request.urlopen(f"http://127.0.0.1:{port}{p}", timeout=10).read(200)
        res = {n: [] for n, *_ in TARGETS}
        tmp = AB / "json"; tmp.mkdir(exist_ok=True)
        for r in range(RUNS):
            for name, _, port, p in TARGETS:  # 交錯跑，讓機器負載平均分攤到新舊版
                m = lighthouse(f"http://127.0.0.1:{port}{p}", tmp / f"{port}-{r}.json")
                res[name].append(m)
                print(f"  run{r+1} {name}: perf {m['perf']} LCP {m['lcp']:.1f}s SI {m['si']:.1f}s TBT {m['tbt']:.0f}ms bench {m['bench']:.0f}", flush=True)
        print("\n| 頁面 | 效能(中位) | FCP | LCP | 速度指數 | TBT | CLS |")
        print("|---|---|---|---|---|---|---|")
        for name, *_ in TARGETS:
            L = res[name]
            med = lambda k: statistics.median(x[k] for x in L)
            print(f"| {name} | {med('perf'):.0f}（{min(x['perf'] for x in L)}–{max(x['perf'] for x in L)}） | {med('fcp'):.1f}s | {med('lcp'):.1f}s | {med('si'):.1f}s | {med('tbt'):.0f}ms | {med('cls'):.3f} |")
    finally:
        for s in servers:
            s.terminate()


if __name__ == "__main__":
    main()
