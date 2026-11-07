#!/usr/bin/env python3
"""贵金属与宏观行情数据构建（纯标准库，零依赖、零密钥、零费用）。

用法：python3 scripts/build_metals.py [--out data/metals.json]

数据源（全部免费、无需注册）：
  - gold-api.com            XAU / XAG 现货（USD/oz），只用于「今日值」
  - World Bank Pink Sheet   黄金 / 白银月度均价（1960 起，CC BY 4.0，需署名）
  - FRED DGS10              10 年期美债收益率（日频，1962 起）
  - FRED DTWEXBGS           美联储广义贸易加权美元指数（日频，2006 起）

设计原则：
  1. 所有指标统一降采样为月度序列（保留最近 30 年），曲线与区间变化
     完全基于同一条序列，绝不把「今日现货价」和「历史月均价」混算涨跌幅。
  2. 10 年期美债是利率，变化用基点（bp）表示，不套用百分比涨跌幅。
  3. 美元指数是贸易加权口径、且仅 2006 年起有数据；30 年窗口如实留空。
  4. 任一源失败、为空、时间戳过期都直接 exit 1，让 Actions 变红，
     绝不静默发布空页或反复重发旧数据。

World Bank 的 xlsx 下载链接每月轮换，因此先从官方页面解析当前链接，
不硬编码文档 ID。
"""
import argparse
import datetime
import hashlib
import io
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 仅本地调试用：指定目录后 fetch 会优先读该目录里的响应副本。
# 生产 workflow 不传此参数，始终实时抓取；时间戳校验依旧生效，旧缓存会报错。
CACHE_DIR = None

WB_PAGE = "https://www.worldbank.org/en/research/commodity-markets"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
SPOT_API = "https://api.gold-api.com/price/{}"

# 环境代理优先（FRED / gold-api / 世界银行页面走它更稳），失败再试直连
# （本机代理会挡 thedocs.worldbank.org，xlsx 必须直连才能下）
DEFAULT = urllib.request.build_opener()
DIRECT = urllib.request.build_opener(urllib.request.ProxyHandler({}))

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

WINDOWS = [
    ("1m", "1月", 1),
    ("3m", "3月", 3),
    ("1y", "1年", 12),
    ("3y", "3年", 36),
    ("10y", "10年", 120),
    ("30y", "30年", 360),
]

MAX_SPOT_AGE_DAYS = 3
MAX_FRED_AGE_DAYS = 14
MAX_WB_AGE_DAYS = 60


def cache_name(url):
    if "fredgraph.csv?id=" in url:
        return "fred_" + url.split("id=")[-1] + ".csv"
    if "api.gold-api.com/price/" in url:
        return "spot_" + url.rsplit("/", 1)[-1] + ".json"
    if url.endswith("commodity-markets"):
        return "wb_page.html"
    if "CMO-Historical-Data-Monthly" in url:
        return "wb_monthly.xlsx"
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16] + ".bin"


def fetch(url, timeout=15, direct_first=False, attempts=2, ua=None):
    path = os.path.join(CACHE_DIR, cache_name(url)) if CACHE_DIR else None
    if path and os.path.exists(path):
        with open(path, "rb") as handle:
            return handle.read()

    last = None
    openers = (DIRECT, DEFAULT) if direct_first else (DEFAULT, DIRECT)
    for opener in openers:
        for _ in range(attempts):
            # FRED / gold-api 用 urllib 默认 UA（带 Mozilla UA 会被本机代理挂起）；
            # World Bank 页面与 xlsx 反过来要求浏览器 UA，否则返回 403。
            headers = {"User-Agent": ua} if ua else {}
            req = urllib.request.Request(url, headers=headers)
            try:
                with opener.open(req, timeout=timeout) as resp:
                    if resp.status != 200:
                        raise RuntimeError("HTTP {}".format(resp.status))
                    data = resp.read()
                    if path and data:
                        os.makedirs(CACHE_DIR, exist_ok=True)
                        with open(path, "wb") as handle:
                            handle.write(data)
                    return data
            except Exception as exc:  # noqa: BLE001 - 所有通道与重试都失败才算失败
                last = exc
    raise RuntimeError("抓取失败 {}：{}".format(url, last))


def parse_iso(ts):
    return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))


def days_since(dt):
    now = datetime.datetime.now(datetime.timezone.utc)
    return (now - dt).days


def month_index(ym):
    year, month = (int(x) for x in ym.split("-"))
    return year * 12 + month - 1


def shift_month(ym, delta):
    idx = month_index(ym) - delta
    return "{:04d}-{:02d}".format(idx // 12, idx % 12 + 1)


def month_end_date(ym):
    year, month = (int(x) for x in ym.split("-"))
    nxt = datetime.date(year + 1, 1, 1) if month == 12 else datetime.date(year, month + 1, 1)
    return nxt - datetime.timedelta(days=1)


def fred_series(series_id):
    raw = fetch(FRED_CSV.format(series_id)).decode("utf-8", "replace")
    out = []
    for line in raw.splitlines()[1:]:
        parts = line.split(",", 1)
        if len(parts) != 2:
            continue
        day, value = parts[0].strip(), parts[1].strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", day) or value in ("", "."):
            continue
        try:
            out.append((day, float(value)))
        except ValueError:
            continue
    if len(out) < 12:
        raise RuntimeError("FRED {} 数据点过少：{}".format(series_id, len(out)))
    age = (datetime.date.today() - datetime.date.fromisoformat(out[-1][0])).days
    if age > MAX_FRED_AGE_DAYS:
        raise RuntimeError("FRED {} 最后观测 {} 已过期 {} 天".format(series_id, out[-1][0], age))
    return out


def to_monthly(daily):
    """日频序列取每月最后一个观测，统一成 [[YYYY-MM, value], ...]。"""
    by_month = {}
    for day, value in daily:
        by_month[day[:7]] = value
    return sorted(by_month.items())


def wb_xlsx_url():
    page = fetch(WB_PAGE, ua="Mozilla/5.0").decode("utf-8", "replace")
    match = re.search(
        r"https://thedocs\.worldbank\.org/[^\"'\s]+CMO-Historical-Data-Monthly\.xlsx", page
    )
    if not match:
        raise RuntimeError("世界银行页面未找到月度价格 xlsx 链接（可能改版）")
    return match.group(0).replace("&amp;", "&")


def wb_prices(url, raw=None):
    """用标准库解析 xlsx 的 Monthly Prices 表，返回 [(YYYY-MM, gold, silver, gsr), url]。"""
    # thedocs.worldbank.org 在本机环境必须直连，且 CDN 偶发 20s+ 延迟
    if raw is None:
        raw = fetch(url, timeout=60, direct_first=True, ua="Mozilla/5.0")
    z = zipfile.ZipFile(io.BytesIO(raw))

    strings = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(NS + "si"):
            strings.append("".join(t.text or "" for t in si.iter(NS + "t")))

    relmap = {}
    for rel in ET.fromstring(z.read("xl/_rels/workbook.xml.rels")):
        relmap[rel.get("Id")] = rel.get("Target")

    sheet_path = None
    for sheet in ET.fromstring(z.read("xl/workbook.xml")).iter(NS + "sheet"):
        if sheet.get("name") == "Monthly Prices":
            target = relmap.get(sheet.get(RID), "")
            sheet_path = target.lstrip("/") if target.startswith("/") else "xl/" + target
    if not sheet_path or sheet_path not in z.namelist():
        raise RuntimeError("xlsx 中找不到 Monthly Prices 工作表")

    rows = []
    for row in ET.fromstring(z.read(sheet_path)).iter(NS + "row"):
        cells = {}
        for cell in row.iter(NS + "c"):
            col = re.match(r"[A-Z]+", cell.get("r"))
            if not col:
                continue
            node = cell.find(NS + "v")
            value = node.text if node is not None else None
            if cell.get("t") == "s" and value is not None:
                value = strings[int(value)]
            elif cell.get("t") == "inlineStr":
                inline = cell.find(NS + "is")
                value = "".join(t.text or "" for t in inline.iter(NS + "t")) if inline is not None else None
            cells[col.group()] = value
        rows.append(cells)

    gold_col = silver_col = None
    for cells in rows[:10]:
        for col, value in cells.items():
            if value == "Gold":
                gold_col = col
            elif value == "Silver":
                silver_col = col
    if not gold_col or not silver_col:
        raise RuntimeError("xlsx 表头缺少 Gold / Silver 列（格式可能已变）")

    out = []
    for cells in rows:
        match = re.match(r"^(\d{4})M(\d{2})$", str(cells.get("A", "")))
        if not match:
            continue
        try:
            gold = float(cells[gold_col])
            silver = float(cells[silver_col])
        except (KeyError, TypeError, ValueError):
            continue
        if gold <= 0 or silver <= 0:
            continue
        out.append(("{}-{}".format(match.group(1), match.group(2)), gold, silver, gold / silver))

    if len(out) < 360:
        raise RuntimeError("世界银行月度数据不足 30 年：{} 行".format(len(out)))
    latest = out[-1][0]
    age = (datetime.date.today() - month_end_date(latest)).days
    if age > MAX_WB_AGE_DAYS:
        raise RuntimeError("世界银行月度数据停在 {}，已过期 {} 天".format(latest, age))
    return out, url


def spot(symbol):
    data = json.loads(fetch(SPOT_API.format(symbol)).decode("utf-8"))
    price = float(data["price"])
    stamp = parse_iso(data["updatedAt"])
    if price <= 0:
        raise RuntimeError("{} 现货价异常：{}".format(symbol, price))
    if days_since(stamp) > MAX_SPOT_AGE_DAYS:
        raise RuntimeError("{} 现货时间戳过期：{}".format(symbol, data["updatedAt"]))
    return price, data["updatedAt"]


def changes_from(series, change_unit):
    """基于同一条月度序列算各窗口变化；窗口超出序列范围则留 None。"""
    latest_ym, latest_value = series[-1]
    result = {}
    for key, _label, months in WINDOWS:
        target = shift_month(latest_ym, months)
        candidates = [value for ym, value in series if ym <= target]
        if not candidates:
            result[key] = None
            continue
        anchor = candidates[-1]
        if change_unit == "bp":
            result[key] = round((latest_value - anchor) * 100, 1)
        else:
            result[key] = round((latest_value / anchor - 1) * 100, 2) if anchor else None
    return result


def make_metric(key, name, unit, basis, now, now_source, now_time, series, change_unit, note):
    cutoff = shift_month(series[-1][0], 360)
    trimmed = [[ym, round(value, 4)] for ym, value in series if cutoff <= ym <= series[-1][0]]
    return {
        "key": key,
        "name": name,
        "unit": unit,
        "basis": basis,
        "now": round(now, 4),
        "now_source": now_source,
        "now_time": now_time,
        "change_unit": change_unit,
        "changes": changes_from(series, change_unit),
        "series": trimmed,
        "series_from": trimmed[0][0],
        "series_to": trimmed[-1][0],
        "note": note,
    }


def main():
    global CACHE_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(ROOT, "data", "metals.json"))
    parser.add_argument("--wb-file", help="本地已有的 Pink Sheet xlsx，跳过下载（离线调试用）")
    parser.add_argument("--cache-dir", help="本地调试用响应缓存目录（生产环境不要传）")
    args = parser.parse_args()
    CACHE_DIR = args.cache_dir

    try:
        gold_spot, gold_time = spot("XAU")
        silver_spot, silver_time = spot("XAG")
        if args.wb_file:
            with open(args.wb_file, "rb") as handle:
                wb_raw = handle.read()
            wb_url = WB_PAGE
        else:
            wb_raw = None
            wb_url = wb_xlsx_url()
        wb_rows, wb_url = wb_prices(wb_url, wb_raw)
        dgs10 = to_monthly(fred_series("DGS10"))
        twd = to_monthly(fred_series("DTWEXBGS"))
    except Exception as exc:  # noqa: BLE001 - 任何源失败都必须让工作流变红
        print("FAIL：数据抓取或校验失败 —— {}".format(exc), file=sys.stderr)
        return 1

    gold_series = [(ym, g) for ym, g, _s, _r in wb_rows]
    silver_series = [(ym, s) for ym, _g, s, _r in wb_rows]
    gsr_series = [(ym, r) for ym, _g, _s, r in wb_rows]

    metrics = [
        make_metric(
            "gold", "黄金", "USD/oz", "月均价 · World Bank",
            gold_spot, "gold-api.com 现货 XAU", gold_time, gold_series, "%",
            "今日值为现货；区间变化与曲线基于世界银行月度均价，两者口径不同，不混用。",
        ),
        make_metric(
            "silver", "白银", "USD/oz", "月均价 · World Bank",
            silver_spot, "gold-api.com 现货 XAG", silver_time, silver_series, "%",
            "今日值为现货；区间变化与曲线基于世界银行月度均价，两者口径不同，不混用。",
        ),
        make_metric(
            "gsr", "金银比", "倍", "月均金价 ÷ 月均银价",
            gold_spot / silver_spot, "由 XAU/XAG 现货价计算", gold_time, gsr_series, "%",
            "金价除以银价；今日值与历史值各自使用同源、同口径的价格计算。",
        ),
        make_metric(
            "us10y", "10 年期美债收益率", "%", "月末观测 · FRED DGS10",
            dgs10[-1][1], "FRED DGS10 最新月内观测", dgs10[-1][0] + " (月内最后观测)",
            dgs10, "bp",
            "利率不是价格，变化以基点 (bp) 表示，不使用百分比涨跌幅。",
        ),
        make_metric(
            "dxy", "美元指数（贸易加权）", "指数点", "月末观测 · FRED DTWEXBGS",
            twd[-1][1], "FRED DTWEXBGS 最新月内观测", twd[-1][0] + " (月内最后观测)",
            twd, "%",
            "美联储广义贸易加权美元指数，**不是 ICE 的 DXY**；该序列自 2006 年起，30 年窗口无数据。",
        ),
    ]

    payload = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "windows": [{"key": k, "label": lab, "months": m} for k, lab, m in WINDOWS],
        "metrics": metrics,
        "sources": [
            {"name": "gold-api.com", "role": "黄金 / 白银现货今日值", "url": "https://api.gold-api.com/", "license": "公开免费接口"},
            {"name": "World Bank Commodity Markets \"Pink Sheet\"", "role": "金银月度均价长周期序列", "url": wb_url, "license": "CC BY 4.0，需署名"},
            {"name": "FRED · DGS10", "role": "10 年期美债收益率", "url": FRED_CSV.format("DGS10"), "license": "美国政府公开数据"},
            {"name": "FRED · DTWEXBGS", "role": "广义贸易加权美元指数", "url": FRED_CSV.format("DTWEXBGS"), "license": "美国政府公开数据"},
        ],
        "caveats": [
            "所有指标统一为月度序列（最近 30 年）；1 月 / 3 月等短周期为月度参考值，不是日频收盘涨跌幅。",
            "世界银行月度均价每月更新一次，页面显示的「今日值」为另一来源的现货价，二者口径不同、不混算。",
            "美元指数采用美联储广义贸易加权口径，非 ICE DXY；该序列始于 2006 年，30 年数据不可用。",
            "金银比在同一时点、同一口径内由金价除以银价得到。",
            "公开来源的数据可能延迟、修订或存在误差，不保证实时、准确、完整，也不构成任何交易报价。",
            "历史涨跌幅与走势曲线仅描述过去，不代表未来表现。",
        ],
        "disclaimer": "本页仅展示公开宏观与行情数据，仅供信息参考，不构成任何投资建议、分析预测、买卖信号或收益承诺。数据可能延迟或存在误差，历史表现不代表未来表现。贵金属价格、利率与汇率波动剧烈，投资有风险，据此操作的风险与后果由读者自行承担。",
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")

    for metric in metrics:
        print("{:<18} now={:<12} 序列 {} → {} ({} 点) 变化={}".format(
            metric["name"], metric["now"], metric["series_from"], metric["series_to"],
            len(metric["series"]), metric["changes"]))
    print("OK：已写入 {}（{} 字节）".format(args.out, os.path.getsize(args.out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
