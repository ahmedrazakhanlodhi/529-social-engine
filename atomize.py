"""Turn one approved fact into eight platform outputs using the strategy's
HOOK -> VALUE -> PROOF -> NEXT STEP formula. Deterministic templates, no API.
Everything returned here is editable in the app before use."""

def _hook(fact):
    tt = (fact.get("template_type") or "").upper()
    hl = fact.get("headline", "")
    if "MYTH" in tt:
        return fact.get("myth_text") or "Think you need a lot of money to start saving?"
    if "STATE" in tt or "PARTNER" in tt:
        return f"{fact.get('state', 'One state')} shows one way to help families save."
    return f"{hl}. Here is what that means for families."

def _proof(fact):
    return f"The 2026 National 529 Survey found: {fact['approved_statement']}"

def _qual(fact):
    q = fact.get("qualifier", "")
    return f" {q}" if q else ""

def _src(fact):
    return f"Source: The 529 Network, 2026 National 529 Survey ({fact.get('source','')})."

def _cta(fact):
    return fact.get("primary_cta", "Learn more")

def instagram_carousel(fact):
    cards = []
    cards.append(f"CARD 1 (hook): {_hook(fact)}")
    cards.append(f"CARD 2 (value): {fact['approved_statement']}")
    if fact.get("qualifier"):
        cards.append(f"CARD 3 (context): {fact['qualifier']}")
    cards.append(f"CARD {len(cards)+1} (proof): {_src(fact)}")
    cards.append(f"CARD {len(cards)+1} (next step): {_cta(fact)}.")
    return "\n".join(cards)

def reel_script(fact):
    return (
        f"[0-3s] {_hook(fact)}\n"
        f"[3-15s] {fact['approved_statement']}\n"
        f"[15-22s]{_qual(fact)}\n"
        f"[22-30s] Next step: {_cta(fact)}. {_src(fact)}"
    ).strip()

def linkedin_post(fact):
    aud = fact.get("primary_audience", "")
    return (
        f"{_hook(fact)}\n\n"
        f"{_proof(fact)}{_qual(fact)}\n\n"
        f"For {aud.lower()}, this is evidence that state 529 plans are actively "
        f"reducing barriers and investing in families.\n\n"
        f"{_cta(fact)}.\n\n{_src(fact)}"
    )

def facebook_post(fact):
    return (
        f"{_hook(fact)}\n\n{fact['approved_statement']}{_qual(fact)}\n\n"
        f"{_cta(fact)}. {_src(fact)}"
    )

def blog_stub(fact):
    return (
        f"Working title: {fact.get('headline','')}: what the 2026 survey shows\n\n"
        f"Lede: {fact['approved_statement']}\n\n"
        f"Outline:\n"
        f"1. The national finding and why it matters to families.\n"
        f"2. How this varies by state ({fact.get('qualifier','rules differ by state')}).\n"
        f"3. The practical next step for a family: {_cta(fact)}.\n"
        f"4. Where the number comes from. {_src(fact)}"
    )

def member_toolkit(fact):
    return (
        "MEMBER SOCIAL KIT\n"
        f"National caption: {facebook_post(fact)}\n\n"
        f"Editable state version: In [STATE], [state program name] reflects this. {fact['approved_statement']} {_cta(fact)}.\n\n"
        f"Alt text: {alt_text(fact)}\n\n"
        f"Source note: {_src(fact)}\n"
        f"Suggested tags: @The529Network + featured member/partner accounts\n"
        f"Link + UTM: ?utm_source=member&utm_medium=social&utm_campaign=national_effort&utm_content={fact.get('id','')}\n"
        "Posting window: 48-72 hour coordinated window"
    )

def email_block(fact):
    return (
        "WHAT THE DATA SAYS\n"
        f"{fact['approved_statement']}{_qual(fact)}\n"
        f"{_cta(fact)} -> [plan finder link]\n"
        f"{_src(fact)}"
    )

def alt_text(fact):
    return (
        f"Graphic from The 529 Network. Headline: {fact.get('headline','')}. "
        f"{fact['approved_statement']} {fact.get('source','')}."
    )

FORMATS = [
    ("Instagram carousel", instagram_carousel),
    ("Reel / Short script", reel_script),
    ("LinkedIn post", linkedin_post),
    ("Facebook post", facebook_post),
    ("Website / blog stub", blog_stub),
    ("Member toolkit", member_toolkit),
    ("Email / newsletter", email_block),
    ("Alt text", alt_text),
]

def all_formats(fact):
    return {name: fn(fact) for name, fn in FORMATS}
