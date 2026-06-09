"""Strip-to-recover name cleaning (WI-117, moved from exocortex graph/utils.py).

This module is the FOUNDATION home for `clean_person_name` — a *strip-to-recover*
pass that removes common artifacts (trailing digits, calendar/transcript
prefixes, archive prefixes, "unknown contact" suffixes, and — when corroborated
by an email domain or an explicit `known_companies` set — company suffixes/
prefixes) so a mangled mention text-matches the clean canonical.

WHY IT LIVES HERE NOW (WI-117, 2026-06-07): it previously lived in exocortex
(`exocortex/graph/utils.py`), the *consumer*. obsidian-schemas (the foundation)
can't import a consumer, so `PersonRepository.find_or_create_stub` — the shared
match-or-create door for every channel — could not clean a query before lookup.
The function is moved here wholesale so BOTH exocortex's meetings ingester (which
re-exports it from here) and `find_or_create_stub` call the SAME rule. No second
copy of the logic. (Collapsing exocortex's parallel match-or-create *orchestration*
onto `find_or_create_stub` is the deferred WI-118.)

RELATIONSHIP TO NameValidator (name_validation.py): COMPLEMENTARY, not duplicative.

  - `clean_person_name` is a *strip-to-recover* pass: it salvages a clean name
    out of recoverable junk ("Dave - Naomi Pavie" -> "Naomi Pavie").
  - `NameValidator` is a *reject* gate at write time: it raises on what recovery
    can't salvage ("Dave -> Thomas Gatten (Adzact)").

  Recovery produces a clean name that then passes the boundary; the boundary
  rejects what recovery can't salvage. We deliberately do NOT delegate cleaning
  to NameValidator (that would turn recoverable prefixes into hard rejections,
  LOSING data). The newer arrow/colon descriptor forms are NOT recovered here —
  recovery is ambiguous — so they flow to the boundary and are rejected there.

CALLER NOTE (WI-117 wrong-merge safety): `find_or_create_stub` does NOT pass
`known_companies` to this function. The unconditional `known_companies` suffix
strip is too aggressive for the shared door — it would collapse "Emma Roberts
Kato" onto a bare "Emma Roberts" canonical (a wrong merge) with no corroboration.
`find_or_create_stub` instead calls this for the unconditionally-safe cleanings
(digits/prefixes/unknown-contact) and applies a CORROBORATED company-suffix strip
separately. The `known_companies` path here is preserved for exocortex's existing
meetings ingester (WI-105 behaviour), unchanged.
"""

import re

# Calendar/transcript prefix forms that are SAFE to strip-recover. Matches the
# exocortex originals exactly (NOT the stricter name_validation.py regexes of the
# same name — those are the reject gate; these are the recovery pass).
_CALENDAR_PREFIX_RE = re.compile(r"^(Dave|Me|My)\s*[-/]\s+", re.IGNORECASE)
# WI-117 follow-up (2026-06-09): leading first-person UNICODE-arrow prefix —
# "Me → Thyra October" (a WhatsApp/iMessage chat-direction label "Me → recipient"
# leaked into the name field). Recovered to the participant ("Thyra October"),
# exactly like the dash ("Me - X") and "Me to X" forms above. ASCII "Me -> X" is
# deliberately NOT recovered here (WI-111 rejects it at the boundary — see
# test_clean_person_name_wi111_divergence); only the Unicode-arrow chat-direction
# form, which recovers cleanly with no trailing descriptor, is handled.
_ARROW_PREFIX_RE = re.compile(r"^(Dave|Me|My)\s*[→⟶⇒➜↦⇨]\s*", re.IGNORECASE)
_ME_TO_PREFIX_RE = re.compile(r"^(Me|My)\s+to\s+", re.IGNORECASE)
_ARCHIVE_PREFIX_RE = re.compile(r"^z+Archived\s*-\s*", re.IGNORECASE)
_UNKNOWN_CONTACT_SUFFIX_RE = re.compile(r"\s+unknown\s+contact\b", re.IGNORECASE)
_GENERIC_ORG_SUFFIXES = {"support", "ltd", "inc", "corp", "group", "team", "limited", "llc"}


def clean_person_name(
    name: str,
    email: str = "",
    known_companies: set = None,
) -> str:
    """Clean up a person name by removing common artifacts.

    Fixes (pre-WI-105):
    - Trailing digits: "Greg Cooke98" → "Greg Cooke"
    - Embedded digits between name parts: "Hannah1 Gadsden" → "Hannah Gadsden"
    - Org suffix appended when email is provided:
      "Anne-Sophie Legrain Vetup" (from vetup.fr) → "Anne-Sophie Legrain"
    - Double spaces

    WI-105 Step 2 additions (work WITHOUT email):
    - Calendar/transcript prefix: "Dave - Naomi Pavie" → "Naomi Pavie"
                                  "Me to Tom Green" → "Tom Green"
    - Archive prefix: "zArchived - Rosie Samuels" → "Rosie Samuels"
    - "unknown contact" suffix: "+E164 unknown contact" → "+E164"
    - Company suffix via DYNAMIC blacklist (known_companies set from
      PersonRepository): "Naomi Pavie Speechmatics" → "Naomi Pavie"
    - Company prefix (reverse): "Speechmatics Emily Mendes team" →
      "Emily Mendes" (strip prefix + generic suffix)

    The known_companies set bypasses the email-only guard that pre-WI-105
    let through every no-email junky record. Empirically (2026-06-02 vault
    audit) Granola is the dominant producer of no-email junk; passing the
    company set from PersonRepository at the call site closes the gap.

    WI-111 (single-authority decision, 2026-06-06): this function is a
    *strip-to-recover* pass at INGEST time and intentionally diverges from
    obsidian-schemas NameValidator, which is a *reject* gate at WRITE time.
    They are complementary, not duplicative — recovery produces a clean name
    that then passes the boundary; the boundary rejects what recovery can't
    salvage. We deliberately do NOT delegate to NameValidator here (that would
    turn recoverable prefixes like "Dave - Naomi Pavie" into hard rejections,
    LOSING data). The newer arrow/colon descriptor forms
    ("Dave -> Thomas Gatten (Adzact)", "Me to: David Field") are NOT recovered
    here — recovery is ambiguous — so they flow to create_stub and are caught
    there (skip + flag-for-review). See test_clean_person_name_wi111_divergence.

    WI-117 (2026-06-07): moved into obsidian-schemas (foundation) from exocortex
    so find_or_create_stub can clean the query before lookup. Behaviour-neutral —
    the body is identical to the exocortex original; exocortex now re-exports it.
    """
    if not name:
        return name

    known_companies = known_companies or set()
    cleaned = name

    # ---- WI-105: prefix strips (run FIRST so subsequent rules see clean ground) ----

    # 'zArchived - X' prefix
    cleaned = _ARCHIVE_PREFIX_RE.sub("", cleaned, count=1).strip()

    # 'Me to X' / 'My to X' prefix (check before generic Me/Dave-dash regex)
    cleaned = _ME_TO_PREFIX_RE.sub("", cleaned, count=1).strip()

    # 'Dave -', 'Me -', 'My -' prefix
    cleaned = _CALENDAR_PREFIX_RE.sub("", cleaned, count=1).strip()

    # 'Dave →', 'Me →', 'My →' leading Unicode-arrow chat-direction prefix
    cleaned = _ARROW_PREFIX_RE.sub("", cleaned, count=1).strip()

    # 'X unknown contact' suffix
    cleaned = _UNKNOWN_CONTACT_SUFFIX_RE.sub("", cleaned).strip()

    # ---- Pre-WI-105 digit cleaning ----
    # Only strip digits when there's actual letter content — preserves
    # pure-phone strings like "447950289840" (which can arrive after the
    # unknown_contact suffix-strip above), so they remain as phone sentinels.

    if re.search(r'[A-Za-z]', cleaned):
        # Strip trailing digits from the full name: "Greg Cooke98" → "Greg Cooke"
        cleaned = re.sub(r'\d+$', '', cleaned).strip()
        # Strip digits stuck to individual words: "Hannah1 Gadsden" → "Hannah Gadsden"
        cleaned = re.sub(r'(\b[A-Za-z]+)\d+(\b)', r'\1\2', cleaned).strip()

    # ---- Pre-WI-105 email-domain-based org-suffix strip ----

    if email and "@" in email:
        domain = email.lower().split("@")[1]
        domain_prefix = domain.split(".")[0]
        words = cleaned.split()
        while len(words) > 2:
            last = words[-1].lower()
            if last == domain_prefix or last in _GENERIC_ORG_SUFFIXES:
                words.pop()
            else:
                break
        cleaned = " ".join(words)

    # ---- WI-105: dynamic-blacklist company-suffix and -prefix stripping ----

    # Strip company SUFFIX using known_companies. Multi-token companies
    # (e.g. "Dawn Capital") supported by checking suffix windows.
    if known_companies:
        words = cleaned.split()
        # Try matching the largest suffix first so "Dawn Capital" beats "Capital"
        for n in (3, 2, 1):
            if len(words) - n < 2:
                continue
            suffix = " ".join(words[-n:])
            if suffix in known_companies:
                words = words[:-n]
                break
        cleaned = " ".join(words)

        # Strip company PREFIX (reverse pattern: "Speechmatics Emily Mendes")
        words = cleaned.split()
        for n in (3, 2, 1):
            if len(words) - n < 2:
                continue
            prefix = " ".join(words[:n])
            if prefix in known_companies:
                words = words[n:]
                break
        cleaned = " ".join(words)

        # After prefix-strip, generic org suffixes like 'team' may now be
        # the trailing token. Strip them.
        words = cleaned.split()
        while len(words) > 2:
            if words[-1].lower() in _GENERIC_ORG_SUFFIXES:
                words.pop()
            else:
                break
        # Allow stripping down to 2 tokens for the "Company X Y team" pattern
        # where after company-prefix-strip we have "X Y team" → "X Y".
        if len(words) >= 2 and words[-1].lower() in _GENERIC_ORG_SUFFIXES:
            words.pop()
        cleaned = " ".join(words)

    # ---- Whitespace normalize ----

    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()

    return cleaned if cleaned else name
