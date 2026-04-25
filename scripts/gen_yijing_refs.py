"""
scripts/gen_yijing_refs.py
从 data/classics_yijing.json 生成 classic_refs.py 格式的易经引文条目，
直接追加写入 services/bazi_engine/classic_refs.py。

用法：
    python scripts/gen_yijing_refs.py           # 追加到 classic_refs.py
    python scripts/gen_yijing_refs.py --dry-run  # 仅打印，不写入
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "classics_yijing.json"
CLASSIC_REFS_FILE = Path(__file__).parent.parent / "services" / "bazi_engine" / "classic_refs.py"

# 命理相关的重点卦：额外提取名句爻辞
FEATURED_YAOCI: dict[int, list[tuple[str, str, list[str]]]] = {
    # {卦号: [(爻位关键词, 引文文本, 额外tags), ...]}
    1: [  # 乾
        ("初九", "潛龍勿用。陽在下也，時機未至，蓄勢待發。", ["大运", "蛰伏"]),
        ("九五", "飛龍在天，利見大人。君子大有為也。", ["大运", "旺运", "用神"]),
        ("上九", "亢龍有悔，盈不可久也。", ["格局", "物极必反"]),
    ],
    2: [  # 坤
        ("初六", "履霜堅冰至。陰始凝也，漸積而至。", ["五行", "阴"]),
        ("六五", "黃裳元吉。文在中也，柔順居中。", ["格局", "阴柔"]),
    ],
    11: [  # 泰
        ("彖辞", "天地交而萬物通也，上下交而其志同也。", ["格局", "五行", "通达"]),
    ],
    12: [  # 否
        ("彖辞", "天地不交而萬物不通也，上下不交而天下無邦也。", ["格局", "阻滞"]),
    ],
    29: [  # 坎
        ("象辞", "水洊至，習坎；君子以常德行，習教事。", ["五行", "水"]),
    ],
    30: [  # 离
        ("象辞", "明兩作，離；大人以繼明照于四方。", ["五行", "火"]),
    ],
    63: [  # 既济
        ("象辞", "水在火上，既濟；君子以思患而豫防之。", ["格局", "完成", "防患"]),
        ("初九", "曳其輪，濡其尾，无咎。善始者未必善終，慎终如始。", ["大运", "谨慎"]),
    ],
    64: [  # 未济
        ("象辞", "火在水上，未濟；君子以慎辨物居方。", ["格局", "未完", "谨慎"]),
        ("上九", "有孚于飲酒，无咎；濡其首，有孚失是。", ["大运", "节制"]),
    ],
}

# 卦名与命理标签的映射
HEXAGRAM_TAGS: dict[int, list[str]] = {
    1:  ["乾", "阳", "刚健", "格局"],
    2:  ["坤", "阴", "柔顺", "格局"],
    11: ["泰", "通达", "五行"],
    12: ["否", "阻滞", "五行"],
    13: ["同人", "人际", "通论"],
    14: ["大有", "丰收", "通论"],
    17: ["随", "顺势", "大运"],
    18: ["蛊", ["整治", "通论"]],
    24: ["复", "回归", "大运"],
    25: ["无妄", "诚信", "通论"],
    29: ["坎", "水", "五行", "险境"],
    30: ["离", "火", "五行", "光明"],
    41: ["损", "减损", "用神"],
    42: ["益", "增益", "用神"],
    47: ["困", "困境", "大运"],
    48: ["井", "滋养", "通论"],
    55: ["丰", "丰盛", "大运"],
    56: ["旅", "漂泊", "命局"],
    63: ["既济", "完成", "格局"],
    64: ["未济", "未完", "格局"],
}


def flatten_tags(tags_val) -> list[str]:
    """将 tags 中可能嵌套的 list 展平"""
    result = []
    for t in tags_val:
        if isinstance(t, list):
            result.extend(t)
        else:
            result.append(t)
    return result


def generate_refs(hexagrams: list[dict]) -> list[dict]:
    refs = []
    idx = 1

    for h in hexagrams:
        num = h["number"]
        name = h["name"]
        # 繁体转为显示名（保留原始繁体，引文原汁原味；source用繁体，tag用简体）
        # 卦辞 + 象辞合并为主引文
        hexci = h.get("hexagram_ci", "").strip()
        xiangci = h.get("xiang_ci", "").strip()
        if hexci and xiangci:
            text = f"{hexci}象曰：{xiangci}"
        elif hexci:
            text = hexci
        elif xiangci:
            text = xiangci
        else:
            continue  # 无内容跳过

        # 去除末尾多余标点重复
        text = text.strip("。").strip() + "。"

        extra_tags = flatten_tags(HEXAGRAM_TAGS.get(num, []))
        base_tags = ["易经", name] + [t for t in extra_tags if t not in ("易经", name)]

        refs.append({
            "id": f"yijing_{idx:03d}",
            "source": f"《易经·{name}卦》",
            "text": text,
            "category": "通论",
            "tags": base_tags,
        })
        idx += 1

        # 重点卦额外爻辞引文
        for yao_pos, yao_text, extra in FEATURED_YAOCI.get(num, []):
            refs.append({
                "id": f"yijing_{idx:03d}",
                "source": f"《易经·{name}卦·{yao_pos}》",
                "text": yao_text,
                "category": extra[0] if extra else "通论",
                "tags": ["易经", name] + extra,
            })
            idx += 1

    return refs


def format_ref_py(r: dict) -> str:
    tags_repr = repr(r["tags"])
    return (
        f'    {{\n'
        f'        "id": "{r["id"]}",\n'
        f'        "source": "{r["source"]}",\n'
        f'        "text": "{r["text"]}",\n'
        f'        "category": "{r["category"]}",\n'
        f'        "tags": {tags_repr},\n'
        f'    }},'
    )


def main():
    dry_run = "--dry-run" in sys.argv

    if not DATA_FILE.exists():
        print(f"ERROR: 找不到 {DATA_FILE}，请先运行 build_yijing_json.py", file=sys.stderr)
        sys.exit(1)

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    hexagrams = data["hexagrams"]
    refs = generate_refs(hexagrams)

    print(f"生成 {len(refs)} 条易经引文")
    print(f"  其中基础卦辞条目：{sum(1 for r in refs if '·' not in r['source'][4:-1] or r['source'].count('·') == 1)} 条")
    print(f"  其中名句爻辞条目：{sum(1 for r in refs if r['source'].count('·') >= 2)} 条")

    if dry_run:
        print("\n--- DRY RUN 输出 ---")
        for r in refs[:5]:
            print(format_ref_py(r))
        print(f"  ... 共 {len(refs)} 条")
        return

    # 追加到 classic_refs.py
    existing = CLASSIC_REFS_FILE.read_text(encoding="utf-8")

    # 检查是否已有易经分区
    if "yijing_001" in existing:
        print("WARNING: classic_refs.py 已含 yijing_001，跳过追加（避免重复）")
        print("  若需重新生成，请先手动删除 classic_refs.py 中的易经分区。")
        return

    # 找到 CLASSIC_REFS 列表的末尾闭合位置（最后一个 ]）
    # 在闭合 ] 前插入新条目
    section_header = (
        "\n    # ── 易经 (yijing_001~{last}) "
        "────────────────────────────────────────────────────\n"
    ).format(last=f"yijing_{len(refs):03d}")

    entries_str = section_header
    for r in refs:
        entries_str += format_ref_py(r) + "\n"

    # 在文件末尾 ] 前插入
    insert_pos = existing.rfind("]")
    if insert_pos == -1:
        print("ERROR: 找不到 CLASSIC_REFS 列表结束标记 ]", file=sys.stderr)
        sys.exit(1)

    new_content = existing[:insert_pos] + entries_str + existing[insert_pos:]
    CLASSIC_REFS_FILE.write_text(new_content, encoding="utf-8")

    print(f"\n[OK] 已追加 {len(refs)} 条到 {CLASSIC_REFS_FILE}")

    # 验证
    import importlib.util
    spec = importlib.util.spec_from_file_location("classic_refs", CLASSIC_REFS_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    count = len(mod.CLASSIC_REFS)
    print(f"   验证：CLASSIC_REFS 现有 {count} 条")


if __name__ == "__main__":
    main()
