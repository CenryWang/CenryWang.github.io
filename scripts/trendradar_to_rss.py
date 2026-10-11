# -*- coding: utf-8 -*-
"""TrendRadar SQLite -> RSS 2.0 适配器（运行在你的轻量服务器上）。

背景：TrendRadar 把热榜存进 SQLite（output/{type}/{date}.db），并不对外发 RSS。
本脚本把最新一份 db 里的 news_items 转成标准 RSS 2.0，供 GitHub Actions 上的
build_digest.py 像订阅 AIHOT 一样把热搜合并进「每日简报」。

两种用法：
  1) 写文件（配合宝塔面板网站目录，由 Web 服务器托管）：
     python trendradar_to_rss.py --dir "D:/TrendRadar/output/news" --out "C:/www/trendradar/rss.xml"
  2) 起一个极轻量的本地 HTTP 服务，实时读 db 并带 token 鉴权（推荐，无需落盘）：
     python trendradar_to_rss.py --dir "D:/TrendRadar/output/news" --serve --port 8088 --token YOUR_SECRET

本文件只依赖 Python 标准库（sqlite3 / http.server / xml），在 2GB 的 Windows
轻量服务器上零额外依赖，配合 Task Scheduler 定时跑即可。

调试：--inspect 打印库的表结构与行数，方便首次部署时确认列名/数据。
"""
import argparse
import datetime
import html
import os
import sqlite3
import sys

try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import urlparse, parse_qs
    _HTTP_OK = True
except Exception:  # pragma: no cover
    _HTTP_OK = False

# 时区：TrendRadar 默认用服务器本地时间（通常为北京时间）
TZ = datetime.timezone(datetime.timedelta(hours=8))


def parse_dt(s):
    """尽量宽容地解析 TrendRadar 存的 TEXT 时间，返回带时区 datetime；失败返回 None。"""
    if not s:
        return None
    s = s.strip()
    try:
        dt = datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        return dt
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s, fmt).replace(tzinfo=TZ)
        except Exception:
            continue
    return None


def _esc(s):
    return html.escape(str(s or ""), quote=True)


def find_latest_db(directory):
    """在 output/{type}/ 目录下找最新修改的 .db 文件（返回绝对路径或 None）。"""
    best, best_t = None, 0
    if not os.path.isdir(directory):
        return None
    for root, _dirs, files in os.walk(directory):
        for fn in files:
            if fn.endswith(".db"):
                p = os.path.join(root, fn)
                try:
                    t = os.path.getmtime(p)
                except OSError:
                    continue
                if t > best_t:
                    best, best_t = p, t
    return best


def db_to_rss(db_path, limit=30, days=2, site_title="热搜雷达 · TrendRadar",
              site_link="https://aihot.news/"):
    """读取一份 TrendRadar SQLite，返回 RSS 2.0 字符串。任何异常都抛出让调用方处理。"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            SELECT n.title AS title, n.url AS url, n.mobile_url AS mobile_url,
                   n.rank AS rank, n.last_crawl_time AS crawl_time,
                   p.name AS platform
            FROM news_items n
            LEFT JOIN platforms p ON n.platform_id = p.id
            WHERE n.url <> '' OR n.mobile_url <> ''
            ORDER BY n.last_crawl_time DESC, n.rank ASC
            """
        )
        now = datetime.datetime.now(TZ)
        cutoff = now - datetime.timedelta(days=days)
        seen, items = set(), []
        for row in cur:
            link = row["url"] or row["mobile_url"] or ""
            if not link:
                continue
            dt = parse_dt(row["crawl_time"])
            if dt is None or dt < cutoff:
                continue
            if link in seen:
                continue
            seen.add(link)
            items.append({
                "title": row["title"] or "",
                "link": link,
                "platform": row["platform"] or "未知平台",
                "rank": row["rank"] if row["rank"] is not None else 0,
                "date": dt,
            })
            if len(items) >= limit:
                break
    finally:
        conn.close()

    if not items:
        items = []

    def rfc822(dt):
        return datetime.datetime.strftime(dt.astimezone(TZ), "%a, %d %b %Y %H:%M:%S %z")

    body = []
    for it in items:
        desc = f"#{it['rank']} · {_esc(it['platform'])}"
        body.append(
            "    <item>\n"
            f"      <title>{_esc(it['title'])}</title>\n"
            f"      <link>{_esc(it['link'])}</link>\n"
            f"      <guid isPermaLink=\"false\">{_esc(it['link'])}</guid>\n"
            f"      <category>{_esc(it['platform'])}</category>\n"
            f"      <description>{desc}</description>\n"
            f"      <pubDate>{rfc822(it['date'])}</pubDate>\n"
            "    </item>"
        )

    built = datetime.datetime.now(TZ)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        f"    <title>{_esc(site_title)}</title>\n"
        f"    <link>{_esc(site_link)}</link>\n"
        f"    <description>来自轻量服务器 TrendRadar 的实时热搜聚合</description>\n"
        f"    <lastBuildDate>{rfc822(built)}</lastBuildDate>\n"
        f"    <generator>TrendRadar-to-RSS adapter</generator>\n"
        + "\n".join(body)
        + "\n  </channel>\n</rss>\n"
    )


def inspect(db_path):
    conn = sqlite3.connect(db_path)
    try:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        print(f"DB: {db_path}\nTables: {tables}")
        for t in tables:
            try:
                n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t})")]
                print(f"  - {t}: {n} 行 | 列: {cols}")
            except Exception as e:
                print(f"  - {t}: 读取失败 {e}")
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description="TrendRadar SQLite -> RSS 适配器")
    ap.add_argument("--db", help="指定单个 .db 文件（优先于 --dir）")
    ap.add_argument("--dir", help="output/{type} 目录，自动选最新 .db")
    ap.add_argument("--out", help="输出 RSS 文件路径（写文件模式）")
    ap.add_argument("--limit", type=int, default=30, help="最多条目数（默认 30）")
    ap.add_argument("--days", type=int, default=2, help="只取最近 N 天抓取到的条目（默认 2）")
    ap.add_argument("--site-title", default="热搜雷达 · TrendRadar")
    ap.add_argument("--site-link", default="https://aihot.news/")
    ap.add_argument("--inspect", action="store_true", help="打印库结构后退出")
    ap.add_argument("--serve", action="store_true", help="起 HTTP 服务实时生成 RSS")
    ap.add_argument("--port", type=int, default=8088)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--token", default="", help="--serve 时的访问令牌（URL ?token=）")
    args = ap.parse_args()

    db = args.db or find_latest_db(args.dir or "")
    if not db or not os.path.isfile(db):
        print(f"ERROR: 找不到可用的 TrendRadar db（--db={args.db} --dir={args.dir}）", file=sys.stderr)
        return 2
    if args.inspect:
        inspect(db)
        return 0

    if args.serve:
        if not _HTTP_OK:
            print("ERROR: 当前环境不支持 http.server", file=sys.stderr)
            return 2
        return _serve(db, args)

    # 默认：写文件
    out = args.out
    if not out:
        print("ERROR: 非 --serve 模式需要 --out 指定输出文件", file=sys.stderr)
        return 2
    rss = db_to_rss(db, limit=args.limit, days=args.days,
                    site_title=args.site_title, site_link=args.site_link)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"RSS 已写出: {out} ({len(rss)} bytes)")
    return 0


def _serve(db, args):
    source_db = db
    token = args.token

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, payload):
            self.send_response(code)
            self.send_header("Content-Type", "application/rss+xml; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path not in ("/rss.xml", "/", "/feed.xml"):
                self._send(404, b"not found")
                return
            if token:
                got = parse_qs(parsed.query).get("token", [""])[0]
                if not got or not _const_eq(got, token):
                    self._send(403, b"forbidden")
                    return
            try:
                rss = db_to_rss(source_db, limit=args.limit, days=args.days,
                                site_title=args.site_title, site_link=args.site_link).encode("utf-8")
                self._send(200, rss)
            except Exception as e:  # 读库失败：500，让 GA 侧优雅跳过
                self._send(500, f"db error: {e}".encode("utf-8"))

        def log_message(self, *a):  # 静默常规日志
            pass

    print(f"Serving TrendRadar RSS at http://{args.host}:{args.port}/rss.xml"
          + (f" (token required)" if token else ""))
    HTTPServer((args.host, args.port), Handler).serve_forever()


def _const_eq(a, b):
    """简单等长比较，避免明显时序侧信道（非密码学级）。"""
    if len(a) != len(b):
        return False
    return a == b


if __name__ == "__main__":
    sys.exit(main())
