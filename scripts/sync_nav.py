#!/usr/bin/env python3
"""把 scripts/nav.py 的导航片段同步到所有页面。

用法：
    python scripts/sync_nav.py                    # 同步全部页面
    python scripts/sync_nav.py --only digest.html # 只同步指定文件（工作流用）

只替换每个文件里的第一段 <nav class="nav">…</nav>，其余内容原样保留。
digest.html 由 bot 每日生成，这里也纳入同步：即使某次生成用了旧模板，
导航也会被强制拉回 nav.py 的唯一配置，不会悄悄回退。

blog/*.html 由 build_blog.py 生成，构建时直接 import nav.py，不在此处理。
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nav import render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGETS = [
    ("index.html", dict(home=True)),
    ("tools.html", dict()),
    ("metals.html", dict()),
    ("404.html", dict(base="/", logo="/", theme=False)),
    ("digest.html", dict(base="/", logo="/", theme=False)),
]

# 允许前导缩进不同（生成页与手写页缩进可能不一致）
PATTERN = re.compile(r"[ \t]*<nav class=\"nav\">.*?</nav>", re.S)


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
        updated, count = PATTERN.subn(lambda _: snippet, text, count=1)
        if count == 0:
            print("WARN: no nav block found in {}".format(rel))
            continue
        if updated != text:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(updated)
            changed.append(rel)
    print("nav synced: " + (", ".join(changed) if changed else "already up to date"))


if __name__ == "__main__":
    main()
