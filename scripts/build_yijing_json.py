"""
scripts/build_yijing_json.py
从 zhouyi-main/docs/ 解析 64 卦 Markdown，生成 data/classics_yijing.json

用法：
    python scripts/build_yijing_json.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ZHOUYI_DOCS = Path(r"D:\Users\Administrator\Desktop\留存\玄天\zhouyi-main\docs")
OUTPUT = Path(__file__).parent.parent / "data" / "classics_yijing.json"


def parse_hexagram_dir(dirpath: Path) -> dict:
    """解析单个卦的目录（NN.XXX/index.md）"""
    # 从目录名提取编号和全称: e.g. "01.乾为天" -> (1, "乾为天")
    dirname = dirpath.name  # e.g. "01.乾为天"
    m = re.match(r"(\d+)\.(.*)", dirname)
    if not m:
        raise ValueError(f"目录名格式异常: {dirname}")
    number = int(m.group(1))
    full_name_raw = m.group(2)  # e.g. "乾为天"

    md_file = dirpath / "index.md"
    if not md_file.exists():
        raise FileNotFoundError(f"缺少 index.md: {dirpath}")

    text = md_file.read_text(encoding="utf-8")
    lines = text.splitlines()

    # 提取卦名（从 H1 标题）: "# 第一卦：乾卦（乾為天）"
    name = ""
    full_name = full_name_raw
    for line in lines:
        h1 = re.match(r"^# .+：(.+?)卦", line)
        if h1:
            name = h1.group(1)
            break
    if not name:
        # fallback: 取第一个汉字序列
        name = re.sub(r"[（(].+", "", full_name_raw).strip()

    # 提取卦辞：紧跟在 "**卦名。**" 或 "**卦名：**" 的那行内容
    # 格式: "**益。** 利有攸往，利涉大川。"
    hexagram_ci = ""
    for line in lines:
        stripped = line.strip()
        # 匹配 **X。** 或 **X：** 开头（支持繁简）
        m2 = re.match(r"^\*\*[^*]+[。：]\*\*\s*(.+)", stripped)
        if m2 and not hexagram_ci:
            hexagram_ci = m2.group(1).strip()
            break

    # 提取象曰
    xiang_ci = ""
    for line in lines:
        m3 = re.match(r"^象曰[：:](.+)", line.strip())
        if m3:
            xiang_ci = m3.group(1).strip()
            break

    # 提取爻辞（六条）
    # 格式: "**初九。** 潛龍勿用。" 或 "**初九爻辭**" 小节下的 "**初九。** ..."
    yaoci = []
    # 策略：找所有 "**NN。**" 或 "**NN：**" 加粗行（爻辞行通常在爻辞小节内）
    # 爻位前缀模式
    yao_prefix = re.compile(
        r"^\*\*(初[六九]|[二三四五]([六九])|上[六九])[。：\s。]\*\*\s*(.*)"
    )
    # 也处理: "**九二。** 見龍在田，利見大人。"
    yao_prefix2 = re.compile(
        r"^\*\*([初上][六九一二三四五]|[六九][二三四五])[。：]?\*\*\s*(.*)"
    )

    seen_yao = set()
    for line in lines:
        stripped = line.strip()
        m4 = yao_prefix.match(stripped)
        if m4:
            pos = m4.group(1)
            content = m4.group(3).strip()
            if pos not in seen_yao and content:
                yaoci.append(f"{pos}：{content}")
                seen_yao.add(pos)
            continue
        m5 = yao_prefix2.match(stripped)
        if m5:
            pos = m5.group(1)
            content = m5.group(2).strip()
            if pos not in seen_yao and content:
                yaoci.append(f"{pos}：{content}")
                seen_yao.add(pos)

    # fallback：若爻辞为空，尝试从 "**XX爻辞**" 小节下的加粗内容提取
    if not yaoci:
        in_yao_section = False
        for line in lines:
            stripped = line.strip()
            if re.search(r"爻[辭辞]", stripped) and stripped.startswith("**"):
                in_yao_section = True
                continue
            if in_yao_section and stripped.startswith("**") and stripped.endswith("**"):
                content = stripped.strip("*").strip()
                if content:
                    yaoci.append(content)
                    if len(yaoci) >= 6:
                        break

    return {
        "number": number,
        "name": name,
        "full_name": full_name,
        "hexagram_ci": hexagram_ci,
        "xiang_ci": xiang_ci,
        "yaoci": yaoci[:6],  # 最多6条
    }


def build_all() -> list[dict]:
    if not ZHOUYI_DOCS.exists():
        print(f"ERROR: 找不到源目录 {ZHOUYI_DOCS}", file=sys.stderr)
        sys.exit(1)

    hexagrams = []
    errors = []

    # 遍历 NN.XXX 格式的子目录
    subdirs = sorted(
        [d for d in ZHOUYI_DOCS.iterdir() if d.is_dir() and re.match(r"\d+\.", d.name)],
        key=lambda d: int(re.match(r"(\d+)\.", d.name).group(1))
    )

    print(f"发现 {len(subdirs)} 个卦目录")

    for d in subdirs:
        try:
            h = parse_hexagram_dir(d)
            hexagrams.append(h)
            yao_count = len(h["yaoci"])
            status = "[OK]" if yao_count >= 6 else f"[WARN] yaoci={yao_count}"
            print(f"  {h['number']:2d}. {h['name']} ({h['full_name']}) {status}")
        except Exception as e:
            errors.append((d.name, str(e)))
            print(f"  [ERR] {d.name}: {e}")

    if errors:
        print(f"\n警告：{len(errors)} 个卦解析有误")
    print(f"\n共解析 {len(hexagrams)} 卦")
    return hexagrams


def main():
    hexagrams = build_all()

    output_data = {
        "title": "易经（周易）六十四卦",
        "source": "zhouyi-main (本地)",
        "total": len(hexagrams),
        "hexagrams": hexagrams,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[DONE] 已写入 {OUTPUT}")
    print(f"   总卦数：{len(hexagrams)}")

    # 验证抽查
    check_nums = {15: "谦", 22: "贲", 42: "益"}
    print("\n[抽查验证]")
    by_num = {h["number"]: h for h in hexagrams}
    for num, expected_name in check_nums.items():
        h = by_num.get(num)
        if h:
            name_ok = "[OK]" if expected_name in h["name"] else f"[WARN] 期待{expected_name}但得到{h['name']}"
            print(f"  第{num}卦 {h['name']}: 卦辞={h['hexagram_ci'][:20]}... {name_ok}")
        else:
            print(f"  第{num}卦: [ERR] 缺失")


if __name__ == "__main__":
    main()
