#!/usr/bin/env python3
"""从 nav.py 的站点树生成「导航页」sitemap.html（纯标准库，零依赖）。

用法：python scripts/build_sitemap.py

页面展示本站的完整分支结构：4 个主板块 → 板块内目录 → 工具页 7 个分类。
结构完全来自 nav.py 这一处配置，改导航后重跑本脚本即可，导航页不会与
实际站点脱节；博客文章从 blog/posts/*.md 的 frontmatter 动态读取。
"""
import glob
import html
import os
import re

from nav import SITE_TREE, render as render_nav, url_for

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "blog", "posts")
OUT = os.path.join(ROOT, "sitemap.html")

FAVICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%2322d3ee'/%3E%3Cstop offset='1' stop-color='%23a855f7'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='64' height='64' rx='14' fill='%2306060d'/%3E%3Ctext x='32' y='46' font-family='Segoe UI,Arial,sans-serif' font-size='40' font-weight='700' fill='url(%23g)' text-anchor='middle'%3EC%3C/text%3E%3C/svg%3E"

HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>站点导航 · Cenry</title>
  <meta name="description" content="CenryWang 个人主页的完整分支结构：首页、信息、博客、奇思四大板块与全部子页面" />
  <link rel="icon" href="{favicon}" />
  <link rel="stylesheet" href="style.css" />
  <script>
    (function () {{
      try {{ var t = localStorage.getItem("theme"); if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t); }} catch (e) {{}}
    }})();
  </script>
</head>
<body>
  <div class="scroll-progress" id="scrollProgress"></div>
  <div class="aurora" aria-hidden="true">
    <span class="blob blob-1"></span><span class="blob blob-2"></span><span class="blob blob-3"></span>
  </div>
  <canvas id="particles" aria-hidden="true"></canvas>

{nav}
"""

FOOT = """
  <footer class="footer">
    <div>© <span id="year">2026</span> CenryWang · <a href="index.html" style="color:var(--muted)">返回首页</a></div>
  </footer>
  <script src="script.js"></script>
</body>
</html>
"""


def read_posts():
    """返回 [(title, 'blog/<slug>.html')]，按日期倒序。"""
    posts = []
    for path in sorted(glob.glob(os.path.join(POSTS_DIR, "*.md"))):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        meta = {}
        m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
        if m:
            for line in m.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
        slug = meta.get("slug") or os.path.splitext(os.path.basename(path))[0]
        posts.append((meta.get("date", ""), meta.get("title", slug), "blog/{}.html".format(slug)))
    posts.sort(key=lambda p: p[0], reverse=True)
    return [(p[1], p[2]) for p in posts]


def branch_items(board, posts):
    items = list(board["items"])
    if board["key"] == "blog":
        items += posts
    return items


def render_branch(board, index, posts):
    rows = []
    for entry in branch_items(board, posts):
        label, href = entry[0], entry[1]
        children = entry[2] if len(entry) > 2 else []
        sub = ""
        if children:
            # 子项是 tools.html 本页锚点，导航页需要补上页面前缀才能跳转
            sub_hrefs = [
                (c[0], href + c[1] if c[1].startswith("#") else c[1]) for c in children
            ]
            sub = '<ul class="sitemap-sub">' + "".join(
                '<li><a href="{}">{}</a></li>'.format(
                    html.escape(url_for(u), quote=True), html.escape(t)
                )
                for t, u in sub_hrefs
            ) + "</ul>"
        rows.append(
            '<li{}><a href="{}">{}</a>{}</li>'.format(
                ' class="has-sub"' if sub else "",
                html.escape(url_for(href), quote=True), html.escape(label), sub
            )
        )
    return """      <li class="sitemap-branch glass">
        <div class="sitemap-branch-head">
          <span class="sitemap-index">{idx:02d}</span>
          <div>
            <h2><a href="{href}">{label}</a></h2>
            <p>{desc}</p>
          </div>
        </div>
        <ul class="sitemap-leaves">{rows}</ul>
      </li>""".format(
        idx=index,
        href=html.escape(url_for(board["href"]), quote=True),
        label=html.escape(board["label"]),
        desc=html.escape(board["desc"]),
        rows="".join(rows),
    )


def main():
    posts = read_posts()
    nav = render_nav()
    branches = "".join(
        render_branch(b, i + 1, posts) for i, b in enumerate(SITE_TREE)
    )
    body = """
  <header class="hero hero--compact">
    <div class="hero-inner">
      <p class="hero-greeting reveal">Site Map</p>
      <h1 class="hero-name hero-name--compact reveal">站点导航</h1>
      <p class="hero-typed"><span>一张图看懂本站的分支结构</span></p>
    </div>
  </header>

  <section class="section sitemap-section">
    <div class="sitemap-root">
      <div class="sitemap-root-node glass">
        <span class="sitemap-root-dot"></span>
        <strong>CenryWang · 个人主页</strong>
        <span class="sitemap-root-meta">4 个主板块 · {count} 个分支节点</span>
      </div>
      <ol class="sitemap-branches">
{branches}
      </ol>
    </div>
    <p class="sitemap-note">顶部导航只保留 4 个主板块；进入任一板块后，左侧目录会展开该板块下的全部去处。</p>
  </section>
""".format(count=sum(len(branch_items(b, posts)) for b in SITE_TREE), branches=branches)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(HEAD.format(favicon=FAVICON, nav=nav) + body + FOOT)
    print("built {} -> {}".format(len(SITE_TREE), OUT))


if __name__ == "__main__":
    main()
