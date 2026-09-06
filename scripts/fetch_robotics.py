# -*- coding: utf-8 -*-
"""抓取 arXiv 机器人方向论文，按方向 + 量化规模打标签，输出 cache/robotics/YYYY-MM-DD.json。

设计要点：
- 主分类 cs.RO 增量拉取近 48 小时；副分类 cs.LG / cs.CV / cs.AI 只挑机器人关键词命中的
- comment 字段正则提会议名（"Accepted at RSS / CoRL / ICRA ..."），命中即加权
- 领域方向标签：6 个具身子方向（VLA / WAM / HUMANOID / TACTILE / DATA-EVAL / AGENTIC），
  每方向有独立关键词白名单，论文可命中多个方向
- 量化标签：从 abstract / comment 正则提取数据规模（"X hours" / "X demos" / "X scenes" 等），
  归一显示为 240H / 60K DEMOS / 1.2M TRAJ
- arXiv API 限流 3 秒一次，单次最多 200 条，分页拉满；任一分类失败容错跳过
- 仅依赖 Python 标准库（urllib + xml.etree + re），无需安装第三方包
- 支持 SAMPLE 环境变量跳过抓取，便于本地反复调 build_robotics.py
"""
import datetime
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# ---- 配置 ----------------------------------------------------------------

PRIMARY_CAT = "cs.RO"
SECONDARY_CATS = ["cs.LG", "cs.CV", "cs.AI"]
INCREMENTAL_HOURS = 48
ARXIV_API_HTTP = "http://export.arxiv.org/api/query"
ARXIV_API_HTTPS = "https://export.arxiv.org/api/query"
PAGE_SIZE = 200
ARXIV_SLEEP_SECS = 3.5

# 6 个具身子方向 × 各自关键词白名单。
# 关键词大小写不敏感；论文可命中多个方向（不互斥）。
DIRECTIONS: dict[str, list[str]] = {
    "VLA": [
        "vision-language-action", "vision language action", "VLA",
        "OpenVLA", "RT-2", "Octo", "π0", "pi0", "pi-0",
        "diffusion policy", "behavior cloning", "action chunking",
        "end-to-end manipulation", "imitation learning",
        "manipulation policy", "teleoperation",
    ],
    "WAM": [
        "world model", "world action model", "WAM",
        "Dreamer", "DreamerV3", "GAIA",
        "predictive model", "dynamics model",
        "video prediction", "model-based RL",
        "latent action", "action-free pretraining",
        "inverse dynamics",
    ],
    "HUMANOID": [
        "humanoid", "bipedal", "quadruped", "legged locomotion",
        "Unitree", "Optimus", "Figure", "Atlas", "H1", "G1",
        "whole-body control", "locomotion", "gait", "balance",
        "MIT cheetah", "humanoid robot",
    ],
    "TACTILE": [
        "tactile", "tactile sensing", "tactile sensor",
        "vision-based tactile", "GelSight", "DIGIT",
        "in-hand manipulation", "in-hand",
        "force feedback", "force control",
        "tactile feedback", "dexterous manipulation",
        "soft gripper", "compliant manipulation",
        "grasping", "grasp",
    ],
    "DATA-EVAL": [
        "dataset", "benchmark", "simulator", "simulation",
        "Isaac Sim", "MuJoCo", "Habitat", "SAPIEN",
        "sim-to-real", "sim2real",
        "evaluation protocol", "eval suite",
        "data collection", "demonstration collection",
        "reproducibility", "open-source dataset",
        "pick-and-place",
    ],
    "AGENTIC": [
        "agentic robot", "agentic", "embodied agent",
        "LLM planner", "language planner",
        "high-level planning", "task planning",
        "Code-as-Policies", "CaP", "SayCan",
        "hierarchical policy", "long-horizon planning",
        "open-vocabulary", "language-conditioned policy",
        "PaLM-E", "LLM-based control",
        "foundation model planner",
    ],
}

# 副分类抓取时用：所有方向关键词的去重合并
ALL_ROBOT_KW = sorted({kw.lower() for kws in DIRECTIONS.values() for kw in kws})

# 会议白名单：comment 字段命中即加权（按引用价值排序）
CONFERENCE_BONUS = [
    ("Science Robotics", 8),
    ("Nature Machine Intelligence", 7),
    ("RSS", 7),
    ("CoRL", 7),
    ("T-RO", 6),
    ("TRO", 6),
    ("ICRA", 6),
    ("IROS", 6),
    ("RA-L", 5),
    ("RAL", 5),
    ("IJRR", 4),
    ("ICML", 3),
    ("NeurIPS", 3),
    ("CVPR", 2),
]

# ---- 量化标签提取 -------------------------------------------------------

_HOUR_RE = re.compile(
    r"([\d,]+(?:\.\d+)?)\s*([KkMmBb])?\s*(?:hours?|hrs?|h)\b", re.IGNORECASE
)
_DEMO_RE = re.compile(
    r"([\d,]+(?:\.\d+)?)\s*([KkMmBb])?\s*(?:demos?|demonstrations?|samples?)\b",
    re.IGNORECASE,
)
_TRAJ_RE = re.compile(
    r"([\d,]+(?:\.\d+)?)\s*([KkMmBb])?\s*(?:episodes?|rollouts?|trajectories?|trajs?)\b",
    re.IGNORECASE,
)
_SCENE_RE = re.compile(
    r"([\d,]+(?:\.\d+)?)\s*([KkMmBb])?\s*(?:scenes?|environments?|envs?)\b",
    re.IGNORECASE,
)
_TASK_RE = re.compile(
    r"([\d,]+(?:\.\d+)?)\s*([KkMmBb])?\s*(?:tasks?|objects?)\b", re.IGNORECASE
)

_QUANT_RULES = [
    (_HOUR_RE, "H", None),
    (_DEMO_RE, "DEMOS", None),
    (_TRAJ_RE, "TRAJ", None),
    (_SCENE_RE, "SCENES", None),
    (_TASK_RE, "TASKS", None),
]


def _to_num(value: str, mult: str | None) -> float:
    n = float(value.replace(",", ""))
    if not mult:
        return n
    m = mult.upper()
    if m == "K":
        return n * 1_000
    if m == "M":
        return n * 1_000_000
    if m == "B":
        return n * 1_000_000_000
    return n


def _fmt_num(n: float) -> str:
    if n < 1000:
        return f"{n:g}"
    if n < 1_000_000:
        s = f"{n / 1000:.1f}".rstrip("0").rstrip(".")
        return f"{s}K"
    s = f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".")
    return f"{s}M"


def extract_quant(text: str, max_tags: int = 2) -> list[str]:
    """从摘要 / comment 提数据规模标签。

    返回示例：['240H', '60K DEMOS']。最多 max_tags 个，避免噪音。
    同类只取首个（先 hours 再 demos/traj 再 scenes/tasks）。
    """
    if not text:
        return []
    found: list[str] = []
    seen: set[str] = set()
    for pattern, unit, _ in _QUANT_RULES:
        m = pattern.search(text)
        if not m:
            continue
        n = _to_num(m.group(1), m.group(2))
        if n <= 0:
            continue
        tag = f"{_fmt_num(n)} {unit}" if unit != "H" else f"{_fmt_num(n)}H"
        if tag in seen:
            continue
        seen.add(tag)
        found.append(tag)
        if len(found) >= max_tags:
            break
    return found


# ---- arXiv 抓取 --------------------------------------------------------

NS_ATOM = "http://www.w3.org/2005/Atom"
NS_ARXIV = "http://arxiv.org/schemas/atom"


def http_get(url: str, timeout: int = 60) -> bytes:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": "arxiv-robotics-daily/1.0"})
    last = None
    urls = [url]
    if url.startswith("http://"):
        urls.append(url.replace("http://", "https://", 1))
    for u in urls:
        try:
            with urllib.request.urlopen(u, timeout=timeout, context=ctx) as r:
                return r.read()
        except Exception as e:
            last = e
    raise RuntimeError(f"fetch failed: {url}: {last}")


def fetch_arxiv(query: str, start: int = 0, max_results: int = PAGE_SIZE) -> bytes:
    qs = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    return http_get(f"{ARXIV_API_HTTP}?{qs}")


def parse_entries(xml_bytes: bytes) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    out: list[dict] = []
    for e in root.iter(f"{{{NS_ATOM}}}entry"):
        id_url = (e.findtext(f"{{{NS_ATOM}}}id") or "").strip()
        tail = id_url.split("/")[-1].split("?")[0]
        m = re.match(r"(\d{4}\.\d{4,5})(v\d+)?", tail)
        arxiv_id = m.group(1) if m else tail
        title = re.sub(r"\s+", " ", (e.findtext(f"{{{NS_ATOM}}}title") or "").strip())
        summary = re.sub(r"\s+", " ", (e.findtext(f"{{{NS_ATOM}}}summary") or "").strip())
        published = (e.findtext(f"{{{NS_ATOM}}}published") or "").strip()
        updated = (e.findtext(f"{{{NS_ATOM}}}updated") or "").strip()
        comment_el = e.find(f"{{{NS_ARXIV}}}comment")
        comment = (comment_el.text or "").strip() if comment_el is not None else ""
        authors: list[str] = []
        for a in e.iter(f"{{{NS_ATOM}}}author"):
            name = (a.findtext(f"{{{NS_ATOM}}}name") or "").strip()
            if name:
                authors.append(name)
        cats: list[str] = []
        for c in e.iter(f"{{{NS_ATOM}}}category"):
            t = c.get("term")
            if t:
                cats.append(t)
        pc_el = e.find(f"{{{NS_ATOM}}}primary_category")
        primary = pc_el.get("term", "") if pc_el is not None else ""
        out.append(
            {
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": authors[:8],
                "summary": summary,
                "comment": comment,
                "primary_category": primary,
                "categories": cats,
                "published": published,
                "updated": updated,
                "abs_url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
            }
        )
    return out


def score_and_tag(
    text_lower: str, comment: str, comment_lower: str
) -> tuple[int, list[str], list[str], list[str]]:
    """返回 (score, score_reasons, directions, quant)。

    - directions：命中的领域方向列表（去重，按 DIRECTIONS 字典顺序）
    - quant：从 comment + text 提的量化标签
    """
    score = 0
    reasons: list[str] = []
    direction_hits: dict[str, str] = {}  # direction → first kw hit

    for direction, keywords in DIRECTIONS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                if direction not in direction_hits:
                    direction_hits[direction] = kw
                    score += 3
                    reasons.append(f"{direction}:{kw}")
                # 同方向多个词命中只加一次分（避免 WAM 论文里既有 video prediction 又有 dynamics model 拿双倍）
                break

    if comment_lower:
        for name, w in CONFERENCE_BONUS:
            if name.lower() in comment_lower:
                score += w
                reasons.append(f"conf:{name}(+{w})")
                break

    quant = extract_quant(text_lower if text_lower else "") + extract_quant(comment)
    # 去重并限 2 个
    seen: set[str] = set()
    quant_uniq: list[str] = []
    for q in quant:
        if q in seen:
            continue
        seen.add(q)
        quant_uniq.append(q)
        if len(quant_uniq) >= 2:
            break

    # direction 输出按 DIRECTIONS 字典顺序
    directions = [d for d in DIRECTIONS if d in direction_hits]
    return score, reasons, directions, quant_uniq


def fetch_category(cat: str, since_utc: datetime.datetime) -> list[dict]:
    """单分类增量抓：分页拉，按 published 过滤；遇 published < since 即停止。"""
    out: list[dict] = []
    for start in range(0, 800, PAGE_SIZE):
        try:
            xml = fetch_arxiv(f"cat:{cat}", start=start, max_results=PAGE_SIZE)
        except Exception as e:
            print(f"[{cat}] fetch failed at start={start}: {e}", file=sys.stderr)
            return out
        entries = parse_entries(xml)
        if not entries:
            break
        all_recent = True
        for ent in entries:
            pub = ent["published"][:19]
            try:
                pub_dt = datetime.datetime.strptime(pub, "%Y-%m-%dT%H:%M:%S").replace(
                    tzinfo=datetime.timezone.utc
                )
            except ValueError:
                continue
            if pub_dt >= since_utc:
                out.append(ent)
            else:
                all_recent = False
        if not all_recent or len(entries) < PAGE_SIZE:
            break
        time.sleep(ARXIV_SLEEP_SECS)
    return out


def main() -> int:
    out_dir = "cache/robotics"
    os.makedirs(out_dir, exist_ok=True)

    if os.environ.get("SAMPLE"):
        sample = os.path.join(out_dir, "_sample.json")
        if not os.path.exists(sample):
            print(f"sample missing: {sample}", file=sys.stderr)
            return 2
        print(f"sample mode: {sample} present, skip fetch")
        return 0

    tz8 = datetime.timezone(datetime.timedelta(hours=8))
    now_local = datetime.datetime.now(tz8)
    now_utc = now_local.astimezone(datetime.timezone.utc)
    since_utc = now_utc - datetime.timedelta(hours=INCREMENTAL_HOURS)
    date_str = now_local.strftime("%Y-%m-%d")

    seen: set[str] = set()
    all_entries: list[dict] = []

    main_entries = fetch_category(PRIMARY_CAT, since_utc)
    for e in main_entries:
        if e["arxiv_id"] not in seen:
            seen.add(e["arxiv_id"])
            all_entries.append(e)
    print(f"[{PRIMARY_CAT}] collected {len(main_entries)}", file=sys.stderr)

    for cat in SECONDARY_CATS:
        try:
            ents = fetch_category(cat, since_utc)
        except Exception as e:
            print(f"[{cat}] skipped: {e}", file=sys.stderr)
            continue
        kept = 0
        for ent in ents:
            if ent["arxiv_id"] in seen:
                continue
            text_lower = (ent["title"] + " " + ent["summary"]).lower()
            if any(kw in text_lower for kw in ALL_ROBOT_KW):
                seen.add(ent["arxiv_id"])
                all_entries.append(ent)
                kept += 1
        print(f"[{cat}] kept {kept} of {len(ents)}", file=sys.stderr)

    for e in all_entries:
        text = (e["title"] + " " + e["summary"]).lower()
        comment = e.get("comment", "")
        s, reasons, dirs, quant = score_and_tag(text, comment, comment.lower())
        e["score"] = s
        e["score_reasons"] = reasons
        e["directions"] = dirs
        e["quant"] = quant
    all_entries.sort(key=lambda e: (-e["score"], e["published"]), reverse=True)

    out_path = os.path.join(out_dir, f"{date_str}.json")
    payload = {
        "date": date_str,
        "fetched_at": now_local.isoformat(),
        "count": len(all_entries),
        "papers": all_entries,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"{out_path}: {len(all_entries)} papers written")
    return 0


if __name__ == "__main__":
    sys.exit(main())