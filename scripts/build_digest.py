# -*- coding: utf-8 -*-
"""把 garss 生成的 README.md 渲染成站点风格的 digest.html。

用法：python3 scripts/build_digest.py <garss README.md> <输出文件>
由 .github/workflows/sync-digest.yml 每日调用。页面直接复用站点根目录的
style.css（极光背景 / 玻璃卡片 / 导航），纯静态输出，不依赖 Jekyll。
"""
import datetime
import re
import sys

import markdown

# 源数据允许的最大年龄（天）。garss 每天 06:00 重新抓取，本工作流 07:30 同步，
# 正常情况下源数据不超过 1 天；超过这个阈值说明上游已停更或抓取失败，
# 此时必须让 workflow 变红，而不是把旧内容再渲染一遍发布出去。
MAX_SOURCE_AGE_DAYS = 3

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
    <p class="digest-meta">源数据 __SRC_TIME__ · 同步于 __TIME__（北京时间） · 每天 07:30 自动更新</p>
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


def main():
    if len(sys.argv) != 3:
        print("usage: build_digest.py <garss README.md> <output.html>", file=sys.stderr)
        return 2
    src, dst = sys.argv[1], sys.argv[2]

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

    now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    page = (
        PAGE.replace("__SRC_TIME__", src_time.strftime("%Y-%m-%d %H:%M"))
        .replace("__TIME__", now)
        .replace("__YEAR__", str(now[:4]))
        .replace("__BODY__", body)
    )

    with open(dst, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"{dst} written ({len(body)} chars of content)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
