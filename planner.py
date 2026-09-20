"""Deterministic weekly recommendation engine.

No generated facts and no black-box scoring: every recommendation exposes a plain
English reason and uses only approved library metadata + calendar history.
"""
from __future__ import annotations

from datetime import date, timedelta
import pandas as pd

DEFAULT_SLOTS = [
    ("Monday", 0),
    ("Wednesday", 2),
    ("Friday", 4),
]


def next_weekday(base: date, weekday: int) -> date:
    return base + timedelta(days=(weekday - base.weekday()) % 7)


def _month_content_mix(calendar: pd.DataFrame, today: date) -> dict[str, float]:
    if calendar.empty:
        return {}
    c = calendar.copy()
    c["date"] = pd.to_datetime(c["date"], errors="coerce")
    m = c[c["date"].dt.strftime("%Y-%m") == today.strftime("%Y-%m")]
    if m.empty:
        return {}
    ideas = m.drop_duplicates(subset=["item_id"])
    counts = ideas["pillar"].value_counts(normalize=True) * 100
    return counts.to_dict()


def _recent_content(calendar: pd.DataFrame, today: date, recency_days: int) -> set[str]:
    if calendar.empty:
        return set()
    c = calendar.copy()
    c["date"] = pd.to_datetime(c["date"], errors="coerce").dt.date
    cutoff = today - timedelta(days=recency_days)
    return set(c.loc[(c["date"] >= cutoff) & (c["date"] <= today), "content_id"].astype(str))


def _audience_days_since(calendar: pd.DataFrame, today: date) -> dict[str, int]:
    if calendar.empty:
        return {}
    c = calendar.copy()
    c["date"] = pd.to_datetime(c["date"], errors="coerce").dt.date
    c = c[c["date"] <= today]
    result = {}
    for aud, g in c.groupby("audience"):
        vals = [d for d in g["date"] if pd.notna(d)]
        if vals:
            result[str(aud)] = (today - max(vals)).days
    return result


def recommend(content: list[dict], calendar: pd.DataFrame, settings: dict, today: date | None = None, n: int | None = None) -> list[dict]:
    today = today or date.today()
    n = int(n or settings.get("posts_per_week", 3))
    targets = settings.get("pillar_targets", {})
    recency_days = int(settings.get("recency_days", 21))
    mix = _month_content_mix(calendar, today)
    recent = _recent_content(calendar, today, recency_days)
    audience_age = _audience_days_since(calendar, today)

    publishable_statuses = {"Approved", "Scheduled", "Published"}
    approved = [x for x in content if x.get("workflow_status") in publishable_statuses]
    candidates = approved or content
    selected = []
    used_ids, used_pillars, used_audiences, used_templates = set(), set(), set(), set()

    for idx in range(min(n, len(DEFAULT_SLOTS))):
        best = None
        best_score = -10**9
        best_reasons = []
        for f in candidates:
            cid = str(f.get("id") or f.get("content_id"))
            if cid in used_ids:
                continue
            pillar = f.get("pillar", "")
            aud = f.get("primary_audience", "")
            templ = f.get("template_type", "")
            target = float(targets.get(pillar, 0))
            current = float(mix.get(pillar, 0))
            under = target - current
            score = under * 1.5
            reasons = []

            if under > 5:
                score += 20
                reasons.append(f"{pillar} is below its monthly target")
            elif under > 0:
                score += 8
                reasons.append(f"helps rebalance {pillar}")

            if cid in recent:
                score -= 80
                reasons.append(f"used within the last {recency_days} days")
            else:
                score += 18
                reasons.append(f"has not been used in the last {recency_days} days")

            days = audience_age.get(aud)
            if days is None:
                score += 18
                reasons.append(f"adds coverage for {aud}")
            elif days >= 10:
                score += min(days, 30)
                reasons.append(f"{aud} has not been served for {days} days")

            if pillar not in used_pillars:
                score += 18
            else:
                score -= 15
            if aud not in used_audiences:
                score += 10
            if templ not in used_templates:
                score += 6

            if f.get("campaign"):
                score += 5
                reasons.append("supports an active campaign")

            # Favor records with complete sourcing and qualifiers.
            if f.get("source"):
                score += 4
            if f.get("qualifier"):
                score += 2

            if score > best_score:
                best_score, best, best_reasons = score, f, reasons

        if not best:
            break
        cid = str(best.get("id") or best.get("content_id"))
        used_ids.add(cid)
        used_pillars.add(best.get("pillar", ""))
        used_audiences.add(best.get("primary_audience", ""))
        used_templates.add(best.get("template_type", ""))
        selected.append({"content": best, "reason": "; ".join(best_reasons[:3]) or "balanced recommendation"})

    return selected


def repetition_warnings(calendar: pd.DataFrame, recency_days: int = 21) -> list[str]:
    if calendar.empty:
        return []
    c = calendar.copy()
    c["date"] = pd.to_datetime(c["date"], errors="coerce")
    warnings = []
    # Same content idea on multiple dates inside a short window.
    ideas = c.drop_duplicates(subset=["item_id"])
    for cid, g in ideas.groupby("content_id"):
        dates = sorted([x for x in g["date"].dropna().tolist()])
        for a, b in zip(dates, dates[1:]):
            if (b - a).days <= recency_days:
                warnings.append(f"{cid} is scheduled more than once within {recency_days} days ({a.date()} and {b.date()}).")
                break
    return warnings


def mix_tables(calendar: pd.DataFrame, month: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return unique-idea content mix and separate channel execution mix."""
    if calendar.empty:
        return pd.DataFrame(), pd.DataFrame()
    c = calendar.copy()
    c["date"] = pd.to_datetime(c["date"], errors="coerce")
    if month:
        c = c[c["date"].dt.strftime("%Y-%m") == month]
    if c.empty:
        return pd.DataFrame(), pd.DataFrame()
    ideas = c.drop_duplicates(subset=["item_id"])
    content_mix = ideas.groupby("pillar", dropna=False).size().reset_index(name="content_ideas")
    channel_mix = c.groupby("channel", dropna=False).size().reset_index(name="executions")
    return content_mix, channel_mix
