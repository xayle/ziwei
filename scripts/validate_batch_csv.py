#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV 校验脚本（批量排盘前使用）
支持字段（必须存在，但不要求顺序）：name,year,month,day,hour,minute,gender,liunian_year
功能：
 - 验证 header 是否包含必需字段
 - 验证每行字段范围与日期合法性（闰年等）
 - 校验 gender（支持中文/英文字样映射）
 - 行数限制（默认 200）
 - 输出终端高亮错误报告（ANSI）并生成错误汇总 CSV
 - 可选生成标准化/清理后的 CSV（normalized_clean.csv）
"""
from __future__ import annotations
import csv
import sys
import argparse
import datetime
from typing import List, Dict, Any

# ANSI color codes for terminal highlighting
ANSI_RED = "\033[31m"
ANSI_YELLOW = "\033[33m"
ANSI_GREEN = "\033[32m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"

REQUIRED_COLUMNS = ["name", "year", "month", "day", "hour", "minute", "gender", "liunian_year"]

DEFAULT_MAX_ROWS = 200

GENDER_MAP = {
    "男": "男", "女": "女",
    "m": "男", "f": "女",
    "male": "男", "female": "女",
    "man": "男", "woman": "女",
    "1": "男", "0": "女"
}

def color(text: str, code: str) -> str:
    return f"{code}{text}{ANSI_RESET}"

def try_int(s: str | None):
    try:
        if s is None or s == "":
            return None
        return int(str(s).strip())
    except Exception:
        return None

def normalize_gender(s: str | None):
    if s is None:
        return None
    key = str(s).strip().lower()
    return GENDER_MAP.get(key) or GENDER_MAP.get(key.replace(" ", ""))

def validate_row(idx: int, row: Dict[str, str], allow_empty_name: bool=False) -> List[str]:
    errors: List[str] = []
    # name
    name = (row.get("name") or "").strip()
    if not name and not allow_empty_name:
        errors.append("name 为空")
    # year
    year = try_int(row.get("year"))
    if year is None:
        errors.append("year 非整数")
    else:
        if not (1800 <= year <= 2100):
            errors.append(f"year ({year}) 不在 1800-2100 范围内")
    # month
    month = try_int(row.get("month"))
    if month is None:
        errors.append("month 非整数")
    else:
        if not (1 <= month <= 12):
            errors.append(f"month ({month}) 非 1-12")
    # day
    day = try_int(row.get("day"))
    if day is None:
        errors.append("day 非整数")
    # hour
    hour = try_int(row.get("hour"))
    if hour is None:
        errors.append("hour 非整数")
    else:
        if not (0 <= hour <= 23):
            errors.append(f"hour ({hour}) 非 0-23")
    # minute
    minute = try_int(row.get("minute"))
    if minute is None:
        errors.append("minute 非整数")
    else:
        if not (0 <= minute <= 59):
            errors.append(f"minute ({minute}) 非 0-59")
    # gender
    gender_raw = row.get("gender")
    norm_gender = normalize_gender(gender_raw or "")
    if norm_gender is None:
        errors.append(f"gender 非法或缺失（支持: 男/女 / M/F / male/female）: '{gender_raw}'")
    # liunian_year
    liu = row.get("liunian_year")
    if liu is None or str(liu).strip() == "":
        # allow empty
        pass
    else:
        ly = try_int(liu)
        if ly is None:
            errors.append("liunian_year 非整数或格式不对")
        else:
            if not (1900 <= ly <= 2100):
                errors.append(f"liunian_year ({ly}) 不在 1900-2100 范围内")
    # date validity
    if year is not None and month is not None and day is not None:
        try:
            datetime.date(year, month, day)
        except Exception as e:
            if month == 2 and day == 29:
                is_leap = (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))
                if not is_leap:
                    errors.append(f"日期不合法: {year}-{month:02d}-{day:02d} 不是闰年")
                else:
                    errors.append(f"日期不合法: {year}-{month:02d}-{day:02d}（错误: {e}）")
            else:
                errors.append(f"日期不合法: {year}-{month}-{day}（错误: {e}）")

    return errors


def main():
    parser = argparse.ArgumentParser(description="批量排盘 CSV 校验脚本")
    parser.add_argument("csvfile", help="要校验的 CSV 文件路径（UTF-8）")
    parser.add_argument("--output-errors", "-o", default="input_errors.csv",
                        help="输出错误汇总 CSV（默认 input_errors.csv）")
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS,
                        help=f"最大行数，默认 {DEFAULT_MAX_ROWS}")
    parser.add_argument("--allow-empty-name", action="store_true",
                        help="允许 name 为空")
    parser.add_argument("--show-clean", action="store_true",
                        help="额外生成 normalized_clean.csv（标准化 gender / birth_iso 等）")
    args = parser.parse_args()

    csv_path = args.csvfile

    # ── 1. Header check ──────────────────────────────────────
    try:
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                print(color("读取 CSV 失败：未检测到列头（header）", ANSI_RED))
                sys.exit(2)
            lower_fields = [h.strip().lower() for h in reader.fieldnames]
            missing = [c for c in REQUIRED_COLUMNS if c not in lower_fields]
            if missing:
                print(color(f"CSV 缺少必要列（请包含且拼写正确）: {', '.join(missing)}", ANSI_RED))
                print("Detected headers:", [h.strip() for h in reader.fieldnames])
                sys.exit(2)
    except FileNotFoundError:
        print(color(f"文件未找到: {csv_path}", ANSI_RED))
        sys.exit(2)

    # ── 2. Read rows ──────────────────────────────────────────
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        header_map = {h.strip().lower(): h for h in fieldnames}
        rows = []
        for i, r in enumerate(reader, start=1):
            norm: Dict[str, str] = {}
            for req in REQUIRED_COLUMNS:
                orig_key = header_map.get(req)
                val = r.get(orig_key, "") if orig_key is not None else ""
                norm[req] = val if val is not None else ""
            norm["_row_index"] = str(i)
            rows.append(norm)

    total = len(rows)
    print(f"读取文件: {csv_path}，检测到 {total} 行（不含 header）")
    if total == 0:
        print(color("没有数据行，退出。", ANSI_YELLOW))
        sys.exit(0)
    if total > args.max_rows:
        print(color(f"行数 {total} 超过限制 {args.max_rows}，请拆分 CSV 后再上传。", ANSI_RED))

    # ── 3. Validate each row ──────────────────────────────────
    results = []
    any_errors = False
    for r in rows:
        idx = r["_row_index"]
        errors = validate_row(idx, r, allow_empty_name=args.allow_empty_name)
        norm_gender = normalize_gender(r.get("gender"))
        birth_iso = None
        y  = try_int(r.get("year"))
        mo = try_int(r.get("month"))
        d  = try_int(r.get("day"))
        hh = try_int(r.get("hour"))
        mm = try_int(r.get("minute"))
        if None not in (y, mo, d, hh, mm):
            try:
                birth_iso = f"{y:04d}-{mo:02d}-{d:02d}T{hh:02d}:{mm:02d}:00"
            except Exception:
                birth_iso = None
        over_limit = total > args.max_rows
        if errors:
            status = "failed"
            any_errors = True
        elif over_limit:
            status = "skipped"
        else:
            status = "success"
        results.append({
            "row_index": idx,
            "original": {k: r.get(k, "") for k in REQUIRED_COLUMNS},
            "errors": errors,
            "status": status,
            "normalized_gender": norm_gender or "",
            "birth_iso": birth_iso or "",
        })

    # ── 4. Terminal report ────────────────────────────────────
    print()
    print(color(ANSI_BOLD + "校验报告（高亮显示错误行）" + ANSI_RESET, ANSI_GREEN))
    for res in results:
        idx  = res["row_index"]
        orig = res["original"]
        errs = res["errors"]
        if errs:
            print(color(f"[行 {idx}] {orig.get('name','')} -> 错误: {len(errs)} 项", ANSI_RED))
            for e in errs:
                print("  -", color(e, ANSI_YELLOW))
        else:
            print(color(f"[行 {idx}] {orig.get('name','')} -> OK", ANSI_GREEN))

    total_errors = sum(1 for r in results if r["errors"])
    print()
    if total_errors:
        print(color(f"校验完成：共 {total} 行，错误行 {total_errors} 行，请修正后再上传。", ANSI_RED))
    else:
        print(color(f"校验完成：共 {total} 行，全部通过。", ANSI_GREEN))

    # ── 5. Write errors CSV ───────────────────────────────────
    out_path = args.output_errors
    with open(out_path, "w", encoding="utf-8", newline="") as outf:
        fieldnames = REQUIRED_COLUMNS + ["status", "error_messages", "normalized_gender", "birth_iso"]
        writer = csv.DictWriter(outf, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            row_out = {k: res["original"].get(k, "") for k in REQUIRED_COLUMNS}
            row_out["status"]           = res["status"]
            row_out["error_messages"]   = " ; ".join(res["errors"])
            row_out["normalized_gender"] = res["normalized_gender"]
            row_out["birth_iso"]        = res["birth_iso"]
            writer.writerow(row_out)
    print(f"已写出错误/汇总文件: {out_path}")

    # ── 6. Optional clean CSV ─────────────────────────────────
    if args.show_clean:
        clean_path = "normalized_clean.csv"
        with open(clean_path, "w", encoding="utf-8", newline="") as cf:
            fieldnames = ["row_index", "name", "birth_iso", "normalized_gender",
                          "liunian_year", "status", "error_messages"]
            w = csv.DictWriter(cf, fieldnames=fieldnames)
            w.writeheader()
            for res in results:
                orig = res["original"]
                w.writerow({
                    "row_index":         res["row_index"],
                    "name":              orig.get("name", ""),
                    "birth_iso":         res["birth_iso"],
                    "normalized_gender": res["normalized_gender"],
                    "liunian_year":      orig.get("liunian_year", ""),
                    "status":            res["status"],
                    "error_messages":    " ; ".join(res["errors"]),
                })
        print(f"已写出标准化清理文件: {clean_path}")

    # ── 7. Exit code ──────────────────────────────────────────
    if total_errors or total > args.max_rows:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
