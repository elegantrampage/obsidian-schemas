"""The five acceptance checks over the frozen fixture corpus (WI-016).

CORPUS_COUPLING: this module reads two files it did not author.
`docs/vault-shape-census.md` — three properties, one file, one digest: its
`census-class` and `census-pool` fence rows (AC-3, AC-5(c)), its whole byte
stream through `identity_tokens` (M1, Design §6.5), and its `sha256`, which is
asserted FIRST against the `CENSUS_DIGEST` literal declared in AC-3(iv) before
any row is trusted. `docs/vault-fixtures.md` — the AC-3 `criteria` fence, read
FENCE-SCOPED for that literal, and this document's five `check:` names, read
with `tests/test_ac_interpreter.py`'s shipped `criterion_checks`. Neither file
is selected by a proxy and neither is written here.

THIS MODULE IS DELIBERATELY OUTSIDE AC-5's REACH (`## Scope Boundary`): it
quotes refused fixtures, corruption specimens and pre-existing tree literals by
design, so an identity scan over it would be RED by construction. Its planted
literals are governed by hand instead — re-typing an identifier ALREADY
COMMITTED in this tree adds no personal data and is permitted; introducing a
NEW real-looking identifier is not.
"""

# FIRST, ahead of every package import: the conveyor may run this module's check
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI (WI-021; see
# `tests/ac_interpreter.py` for the failure this closes).
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

import fnmatch  # noqa: E402 — everything below runs only once the interpreter is right
import hashlib
import re
import unicodedata
from pathlib import Path

from obsidian_schemas.body_sections import ENTITY_BODY_CONFIG, get_default_body
from obsidian_schemas.errors import NameGateRefusal
from obsidian_schemas.models import TYPE_TO_MODEL
from obsidian_schemas.name_cleaning import _GENERIC_ORG_SUFFIXES, clean_person_name
from obsidian_schemas.name_validation import COMPANY_TIER1_BRANCHES, TIER1_BRANCHES
from obsidian_schemas.parser import parse_markdown_file
from obsidian_schemas.phone_normalization import normalize_phone, phones_match
from obsidian_schemas.repositories.base import BaseRepository, SKIP_REASONS
from obsidian_schemas.writer import write_markdown_file
from tests import fixture_vault
from tests import support
from tests.derivations import (
    PACKAGE_ROOT,
    TESTS_ROOT,
    python_files_under,
    skip_reason_literal_sites,
    skip_reason_return_values,
)
from tests.fixture_vault import (
    CONNECTIVE_SET,
    CORPUS_DIGEST,
    CORPUS_ROOT,
    IDENTITY_FIELDS,
    LOADABLE,
    NAME_POOL,
    NOTES,
    PROSE_ALLOWLIST,
    RESERVED_ISBN,
    RESOLVABLE,
    SKIPS,
    corpus_digest,
    materialize_vault,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CENSUS = REPO_ROOT / "docs" / "vault-shape-census.md"
WORK_ITEM_DOC = REPO_ROOT / "docs" / "vault-fixtures.md"


# --------------------------------------------------------------------------
# The census's machine surface (Design §2) — three fence kinds, flat key: value,
# every value on ONE line. A fence with an unrecognised key, a missing required
# key or a `status` outside the two-member vocabulary is a LOUD parse failure,
# never a skipped row.
# --------------------------------------------------------------------------

CLASS_REQUIRED = ("id", "count", "status", "command", "stdout")
CLASS_OPTIONAL = ("specimen", "ruling")
POOL_REQUIRED = ("token", "class", "command", "stdout")
META_REQUIRED = ("snapshot",)
STATUS_VOCABULARY = ("MEASURED", "ABSENT")


def _fence_bodies(text, kind):
    return re.findall(r"^```%s\n(.*?)^```" % re.escape(kind), text, re.S | re.M)


def _fence_rows(text, kind, required, optional=()):
    """Every `kind` fence of `text` as a dict, LOUD on any shape violation."""
    rows = []
    for body in _fence_bodies(text, kind):
        row = {}
        for line in body.splitlines():
            if not line.strip():
                continue
            if ": " not in line and not line.rstrip().endswith(":"):
                raise AssertionError(
                    f"{kind} fence carries a line that is not `key: value`: {line!r}")
            key, _, value = line.partition(": ")
            key = key.rstrip(":")
            if key in row:
                raise AssertionError(f"{kind} fence repeats key {key!r}")
            row[key] = value
        unknown = set(row) - set(required) - set(optional)
        if unknown:
            raise AssertionError(
                f"{kind} fence carries unrecognised key(s) {sorted(unknown)} — an "
                f"unknown key is a LOUD parse failure, never a skipped row")
        missing = set(required) - set(row)
        if missing:
            raise AssertionError(
                f"{kind} fence is missing required key(s) {sorted(missing)}: {row}")
        rows.append(row)
    return rows


def census_class_rows(text=None):
    text = CENSUS.read_text(encoding="utf-8") if text is None else text
    rows = _fence_rows(text, "census-class", CLASS_REQUIRED, CLASS_OPTIONAL)
    for row in rows:
        if row["status"] not in STATUS_VOCABULARY:
            raise AssertionError(
                f"census-class {row['id']!r} carries status {row['status']!r}, "
                f"outside the two-member vocabulary {STATUS_VOCABULARY}")
        if not re.fullmatch(r"\d+", row["count"]):
            raise AssertionError(
                f"census-class {row['id']!r} carries a non-integer count "
                f"{row['count']!r}")
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise AssertionError(f"census-class ids are not unique: {ids}")
    return rows


def census_pool_rows(text=None):
    text = CENSUS.read_text(encoding="utf-8") if text is None else text
    return _fence_rows(text, "census-pool", POOL_REQUIRED)


def census_meta(text=None):
    """The one header fence. `snapshot` is required; every other key is a
    free-form `vault_notes_<type>` count the reader ignores by design, so the
    conductor can record per-type totals without a paired spec edit."""
    text = CENSUS.read_text(encoding="utf-8") if text is None else text
    bodies = _fence_bodies(text, "census-meta")
    if len(bodies) != 1:
        raise AssertionError(
            f"expected exactly one census-meta fence, found {len(bodies)}")
    row = {}
    for line in bodies[0].splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(": ")
        row[key.rstrip(":")] = value
    missing = set(META_REQUIRED) - set(row)
    if missing:
        raise AssertionError(f"census-meta is missing {sorted(missing)}")
    return row


def declared_census_digest(doc=None):
    """The `CENSUS_DIGEST` value declared INSIDE the AC-3 `criteria` fence.

    FENCE-SCOPED and never file-wide: every gate section in that document quotes
    the criterion text it reviews, so a file-wide uniqueness read would go RED
    on a later quotation of the filled declaration and its only remedy would be
    editing a historical gate section.
    """
    doc = WORK_ITEM_DOC if doc is None else doc
    text = doc.read_text(encoding="utf-8")
    fences = re.findall(r"^```criteria\n(.*?)^```", text, re.S | re.M)
    ac3 = [f for f in fences if re.search(r"^id:\s*AC-3\s*$", f, re.M)]
    if len(ac3) != 1:
        raise AssertionError(
            f"expected exactly one AC-3 `criteria` fence in {doc.name}, "
            f"found {len(ac3)}")
    found = re.findall(r"CENSUS_DIGEST\s*=\s*sha256:([0-9a-f]{64})", ac3[0])
    if len(found) != 1:
        raise AssertionError(
            f"expected exactly ONE well-formed CENSUS_DIGEST declaration inside "
            f"the AC-3 criteria fence, found {len(found)} — a reader that finds "
            f"nothing is RED, never vacuously green")
    return found[0]


def assert_census_is_frozen():
    """AC-3(iv) / AC-5(c): the artifact both criteria treat as ground truth is
    frozen by digest, and the expected value lives in the SIGNED criterion —
    never in a constant this build owns, which would be updated in the same
    commit that edits the file it digests."""
    expected = declared_census_digest()
    actual = hashlib.sha256(CENSUS.read_bytes()).hexdigest()
    assert actual == expected, (
        f"{CENSUS.name} has changed since AC-3(iv) froze it: expected "
        f"{expected}, got {actual}. The census is the sole oracle for every "
        f"claim about the live vault this hermetic suite cannot re-derive; "
        f"correcting it is a conductor pass and a re-taken digest, never a "
        f"build-side edit.")


# --------------------------------------------------------------------------
# The identity-token extractor (Design §6.1). ONE object, driven by the live
# legs AND by Task 9's shape battery — never a second copy of the rule.
# --------------------------------------------------------------------------

def _runs(text):
    """Maximal contiguous spans over {Unicode letters, combining marks, ', -}.

    Bounded only by a character outside that class and NEVER restarted at an
    internal capital: `McDonald` is one run, and `zArchived` is one run that
    begins lowercase.
    """
    cur = []
    for ch in text:
        if ch in "'-" or unicodedata.category(ch)[0] in ("L", "M"):
            cur.append(ch)
        else:
            if cur:
                yield "".join(cur)
                cur = []
    if cur:
        yield "".join(cur)


def identity_tokens(text):
    """Every run whose FIRST character is an uppercase or non-ASCII letter,
    with leading and trailing `'` and `-` trimmed before comparison.

    The first character is read BEFORE trimming, so `-Voxleaf` yields nothing.
    """
    out = set()
    for run in _runs(text):
        first = run[0]
        if first.isupper() or ord(first) > 127:
            trimmed = run.strip("'-")
            if trimmed:
                out.add(trimmed)
    return out


# --------------------------------------------------------------------------
# Leg (a)'s three reserved-range predicates (Design §6.4). Each is ONE named
# function; the live leg and Task 9's battery drive the SAME objects.
# --------------------------------------------------------------------------

EMAIL_SHAPED = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
URL_SHAPED = re.compile(r"https?://[^\s\"'<>)]+")
PHONE_SHAPED = re.compile(r"[0-9+()\-. ]+")

RESERVED_EMAIL_DOMAINS = frozenset({"example.com", "example.net", "example.org"})
RESERVED_TLDS = (".test", ".invalid", ".example")
RESERVED_PHONE_PATTERNS = (
    re.compile(r"^447700900\d{3}$"),   # UK Ofcom drama block, international spelling
    re.compile(r"^07700900\d{3}$"),    # the SAME block, national spelling
    re.compile(r"^1?\d{3}55501\d{2}$"),  # NANP 555-01xx, optional country code
)


def _host_is_reserved(host):
    host = host.lower().rstrip(".")
    if host in RESERVED_EMAIL_DOMAINS:
        return True
    return any(host.endswith(tld) for tld in RESERVED_TLDS)


def reserved_email_violations(text):
    """Every email-shaped token whose domain is not RFC 2606 / RFC 6761."""
    return {m.group(0) for m in EMAIL_SHAPED.finditer(text)
            if not _host_is_reserved(m.group(0).rsplit("@", 1)[1])}


def reserved_url_violations(text):
    """Every URL-shaped token whose HOST is not under a reserved name. That is
    the concrete reading of AC-5(a)'s "declared placeholder form": the declared
    form IS "host under a reserved name", which reuses one rule rather than
    minting a second and cannot be padded."""
    out = set()
    for match in URL_SHAPED.finditer(text):
        url = match.group(0)
        host = url.split("//", 1)[1].split("/", 1)[0].split("@")[-1].split(":")[0]
        if not _host_is_reserved(host):
            out.add(url)
    return out


def reserved_phone_violations(text):
    """Every maximal `[0-9+()\\-. ]` span carrying ≥ 9 digits whose
    `normalize_phone` value matches none of the three reserved patterns.

    `RESERVED_ISBN` is the one author-declared exemption, asserted by EQUALITY
    against a one-member literal so it cannot be padded: an ISBN-13 is a
    13-digit run the phone predicate matches, an ISBN is not a phone, and there
    is no reserved ISBN range to move into.
    """
    out = set()
    for match in PHONE_SHAPED.finditer(text):
        span = match.group(0).strip()
        if sum(ch.isdigit() for ch in span) < 9:
            continue
        if span == RESERVED_ISBN:
            continue
        digits = normalize_phone(span)
        if not any(p.match(digits) for p in RESERVED_PHONE_PATTERNS):
            out.add(span)
    return out


def excise(text, literals):
    """Remove each declared literal from `text` before the span walk.

    By NAME and by equality, never by shape: excision by shape would let a
    builder spell any awkward run as hex. An excision of an absent substring is
    a no-op, which is why this runs over every file's text whether or not that
    file holds the literal.
    """
    for literal in sorted(literals, key=len, reverse=True):
        text = text.replace(literal, "")
    return text


def declared_hex_literals():
    literals = {CORPUS_DIGEST}
    literals |= {spec.raw_bytes_hex for spec in NOTES.values() if spec.raw_bytes_hex}
    restated = getattr(fixture_vault, "CENSUS_DIGEST", None)
    if restated:
        literals.add(restated)
    return literals


def reach_files():
    """AC-5's reach: every file under `tests/fixtures/vault/` PLUS the manifest
    module itself, which restates each specimen's field values as AC-2's
    declared oracle — a wall that scanned only the corpus would miss a real name
    typed into the oracle."""
    return sorted(p for p in CORPUS_ROOT.iterdir() if p.is_file()) + [
        TESTS_ROOT / "fixture_vault.py"]


# --------------------------------------------------------------------------
# The census's own ordinary technical vocabulary (M1, Design §6.5 item 3).
#
# NOT in the manifest: AC-5(b) is signed text and says `fixture_vault.py`
# declares THREE literal frozensets, naming them — a fourth there would make a
# signed sentence false. It is also the honest home, because this is a property
# of the ARTIFACT this module reads and not of the corpus the manifest declares.
#
# ITS MEMBERSHIP IS THE SCAN'S OWN RESIDUE OVER THE LANDED ARTIFACT, never
# §6.5's illustrative list: a token that cannot be placed as the census's
# technical vocabulary is M2's abort at Task 3 and a conductor pass, never a
# member added here to make a red go away.
# --------------------------------------------------------------------------

CENSUS_PROSE_ALLOWLIST = frozenset({
    # Section headings, prose sentence openers and emphasis caps.
    "A", "AC", "ABSENT", "ALL", "AT", "Attended", "BEFORE", "BRANCHES", "Branch",
    "Branch-backed", "C", "CERTIFIED", "CLI", "CONNECTIVE", "COUNT", "Class",
    "Conductor-performed", "Counter", "Design", "EMITS", "EXCLUDING", "EXTRACTS",
    "Each", "Empty", "Every", "Everything", "Excluding", "FILES", "FIRST",
    "Furniture", "GRANULARITY", "Hand-listed", "Header", "INCLUDED", "IS",
    "Identity", "In", "L", "LC", "LETTERS", "LIVE", "LONG", "LOWERCASE", "M",
    "MEASURED", "Machine", "Method", "Missing", "NAME", "No", "None", "ONE",
    "ONE-class-or-TWO", "ONE-or-TWO", "One", "POOL", "Path", "Person-name",
    "Precedents", "Prose", "RED", "RFC", "RULING", "Reconciliation", "SEPARATE",
    "SET", "Specimens", "THE", "TIER", "TWO", "Targets", "That", "The", "They",
    "This", "Tier", "Timeline", "Unicode", "V", "VAULT", "Vault", "WHOLE", "WI",
    "What", "Whole", "Whole-vault", "Write", "X",
    # Symbol names and tool vocabulary the Method section cites.
    "DaveRemoteVault", "Obsidian", "PersonRepository", "Python", "Templates",
    "Dave's", "Ofcom's", "DAVE", "ME", "Archived", "Contact", "Unknown",
    # Regex fragments and street-kind words quoted inside the scan commands.
    "A-Z", "A-Za-z", "Ave", "Avenue", "Close", "Dr", "Drive", "Lane", "Ln",
    "Place", "Rd", "Road", "Square", "St", "Street", "Way",
})


def census_identity_residue(text=None):
    """M1: every token `identity_tokens` yields over the census's WHOLE byte
    stream — prose and fences alike — that none of the four admissions covers.

    The four are the artifact's OWN pool table, `CONNECTIVE_SET`, the derived
    org-suffix set and `CENSUS_PROSE_ALLOWLIST`; the first three exactly as
    Design §6.2 admits them for the corpus's identity positions, so no new
    admission rule is minted.
    """
    text = CENSUS.read_text(encoding="utf-8", errors="replace") if text is None else text
    pool = {row["token"] for row in census_pool_rows(text)}
    return {t for t in identity_tokens(text)
            if t not in pool
            and t not in CONNECTIVE_SET
            and t.lower() not in _GENERIC_ORG_SUFFIXES
            and t not in CENSUS_PROSE_ALLOWLIST}


# --------------------------------------------------------------------------
# Task 2 — the skip-reason declaration and its binding.
# --------------------------------------------------------------------------

_BASE_PY = PACKAGE_ROOT / "repositories" / "base.py"


def _plant(root, name, source):
    path = Path(root) / name
    path.write_text(source, encoding="utf-8")
    return path


def test_skip_reason_declaration_binds_to_its_functions_returns():
    """AC-4's declaration leg: `SKIP_REASONS` is the codomain, bound to
    `_skip_reason`'s own returns by syntax so the export cannot drift into
    decoration, and the vocabulary's legal homes are closed by set EQUALITY."""
    # (a) the binding — equality, never containment, so the scan's own silent
    # under-read reports RED instead of passing green (LESSONS #46).
    assert skip_reason_return_values(_BASE_PY) == set(SKIP_REASONS), (
        f"_skip_reason's own returns {skip_reason_return_values(_BASE_PY)} do not "
        f"equal SKIP_REASONS {set(SKIP_REASONS)} — an arm added without a matching "
        f"frozenset member, or a return this scan cannot resolve")

    # (b) the derived population, asserted non-empty and against its size.
    assert SKIP_REASONS, "SKIP_REASONS resolved to an empty set"
    assert len(SKIP_REASONS) == 3, f"SKIP_REASONS holds {len(SKIP_REASONS)}, expected 3"

    # (c) THE ONE hand-typed spelling pin the vocabulary keeps. Once
    # test_loud_fail_load.py reads SKIP_REASONS, both sides of its comparison
    # move together and nothing else in the tree catches a rename of a value
    # consumers read off `SkippedNote.reason`. This is the second legal home the
    # W-15 wall names, and the one place a rename must be a deliberate edit.
    assert set(SKIP_REASONS) == {
        "malformed-frontmatter", "schema-drift", "unreadable"}

    # (d) the predicates driven over PLANTED source — the same objects the live
    # assertions call, never a re-implementation (WI-235).
    with support.temp_dir() as tmp:
        resolves = _plant(tmp, "resolves.py", (
            'ALPHA = "alpha-reason"\n'
            "\n"
            "def _skip_reason(error):\n"
            "    if error:\n"
            '        return "literal-reason"\n'
            "    for _ in range(1):\n"
            "        return ALPHA\n"
            '    return "tail-reason"\n'
            "\n"
            "def outer():\n"
            "    def _skip_reason(error):\n"
            '        return "nested-must-not-contribute"\n'
            "    return _skip_reason\n"
        ))
        assert skip_reason_return_values(resolves) == {
            "literal-reason", "alpha-reason", "tail-reason"}, (
            "the resolvable shapes are a literal return, a module-level str Name, "
            "two arms in one function, an arm under `if` and one under `for` — and "
            "a nested function of the same name must contribute nothing")

        for name, body, why in (
            ("local.py", "def _skip_reason(e):\n    v = 'x'\n    return v\n",
             "a local variable"),
            ("fstring.py", "def _skip_reason(e):\n    return f'{e}'\n", "an f-string"),
            ("subscript.py", "CHOICES = ['a']\ndef _skip_reason(e):\n"
                             "    return CHOICES[0]\n", "a subscript"),
        ):
            planted = _plant(tmp, name, body)
            try:
                skip_reason_return_values(planted)
            except AssertionError as exc:
                assert name.split(".")[0] in str(exc) or "cannot resolve" in str(exc)
            else:
                raise AssertionError(
                    f"skip_reason_return_values silently dropped {why} — an "
                    f"under-generating scan is green against the drift it exists "
                    f"to catch")

        # skip_reason_literal_sites: the shapes it MUST return...
        for name, body in (
            ("bare.py", 'x = "unreadable"\n'),
            ("collection.py", 'X = {"schema-drift": 1}\n'),
            ("argument.py", 'print("malformed-frontmatter")\n'),
            ("comparison.py", 'def f(r):\n    return r == "unreadable"\n'),
        ):
            planted = _plant(tmp, name, body)
            assert skip_reason_literal_sites([planted], SKIP_REASONS), (
                f"skip_reason_literal_sites missed a hand-typed member in {name}")

        # ...and the near-misses it must NOT return.
        for name, body in (
            ("comment.py",
             '# reason: "malformed-frontmatter" | "schema-drift" | "unreadable"\n'
             "x = 1\n"),
            ("docstring.py",
             '"""A sentence mentioning unreadable in running prose."""\n'),
            ("substring.py", 'x = "unreadable-permission"\n'),
            ("identifiers.py",
             "UNREADABLE = 1\nSCHEMA_DRIFT = 2\nMALFORMED_FRONTMATTER = 3\n"
             "y = (UNREADABLE, SCHEMA_DRIFT, MALFORMED_FRONTMATTER)\n"),
        ):
            planted = _plant(tmp, name, body)
            assert not skip_reason_literal_sites([planted], SKIP_REASONS), (
                f"skip_reason_literal_sites matched the near-miss in {name} — the "
                f"scan reads parsed SYNTAX precisely so a comment, a prose "
                f"docstring, a substring and an identifier are all invisible to it")

    # The LIVE set equality (Task 11): the vocabulary has exactly two legal
    # homes, and a fifth hand-typed site anywhere under the package or the suite
    # is RED with the file named. Its remedy is one import.
    homes = skip_reason_literal_sites(
        python_files_under(PACKAGE_ROOT, TESTS_ROOT), SKIP_REASONS)
    assert homes == {
        "obsidian_schemas/repositories/base.py",
        "tests/test_fixture_vault.py",
    }, (f"the skip-reason vocabulary is hand-typed outside its two declared "
        f"homes: {sorted(homes)}")


# --------------------------------------------------------------------------
# Task 4 — AC-1: the corpus is frozen and materialized by BYTE COPY.
# --------------------------------------------------------------------------

def _branch_ids():
    """The refusal-branch population, READ from the package's own exported
    declarations rather than transcribed here, and asserted non-empty and
    against its size at the moment of writing (LESSONS #46): a derived read
    returns green when it works and green when it silently reads nothing."""
    ids = {record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}
    assert ids, "the Tier-1 branch union resolved to nothing"
    assert len(ids) == 10, f"the branch union holds {len(ids)} ids, expected 10"
    return ids


def test_fixture_vault_is_frozen_and_materialized_by_byte_copy():
    """AC-1. (a) FROZEN, (b) FAITHFUL and idempotent-without-emptying,
    (c) THE DISCRIMINATOR — the corpus carries notes the write door refuses."""
    members = {p.name: p.read_bytes() for p in CORPUS_ROOT.iterdir() if p.is_file()}
    assert len(members) >= 50, (
        f"the corpus holds {len(members)} notes, fewer than the 50 AC-1 requires")
    assert set(members) == set(NOTES), (
        f"the manifest and the corpus disagree about membership: "
        f"on disk only {sorted(set(members) - set(NOTES))}, "
        f"declared only {sorted(set(NOTES) - set(members))}")

    # (a) FROZEN.
    assert corpus_digest() == CORPUS_DIGEST, (
        f"a fixture note has been edited, added or deleted without regenerating "
        f"CORPUS_DIGEST: expected {CORPUS_DIGEST}, got {corpus_digest()}")

    # (b) FAITHFUL — and the SECOND call is asserted too.
    with support.temp_dir() as tmp:
        dest = tmp / "vault"
        materialize_vault(dest)
        copied = {p.name: p.read_bytes() for p in dest.iterdir() if p.is_file()}
        assert copied == members, "materialize_vault did not reproduce the corpus"
        assert corpus_digest(dest) == CORPUS_DIGEST

        foreign = dest / "foreign-file.txt"
        foreign.write_bytes(b"a caller's own file\n")
        materialize_vault(dest)
        again = {name: (dest / name).read_bytes() for name in members}
        assert again == members, (
            "a second materialization did not overwrite every corpus member "
            "with identical bytes")
        assert foreign.exists() and foreign.read_bytes() == b"a caller's own file\n", (
            "materialize_vault emptied a caller-supplied directory — it ADDS, it "
            "never cleans, and a `shutil.rmtree(dest)` added for cleanliness "
            "would destroy a caller's data with every other criterion green")
        # The oracle here is the CORPUS MEMBERS and deliberately not
        # `corpus_digest(dest)`: the foreign file is a member of that tree and
        # not of the corpus.
        assert hashlib.sha256(b"".join(
            name.encode("utf-8") + b"\x00" + members[name] + b"\x00"
            for name in sorted(members))).hexdigest() == CORPUS_DIGEST

    # (c) THE DISCRIMINATOR. "NAMED as such in the manifest" is read off
    # `NoteSpec.discriminator` and NEVER off `shape_classes`: the landed census
    # rules both branches ABSENT, so folding them into `shape_classes` would put
    # two ABSENT ids on AC-3(i)'s MEASURED side and redden a correct corpus.
    named = {name: spec.discriminator for name, spec in NOTES.items()
             if spec.discriminator}
    assert set(named.values()) >= {"arrow_connective", "path_hostile"}, (
        f"the corpus names no arrow-connective and path-hostile discriminator: "
        f"{named}")
    ids = _branch_ids()
    for name, branch in named.items():
        assert branch in ids, (
            f"{name} declares discriminator {branch!r}, which is not a "
            f"`branch_id` the package declares — the field cannot be padded "
            f"with a free-text label")
        assert NOTES[name].shape_classes == (), (
            f"{name} is an AC-1(c) discriminator and must carry "
            f"`shape_classes = ()`; it carries {NOTES[name].shape_classes}")

    with support.temp_dir() as tmp:
        dest = materialize_vault(tmp / "vault")
        for name in named:
            assert (dest / name).read_bytes() == members[name], (
                f"{name} did not materialize byte-identically")
        # A build that materializes via the write door instead of copying bytes
        # is RED on exactly these members. The first argument is the note's own
        # FILE path (`writer.py:160-169`, `:205`), and the `frontmatter=` arm
        # reaches the gate at `writer.py:252-253` with
        # `declared_type=fm.get("type")`.
        out = tmp / "gated"
        out.mkdir()
        for name in named:
            spec = NOTES[name]
            payload = dict(spec.fields)
            try:
                write_markdown_file(out / name, frontmatter=payload)
            except NameGateRefusal:
                continue
            raise AssertionError(
                f"{name} was written through the gated door without refusal — "
                f"the corpus is materialized by BYTE COPY precisely because a "
                f"large share of its specimens are notes the WI-021/WI-022 gate "
                f"exists to refuse to create")


# --------------------------------------------------------------------------
# Task 5 — AC-2: the type-registry sweep.
# --------------------------------------------------------------------------

def _representative(entity_type):
    named = [name for name, spec in NOTES.items()
             if spec.roundtrip_representative and spec.declared_type == entity_type]
    assert len(named) == 1, (
        f"expected exactly ONE roundtrip_representative for {entity_type!r}, "
        f"found {named}")
    return named[0]


def _frontmatter_key(model_class, attribute):
    """`model_to_frontmatter` emits field ALIASES (`writer.py:112-117`), so
    `GiftIdea.for_person` survives as `for`."""
    info = model_class.model_fields.get(attribute)
    return info.alias if (info is not None and info.alias) else attribute


def test_every_entity_type_round_trips_against_declared_values():
    """AC-2. The population is READ from `TYPE_TO_MODEL`; the oracle is the
    manifest's HAND-WRITTEN declared values."""
    types = set(TYPE_TO_MODEL)
    assert types, "TYPE_TO_MODEL resolved to nothing"
    assert len(types) == 8, f"TYPE_TO_MODEL declares {len(types)} types, expected 8"
    covered = {spec.declared_type for spec in NOTES.values()
               if spec.declared_type is not None and spec.fields is not None}
    assert covered == types, (
        f"the corpus does not cover the type registry: missing "
        f"{sorted(types - covered)}, unknown {sorted(covered - types)}")

    with support.temp_dir() as tmp:
        dest = materialize_vault(tmp / "vault")
        written = tmp / "written"
        written.mkdir()
        for entity_type in sorted(types):
            model = TYPE_TO_MODEL[entity_type]
            name = _representative(entity_type)
            spec = NOTES[name]

            # GATE-CLEAN by the DOOR's own predicate, never by a transcribed
            # list of corruption forms.
            stored = spec.fields.get("name", "")
            if entity_type == "person":
                tripped = [r.branch_id for r in TIER1_BRANCHES if r.matches(stored)]
                assert not tripped, (
                    f"{name} is the person representative and trips {tripped}")
            elif entity_type == "company":
                tripped = [r.branch_id for r in COMPANY_TIER1_BRANCHES
                           if r.matches(stored)]
                assert not tripped, (
                    f"{name} is the company representative and trips {tripped}")

            # (a) PARSE.
            doc = parse_markdown_file(dest / name, model)
            assert isinstance(doc.entity, model), (
                f"{name} parsed to {type(doc.entity)!r}, expected {model!r}")

            # (b) ORACLE — hand-written values, compared by equality.
            for attribute, expected in spec.fields.items():
                assert getattr(doc.entity, attribute) == expected, (
                    f"{name}.{attribute} parsed to "
                    f"{getattr(doc.entity, attribute)!r}, declared {expected!r}")

            # (c) ROUND TRIP through the GATED door, then RE-PARSE and compare
            # the frontmatter MAPPING to the same declared oracle — never
            # byte-equality against the original, whose fixity is AC-1(a).
            write_markdown_file(written / name, entity=doc.entity)
            reparsed = parse_markdown_file(written / name, model)
            for attribute, expected in spec.fields.items():
                key = _frontmatter_key(model, attribute)
                assert key in reparsed.frontmatter, (
                    f"the write door dropped {key!r} from {name}")
                assert reparsed.frontmatter[key] == expected, (
                    f"{name}'s round trip changed {key!r}: "
                    f"{reparsed.frontmatter[key]!r} != {expected!r}")

    # THE NARROWING ARM, its population DERIVED rather than named.
    no_body_config = set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)
    assert len(no_body_config) == 3, (
        f"{len(no_body_config)} types have no body config, expected 3")
    for entity_type in no_body_config:
        assert get_default_body(entity_type) == "", (
            f"{entity_type} has no ENTITY_BODY_CONFIG entry, so the declared "
            f"marker is the empty string and no section list is invented for it")
    for entity_type in set(TYPE_TO_MODEL) & set(ENTITY_BODY_CONFIG):
        expected = ENTITY_BODY_CONFIG[entity_type]["sections"]
        body = get_default_body(entity_type)
        for section in expected:
            assert f"## {section}" in body, (
                f"{entity_type}'s default body is missing section {section!r}")


# --------------------------------------------------------------------------
# Task 6 — AC-3: the census reader and the class floor.
# --------------------------------------------------------------------------

def test_every_census_corruption_class_has_a_specimen_with_a_verdict():
    """AC-3. (iv) fixity FIRST, then (i) the both-directions equality over
    MEASURED rows, (ii) the per-row shape check conditional on status, and
    (iii) the class floor — branch half DERIVED, the six shape classes with no
    branch hand-listed because there is nothing to derive them from."""
    # (iv) CENSUS FIXITY, before any row of the table is trusted.
    assert_census_is_frozen()

    rows = census_class_rows()
    assert rows, "the census declares no class rows"
    by_id = {row["id"]: row for row in rows}
    measured = {row["id"] for row in rows if row["status"] == "MEASURED"}

    # (i) EQUALITY over MEASURED rows only, both directions. The manifest side
    # is the union of `shape_classes` over NOTES and reads NO other field — in
    # particular NOT `discriminator`, whose values name branches the census
    # rules ABSENT.
    declared = {c for spec in NOTES.values() for c in spec.shape_classes}
    assert declared == measured, (
        f"measured census classes with no specimen: {sorted(measured - declared)}; "
        f"specimens belonging to no measured class: {sorted(declared - measured)}")

    # (ii) PER-ROW SHAPE, conditional on status.
    for row in rows:
        count = int(row["count"])
        assert row["command"].strip(), f"{row['id']} carries an empty command"
        assert row["stdout"].strip(), (
            f"{row['id']} carries empty stdout — every recorded scan command "
            f"must emit a COUNT, so an honest zero records verbatim as `0`")
        if row["status"] == "MEASURED":
            assert count > 0, f"{row['id']} is MEASURED with count {count}"
            assert row.get("specimen", "").strip(), (
                f"{row['id']} is MEASURED and carries no specimen")
            assert "ruling" not in row, f"{row['id']} is MEASURED and carries a ruling"
        else:
            assert count == 0, f"{row['id']} is ABSENT with count {count}"
            assert row.get("ruling", "").strip(), (
                f"{row['id']} is ABSENT with no affirmative ruling")
            assert "specimen" not in row, (
                f"{row['id']} is ABSENT and carries a specimen — there is "
                f"nothing to specimen")

    # (iii) THE CLASS FLOOR. The branch half is a runtime read of the package's
    # own declarations, keyed on `branch_id` and NEVER on the deliberately
    # non-unique `pattern`; a branch added to either table later joins the floor
    # automatically. Both directions: a row naming a `branch_id` the package no
    # longer declares is RED rather than surviving as an ABSENT phantom.
    ids = _branch_ids()
    assert ids <= set(by_id), (
        f"the census declares no row for refusal branch(es) "
        f"{sorted(ids - set(by_id))} — a class measured at ZERO is a row the "
        f"conductor writes, not a row that may be omitted")
    branch_shaped = {row_id for row_id in by_id if row_id in ids}
    assert branch_shaped == ids, (
        f"branch-keyed census rows the package no longer declares: "
        f"{sorted(branch_shaped - ids)}")

    # The six shape classes with NO branch — the only hand-listed half, and the
    # only rows AC-3 reconciles against the census's own naming.
    shape_classes = {
        "diacritics", "hyphenated_surname", "whitespace_damage",
        "stem_name_divergence", "same_name_collision", "postal_address_in_name",
    }
    assert shape_classes <= set(by_id), (
        f"the census declares no row for shape class(es) "
        f"{sorted(shape_classes - set(by_id))}")

    # The declared VERDICT per MEASURED floor class. An ABSENT class has no
    # specimen and therefore no verdict to declare (§9.4 names `empty` as the
    # likely such row), so the qualifier is load-bearing rather than a hedge.
    with support.temp_dir() as tmp:
        out = tmp / "gated"
        out.mkdir()
        for name, spec in NOTES.items():
            if not spec.shape_classes:
                continue
            assert spec.verdict is not None, (
                f"{name} is the specimen of {spec.shape_classes} and declares "
                f"no Verdict")
            for shape_class in spec.shape_classes:
                assert by_id[shape_class]["status"] == "MEASURED", (
                    f"{name} declares {shape_class!r}, which the census rules "
                    f"{by_id[shape_class]['status']}")
            verdict = spec.verdict
            stored = spec.fields["name"]
            if verdict.kind == "refusal":
                try:
                    write_markdown_file(out / name, frontmatter=dict(spec.fields))
                except NameGateRefusal as exc:
                    assert exc.pattern == verdict.pattern, (
                        f"{name} was refused carrying pattern {exc.pattern!r}, "
                        f"declared {verdict.pattern!r}")
                else:
                    raise AssertionError(
                        f"{name} declares a refusal verdict and the write door "
                        f"accepted it")
            elif verdict.kind == "cleaned":
                assert clean_person_name(stored) == verdict.cleaned, (
                    f"clean_person_name({stored!r}) returned "
                    f"{clean_person_name(stored)!r}, declared {verdict.cleaned!r}")
            elif verdict.kind == "loads":
                doc = parse_markdown_file(CORPUS_ROOT / name, TYPE_TO_MODEL["person"])
                assert doc.entity is not None and doc.entity.name == stored, (
                    f"{name} declares a successful load and did not produce its "
                    f"declared name")
            else:
                raise AssertionError(
                    f"{name} declares Verdict.kind {verdict.kind!r}, outside the "
                    f"three-member vocabulary")

    # The header is read and its one required key asserted, so a census with no
    # snapshot is RED rather than silently trusted.
    assert census_meta()["snapshot"].strip()


# --------------------------------------------------------------------------
# Task 7 — AC-4: the skip surface, per repository.
# --------------------------------------------------------------------------

def _exported_repositories():
    """The concrete `BaseRepository` subclasses the package EXPORTS.

    The names `repositories/__init__.py` lists in `__all__`, FILTERED to
    concrete subclasses — never `BaseRepository.__subclasses__()`, whose answer
    depends on which modules happen to have been imported. The filter is what
    drops `VaultPathNotConfiguredError`, an exception rather than a repository.
    """
    from obsidian_schemas import repositories

    found = []
    for exported in repositories.__all__:
        obj = getattr(repositories, exported)
        if (isinstance(obj, type) and issubclass(obj, BaseRepository)
                and obj is not BaseRepository):
            found.append(obj)
    assert found, "the package exports no concrete BaseRepository subclass"
    assert len(found) == 4, f"{len(found)} repositories exported, expected 4"
    return found


def test_the_skip_surface_over_the_corpus_equals_its_declared_reasons():
    """AC-4. Every equality's DOMAIN is ONE repository, never a union across
    them: ownership is what decides whether a bad note is VISIBLE to the
    repository that would otherwise mint a duplicate for it."""
    assert skip_reason_return_values(_BASE_PY) == set(SKIP_REASONS)
    assert SKIP_REASONS and len(SKIP_REASONS) == 3

    union = {reason for mapping in SKIPS.values() for reason in mapping.values()}
    assert union == set(SKIP_REASONS), (
        f"the corpus declares no specimen for skip reason(s) "
        f"{sorted(set(SKIP_REASONS) - union)}; it declares unknown reason(s) "
        f"{sorted(union - set(SKIP_REASONS))}")

    with support.temp_dir() as tmp:
        dest = materialize_vault(tmp / "vault")
        repos = [cls(vault_path=str(dest)) for cls in _exported_repositories()]
        assert set(SKIPS) == {repo.type_name for repo in repos}, (
            f"the manifest declares skips for {sorted(SKIPS)}, the package "
            f"exports {sorted(repo.type_name for repo in repos)}")
        assert set(LOADABLE) == {repo.type_name for repo in repos}

        for repo in repos:
            repo.load()
            # (a) SKIPPED — both directions, per repository.
            observed = {note.path.name: note.reason for note in repo.skipped_notes}
            assert observed == SKIPS[repo.type_name], (
                f"{repo.type_name}'s skip surface is {observed}, declared "
                f"{SKIPS[repo.type_name]}")
            # (c) LOADED — the `get_all()` quantity, so a corpus whose malformed
            # members poison the surrounding load is RED rather than merely
            # under-reported.
            assert len(repo.get_all()) == LOADABLE[repo.type_name], (
                f"{repo.type_name} loaded {len(repo.get_all())} entities, "
                f"declared {LOADABLE[repo.type_name]}")

        # (b) THE PLANTED DISCRIMINATORS. An untyped specimen under EACH owning
        # glob, and book's mapping over the untyped classes asserted EMPTY —
        # the only assertion in the suite that the catch-all glob declines
        # ownership by design.
        untyped = {name for name, spec in NOTES.items()
                   if spec.declared_type is None}
        assert any(n.startswith("@") for n in untyped), (
            "no untyped specimen under the `@*.md` glob")
        assert any(n.startswith("Meeting ") for n in untyped), (
            "no untyped specimen under the `Meeting *.md` glob")
        assert not (set(SKIPS["book"]) & untyped), (
            f"book's declared mapping carries untyped specimens "
            f"{sorted(set(SKIPS['book']) & untyped)} — `*.md`'s stem is exactly "
            f"`*`, so `_owns(None)` declines every untyped failure")

        person = [r for r in repos if r.type_name == "person"][0]
        for query, expected in RESOLVABLE:
            resolved = person.resolve(query)
            assert resolved is not None and resolved.name == expected, (
                f"resolve({query!r}) returned "
                f"{resolved.name if resolved else None!r}, declared {expected!r}")


# --------------------------------------------------------------------------
# Task 8 — AC-5: the containment wall, and M1's scan over the census's bytes.
# --------------------------------------------------------------------------

def _stem_tokens(filename):
    """The filename stem, normalised per Design §1.2: strip a leading `@`,
    strip a leading `Meeting <digits> - ` prefix, drop the `.md` suffix."""
    stem = filename[:-3] if filename.endswith(".md") else filename
    stem = stem[1:] if stem.startswith("@") else stem
    stem = re.sub(r"^Meeting \d+ - ", "", stem)
    return stem


def _identity_text():
    """The three identity sources of Design §6.2, concatenated.

    1. every corpus filename stem, normalised;
    2. the manifest's declared values for that note's type's identity fields,
       read from `IDENTITY_FIELDS` — scalars contribute their own text, list
       fields each element, a wikilink the text inside `[[…]]` (which the run
       rule already yields, brackets being outside its character class);
    3. every value in every note's `undeclared` mapping — clause 3's
       `extra="allow"` default, with no manifest flag to opt out.
    """
    parts = []
    for name, spec in NOTES.items():
        parts.append(_stem_tokens(name))
        if spec.fields is not None:
            for attribute in IDENTITY_FIELDS.get(spec.declared_type, ()):
                value = spec.fields.get(attribute)
                if isinstance(value, (list, tuple)):
                    parts.extend(str(v) for v in value)
                elif value is not None:
                    parts.append(str(value))
        parts.extend(str(v) for v in spec.undeclared.values())
    return "\n".join(parts)


def _org_suffix_admitted(token):
    """READ from the package (`name_cleaning.py:58`) rather than declared here,
    so a builder looking for the cheapest green cannot pad it — and compared
    with `str.lower()`, the operation the package itself performs at `:148`,
    `:185` and `:191`, never `str.casefold()`."""
    return token.lower() in _GENERIC_ORG_SUFFIXES


def test_no_corpus_note_carries_a_live_identifier():
    """AC-5. Five legs over the corpus bytes PLUS the manifest module, which
    restates each specimen's field values as AC-2's declared oracle — then M1,
    which puts the census's own bytes inside the closure they certify."""
    assert_census_is_frozen()

    files = reach_files()
    texts = {path.name: path.read_text(encoding="utf-8", errors="replace")
             for path in files}
    union = "\n".join(texts.values())

    # ---- (a) RESERVED RANGES ------------------------------------------------
    # The named, author-declared hex exemption: asserted well-formed FIRST, then
    # asserted to occur SOMEWHERE IN THE REACH — once against the union of every
    # scanned file's bytes and never per file, because `CORPUS_DIGEST` and every
    # `raw_bytes_hex` live in the manifest BY §3's design and appear in no
    # corpus note at all.
    literals = declared_hex_literals()
    assert CORPUS_DIGEST in literals
    for literal in literals:
        assert re.fullmatch(r"[0-9a-f]+", literal), (
            f"declared hex literal {literal[:16]}… is not lowercase hex")
        assert len(literal) % 2 == 0, (
            f"declared hex literal {literal[:16]}… is of odd length")
        assert literal in union, (
            f"a hex literal is declared exempt but occurs NOWHERE in the reach: "
            f"{literal[:16]}… — an exemption for an absent literal is RED rather "
            f"than free, which is what stops it becoming a hiding place")
    assert len(CORPUS_DIGEST) == 64
    restated = getattr(fixture_vault, "CENSUS_DIGEST", None)
    if restated:
        assert len(restated) == 64

    for name, text in texts.items():
        # The EXCISION runs per file whether or not that file holds the literal
        # — an excision of an absent substring is a no-op. Without it this leg
        # is RED on a wholly correct corpus: printable ASCII hex-encodes to
        # first nibbles `2`–`7`, all digits, so `type:` alone yields the
        # nine-digit run `747970653`.
        scanned = excise(text, literals)
        assert not reserved_email_violations(scanned), (
            f"{name} carries an email outside RFC 2606 / RFC 6761: "
            f"{sorted(reserved_email_violations(scanned))}")
        assert not reserved_url_violations(scanned), (
            f"{name} carries a URL whose host is not reserved: "
            f"{sorted(reserved_url_violations(scanned))}")
        assert not reserved_phone_violations(scanned), (
            f"{name} carries a phone outside the reserved fictional ranges: "
            f"{sorted(reserved_phone_violations(scanned))}")

    # ---- (b) NAME CLOSURE, SPLIT BY POSITION -------------------------------
    # `CONNECTIVE_SET` is asserted equal to the literal written into AC-5(b), so
    # the set cannot grow without an AC change and is never a build-time choice.
    assert CONNECTIVE_SET == frozenset({"Me", "My", "Dave"})

    # The non-UTF-8 member is EXEMPT from the token scan and reviewed instead:
    # its complete bytes are declared in the manifest as a LOWERCASE hex literal
    # and asserted byte-equal.
    exempt = {name for name, spec in NOTES.items() if spec.raw_bytes_hex}
    assert len(exempt) == 1, (
        f"exactly one corpus member is not valid UTF-8; the manifest declares "
        f"raw bytes for {sorted(exempt)}")
    for name in exempt:
        declared_bytes = bytes.fromhex(NOTES[name].raw_bytes_hex)
        assert (CORPUS_ROOT / name).read_bytes() == declared_bytes, (
            f"{name}'s declared raw bytes do not match the file")
        try:
            (CORPUS_ROOT / name).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            pass
        else:
            raise AssertionError(
                f"{name} is declared as the non-UTF-8 member and decodes cleanly "
                f"— that is the only spelling of the `unreadable` class that "
                f"survives git")

    scanned_text = "\n".join(text for name, text in texts.items()
                             if name not in exempt)
    all_tokens = identity_tokens(scanned_text)
    id_tokens = identity_tokens(_identity_text())
    prose_tokens = all_tokens - id_tokens

    stray = {t for t in id_tokens
             if t not in NAME_POOL and t not in CONNECTIVE_SET
             and not _org_suffix_admitted(t)}
    assert not stray, (
        f"tokens in an IDENTITY position drawn from no certified pool: "
        f"{sorted(stray)} — the only way to green is the pool and the census's "
        f"provenance row, never the prose allowlist")

    loose = {t for t in prose_tokens
             if t not in NAME_POOL and t not in CONNECTIVE_SET
             and t not in PROSE_ALLOWLIST}
    assert not loose, (
        f"tokens in a free-prose position admitted by nothing: {sorted(loose)}")

    # THE DISJOINTNESS IS THE WALL: adding a surname to the allowlist buys
    # nothing whatsoever for a `name:` value, an alias, a title field or a stem.
    assert not (PROSE_ALLOWLIST & id_tokens), (
        f"PROSE_ALLOWLIST overlaps the identity token set at "
        f"{sorted(PROSE_ALLOWLIST & id_tokens)} — no token may hold both roles")

    # NON-VACUITY, `NAME_POOL` ONLY. "Somewhere in the reach" is deliberately
    # not the bar: a pool padded through a note body would satisfy it.
    unused = NAME_POOL - id_tokens
    assert not unused, (
        f"NAME_POOL declares tokens no IDENTITY position uses: {sorted(unused)}")

    # ---- (c) POOL PROVENANCE — a CONTAINMENT, one direction -----------------
    pool_rows = census_pool_rows()
    assert pool_rows, "the census declares no pool rows"
    pool = {row["token"] for row in pool_rows}
    assert NAME_POOL <= pool, (
        f"NAME_POOL carries tokens the census certifies for no live-vault "
        f"non-occurrence scan: {sorted(NAME_POOL - pool)}")
    for row in pool_rows:
        assert row["command"].strip(), f"pool row {row['token']!r} has no command"
        assert row["stdout"].strip(), f"pool row {row['token']!r} has no stdout"
    assert not (pool & CONNECTIVE_SET), (
        f"the census's pool table certifies connective furniture "
        f"{sorted(pool & CONNECTIVE_SET)} — a zero-hit row for one of those "
        f"would be a false statement inside the ledger whose whole job is to be "
        f"trustworthy")

    # ---- (d) THE PROPERTY IS NOT PAID FOR ----------------------------------
    for name, spec in NOTES.items():
        if spec.fields is None:
            continue
        for stored in spec.fields.get("phones", ()):
            digits = normalize_phone(stored)
            assert digits and digits.isdigit(), (
                f"{name}'s phone {stored!r} does not normalize to a digits-only "
                f"value (`phone_normalization.py:39-55` strips every non-digit; "
                f"the package emits E.164 nowhere and none is asserted)")
            national = "0" + digits[2:] if digits.startswith("44") else digits
            assert phones_match(stored, "+" + digits), (
                f"{name}'s reserved phone {stored!r} stopped matching its own "
                f"`+`-prefixed variant — the reservation must not cost the shape "
                f"the fixture exists to exercise")
            assert phones_match(stored, national), (
                f"{name}'s reserved phone {stored!r} stopped matching its "
                f"`0`-prefixed variant")

    # ---- (e) HERMETIC -------------------------------------------------------
    for name, text in texts.items():
        assert "/Users/" not in text, f"{name} carries an absolute user path"
        assert not re.search(r"(?<![\w.])/(?:Users|home|var|tmp|opt|etc)/", text), (
            f"{name} carries an absolute filesystem path — a fixture carrying "
            f"one is both a small leak and a note that means something "
            f"different on any other machine")
    with support.temp_dir() as tmp:
        dest = tmp / "vault"
        before = {p.name for p in tmp.iterdir()}
        materialize_vault(dest)
        after = {p.name for p in tmp.iterdir()}
        assert after - before == {"vault"}, (
            f"materialize_vault wrote outside the caller's dest: {after - before}")

    # ---- M1 — THE CENSUS'S OWN BYTES JOIN THE CLOSURE THEY CERTIFY ---------
    # The artifact this whole approach delegates its privacy ground truth to sat
    # outside every check in this document, including the one it grounds, so its
    # prose could carry a real live-vault name with everything green and two
    # signed criteria then asserting those bytes immutable.
    assert pool, "the census pool-row token set is empty — a reader that finds "\
                 "nothing admits everything"
    assert not (CENSUS_PROSE_ALLOWLIST & pool), (
        f"CENSUS_PROSE_ALLOWLIST overlaps the census's own certified pool table "
        f"at {sorted(CENSUS_PROSE_ALLOWLIST & pool)} — a name cannot be quietly "
        f"moved from the certified table into the allowlist")
    residue = census_identity_residue()
    assert not residue, (
        f"{CENSUS.name} carries identity-shaped token(s) its own pool table does "
        f"not certify: {sorted(residue)} — the remedy is a conductor pass, never "
        f"a member added here to make a red go away")


# --------------------------------------------------------------------------
# Task 9 — drive the claimed shapes through the predicates themselves (WI-235).
#
# AC-5's whole wall is a token count, and `matches == 0` is satisfied
# identically by an extractor that resolves every claimed shape and by one that
# resolves almost none. Every fixture below goes through the SAME function
# OBJECTS the live legs call, never a re-implementation and never a re-typed
# regex.
#
# On the planted literals: `## Scope Boundary` puts this module outside AC-5's
# reach, so nothing walls what is typed here and the rule is applied by hand.
# The NAME fixtures are the PACKAGE'S OWN declared specimens — `José García`,
# `Anne-Sophie Legrain`, `Dave -> Thomas Gatten`, `Me to David Field` and
# `zArchived - Rosie` are already committed in this tree — and the extractor's
# whole job is to resolve exactly the shapes this package declares, so a
# constructed substitute would test a shape the package does not have.
# Re-typing a literal already committed here adds no personal data; introducing
# a NEW real-looking identifier does not happen, which is why the email and
# phone fixtures below are constructed vocabulary and a reserved drama block.
# --------------------------------------------------------------------------

def test_the_identity_token_extractor_resolves_its_claimed_shapes():
    """Every shape AC-5(b) and §6.4 CLAIM, driven through the live predicates."""
    must_yield = {
        "McDonald": {"McDonald"},                 # one run, never Mc + Donald
        "Zeta-9": {"Zeta"},                       # the run is `Zeta-`, trimmed
        "José García": {"José", "García"},
        "Anne-Sophie Legrain": {"Anne-Sophie", "Legrain"},
        "Dave -> Thomas Gatten": {"Dave", "Thomas", "Gatten"},
        "Me to David Field": {"Me", "David", "Field"},
        "[[Voxleaf Kelmarra]]": {"Voxleaf", "Kelmarra"},
    }
    for text, expected in must_yield.items():
        assert identity_tokens(text) == expected, (
            f"identity_tokens({text!r}) returned {identity_tokens(text)!r}, "
            f"claimed {expected!r}")

    must_not_yield = {
        "d'Angelo": set(),                        # one run beginning lowercase
        "zArchived - Rosie": {"Rosie"},           # never `Archived`
        "zzArchived": set(),
        "-Voxleaf": set(),                        # first char read BEFORE trimming
        "447700900123": set(),
        "dave@example.com": set(),                # all-lowercase runs
    }
    for text, expected in must_not_yield.items():
        assert identity_tokens(text) == expected, (
            f"identity_tokens({text!r}) returned {identity_tokens(text)!r}, "
            f"claimed {expected!r}")

    # ---- leg (a)'s three predicates, and the near-misses that stop the
    # ---- narrowing swallowing the shapes it claims to keep.
    accepted_phones = [
        "+44 7700 900123",   # -> 447700900123, the international spelling
        "07700 900456",      # -> 07700900456, the SAME drama block, national
        "(415) 555-0123",    # -> 4155550123, NANP 555-01xx
        "+1 415 555 0199",   # -> 14155550199, the optional-country-code arm
    ]
    for value in accepted_phones:
        assert not reserved_phone_violations(value), (
            f"{value!r} normalizes to {normalize_phone(value)!r} and was scored "
            f"a violation — it is inside a reserved fictional range")

    refused_phones = [
        # ONE digit outside the drama block, and exactly the shape a `\\d{4}`
        # tail would have admitted: `+44 7700 901234` is live allocatable.
        "+44 7700 901234",
        "+44 20 7946 0958",
    ]
    for value in refused_phones:
        assert reserved_phone_violations(value), (
            f"{value!r} normalizes to {normalize_phone(value)!r} and was NOT "
            f"scored — the wall would then pass by matching everything")

    assert not reserved_email_violations("someone@example.com")
    assert not reserved_email_violations("someone@host.invalid")
    assert reserved_email_violations("t.kelmarra@voxleaf.co")
    assert not reserved_url_violations("https://example.org/books/drostane")
    assert reserved_url_violations("https://linkedin.com/in/someone")

    # ---- the excision is by NAME and by equality, never by shape.
    literals = declared_hex_literals()
    raw = [spec.raw_bytes_hex for spec in NOTES.values() if spec.raw_bytes_hex][0]
    for literal in (CORPUS_DIGEST, raw):
        assert not reserved_phone_violations(excise(literal, literals)), (
            "a declared hex literal survived the excision")
    # ...and it really did need excising: hex encodes printable ASCII to first
    # nibbles 2-7, all digits, so `type:` alone yields the run `747970653`.
    assert reserved_phone_violations(raw), (
        "the non-UTF-8 member's raw hex carries no phone-shaped run, so this "
        "battery would prove nothing about why §6.4 excises it")

    # The near-misses that prove the exemption cannot be padded: a ≥9-digit run
    # that is a PREFIX or SUFFIX of no declared literal is still scored, and a
    # lowercase-hex-shaped run that is not one of the declared literals is too.
    assert reserved_phone_violations(excise("123456789012", literals)), (
        "a bare twelve-digit run escaped the phone predicate")
    other_hex = "deadbeef" + "0" * 12
    assert other_hex not in literals
    assert reserved_phone_violations(excise(other_hex, literals)), (
        "a hex-SHAPED run that is not a declared literal was exempted — the "
        "excision is by name and by equality, never by shape")
    assert reserved_phone_violations(excise(CORPUS_DIGEST[:20] + "111111111", literals)), (
        "a run built from a PREFIX of a declared literal was exempted")


# --------------------------------------------------------------------------
# Task 12 — RUN every wall whose universe this item's files GROW, calling that
# wall's own shipped predicate on the final bytes rather than reasoning about
# which shapes match. Six rows: five shipped callables and one declared absence.
# --------------------------------------------------------------------------

def _item_test_modules():
    """This item's write targets that define top-level `def test_`."""
    return [
        TESTS_ROOT / "test_fixture_vault.py",
        TESTS_ROOT / "test_parser.py",
        TESTS_ROOT / "test_writer.py",
        TESTS_ROOT / "test_repositories.py",
        TESTS_ROOT / "test_loud_fail_load.py",
        TESTS_ROOT / "test_name_gate.py",
    ]


def _declared_pytest_python_files():
    """`[tool.pytest.ini_options] python_files` read from `pyproject.toml`.

    RAISES rather than defaults, and that is the point: `tomllib` is 3.11-only
    against this project's >= 3.10 floor and pytest ships no importable "would
    this path be collected" membership function, so the strongest available arm
    is to drive the CONFIG'S OWN declared values. A silent fallback to
    `test_*.py` would be a green over a config that moved.
    """
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    section = re.search(r"^\[tool\.pytest\.ini_options\]\s*$(.*?)(^\[|\Z)",
                        text, re.S | re.M)
    if section is None:
        raise AssertionError(
            "pyproject.toml declares no [tool.pytest.ini_options] section")
    entry = re.search(r"^python_files\s*=\s*\[(.*?)\]", section.group(1), re.S | re.M)
    if entry is None:
        raise AssertionError(
            "[tool.pytest.ini_options] declares no python_files key")
    globs = re.findall(r"[\"']([^\"']+)[\"']", entry.group(1))
    if not globs:
        raise AssertionError(
            "python_files is not a parseable bracketed list of quoted globs")
    return globs


def test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate():
    """§11's six GROWING rows, each RUN rather than reasoned about.

    The name says WHOSE walls it grades: `check_module` is a `def <name>(`
    SUBSTRING scan that raises on anything but exactly one match, and WI-022's
    `tests/test_name_gate_wall.py:1057` has held the generic name since that
    item shipped — so the collision is resolved from THIS side.
    """
    from tests.derivations import modules_using_ast
    from tests.test_ac_interpreter import check_module
    from tests.test_vault_path_required import (
        NO_ARG_CONSTRUCTION,
        _scanned_markdown_files,
    )

    universe = python_files_under(PACKAGE_ROOT, TESTS_ROOT)

    # W-1 AND W-2 in ONE call: W-2's row is the IDENTICAL live assertion re-run
    # from a second module, and re-typing it here would be the
    # re-implementation this task exists to forbid. The PROJECTION is part of
    # the call — `modules_using_ast` returns USE RECORDS, and the shipped wall
    # projects them as `{use.module for use in live}`.
    homes = {use.module for use in modules_using_ast(universe)}
    assert homes == {"tests/derivations.py"}, (
        f"the `ast` capability must stay single-homed to the shared scan "
        f"module; found {sorted(homes)}")

    # W-15, minted by this item: set EQUALITY over the vocabulary's legal homes.
    assert skip_reason_literal_sites(universe, SKIP_REASONS) == {
        "obsidian_schemas/repositories/base.py",
        "tests/test_fixture_vault.py",
    }

    # W-8 — the one wall the CORPUS itself joins, driven through the wall's OWN
    # generator and matcher. The non-vacuity clause comes first: without it
    # "zero offenders" is satisfied identically by a scan that never reaches the
    # corpus.
    scanned = list(_scanned_markdown_files())
    reached = {p.name for p in scanned if p.parent == CORPUS_ROOT}
    corpus = {p.name for p in CORPUS_ROOT.iterdir() if p.is_file()}
    assert reached == corpus, (
        f"the repo-wide markdown scan does not reach the whole corpus: "
        f"unreached {sorted(corpus - reached)}, unexpected {sorted(reached - corpus)}")
    for path in scanned:
        if path.parent != CORPUS_ROOT:
            continue
        # errors="replace" exactly as the shipped wall reads
        # (`test_vault_path_required.py:451`), which is what makes the
        # non-UTF-8 member safe here.
        text = path.read_text(encoding="utf-8", errors="replace")
        assert not NO_ARG_CONSTRUCTION.search(text), (
            f"corpus note {path.name} advertises no-arg construction")

    # W-14 — the ONE row with no callable predicate, declared LOUDLY rather
    # than skipped or quietly reasoned.
    globs = _declared_pytest_python_files()
    for path in CORPUS_ROOT.iterdir():
        for pattern in globs:
            assert not fnmatch.fnmatch(path.name, pattern), (
                f"{path.name} matches the collection glob {pattern!r}")
    for pattern in globs:
        assert not fnmatch.fnmatch("fixture_vault.py", pattern), (
            f"the manifest module matches the collection glob {pattern!r}; it "
            f"is not a check module and defines no test")
    # The near-miss control that stops the matcher passing by matching nothing.
    assert any(fnmatch.fnmatch("test_fixture_vault.py", p) for p in globs), (
        "no declared glob matches this module's own name — the matcher is "
        "passing by matching nothing")
    assert not (TESTS_ROOT / "conftest.py").exists(), (
        "tests/ gained a conftest.py; its absence is load-bearing (P2)")

    # W-10 — check-name uniqueness, DERIVED over every top-level `def test_`
    # this item's write targets define, read from those modules' own source at
    # test time and never from a list in the plan.
    for module in _item_test_modules():
        for name in re.findall(r"^def (test_\w+)\(", module.read_text(), re.M):
            resolved = check_module(name)
            assert resolved.name == module.name, (
                f"{name} resolves to {resolved.name}, not {module.name}")


def test_this_items_checks_pass_under_the_conveyors_interpreter():
    """W-16 closed by RUNNING it — the only thing that can prove §3.1's bridge
    is actually there, because the floor is green with or without it."""
    from tests.test_ac_interpreter import check_module, criterion_checks, run_foreign

    checks = criterion_checks(WORK_ITEM_DOC)
    assert len(checks) == 5, (
        f"expected 5 `check:` names inside this document's ```criteria fences, "
        f"found {len(checks)}: {checks} — a fence reader that finds nothing is "
        f"green (LESSONS #46)")

    failures = []
    for check in checks:
        module = check_module(check)
        proc = run_foreign(module, check)
        if proc.returncode != 0:
            failures.append(
                f"{check} ({module.name}) exited {proc.returncode}\n"
                f"--- stdout ---\n{proc.stdout[-2000:]}\n"
                f"--- stderr ---\n{proc.stderr[-2000:]}")
        elif "[ac_interpreter]" not in proc.stderr:
            # `-S` strips `site`, not an ambient or CI install, so exit 0 alone
            # is a wall-shaped no-op: on any interpreter where the runtime deps
            # survive `-S`, every check exits 0 having never delegated.
            failures.append(
                f"{check} ({module.name}) exited 0 WITHOUT delegating — the "
                f"foreign interpreter imported the project's deps, so this run "
                f"proves nothing about the battery's conditions")
    assert not failures, (
        f"{len(failures)} of {len(checks)} criteria fail under the conveyor's "
        f"interpreter:\n\n" + "\n\n".join(failures))


def test_a_nonexistent_check_is_red_under_the_conveyors_interpreter():
    """The near-miss control the shipped module carries, driven over THIS
    document's fences: the bridge must not pass by exiting 0 whatever the child
    did, and the failing run must be proven to have gone THROUGH the bridge."""
    from tests.test_ac_interpreter import check_module, criterion_checks, run_foreign

    module = check_module(criterion_checks(WORK_ITEM_DOC)[0])
    proc = run_foreign(module, "test_this_check_does_not_exist_anywhere")
    assert proc.returncode != 0, (
        f"a nonexistent check delegated to {module.name} exited 0 — the bridge "
        f"is reporting green for a run that proved nothing:\n{proc.stdout[-2000:]}")
    assert "[ac_interpreter]" in proc.stderr, (
        f"the failing run did not delegate, so it did not exercise the bridge:\n"
        f"{proc.stderr[-2000:]}")
