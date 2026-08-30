# -*- coding: utf-8 -*-
"""抓取 RSSHub 热榜源，生成站点风格的静态热榜页 hot.html。

用法：python3 scripts/build_hot.py
由 .github/workflows/hot-board.yml 每小时调用：workflow 负责启动 RSSHub
容器并调用本脚本。页面复用站点根目录的 style.css。单个源失败只在卡片
上标记"暂时获取失败"，不影响其他源；全部失败才以非零码退出。
"""
import datetime
import html
import sys
import urllib.request

import feedparser

RSSHUB = "http://127.0.0.1:1200"
LIMIT = 20    # 每个榜最多展示条数
TIMEOUT = 30  # 单源抓取超时（秒）

# 想增删热榜改这里；路由参考 https://docs.rsshub.app
FEEDS = [
    ("微博热搜", "/weibo/search/hot"),
    ("百度热搜", "/baidu/top"),
    ("知乎热榜", "/zhihu/hot"),
    ("B站热搜", "/bilibili/hot-search"),
    ("B站排行榜", "/bilibili/ranking"),
    ("豆瓣·正在热映", "/douban/movie/playing"),
]

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>热榜速览 · Cenry</title>
<meta name="description" content="全网热榜聚合，每小时自动更新" />
<link rel="stylesheet" href="style.css" />
<style>
  .board-shell { max-width: 1200px; }
  .board-meta { text-align: center; color: var(--muted); font-size: 0.95rem; margin: -18px 0 30px; }
  .board-meta a { color: var(--accent1); text-decoration: none; }
  .board-meta a:hover { text-decoration: underline; }
  .board-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
    gap: 18px;
  }
  .board-card { padding: 22px 24px; }
  .board-card h2 {
    font-size: 1.05rem; margin: 0 0 12px; padding-left: 10px;
    border-left: 3px solid var(--accent1);
  }
  .board-card:nth-child(3n+2) h2 { border-left-color: var(--accent2); }
  .board-card:nth-child(3n) h2 { border-left-color: var(--accent3); }
  .board-card ol { margin: 0; padding-left: 20px; }
  .board-card li { margin: 7px 0; font-size: 0.9rem; line-height: 1.55; }
  .board-card a { color: var(--text); text-decoration: none; }
  .board-card a:hover { color: var(--accent1); }
  .fail { color: #d29922; font-size: 0.9rem; margin: 0; }
  .board-footer { text-align: center; color: var(--muted); font-size: 0.85rem; margin-top: 50px; }
</style>
</head>
<body>
  <div class="scroll-progress" id="scrollProgress"></div>

  <div class="aurora" aria-hidden="true">
    <span class="blob blob-1"></span>
    <span class="blob blob-2"></span>
    <span class="blob blob-3"></span>
  </div>

  <nav class="nav">
    <a href="/" class="nav-logo">Cenry</a>
    <ul class="nav-links">
      <li><a href="digest.html">简报</a></li>
      <li><a href="hot.html">热榜</a></li>
      <li><a href="/">首页</a></li>
    </ul>
  </nav>

  <section class="section board-shell">
    <h2 class="section-title">🔥 热榜速览</h2>
    <p class="board-meta">更新于 __TIME__（北京时间） · 每小时自动抓取 · <a href="digest.html">每日简报</a></p>
    <div class="board-grid">
__CARDS__
    </div>
  </section>

  <footer class="board-footer">© 2026 CenryWang · 本次成功 __OK__/__TOTAL__ 个源 · 数据经 RSSHub 抓取，GitHub Actions 自动生成</footer>

  <script>
    (function () {
      var bar = document.getElementById("scrollProgress");
      window.addEventListener("scroll", function () {
        var h = document.documentElement;
        bar.style.width = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100 + "%";
      });
      if ("IntersectionObserver" in window) {
        var io = new IntersectionObserver(function (entries) {
          entries.forEach(function (e) { if (e.isIntersecting) e.target.classList.add("visible"); });
        }, { threshold: 0.1 });
        document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
      } else {
        document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("visible"); });
      }
    })();
  </script>
</body>
</html>
"""


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def card(name, items):
    if items:
        lis = "".join(
            '<li><a href="{}" target="_blank" rel="noopener">{}</a></li>'.format(
                html.escape(link, quote=True), html.escape(title)
            )
            for title, link in items
        )
        body = "<ol>{}</ol>".format(lis)
    else:
        body = '<p class="fail">暂时获取失败，下个整点自动重试</p>'
    return '<section class="glass board-card reveal"><h2>{}</h2>{}</section>'.format(
        html.escape(name), body
    )


def main():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    cards = []
    ok = 0
    for name, path in FEEDS:
        items = None
        try:
            parsed = feedparser.parse(fetch(RSSHUB + path))
            items = [(e.get("title", ""), e.get("link", "")) for e in parsed.entries[:LIMIT]]
        except Exception as exc:
            print(f"[warn] {name}: {exc}", file=sys.stderr)
        if items:
            ok += 1
        cards.append(card(name, items))

    if ok == 0:
        print("[error] 所有源均失败，放弃生成；请查看 RSSHub 容器日志", file=sys.stderr)
        return 1

    page = (
        PAGE.replace("__TIME__", now)
        .replace("__CARDS__", "\n".join(cards))
        .replace("__OK__", str(ok))
        .replace("__TOTAL__", str(len(FEEDS)))
    )
    with open("hot.html", "w", encoding="utf-8") as f:
        f.write(page)
    print(f"hot.html written: {ok}/{len(FEEDS)} feeds ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
