#!/usr/bin/env python3
"""全站导航与「板块目录」的唯一配置源（纯标准库，零依赖）。

站点结构是一棵树，改导航只改本文件：

    python scripts/sync_nav.py        # 同步所有手写页（含 bot 生成的 digest.html）
    python scripts/build_blog.py      # 重新生成 blog/*.html
    python scripts/build_sitemap.py   # 重新生成导航页 sitemap.html

build_blog.py / build_digest.py 直接 import 本模块，所以博客页与每日自动生成的
简报页始终使用同一套导航，不会被 bot 覆盖回旧版本。

层级约定（2026-11-15 重构）：
    一级：顶部主导航 4 个主板块（首页 / 信息 / 博客 / 奇思）
    二级：每个主板块左侧的「板块内目录」（render_sidebar 输出）
    三级：工具页的 7 个分类锚点，作为「工具」目录项的嵌套子项

原先 9 个入口把首页锚点（关于/技能/作品/推荐/联系）和独立页面
（工具/简报/行情/博客）混在一行，既长又分不清层级；现在顶部只保留 4 个
主板块，具体去处一律收进左侧目录，窄屏时目录退化为顶部横向滚动条。

参数说明：
    base  链接前缀。根目录页面用 ""，blog/ 子目录用 "../"，
          404 与 digest 用 "/"（绝对路径，任意 URL 下都正确）
    home  是否为首页（首页用 #home 锚点，其他页用 index.html）
    logo  logo 链接，默认首页 "index.html" / "#home"
    theme 是否输出明暗切换按钮（所有页面都输出，统一支持亮/暗）
    board 当前所属主板块（label 或 key），决定顶部高亮与是否输出左侧目录
    active 左侧目录中高亮的目录项 label
    sidebar_items 覆盖板块默认目录项，供博客页动态注入文章列表
"""
from html import escape

THEME_BUTTON = """    <button id="themeToggle" class="theme-toggle" type="button" aria-label="切换明暗主题">
      <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
    </button>
"""

# 工具页的 7 个二级分类。锚点与 tools.html 里 <h3 class="tools-cat" id="..."> 一一对应，
# 侧栏只在「工具」页展开它们，其它页面保持收拢，避免目录过长。
# 子项写成纯锚点（只在 tools.html 本页展开）；导航页生成时会自动补 tools.html 前缀。
TOOL_CATEGORIES = [
    ("AI大模型", "#cat-llm"),
    ("Coding工具", "#cat-coding"),
    ("常用框架", "#cat-framework"),
    ("常用工具软件", "#cat-software"),
    ("学习科研", "#cat-research"),
    ("设计绘图", "#cat-design"),
    ("Agent Skills", "#cat-skills"),
]

# 目录项格式：(label, href) 或 (label, href, [(sub_label, sub_href), ...])
# href 一律写成「相对站点根」的路径；render_sidebar 会按当前页 base 自动加前缀。
SITE_TREE = [
    {
        "key": "home",
        "label": "首页",
        "href": "index.html",
        "anchor": "#home",
        "desc": "关于我、技能、作品、推荐与联系方式",
        "items": [
            ("关于我", "index.html#about"),
            ("技能", "index.html#skills"),
            ("作品", "index.html#projects"),
            ("推荐", "index.html#recommend"),
            ("联系", "index.html#contact"),
        ],
    },
    {
        "key": "info",
        "label": "信息",
        "href": "info.html",
        "anchor": "",
        "desc": "每日简报、工具严选与贵金属宏观行情",
        "items": [
            ("板块概览", "info.html"),
            ("简报", "digest.html"),
            ("工具", "tools.html", TOOL_CATEGORIES),
            ("行情", "metals.html"),
        ],
    },
    {
        "key": "blog",
        "label": "博客",
        "href": "blog/index.html",
        "anchor": "",
        "desc": "随笔、笔记与研究碎片",
        # 文章由 build_blog.py 动态追加，保证导航页与侧栏都能列出最新文章
        "items": [("全部文章", "blog/index.html")],
    },
    {
        "key": "ideas",
        "label": "奇思",
        "href": "whimsy.html",
        "anchor": "",
        "desc": "一些好玩的小工具与实验",
        "items": [
            ("人生一万天", "whimsy.html#days"),
            ("合成大冒险", "merge-quest.html"),
        ],
    },
]

BOARD_LABELS = [b["label"] for b in SITE_TREE]
_BY_LABEL = {b["label"]: b for b in SITE_TREE}
_BY_KEY = {b["key"]: b for b in SITE_TREE}


def url_for(href, base=""):
    """把站点根相对路径转换成当前页可用的 URL；纯锚点 / 绝对 URL 原样返回。"""
    if href.startswith("#") or href.startswith("/") or href.startswith("http"):
        return href
    return base + href


def _find_board(board):
    if not board:
        return None
    return _BY_LABEL.get(board) or _BY_KEY.get(board)


def render_sidebar(board, active=None, base="", sidebar_items=None):
    """输出主板块左侧的「板块内目录」。board 为空时返回空串（不显示侧栏）。"""
    b = _find_board(board)
    if not b:
        return ""
    items = b["items"] if sidebar_items is None else sidebar_items
    rows = []
    for entry in items:
        label, href = entry[0], entry[1]
        children = entry[2] if len(entry) > 2 else []
        is_active = active is not None and active == label
        link = '<a href="{}"{}>{}</a>'.format(
            escape(url_for(href, base), quote=True),
            ' class="is-active" aria-current="page"' if is_active else "",
            escape(label),
        )
        sub = ""
        # 子目录只在当前目录项激活时展开
        if children and is_active:
            sub = '<ul class="board-tree-sub">' + "".join(
                '<li><a href="{}">{}</a></li>'.format(
                    escape(url_for(c[1], base), quote=True), escape(c[0])
                )
                for c in children
            ) + "</ul>"
        rows.append("<li{}>{}{}</li>".format(' class="has-sub"' if sub else "", link, sub))
    return (
        '<aside class="board-sidebar">\n'
        '  <div class="board-sidebar-head">\n'
        '    <span class="board-kicker">板块目录</span>\n'
        '    <strong class="board-name">{}</strong>\n'
        '  </div>\n'
        '  <nav class="board-tree-nav" aria-label="{}板块目录">\n'
        '    <ul class="board-tree">\n'
        '      {}\n'
        '    </ul>\n'
        '  </nav>\n'
        '  <a class="board-map-link" href="{}">站点分支结构 →</a>\n'
        '</aside>'
    ).format(
        escape(b["label"]),
        escape(b["label"]),
        "\n      ".join(rows),
        escape(url_for("sitemap.html", base), quote=True),
    )


def render(base="", home=False, logo=None, theme=True, board=None, active=None, sidebar_items=None):
    """生成 <nav class="nav">（+ 可选的 <aside class="board-sidebar">）HTML 片段。"""
    if logo is None:
        logo = "#home" if home else base + "index.html"
    items = []
    current = _find_board(board)
    for b in SITE_TREE:
        href = b["anchor"] if (home and b["anchor"]) else b["href"]
        url = url_for(href, base)
        attrs = ' class="nav-active" aria-current="page"' if current is b else ""
        items.append(
            '      <li><a href="{}"{}>{}</a></li>'.format(
                escape(url, quote=True), attrs, escape(b["label"])
            )
        )
    # 导航页是工具型入口，放在主板块列表之外，避免占用「四个主板块」的层级
    map_link = '    <a class="nav-map" href="{}" title="查看站点分支结构">导航</a>\n'.format(
        escape(url_for("sitemap.html", base), quote=True)
    )
    button = THEME_BUTTON if theme else ""
    nav = (
        '  <nav class="nav">\n'
        '    <a href="{}" class="nav-logo">Cenry</a>\n'
        '    <ul class="nav-links">\n'
        '{}\n'
        '    </ul>\n'
        '{}{}'
        '  </nav>'
    ).format(escape(logo, quote=True), "\n".join(items), map_link, button)
    # 首页本身的目录用纯锚点，避免点「关于我」时整页重载
    if home and current is not None and current["key"] == "home" and sidebar_items is None:
        sidebar_items = []
        for e in current["items"]:
            href = e[1].replace("index.html#", "#", 1)
            sidebar_items.append((e[0], href, e[2]) if len(e) > 2 else (e[0], href))
    sidebar = render_sidebar(board, active, base, sidebar_items)
    return nav + ("\n" + sidebar if sidebar else "")
