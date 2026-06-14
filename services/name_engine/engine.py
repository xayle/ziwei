"""
services/name_engine/engine.py — 姓名学分析引擎

实现五格数理（天/人/地/外/总格）+ 三才配置分析 + 改名字选建议。
数据来源：
  data/name_eighty_one.json  — 81数理吉凶表
  data/name_sancai.json      — 三才五行配置表
  data/name_chars.json       — 汉字笔画+五行数据库
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product as _iterproduct
import json
from pathlib import Path

# ── 数据加载 ──────────────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _load_json(filename: str):
    path = _DATA_DIR / filename
    # 用 utf-8-sig 自动剥离 BOM（Windows 环境下常见）
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except UnicodeDecodeError:
        with open(path, encoding="utf-8") as f:
            return json.load(f)


# 81数理：{draw(1-81): {draw, content, value, text}}
_EIGHTY_ONE: dict[int, dict] = {item["draw"]: item for item in _load_json("name_eighty_one.json")}

# 三才配置：{"木木木": {content, text, value}, ...}
_SANCAI: dict[str, dict] = _load_json("name_sancai.json")

# 汉字笔画+五行
_CHAR_STROKES: dict[str, int] = {}  # char → stroke count
_CHAR_ELEMENT: dict[str, str] = {}  # char → fiveEle (金木水火土)
for _entry in _load_json("name_chars.json"):
    _draw = _entry["draw"]
    _ele = _entry["fiveEle"]
    for _ch in _entry["chars"]:
        if _ch not in _CHAR_STROKES:  # 首次出现优先
            _CHAR_STROKES[_ch] = _draw
            _CHAR_ELEMENT[_ch] = _ele

# ── 笔画末位 → 五行映射 ────────────────────────────────────────────────────────
_DIGIT_TO_ELEMENT: dict[int, str] = {
    1: "木",
    2: "木",
    3: "火",
    4: "火",
    5: "土",
    6: "土",
    7: "金",
    8: "金",
    9: "水",
    0: "水",
}

# ── 建议用字候选池（按五行分组，笔画 5-13，每五行最多 50 字）────────────────────
_SUGGEST_POOL_MAX = 50  # 每五行最多候选字数
_VALID_ELEMENTS: frozenset[str] = frozenset({"木", "火", "土", "金", "水"})


def _build_suggest_pool() -> dict[str, list[str]]:
    """
    构建字选候选池。
    优先读取 data/name_suggest_chars.json（精选字库），
    若文件不存在则回退到从 name_chars.json 自动采样（笔画 5-13，每五行 ≤50 字）。
    """
    pool: dict[str, list[str]] = {e: [] for e in _VALID_ELEMENTS}
    seen: set[str] = set()

    # 尝试加载精选字库
    curated_path = _DATA_DIR / "name_suggest_chars.json"
    if curated_path.exists():
        curated = json.loads(curated_path.read_text(encoding="utf-8"))
        chars_by_ele: dict[str, str] = curated.get("chars_by_element", {})
        for ele, chars_str in chars_by_ele.items():
            if ele not in pool:
                continue
            for ch in chars_str:
                if ch not in seen and ch in _CHAR_STROKES:
                    seen.add(ch)
                    pool[ele].append(ch)
        # 如果精选库覆盖了 ≥3 个五行就直接返回
        non_empty = sum(1 for v in pool.values() if v)
        if non_empty >= 3:
            return pool

    # 回退：从 name_chars.json 自动采样（笔画 5-13，每五行 ≤50 字）
    for entry in _load_json("name_chars.json"):
        draw: int = entry["draw"]
        ele: str = entry["fiveEle"]
        if not (5 <= draw <= 13) or ele not in pool:
            continue
        bucket = pool[ele]
        if len(bucket) >= _SUGGEST_POOL_MAX:
            continue
        for ch in entry["chars"]:
            if ch in seen or ch not in _CHAR_STROKES:
                continue
            seen.add(ch)
            bucket.append(ch)
            if len(bucket) >= _SUGGEST_POOL_MAX:
                break
    return pool


_SUGGEST_POOL: dict[str, list[str]] = {}  # 延迟初始化，见模块末尾


# ── 数据类 ────────────────────────────────────────────────────────────────────


@dataclass
class GridInfo:
    """单格（天/人/地/外/总格）分析结果。"""

    number: int  # 格数（笔画数之和）
    element: str  # 对应五行（按末位规则）
    lucky: str  # 吉凶文字，如 "吉"/"凶"
    score: int  # 吉凶分值（1=极凶, 10=大吉）
    desc: str  # 数理释义


@dataclass
class SancaiInfo:
    """三才五行配置结果。"""

    pattern: str  # 三才组合，如 "木火土"
    lucky: str  # 吉凶，如 "大吉"/"凶多吉少"
    score: int  # 吉凶分值（1-10）
    desc: str  # 三才释义


@dataclass
class NameAnalysis:
    """完整姓名分析结果。"""

    surname: str
    given_name: str
    # 五格
    tianke: GridInfo  # 天格
    renke: GridInfo  # 人格
    dike: GridInfo  # 地格
    waike: GridInfo  # 外格
    zonge: GridInfo  # 总格
    # 三才
    sancai: SancaiInfo
    # 综合
    overall_score: int  # 综合评分 0-100
    summary: str  # 一句话摘要


@dataclass
class NameSuggestion:
    """改名建议单条结果。"""

    given_name: str  # 建议名（1-2字）
    overall_score: int  # 综合评分 0-100
    renke_score: int  # 人格吉凶分（1-10）
    sancai_score: int  # 三才吉凶分（1-10）
    sancai_pattern: str  # 三才五行组合，如 "金水木"
    element_composition: list[str] = field(default_factory=list)  # 各字五行
    summary: str = ""  # 一句话摘要


# ── 核心函数 ──────────────────────────────────────────────────────────────────


def get_stroke_count(char: str) -> int:
    """
    查汉字笔画数。
    未收录字回退到 Unicode CJK 区域粗估（每 700 个码点 +1 画，最小 1 画）。
    """
    if char in _CHAR_STROKES:
        return _CHAR_STROKES[char]
    cp = ord(char)
    if 0x4E00 <= cp <= 0x9FFF:
        return max(1, (cp - 0x4E00) // 700 + 1)
    return 1


def _num_to_element(n: int) -> str:
    """笔画数末位 → 五行。"""
    return _DIGIT_TO_ELEMENT[n % 10]


def _lookup_81(n: int) -> GridInfo:
    """查81数理表，自动处理超出范围（>81）的情况。"""
    if n <= 0:
        n = 1
    actual = n % 81
    if actual == 0:
        actual = 81
    info = _EIGHTY_ONE.get(actual, {"draw": actual, "content": "（未收录）", "value": 5, "text": "中性"})
    return GridInfo(
        number=n,
        element=_num_to_element(n),
        lucky=info["text"],
        score=info["value"],
        desc=info["content"],
    )


def calc_five_grids(surname: str, given_name: str) -> tuple[int, int, int, int, int]:
    """
    计算五格数字（天/人/地/外/总格）。

    规则：
      s = 姓字列表，n = 名字列表
      天格：单姓 = 姓笔画+1；复姓 = 姓所有字笔画之和
      人格：姓末字笔画 + 名首字笔画（无名字则 +1）
      地格：单名 = 名笔画+1；复名 = 名所有字笔画之和（无名字则 = 1）
      外格：天格 + 地格 - 人格（结果 ≤ 1 → 外格 = 1）
      总格：全名所有字笔画之和

    返回 (tianke, renke, dike, waike, zonge)
    """
    s = list(surname)
    n = list(given_name)
    s_strokes = [get_stroke_count(c) for c in s]
    n_strokes = [get_stroke_count(c) for c in n]

    # 天格
    if len(s) == 1:
        tianke = s_strokes[0] + 1
    else:
        tianke = sum(s_strokes)

    # 人格
    renke = (s_strokes[-1] if s_strokes else 1) + (n_strokes[0] if n_strokes else 1)

    # 地格
    if len(n) == 0:
        dike = 1
    elif len(n) == 1:
        dike = n_strokes[0] + 1
    else:
        dike = sum(n_strokes)

    # 外格
    waike = max(1, tianke + dike - renke)

    # 总格
    zonge = sum(s_strokes) + sum(n_strokes)

    return tianke, renke, dike, waike, zonge


def analyze_name(surname: str, given_name: str) -> NameAnalysis:
    """
    完整姓名学分析：五格数理 + 三才配置 + 综合评分。

    Parameters
    ----------
    surname   : 姓（1-3个汉字）
    given_name: 名（0-3个汉字）

    Returns
    -------
    NameAnalysis
    """
    if not surname:
        raise ValueError("surname 不能为空")

    t, r, d, w, z = calc_five_grids(surname, given_name)

    tianke = _lookup_81(t)
    renke = _lookup_81(r)
    dike = _lookup_81(d)
    waike = _lookup_81(w)
    zonge = _lookup_81(z)

    # 三才（天格→人格→地格五行）
    sancai_key = f"{tianke.element}{renke.element}{dike.element}"
    sc_info = _SANCAI.get(sancai_key, {"content": "（未收录）", "text": "中性", "value": 5})
    sancai = SancaiInfo(
        pattern=sancai_key,
        lucky=sc_info["text"],
        score=sc_info["value"],
        desc=sc_info["content"],
    )

    # 综合评分（0-100）：人格权重最高（30%），三才次之（20%），地格（20%），总格（10%），天/外格各（10%）
    overall_score = min(
        100,
        (
            tianke.score * 10
            + renke.score * 30
            + dike.score * 20
            + waike.score * 10
            + zonge.score * 10
            + sancai.score * 20
        )
        // 10,
    )

    # 摘要
    parts: list[str] = []
    if renke.score >= 8:
        parts.append(f"人格{renke.number}{renke.lucky}")
    elif renke.score <= 3:
        parts.append(f"人格{renke.number}{renke.lucky}")
    if sancai.score >= 8:
        parts.append(f"三才{sancai.pattern}{sancai.lucky}")
    elif sancai.score <= 3:
        parts.append(f"三才{sancai.pattern}{sancai.lucky}需关注")
    if not parts:
        parts.append(f"三才{sancai.pattern}，五格综合{zonge.lucky}")
    summary = "，".join(parts)

    return NameAnalysis(
        surname=surname,
        given_name=given_name,
        tianke=tianke,
        renke=renke,
        dike=dike,
        waike=waike,
        zonge=zonge,
        sancai=sancai,
        overall_score=overall_score,
        summary=summary,
    )


# ── 改名建议 ──────────────────────────────────────────────────────────────────


def suggest_names(
    surname: str,
    name_length: int = 2,
    preferred_elements: list[str] | None = None,
    top_n: int = 10,
    min_score: int = 60,
) -> tuple[list[NameSuggestion], int]:
    """
    改名字选建议：在候选字库中穷举组合，返回评分最高的 top_n 个名字。

    Parameters
    ----------
    surname            : 姓（固定不变）
    name_length        : 名字字数，1 或 2
    preferred_elements : 希望包含的五行列表，如 ["水","木"]
                         可从八字用神/喜神分析结果传入；None 表示不限。
    top_n              : 返回建议数量（1-20）
    min_score          : 最低综合评分过滤（0-100），低于此分的名字不返回

    Returns
    -------
    (suggestions, total_candidates_evaluated)
      suggestions — NameSuggestion 列表，按 overall_score 降序
      total_candidates_evaluated — 评估过的候选组合总数（含被 min_score 过滤掉的）
    """
    if not surname:
        raise ValueError("surname 不能为空")
    if name_length not in (1, 2):
        raise ValueError("name_length 必须为 1 或 2")
    top_n = max(1, min(top_n, 20))

    # 确定候选字池
    wanted: list[str] = []
    if preferred_elements:
        valid_pref = [e for e in preferred_elements if e in _VALID_ELEMENTS]
        for ele in valid_pref:
            wanted.extend(_SUGGEST_POOL.get(ele, []))
    if not wanted:
        # 无偏好 → 使用全部五行池
        for ele in sorted(_VALID_ELEMENTS):
            wanted.extend(_SUGGEST_POOL.get(ele, []))

    # 去重，保持顺序
    seen_chars: set[str] = set()
    pool_chars: list[str] = []
    for ch in wanted:
        if ch not in seen_chars:
            seen_chars.add(ch)
            pool_chars.append(ch)

    # 生成候选名
    if name_length == 1:
        candidates: list[tuple[str, ...]] = [(ch,) for ch in pool_chars]
    else:
        candidates = list(_iterproduct(pool_chars, pool_chars))

    # 评分并排序
    results: list[NameSuggestion] = []
    total_evaluated = len(candidates)
    for chars in candidates:
        given = "".join(chars)
        try:
            analysis = analyze_name(surname, given)
        except Exception:
            continue
        if analysis.overall_score < min_score:
            continue
        results.append(
            NameSuggestion(
                given_name=given,
                overall_score=analysis.overall_score,
                renke_score=analysis.renke.score,
                sancai_score=analysis.sancai.score,
                sancai_pattern=analysis.sancai.pattern,
                element_composition=[_CHAR_ELEMENT.get(ch, "?") for ch in given],
                summary=analysis.summary,
            )
        )

    # 按综合分 → 人格分+三才分 降序
    results.sort(
        key=lambda x: (x.overall_score, x.renke_score + x.sancai_score),
        reverse=True,
    )
    return results[:top_n], total_evaluated


# ── 候选池延迟初始化（依赖 _CHAR_STROKES 已就绪）──────────────────────────────
_SUGGEST_POOL = _build_suggest_pool()
