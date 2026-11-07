#!/usr/bin/env python3
"""把 scripts/nav.py 的导航片段同步到所有手写页面。

用法：python scripts/sync_nav.py

只替换每个文件里的第一段 <nav class="nav">…</nav>，其余内容原样保留。
生成类页面（blog/*.html、digest.html）不在这里处理，它们由各自的
构建脚本从 nav.py 直接取导航。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nav import render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGETS = [
    ("index.html", dict(home=True)),
    ("now.html", dict()),
    ("tools.html", dict()),
    ("metals.html", dict()),
    ("404.html", dict(base="/", logo="/", theme=False)),
]

PATTERN = re.compile(r"  <nav class=\"nav\">.*?  </nav>", re.S)


def main():
    changed = []
    for rel, kwargs in TARGETS:
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
