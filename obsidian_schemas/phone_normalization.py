"""The phone-normalization authority, as a stdlib-only LEAF (WI-021, Design §5).

`normalize_phone` and `phones_match` lived in `repositories/person.py` until this
item. That home was fine while every caller sat at or above the repository layer;
it stopped being fine the moment a LEAF needed them. `name_gate.py` dedupes
`phones[]` on `normalize_phone`'s output, and a leaf gate naming
`repositories/person.py` closes the cycle
`writer.py -> name_gate -> repositories/person.py -> repositories/base.py -> writer.py`
at package load (`person.py` imports `.base`, `base.py` imports `..writer`).

So the two functions move here VERBATIM — same bodies, same behaviour — and:

  * `name_gate.py` imports them at module scope (leaf -> leaf, no cycle);
  * `identifier.py` imports at module scope too, which DELETES the two deferred
    imports it carried inside `Phone.parse` and `WhatsAppJID.parse` — the
    workaround this item would otherwise have reached for a third time. After
    that move `identifier.py` is still a leaf (it names one package sibling and
    nothing above it) but it is no longer *stdlib-only*;
  * `repositories/person.py` RE-EXPORTS both names, so
    `obsidian_schemas.repositories.person.normalize_phone` keeps resolving. That
    re-export is load-bearing in live consumer code, measured 2026-09-05: HAL9000
    `core/contact_resolver.py:13` and exocortex `clients/contacts.py:13` both
    import it from there.

This module is stdlib-only (`re`) and imports nothing from the package. That is
what makes it safe for `identifier.py` — the pure layer — to name at module
scope, and it lands WI-023's own scope item 4 early rather than duplicating it.

NOTE ON WHAT DID **NOT** MOVE WITH THEM. `phones_match`'s country-code
equivalence is WI-023 item 2's open question, not this item's, and it is NOT the
gate's dedupe predicate: it reports `447990558521` and `07990558521` as one
number, and it is not even transitive, so it is not a relation a seen-set can be
built on. The gate dedupes on `normalize_phone` alone.
"""

import re


def normalize_phone(phone: str) -> str:
    """
    Normalize a phone number to digits only.

    Examples:
        "+44 7990 558521" → "447990558521"
        "447990558521@s.whatsapp.net" → "447990558521"
        "(555) 123-4567" → "5551234567"
    """
    if not phone:
        return ""

    # Remove WhatsApp JID suffix
    phone = phone.split("@")[0]

    # Keep only digits
    return re.sub(r"\D", "", phone)


def phones_match(phone1: str, phone2: str) -> bool:
    """
    Check if two phone numbers represent the same person.

    Handles country code variations:
    - UK: 44... vs 0...
    - US: 1... vs 10-digit
    """
    norm1 = normalize_phone(phone1)
    norm2 = normalize_phone(phone2)

    if not norm1 or not norm2:
        return False

    # Direct match
    if norm1 == norm2:
        return True

    # UK: 44 prefix vs 0 prefix
    if norm1.startswith("44") and norm2.startswith("0"):
        return norm1[2:] == norm2[1:]
    if norm2.startswith("44") and norm1.startswith("0"):
        return norm2[2:] == norm1[1:]

    # US: 1 prefix vs 10-digit
    if norm1.startswith("1") and len(norm1) == 11:
        if norm1[1:] == norm2:
            return True
    if norm2.startswith("1") and len(norm2) == 11:
        if norm2[1:] == norm1:
            return True

    return False
