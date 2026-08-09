---
id: WI-017
title: "PersonRepository.create_stub: parse RFC 2822 sender strings before regex-sanitizing the name"
project: obsidian-schemas
stage: done
created: 2026-06-01
last_touched: 2026-07-05
stage_changed: 2026-06-01
touched_by: session
tags: [person-repository, sanitization, data-quality, root-fix, small-mechanical]
parent: null
depends_on: []
---

# `PersonRepository.create_stub`: parse RFC 2822 sender strings before regex-sanitizing the name

> Note on numbering: this is **WI-017 in the obsidian-schemas project**. The same surgery is referenced as "WI-103" in the orchestrator session that surfaced it, because each project numbers its own WIs independently and obsidian-schemas's next_id was 17 at capture time. The two IDs refer to the same work.

## Problem / Motivation

Surfaced during the 2026-06-01 orchestrator session reviewing duplicate `@*.md` person notes (WI-102 capture). Spot-checking `@David Agmen-Smith davidasspeechmaticscom.md` revealed corrupted frontmatter:

```yaml
type: person
name: David Agmen-Smith davidasspeechmaticscom        # ← mashed
aliases:
  - David Agmen-Smith <davidas@speechmatics.com>      # ← raw RFC 2822
emails:
  - David Agmen-Smith <davidas@speechmatics.com>      # ← sender string in email[]
```

The filename, the `name` field, and both `aliases[]` and `emails[]` all carry the same broken data. Tracing in `obsidian_schemas/repositories/person.py:380`:

```python
clean_name = re.sub(r'[^\w\s-]', '', name).strip()
```

This regex strips every character that's not `\w` (word char), `\s` (whitespace), or `-`. When the caller passes the raw email sender field (`"David Agmen-Smith <davidas@speechmatics.com>"`), the regex strips `<`, `>`, `@`, `.` — leaving `"David Agmen-Smith davidasspeechmaticscom"` as both the canonical name AND the filename. The original sender string also leaks into `aliases[]` (line 385: `aliases = [email] if email else []` — but `email` here is the caller-passed param, not the parsed-out email; if the caller passes nothing for `email`, aliases is empty, but if they pass the same full string for `email` too, it leaks).

**Empirical scope on production vault (2026-06-01):** 62 person notes have email-derived suffixes in their filenames (regex pattern: `\s+[a-z0-9]+(at)?[a-z]+(com|net|io|org|co|ai|de|fr|uk|us)\s*$` against the file stem). Each represents this same bug-class.

**Caller is also buggy** — passing the full RFC 2822 sender field to `create_stub(name=...)` instead of parsing it first. That's a separate fix in the orchestrator's scanners / contact-detector code. But the `obsidian-schemas` side should be defensive: the regex sanitizer was designed to strip filesystem-unsafe characters, not to handle RFC 2822 — and a defensive parse here protects against any current or future caller making the same mistake.

This is a real cause of duplicate person notes (WI-102 territory): when the same person sends a properly-parsed email next time, the system creates `@David Agmen-Smith.md` cleanly, leaving the corrupted variant as a sibling. So fixing this bug reduces future duplicate inflow.

## Verified diagnosis

| Claim | Verification artifact |
|---|---|
| `create_stub` regex strips `<`, `>`, `@`, `.` from `name` | `obsidian_schemas/repositories/person.py:380` — `re.sub(r'[^\w\s-]', '', name)` |
| Production vault has 62 corrupted person notes matching the pattern | regex `\s+[a-z0-9]+(at)?[a-z]+(com\|net\|io\|org\|co\|ai\|de\|fr\|uk\|us)\s*$` against `@*.md` stems in `/Users/davewascha/Documents/Obsidian/DaveRemoteVault` |
| Example file's frontmatter shows the leak in `name`, `aliases`, AND `emails` fields | `@David Agmen-Smith davidasspeechmaticscom.md` head-25 inspection |
| RFC 2822 parsing not happening anywhere upstream of `create_stub` | grep for `parseaddr\|email.utils\|<.*@.*>` in scanners / contact-detector roles returns nothing |

## Design

Pre-pipeline doc (built 2026-06, before the done-stage template): the design is carried by
`## Verified diagnosis` above and `## Approach` below — no separate Design section was written.

## Approach

Add a defensive parse step at the top of `create_stub` that detects the RFC 2822 form (`"Display Name <email@domain>"`) and splits it cleanly. Use Python's stdlib `email.utils.parseaddr` — battle-tested, handles edge cases (no display name, quoted display name, etc.).

```python
from email.utils import parseaddr

def create_stub(self, name: str, email: Optional[str] = None, ...) -> Person:
    # WI-017: defensive RFC 2822 parse — if `name` looks like
    # "Display Name <email@domain>" form, separate into display name
    # and email. Protects against any caller passing the raw sender
    # string from a scanner.
    parsed_name, parsed_email = parseaddr(name)
    if parsed_email and "@" in parsed_email:
        # parseaddr extracted an email — accept it
        if not email:
            email = parsed_email
        # Use the display-name part if present, else the local-part of the email
        name = parsed_name or parsed_email.split("@", 1)[0]

    # ... existing logic unchanged ...
```

### Why parseaddr, not a custom regex

- `parseaddr("Smith <a@b.com>")` → `("Smith", "a@b.com")` ✓
- `parseaddr("plain text")` → `("", "plain text")` — guard with `"@" in parsed_email` check ✓
- `parseaddr("a@b.com")` → `("", "a@b.com")` ✓ (caller passed an email as name; we recover)
- `parseaddr('"Doe, Jane" <jane@x.com>')` → `("Doe, Jane", "jane@x.com")` ✓ (quoted display name)
- `parseaddr("Phil")` → `("", "Phil")` — `"@" in parsed_email` is False, no-op ✓
- `parseaddr("+447739341679")` → `("", "+447739341679")` — phone as name (existing behaviour for phone-only stubs), `"@"` check fails, no-op ✓

The `"@" in parsed_email` guard is critical: `parseaddr` returns the *whole input* as the "email" slot when no `<...>` is present, which would incorrectly trigger our split for plain names and phone strings.

### What gets emitted to the file after the fix

For the David Agmen-Smith example (caller passes `name="David Agmen-Smith <davidas@speechmatics.com>"`, no `email` arg):

```yaml
name: David Agmen-Smith                                    # ← clean
aliases:
  - davidas@speechmatics.com                               # ← email is the alias source
emails:
  - davidas@speechmatics.com                               # ← actual email
```

Filename becomes `@David Agmen-Smith.md`.

## Edge cases (must all pass tests)

| Input `name` | Expected behaviour |
|---|---|
| `"David Smith <ds@x.com>"` | name="David Smith", email="ds@x.com" |
| `"<ds@x.com>"` | name="ds" (local-part fallback), email="ds@x.com" |
| `"ds@x.com"` | name="ds", email="ds@x.com" |
| `'"Doe, Jane" <jane@x.com>'` (quoted display name with comma) | name="Doe, Jane", email="jane@x.com" |
| `"+447739341679"` (phone-only stub) | name="+447739341679", email=None — **unchanged behaviour** |
| `"David Smith"` (plain name) | name="David Smith", email=None — **unchanged behaviour** |
| `"David Smith <ds@x.com>"` AND caller also passes `email="other@x.com"` | name="David Smith", email="other@x.com" — caller's explicit arg wins |
| `name=""` (empty string) | Existing fallback to `email.split("@")[0]` or "Unknown" preserved |
| `"David Smith <not-an-email>"` (broken angle brackets, no `@`) | `"@" in parsed_email` is False → no-op; existing regex sanitizer takes over |

## Out of scope (separate WIs)

1. **Upstream caller fix.** Scanners / contact-detector should parse sender fields before calling `create_stub`. Tracked in the orchestrator as a follow-on; this WI is the defensive layer in `obsidian-schemas` only.
2. **Retroactive repair of the 62 corrupted notes.** Worth its own disposable script (mirror WI-100 / WI-101 fix scripts) in `orchestrator/bin/repair-rfc2822-leaked-names.py`. Not in this WI's spec — caller-side; runs against a vault, not the library.
3. **Wider `name` validation.** Notes that aren't from RFC 2822 sources but still have weird characters in `name` (slashes, brackets) are out of scope. The defensive fix here targets one specific drift pattern.

## Implementation Plan

1. Write failing tests in `tests/test_repositories.py` per the Edge Cases table above. Each row → one parametrized test case. **Run them — they must fail on current state** (per WI-029 / workshop/WI-029 verification-artifacts-first discipline).
2. Apply the defensive parse to `create_stub` per the Approach section.
3. Run tests — must all pass.
4. Run the full `tests/test_repositories.py` — no regressions.
5. Commit with message describing the bug, the fix, and the test verification.

## Verification gates

- [ ] All 9 edge-case tests added
- [ ] All 9 tests FAIL on current `main` (verified before applying fix)
- [ ] All 9 tests PASS after applying fix
- [ ] No regressions in full `tests/test_repositories.py`
- [ ] No regressions in `obsidian-schemas` consumer projects: spot-check orchestrator's contact_normalizer.py and HAL9000's contact_resolver.py for any code that depends on the previous name-mangling behavior (unlikely — but verify)

## Related work

- **`orchestrator/WI-102` (idea, 2026-06-01)** — vault person-record dedupe. This WI's bug is a likely contributor to duplicate inflow; fixing it reduces future dedupe-load.
- **`orchestrator/WI-101` (idea, 2026-06-01)** — enricher YAML-bool drift. Different drift class but same surface (frontmatter writes). Both surfaced from the same session.
- **`workshop/WI-029` (idea, 2026-06-01)** — LLM-proposal verification-artifacts discipline. This spec is grounded in cited file:line + counted production data + a failing-test-first plan, per that discipline.
