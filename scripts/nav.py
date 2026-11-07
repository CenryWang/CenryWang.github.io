#!/usr/bin/env python3
"""全站导航的唯一配置源（纯标准库，零依赖）。

改导航只改本文件，然后运行：

    python scripts/sync_nav.py        # 同步到手写页面
    python scripts/build_blog.py      # 重新生成博客页

build_blog.py / build_digest.py 会直接 import 本模块，所以 bot 每天
自动生成的 digest.html 也始终使用同一套导航，不会回退。

参数说明：
    base  链接前缀。根目录页面用 ""，blog/ 子目录用 "../"，
          404 与 digest 用 "/"（绝对路径，任意 URL 下都正确）
    home  是否为首页（首页用 #anchor，其他页用 index.html#anchor）
    logo  logo 链接，默认首页 "index.html" / "#home"
    theme 是否输出明暗切换按钮（404 / digest 有自己的内联脚本，不带按钮）
"""
from html import escape

THEME_BUTTON = """    <button id="themeToggle" class="theme-toggle" type="button" aria-label="切换明暗主题">
      <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
    </button>
"""

HOME_LINKS = [
    ("关于", "#about"),
    ("技能", "#skills"),
    ("作品", "#projects"),
    ("推荐", "#recommend"),
    ("工具", "tools.html"),
    ("简报", "digest.html"),
    ("行情", "metals.html"),
    ("博客", "blog/index.html"),
    ("联系", "#contact"),
]

SUB_LINKS = [
    ("关于", "index.html#about"),
    ("技能", "index.html#skills"),
    ("作品", "index.html#projects"),
    ("推荐", "index.html#recommend"),
    ("工具", "tools.html"),
    ("简报", "digest.html"),
    ("行情", "metals.html"),
    ("博客", "blog/index.html"),
    ("联系", "index.html#contact"),
]


def render(base="", home=False, logo=None, theme=True):
    """生成一段完整的 <nav class="nav"> HTML。"""
    if logo is None:
        logo = "#home" if home else base + "index.html"
    links = HOME_LINKS if home else SUB_LINKS
    items = []
    for label, href in links:
        url = href if href.startswith("#") else base + href
        items.append(
            '      <li><a href="{}">{}</a></li>'.format(escape(url, quote=True), escape(label))
        )
    button = THEME_BUTTON if theme else ""
    return (
        '  <nav class="nav">\n'
        '    <a href="{}" class="nav-logo">Cenry</a>\n'
        '    <ul class="nav-links">\n'
        '{}\n'
        '    </ul>\n'
        '{}'
        '  </nav>'
    ).format(escape(logo, quote=True), "\n".join(items), button)
