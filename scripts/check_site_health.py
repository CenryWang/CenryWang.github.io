#!/usr/bin/env python3
"""站点健康自检（纯标准库，零依赖）。

检查线上页面可访问、简报与行情数据新鲜、已下线功能没有被手滑恢复。
任一项失败都以非零码退出，让 Actions 变红——绝不静默通过。

用法：python3 scripts/check_site_health.py [BASE_URL]
"""
import datetime
import json
import re
import sys
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://cenrywang.github.io").rstrip("/")

PAGES = [
    "/",
    "/info.html",
    "/tools.html",
    "/metals.html",
    "/whimsy.html",
    "/sitemap.html",
    "/data/metals.json",
    "/blog/index.html",
    "/blog/welcome.html",
    "/digest.html",
    "/merge-quest.html",
    "/404.html",
    "/script.js",
]

# 已下线功能：一旦重新出现在页面里就说明有人误覆盖了文件
FORBIDDEN = ["guestbook.html", "countapi.xyz", "giscus.app", "now.html"]

# 导航重构后，首页必须包含 4 个主板块入口与导航页入口
NAV_REQUIRED = ["info.html", "blog/index.html", "whimsy.html", "sitemap.html"]

# 这些页面都必须使用 nav.py 的同一套 4 项主导航（按标签比对）
NAV_CHECK_PAGES = [
    "/", "/info.html", "/tools.html", "/metals.html", "/whimsy.html",
    "/sitemap.html", "/blog/index.html", "/blog/welcome.html",
    "/digest.html", "/404.html",
]

# 这些页面属于某个主板块，左侧必须出现板块内目录
SIDEBAR_PAGES = [
    "/", "/info.html", "/tools.html", "/metals.html", "/whimsy.html",
    "/blog/index.html", "/blog/welcome.html", "/digest.html",
]

# 全站明暗主题：每个 HTML 页面都要有主题预加载 + 可切换的按钮。
# 普通页靠 script.js；merge-quest.html 是 Vite 单文件产物，靠自身内联脚本。
THEME_PAGES = [
    "/", "/info.html", "/tools.html", "/metals.html", "/whimsy.html",
    "/sitemap.html", "/blog/index.html", "/blog/welcome.html",
    "/digest.html", "/404.html", "/merge-quest.html",
]

# 导航页必须列出完整分支结构（防止改了 nav.py 却忘了重跑 build_sitemap.py）
SITEMAP_REQUIRED = [
    "首页", "信息", "博客", "奇思", "板块概览", "简报", "工具", "行情",
    "人生一万天", "合成大冒险", "AI大模型", "Coding工具", "常用框架",
    "常用工具软件", "学习科研", "设计绘图", "Agent Skills",
]

MAX_DIGEST_AGE_DAYS = 3
MAX_METALS_AGE_DAYS = 3

errors = []


def fetch(path):
    req = urllib.request.Request(
        BASE + path, headers={"User-Agent": "site-health-check/1.0"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        if resp.status != 200:
            raise RuntimeError("HTTP {}".format(resp.status))
        return resp.read().decode("utf-8", "replace")


def main():
    nav_labels = [None]  # 第一份导航作为基准，后面逐页比对
    for path in PAGES:
        try:
            text = fetch(path)
        except Exception as exc:
            errors.append("{} 不可访问：{}".format(path, exc))
            continue

        for bad in FORBIDDEN:
            if bad in text:
                errors.append("{} 仍包含已下线引用：{}".format(path, bad))

        if path == "/":
            for item in NAV_REQUIRED:
                if item not in text:
                    errors.append("首页导航缺少 {}".format(item))

        if path in NAV_CHECK_PAGES:
            nav = re.search(r'<nav class="nav">(.*?)</nav>', text, re.S)
            if not nav:
                errors.append("{} 缺少站点导航".format(path))
            else:
                labels = tuple(re.findall(r"<li><a[^>]*>([^<]+)</a>", nav.group(1)))
                if not labels:
                    errors.append("{} 导航没有入口".format(path))
                elif nav_labels[0] is None:
                    nav_labels[0] = labels
                elif labels != nav_labels[0]:
                    errors.append("{} 导航与其它页不一致：{}".format(path, " / ".join(labels)))

        if path in SIDEBAR_PAGES and 'class="board-sidebar"' not in text:
            errors.append("{} 缺少左侧板块目录".format(path))

        if path in THEME_PAGES:
            if 'localStorage.getItem("theme")' not in text:
                errors.append("{} 缺少明暗主题预加载".format(path))
            if path == "/merge-quest.html":
                if "mqThemeToggle" not in text or 'html[data-theme="dark"]' not in text:
                    errors.append("{} 缺少明暗主题接入（Vite 重建后容易丢）".format(path))
            elif "script.js" not in text or 'id="themeToggle"' not in text:
                errors.append("{} 缺少全站主题按钮或 script.js".format(path))

        if path == "/sitemap.html":
            for label in SITEMAP_REQUIRED:
                if label not in text:
                    errors.append("导航页缺少分支：{}".format(label))

        if path == "/digest.html":
            match = re.search(r"同步于\s*(\d{4}-\d{2}-\d{2})", text)
            if not match:
                errors.append("简报缺少同步时间，无法判断新鲜度")
            else:
                day = datetime.date.fromisoformat(match.group(1))
                age = (datetime.date.today() - day).days
                if age > MAX_DIGEST_AGE_DAYS:
                    errors.append("简报已 {} 天未更新（{}）".format(age, day))
                else:
                    print("digest 同步于 {}，{} 天前".format(day, age))

        if path == "/data/metals.json":
            try:
                data = json.loads(text)
                stamp = datetime.datetime.fromisoformat(
                    data["generated_at"].replace("Z", "+00:00")
                )
                age = (datetime.datetime.now(datetime.timezone.utc) - stamp).days
                if age > MAX_METALS_AGE_DAYS:
                    errors.append("行情数据已 {} 天未更新（{}）".format(age, data["generated_at"]))
                else:
                    print("metals 生成于 {}，{} 天前".format(data["generated_at"], age))
                if len(data.get("metrics", [])) < 6:
                    errors.append("行情数据指标数量异常：{}".format(len(data.get("metrics", []))))
            except Exception as exc:
                errors.append("行情数据格式或时间戳异常：{}".format(exc))

    if errors:
        print("FAIL：站点健康检查未通过", file=sys.stderr)
        for item in errors:
            print("  - " + item, file=sys.stderr)
        return 1
    print("OK：{} 个资源全部 200，简报与行情数据新鲜，无已下线功能残留".format(len(PAGES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
