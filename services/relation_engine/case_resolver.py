"""Resolve relation person input from Case records."""

from __future__ import annotations

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Case, User


def case_to_person_dict(case: Case, *, label: str | None = None) -> dict:
    gender = case.gender or "male"
    if gender in ("M", "m"):
        gender = "male"
    elif gender in ("F", "f"):
        gender = "female"
    return {
        "case_id": str(case.id),
        "birth_datetime": case.birth_dt_local,
        "tz": case.tz or "Asia/Shanghai",
        "longitude": float(case.lon or 116.41),
        "gender": gender,
        "label": label or case.name or "档案",
    }


def load_case_for_user(session: Session, case_id: str, user: User) -> Case:
    case = session.exec(
        select(Case).where(Case.id == case_id, Case.deleted_at.is_(None))  # type: ignore
    ).first()
    if case is None:
        raise HTTPException(404, f"Case not found: {case_id}")
    if case.owner_id is not None and case.owner_id != user.id:
        raise HTTPException(403, "Forbidden")
    return case


def resolve_person_input(
    person: dict,
    *,
    user: User | None,
    session: Session | None,
    default_label: str,
) -> dict:
    case_id = person.get("case_id")
    birth = person.get("birth_datetime")

    if case_id:
        if user is None or session is None:
            raise HTTPException(401, "case_id requires authentication")
        case = load_case_for_user(session, case_id, user)
        resolved = case_to_person_dict(case, label=person.get("label") or case.name or default_label)
        if birth:
            resolved["birth_datetime"] = birth
        if person.get("tz"):
            resolved["tz"] = person["tz"]
        if person.get("longitude") is not None:
            resolved["longitude"] = person["longitude"]
        if person.get("gender"):
            resolved["gender"] = person["gender"]
        return resolved

    if not birth:
        raise HTTPException(422, f"{default_label}: birth_datetime required when case_id omitted")

    return {
        "case_id": None,
        "birth_datetime": birth,
        "tz": person.get("tz") or "Asia/Shanghai",
        "longitude": float(person.get("longitude") or 116.41),
        "gender": person.get("gender") or "male",
        "label": person.get("label") or default_label,
    }
