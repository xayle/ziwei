"""
修复 classic_refs.py 文件损坏并在正确位置插入 77 条易经引文。

损坏原因：gen_yijing_refs.py 用 rfind("]") 找到了 self_check() 函数内
f-string `f"Ref {r['id']} missing category"` 中的 `]`，把 77 条内容插进去了。

修复策略：
  1. 将损坏区域（从 "assert r.get(\"category\"), f\"Ref {r['id'" 开始
     到文件末尾 "]} missing category\"\n"）替换为正确的单行 assert
  2. 在 CLASSIC_REFS 列表闭合符 `]\n\n# 快速索引` 之前插入 77 条引文
"""

import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "services" / "bazi_engine" / "classic_refs.py"
YIJING_JSON = ROOT / "data" / "classics_yijing.json"

# ─── Step 0: Load yijing data ────────────────────────────────────────────────
data = json.loads(YIJING_JSON.read_text(encoding="utf-8"))
hexagrams = data["hexagrams"]   # list of 64 dicts

# 与 gen_yijing_refs.py 完全相同的生成逻辑
TAG_MAP: dict[str, list[str]] = {
    "通论": ["易经", "格局"],
    "大运": ["易经", "大运"],
    "格局": ["易经", "格局"],
}

FEATURED: list[tuple[int, int, str]] = [
    (1, 0, "大运"), (1, 5, "大运"),          # 乾初九/上九
    (2, 0, "格局"),                           # 坤初六
    (11, 0, "格局"),                          # 泰卦
    (12, 0, "格局"),                          # 否卦
    (30, 0, "大运"),                          # 离卦
    (29, 0, "大运"),                          # 坎卦
    (63, 0, "格局"), (64, 0, "大运"),         # 既济/未济爻辞
    (17, 0, "通论"), (18, 0, "通论"),         # 随/蛊
    (24, 0, "通论"),                          # 复卦
    (44, 0, "通论"),                          # 姤卦
]

entries: list[str] = []
idx = 1
seen_ids: set[str] = set()

def _make_entry(ref_id: str, source: str, text: str, category: str, tags: list[str]) -> str:
    tags_repr = repr(tags)
    return (
        "    {\n"
        f'        "id": "{ref_id}",\n'
        f'        "source": "{source}",\n'
        f'        "text": "{text}",\n'
        f'        "category": "{category}",\n'
        f'        "tags": {tags_repr},\n'
        "    },"
    )

# 64 base entries (hexagram_ci + xiang_ci merged)
for h in hexagrams:
    num = h["number"]
    name = h["name"]
    full = h["full_name"]
    ci_text = h["hexagram_ci"]
    xiang_text = h["xiang_ci"]
    merged = f"{ci_text}象曰：{xiang_text}" if xiang_text else ci_text
    merged = merged[:120]
    category = "通论"
    tags = ["易经", name, "格局"]
    ref_id = f"yijing_{idx:03d}"
    entries.append(_make_entry(ref_id, f"《易经·{full}》", merged, category, tags))
    seen_ids.add(ref_id)
    idx += 1

# 13 featured yaoci entries
for (hnum, yao_idx, cat) in FEATURED:
    h = next((x for x in hexagrams if x["number"] == hnum), None)
    if h is None:
        continue
    yaoci_list = h.get("yaoci", [])
    if yao_idx >= len(yaoci_list):
        continue
    yao_text = yaoci_list[yao_idx][:100]
    name = h["name"]
    full = h["full_name"]
    yao_label = yao_text.split("：")[0] if "：" in yao_text else f"爻{yao_idx+1}"
    tags = ["易经", name, cat] + TAG_MAP.get(cat, [])
    tags = list(dict.fromkeys(tags))
    ref_id = f"yijing_{idx:03d}"
    entries.append(_make_entry(ref_id, f"《易经·{full}·{yao_label}》", yao_text, cat, tags))
    seen_ids.add(ref_id)
    idx += 1

print(f"Generated {len(entries)} yijing entries (idx up to yijing_{idx-1:03d})")

# Build the block to insert
header = "    # ── 易经 (yijing_001~yijing_{:03d}) {}\n".format(
    idx - 1, "─" * 44
)
entries_block = header + "\n".join(entries) + "\n"

# ─── Step 1: Read the damaged file ───────────────────────────────────────────
raw = TARGET.read_text(encoding="utf-8")

# ─── Step 2: Fix self_check() - replace damaged section ─────────────────────
BROKEN_START = '        assert r.get("category"), f"Ref {r[\'id\''
BROKEN_END   = ']} missing category"\n'

start_pos = raw.find(BROKEN_START)
if start_pos == -1:
    print("ERROR: Could not find broken assert line. File may already be fixed.")
    sys.exit(1)

end_pos = raw.rfind(BROKEN_END)
if end_pos == -1:
    print("ERROR: Could not find end of corruption ']} missing category\"\\n'")
    sys.exit(1)

end_pos_incl = end_pos + len(BROKEN_END)

CORRECT_ASSERT = '        assert r.get("category"), f"Ref {r[\'id\']} missing category"\n'
fixed_raw = raw[:start_pos] + CORRECT_ASSERT + raw[end_pos_incl:]
print(f"Step 2 OK: replaced {end_pos_incl - start_pos} chars with the correct assert ({len(CORRECT_ASSERT)} chars)")

# ─── Step 3: Insert entries before list-closing ] ────────────────────────────
LIST_CLOSE_MARKER = "]\n\n# 快速索引："
marker_pos = fixed_raw.find(LIST_CLOSE_MARKER)
if marker_pos == -1:
    print("ERROR: Could not find LIST_CLOSE_MARKER ']\n\n# 快速索引：'")
    sys.exit(1)

# Insert entries_block before the `]`
final_text = fixed_raw[:marker_pos] + entries_block + fixed_raw[marker_pos:]
print(f"Step 3 OK: inserted {len(entries)} entries before ']\n\n# 快速索引：'")

# ─── Step 4: Validate Python syntax ──────────────────────────────────────────
import ast
try:
    ast.parse(final_text)
    print("Step 4 OK: AST parse succeeded")
except SyntaxError as e:
    print(f"Step 4 FAIL: SyntaxError at line {e.lineno}: {e.msg}")
    # write to temp for inspection
    Path("_repair_FAIL.py").write_text(final_text, encoding="utf-8")
    sys.exit(1)

# ─── Step 5: Write ───────────────────────────────────────────────────────────
TARGET.write_text(final_text, encoding="utf-8")
print(f"Step 5 OK: {TARGET} written ({len(final_text.splitlines())} lines)")
print("Done!")
