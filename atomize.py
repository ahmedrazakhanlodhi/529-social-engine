"""Turn one approved fact into channel outputs using HOOK -> VALUE -> PROOF ->
NEXT STEP. Deterministic templates, no API. All outputs are editable in the app.

When settings carry real URLs, the NEXT STEP becomes an actionable link with UTM
tags; otherwise it stays a plain call to action with no dead placeholder link.
"""
from __future__ import annotations


def resolve_link(cta: str, settings: dict | None, content_id: str = "") -> str:
    if not settings:
        return ""
    cl = (cta or "").lower()
    if "plan" in cl:
        url = settings.get("plan_finder_url", "")
    elif "report" in cl:
        url = settings.get("report_url", "")
    elif "work" in cl or "employer" in cl:
        url = settings.get("employer_url", "")
    else:
        url = settings.get("primary_website_url", "")
    if not url:
        return ""
    utm = settings.get("utm_campaign", "529_network_content")
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source=social&utm_medium=organic&utm_campaign={utm}&utm_content={content_id}"


def _next_step(fact, settings):
    cta = fact.get("primary_cta", "Learn more")
    link = resolve_link(cta, settings, str(fact.get("id", "")))
    return f"{cta}: {link}" if link else f"{cta}."


def _hook(fact):
    tt = (fact.get("template_type") or "").upper()
    hl = fact.get("headline", "")
    if "MYTH" in tt:
        return fact.get("myth_text") or "Think you need a lot of money to start saving?"
    if "STATE" in tt or "PARTNER" in tt or "PEOPLE" in tt:
        return f"{fact.get('state', 'One state')} shows one way to help families save."
    return f"{hl}. Here is what that means for families."


def _proof(fact):
    return f"The 2026 National 529 Survey found: {fact['approved_statement']}"


def _qual(fact):
    q = fact.get("qualifier", "")
    return f" {q}" if q else ""


def _src(fact):
    return f"Source: The 529 Network, 2026 National 529 Survey ({fact.get('source','')})."


def instagram_carousel(fact, settings=None):
    cards = [f"CARD 1 (hook): {_hook(fact)}", f"CARD 2 (value): {fact['approved_statement']}"]
    if fact.get("qualifier"):
        cards.append(f"CARD 3 (context): {fact['qualifier']}")
    cards.append(f"CARD {len(cards)+1} (proof): {_src(fact)}")
    cards.append(f"CARD {len(cards)+1} (next step): {_next_step(fact, settings)}")
    return "\n".join(cards)


def reel_script(fact, settings=None):
    return (
        f"[0-3s] {_hook(fact)}\n"
        f"[3-15s] {fact['approved_statement']}\n"
        f"[15-22s]{_qual(fact)}\n"
        f"[22-30s] Next step: {_next_step(fact, settings)} {_src(fact)}"
    ).strip()


def linkedin_post(fact, settings=None):
    aud = fact.get("primary_audience", "")
    return (
        f"{_hook(fact)}\n\n{_proof(fact)}{_qual(fact)}\n\n"
        f"For {aud.lower()}, this is evidence that state 529 plans are actively "
        f"reducing barriers and investing in families.\n\n"
        f"{_next_step(fact, settings)}\n\n{_src(fact)}"
    )


def facebook_post(fact, settings=None):
    return f"{_hook(fact)}\n\n{fact['approved_statement']}{_qual(fact)}\n\n{_next_step(fact, settings)} {_src(fact)}"


def short_form(fact, settings=None):
    return f"{fact.get('headline','')} {fact['approved_statement']} {_next_step(fact, settings)}"


def blog_stub(fact, settings=None):
    return (
        f"Working title: {fact.get('headline','')}: what the 2026 survey shows\n\n"
        f"Lede: {fact['approved_statement']}\n\n"
        f"Outline:\n"
        f"1. The national finding and why it matters to families.\n"
        f"2. How this varies by state ({fact.get('qualifier','rules differ by state')}).\n"
        f"3. The practical next step for a family: {_next_step(fact, settings)}\n"
        f"4. Where the number comes from. {_src(fact)}"
    )


def member_toolkit(fact, settings=None):
    link = resolve_link(fact.get("primary_cta", ""), settings, str(fact.get("id", ""))) or "[add link in Settings]"
    return (
        "MEMBER SOCIAL KIT\n"
        f"National caption: {facebook_post(fact, settings)}\n\n"
        f"Editable state version: In [STATE], [state program name] reflects this. {fact['approved_statement']} {fact.get('primary_cta','Learn more')}.\n\n"
        f"Alt text: {alt_text(fact)}\n\n"
        f"Source note: {_src(fact)}\n"
        f"Suggested tags: @The529Network plus featured member or partner accounts\n"
        f"Link: {link}\n"
        "Posting window: 48 to 72 hour coordinated window"
    )


def email_block(fact, settings=None):
    return (
        "WHAT THE DATA SAYS\n"
        f"{fact['approved_statement']}{_qual(fact)}\n"
        f"{_next_step(fact, settings)}\n"
        f"{_src(fact)}"
    )


def alt_text(fact, settings=None):
    return (
        f"Graphic from The 529 Network. Headline: {fact.get('headline','')}. "
        f"{fact['approved_statement']} {fact.get('source','')}."
    )


FORMATS = [
    ("LinkedIn", linkedin_post),
    ("Instagram", facebook_post),
    ("Facebook", facebook_post),
    ("Short-form copy", short_form),
    ("Instagram carousel", instagram_carousel),
    ("30-second video script", reel_script),
    ("Website / newsletter paragraph", blog_stub),
    ("Email block", email_block),
    ("Member toolkit", member_toolkit),
    ("Alt text", alt_text),
]


def all_formats(fact, settings=None):
    return {name: fn(fact, settings) for name, fn in FORMATS}
