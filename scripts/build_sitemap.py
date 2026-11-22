#!/usr/bin/env python3
"""从 nav.py 的站点树生成「导航页」sitemap.html（纯标准库，零依赖）。

用法：python scripts/build_sitemap.py

页面展示本站的完整分支结构：4 个主板块 → 板块内目录 → 工具页 7 个分类。
结构完全来自 nav.py 这一处配置，改导航后重跑本脚本即可，导航页不会与
实际站点脱节；博客文章从 blog/posts/*.md 的 frontmatter 动态读取。
"""
import glob
import html
import math
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
  <script>
    (function () {
      var out = document.getElementById("starReadout");
      var map = document.querySelector(".star-map");
      if (!out || !map) return;
      var nodes = map.querySelectorAll(".star-node");
      Array.prototype.forEach.call(nodes, function (a) {
        function show() {
          out.textContent = a.getAttribute("data-label") + " → " + a.getAttribute("data-href");
          out.classList.add("is-live");
        }
        a.addEventListener("mouseenter", show);
        a.addEventListener("focus", show);
      });
      map.addEventListener("mouseleave", function () {
        out.textContent = "悬停任意节点查看去处，点击即可跳转";
        out.classList.remove("is-live");
      });
    })();
  </script>
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


STAR_CX, STAR_CY = 450.0, 350.0
STAR_R_BOARD, STAR_R_LEAF = 150.0, 268.0


def _pol(r, deg):
    """极坐标转直角坐标（角度制，0° 指向右侧）。"""
    rad = math.radians(deg)
    return STAR_CX + r * math.cos(rad), STAR_CY + r * math.sin(rad)


def _f(v):
    return "{:.1f}".format(v)


def render_star_map(posts):
    """把 SITE_TREE 摊成极坐标星图：中心 → 4 主板块 → 全部叶子节点。

    每个 <a> 内都带 <title>label</title>：既是原生 tooltip / 无障碍文本，
    也让 check_site_health.py 的 SITEMAP_REQUIRED 文本核对仍然成立
    （星图不能只画点，分支标签必须留在 HTML 源码里）。
    颜色全部交给 style.css 的 CSS 变量，明暗主题自动适配。
    """
    boards = []
    total = 0
    for board in SITE_TREE:
        items = branch_items(board, posts)
        leaves = []
        for entry in items:
            label, href = entry[0], entry[1]
            children = entry[2] if len(entry) > 2 else []
            leaves.append((label, url_for(href)))
            for c in children:
                sub_href = href + c[1] if c[1].startswith("#") else c[1]
                leaves.append((c[0], url_for(sub_href)))
        boards.append((board, leaves))
        total += len(leaves)

    out = [
        '<svg class="star-map" viewBox="70 40 760 620" width="100%" height="auto" '
        'role="img" aria-label="站点星图：4 个主板块与全部子页面">',
        '  <g class="star-orbits" aria-hidden="true">',
        '    <circle cx="450" cy="350" r="150"/>',
        '    <circle cx="450" cy="350" r="268"/>',
        '  </g>',
        '  <g class="star-core">',
        '    <circle cx="450" cy="350" r="40"/>',
        '    <text x="450" y="345" text-anchor="middle">Cenry</text>',
        '    <text x="450" y="366" text-anchor="middle" class="star-core-sub">'
        '4 板块 · {} 节点</text>'.format(total),
        '  </g>',
    ]

    for i, (board, leaves) in enumerate(boards):
        center_deg = -90 + i * 90
        bx, by = _pol(STAR_R_BOARD, center_deg)
        out.append('  <g class="star-branch" data-board="{}">'.format(i))
        out.append('    <path class="star-edge star-edge--trunk" d="M{},{} L{},{}"/>'.format(
            _f(STAR_CX), _f(STAR_CY), _f(bx), _f(by)))
        n = len(leaves)
        for k, (label, href) in enumerate(leaves):
            deg = center_deg + (-33 + 66 * (k / max(1, n - 1)) if n > 1 else 0)
            lx, ly = _pol(STAR_R_LEAF, deg)
            out.append('    <path class="star-edge" d="M{},{} L{},{}"/>'.format(
                _f(bx), _f(by), _f(lx), _f(ly)))
            esc_href = html.escape(href, quote=True)
            esc_label = html.escape(label, quote=True)
            out.append(
                '    <a class="star-node star-node--leaf" href="{}" '
                'data-label="{}" data-href="{}">'
                '<circle cx="{}" cy="{}" r="5.5"/><title>{}</title></a>'.format(
                    esc_href, esc_label, esc_href, _f(lx), _f(ly), esc_label)
            )
        board_href = html.escape(url_for(board["href"]), quote=True)
        board_label = html.escape(board["label"], quote=True)
        out.append(
            '    <a class="star-node star-node--board" href="{}" '
            'data-label="{}" data-href="{}">'
            '<circle cx="{}" cy="{}" r="25"/>'
            '<text x="{}" y="{}" text-anchor="middle" dominant-baseline="central">{}</text>'
            '<title>{}</title></a>'.format(
                board_href, board_label, board_href,
                _f(bx), _f(by), _f(bx), _f(by), board_label, board_label)
        )
        out.append('  </g>')
    out.append('</svg>')
    return "\n".join(out)


def main():
    posts = read_posts()
    nav = render_nav()
    branches = "".join(
        render_branch(b, i + 1, posts) for i, b in enumerate(SITE_TREE)
    )
    star = render_star_map(posts)
    body = """
  <header class="hero hero--compact">
    <div class="hero-inner">
      <p class="hero-greeting reveal">Site Map</p>
      <h1 class="hero-name hero-name--compact reveal">站点导航</h1>
      <p class="hero-typed"><span>把整站摊开成一张可以点的星图</span></p>
    </div>
  </header>

  <section class="section star-section">
    <h2 class="section-title reveal">星图</h2>
    <div class="star-map-wrap glass reveal">
      <p class="star-readout" id="starReadout">悬停任意节点查看去处，点击即可跳转</p>
      <div class="star-map-scroll">
{star}
      </div>
      <p class="star-hint">中心 → 4 个主板块 → 全部叶子节点 · 窄屏可左右滑动</p>
    </div>
  </section>

  <section class="section sitemap-section">
    <h2 class="section-title reveal">完整目录</h2>
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
""".format(star=star, count=sum(len(branch_items(b, posts)) for b in SITE_TREE), branches=branches)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(HEAD.format(favicon=FAVICON, nav=nav) + body + FOOT)
    print("built {} -> {}".format(len(SITE_TREE), OUT))


if __name__ == "__main__":
    main()
