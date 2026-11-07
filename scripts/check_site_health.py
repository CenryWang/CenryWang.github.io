#!/usr/bin/env python3
"""站点健康自检（纯标准库，零依赖）。

检查线上页面可访问、简报新鲜、已下线功能没有被手滑恢复。
任一项失败都以非零码退出，让 Actions 变红——绝不静默通过。

用法：python3 scripts/check_site_health.py [BASE_URL]
"""
import datetime
import re
import sys
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://cenrywang.github.io").rstrip("/")

PAGES = [
    "/",
    "/tools.html",
    "/now.html",
    "/blog/index.html",
    "/blog/welcome.html",
    "/digest.html",
    "/merge-quest.html",
    "/404.html",
    "/script.js",
]

# 已下线功能：一旦重新出现在页面里就说明有人误覆盖了文件
FORBIDDEN = ["guestbook.html", "countapi.xyz", "giscus.app"]

# 导航统一后，首页必须包含这些入口
NAV_REQUIRED = ["tools.html", "digest.html", "now.html", "blog/index.html"]

MAX_DIGEST_AGE_DAYS = 3

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

    if errors:
        print("FAIL：站点健康检查未通过", file=sys.stderr)
        for item in errors:
            print("  - " + item, file=sys.stderr)
        return 1
    print("OK：{} 个资源全部 200，简报新鲜，无已下线功能残留".format(len(PAGES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
