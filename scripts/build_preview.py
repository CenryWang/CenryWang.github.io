#!/usr/bin/env python3
"""生成自包含的静态预览快照（仅用于本地 / WorkBuddy 面板预览，不属于站点产物）。

为什么需要：预览服务会把「被打开文件的所在目录」单独映射成
/static-html/<hash>/。直接打开 blog/index.html 时 blog/ 成了映射根，
页面里的 ../style.css 会解析到映射之外 → 404，页面只剩裸文字。
本脚本把 CSS / JS 内联、把站内链接全部改写到同一目录，
快照里的每个页面都不依赖任何外部资源，任何映射方式下都能完整显示。

用法：
    python scripts/build_preview.py                 # 输出到系统临时目录
    python scripts/build_preview.py <输出目录>      # 指定输出目录

注意：快照只是「看效果」用，不要把它当站点提交；站点源文件仍是原来的结构。
"""
import os
import re
import sys
import shutil
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (站点内相对路径, 快照内文件名, 是否位于 blog/ 子目录)
PAGES = [
    ("index.html", "index.html", False),
    ("info.html", "info.html", False),
    ("tools.html", "tools.html", False),
    ("metals.html", "metals.html", False),
    ("whimsy.html", "whimsy.html", False),
    ("sitemap.html", "sitemap.html", False),
    ("404.html", "404.html", False),
    ("digest.html", "digest.html", False),
    ("merge-quest.html", "merge-quest.html", False),
    ("blog/index.html", "blog.html", True),
    ("blog/welcome.html", "welcome.html", True),
]

# 这些资源会被内联，不再以相对路径引用
CSS_LINK = re.compile(r'<link[^>]+rel="stylesheet"[^>]*href="[^"]*style\.css"[^>]*/?>', re.I)
JS_SCRIPT = re.compile(r'<script[^>]+src="[^"]*script\.js"[^>]*>\s*</script>', re.I)
ATTR = re.compile(r'(\b(?:href|src)=")([^"]+)(")')


def map_href(href, from_blog):
    """把站点内链接改写成快照同一目录下的文件名。"""
    if not href or href.startswith(("http:", "https:", "//", "data:", "mailto:", "#", "'", "javascript:")):
        return href
    path, sep, frag = href.partition("#")
    if path.startswith("./"):
        path = path[2:]
    if path.startswith("../"):
        path = path[3:]
    elif path.startswith("/"):
        path = path[1:]
    elif from_blog and path == "index.html":
        # 文章页的「← 返回博客列表」在 blog/ 下指向 blog/index.html
        path = "blog.html"
    if path in ("", "/"):
        path = "index.html"
    if path == "blog/index.html":
        path = "blog.html"
    elif path.startswith("blog/"):
        path = path[len("blog/"):]
    return path + (sep + frag if sep else "")


def build(out_dir):
    css = open(os.path.join(ROOT, "style.css"), encoding="utf-8").read()
    js = open(os.path.join(ROOT, "script.js"), encoding="utf-8").read()
    if "</style" in css.lower() or "</script" in js.lower():
        raise RuntimeError("CSS / JS 含有会截断内联标签的字符串，需要先转义")

    os.makedirs(out_dir, exist_ok=True)
    made = []
    for src, dst, from_blog in PAGES:
        text = open(os.path.join(ROOT, src), encoding="utf-8").read()
        # 用 lambda 作为替换值：re.sub 的字符串替换会把内容里的 \s / \d 当转义解析
        text = CSS_LINK.sub(lambda m: "<style>\n" + css + "\n</style>", text)
        text = JS_SCRIPT.sub(lambda m: "<script>\n" + js + "\n</script>", text)
        text = ATTR.sub(lambda m: m.group(1) + map_href(m.group(2), from_blog) + m.group(3), text)
        with open(os.path.join(out_dir, dst), "w", encoding="utf-8") as f:
            f.write(text)
        made.append(dst)

    # 行情页运行时会 fetch 数据，快照里也要有一份
    data_src = os.path.join(ROOT, "data", "metals.json")
    if os.path.exists(data_src):
        os.makedirs(os.path.join(out_dir, "data"), exist_ok=True)
        shutil.copy2(data_src, os.path.join(out_dir, "data", "metals.json"))

    return made


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "mypb05-site-preview")
    made = build(out)
    print("preview -> {} ({} pages)".format(out, len(made)))
    for name in made:
        print("  " + name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
