#!/usr/bin/env python3
"""极简静态博客构建器（纯标准库，零依赖）。

读取 blog/posts/*.md（带 YAML 风格 frontmatter），生成：
  - blog/index.html      博客索引（卡片列表）
  - blog/<slug>.html     每篇文章独立页

用法：python scripts/build_blog.py
样式与首页共用 ../style.css，交互复用 ../script.js（粒子 / 主题切换 / 滚动揭示）。
"""
import os
import re
import html
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "blog", "posts")
OUT_DIR = os.path.join(ROOT, "blog")

NAV = """
  <nav class="nav">
    <a href="../index.html" class="nav-logo">Cenry</a>
    <ul class="nav-links">
      <li><a href="../index.html#about">关于</a></li>
      <li><a href="../index.html#projects">作品</a></li>
      <li><a href="index.html">博客</a></li>
      <li><a href="../digest.html">简报</a></li>
      <li><a href="../now.html">现在</a></li>
      <li><a href="../index.html#contact">联系</a></li>
    </ul>
    <button id="themeToggle" class="theme-toggle" type="button" aria-label="切换明暗主题">
      <svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
      <svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
    </button>
  </nav>
"""

HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} · Cenry 博客</title>
  <meta name="description" content="{desc}" />
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%2322d3ee'/%3E%3Cstop offset='1' stop-color='%23a855f7'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='64' height='64' rx='14' fill='%2306060d'/%3E%3Ctext x='32' y='46' font-family='Segoe UI,Arial,sans-serif' font-size='40' font-weight='700' fill='url(%23g)' text-anchor='middle'%3EC%3C/text%3E%3C/svg%3E" />
  <link rel="stylesheet" href="../style.css" />
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
    <div>© <span id="year">2026</span> CenryWang · <a href="../index.html" style="color:var(--muted)">返回首页</a></div>
  </footer>
  <script src="../script.js"></script>
</body>
</html>
"""


def parse_frontmatter(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            fm = text[3:end].strip()
            body = text[end + 4:]
            meta = {}
            for line in fm.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            return meta, body
    return {}, text


def md_inline(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def md_to_html(md):
    lines = md.splitlines()
    out = []
    i = 0
    in_code = False
    code_buf = []
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
                code_buf = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue
        if not line.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level = min(len(m.group(1)) + 1, 4)
            out.append(f"<h{level}>{md_inline(m.group(2))}</h{level}>")
            i += 1
            continue
        if line.startswith(">"):
            out.append("<blockquote>" + md_inline(line[1:].strip()) + "</blockquote>")
            i += 1
            continue
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i]):
                items.append("<li>" + md_inline(re.sub(r"^[-*]\s+", "", lines[i])) + "</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                items.append("<li>" + md_inline(re.sub(r"^\d+\.\s+", "", lines[i])) + "</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", ">", "```")) and not re.match(r"^[-*]\s+|\d+\.\s+", lines[i]):
            para.append(lines[i])
            i += 1
        out.append("<p>" + md_inline(" ".join(para)) + "</p>")
    return "\n".join(out)


def render_post(meta, body_html, slug):
    title = meta.get("title", slug)
    desc = meta.get("description", title)
    date = meta.get("date", "")
    tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    tag_html = " · ".join(f'<span class="gh-label">{t}</span>' for t in tags) if tags else ""
    meta_line = (date + ("　" if date and tag_html else "") + tag_html)
    head = HEAD.format(title=html.escape(title), desc=html.escape(desc), nav=NAV)
    body = f"""
  <header class="hero">
    <div class="hero-inner">
      <p class="hero-greeting reveal">博客</p>
      <h1 class="hero-name reveal" style="font-size:clamp(1.8rem,6vw,3.4rem)">{html.escape(title)}</h1>
      <p class="hero-typed"><span>{html.escape(meta_line)}</span></p>
    </div>
  </header>
  <section class="section">
    <article class="about-card glass reveal" style="max-width:760px;margin:0 auto">
{body_html}
      <p style="margin-top:28px"><a href="index.html" style="color:var(--accent1)">← 返回博客列表</a></p>
    </article>
  </section>
"""
    return head + body + FOOT


def render_index(posts):
    cards = []
    for p in sorted(posts, key=lambda x: x[0].get("date", ""), reverse=True):
        meta, slug = p[0], p[2]
        title = html.escape(meta.get("title", slug))
        desc = html.escape(meta.get("description", ""))
        date = meta.get("date", "")
        tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
        tag_html = " ".join(f'<span class="gh-label">{html.escape(t)}</span>' for t in tags)
        cards.append(f"""
      <article class="project glass reveal">
        <h3><a href="{slug}.html" style="color:var(--text);text-decoration:none">{title}</a></h3>
        <p>{desc}</p>
        <div class="gh-meta"><span>{date}</span>{('&nbsp;' + tag_html) if tag_html else ''}</div>
      </article>""")
    head = HEAD.format(title="博客", desc="CenryWang 的随笔与笔记", nav=NAV)
    body = f"""
  <header class="hero">
    <div class="hero-inner">
      <p class="hero-greeting reveal">写作</p>
      <h1 class="hero-name reveal" style="font-size:clamp(1.8rem,6vw,3.4rem)">博客</h1>
      <p class="hero-typed"><span>随笔 · 笔记 · 研究碎片</span></p>
    </div>
  </header>
  <section class="section">
    <div class="projects-grid">
{''.join(cards)}
    </div>
  </section>
"""
    return head + body + FOOT


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    posts = []
    for path in sorted(glob.glob(os.path.join(POSTS_DIR, "*.md"))):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        meta, body = parse_frontmatter(text)
        slug = meta.get("slug") or os.path.splitext(os.path.basename(path))[0]
        body_html = md_to_html(body)
        with open(os.path.join(OUT_DIR, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(render_post(meta, body_html, slug))
        posts.append((meta, body_html, slug))
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(posts))
    print(f"built {len(posts)} post(s) + index -> {OUT_DIR}")


if __name__ == "__main__":
    main()
