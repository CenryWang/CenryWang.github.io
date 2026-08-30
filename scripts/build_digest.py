# -*- coding: utf-8 -*-
"""把 garss 生成的 README.md 渲染成站点风格的 digest.html。

用法：python3 scripts/build_digest.py <garss README.md> <输出文件>
由 .github/workflows/sync-digest.yml 每日调用。页面直接复用站点根目录的
style.css（极光背景 / 玻璃卡片 / 导航），纯静态输出，不依赖 Jekyll。
"""
import datetime
import sys

import markdown

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>每日简报 · Cenry</title>
<meta name="description" content="RSS 聚合每日简报，GitHub Actions 自动更新" />
<link rel="stylesheet" href="style.css" />
<style>
  .digest-shell { max-width: 1080px; }
  .digest-meta { text-align: center; color: var(--muted); font-size: 0.95rem; margin: -18px 0 30px; }
  .digest-meta a { color: var(--accent1); text-decoration: none; }
  .digest-meta a:hover { text-decoration: underline; }
  .digest-body h2 { margin: 44px 0 16px; font-size: 1.35rem; }
  .digest-body h2::after {
    content: ""; display: block; width: 44px; height: 3px; margin-top: 8px;
    background: linear-gradient(90deg, var(--accent1), var(--accent2)); border-radius: 2px;
  }
  .digest-body p { color: var(--muted); font-size: 0.95rem; }
  .table-wrap { overflow-x: auto; border: 1px solid var(--glass-border); border-radius: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.9rem; min-width: 660px; }
  th {
    text-align: left; color: var(--muted); font-size: 0.78rem; letter-spacing: 1px;
    padding: 12px 14px; border-bottom: 1px solid var(--glass-border); white-space: nowrap;
  }
  td { padding: 10px 14px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255, 255, 255, 0.02); }
  td a, td a:visited { color: var(--accent1); text-decoration: none; }
  td a:hover { text-decoration: underline; }
  td img { width: 22px; height: 22px; border-radius: 5px; vertical-align: middle; }
  .digest-footer { text-align: center; color: var(--muted); font-size: 0.85rem; margin-top: 50px; }
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

  <section class="section digest-shell">
    <h2 class="section-title">每日简报</h2>
    <p class="digest-meta">同步于 __TIME__（北京时间） · 每天 07:30 自动更新 · <a href="hot.html">🔥 热榜速览</a></p>
    <div class="glass digest-body">
__BODY__
    </div>
  </section>

  <footer class="digest-footer">© 2026 CenryWang · 内容来自 RSS 订阅源，GitHub Actions 自动生成</footer>

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
        }, { threshold: 0.05 });
        document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
      } else {
        document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("visible"); });
      }
    })();
  </script>
</body>
</html>
"""


def main():
    if len(sys.argv) != 3:
        print("usage: build_digest.py <garss README.md> <output.html>", file=sys.stderr)
        return 2
    src, dst = sys.argv[1], sys.argv[2]

    with open(src, encoding="utf-8") as f:
        text = f.read()

    # 去掉源文件首行 H1（页面已有自己的标题），避免重复
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    text = "\n".join(lines).strip()

    body = markdown.markdown(text, extensions=["tables"])
    # 表格外包一层滚动容器，窄屏横向滑动不撑破布局
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace(
        "</table>", "</table></div>"
    )

    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    page = PAGE.replace("__TIME__", now).replace("__BODY__", body)

    with open(dst, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"{dst} written ({len(body)} chars of content)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
