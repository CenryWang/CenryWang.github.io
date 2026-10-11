# -*- coding: utf-8 -*-
"""把 garss 生成的 README.md 渲染成站点风格的 digest.html。

用法：python3 scripts/build_digest.py <garss README.md> <输出文件> [--feed "标题|URL|备注"]...
由 .github/workflows/sync-digest.yml 每日调用。页面直接复用站点根目录的
style.css（极光背景 / 玻璃卡片 / 导航），纯静态输出，不依赖 Jekyll。

附加源（可选，可重复 --feed）：
  --feed "AIHOT 精选 · 数字生命卡兹克|https://aihot.news/feed.xml"
  --feed "热搜雷达 · TrendRadar|https://你的服务器/rss.xml?token=xxx|来自你的轻量服务器 TrendRadar"
每个 --feed 作为一个独立区块合并进简报，解析/渲染/上限/转义逻辑通用。
附加源一律「优雅降级」：抓取失败或疑似停更时只跳过该区块并告警，
绝不连累 garss 主源（不会像当年 robotics 那样静默发空内容）。
兼容旧用法：第 3 个位置参数若为 URL，仍当作 AIHOT feed。
设置环境变量 DIGEST_INSECURE=1 可跳过 RSS 源 HTTPS 证书校验（仅自签证书时临时用）。
"""
import datetime
import html
import os
import re
import ssl
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import markdown

# 自签证书兜底（仅当 DIGEST_INSECURE=1）
_SSL_CTX = ssl._create_unverified_context() if os.environ.get("DIGEST_INSECURE", "").lower() in ("1", "true") else None

# 源数据允许的最大年龄（天）。garss 每天 06:00 重新抓取，本工作流 07:30 同步，
# 正常情况下源数据不超过 1 天；超过这个阈值说明上游已停更或抓取失败，
# 此时必须让 workflow 变红，而不是把旧内容再渲染一遍发布出去。
MAX_SOURCE_AGE_DAYS = 3

# ---- 附加源通用参数 ----
FEED_RECENT_DAYS = 3      # 取最近 N 天内的条目
FEED_MIN_ITEMS = 8        # 近 N 天不足此数时，退回到最新 N 条
FEED_FALLBACK_N = 15
FEED_MAX_ITEMS = 20       # 单页最多展示条数，避免页面过长
FEED_STALE_DAYS = 7       # 最新条目超过此天数，视为停更，整块跳过
# 按域名给附加源一句说明（省去每次 --feed 都写备注）
DOMAIN_NOTES = {
    "aihot.news": '来自 <a href="https://aihot.news/" target="_blank" rel="noopener">AIHOT</a>'
                  '（卡兹克做的 AI 资讯聚合站）的近期精选，自动同步自其 RSS；原始内容版权归原作者所有。',
}

# garss README 头部形如：
#   > 精选 RSS 订阅聚合 · 已收录 20 个源 · 生成时间 2026-10-06 10:04:40 · ...
_SRC_TIME_RE = re.compile(
    r"生成时间\s+(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?"
)

PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>每日简报 · Cenry</title>
<meta name="description" content="RSS 聚合每日简报，GitHub Actions 自动更新" />
<link rel="stylesheet" href="style.css" />
<style>
  .digest-shell { max-width: 1080px; }
  .digest-meta { text-align: center; color: var(--muted); font-size: 0.95rem; margin: -18px 0 30px; }
  .digest-meta a { color: var(--accent1); text-decoration: none; }
  .digest-meta a:hover { text-decoration: underline; }
  .digest-body h2 { margin: 44px 0 16px; font-size: 1.35rem; }
  .digest-body h2::after {
    content: ""; display: block; width: 44px; height: 3px; margin-top: 8px;
    background: linear-gradient(90deg, var(--accent1), var(--accent2)); border-radius: 2px;
  }
  .digest-body p { color: var(--muted); font-size: 0.95rem; }
  .table-wrap { overflow-x: auto; border: 1px solid var(--glass-border); border-radius: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.9rem; min-width: 660px; }
  th {
    text-align: left; color: var(--muted); font-size: 0.78rem; letter-spacing: 1px;
    padding: 12px 14px; border-bottom: 1px solid var(--glass-border); white-space: nowrap;
  }
  td { padding: 10px 14px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255, 255, 255, 0.02); }
  td a, td a:visited { color: var(--accent1); text-decoration: none; }
  td a:hover { text-decoration: underline; }
  td img { width: 22px; height: 22px; border-radius: 5px; vertical-align: middle; }
  .digest-footer { text-align: center; color: var(--muted); font-size: 0.85rem; margin-top: 50px; }
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
      <li><a href="/">首页</a></li>
      <li><a href="digest.html">简报</a></li>
      <li><a href="merge-quest.html">游戏</a></li>
    </ul>
  </nav>

  <section class="section digest-shell">
    <h2 class="section-title">每日简报</h2>
    <p class="digest-meta">源数据 __SRC_TIME__ · 同步于 __TIME__（北京时间） · 每天 07:30 自动更新__FEED_NOTES__</p>
    <div class="glass digest-body">
__BODY__
    </div>
  </section>

  <footer class="digest-footer">© __YEAR__ CenryWang · 内容来自 RSS 订阅源，GitHub Actions 自动生成</footer>

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


def parse_source_time(text):
    """从 garss README 头部提取「生成时间」，返回带时区的 datetime；失败返回 None。"""
    tz = datetime.timezone(datetime.timedelta(hours=8))
    m = _SRC_TIME_RE.search(text)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    hh = int(m.group(4) or 0)
    mm = int(m.group(5) or 0)
    ss = int(m.group(6) or 0)
    try:
        return datetime.datetime(y, mo, d, hh, mm, ss, tzinfo=tz)
    except ValueError:
        return None


def parse_rfc822(s):
    """解析 RSS 的 RFC822 时间（如 'Sat, 10 Oct 2026 21:30:36 GMT'）→ 带时区 datetime。"""
    if not s:
        return None
    try:
        dt = parsedate_to_datetime(s)
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        return None


def fetch_feed(url, timeout=20):
    """抓取并解析任意 RSS 2.0 feed，返回按时间倒序的条目列表；任何失败返回 None。"""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; CenryDigest/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
            data = resp.read()
        root = ET.fromstring(data)
        items = []
        for it in root.iter("item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            if not title or not link:
                continue
            items.append({
                "title": title,
                "link": link,
                "category": (it.findtext("category") or "").strip(),
                "author": (it.findtext("author") or "").strip(),
                "date": parse_rfc822(it.findtext("pubDate") or ""),
                # guid 用于内部去重
                "guid": (it.findtext("guid") or link).strip(),
            })
        # 按时间倒序；无日期的排最后
        items.sort(
            key=lambda x: x["date"] or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc),
            reverse=True,
        )
        return items
    except Exception as e:  # 网络/解析异常：返回 None，由调用方决定降级
        print(f"WARN fetch_feed: {e}", file=sys.stderr)
        return None


def render_feed_section(title, items, note):
    """把一份附加源条目渲染成「日期/分类/标题/来源」表格区块。返回 (html, 展示条数)。"""
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz)

    # 停更保护：最新条目过旧，整块跳过（避免展示过时内容却看似实时）
    if items and items[0]["date"]:
        age_newest = now - items[0]["date"].astimezone(tz)
        if age_newest > datetime.timedelta(days=FEED_STALE_DAYS):
            print(
                f"WARN: 附加源「{title}」最新条目已 {age_newest.days} 天，疑似停更，跳过该区块",
                file=sys.stderr,
            )
            return "", 0

    # 内部去重（按 guid/link）
    seen, deduped = set(), []
    for i in items:
        key = i["guid"] or i["link"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(i)

    recent = [
        i for i in deduped
        if i["date"] and (now - i["date"].astimezone(tz)) <= datetime.timedelta(days=FEED_RECENT_DAYS)
    ]
    if len(recent) < FEED_MIN_ITEMS:
        recent = deduped[:FEED_FALLBACK_N]
    recent = recent[:FEED_MAX_ITEMS]
    if not recent:
        return "", 0

    rows = []
    for i in recent:
        d = i["date"].astimezone(tz).strftime("%Y-%m-%d") if i["date"] else ""
        title_txt = html.escape(i["title"])
        link = html.escape(i["link"])
        cat = html.escape(i["category"] or "—")
        author = html.escape(i["author"] or i["category"] or "—")
        rows.append(
            f'<tr><td>{d}</td><td>{cat}</td>'
            f'<td><a href="{link}" target="_blank" rel="noopener">{title_txt}</a></td>'
            f'<td>{author}</td></tr>'
        )

    sec = (
        f'<h2>{html.escape(title)}</h2>'
        f'<p>{note}</p>'
        '<div class="table-wrap"><table>'
        '<thead><tr><th>日期</th><th>分类</th><th>标题</th><th>来源</th></tr></thead>'
        '<tbody>' + "".join(rows) + '</tbody></table></div>'
    )
    return sec, len(recent)


def strip_rownum_column(body):
    """去掉 garss 表格里无意义的「编号」列（K001 等内部源 ID，且经常跳号不连续）。

    只在 garss 主体上调用——AIHOT 区块在调用本函数之后才拼接，不受影响。
    """
    # 表头：删除「编号」那一格
    body = body.replace('<th>编号</th>', '')
    # 表体：只删除每个 <tr> 后紧跟的「源编码」格（形如 K001 / B003 的 字母+数字）。
    # 用 [A-Z]\\d{2,4} 精确匹配，避免误删首格为纯中文名称的行。
    body = re.sub(r'(<tr>\s*)<td>[A-Z]\d{2,4}</td>', r'\1', body)
    return body


def _parse_cli(argv):
    """解析参数：前两个为位置参数（源 / 输出），其余支持 --feed "标题|URL|备注?" 与 --insecure。"""
    positional, feeds = [], []
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--feed":
            feeds.append(argv[i + 1]); i += 2
        elif a.startswith("--feed="):
            feeds.append(a[len("--feed="):]); i += 1
        elif a == "--insecure":
            os.environ["DIGEST_INSECURE"] = "1"; i += 1
        else:
            positional.append(a); i += 1
    return positional, feeds


def _build_feeds(positional, feeds_raw):
    """汇总附加源列表：兼容旧用法（第 3 个位置参数为 AIHOT URL），并合并 --feed。"""
    feeds = []
    if len(positional) >= 3 and positional[2].startswith("http"):
        feeds.append(("AIHOT 精选 · 数字生命卡兹克", positional[2], None))
    for spec in feeds_raw:
        parts = spec.split("|", 2)
        if len(parts) < 2 or not parts[1].strip():
            print(f"WARN: 跳过无效 --feed 规格: {spec}", file=sys.stderr)
            continue
        title, url = parts[0].strip(), parts[1].strip()
        note = parts[2].strip() if len(parts) == 3 else None
        feeds.append((title, url, note))
    return feeds


def _note_for(title, url, note):
    """确定附加源说明文字：显式备注优先，否则按域名匹配，最后给通用说明。"""
    if note:
        return html.escape(note)
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower()
    except Exception:
        host = ""
    for domain, txt in DOMAIN_NOTES.items():
        if domain in host:
            return txt
    return (f'来源：<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(host or url)}</a>'
            '，自动同步自其 RSS；内容版权归各平台与作者所有。')


def main():
    positional, feeds_raw = _parse_cli(sys.argv)
    if len(positional) < 2:
        print("usage: build_digest.py <garss README.md> <output.html> [--feed \"标题|URL|备注\"]...", file=sys.stderr)
        return 2
    src, dst = positional[0], positional[1]

    with open(src, encoding="utf-8") as f:
        text = f.read()

    # 新鲜度校验：源数据缺失时间标记或已过期，直接失败退出。
    # 这里绝不能静默降级——否则上游停更时会一直把旧日报当新内容发布出去，
    # 页面上看起来「一切正常」，实际已经停摆（robotics 功能就是这么死的）。
    tz = datetime.timezone(datetime.timedelta(hours=8))
    src_time = parse_source_time(text)
    if src_time is None:
        print(
            f"ERROR: 源 README 里找不到「生成时间」标记，上游格式可能已变化：{src}",
            file=sys.stderr,
        )
        return 1
    age = datetime.datetime.now(tz) - src_time
    if age > datetime.timedelta(days=MAX_SOURCE_AGE_DAYS):
        print(
            f"ERROR: 源数据已过期 {age.days} 天（生成于 {src_time:%Y-%m-%d %H:%M}，"
            f"阈值 {MAX_SOURCE_AGE_DAYS} 天），上游 garss 可能已停更",
            file=sys.stderr,
        )
        return 1

    # 去掉源文件首行 H1（页面已有自己的标题），避免重复
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    # 丢弃抓取失败的占位行。上游 garss 对反爬源（36氪 / 美团技术团队）以及
    # 内网 RSSHub 源（订阅地址形如 http://rsshub:1200/...，Actions runner 上
    # 永远解析不了）都会输出「暂无法通过爬虫获取信息, 点击进入源网站主页」，
    # 这类行只有占位价值，直接整行剔除；将来上游修好某个源后它会自动回来。
    lines = [ln for ln in lines if "暂无法通过爬虫获取信息" not in ln]
    text = "\n".join(lines).strip()

    body = markdown.markdown(text, extensions=["tables"])
    # 表格外包一层滚动容器，窄屏横向滑动不撑破布局
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace(
        "</table>", "</table></div>"
    )
    # 去掉 garss 表格里无意义的「编号」列（K001 等内部源 ID，且经常跳号不连续）
    body = strip_rownum_column(body)

    # ---- 附加源区块（AIHOT / TrendRadar 等，互不影响、各自优雅降级） ----
    feed_notes = ""
    feeds = _build_feeds(positional, feeds_raw)
    for title, url, note in feeds:
        items = fetch_feed(url)
        if items is None:
            print(f"WARN: 附加源「{title}」feed 拉取/解析失败，跳过该区块（garss 简报正常生成）", file=sys.stderr)
            continue
        section, count = render_feed_section(title, items, _note_for(title, url, note))
        if count:
            body += section
            feed_notes += f" · {html.escape(title)} {count} 条"
        else:
            print(f"WARN: 附加源「{title}」无可用条目，跳过该区块", file=sys.stderr)

    now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    page = (
        PAGE.replace("__SRC_TIME__", src_time.strftime("%Y-%m-%d %H:%M"))
        .replace("__TIME__", now)
        .replace("__YEAR__", str(now[:4]))
        .replace("__FEED_NOTES__", feed_notes)
        .replace("__BODY__", body)
    )

    with open(dst, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"{dst} written ({len(body)} chars of content)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
