"""Deterministic editorial and creative quality checks."""
from __future__ import annotations


def content_checks(item: dict) -> list[tuple[str, str]]:
    issues = []
    if not str(item.get("source", "")).strip():
        issues.append(("error", "Missing source."))
    if not str(item.get("approved_statement", "")).strip():
        issues.append(("error", "Missing factual core / approved statement."))
    src = str(item.get("source", ""))
    if src and not any(token in src.lower() for token in ["p.", "page", "section", "figure"]):
        issues.append(("warning", "Source does not include a page, section, or figure reference."))
    if len(str(item.get("approved_statement", ""))) > 280:
        issues.append(("warning", "Factual core is long. Keep the full version in the caption and use a shorter hook on the graphic."))
    if not str(item.get("primary_cta", "")).strip():
        issues.append(("warning", "CTA is missing."))
    if item.get("state") and not item.get("qualifier"):
        issues.append(("warning", "State-specific content has no qualifier."))
    return issues


def creative_checks(headline: str, graphic_text: str, source: str, cta: str, alt_text: str = "", has_photo: bool = False, rights_note: str = "") -> list[tuple[str, str]]:
    issues = []
    if len(headline) > 55:
        issues.append(("warning", "Headline is long for a mobile graphic."))
    if len(graphic_text) > 170:
        issues.append(("warning", "Too much body text for a mobile graphic. Use the caption for explanation."))
    if not source.strip():
        issues.append(("error", "Source is missing."))
    if not cta.strip():
        issues.append(("warning", "CTA is missing."))
    if not alt_text.strip():
        issues.append(("warning", "Alt text has not been created."))
    if has_photo and not rights_note.strip():
        issues.append(("error", "Photo rights/source field is blank."))
    return issues


def show_issues(st, issues):
    for level, text in issues:
        getattr(st, "error" if level == "error" else "warning")(text)
