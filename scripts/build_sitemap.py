#!/usr/bin/env python3
"""从 nav.py 的站点树生成「导航页」sitemap.html（纯标准库，零依赖）。

用法：python scripts/build_sitemap.py

设计语言：编辑式「站点索引」——排版驱动，不依赖任何图形库。
4 个板块各成一章：超大描边编号 + 板块名 + 该板块全部去处的紧凑链接矩阵。
所有结构来自 nav.py，博客条目从 blog/posts/*.md 的 frontmatter 动态读取。
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
  <title>站点索引 · Cenry</title>
  <meta name="description" content="CenryWang 个人主页完整索引：首页、信息、博客、奇思四大板块与全部子页面" />
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

# 板块的英文副名——编辑式排版的固定组成部分
SECTOR_EN = ["HOME", "INFORMATION", "JOURNAL", "WHIMSY"]


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


def collect_leaves(board, posts):
    """展开板块的全部去处，含工具页的子分类锚点。"""
    leaves = []
    for entry in branch_items(board, posts):
        label, href = entry[0], entry[1]
        children = entry[2] if len(entry) > 2 else []
        leaves.append((label, href))
        for c in children:
            sub_href = href + c[1] if c[1].startswith("#") else c[1]
            leaves.append((c[0], sub_href))
    return leaves


def render_chapter(board, i, posts):
    """一个板块 = 一章：超大编号 + 板块名 + 全部去处的链接矩阵。"""
    leaves = collect_leaves(board, posts)
    links = []
    for label, href in leaves:
        links.append(
            '<li><a href="{href}" title="{label}"><span class="idx-num">{n:02d}</span>'
            '<span class="idx-name">{label}</span><span class="idx-arrow" aria-hidden="true">↗</span></a></li>'.format(
                href=html.escape(url_for(href), quote=True),
                n=len(links) + 1,
                label=html.escape(label),
            )
        )
    return """    <article class="idx-chapter reveal" data-sector="{i}">
      <div class="idx-chapter-mark" aria-hidden="true">
        <span class="idx-chapter-no">{no:02d}</span>
        <span class="idx-chapter-en">{en}</span>
      </div>
      <div class="idx-chapter-body">
        <header class="idx-chapter-head">
          <h2><a href="{href}">{label}</a></h2>
          <p>{desc}</p>
          <span class="idx-chapter-count">{count:02d} ENTRIES</span>
        </header>
        <ol class="idx-links">
{links}
        </ol>
      </div>
    </article>""".format(
        i=i, no=i + 1, en=SECTOR_EN[i] if i < len(SECTOR_EN) else "SECTOR",
        href=html.escape(url_for(board["href"]), quote=True),
        label=html.escape(board["label"]), desc=html.escape(board["desc"]),
        count=len(leaves), links="\n".join(links),
    )


def main():
    posts = read_posts()
    nav = render_nav()
    chapters = "\n".join(render_chapter(b, i, posts) for i, b in enumerate(SITE_TREE))
    total = sum(len(collect_leaves(b, posts)) for b in SITE_TREE)

    body = """
  <section class="idx-hero">
    <div class="idx-hero-meta">
      <span>CENRYWANG / SITE INDEX</span>
      <span>EDITION 2026</span>
    </div>
    <h1 class="idx-hero-title reveal">站点索引</h1>
    <p class="idx-hero-sub reveal">{total} 个去处，4 个板块。<br />从这里进入网站的每一个角落。</p>
    <div class="idx-hero-rule" aria-hidden="true"></div>
  </section>

  <section class="idx-section">
{chapters}
  </section>
""".format(total=total, chapters=chapters)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(HEAD.format(favicon=FAVICON, nav=nav) + body + FOOT)
    print("built {} chapters / {} links -> {}".format(len(SITE_TREE), total, OUT))


if __name__ == "__main__":
    main()
