# -*- coding: utf-8 -*-
"""把 fetch_robotics.py 产出的 JSON 渲染成 robotics.html + robotics.xml + papers/YYYY-MM-DD.md。

调用方式：python3 scripts/build_robotics.py <cache/robotics/YYYY-MM-DD.json> <out_dir>
由 .github/workflows/robotics.yml 每日调用。本脚本零外部依赖（仅 Python 标准库）。

页面结构：
  顶部 meta（同步时间 + 命中数 + RSS 链接）
  「今日精选 N 篇」  Top 5：全量展示（标题 / 作者 / 会议标签 / 摘要前 320 字 / arXiv+PDF 链接）
  「其余 M 篇」       折叠列表（仅标题 + 会议标签）
  「历史归档」        按日期倒序列出已生成的 papers/*.md
"""
import datetime
import glob
import json
import os
import re
import sys

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>机器人文献 · Cenry</title>
<meta name="description" content="每日精选 arXiv 机器人论文，GitHub Actions 自动更新" />
<link rel="alternate" type="application/rss+xml" title="机器人文献 RSS" href="robotics.xml" />
<link rel="stylesheet" href="style.css" />
<style>
  .robo-shell { max-width: 1080px; }
  .robo-meta { text-align: center; color: var(--muted); font-size: 0.95rem; margin: -18px 0 30px; }
  .robo-meta a { color: var(--accent1); text-decoration: none; }
  .robo-meta a:hover { text-decoration: underline; }
  .robo-body h2 { margin: 44px 0 16px; font-size: 1.35rem; }
  .robo-body h2::after {
    content: ""; display: block; width: 44px; height: 3px; margin-top: 8px;
    background: linear-gradient(90deg, var(--accent1), var(--accent2)); border-radius: 2px;
  }
  .paper-list { display: flex; flex-direction: column; gap: 18px; margin-top: 12px; }
  .paper {
    border: 1px solid var(--glass-border); border-radius: 14px;
    padding: 20px 22px; background: rgba(255, 255, 255, 0.02);
    transition: transform .15s ease, border-color .15s ease;
  }
  .paper:hover { border-color: var(--accent1); transform: translateY(-2px); }
  .paper-title { font-size: 1.05rem; font-weight: 600; margin: 0 0 6px; }
  .paper-title a { color: var(--accent1); text-decoration: none; }
  .paper-title a:hover { text-decoration: underline; }
  .paper-authors { font-size: 0.82rem; color: var(--muted); margin-bottom: 8px; }
  .paper-tags { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; font-size: 0.72rem; }
  .tag-conf {
    padding: 2px 9px; border-radius: 999px;
    background: linear-gradient(90deg, var(--accent1), var(--accent2));
    color: #fff; font-weight: 500;
  }
  .tag-dir {
    padding: 2px 9px; border-radius: 999px;
    border: 1px solid var(--accent1); color: var(--accent1);
    font-weight: 500; font-size: 0.7rem;
  }
  .tag-quant {
    padding: 2px 9px; border-radius: 999px;
    border: 1px solid var(--accent2); color: var(--accent2);
    font-family: var(--font-mono); font-size: 0.7rem;
  }
  .tag-cat {
    padding: 2px 9px; border-radius: 999px;
    border: 1px solid var(--glass-border); color: var(--muted);
  }
  .tag-score {
    padding: 2px 9px; border-radius: 999px;
    border: 1px solid var(--accent1); color: var(--accent1);
  }
  .paper-summary { color: var(--muted); font-size: 0.88rem; line-height: 1.7; margin: 0 0 10px; }
  .paper-links { font-size: 0.8rem; }
  .paper-links a { color: var(--accent1); text-decoration: none; margin-right: 14px; }
  .paper-links a:hover { text-decoration: underline; }
  .paper-id { color: var(--muted); font-size: 0.74rem; margin-left: 4px; }
  details.more { margin-top: 12px; }
  details.more > summary {
    cursor: pointer; color: var(--muted); font-size: 0.9rem;
    padding: 10px 14px; border: 1px solid var(--glass-border); border-radius: 10px;
    list-style: none;
  }
  details.more > summary::-webkit-details-marker { display: none; }
  details.more > summary::before { content: "▸ "; color: var(--accent1); }
  details.more[open] > summary::before { content: "▾ "; }
  details.more > ul { margin: 12px 0 0 8px; color: var(--muted); font-size: 0.9rem; line-height: 1.85; list-style: none; padding: 0; }
  details.more > ul li { padding: 4px 0; }
  details.more > ul a { color: var(--accent1); text-decoration: none; }
  details.more > ul a:hover { text-decoration: underline; }
  details.more > ul .conf { color: var(--muted); font-size: 0.78rem; margin-left: 6px; }
  .archive-list {
    display: flex; flex-direction: column; gap: 8px;
    padding: 14px 18px; border: 1px solid var(--glass-border); border-radius: 12px;
    font-size: 0.9rem;
  }
  .archive-list a { color: var(--accent1); text-decoration: none; }
  .archive-list a:hover { text-decoration: underline; }
  .archive-empty { color: var(--muted); font-size: 0.9rem; }
  .robo-footer { text-align: center; color: var(--muted); font-size: 0.85rem; margin-top: 50px; }
  .robo-empty {
    text-align: center; color: var(--muted); padding: 40px 20px;
    border: 1px dashed var(--glass-border); border-radius: 12px;
  }
</style>
</head>
<body>
  <div class="scroll-progress" id="scrollProgress"></div>

  <div class="aurora" aria-hidden="true">
    <span class="blob blob-1"></span>
    <span class="blob blob-2"></span>
    <span class="blob blob-3"></span>
  </div>

  <nav class="nav">
    <a href="/" class="nav-logo">Cenry</a>
    <ul class="nav-links">
      <li><a href="robotics.html">文献</a></li>
      <li><a href="digest.html">简报</a></li>
      <li><a href="/">首页</a></li>
    </ul>
  </nav>

  <section class="section robo-shell">
    <h2 class="section-title">机器人文献</h2>
    <p class="robo-meta">__META__ · 每日北京时间 08:17 自动更新 · <a href="robotics.xml">RSS 订阅</a></p>
    <div class="glass robo-body">
__BODY__
    </div>
  </section>

  <footer class="robo-footer">© 2026 CenryWang · 数据来自 arXiv，GitHub Actions 自动生成</footer>

  <script>
    (function () {
      var bar = document.getElementById("scrollProgress");
      window.addEventListener("scroll", function () {
        var h = document.documentElement;
        bar.style.width = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100 + "%";
      });
      if ("IntersectionObserver" in window) {
        var io = new IntersectionObserver(function (entries) {
          entries.forEach(function (e) { if (e.isIntersecting) e.target.classList.add("visible"); });
        }, { threshold: 0.05 });
        document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
      } else {
        document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("visible"); });
      }
    })();
  </script>
</body>
</html>
"""

FEATURED_LIMIT = 5
CONF_PATTERN = re.compile(
    r"(?:Accepted at|Accepted by|Accepted to|To appear in|to be published in|published in)\s+([A-Z][A-Za-z0-9 \-]{2,40})",
    re.IGNORECASE,
)

# 会议归一（命中即替换为简写）
CONF_ALIASES = [
    ("Conference on Robot Learning", "CoRL"),
    ("Robotics: Science and Systems", "RSS"),
    ("IEEE International Conference on Robotics and Automation", "ICRA"),
    ("International Conference on Robotics and Automation", "ICRA"),
    ("IEEE/RSJ International Conference on Intelligent Robots and Systems", "IROS"),
    ("Intelligent Robots and Systems", "IROS"),
    ("IEEE Robotics and Automation Letters", "RA-L"),
    ("Robotics and Automation Letters", "RA-L"),
    ("IEEE Transactions on Robotics", "T-RO"),
    ("Transactions on Robotics", "T-RO"),
    ("International Journal of Robotics Research", "IJRR"),
    ("Science Robotics", "Science Robotics"),
    ("Nature Machine Intelligence", "Nature Machine Intelligence"),
    ("Neural Information Processing Systems", "NeurIPS"),
    ("International Conference on Machine Learning", "ICML"),
    ("Conference on Computer Vision and Pattern Recognition", "CVPR"),
]


def esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def short_summary(text: str, n: int = 320) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0]
    return cut + "…"


def fmt_authors(authors: list[str]) -> str:
    if not authors:
        return "匿名"
    if len(authors) <= 4:
        return ", ".join(authors)
    return ", ".join(authors[:4]) + f" 等 {len(authors)} 人"


def extract_conf(comment: str) -> str:
    if not comment:
        return ""
    m = CONF_PATTERN.search(comment)
    if not m:
        return ""
    raw = m.group(1).strip()
    for needle, alias in CONF_ALIASES:
        if needle.lower() in raw.lower():
            return alias
    # 没匹配到别名就保留原文（裁掉尾随数字 / 期号）
    raw = re.sub(r"\s+\d{4}.*$", "", raw)
    raw = re.sub(r"\s+\d{1,3}.*$", "", raw)
    return raw.strip() or raw


def render_paper(p: dict) -> str:
    conf = extract_conf(p.get("comment", ""))
    tags: list[str] = []
    if conf:
        tags.append(f'<span class="tag-conf">{esc(conf)}</span>')
    for d in p.get("directions", []):
        tags.append(f'<span class="tag-dir">{esc(d)}</span>')
    for q in p.get("quant", []):
        tags.append(f'<span class="tag-quant">{esc(q)}</span>')
    if p.get("primary_category"):
        tags.append(f'<span class="tag-cat">{esc(p["primary_category"])}</span>')
    if p.get("score", 0) > 0:
        tags.append(f'<span class="tag-score">+{p["score"]}</span>')

    authors_str = fmt_authors(p.get("authors", []))
    summary_html = short_summary(p.get("summary", ""))
    abs_url = p.get("abs_url", "#")
    pdf_url = p.get("pdf_url", "#")
    arxiv_id = p.get("arxiv_id", "")

    return f"""<article class="paper">
<h3 class="paper-title"><a href="{esc(abs_url)}" target="_blank" rel="noopener">{esc(p.get("title", ""))}</a></h3>
<div class="paper-authors">{esc(authors_str)}</div>
<div class="paper-tags">{''.join(tags)}</div>
<p class="paper-summary">{esc(summary_html)}</p>
<div class="paper-links">
  <a href="{esc(abs_url)}" target="_blank" rel="noopener">arXiv</a>
  <a href="{esc(pdf_url)}" target="_blank" rel="noopener">PDF</a>
  <span class="paper-id">{esc(arxiv_id)}</span>
</div>
</article>"""


def render_featured(papers: list[dict]) -> str:
    if not papers:
        return '<p class="robo-empty">今日无新论文。<br/>arXiv 在北京时间周五、周六、周日不公布新 announcement，周一通常会一次性堆出两天量。</p>'
    items = [render_paper(p) for p in papers[:FEATURED_LIMIT]]
    return f'<div class="paper-list">\n' + "\n".join(items) + "\n</div>"


def render_rest(papers: list[dict]) -> str:
    rest = papers[FEATURED_LIMIT:]
    if not rest:
        return ""
    items = []
    for p in rest:
        conf = extract_conf(p.get("comment", ""))
        conf_html = f' <span class="conf">[{esc(conf)}]</span>' if conf else ""
        items.append(
            f'<li><a href="{esc(p.get("abs_url", "#"))}" target="_blank" rel="noopener">{esc(p.get("title", ""))}</a>{conf_html}</li>'
        )
    return f"""<details class="more">
<summary>其余 {len(rest)} 篇（折叠）</summary>
<ul>
{chr(10).join(items)}
</ul>
</details>"""


def render_archive(papers_dir: str, current_date: str) -> str:
    if not os.path.isdir(papers_dir):
        return '<p class="archive-empty">尚无历史归档</p>'
    files = sorted(glob.glob(os.path.join(papers_dir, "*.md")), reverse=True)
    items = []
    for f in files[:60]:
        date = os.path.splitext(os.path.basename(f))[0]
        if date == current_date:
            continue
        items.append(f'<a href="papers/{esc(date)}.md">{esc(date)}</a>')
    if not items:
        return '<p class="archive-empty">尚无历史归档</p>'
    return '<div class="archive-list">' + " · ".join(items) + "</div>"


def render_xml(payload: dict) -> str:
    papers = payload.get("papers", [])
    items = []
    for p in papers[:50]:
        items.append(
            f"""  <item>
    <title>{esc(p.get("title", ""))}</title>
    <link>{esc(p.get("abs_url", ""))}</link>
    <guid isPermaLink="false">{esc(p.get("arxiv_id", ""))}</guid>
    <pubDate>{esc(p.get("published", ""))}</pubDate>
    <description><![CDATA[{p.get("summary", "")}]]></description>
  </item>"""
        )
    last_build = payload.get("fetched_at", "")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>机器人文献 · Cenry</title>
  <link>https://cenrywang.github.io/robotics.html</link>
  <description>每日精选 arXiv 机器人论文（cs.RO + 副分类关键词命中）</description>
  <language>zh-CN</language>
  <lastBuildDate>{esc(last_build)}</lastBuildDate>
{chr(10).join(items)}
</channel>
</rss>
"""


def render_markdown(payload: dict) -> str:
    papers = payload.get("papers", [])
    lines: list[str] = []
    lines.append(f"# {payload.get('date', '')} 机器人文献")
    lines.append("")
    lines.append(f"共 {len(papers)} 篇（按相关度排序）")
    lines.append("")
    for p in papers:
        conf = extract_conf(p.get("comment", ""))
        conf_md = f" · **{conf}**" if conf else ""
        dirs = p.get("directions", [])
        dirs_md = f" · `{'` `'.join(dirs)}`" if dirs else ""
        quants = p.get("quant", [])
        quant_md = f" · {' / '.join(f'**{q}**' for q in quants)}" if quants else ""
        score = f" · score +{p.get('score', 0)}" if p.get("score", 0) > 0 else ""
        lines.append(
            f"## [{p.get('title', '')}]({p.get('abs_url', '')}){conf_md}{dirs_md}{quant_md}{score}"
        )
        lines.append("")
        lines.append(f"作者：{fmt_authors(p.get('authors', []))}  ")
        lines.append(
            f"arXiv: `{p.get('arxiv_id', '')}` · 分类 `{p.get('primary_category', '')}` · 发表 {p.get('published', '')[:10]}"
        )
        lines.append("")
        summary = p.get("summary", "").replace("\n", "\n> ")
        lines.append(f"> {summary}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: build_robotics.py <cache/robotics/YYYY-MM-DD.json> <out_dir>", file=sys.stderr)
        return 2
    src = sys.argv[1]
    out_dir = sys.argv[2]

    if not os.path.exists(src):
        print(f"source not found: {src}", file=sys.stderr)
        return 1
    with open(src, encoding="utf-8") as f:
        payload = json.load(f)

    papers = payload.get("papers", [])
    date_str = payload.get("date", datetime.date.today().isoformat())

    tz = datetime.timezone(datetime.timedelta(hours=8))
    now_str = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    body_parts: list[str] = []
    body_parts.append(f'<h2>今日精选 · {esc(date_str)}</h2>')
    body_parts.append(render_featured(papers))
    body_parts.append(render_rest(papers))
    body_parts.append("<h2>历史归档</h2>")
    papers_dir = os.path.join(out_dir, "papers") if os.path.isdir(os.path.join(out_dir, "papers")) else "papers"
    body_parts.append(render_archive(papers_dir, date_str))
    body = "\n".join(body_parts)

    meta = f"同步于 {now_str}（北京时间） · 命中 {len(papers)} 篇"
    page = PAGE.replace("__META__", meta).replace("__BODY__", body)

    html_path = os.path.join(out_dir, "robotics.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"{html_path} written ({len(papers)} papers)")

    xml_text = render_xml(payload)
    xml_path = os.path.join(out_dir, "robotics.xml")
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_text)
    print(f"{xml_path} written")

    md_text = render_markdown(payload)
    md_dir = os.path.join(out_dir, "papers")
    os.makedirs(md_dir, exist_ok=True)
    md_path = os.path.join(md_dir, f"{date_str}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"{md_path} written")

    return 0


if __name__ == "__main__":
    sys.exit(main())