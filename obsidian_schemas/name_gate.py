"""THE semantic write gate (WI-021) — one function every write door hands its
delta to, which validates the name it introduces and normalizes the addresses,
or refuses.

WI-004 closed the MECHANICAL write door (atomicity, per-note locking, stamp
preconditions). This is the SEMANTIC layer on the same door. Before it,
`NameValidator` fired at exactly one site in the package — `create_stub` — so a
direct `repo.save(...)`, an `update_fields(person, {"name": ...})` or a bare
`write_markdown_file(...)` wrote an arbitrary or path-hostile name with no
validation at all; and RFC 2822 normalization ran only inside
`PersonRepository.save`, so `_writeback_identifier` appended raw `Name <email>`
strings straight into `emails[]` and broke exact-email dedupe.

**A LEAF module.** Its imports are `errors`, `identifier`, `name_validation` and
`phone_normalization` — all leaves. It must NOT import `writer`, `parser`,
`vault_io`, `models` or anything under `repositories/`: the entity-shaped arms
project through `writer.model_to_frontmatter` BEFORE calling, so the gate never
needs a model type, and naming a repository here would close
`writer -> gate -> repositories/person -> repositories/base -> writer` at
package load. That is also why `normalize_phone` had to move to a leaf first.

**DECLARE.** The gate is HANDED its entity type; it never derives one. It reads
only its own arguments — no filesystem, no glob, no path shape, no sibling note,
and `BaseRepository._owns` is called nowhere in this design. Two things fall out
of that and both are load-bearing: the gate call can be HOISTED above
`vault_io.note_lock` at the arms that support it (nothing it reads is
lock-protected), which is what lets a refusal land BEFORE the lock's own
`mkdir` puts a path-mangled `<vault>/@Dave/` on disk; and an UNDECLARED write
that introduces a `name:` is refused outright rather than guessed at.

**THE DELTA, never the record.** `introduced` is what THIS write introduces. The
gate judging the merged record instead would make `update_frontmatter_field`
permanently refuse every note whose STORED name is already Tier-1 dirty — the
remedy-is-the-disease outcome, at exactly the arms those notes are reachable
through. A stored-dirty note stays writable for every write that does not
re-introduce its name.

**THE NAME IS AN IDENTITY, not a transform.** On `name` the gate is a PREDICATE:
it calls `validate_strict` for its RAISE behaviour, discards the repaired string,
and emits the name it was handed byte-for-byte. That is not tidiness. The
FILENAME is bound from the raw `entity.name` one frame ABOVE every gate call and
never revisited, so a gate that returned `"Dave Smith"` for `"Dave  Smith"` would
write that field into `@Dave  Smith.md` and the next `save()` would mint a second
note for one person. Tier-2 repair therefore stays exactly where it already runs
— `create_stub`, ABOVE the filename derivation — which is why it has never
produced that divergence.

**THE OUTPUT NEVER GROWS.** The returned dict's key set is exactly the input's.
That is forced rather than stylistic: `update_fields` merges by key REPLACEMENT,
so a gate that emitted a destination key would OVERWRITE that field's stored list
rather than append to it. It is also why the two cross-field migrations are
available only where the caller's payload IS the whole record.
"""

import re
from email.utils import parseaddr
from typing import Any, Mapping, NoReturn, Optional

from .errors import NameGateRefusal, chainable_cause
from .identifier import Email, IdentifierError
from .name_validation import (
    COMPANY_TIER1_BRANCHES,
    NameValidationError,
    NameValidator,
)
from .phone_normalization import normalize_phone

# The rule-(ii) refusal's pattern key. Not a NameValidator pattern — it is the
# gate's own, and it is what discriminates "this write declared nothing" from
# "this name matched a Tier-1 pattern" on ONE `REASONS` literal.
UNDECLARED_PATTERN: str = "undeclared_name_write"

PERSON_TYPE: str = "person"

# WI-022. The second declared type the gate has a judgement for, and the value
# `Company.type`'s `Literal["company"]` puts in every company write's `type:`.
COMPANY_TYPE: str = "company"

# The single enumerated reason every refusal carries. One literal, not two:
# `pattern` is the routing signal consumers keep.
_REFUSAL_REASON: str = "the write introduces a name this package refuses"

# The three identifier-bearing frontmatter keys this gate has any rule about.
_CONTAINER_KEYS = ("emails", "phones", "aliases")

# The parens form — `Name (a@b.com)` — which `Email.parse` deliberately does not
# accept. The splitter owns it BEFORE delegating, which is the whole of what
# "owns the parens form" means: the address it extracts still goes through
# `Email.parse`, so there is no second address authority.
_PARENS_ADDRESS_RE = re.compile(r"^(.*?)\s*\(\s*([^@\s]+@[^\s)]+)\s*\)\s*$")


# ---------------------------------------------------------------------------
# The address splitter — the ONE implementation of the job (Design §4)
# ---------------------------------------------------------------------------

def split_address(entry: Any) -> tuple:
    """Split a display-name/address blob into `(address | None, display)`.

    TOTAL: every input returns, nothing raises. `address` is
    `Email.parse(candidate).value` — the LOWER-CASED normalized address — never
    the raw slice, and that choice is the item's own subject in miniature:
    `Email.value` is the identity key the WI-125 engine dedupes on, so storing a
    raw-cased slice while deduping on the lowered one is the corruption class
    this gate exists to close. `display` is `""` whenever there is none.

    It does NOT widen `Email.parse`'s angle-bracket gate. That gate routes
    through `parseaddr` only for genuine `<...>` forms because parseaddr
    silently REPAIRS a bare `"a@b c.com"` into `"a@bc.com"`, minting a wrong
    identity key; this function's own `<`/`>` test mirrors it exactly, and is
    used only to recover the DISPLAY half, which `Email.parse` does not return.

    An `IdentifierError` maps to "not an address" — `(None, "")` — so a caller
    can keep the entry verbatim rather than discard it.
    """
    if not isinstance(entry, str) or not entry:
        return None, ""

    parens = _PARENS_ADDRESS_RE.match(entry)
    if parens:
        candidate = parens.group(2).strip()
        display = parens.group(1).strip()
    elif "<" in entry and ">" in entry:
        # The one permitted parseaddr reach, and it is for the DISPLAY half
        # only — the address below still comes from Email.parse.
        candidate = entry
        display = (parseaddr(entry)[0] or "").strip()
    else:
        candidate = entry
        display = ""

    try:
        return Email.parse(candidate).value, display
    except IdentifierError:
        return None, ""


# ---------------------------------------------------------------------------
# The ONE refusal construction site (Design §2)
# ---------------------------------------------------------------------------

def _refuse(pattern_key: str, *, cause: Optional[BaseException] = None) -> NoReturn:
    """Build and raise the gate's refusal. The ONE construction site.

    Two rules, both total over this single raise-site, and both are about a
    channel rather than about tidiness — because of what the caught object
    carries: `NameValidationError`'s message interpolates the RAW NAME at every
    one of its nine branch sites, and for `contains_email_chars` and
    `rfc2822_leak` that name IS an email address.

    1. **The chain is suppressed, by the package's own function.** The natural
       build — `except NameValidationError as e: _refuse(e.pattern)` — raises
       INSIDE the handler with no `from` clause, so the interpreter sets
       `__context__` and every default traceback renders the refused note's
       bytes. `chainable_cause` returns None for a `NameValidationError` (a
       plain ValueError, in neither CHAINABLE arm), so `raise ... from` it both
       empties `__cause__` and sets `__suppress_context__`. This does NOT write
       `from None` by hand: the decision belongs to `chainable_cause`, and a
       site that spells the answer itself is the site that is wrong when the
       answer moves. The `is not None` guard exists only because
       `chainable_cause` is annotated over `BaseException` and rule (ii)'s
       refusal is raised from no handler at all.

    2. **No note-derived value enters the constructor.** The one `REASONS`
       literal and nothing else — no `declared_type=`, which `bounded_message`
       renders and which at three of the eight arms IS the target note's own
       parsed `type:`; no `cause=`, which it projects; and no `path=`, which it
       renders and which at the create-shaped arms ends in `@<the refused
       name>.md`. `pattern` is set as an ATTRIBUTE after construction, so it
       reaches no message at all.
    """
    exc = NameGateRefusal(_REFUSAL_REASON)
    exc.pattern = pattern_key
    raise exc from (chainable_cause(cause) if cause is not None else None)


# ---------------------------------------------------------------------------
# The list-shape precondition (Design §1.4)
# ---------------------------------------------------------------------------

def _is_str_list(value: Any) -> bool:
    """ONE positive predicate, which is the point rather than the style.

    The value under `emails`, `phones` or `aliases` is a caller's UNTYPED value
    at exactly the arms this boundary was declared over —
    `update_frontmatter_field` types it `Any`, `update_fields` types its payload
    `dict[str, Any]`. The `List[str]` shape pydantic guarantees on the entity
    arms is guaranteed on none of them. Because the test is positive, `None`, a
    bare `str`, an `int`, a `dict` and a list carrying one non-`str` member all
    take the same pass-through arm, and a shape nobody enumerated falls to
    pass-through rather than to iteration.
    """
    return isinstance(value, list) and all(isinstance(member, str) for member in value)


def _shaped(introduced: Mapping[str, Any], key: str) -> bool:
    """The key is present AND its value is a list of strings."""
    return key in introduced and _is_str_list(introduced[key])


# ---------------------------------------------------------------------------
# The phones[] dedupe (Design §5)
# ---------------------------------------------------------------------------

def _dedupe_phones(values: list) -> list:
    """Dedupe on `normalize_phone`'s output while storing the DISPLAY form.

    Four rules, none inferable from the others:

    1. **The key is `normalize_phone`'s output and nothing else.**
       `Phone.parse`'s `MIN_DIGITS = 7` floor is never introduced into this path
       — it would make a short entry unkeyable by RAISING — and `phones_match`'s
       country-code equivalence is not adopted: it reports `447990558521` and
       `07990558521` as one number, which is a UK-specific question this item
       does not own, and it is not even transitive, so it is not a relation a
       seen-set can be built on. Both are stated as rules rather than left as an
       absence, because a build that dedupes with either is green everywhere
       else in this design.
    2. **The empty key is not a key.** An entry carrying NO DIGIT AT ALL after
       the `@` split — `"n/a"`, `"ext."`, `"call the office"`; NOT an
       extension-only string like `"ext. 4021"`, whose output is `"4021"` — is
       never a dedupe key and passes through byte-identical, in place. A naive
       seen-set keyed on the normalized form would otherwise silently delete
       every digit-less entry after the first.
    3. **The winner among entries sharing a non-empty key is the E.164
       spelling** (Dave's ruling 4, 2026-09-05) — the first entry in source
       order whose stripped display form begins with `"+"`, else the first in
       source order. This selects a winner AMONG duplicates; it does not rewrite
       non-duplicate stored phones to E.164.
    4. **The survivor is stored byte-identical at the index of its group's FIRST
       entry.** Nothing is re-spelled, and pinning the output position to the
       first occurrence is what makes the output a function of the input alone
       and makes a second pass a no-op — which idempotence requires and the
       rider actually exercises.

    This is a DELETION over live stored data: nothing in this package normalizes
    or dedupes `phones[]` today, so two spellings of one number coexist on disk
    right now and the first gated whole-list write drops one of them. That is
    signed behaviour, against a measured population.
    """
    groups: dict = {}
    slots: list = []          # (key, entry) — key None means "passes through"

    for entry in values:
        key = normalize_phone(entry)
        if not key:                       # rule 2
            slots.append((None, entry))
            continue
        if key not in groups:
            groups[key] = []
            slots.append((key, None))     # rule 4 — the group's FIRST index
        groups[key].append(entry)

    out: list = []
    for key, entry in slots:
        if key is None:
            out.append(entry)
            continue
        members = groups[key]
        # rule 3 — E.164 wins where one is present, first-seen otherwise
        winner = next((m for m in members if m.strip().startswith("+")), members[0])
        out.append(winner)                # rule 4 — byte-identical
    return out


# ---------------------------------------------------------------------------
# The gate (Design §1)
# ---------------------------------------------------------------------------

def gate_write(
    introduced: Mapping[str, Any],
    *,
    declared_type: Optional[str],
    whole_record: bool,
) -> dict:
    """Judge and normalize the fields a write INTRODUCES.

    Returns a NEW dict carrying exactly the keys `introduced` carried, or raises
    `NameGateRefusal`.

    Args:
        introduced: the DELTA — what this write introduces, never the merged
            record.
        declared_type: the declaration the arm HOLDS, `None` when it genuinely
            has none. **No default**, so an arm holding no declaration passes
            the literal `None` explicitly: the absence is EXPRESSED, never
            defaulted, and "defaulted" is unconstructible by `TypeError` at the
            signature rather than merely asserted against.
        whole_record: `True` only where the payload guarantees BOTH a
            migration's source and its destination field, so that no key the
            write did not carry can be emitted. `model_to_frontmatter`'s
            unconditional emission makes the entity arm `True`; a caller's dict
            makes the dict-shaped arms `False` even when their payload happens
            to be the whole note.

    Idempotent on both values of `whole_record` — `gate_write(gate_write(x)) ==
    gate_write(x)` — which is required rather than incidental: one
    `PersonRepository.save` invokes it twice, the write-back rider and then the
    entity arm on the projection the rider just normalized.
    """
    # ---- 1. Rule (ii) — the undeclared refusal -----------------------------
    #
    # Precedes every pattern evaluation, so no person-derived Tier-1 pattern
    # ever judges an undeclared write.
    if "name" in introduced and declared_type is None:
        _refuse(UNDECLARED_PATTERN)

    # ---- 2. A DECLARED non-person type passes through untouched ------------
    #
    # The `is not None` half is load-bearing and is the one place this branch
    # could be written half a line shorter and be wrong: an UNDECLARED write
    # that introduces identifiers but NO `name:` must fall THROUGH and normalize
    # exactly as a declared one, because rule (ii) speaks only to `name:`. A
    # bare `declared_type != PERSON_TYPE` test would return it unchanged.
    #
    # This branch is also why a Person-only gate survives at the entity arm,
    # which every entity type reaches: a Book write is gated and handed straight
    # back.
    if declared_type is not None and declared_type != PERSON_TYPE:
        # WI-022 — the COMPANY judgement, INSIDE this branch and above its
        # return, deliberately NOT written as a widened condition
        # (`declared_type not in (PERSON_TYPE, COMPANY_TYPE)`) letting company
        # fall through to the person body. That cheaper-looking edit is wrong
        # twice: it would apply the PERSON table to company names — whose
        # `rfc2822_leak` branch refuses the real company "wetransfer.com" — and
        # it would silently subject company writes to the phones[] dedupe below
        # (a DELETION over stored data) and to the two alias/email migrations,
        # none of which this item signs off for companies.
        if declared_type == COMPANY_TYPE and "name" in introduced:
            raw_name = introduced["name"]
            # `None` coerces to "" rather than to the string "None", for the
            # same reason the person arm does it below: the decision for a null
            # name is the `empty` refusal, and str(None) is a name that would
            # sail through.
            name_text = "" if raw_name is None else str(raw_name)
            try:
                # Called for its RAISE behaviour; the repaired string is
                # DISCARDED. THE NAME IS AN IDENTITY, not a transform — the
                # filename is bound from the raw name one frame above.
                NameValidator().validate_strict(
                    name_text, branches=COMPANY_TIER1_BRANCHES)
            except NameValidationError as exc:
                _refuse(exc.pattern, cause=exc)
        return dict(introduced)

    result = dict(introduced)

    # ---- 3. Name — a PREDICATE, not a transform ----------------------------
    if "name" in introduced:
        raw_name = introduced["name"]
        # `None` coerces to the empty string rather than to the string "None":
        # the decision for a null name is the `empty` refusal, and `str(None)`
        # is a perfectly valid name that would sail through.
        name_text = "" if raw_name is None else str(raw_name)
        allow_phone_sentinel = (
            bool(introduced.get("phones"))
            and name_text.strip().lstrip("+").isdigit()
        )
        try:
            # Called for its RAISE behaviour; the repaired string is DISCARDED.
            NameValidator().validate_strict(
                name_text, allow_phone_sentinel=allow_phone_sentinel
            )
        except NameValidationError as exc:
            _refuse(exc.pattern, cause=exc)
        # On the accept path the name the caller handed us is emitted
        # byte-for-byte — `result` already carries it, untouched.

    # ---- 4. Addresses ------------------------------------------------------
    #
    # The list-shape precondition is evaluated FIRST, above every rule below and
    # above both migrations, and it is per-KEY rather than a whole-payload
    # bail-out.
    emails_ok = _shaped(introduced, "emails")
    phones_ok = _shaped(introduced, "phones")
    aliases_ok = _shaped(introduced, "aliases")

    if phones_ok:
        result["phones"] = _dedupe_phones(introduced["phones"])

    # Both migrations are PAIRWISE — M1 reads `aliases` and writes `emails`, M2
    # the reverse — so each runs only when BOTH its source and its destination
    # key pass. Where either fails, both keys pass through and the migration is
    # a no-op for this write.
    migrations = whole_record and emails_ok and aliases_ok

    if emails_ok:
        new_emails: list = []
        display_halves: list = []
        seen_emails: set = set()
        for entry in introduced["emails"]:
            address, display = split_address(entry)
            if address:
                if address.lower() not in seen_emails:
                    new_emails.append(address)
                    seen_emails.add(address.lower())
                if display:
                    display_halves.append(display)
            elif entry and entry.lower() not in seen_emails:
                # Not an address this package can parse — kept verbatim rather
                # than discarded.
                new_emails.append(entry)
                seen_emails.add(entry.lower())
        result["emails"] = new_emails

    # ---- 5. Migrations — only where the payload holds both fields ----------
    if migrations:
        new_aliases: list = []
        seen_aliases: set = set()
        for entry in introduced["aliases"]:
            address, display = split_address(entry)
            if address:
                # M1 — an alias that parses as an address moves to emails[],
                # guarded by the destination's own case-folded seen-set.
                if address.lower() not in seen_emails:
                    new_emails.append(address)
                    seen_emails.add(address.lower())
                if display and display.lower() not in seen_aliases:
                    new_aliases.append(display)
                    seen_aliases.add(display.lower())
            elif entry and entry.lower() not in seen_aliases:
                new_aliases.append(entry)
                seen_aliases.add(entry.lower())
        # M2 — the display half of an emails[] entry moves to aliases[],
        # guarded by its own seen-set.
        for display in display_halves:
            if display and display.lower() not in seen_aliases:
                new_aliases.append(display)
                seen_aliases.add(display.lower())
        result["aliases"] = new_aliases

    # ---- 6. Output ---------------------------------------------------------
    #
    # A NEW dict whose key set is exactly `introduced`'s. Every assignment above
    # is to a key `introduced` already carried, so this holds by construction.
    return result
