"""Parse fusheng profile tags stored on Case.tags (FE profileCaseSync parity)."""

from __future__ import annotations

from app.models import Case


def parse_fusheng_tags(tags: str | None) -> dict[str, str | bool]:
    """Return known tag keys from comma-separated fusheng tags."""
    result: dict[str, str | bool] = {}
    if not tags:
        return result
    for part in tags.split(","):
        trimmed = part.strip()
        if trimmed.startswith("lz:"):
            result["late_zishi"] = trimmed[3:] == "1"
        elif trimmed.startswith("zbm:"):
            result["ziwei_brightness_method"] = trimmed[4:]
        elif trimmed.startswith("zyb:"):
            result["ziwei_youbi_method"] = trimmed[4:]
        elif trimmed.startswith("zsm:"):
            result["ziwei_sihua_method"] = trimmed[4:]
        elif trimmed.startswith("zlsm:"):
            result["ziwei_liunian_sihua_method"] = trimmed[5:]
        elif trimmed.startswith("zkm:"):
            result["ziwei_kuiyue_method"] = trimmed[4:]
        elif trimmed.startswith("ztm:"):
            result["ziwei_tianma_method"] = trimmed[4:]
        elif trimmed.startswith("ztv:"):
            result["ziwei_template_version"] = trimmed[4:]
    return result


def case_late_zishi(case: Case, *, default: bool = True) -> bool:
    """Resolve late_zishi: Case column if present, else tags lz:0|1, else default."""
    explicit = getattr(case, "late_zishi", None)
    if explicit is not None:
        return bool(explicit)
    tag_meta = parse_fusheng_tags(case.tags)
    if "late_zishi" in tag_meta:
        return bool(tag_meta["late_zishi"])
    return default
