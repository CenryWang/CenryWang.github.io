#!/usr/bin/env python3
"""把 scripts/nav.py 的「4 主板块导航 + 左侧板块目录」同步到所有页面。

用法：
    python scripts/sync_nav.py                     # 同步全部页面
    python scripts/sync_nav.py --only digest.html  # 只同步指定文件（工作流用）

替换单元是「<nav>…</nav> + 紧随其后的可选 <aside class="board-sidebar">…</aside>」，
因此重复运行是幂等的：第二次会把上一次生成的侧栏一并换掉，不会叠加。
同时按是否输出侧栏维护 <body class="has-board">，让 CSS 给内容让出左侧空间。

digest.html 由 bot 每日生成，这里也纳入同步：即使某次生成用了旧模板，
导航与侧栏也会被强制拉回 nav.py 的唯一配置，不会悄悄回退。

blog/*.html 由 build_blog.py 生成，构建时直接 import nav.py，不在此处理。
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nav import render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# board/active 决定顶部高亮与左侧目录内容；base 决定链接前缀
TARGETS = [
    ("index.html", dict(home=True, board="首页")),
    ("info.html", dict(board="信息", active="板块概览")),
    ("tools.html", dict(board="信息", active="工具")),
    ("metals.html", dict(board="信息", active="行情")),
    ("whimsy.html", dict(board="奇思", active="人生一万天")),
    ("sitemap.html", dict()),                      # 导航页不显示侧栏，自身就是全站目录
    ("404.html", dict(base="/", logo="/")),        # 404 不属于任何主板块
    ("digest.html", dict(base="/", logo="/", board="信息", active="简报")),
]

# 允许前导缩进不同（生成页与手写页缩进可能不一致）
PATTERN = re.compile(
    r"[ \t]*<nav class=\"nav\">.*?</nav>(?:\s*<aside class=\"board-sidebar\">.*?</aside>)?",
    re.S,
)


def sync_body_class(text, has_sidebar):
    """有侧栏就给 body 加 has-board，没有就去掉（幂等替换）。"""
    def repl(match):
        attrs = match.group(1) or ""
        cm = re.search(r'class="([^"]*)"', attrs)
        if cm:
            classes = [c for c in cm.group(1).split() if c != "has-board"]
            if has_sidebar:
                classes.append("has-board")
            new_class = " ".join(classes)
            if new_class:
                return "<body" + attrs.replace(cm.group(0), 'class="{}"'.format(new_class)) + ">"
            return "<body" + attrs.replace(cm.group(0), "") + ">"
        if has_sidebar:
            return '<body class="has-board"' + attrs + ">"
        return match.group(0)
    return re.sub(r"<body([^>]*)>", repl, text, count=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="*", help="仅同步这些相对路径（默认全部）")
    args = parser.parse_args()
    only = set(args.only) if args.only else None

    changed = []
    for rel, kwargs in TARGETS:
        if only is not None and rel not in only:
            continue
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print("WARN: missing {}".format(rel))
            continue
        with open(path, "r", encoding="utf-8", newline="") as f:
            text = f.read()
        newline = "\r\n" if "\r\n" in text else "\n"
        snippet = render(**kwargs).replace("\n", newline)
        has_sidebar = '<aside class="board-sidebar">' in snippet
        updated, count = PATTERN.subn(lambda _: snippet, text, count=1)
        if count == 0:
            print("WARN: no nav block found in {}".format(rel))
            continue
        updated = sync_body_class(updated, has_sidebar)
        if updated != text:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(updated)
            changed.append(rel)
    print("nav synced: " + (", ".join(changed) if changed else "already up to date"))


if __name__ == "__main__":
    main()
