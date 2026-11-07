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
    "/tools.html",
    "/metals.html",
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

# 导航统一后，首页必须包含这些入口
NAV_REQUIRED = ["tools.html", "digest.html", "metals.html", "blog/index.html"]

# 这些页面都必须使用 nav.py 的同一套入口（按标签比对，忽略 ../ 等路径前缀差异）
NAV_CHECK_PAGES = [
    "/", "/tools.html", "/metals.html", "/blog/index.html",
    "/blog/welcome.html", "/digest.html", "/404.html",
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
