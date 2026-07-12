"""六爻排盘引擎"""

from __future__ import annotations

import random
from typing import Any

from .constants import (
    BRANCH_ELEMENT,
    PALACE_ELEMENT,
    PALACE_GUA,
    PALACE_SHI_YAO,
    get_liuqin,
    ying_yao,
)

# 六兽 (按日干循环)
LIU_SHOU = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]


def _coin_toss() -> int:
    """三枚铜钱: 3正=老阳9, 2正=少阴8, 1正=少阳7, 0正=老阴6"""
    coins = [random.randint(0, 1) for _ in range(3)]
    heads = sum(coins)
    if heads == 3:
        return 9
    if heads == 2:
        return 8
    if heads == 1:
        return 7
    return 6


def _yao_to_text(value: int) -> str:
    if value == 9:
        return "○ 老阳"
    if value == 8:
        return "▅▅ 少阴"
    if value == 7:
        return "▅ 少阳"
    return "× 老阴"


def _yao_is_yang(value: int) -> bool:
    return value in (7, 9)


def _time_yao(year: int, month: int, day: int, hour: int) -> list[int]:
    """时间起卦: 年月日时各取余数成卦"""
    shang = (year + month + day) % 8 or 8
    xia = (year + month + day + hour) % 8 or 8
    shang_gua = [7 if _yao_is_yang(shang) and _yao_is_yang(shang) else 8 for _ in range(6)]
    xia_gua = [7 if _yao_is_yang(xia) and _yao_is_yang(xia) else 8 for _ in range(6)]
    return xia_gua + shang_gua


def _build_gua_from_yao(yao_list: list[int]) -> dict[str, Any]:
    """从六爻列表构建卦的对象, 含变卦和互卦"""
    ben_yao = yao_list[:6]

    # 上下卦判定 (3爻一组)
    xia_yao = tuple(1 if _yao_is_yang(y) else 0 for y in ben_yao[:3])
    shang_yao = tuple(1 if _yao_is_yang(y) else 0 for y in ben_yao[3:])

    # 变卦：老阳9→阴, 老阴6→阳
    bian_yao = [8 if y == 9 else (7 if y == 6 else y) for y in ben_yao]

    # 动爻位置 (0-based)
    dong_yao_idx = [i for i, y in enumerate(ben_yao) if y in (6, 9)]

    # 互卦: 234爻为下卦, 345爻为上卦
    hu_xia = tuple(1 if _yao_is_yang(y) else 0 for y in ben_yao[1:4])
    hu_shang = tuple(1 if _yao_is_yang(y) else 0 for y in ben_yao[2:5])

    # 查找本卦名
    gua_name = _find_gua_name(xia_yao, shang_yao)
    bian_name = _find_gua_name(
        tuple(1 if _yao_is_yang(y) else 0 for y in bian_yao[:3]),
        tuple(1 if _yao_is_yang(y) else 0 for y in bian_yao[3:]),
    )
    hu_name = _find_gua_name(hu_xia, hu_shang)

    # 查找宫位和世应
    palace, shi_pos = _find_palace_and_shi(gua_name)

    return {
        "gua_name": gua_name,
        "gua_bian": bian_name,
        "gua_hu": hu_name,
        "palace": palace,
        "palace_element": PALACE_ELEMENT.get(palace, ""),
        "ben_yao": ben_yao,
        "bian_yao": bian_yao,
        "dong_yao": dong_yao_idx,
        "shi_yao": shi_pos,
        "ying_yao": ying_yao(shi_pos),
        "yao_details": _build_yao_details(ben_yao, palace, shi_pos, dong_yao_idx),
    }


_GUA_NAME_CACHE: dict[tuple, str] = {}


def _find_gua_name(xia: tuple, shang: tuple) -> str:
    """根据上下卦查找卦名"""
    key = (xia, shang)
    if key in _GUA_NAME_CACHE:
        return _GUA_NAME_CACHE[key]

    # Fix: correct trigram mapping
    TRIGRAM = {
        (1, 1, 1): "乾",
        (1, 1, 0): "兑",
        (1, 0, 1): "离",
        (1, 0, 0): "震",
        (0, 1, 1): "巽",
        (0, 1, 0): "坎",
        (0, 0, 1): "艮",
        (0, 0, 0): "坤",
    }

    xia_name = TRIGRAM.get(xia, "?")
    shang_name = TRIGRAM.get(shang, "?")
    result = f"{shang_name}{xia_name}"
    _GUA_NAME_CACHE[key] = result
    return result


def _find_palace_and_shi(gua_name: str) -> tuple[str, int]:
    for palace, names in PALACE_GUA.items():
        if gua_name in names:
            idx = names.index(gua_name)
            return palace, PALACE_SHI_YAO[palace][idx]
    return "?", 0


def _build_yao_details(
    ben_yao: list[int],
    palace: str,
    shi_pos: int,
    dong_idx: list[int],
) -> list[dict[str, Any]]:
    """构建每爻的详细信息: 纳甲, 六亲, 六兽"""
    palace_wx = PALACE_ELEMENT.get(palace, "?")
    details = []
    for i, y in enumerate(ben_yao):
        pos = i + 1
        is_yang = _yao_is_yang(y)
        is_dong = i in dong_idx
        is_shi = pos == shi_pos
        is_ying = pos == ying_yao(shi_pos)

        # 纳甲
        stem, branch = _najia_for_line(gua_name="", pos=pos, is_yang=is_yang)

        # 六亲
        yao_wx = BRANCH_ELEMENT.get(branch, "?")
        liuqin = get_liuqin(palace_wx, yao_wx)

        details.append(
            {
                "position": pos,
                "value": y,
                "text": _yao_to_text(y),
                "is_yang": is_yang,
                "is_dong": is_dong,
                "is_shi": is_shi,
                "is_ying": is_ying,
                "najia_stem": stem,
                "najia_branch": branch,
                "najia": f"{stem}{branch}",
                "wuxing": yao_wx,
                "liuqin": liuqin,
            }
        )
    return details


def _najia_for_line(gua_name: str, pos: int, is_yang: bool) -> tuple[str, str]:
    """简化纳甲: 阳卦纳阳支, 阴卦纳阴支"""
    yang_stems = "甲丙戊庚壬"
    yin_stems = "乙丁己辛癸"
    yang_branches = ["子", "寅", "辰", "午", "申", "戌"]
    yin_branches = ["丑", "亥", "酉", "未", "巳", "卯"]

    idx = (pos - 1) % 6
    if is_yang:
        return (yang_stems[idx % 5], yang_branches[idx])
    return (yin_stems[idx], yin_branches[idx])


def cast_coins() -> dict[str, Any]:
    """铜钱起卦"""
    yao_list = [_coin_toss() for _ in range(6)]
    return _build_gua_from_yao(yao_list)


def cast_by_time(year: int, month: int, day: int, hour: int) -> dict[str, Any]:
    """时间起卦"""
    yao_list = _time_yao(year, month, day, hour)
    return _build_gua_from_yao(yao_list)


def get_gua_info(gua_name: str) -> dict[str, Any]:
    """获取指定卦的详细信息"""
    palace, shi_pos = _find_palace_and_shi(gua_name)
    return {
        "name": gua_name,
        "palace": palace,
        "palace_element": PALACE_ELEMENT.get(palace, ""),
        "shi_yao": shi_pos,
        "ying_yao": ying_yao(shi_pos),
    }
