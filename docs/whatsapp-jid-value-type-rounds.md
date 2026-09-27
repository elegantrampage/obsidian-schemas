# Validate the WhatsApp JID shape at the person boundary — archived gate rounds

<!-- archive-split:v1 — IMMUTABLE APPEND-ONLY ARCHIVE. Written only by src/archive_split.py at a
completed conveyor transition; appended to, never edited, reordered or rewritten. It
carries no work-item frontmatter by design, so it is invisible to find_work_items and to
find_corrupt_work_item_docs. Living spec: docs/whatsapp-jid-value-type.md -->

## AC Red-Team — 2026-09-26

Round 1, no prior `ac-red-team` verdict on this document. Read in the prescribed order: `## Intent`,
`### Examples of done`, `## Problem / Motivation` and the exploration sections, then `##
Acceptance Criteria` last. Re-verified every code citation below at this worktree's HEAD
(`c93006a` plus the seeded uncommitted delta) rather than trusting the architect rounds' prior
reads.

The Intent's referent is narrow and testable: a value carrying a WhatsApp JID domain is
storable, a value that merely parses is not thereby storable, nothing already stored is dropped,
and resolution stays liberal. Measured against that referent, AC-1 through AC-4 hold up under
attack — the class table is derived by calling the two predicates rather than hand-listed, the
plants are named and unhoped-for (AC-1's negative-control lid, AC-3's required class-C literal at
every arm), and the anti-erasure and anti-projection legs (AC-3's two-directional `save` pin,
AC-4 leg (b) and leg (c)) each close a specific silent-corruption branch a builder could otherwise
ship. One AC does not survive the attack: AC-5's own oracle is unsatisfiable over the fixture the
same AC mandates.

**AC-5 — MATERIAL. The readback oracle in leg (c) raises an exception on the class-D member
leg's own fixture description requires it to plant, rather than passing or failing.**

Failure scenario: AC-5's desc requires the migration test's corpus be "planted with at least one
note per AC-1 class" — A, B, C, and D, where D is defined (AC-1, and `identifier.py:269-281`,
re-verified this round) as "does not parse": `WhatsAppJID.parse` raises `IdentifierError` for
`None`, empty, and any non-`@lid` string whose `normalize_phone` output carries fewer than
`Phone.MIN_DIGITS == 7` digits — e.g. `"n/a"`. Leg (c)'s oracle is stated as: "for every note, the
MULTISET of `WhatsAppJID.parse(v).key` over the post-migration values equals the multiset computed
from the pre-migration raw value or values." A test author implementing that sentence literally
calls `.parse(v).key` on the pre-migration raw value of every planted note, including the
mandatory class-D one — and `.parse("n/a")` raises. The oracle as worded cannot execute over its
own required fixture; it does not merely fail on a correct-vs-wrong build, it errors out before
either build gets judged. The document elsewhere states the CORRECT behavior for class D
elsewhere in the same AC ("A class-D value is never dropped and never rewritten — it is reported
as needing repair and left byte-identical") and in `## Approach` step (4) ("class D is reported
and left untouched"), but leg (c)'s oracle sentence itself does not say "over the parseable
values, with class D covered by byte-identical instead" — so the correct exclusion is nowhere
in the frozen criterion text a test author is meant to build against; it exists only as an
inference from other paragraphs plus the architect's round-2 note 3, which the AC text has not
absorbed. What changes: leg (c) needs its own sentence stating the multiset equality holds over
the PARSEABLE values only, with class D covered by the leg (a)/(e) byte-identical and
reported-and-left clauses instead of by the same oracle — the fix is one sentence, but it is a
frozen-AC-text fix, not a build-runner inference, because two honest implementers reading only
the criterion as currently worded would diverge on whether the readback check runs at all for a
corpus containing unrepaired junk (every real vault has some).

**AC-1 — MINOR, non-blocking. The four-class partition is not provably exhaustive over the
domain `parse` actually accepts, and the gap sits exactly on the `@lid` boundary the criterion
depends on for its guards.** `parse` tests for the SUBSTRING `"@lid"` anywhere in the value
(`identifier.py:276`), not a `@lid` suffix. A value like `"123@lid.example.com"` therefore parses
via that branch (`phone_digits == ""`), which is neither A nor C (both require non-empty
`phone_digits`); under the STORABLE predicate's stated closed set `{"s.whatsapp.net", "lid"}`
its domain (the text after the last `@`, i.e. `"lid.example.com"`) is not a member, so it is also
not storable, ruling out B (which requires storable). It parses, so it is not D either. This
input has no cell in the declared four-class table, so AC-1's "classification asserted exhaustive"
is false for it — a property-level assertion over arbitrary strings would find this counterexample;
an assertion scoped only to the planted exemplars would never see it and would go green while
silently leaving this slice of the input space unclassified. Not blocking on its own (the live
corpus has zero `@lid`-bearing values today per F6, so the population is very likely empty, and
the document's other guards — the independence assertion on `notaphone@s.whatsapp.net` — already
probe the adjacent boundary), but it is the same shape of gap AC-5 has, one level up: a criterion
claims a totality property the declared predicate table does not actually cover. What would have
to change: either state the table has a fifth (empty-by-construction) cell for "parses via `@lid`
substring, not storable" and assert it stays empty, or scope the "exhaustive" claim explicitly to
the domain the corpus and the plants exercise rather than to "every value."

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-26
model: claude-sonnet-5
note: AC-5 leg (c)'s readback oracle calls `WhatsAppJID.parse(v).key` over every planted note's pre-migration value, but AC-5's own fixture mandate requires a class-D (unparseable) note, which makes `.parse` raise rather than let the oracle pass or fail — the exclusion lives in other paragraphs, not in leg (c) itself.
targets: AC-5, AC-1
prior: none
basis: original
findings: 1/2
```


## AC Red-Team — 2026-09-26 (round 2)

Round 2 for this gate. Round 1 (above) found AC-5 leg (c)'s oracle unsatisfiable over its own
mandated class-D fixture and an AC-1 exhaustiveness gap at the `@lid`-substring boundary; both were
folded (class E entered the table, AC-1's classifier gained the no-fall-through assertion, AC-5 leg
(c) was rescoped to the parseable values). Re-verified this round rather than carried: `parse`'s
`@lid` branch runs before the digit test and `phone_normalization.py` splits at the first `@`
(re-read at `identifier.py:270-281`, `phone_normalization.py:52`), so the five-cell table is now an
actual partition of `parse`'s outcome space and AC-1's independence legs still hold on
`notaphone@s.whatsapp.net` (pinned at `tests/test_identifier.py:140`, re-read). **Round-1 findings:
HELD.**

Between round 1 and this round, the architect ran two further rounds on this same document (rounds
2 and 3, both present above). Round 3's blocking finding lands on `AC-3`/`AC-4`, inside my gate's
scope, and it is ORIGINAL text — the class table's placement of `""`/`None` under class D predates
every fold this document has undergone. I re-derived it independently rather than trusting the
architect's fence, because a defect two gates find the same way is stronger evidence than one gate's
say-so, and because my job is to attack the frozen criteria, not the other gate's prose.

**AC-3 / AC-4 — CRITICAL. AC-3, read literally, requires refusing the one value that is simultaneously the model default, the person template's value, 21 of 22 `whatsapp`-carrying fixture notes, and the only spelling this package has for "clear the field" — which makes the design's own promised repair path for classes C/D/E unbuildable, and the contradiction is invisible to every test AC-3 through AC-5 currently name.**

Failure scenario: a builder implements AC-3's desc exactly as worded — "Every write arm that can
introduce a `whatsapp` value refuses a value that is not STORABLE - classes C, D and E ... in BOTH
shapes, with nothing written." The class table (`## Exploration Notes`) lists `""` and `None` as
class-D exemplars alongside `"n/a"`, and I re-verified `WhatsAppJID.parse` treats them identically:
`identifier.py:273-275` — `if not s: raise IdentifierError(...)` — fires for `""` exactly as it does
for `"n/a"`; there is no branch that special-cases blank. So a `gate_write` arm built to AC-3's
letter refuses `whatsapp: ""` through every dict door with the same `pattern` and the same
"nothing written" guarantee it applies to `"n/a"`.

That build is self-consistent and passes AC-3 as drafted — AC-3 never names an empty-string case as
a required member at any arm, positive or negative, so nothing forces a test author to notice the
collision. It also passes AC-4(a) as drafted, because AC-4(a) is a READ-side assertion ("a note with
an empty value... present the empty collection") and the entity-shaped arms AC-4/AC-5 exercise never
construct a literal `""` payload for the gate to judge: with the stored field `List[str]` and a
model default of `[]` (`models.py:94` today; `[]` post-migration per the fold), `model_to_frontmatter`
emits `[]`, and an empty list has no member for a per-element arm to refuse — confirmed by re-reading
`writer.py:112-117`. Only the three dict arms (`writer.py:385`, `writer.py:443`, `base.py:728`) ever
receive a bare `""`, and none of AC-3's required members (`"+44 7739 341679"`, class-E's
`447700900456@lid.example.com`) is blank, so the whole AC-3 through AC-5 suite is green on a build
that refuses blank.

The break this produces is two-fold and both halves are load-bearing, not decorative: (1) Ruling B
leg 2 and AC-5 leg (e) both promise that the class-D/E residual is "reported and left for hand
repair" — but the package's only clearing doors are `update_frontmatter_field(path, "whatsapp", "")`
and `update_fields(person, {"whatsapp": None})` (re-verified: `writer.py:333-337` sets a field value,
there is no delete/remove affordance anywhere in the writer), and both hand the gate an empty or
`None` value, which a build honoring AC-3's letter refuses. The one repair channel the design commits
to elsewhere in the same document is therefore unbuildable under AC-3 as currently worded. (2) Any
producer that writes the template's own default — HAL9000's PATCH door clearing the field, `new-person`
minting a stub with `whatsapp` unset — starts being refused on the single most common value in the
corpus (21 of 22 `whatsapp`-carrying fixture notes per F6, re-verified by `rg -n -i 'whatsapp'
tests/fixtures/vault`), which is a materially larger consumer-visible break than the C+D+E population
the census precondition is scoped to measure.

This is the "mutually unsatisfiable ACs" failure class in the role's own hunt list: AC-3's literal
refusal population and AC-4(a)'s treatment of empty-as-absence, combined with Ruling B/AC-5's
repair-path promise, cannot all hold under one build, and no criterion states the resolving rule
("absent/empty/None introduces no identifier and is therefore never refused — the refused population
is the NON-empty unparseable/unstorable values") in the frozen text itself.

What would have to change (matches the fold the architect round-3 fence already proposes, verified
independently rather than copied): AC-3's desc needs one clause scoping its refusal population to
NON-EMPTY values that fail STORABLE, plus a new leg asserting that clearing the field (writing `""`
or `None`) through a delta arm SUCCEEDS even when the note's stored value is class C, D or E — since
that is precisely the hand-repair path AC-5/Ruling B depend on. The class table's D exemplars should
drop `""`/`None` (or the table should state explicitly that absence is a separate, always-accepted
case, matching `_project_identifiers`'s own `add()`, which returns on a None/blank raw before parsing
at all — re-verified at `person.py:318-320`). This is a frozen-AC-text fix, not a build-runner
inference: two honest implementers reading AC-3 as currently worded diverge on whether writing `""`
should succeed, and the criteria exist precisely so that question is not left to whoever builds first.

No other material defect survived this round's attack on AC-1, AC-2, AC-4(b)-(d), or AC-5(a)-(d):
the plants are named and unhoped-for, the anti-erasure and anti-projection legs each pin a specific
silent-corruption branch, the `check:` keys all name bare test function names a battery can discover,
and the empirical premises (F6's corpus count, the derivation citations) were re-run rather than
trusted this round.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-26
model: claude-sonnet-5
note: AC-3 read literally refuses `""`/`None` (class D) at every write arm, but that is the model default, the template value, and 21/22 fixture notes, and it is also the only spelling the package has for clearing a field — so the hand-repair path AC-5/Ruling B promise for the C/D/E residual is unbuildable, and no AC-3 through AC-5 test as drafted would ever exercise the collision; independently re-derived, converges with the architect's round-3 finding.
targets: AC-3, AC-4, #exploration-notes
prior: held
basis: original
findings: 1/1
```


## AC Red-Team — 2026-09-26 (round 3)

Round 3 for this gate. Rounds 1 and 2 (above) found AC-5 leg (c)'s oracle unsatisfiable over its
own mandated class-D fixture plus an AC-1 exhaustiveness gap (round 1, folded: class E entered the
table, AC-5 leg (c) rescoped to parseable values), and independently re-derived the class-Ø
contradiction between AC-3's refusal population and AC-4(a)'s empty-as-absence reading (round 2,
folded: class Ø entered the table as its own cell, AC-3 gained its CLEARING and CLASS-Ø legs).
Re-verified this round rather than carried: the current AC-3 desc now reads "THE CLEARING LEG...
THE CLASS-Ø LEG" with both asserted at every delta arm, and AC-5 leg (c) now reads "computed over
the PARSEABLE values ONLY" with the parseable split computed by calling `parse` and catching
`IdentifierError`. **Both prior rounds' findings: HELD.**

Between round 2 and this round, the architect ran a fourth round on this same document (present
above), landing two blocking findings on the fixture-plant plan that sit inside criteria this gate
signs off on — AC-1's `why:`, AC-3's required members, and AC-5's plant list. I re-derived both
independently against this tree's code rather than trusting the architect's fence, because my job
is to attack the frozen criteria text, not the other gate's prose, and because a defect two
decorrelated gates find the same way is stronger evidence than one gate's say-so. Both hold.

**AC-1 / AC-3 — CRITICAL. AC-1's own `why:` clause asserts `@Thrandell Ibberly.md` supplies class C
"for free," but that note is the corpus's sole `roundtrip_representative` for `person`, and two
in-tree tests already write it through the gated whole-record entity door asserting NO refusal —
so a build that correctly implements AC-3 makes both tests fail, and the self-consistent "fix" is
to delete the repo's only proof that a full person field set survives the write door.**

Failure scenario: I re-read `tests/fixture_vault.py:219-233` — `@Thrandell Ibberly.md` carries
`whatsapp="447700900789@example.com"` and `roundtrip_representative=True`.
`tests/test_fixture_vault.py:689-695`'s `_representative` helper asserts there is EXACTLY ONE such
note per `declared_type`, so this is not one specimen among several — it is the note. Two tests
then write that entity through `write_markdown_file(entity=…)`, the whole-record-projection arm
AC-3 itself names as a refusal surface: `tests/test_writer.py:404-428`, specifically line 421
(`write_markdown_file(out / name, entity=doc.entity, body=doc.body)`) followed by an assertion at
`:424-427` that every declared field — `whatsapp` among them — round-trips unchanged, with no
`NameGateRefusal` anywhere in the test; and `tests/test_fixture_vault.py:705-761`'s AC-2
type-registry sweep, which at `:726-732` asserts the person representative is "GATE-CLEAN by the
DOOR's own predicate." Under the STORABLE predicate's closed set `{"s.whatsapp.net", "lid"}`,
`447700900789@example.com` parses (phone-bearing, `phones_match` digits `447700900789`) and is NOT
storable — it is a class-C value by this document's own table. So a builder who implements AC-3's
"whole-record arms refuse classes C, D and E" correctly makes both of these tests raise
`NameGateRefusal` where they currently assert a clean round trip. The branch a builder reaches for
when the battery goes red is "the round trip now legitimately refuses, so change the test to expect
that" — a build that takes it is self-consistent and green on every AC in this set, and it silently
trades away the repo's only assertion that a whole person field set survives the write door, in
exchange for nothing this item asked for. AC-1's `why:` (`"the corpus supplies Ø (21 notes) and C
(`@Thrandell Ibberly.md:7`) for free"`) is the sentence that licenses this: it tells a spec-writer
the class-C member costs nothing to plant, when in fact planting it on THIS note costs the
round-trip representative's own invariant. What would have to change: AC-1's `why:` stops calling
Thrandell's value "free"; the representative's `whatsapp` moves to a value AC-3 accepts (class Ø or
a storable class-B `@lid`), and the class-C exemplar (`447700900789@example.com`, or an equivalent
wall-clean spelling) moves onto a plant on a non-representative note.

**AC-3 / AC-5 — MATERIAL. Two of the literal plant values these criteria require — the class-A and
class-E exemplars — cannot be planted inside the frozen fixture corpus's own reach without
violating the WI-016 privacy wall that same corpus enforces on itself, and neither AC nor `##
Exploration Notes` says where they go instead.**

Failure scenario: I re-read `tests/test_fixture_vault.py:302-319` — `RESERVED_EMAIL_DOMAINS =
{"example.com", "example.net", "example.org"}` is matched by EQUALITY, `RESERVED_TLDS = (".test",
".invalid", ".example")` by suffix, and `_host_is_reserved` accepts only those two routes; `reach_files()`
at `:386-392` scopes the check to every file under `tests/fixtures/vault/` plus
`tests/fixture_vault.py` itself. AC-3 names `447700900456@lid.example.com` as "a REQUIRED class-E
member at every arm," and AC-5 requires a plant for every non-Ø cell including class A (the
`## Exploration Notes` table's own exemplar for class A is `447700900123@s.whatsapp.net`). Neither
domain clears `_host_is_reserved`: `s.whatsapp.net` is not an exact member of the reserved set and
carries no reserved TLD, and `lid.example.com` is a SUBDOMAIN of `example.com`, which the equality
check does not match. A spec-writer who follows F6's own instruction ("the plant must KEEP
Thrandell's value" implies corpus-resident plants generally, and nothing in the document says
otherwise for A and E) and plants either literal as a fixture-corpus note makes the frozen corpus's
own privacy-wall leg fail — a test this document did not write and cannot touch, since `## Write
Targets` and the ACs treat the corpus's existing walls as fixed ground. There is no declared
exemption for either domain anywhere in this document (contrast `RESERVED_ISBN`, which the wall
already carries as a named, equality-pinned exception) — so the AC frame as currently worded is
unsatisfiable for these two cells by any build that keeps the corpus's privacy wall green, and the
class-D exemplar (`notaphone@s.whatsapp.net`) has the same problem IF it is ever planted in the
corpus rather than kept in a fresh test module's own literals, which AC-1's independence leg needs
it to be. What would have to change: state explicitly, in `## Exploration Notes` (F6) or in AC-1/
AC-3/AC-5 directly, that the class-A and class-E storable-form plants live in the new test module's
own temporary vault rather than the frozen corpus, and respell the class-E exemplar's domain to a
reserved-TLD-safe form (e.g. `447700900456@lid.example`) so it stays wall-clean while remaining the
same cell — a subdomain of a reserved TLD, still outside the closed set `{"s.whatsapp.net",
"lid"}`.

No other material defect survived this round's attack on AC-2 or on AC-4's legs (a)-(d): the
class-Ø round trip in AC-4(a) still meets AC-3's CLASS-Ø leg on the write side exactly as round 2's
fold intended, the anti-erasure and anti-projection legs still pin a specific silent-corruption
branch each, and the `check:` keys still name bare test function names. Rulings A, B and C are
untouched by both findings above — neither reopens a question for Dave; both are corrections to
this document's own fixture plan.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-26
model: claude-sonnet-5
note: AC-1's `why:` calls `@Thrandell Ibberly.md`'s whatsapp value a free class-C plant, but that note is the corpus's sole person round-trip representative and two tests write it through the gated whole-record door asserting no refusal — and separately, AC-3/AC-5's required class-A/class-E literals (`@s.whatsapp.net`, `@lid.example.com`) fail the frozen corpus's own privacy wall if planted in its reach; both independently re-derived, converge with the architect's round-4 findings.
targets: AC-1, AC-3, AC-5, #exploration-notes
prior: held
basis: folded-material
findings: 2/2
```


## AC Red-Team — 2026-09-26 (round 4)

Round 4 for this gate. Rounds 1-3 (above) found AC-5 leg (c)'s oracle unsatisfiable over its own
mandated class-D fixture (round 1, folded: class E entered the table, leg (c) rescoped to parseable
values), the class-Ø contradiction between AC-3's literal refusal population and AC-4(a)'s
empty-as-absence reading (round 2, folded: class Ø entered the table, AC-3 gained its CLEARING and
CLASS-Ø legs), and the fixture-plant-vs-frozen-corpus-contract collisions on the round-trip
representative and the privacy wall (round 3, folded, converging independently with the architect's
round 4). Re-verified this round rather than carried: AC-3's desc now reads "THE CLEARING LEG...THE
CLASS-Ø LEG" asserted at every delta arm, AC-5 leg (c) reads "computed over the PARSEABLE values
ONLY" with the split computed by calling `parse` and catching `IdentifierError`, and AC-1's WHERE
clause now pins the representative to the storable class-B value `15555550142@lid` with the class-C
member moved to a non-representative note. **All three prior rounds' findings: HELD.**

Between round 3 and this round, the architect ran a fifth round (present above), finding that
`### Effort` item (iv) and F6's third amendment price a `docs/vault-shape-census.md` row as a free,
build-side cost when that file's digest is pinned inside WI-016's own SIGNED AC-3 criterion and its
row vocabulary has no cell a `whatsapp` value could occupy. I re-read `tests/test_fixture_vault.py:217-254`,
`:789` and `:1031`, and `docs/vault-fixtures.md:1418`, and the citation holds: `declared_census_digest()`
reads `CENSUS_DIGEST` out of `vault-fixtures.md`'s own frozen `AC-3` fence, and `census_class_rows`'
ids are name-corruption `branch_id`s or the six hand-listed shape classes, none of which fits a
parses-but-not-storable JID. It is not yet folded — F6's third amendment and `### Effort` item (iv)
still state it. That finding lives in `## Exploration Notes` and `### Effort`, not inside a `criteria`
fence, so it is the architect's cost-accounting turf rather than a gameable-AC defect in my own hunt
list; I record it here as verified-and-still-open rather than re-deriving it as my own finding, and
turn to what my own attack on the frozen criteria text found.

**AC-5 — MATERIAL. The one plant AC-5 requires beyond the six-cell sweep — "one note carrying TWO
JIDs" — is the only required member in the whole criterion with no pinned literal, in the one
document that already spent a finding (F17 leg 3) proving that reusing digits across two plants in
the same materialized vault mints a silent, non-red identifier conflict.**

Failure scenario: I re-read AC-5's desc in full. Every other required plant gets a hard-pinned,
reserved-block-safe value: class A is `447700900321@s.whatsapp.net`, class E is
`447700900654@lid.example`, class B is `15555550142@lid` (on the representative), class C is
`447700900789@example.com` (moved to a non-representative note), class D is digit-less junk per
AC-1. The "note carrying TWO JIDs (a phone-bearing one and an `@lid`)" is required by the same
sentence and named nowhere else — I grepped the whole document for "TWO JIDs" / "second JID" and
every other hit is `## Approach`'s back-out prose (F14), never a fixture value — so it pins no
literal at all. A test author who reaches for the values already printed two sentences earlier to
build "a phone-bearing one and an `@lid`" — e.g. `447700900321@s.whatsapp.net` for the phone half and
`15555550142@lid` for the lid half — plants a SECOND entity in the same materialized copy holding the
exact same `phone:447700900321` and/or `jid:15555550142` keys as the class-A plant and the
representative. That is verbatim the class-A-reused-Thrandell's-digits mechanism F17 leg 3 already
found and priced: `_index_identifiers` (`person.py:336-366`) does not raise on the collision — the
document's own words for this exact mechanism are "it would not go red, it would just be wrong" — so
AC-5's own readback oracle (the `.key` multiset per note, the criterion whose entire point is proving
"no identifier moved") is exercised against an ambiguous or wrong index for that note, silently. I
re-ran the digit predicate this round (`rg -n '7700 ?900\d{3}|55501\d{2}'` over `tests/fixture_vault.py`
and `tests/fixtures/vault/`): the only claimed runs are `447700900123`, `447700900456` and
`447700900789`, and the only new ones this document mints are `447700900321`, `447700900654` and
`15555550142` — confirming both that the document's own accounting is accurate and that no fourth
unused run is named for the seventh plant, so the failure mode is a builder copying an EXISTING run
rather than being pointed at an unused one.

What would have to change: AC-5's desc needs its own pinned pair of digits for the two-JID note — an
unclaimed member of the drama block or NANP 555-01xx, distinct from all five runs already spent —
exactly the discipline every other required member in this same criterion already gets, and exactly
what the conductor's "sweep the next level... against the same walls" instruction already asked this
document to do for every literal it names. This is a frozen-AC-text fix, not a build-runner inference:
the fixture cost of pinning one more unused pair is free, but leaving the pair unstated invites the
one mistake this document has already spent a finding closing.

No other material defect survived this round's attack on AC-1 through AC-4: the six-cell classifier's
ordering and no-fall-through assertions still hold against the current text, the anti-erasure and
anti-projection legs on `save`/`write_markdown_file(entity=…)` still pin both directions, the
CLEARING and CLASS-Ø legs still make the D+E hand-repair path exercised rather than merely promised,
and the `check:` keys all still name bare, discoverable test functions. F6's and F17's corpus counts
were re-run rather than trusted: `rg -n -i 'whatsapp' tests/fixtures/vault` returns 22 lines (21
`whatsapp: ""` plus Thrandell's), and `rg -c '^type: person' tests/fixtures/vault` returns 25,
matching the document's "22 of the 25" claim exactly. Rulings A, B and C are untouched by the finding
above; it is a correction to AC-5's fixture plant, not a question for Dave.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-26
model: claude-sonnet-5
note: AC-5 requires a plant "note carrying TWO JIDs" but, alone among that criterion's required members, pins no literal for it — so a test author reusing the already-printed class-A/class-B digits (447700900321, 15555550142) mints the exact silent identifier conflict F17 leg 3 already found and priced ("it would not go red, it would just be wrong").
targets: AC-5
prior: held
basis: original
findings: 1/1
```


## AC Red-Team — 2026-09-26 (round 5)

Rulings on record:
Rulings A, B and C stay Dave's, unchanged by everything below; none of it reopens a question for him.

Round 5 for this gate. Rounds 1–4 (above) found, and folds closed: AC-5 leg (c)'s oracle unsatisfiable
over its own mandated class-D fixture (round 1); the class-Ø contradiction between AC-3's literal
refusal population and AC-4(a)'s empty-as-absence reading (round 2); the fixture-plant collisions with
the round-trip representative and the privacy wall (round 3, converging with the architect's round 4);
and AC-5's unpinned two-JID literal (round 4). Re-verified this round rather than carried: AC-1's WHERE
clause still pins the representative to `15555550142@lid` with the class-C member on a non-representative
note; AC-5's desc still pins `447700900987@s.whatsapp.net`/`15555550163@lid` for the two-JID plant, and I
grepped the tree for both runs (`rg -n '900987|5550163'`) and found them nowhere outside this document.
**All four prior rounds' findings: HELD.**

Between round 4 and this round, the architect ran a sixth round (present above), finding that F9's "the
linter's report surface comes free" is false: `_gate_refusal_pattern` has exactly one call site in
`scripts/lint_vault.py`, and it sits behind `stem_name_divergence`'s `stem != stored` guard rather than
behind anything that reads `whatsapp`. I re-derived this independently against the tool's source rather
than trusting the architect's fence, because my job is to attack what the frozen criteria text currently
asserts, not the other gate's prose.

**AC-3 — CRITICAL. AC-3's closing clause asserts a repair-visibility guarantee that the cited function
cannot deliver, and the promise it breaks is made in five places outside the criteria fence, none of
which a builder reading only `## Acceptance Criteria` would think to check.**

Failure scenario: I read `scripts/lint_vault.py:334-352` (`_gate_refusal_pattern`'s definition) and
`rg -n '_gate_refusal_pattern' scripts/lint_vault.py`, which returns exactly two lines — the `def` and one
call, at `:450`. That call sits inside `check_structural`'s `stem_name_divergence` arm
(`:433-462`), gated on `vf.entity_type == "person"` (`:433`) AND `isinstance(stored, str) and
stored.strip() and stem != stored` (`:449`) — a filename/stored-name divergence, nothing to do with
`whatsapp`. Its return value is spliced into that ERROR's message as a marker (`:451-454`); it emits no
`LintIssue` of its own, and none of the five check functions I read (`check_structural` at `:355`, and
the four others at `:496`, `:577`, `:698`, `:798`) names `whatsapp` at all (`rg -n 'whatsapp'
scripts/lint_vault.py` → 0 matches, re-run this round). I then read
`docs/stem-divergence-live-baseline.md:191`, which the architect cites for the live population of that
arm: `divergent live person notes | 8 | 0` — WI-029 closed it five days before this item was minted. So
on the vault as it stands, the one route into `_gate_refusal_pattern` is taken zero times.

AC-3's own desc closes with: "one consequence pinned where it is FREE - `lint_vault` REPORTS such a note
through `_gate_refusal_pattern` under that distinct pattern, and `--fix` still repairs the note's other
issues." That sentence is the only place in `## Acceptance Criteria` that names the linter at all, and it
states a false fact about a function it does not ask any `check:` to exercise — there is no fifth or sixth
criterion, and no leg of AC-1 through AC-5, that asserts a note carrying a class-C/D/E `whatsapp` value
produces ANY lint output. A builder who reads AC-3 literally has nothing to build here: the clause reads
as already-true scenery, not as a requirement, because it is phrased as a consequence rather than an
assertion with a `check:` behind it. That is a stronger form of the role's own "an AC whose check cannot
execute" failure class — this is a clause with no `check:` attached to it AT ALL, riding on the coattails
of AC-3's `check: test_whatsapp_refusal_at_every_derived_write_arm`, which tests refusal at the write door
and has no reason to also assert anything about `scripts/lint_vault.py`.

The promise the clause licenses is made five times outside the criteria fence — `## Intent` ("A value
that is already wrong is reported and left, never erased"), F13 leg 3 ("both reported by the linter and
left for hand repair"), Ruling B leg 2, AC-5 leg (e) ("reported as needing repair"), and `### Examples of
done` ("the linter names it instead of nobody noticing until a hand repair") — and every one of them cites
AC-3's clause as the mechanism, not a claim any `check:` in this set verifies. Three self-consistent builds
satisfy every named `check:` in `## Acceptance Criteria`: leave `scripts/lint_vault.py` untouched (green,
residual silent); widen the existing `stem_name_divergence` marker to fire on a non-storable `whatsapp`
(green, and it also puts a false statement into that marker's own text — "repair the field" — for a
divergence whose actual defect is a filename, and it would flip WI-029's own zero-row bracket back toward
nonzero for the wrong reason); or add a real report-only detector (the only one that keeps the promise,
and the one the touch list does not price — `### Effort` lists `scripts/lint_vault.py` as "(pattern
routing only)"). Nothing in the frozen criteria distinguishes the first two from the third.

What would have to change: AC-3 needs its own `check:`-backed assertion — a new report-only detector in
`scripts/lint_vault.py` fires on a class-C/D/E `whatsapp` value under its own check name, never under
`stem_name_divergence`'s marker, and `auto_fixable` stays at its default so `--fix`'s delta-only contract
is untouched — rather than a prose clause riding on AC-3's write-door test. This is a frozen-AC-text fix
and not a build-runner inference: the sentence as worded is satisfied by silence, which is exactly the
"pinned where it is free" framing that told a spec-writer (and, on this round's evidence, three prior
gate rounds before this one) that nothing needed checking here.

No other material defect survived this round's attack on AC-1, AC-2, AC-4, or AC-5's other legs: the
five `check:` names remain globally unique (`rg` for each of the five function names over the whole tree
returns zero matches outside this document, re-run this round), the class table's ordering and
no-fall-through assertions still hold, and the anti-erasure/anti-projection legs on `save`/
`write_markdown_file(entity=…)` still pin both directions. Rulings A, B and C are untouched by the finding
above; it is a correction to AC-3's closing clause, not a question for Dave.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-26
model: claude-sonnet-5
note: AC-3's closing clause asserts `lint_vault` reports a class-C/D/E `whatsapp` value "where it is free," but `_gate_refusal_pattern` has one call site, gated on filename/stored-name divergence rather than on anything reading `whatsapp` (confirmed independently at `scripts/lint_vault.py:334-352`, `:449-450`), and no criterion's `check:` exercises the claim — so the report promise made in Intent, F13 leg 3, Ruling B leg 2, AC-5 leg (e) and Examples of done rides on a sentence with no test behind it; converges with the architect's round-6 finding.
targets: AC-3, #intent, #exploration-notes
prior: held
basis: original
findings: 1/1
```


## AC Red-Team — 2026-09-26 (round 6)

Rulings on record:
Rulings A, B and C stay Dave's, unchanged by everything below; none of it reopens a question for him.

Round 6 for this gate. Rounds 1–5 (above) found, and folds closed: AC-5 leg (c)'s oracle
unsatisfiable over its own mandated class-D fixture (round 1); the class-Ø contradiction between
AC-3's literal refusal population and AC-4(a)'s empty-as-absence reading (round 2); the
fixture-plant collisions with the round-trip representative and the privacy wall (round 3,
converging with the architect's round 4); AC-5's unpinned two-JID literal (round 4); and AC-3's
closing clause asserting a linter report surface with no `check:` behind it (round 5, converging
with the architect's round 6). Re-verified this round rather than carried: AC-1's WHERE clause
still pins the representative to `15555550142@lid` with the class-C member on a non-representative
note; AC-5's desc still pins the two-JID literals and the class-D/E plant guards; AC-3's desc still
carries THE REPORT LEG's five assertions and names both surfaces in its `check:`. **All five prior
rounds' findings: HELD.**

Between round 5 and this round, the architect ran a seventh round (present above), finding that
`PersonRepository.save`'s docstring is a prose fixture frozen by WI-024's `test_identity_endgame.py`
wall, that `save` is not among its thirteen authorized owners, and that F11's write-back disclosure
and `### Examples of done`'s refusal disclosure both point at exactly the frozen lines. I re-derived
this independently against the wall's own source rather than trusting the architect's fence, because
my job is to attack what the frozen criteria text currently asserts, not the other gate's prose: I
read `person.py:1155–1200` directly — the write-back at `:1192–1194` sets `entity.emails`,
`entity.phones`, `entity.aliases` and nothing else, and the docstring at `:1174–1178` and `:1180–1184`
states that enumeration and the `phones[]` in-place-mutation disclosure in the exact words the
architect cites. I then read `tests/test_identity_endgame.py:359–373`, confirming
`AUTHORIZED_PROSE_OWNERS` is the thirteen-member list with no `PersonRepository.save` entry, and
`:995–1030`, confirming clause (e1) requires every Cut-0 line of an unauthorized owner to survive
VERBATIM in the final text (compared on `(owner, text)`, so an append is free but an edit or deletion
of an existing line is not) while clause (e2) requires an AUTHORIZED owner to lose at least one
Cut-0 line — the two clauses that make Build B (authorizing `save`) cost a mandatory deletion. The
citations hold exactly as the architect states them.

**AC-3 — MATERIAL. AC-3's `save` arm names `person.py:1180–1184` as the model for this item's
write-back disclosure, but no leg of AC-1 through AC-5 asserts that the disclosure must be added
APPEND-ONLY against a prose surface `test_identity_endgame.py` freezes — so a builder who reads
AC-3's `why:` and reaches for the shortest edit that keeps the citation accurate can satisfy every
named `check:` in this set while landing on one of two builds that break another item's frozen
wall or silently drop this item's own disclosure promise.**

Failure scenario: `## Approach` step (2) and AC-3's `why:` both instruct that "the same class of
disclosure WI-021 made for `phones[]` (`person.py:1180-1184`)" is the model for stating that
`save`'s write-back has grown a field, and `### Examples of done` promises of the refusal surface
that "it says so." A builder extending that exact paragraph in place — the natural reading of
"the same class of disclosure" as "edit the paragraph that already carries this disclosure shape" —
rewrites one of the 31 Cut-0 `(owner, text)` pairs `prose_surface_cut0.json:2401-2543` freezes for
`PersonRepository.save`, and `test_identity_endgame.py:1016-1019`'s `unauthorized_losses` assertion
goes RED with a message that names exactly two ways out: authorize the owner, or revert. Both exits
are green on every `check:` this document names and both are wrong for a different reason. Reverting
withdraws the "it says so" promise silently — the same defect SHAPE round 5's F19 finding closed one
artifact over, here arriving through a docstring instead of through a linter's silence. Authorizing
`save` satisfies (e1) but trips (e2) (`:1021-1030`), which demands at least one of `save`'s 31 Cut-0
lines go missing from the final text — so the fix for one wall assertion is a mandatory deletion that
buys the green by destroying prose, which is the identical "widen another item's wall" trap rejected
item 11 already refused for the privacy wall, now with a forced deletion attached rather than a
forced admission. Only the third build — append a new paragraph and leave all 31 lines
byte-identical — is both correct and free, and nothing in `## Acceptance Criteria` tells a builder
that is the one required path; AC-3's `check:` tests write-door refusal behaviour only and has no
reason to also assert anything about `person.py`'s comment text.

What would have to change: AC-3's `save` arm (or `## Approach` step (2), whichever the spec-writer
prefers as the pin) needs a clause stating the disclosure lands APPEND-ONLY in that frame — new
paragraphs only, every one of `save`'s existing Cut-0 lines byte-identical, `AUTHORIZED_PROSE_OWNERS`
and `prose_surface_cut0.json` untouched — the same "leave the other item's wall alone" instruction
this document already gives for the privacy wall (rejected item 11) and for the census digest (round
5's architect fold), applied to this third frozen artifact. This is a frozen-AC-text gap, not a
build-runner inference: the citation that names the disclosure's home is accurate, but the criteria
text is silent on the ONE property — append-only — that keeps following it from reddening a wall no
criterion in this set names.

No other material defect survived this round's attack on AC-1, AC-2, AC-4, or AC-5: the six-cell
classifier's ordering and no-fall-through assertions still hold, the CLEARING and CLASS-Ø legs still
make the D+E hand-repair path exercised, AC-3's REPORT LEG still carries five checked assertions
under a `check:` naming both surfaces, and the five `check:` names remain globally unique
(`rg` for each of the five function names over the whole tree returns zero matches outside this
document, re-run this round). Rulings A, B and C are untouched by the finding above; it is a
correction to AC-3's `save` arm and `## Approach` step (2), not a question for Dave.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-26
model: claude-sonnet-5
note: AC-3's `save` arm cites `person.py:1180-1184` as the model for this item's write-back disclosure, but no criterion asserts the disclosure must land APPEND-ONLY against `test_identity_endgame.py`'s frozen prose wall (`AUTHORIZED_PROSE_OWNERS` at `:359-373` omits `save`; clause (e1) at `:1006-1019` requires its 31 Cut-0 lines survive verbatim) — confirmed independently against `person.py:1155-1200` and the wall's own source — so a builder extending the cited paragraph in place lands on a red that resolves only by reverting the disclosure or by authorizing `save` and deleting one of its lines per clause (e2); converges with the architect's round-7 finding.
targets: AC-3, #approach, #exploration-notes
prior: held
basis: original
findings: 1/1
```


## AC Red-Team — 2026-09-27 (round 7)

Rulings on record:
Rulings A, B and C stay Dave's, unchanged by everything below; none of it reopens a question for him.

Round 7 for this gate, cold-start at this worktree's HEAD (`8b9b95e` plus the seeded uncommitted
delta, which carries the round-6 red-team fold and the round-8 architect fence). Read in the
prescribed order: `## Intent`, `### Examples of done`, `## Problem / Motivation` and the exploration
sections, then `## Acceptance Criteria` last.

### The prior rounds' findings, re-read against this tree

**Rounds 1–6: still HELD**, re-verified against the criteria text rather than carried. AC-1's WHERE
clause still pins the round-trip representative to the storable `15555550142@lid` with the class-C
member moved to a non-representative note (`## Acceptance Criteria`, AC-1 desc, the WHERE CLAUSE
paragraph). AC-3 still carries THE REPORT LEG's five assertions naming both the write-door and
`lint_vault` surfaces under one `check:`, still carries THE CLEARING and CLASS-Ø legs, and — round 6's
finding — still carries THE APPEND-ONLY CLAUSE with its three conjuncts (Cut-0 pairs survive,
`AUTHORIZED_PROSE_OWNERS`/`prose_surface_cut0.json` untouched, the disclosure demonstrably landed). AC-5
still pins the two-JID literals (`447700900987@s.whatsapp.net`, `15555550163@lid`) as unused
reserved-block members distinct from every other plant in the document. All five `check:` names are
still present and still name the surfaces their `why:` clauses claim. Nothing in this text has
regressed.

### This round's finding

**AC-5 — CRITICAL. AC-5 leg (e) commits to "zero notes left in the scalar shape" in the same breath
as requiring the class-D and class-E residual to be reported and left BYTE-IDENTICAL, and AC-3 refuses
a class-D or class-E value at every write arm in BOTH shapes — so no build can satisfy both conjuncts
when the live D+E population is non-zero, and the document's own AC-5 plant list forces that population
to be non-zero even in the hermetic suite.**

I re-derived this from the criteria text itself rather than trusting the architect's round-8 fence
(present above in this document, which reaches the same conclusion): AC-3's `desc` states the refusal
"in BOTH shapes, with nothing written" over classes C, D and E, and AC-5 leg (b) requires "every write
goes through `vault_io` and through the gate" for the migration itself — so a migration write that
would convert a class-D or class-E note from the scalar shape into the list shape is exactly the kind
of write AC-3 refuses, and there is no write arm carved out for the migration to bypass it. AC-5's own
`desc` requires the fixture to plant "at least one note per NON-Ø cell of AC-1's table — A, B, C, D and
E" — so the hermetic suite itself guarantees a non-zero D+E population — and the same `desc`'s leg (e)
says of that residual "its note's `whatsapp` bytes are asserted byte-identical," which is only true if
the note stays in the scalar shape it started in. Read together, leg (e)'s "zero notes left in the
scalar shape" and leg (e)'s own byte-identical-D/E clause cannot both be green on the criterion's own
required fixture — not on some future live-vault edge case, but on the suite AC-5 mandates.

The same conjunct is restated as a ship condition and a user-facing promise, so the defect is not
contained to one criterion's internal wording: `## Approach` step (4)'s exit numbers ("zero notes left
in the scalar shape, the class-C repair count equal to the census's class-C row, the D+E residual
reported and byte-identical") and `### Examples of done`'s given/when/then ("the readback reports zero
notes left in the old shape") both commit the same live-vault bracket to a number that cannot be
produced once the D+E population is non-zero — which the document's own `## Exploration Notes` and
`## Write Targets` census precondition treat as an open, unmeasured, non-guaranteed-zero quantity for
every class except E.

Failure scenario, concretely: a builder implements AC-3 and AC-5 exactly as drafted — gate refuses
D/E in both shapes at every arm including the migration's own write, migration reports and leaves D/E
byte-identical, `lint_vault`'s new detector reports the residual. Every named `check:` in this document
passes. AC-5's own required fixture plant (one class-D note, one class-E note) then makes the readback
assertion "zero notes left in the scalar shape" — if that assertion is coded literally as written —
FALSE on the fixture the same criterion mandates, so either the test as specified cannot be written
green at all, or a builder narrows "zero notes left in the scalar shape" to mean "zero of the notes the
migration COMMITS" (excluding the reported residual) without any criterion text licensing that
narrowing — the same "satisfied by a reader's generosity rather than by construction" shape this
document's own F19 closed on a different artifact. If the narrowing happens to be right, it is right by
luck of the reader's charity, not by what the frozen text says; if a future conductor takes leg (e) at
its word during the live bracket and the census's class-D or class-E row is non-zero, the bracket's exit
number cannot be produced and the run is left in exactly the prose-adjudication position the
entry/exit discipline exists to prevent.

What would have to change: leg (e)'s exit condition, `## Approach` step (4)'s exit numbers and
`### Examples of done`'s given/when/then all need the same one-clause fix — the zero-scalar promise
scoped to "except the reported D+E residual (C+D+E under Ruling B's alternative arm), whose scalar
count equals the census's own class-D/class-E rows" — still an oracle, still falsifiable, still backed
by the `lint_vault` detector as an independent second witness. That is a textual fold in three places,
not a design change: nothing about what the migration DOES to any cell moves, only what the document
tells Dave and the live-bracket conductor the vault looks like when it is done.

**This converges with the architect's round-8 finding on the same document, reached from the same
citations.** I am recording it as a red-team finding in its own right rather than deferring to the
architect's fence, per this gate's calibration: a defect that makes the frozen AC set unbuildable as
specified — the "mutually unsatisfiable ACs" failure class this role hunts for by name — is squarely
inside AC red-team's remit even when another gate found it first, and a fresh, independently-derived
confirmation is what tells a converging ladder apart from a single gate's isolated read.

No other material defect survived this round's attack on AC-1, AC-2, AC-4, or the resolution/read-write
legs: the six-cell classifier's ordering and no-fall-through assertions still hold, the derived arm set
and the append-only clause are unchanged, and the five `check:` names are still globally unique. Rulings
A, B and C are untouched — the fold corrects what the document claims about the vault's terminal state,
not what the migration does to any cell.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-27
model: claude-sonnet-5
note: AC-5 leg (e) commits to "zero notes left in the scalar shape" while its own mandated class-D/E plants must be reported and left byte-identical, and AC-3 refuses a class-D/E value at every write arm (including the migration's) in both shapes — so the two conjuncts cannot both hold whenever the D+E population is non-zero, which AC-5's own fixture guarantees in the hermetic suite; the same unscoped "zero notes left in the scalar shape" promise is restated in `## Approach` step (4)'s exit numbers and in `### Examples of done`, so a live bracket run against a non-zero census row cannot produce the number the document commits Dave to. Converges with the architect's round-8 finding, independently re-derived from AC-3's and AC-5's own criterion text.
targets: AC-5, AC-3, #approach, #acceptance-criteria
prior: held
basis: original
findings: 1/1
```


## Architectural Review — 2026-09-26 (round 4)

**Recommendation: REVISE — two blocking findings, both on the fixture-plant plan, both with a
precedent in this repo for the fold**

Round 4, re-read at this worktree's HEAD (`c93006a` plus the seeded uncommitted delta). Every
citation below was read in the code or the doc this round. **The prior rounds' findings all HELD**,
including round 3's and the AC red-team's convergent class-Ø finding, which is closed at the right
altitude. What this round found is in the material the FOLDS added: the reclassification of
`@Thrandell Ibberly.md` as the corpus's free class-C member (F6's first amendment) and the plant
list that fell out of it (F6's second) were never checked against the frozen corpus's own two
contracts — its ROUND-TRIP REPRESENTATIVE and its PRIVACY WALL. Neither touches Ruling A or Ruling
B, and I raise no new question for Dave; both are corrections to this document, and both must land
before the AC frame freezes because the frozen criterion text asserts the answers.

### Trigger check

Fired for the reasons rounds 1–3 recorded: a new persistent frontmatter shape across ~1,170 live
person notes; significant extension of three core systems (the WI-021 gate, the WI-125 identifier
index, `resolve_all`); >3 files in different concerns; cross-system consumers; effort > 1 day.

### The prior findings, re-read against this tree

**Round-1 findings 1 and 2 — still CLOSED.** Re-verified rather than carried: `identifier.py:276-281`
tests the `@lid` SUBSTRING then `normalize_phone(s)` ≥ `Phone.MIN_DIGITS == 7` and tests for a JID
suffix nowhere, so `WhatsAppJID.parse("+44 7739 341679")` still succeeds and only the STORABLE
predicate refuses it; `phone_normalization.py:52` splits at the FIRST `@`; `person.py:1190-1194` is
the save rider and writes back `emails`/`phones`/`aliases` only; `writer.py:112-117` emits every
declared field unconditionally.

**Round-3's blocking finding (class Ø) — CLOSED, and the fold is complete rather than cosmetic.**
Every leg of it is now asserted rather than described: the ABSENCE bullet ahead of both predicates in
`## Exploration Notes`, class Ø as a CELL, AC-1's ORDER assertion, AC-3's CLEARING and CLASS-Ø legs
at every arm, AC-4(a)'s round trip meeting the write side, and F16 carrying the derivation. The
mechanism re-read this round: `identifier.py:271-275` has no blank branch — and the package's own
existing test already parametrizes `None` and `""` alongside `"notaphone@s.whatsapp.net"`
(`tests/test_identifier.py:140`), which is the sharpest form of F16's point; `person.py:318-320`'s
`add()` returns on a `None`-or-blank raw before parsing; `name_gate.py:399`'s `elif entry and …`
draws the same line by falsiness; `writer.py:333-337` sets a field and there is no delete affordance
anywhere in the writer, so CLEARING really is the residual's only repair door; `models.py:94` and
`tests/fixture_vault.py:94` are the default and the transcribed oracle the refusing build would have
broken.

**Round-3's three non-blocking notes and round-2's notes 4 and 5 — all folded.** Verified the
corrections are true, not just present: `writer.py:229-233` is a second `whole_record=True` gate call
and `base.py:462-465` is the delegation, so `BaseRepository.save` reaches it and
`name_gate.py:289-294`'s docstring confirms the flag is not the discriminant — the payload containing
the key is; `frontmatter_write_arms` (`tests/derivations.py:979-1010`) derives arms off
`write_frontmatter`'s payload binding, so the writer entity arm is in the derived-by-equality set
exactly as F11's correction claims. AC-5's RE-READ clause, the live run as a SHIP CONDITION, the
producer-side disclosure in `## Approach`, and Ruling C's mint-on-ruling are all in the text.

### Review (only where this round's findings bite)

**Fit, Duplication, Boundaries, Determinism, Reversibility, Generalization, Build-vs-extend, Prior
art.** Unchanged from round 2's reads, all re-spot-checked: `_CONTAINER_KEYS` still excludes
`whatsapp` (`name_gate.py:84`), `_is_str_list`/`_shaped` are still positive predicates under which a
bare `str` falls to pass-through (`name_gate.py:181-198`), `_refuse` still admits no note-derived
value (`name_gate.py:142-174`), `_resolve_identifier` still reads `jid:<lid>` and pivots
phone-bearing JIDs (`person.py:902-908`), `_index_entity`/`_remove_entity_from_indexes` are still
exact mirrors (`person.py:266-270`, `:412-416`), and `resolve_all`'s cascade still has no
`whatsapp_jid` step (`person.py:628-651`). Liberal-for-reach / conservative-for-storage remains the
outside view rather than a local invention, so no cited execution is owed.

**Cost & maintenance — this is the dimension that moved.** F6 prices the fixture plant as "one
`CORPUS_DIGEST` regeneration … and, if the plant declares a new class, a census row", and calls the
plant-versus-inline-note choice the spec-writer's. Both findings below are that price being wrong:
the frozen corpus is not a blank page with a digest on it, it is a corpus with two live contracts,
and one of the five cells cannot be planted in it at all as the class table spells it.

### Blocking issues

**1. The note the folds appointed as the free class-C member is the corpus's ONE person round-trip
representative, and two in-tree tests write it through the gated whole-record arm asserting NO
refusal. After AC-3 both go RED, and the note is not substitutable.**

`@Thrandell Ibberly.md` carries `roundtrip_representative=True` (`tests/fixture_vault.py:219-233`),
`_representative` asserts there is EXACTLY ONE per type (`tests/test_fixture_vault.py:689-695`), and
the flag's declared contract is that those notes "declare their model's whole field set, which is
what makes AC-2's round trip total for them" (`tests/fixture_vault.py:13-14`). Two tests then write
that entity through the door:

- `tests/test_writer.py:404-428` — `test_corpus_note_round_trips_through_the_write_door` parses the
  person representative and calls `write_markdown_file(out / name, entity=doc.entity, …)` at `:421`,
  then asserts every declared field survives, `whatsapp` among them (`:424-427`);
- `tests/test_fixture_vault.py:705-761` — the AC-2 type-registry sweep does the same for every
  representative at `:753`, and at `:726-732` asserts the person representative is "GATE-CLEAN by the
  DOOR's own predicate".

That arm is `write_markdown_file(entity=…)` with `whole_record=True` (`writer.py:229-233`) — the
second whole-record-projection arm F11's own correction added — so under AC-3 a class-C stored value
is REFUSED there and both tests raise `NameGateRefusal` instead of comparing a field. F6 does name a
consequence here, but it names the wrong arm and understates the shape: it says "any existing test
that round-trips a fixture person through `save` needs re-reading", when the colliding arm is the
exported writer entity arm, the tests are the two above rather than a set to go looking for, and the
note is the corpus's unique representative rather than one specimen among several. Meanwhile F6
instructs the opposite of what the collision requires — "The plant must KEEP Thrandell's value rather
than tidy it — it is the discriminating member" — and AC-1's frozen `why:` restates it ("the corpus
supplies Ø (21 notes) and C (`@Thrandell Ibberly.md:7`) for free"). One note cannot be both the
gate-clean total round trip and the door-refused class-C specimen.

The reason this is blocking rather than a build-time surprise is the branch a builder reaches for
when the battery goes red: "the round trip now legitimately refuses, so change the test to expect a
refusal." That build is self-consistent and green, and it silently deletes the only assertion in the
repo that a whole person field set survives the write door — an existing invariant, traded away
inside a build whose AC text told the builder that C was free.

**The fold, and this corpus has already solved this exact collision once.**
`docs/vault-fixtures.md:5938-5943` (WI-016's own build log, deviation 3) records the identical shape
— a representative must declare every field, a wall forbids the realistic value for one of them —
and resolves it IN THE CORPUS rather than in either rule: "the four representatives carry those
fields empty and four non-representative notes carry the URLs … No criterion moved." Fold the same
way: the person representative's `whatsapp` becomes a value the door accepts (class Ø, or class B —
see finding 2 for why class A is not available to it), the class-C specimen moves onto a
NON-representative note keeping the `@example.com` spelling, and F6's plant accounting plus AC-1's
`why:` are corrected to say C is a plant rather than free. Also worth one line in the touch list: the
manifest's own override moves with the field's shape as well as its default —
`tests/fixture_vault.py:225` (`whatsapp="447700900789@example.com"`) alongside `:94`, because
`tests/test_fixture_vault.py:745-748` compares the parsed attribute against that declared scalar.

**2. Two of the four plant literals the class table names are inadmissible ANYWHERE in the fixture
corpus's reach, and the class-A cell is structurally inadmissible there — the corpus's one JID is
spelled `@example.com` BECAUSE of that wall, which is also why Thrandell is class C in the first
place.**

WI-016's privacy wall scores every email-shaped token in its reach against RFC 2606 / RFC 6761:
`EMAIL_SHAPED = [\w.+-]+@[\w.-]+\.\w+`, `RESERVED_EMAIL_DOMAINS = {example.com, example.net,
example.org}` as an EXACT-match frozenset, `RESERVED_TLDS = (".test", ".invalid", ".example")`, and
`_host_is_reserved` accepts only exact membership or a reserved-TLD suffix
(`tests/test_fixture_vault.py:302-325`). The live leg asserts zero violations per file
(`:1067-1069`), and the reach is every file under `tests/fixtures/vault/` PLUS the manifest module
`tests/fixture_vault.py` (`:386-392`). Applied to the literals this document freezes:

- **class A — `447700900123@s.whatsapp.net`: RED.** `s.whatsapp.net` is neither exact-reserved nor
  under a reserved TLD. And this is not a spelling accident that a different exemplar fixes: STORABLE
  is membership of the closed set `{"s.whatsapp.net", "lid"}`, so a phone-bearing STORABLE value must
  carry exactly that domain. **No class-A member can exist anywhere in the corpus's reach**, which
  also means the person representative cannot be made class A. `docs/vault-fixtures.md:5944-5948` is
  this constraint already recorded and already paid for: "A real JID (`<digits>@s.whatsapp.net`) is
  scored by `reserved_email_violations` against a domain no RFC reserves, so the corpus's JID is
  spelled `447700900789@example.com`" — the decision that makes Thrandell class C.
- **class E — `447700900456@lid.example.com`: RED.** `lid.example.com` is a SUBDOMAIN of
  `example.com`, which the frozenset matches by equality only, and it ends in none of the three
  reserved TLDs. Cheap fix, and it stays the cell it is: `447700900456@lid.example` is wall-clean
  (`.example` is a reserved TLD) and still class E — it contains the `@lid` substring so it parses
  with empty `phone_digits`, and its domain after the LAST `@` is `lid.example`, outside the closed
  set. But it is a correction to a literal three criteria name (the class table, AC-1's boundary-probe
  list, AC-3's required class-E member) plus AC-5's plant.
- **class D — `notaphone@s.whatsapp.net`: RED if planted in the reach**, same mechanism as class A.
  It is admissible in a test module's own literals, which is where AC-1's independence leg needs it.
- **class B is admissible, with a constraint nobody has stated.** `@lid` carries no dot after the
  `@`, so it is not email-shaped and the email wall never sees it — but `reserved_phone_violations`
  does (`:342-347`), and AC-1's REQUIRED negative-control lid ("11-digit string beginning with `1`")
  is satisfiable only from the NANP 555-01xx pattern: `15555550142@lid` passes
  (`RESERVED_PHONE_PATTERNS`' third member, `tests/test_fixture_vault.py:308-312`) and its 10-digit
  form `5555550142` is the `phones_match` counterpart the control needs. An arbitrary 11-digit lid is
  RED on the phone wall. Worth naming so the control is not discovered to be unplantable.
- **One more digit-level trap in the class-A exemplar even before the domain.** Thrandell's stored
  phone is `+44 7700 900123` (`tests/fixture_vault.py:224`), which normalizes to `447700900123` — the
  same digits the class-A exemplar uses — so that value would key `phone:447700900123` onto a second
  entity and mint an identifier conflict in the frozen corpus (`_index_identifiers`,
  `person.py:336-366`). Nothing in the battery pins the corpus's conflict set, so it would not go
  red; it would just be wrong. A plant has to pick an UNUSED member of a narrow reserved block, not
  merely a reserved-looking one.

So F6's cost line is short by the wall, and the choice it hands the spec-writer ("that cost is the
spec-writer's choice against an inline temp-vault note, not an open question for Dave") is FORCED for
class A rather than free. Decide it in this document, because F6 currently invokes WI-286 to argue
the opposite direction. Two arms: (a) the storable-form members live in the new test module's own
temp vault, and F6 says plainly that WI-286's reach-for-the-corpus-first rule yields here to WI-016's
privacy wall — nothing frozen is touched, and classes Ø, C and E can still come from the corpus; or
(b) this item declares a named `s.whatsapp.net` exemption in WI-016's wall the way `RESERVED_ISBN` is
declared (`tests/fixture_vault.py:46-50` — "asserted by EQUALITY against a one-member literal so it
cannot be padded"). **Recommend (a):** the exemption in (b) is defensible on the merits
(`s.whatsapp.net` is a protocol constant, not an identifying host) but it widens another item's
privacy wall to admit a real domain, and (a) buys the same coverage while leaving the wall alone.
Either way it is one sentence in F6 and a correction to AC-1's `why:`; what is not affordable is
freezing a plant list whose two storable-form members cannot be planted where the criterion says.

### Non-blocking notes (fold if cheap; no round is owed for them)

1. **AC-2's class-Ø cascade leg is satisfied today by a guard that predates this item, so it cannot
   fail for the reason it states.** `resolve_all` returns `[]` for a blank or whitespace-only query
   before step 1 runs (`person.py:606-611`), so "a blank query neither raises nor returns a person
   who merely has an empty `whatsapp:` field" is already true and stays true however the new step is
   written. Keep the leg — but state it as a pin on the guard's POSITION (the blank bail-out stays
   ABOVE the new `whatsapp_jid` step), which is the thing inserting a step can actually break.
2. **Class Ø's `None` member reaches the READER only as a bare `whatsapp:` key, and today such a note
   is INVISIBLE rather than empty.** YAML loads a valueless key as `None`,
   `_normalize_frontmatter` passes `None` through untouched (`parser.py:118-132`), and
   `whatsapp: str` (`models.py:94`) rejects it — so `model_validate` fails and the owned note raises
   `SchemaDriftError` onto the load skip surface (`parser.py:203-208`). Two cheap consequences: AC-4(a)
   should name YAML null explicitly as a class-Ø READ spelling, because the post-migration annotation
   has to coerce null → `[]` or the clearing spelling's own residue is unreadable; and the census's
   class-Ø row must be counted off the note BYTES rather than off loaded models, or it omits exactly
   the bare-key notes — a clause for `docs/wi-032-whatsapp-corpus-census.md`'s `why:`.
3. **Carried, not re-raised.** Rulings A, B and C are untouched by everything above, and the ordering
   the document states — settle A and B, measure the census, then freeze the frame — is still right.
   The two findings above are upstream of the FREEZE but downstream of the rulings, so they do not
   reopen anything Dave is being asked to sign.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-26
model: claude-opus-5
note: The fold that made `@Thrandell Ibberly.md` the free class-C member collides with the frozen corpus's own two contracts — it is the ONE person round-trip representative, written through the gated whole-record arm with no refusal expected at `tests/test_writer.py:421` and `tests/test_fixture_vault.py:753`, and the class-A/class-E plant literals are unreserved hosts under the WI-016 privacy wall (`tests/test_fixture_vault.py:302-325`, reach at `:386-392`), which is itself why the corpus's one JID is `@example.com` and therefore class C at all.
targets: AC-1, AC-2, AC-3, AC-4, AC-5, #exploration-notes, #write-targets
prior: held
basis: folded-material
findings: 2/5
```


## Architectural Review — 2026-09-26 (round 5)

**Recommendation: REVISE — one blocking finding, and the fold is one deletion plus one sentence**

Round 5, re-read at this worktree's HEAD (`c93006a` plus the seeded uncommitted delta). Every citation
below was read in the code or the doc THIS round. **The prior rounds' findings all HELD**, including
round 4's two fixture-plant findings and the AC red-team's convergent round-3 pair, both of which are
closed at the right altitude (F17, the class table's fourth column, AC-1's WHERE clause, rejected items
11 and 12). What this round found is the NEXT member of the class the conductor note ruled must be
closed in ONE fold: the fixture-and-cost plan still carries one instruction that was never checked
against the contract of the artifact it proposes to edit. It touches no ruling, raises no new question
for Dave, and is a correction to this document.

### Trigger check

Fired for the reasons rounds 1–4 recorded: a new persistent frontmatter shape across ~1,170 live person
notes; significant extension of three core systems (the WI-021 gate, the WI-125 identifier index,
`resolve_all`); >3 files in different concerns; cross-system consumers; effort > 1 day.

### The prior findings, re-read against this tree

**Round-1 findings 1 and 2 — still CLOSED.** Re-verified rather than carried: `identifier.py:269-281`
raises on `None` and on empty through two lines with no blank branch, tests the `@lid` SUBSTRING at
`:276`, then `normalize_phone(s)` against `Phone.MIN_DIGITS` at `:278-280`, and tests for a JID suffix
nowhere — so `WhatsAppJID.parse("+44 7739 341679")` still succeeds and only the STORABLE predicate
refuses it; `phone_normalization.py:39-55` splits at the FIRST `@` and strips every non-digit;
`identifier.py:298` keys a phone-bearing JID on `phone:<digits>` and a lid on `jid:<jid>`. The
`List[str]` answer and its derived accessor are unchanged and still right.

**Round-3's class-Ø finding and round-4's two plant findings — CLOSED, and the round-4 folds check out
against the code they rest on.** Re-verified this round, not carried: `tests/fixture_vault.py:219-233`
is Thrandell's spec with `whatsapp="447700900789@example.com"` and `roundtrip_representative=True`;
`tests/test_fixture_vault.py:689-695` asserts EXACTLY ONE representative per declared type, and
`:726-732` / `:753-761` are the gate-clean assertion and the write through the whole-record entity arm;
`tests/test_writer.py:404-428` is the second such write. The privacy wall is as F17 leg 2 states —
`EMAIL_SHAPED` requires a dot after the `@` (`:302`), `RESERVED_EMAIL_DOMAINS` is matched by EQUALITY
and `RESERVED_TLDS` by suffix (`:306-319`), and `reach_files()` is the corpus directory plus
`tests/fixture_vault.py` (`:386-392`). The three respelled literals are right at the digit level too:
`15555550142` matches `RESERVED_PHONE_PATTERNS`' third member `^1?\d{3}55501\d{2}$` (`:311`) and
`normalize_phone("15555550142@lid")` is `15555550142`, so the class-B corpus plant is wall-clean on the
phone leg while being invisible to the email leg (`@lid` carries no dot); `447700900321` and
`447700900654` are unclaimed members of the drama block; and I re-ran F17 leg 3's predicate — the only
claimed members are `447700900123` (`:224`, `:288-290`), `447700900456` (`:323`, and the `RESOLVABLE`
row at `:533`) and `447700900789` (`:225`). One fact worth adding because it is the leg most likely to
have been broken by moving a value and nobody checked it: `RESOLVABLE` (`tests/fixture_vault.py:529-534`)
carries no `447700900789` query, so relocating the class-C value to a non-representative note changes no
declared resolution answer, and `LOADABLE`/`SKIPS` (`:490-525`) are untouched because the tolerant reader
adds no skip.

### Review (only where this round's finding bites)

**Fit, Duplication, Boundaries, Determinism, Reversibility, Generalization, Build-vs-extend, Prior art.**
Unchanged from rounds 2 and 4, re-spot-checked: `_refuse` still admits no note-derived value and takes a
plain `pattern_key: str` (`name_gate.py:142-174`), `_is_str_list`/`_shaped` are still positive predicates
under which a bare `str` falls to pass-through (`name_gate.py:181-198`), and `normalize_phone` is still
the stdlib-only leaf whose consumers want the naive split. Liberal-for-reach / conservative-for-storage
remains the outside view; no cited execution is owed.

**Cost & maintenance — again the dimension that moves, and for the same reason one level out.** Round 4
found the plant plan priced against the corpus's bytes rather than against the corpus's CONTRACTS. The
fold corrected that for three contracts — the round-trip representative, the privacy wall, and
identifier-conflict uniqueness. It did not sweep the rest, and one of the unswept ones is named in the
fixture cost line itself.

### Blocking issue

**1. "The census gains a row for each newly declared class, and its own digest follows" is wrong on both
halves. `docs/vault-shape-census.md` is frozen against a digest that lives inside ANOTHER work item's
SIGNED criterion, and its class-row vocabulary cannot hold a `whatsapp` cell — so following the line
lands the builder in a red whose cheapest green is amending WI-016's frozen AC-3 text or writing a false
count into the estate's shape ledger.**

The line is `### Effort`'s itemized fixture work (iv), and the claim behind it is F6's cost sentence ("if
the plant declares a new class, a census row") re-endorsed by F6's third amendment ("and one census row
per newly declared class"). Three facts, each read this round:

- **The digest has no build-owned home.** `assert_census_is_frozen()` compares `sha256` over
  `docs/vault-shape-census.md` against `declared_census_digest()`, which reads the value out of the
  `AC-3` `criteria` fence in `docs/vault-fixtures.md` (`tests/test_fixture_vault.py:217-254`). Those
  criteria are FROZEN — signed 2026-09-08, and that document states in terms that "every remaining
  correction to a criterion's own text is now a D4b re-sign" (`docs/vault-fixtures.md:1389-1396`). The
  value currently stands at `CENSUS_DIGEST = sha256:4cb7945f…` inside that fence (`:1418`). So "its own
  digest follows" names an edit that does not exist: the digest follows only by editing another item's
  signed criterion, and the assertion runs in TWO places (`tests/test_fixture_vault.py:789`, `:1031`), so
  a census edit reddens the floor the moment it lands.
- **The row vocabulary is name-corruption classes, not field-value cells.** `census_class_rows`
  (`:122-138`) reads `census-class` fences whose ids are either a `branch_id` derived from
  `TIER1_BRANCHES + COMPANY_TIER1_BRANCHES` — asserted in BOTH directions at `:830-838` — or one of the
  six hand-listed shape classes (`:842-848`), and the landed table is exactly those sixteen
  (`docs/vault-shape-census.md:62-210`, ids `email_chars` … `postal_address_in_name`). `count` is a
  LIVE-VAULT count and `specimen` is a name string. There is no cell in that table for "a `whatsapp`
  value that parses and is not storable".
- **And leg (i) is an EQUALITY, which makes a MEASURED whatsapp row unsatisfiable for the one cell that
  matters.** `{MEASURED row ids}` must equal `{union of NOTES[...].shape_classes}` (`:800-803`), and any
  note declaring a `shape_class` must also declare a `Verdict` (`:856-891`) from a three-member
  vocabulary every arm of which is evaluated against that note's `name`. Class A's live count is not
  zero, and F17 leg 2's own derivation says no class-A member can exist anywhere in the corpus's reach —
  so a MEASURED class-A row can never acquire the corpus specimen the equality demands. Class Ø's 21
  members are not corruption specimens and have no verdict to declare.

Why this is blocking rather than a build-time surprise: `docs/**` is builder-writable in full, which
WI-016's own AC-3 `why:` names as the reason leg (iv) exists. So the builder who follows item (iv), sees
two tests go red, and reaches for the shortest green has two self-consistent routes and both are green on
every criterion in THIS set — re-freeze the digest by editing WI-016's signed AC-3 fence, or write the
new rows as `status: ABSENT, count: 0` with a plausible command/stdout pair, which is verbatim the
false-ledger route that same `why:` says the leg was added to close. Neither is a thing to discover from a
build, and the second corrupts the artifact this repo designates as the sole oracle for every live-vault
claim its hermetic suite cannot re-derive.

**The fold, and it is cheaper than either wrong route.** WI-032's six cells already have a home:
`docs/wi-032-whatsapp-corpus-census.md`, the precondition this document declares in `## Write Targets`,
whose `why:` already asks for "one row per cell of the SIX-cell class table". So delete the census-row
cost from F6's original sentence and from F6's third amendment, and replace `### Effort` item (iv) with
the affirmative statement that `docs/vault-shape-census.md` is NOT touched by this item — its class table
is WI-016's name-corruption vocabulary, its digest lives in WI-016's signed AC-3 fence, and the per-cell
counts this item needs belong in its own census precondition. The fixture cost then reduces to what is
genuinely build-side: the two corpus edits, the manifest overrides, and one `CORPUS_DIGEST` regeneration,
all of which `tests/fixture_vault.py:21-25` and `:44` make a legal build-side move. If a later reader
decides WI-032 does owe a row in WI-016's census, that is a conductor pass plus a D4b re-sign of another
item's signed criterion and it goes in front of Dave — not into a cost line.

**The generator, stated so the next fold can close the class rather than the member.** The conductor note
asked for a MATRIX of every plant literal × every corpus contract, naming the privacy wall,
`roundtrip_representative` uniqueness, the type-registry sweep, "and any other wall that reads
`tests/fixtures/vault/`". F17 delivered three of those. Unswept and reading the corpus or its manifest:
`test_every_census_corruption_class_has_a_specimen_with_a_verdict` (`:783`, the one above),
`test_the_skip_surface_over_the_corpus_equals_its_declared_reasons` (`:923`, with `SKIPS`, `LOADABLE` and
`RESOLVABLE` as its declared oracles — I checked it and it is CLEAN under the corpus edits, which is
worth SAYING rather than leaving unsaid), and
`test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate` (`:1353`, whose
universe the new test module joins — note 3 below). The conductor also asked for a next-level sweep over
every OTHER literal the ACs name and for its result to be stated "even if it found nothing"; the document
states no such sweep. Completing the matrix over the four walls named here, and stating the next-level
result, is what makes this the last round of this class rather than the fifth.

### Non-blocking notes (fold if cheap; no round is owed for them)

1. **Say where the whatsapp refusal `pattern` is DECLARED, not only that it is distinct.** AC-3 requires
   "its own stable `pattern` value distinct from every `NameValidator` pattern", which is the right
   requirement and is satisfiable for free: `_refuse` takes a plain `pattern_key: str`
   (`name_gate.py:142-174`), so a gate-local literal needs no record anywhere. The gap is what it does
   not forbid. WI-016's AC-3 floor is DERIVED from `{record.branch_id for record in TIER1_BRANCHES +
   COMPANY_TIER1_BRANCHES}` and asserted in both directions (`tests/test_fixture_vault.py:830-838`), and
   that criterion's `why:` pre-prices the consequence by name: a new Tier-1 branch reddens it
   immediately and discharging it needs a live-vault count, a scan command and verbatim stdout plus a
   re-taken digest — a conductor pass. A builder who declares the whatsapp refusal as a
   `name_validation` record because that is where the other patterns live pays exactly that. One clause
   in AC-3 or in the touch list closes it.
2. **The class-B corpus edit changes the DECLARED SHAPE as well as the value, and the manifest override
   has to move with both.** `tests/test_fixture_vault.py:745-748` compares
   `getattr(doc.entity, attribute)` against the declared literal and `:755-761` compares the re-parsed
   frontmatter MAPPING against the same literal, so with the stored field `List[str]`,
   `tests/fixture_vault.py:225` must declare `["15555550142@lid"]` and `:94`'s default must become `[]`
   even though the corpus note itself keeps the scalar spelling (the tolerant reader is what makes that
   pair agree). The document names both lines; it does not say the declared VALUE becomes a list, and
   that is the half a builder gets wrong while reading the line as "change the string".
3. **The new test module joins three set-equality walls, all in one test.** `ast` use is asserted
   single-homed to `tests/derivations.py` (`tests/test_fixture_vault.py:1383-1386`), the legal homes for
   a `SKIP_REASONS` literal are pinned to exactly two files by EQUALITY (`:1392-1395`), and every
   top-level `def test_` in the listed modules must resolve uniquely through `check_module`
   (`:1438-1442`). AC-3 and AC-5 already route their derivations through `tests/derivations.py`, so the
   first is honoured by design; the second is the one that bites, because AC-4(a)'s skip-surface
   assertions invite typing a reason literal instead of importing it from
   `obsidian_schemas/repositories/base.py`. One line in the touch list, and it is cheaper than the red.
4. **Carried, not re-raised.** Rulings A, B and C are untouched by everything above — by both gates'
   statement and by mine — and the ordering the document states, settle A and B, measure the census,
   then freeze the frame, is still the right one. The finding above is upstream of the FREEZE and
   downstream of the rulings, so it reopens nothing Dave is being asked to sign.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-26
model: claude-opus-5
note: `### Effort` item (iv) and F6 still price "a census row per newly declared class, and its own digest follows" as build-side and free, but `docs/vault-shape-census.md` is frozen against a digest that lives inside WI-016's SIGNED AC-3 fence (`tests/test_fixture_vault.py:217-254`, `docs/vault-fixtures.md:1418`) and its class-row vocabulary is name-corruption `branch_id`s with live-vault counts and name specimens, so a whatsapp cell has no row — and the two cheapest greens are amending another item's signed criterion or writing a false ABSENT/0 row, which is verbatim the route WI-016's own leg (iv) exists to close; the item's six cell counts already belong in `docs/wi-032-whatsapp-corpus-census.md`.
targets: AC-1, AC-3, AC-5, #exploration-notes
prior: held
basis: folded-material
findings: 1/4
```


## Architectural Review — 2026-09-26 (round 6)

**Recommendation: REVISE — one blocking finding, and it is NOT the plant class's next member**

Round 6, re-read at this worktree's HEAD (`c93006a` plus the seeded uncommitted delta). Every citation
below was read in the code THIS round. **The prior rounds' findings all HELD**, and the class the
conductor note ruled must be closed in ONE fold — the fixture-plant × corpus-contract matrix — IS closed:
F18's six legs check out leg by leg against the code they cite, including the three that report a clean
result. What this round found is a different generator in ORIGINAL text: F9's claim that the linter's
REPORT surface comes free. `_gate_refusal_pattern` has exactly ONE call site in the tool and that call
site was never read. It touches no ruling, raises no new question for Dave, and the fold is one detector
arm plus one AC clause.

### Trigger check

Fired for the reasons rounds 1–5 recorded: a new persistent frontmatter shape across ~1,170 live person
notes; significant extension of three core systems (the WI-021 gate, the WI-125 identifier index,
`resolve_all`); >3 files in different concerns; cross-system consumers; effort > 1 day.

### The prior findings, re-read against this tree

**Round-1 findings 1 and 2 — still CLOSED.** Re-verified rather than carried: `identifier.py:269-281`
raises on `None` and on empty through two lines with no blank branch (`:271-275`), tests the `@lid`
SUBSTRING at `:276`, then `normalize_phone(s)` against `Phone.MIN_DIGITS` at `:278-280`, and tests for a
JID suffix nowhere — so `WhatsAppJID.parse("+44 7739 341679")` still succeeds and only the STORABLE
predicate refuses it; `:298` keys a phone-bearing JID `phone:<digits>` and a lid `jid:<jid>`. One fact
worth adding because the design's shape rests on it and no finding states it: `WhatsAppJID` is a frozen
dataclass that ALREADY carries three derived `@property`s (`phone` at `:283-286`, `value` at `:288-290`,
`key` at `:292-298`), so `jid_domain`/`is_storable` is the fourth member of an existing pattern rather
than a new mechanism on the type.

**Round-3's class-Ø finding — CLOSED.** `person.py:318-320`'s `add()` returns on a `None`-or-blank raw
BEFORE parsing, re-read; `:330-331` projects `whatsapp` only when truthy; `name_gate.py:399`'s
`elif entry and …` draws the same line by falsiness; `models.py:94` is the `""` default and
`tests/fixture_vault.py:94` the hand-transcribed oracle.

**Round-4's two plant findings and round-5's census finding — CLOSED, and F18's matrix is sound where I
re-drove it.** Leg 1: `declared_census_digest()` really does read `CENSUS_DIGEST` out of the AC-3
`criteria` fence of `docs/vault-fixtures.md` (`tests/test_fixture_vault.py:217-239`), `assert_census_is_frozen()`
compares it to `sha256` over the census bytes (`:242-254`) and runs at `:789` and `:1031`;
`census_class_rows` (`:122-137`) admits only `branch_id`s from `_branch_ids()` (`:587-595`, asserted both
ways at `:830-838`) or the six hand-listed shape classes (`:842-848`), the MEASURED set is an EQUALITY
against `NOTES[...].shape_classes` (`:800-803`), and every shape-class specimen must declare a `Verdict`
evaluated against its `name` (`:856-891`). So "a `whatsapp` cell has no row and the digest has no
build-owned home" is exactly right, and item (iv)'s affirmative statement is the correct fold. Leg 2:
the eight admissible receivers are at `tests/fixture_vault.py:326-341` and `@Fennwick Drostane.md` is
`:340-341`. Leg 3: `reserved_phone_violations` sweeps `spec.fields.get("phones", ())` only
(`:1152-1168`) and never reads `whatsapp`; `RESOLVABLE` (`tests/fixture_vault.py:529-534`) carries no
`447700900789` query. Legs 5 and 6: `_temp_vault`-style walls confirmed at
`tests/test_fixture_vault.py:1353-1442`, and the three derivation hooks the ACs lean on all exist
(`tests/derivations.py:979`, `:1870`, `:2175`). The digit arithmetic checks out too: `15555550142`,
`15555550163` and `5555550142`/`5555550163` all match `^1?\d{3}55501\d{2}$` (`:311`), `447700900987`
matches `^447700900\d{3}$` (`:309`), and `@lid` carries no dot so `EMAIL_SHAPED` (`:302`) never fires on
either lid literal.

### Review (only where this round's finding bites)

**Fit, Duplication, Boundaries, Determinism, Reversibility, Generalization, Build-vs-extend, Prior art.**
Unchanged from rounds 2, 4 and 5, re-spot-checked. `_index_entity` still feeds
`normalize_phone(entity.whatsapp)` into `_phone_index` unconditionally (`person.py:266-270`);
`_index_identifiers` still records a collision to `_conflict_sets` and "never raises: a conflict is an
observability output" (`person.py:336-344`), which is the mechanism F17 leg 3 and AC-5's pinned pairs
exist to avoid; `resolve_all` still bails on a blank query BEFORE step 1 (`:608-609`) and still has no
`whatsapp_jid` step (`:628-651`); `_RESOLVE_CASCADE_ORDER` is still four labels (`:145`) with an unknown
label ranking last (`:190-197`). Liberal-for-reach / conservative-for-storage remains the outside view;
no cited execution is owed.

**Cost & maintenance — the dimension that moves again, and this time one level SIDEWAYS rather than
out.** Rounds 4 and 5 found the plant plan priced against the corpus's bytes rather than its contracts.
This round's finding is the same mistake against a different artifact: a capability the document prices
at ZERO on the strength of a function's docstring, without reading where the function is CALLED.

### Blocking issue

**1. F9's "the linter's report surface comes free" is false. `_gate_refusal_pattern` has exactly ONE call
site in the tool, inside the `stem_name_divergence` arm and behind `stem != stored` — so a note whose
`whatsapp` the door refuses is reported by `lint_vault` only if its filename ALSO disagrees with its
stored name, a live population WI-029 closed to ZERO five days ago. The item promises in five places
that the D+E residual is "reported and left"; as specced, it is left and not reported.**

The facts, each read this round:

- **One call site, and it is not a detector.** `_gate_refusal_pattern` is defined at
  `scripts/lint_vault.py:334-352` and called at `scripts/lint_vault.py:450` — the only occurrence in the
  tool. It sits inside `check_structural`'s `stem_name_divergence` arm, behind
  `if vf.entity_type == "person"` (`:433`) and `if isinstance(stored, str) and stored.strip() and stem
  != stored` (`:449`), and its return value becomes a MARKER appended to that issue's message (`:451-462`).
  It emits no `LintIssue` of its own. `rg -n 'whatsapp' scripts/lint_vault.py` is still 0 matches, and
  none of the five check functions (`:355`, `:496`, `:577`, `:698`, `:798`) reads the field —
  `field_type_mismatch` is about `auto_created` (`:464-465`).
- **The live population of that arm is zero.** `docs/stem-divergence-live-baseline.md:191` records the
  exit figure: divergent live person notes **8 → 0**, conductor-performed 2026-09-26. So on today's vault
  the one route to `_gate_refusal_pattern` is never taken at all. It is not a narrow report surface; it
  is an empty one.
- **And the `--fix` half is true for a different reason than F9 gives.** F9 says a refusing arm "does not
  make a malformed-JID note unfixable — PROVIDED the refusal carries its own `pattern` value". The
  `pattern` requirement is right, but it is not what makes that true: `apply_fixes` gates the DELTA
  (`whole_record=False`, `:1181`) and no auto-fixable rule's delta contains `whatsapp` at all — the five
  are `field_type_mismatch`, `person_missing_name`, `missing_body_sections`,
  `meeting_missing_from_timeline`, `broken_wikilink` (`tests/test_lint_vault_fix_rules.py:614-624`). So
  the refusal bucket never fires for this field either, from either direction.

**Why this is blocking rather than a build-time surprise: the item is buildable three ways and two of
them ship silent.** AC-3's closing clause reads "And one consequence pinned where it is FREE -
`lint_vault` REPORTS such a note through `_gate_refusal_pattern` under that distinct pattern", and
`### Effort`'s touch list prices `scripts/lint_vault.py` as "(pattern routing only)".

- **Build A** adds a report-only detector. Correct, and it is what the Intent needs — but it is a NEW
  detector in a tool whose changes carry a WI-026 floor, which the AC calls free and the touch list does
  not carry.
- **Build B** follows the citation literally and widens the existing marker so a non-storable `whatsapp`
  turns it on. Green on every criterion in this set, and wrong twice over: the marker's own text says
  "this divergence is not repaired by renaming the file to the stored name; repair the field"
  (`scripts/lint_vault.py:451-454`), which is a FALSE statement about a divergence whose actual defect is
  a JID; and it would flip live rows from UNMARKED to MARKED against a bracket that records "divergent
  rows the WRITE DOOR refuses (b3): 0 of 8" (`docs/stem-divergence-live-baseline.md:124`).
- **Build C** reads "pinned where it is free" as already-true and touches the tool not at all. Green on
  every criterion, and the residual is silent.

So the promise is made in `## Intent` ("A value that is already wrong is reported and left, never
erased"), in F13 leg 3 ("both reported by the linter and left for hand repair"), in Ruling B leg 2, in
AC-5 leg (e) ("reported as needing repair") and in `### Examples of done` ("the linter names it instead
of nobody noticing until a hand repair") — and the machinery behind it does not exist. This is the same
defect SHAPE the class-Ø fold closed one artifact over: a repair path the document commits to that the
item's own tooling does not provide. There the door refused the repair; here nothing reports that a
repair is owed.

**The fold, and it is cheap because this repo has already built exactly this detector once.** Add ONE
report-only arm to `scripts/lint_vault.py`'s `check_structural` — a `whatsapp` value the STORABLE
predicate rejects, `auto_fixable` left at its default so it never enters `apply_fixes`, carrying its own
check name and never the `stem_name_divergence` marker. WI-029's own detector is the precedent to copy
literally (ERROR, `structural`, never auto-fixable), and the cost is bounded and measurable rather than
assumed: the AC-1 oracle-table equality in `tests/test_lint_vault_fix_rules.py:596-624` is scoped to
`auto_fixable_emitter_checks` (`:599`), so a report-only rule does NOT join it and owes no repair oracle;
and `tests/test_stem_name_divergence_detector.py:283-289` filters on `issue.check == DIVERGENCE_CHECK`,
so a new check name disturbs none of that module's set equalities. Then: AC-3's closing clause stops
saying "free" and names the new check as an assertion (fires on class C/D/E, silent on Ø and on storable
values, `auto_fixable is False`); `### Effort`'s touch list carries `scripts/lint_vault.py` as a DETECTOR
plus a test module for it; and F9 is corrected to say the report surface is a new arm and the `--fix`
survivability comes from the delta containing no `whatsapp` key. If Dave would rather not grow the
linter, the honest alternative is to DELETE the word "reported" from the Intent, F13 leg 3, Ruling B leg
2, AC-5 leg (e) and `### Examples of done` and say the residual is discovered by the migration's own
report only — but that is a promise being withdrawn, so it should be withdrawn in writing rather than by
a build.

### Non-blocking notes (fold if cheap; no round is owed for them)

1. **AC-1's receiver constraint list is short by one class, and it is the same unread call site.** The
   WHERE clause admits any non-representative person note that LOADS and declares no
   `shape_classes`/`verdict`. Two notes satisfy all three and are still wrong receivers:
   `@Perrowin Tessamund Drostane.md` and `@Yolvenna Brindlecote Skarnell.md` declare
   `shape_classes=()` and no `verdict` — they carry a `discriminator` instead
   (`tests/fixture_vault.py:297-306`) — and they are the corpus's two MARKER-BEARING stem-divergent
   notes, asserted by EQUALITY at `tests/test_stem_name_divergence_detector.py:341-345` with their
   patterns pinned at `:346-352`. A non-storable `whatsapp` on either makes WI-029's marker set depend on
   the gate's arm ORDER, the same question F18 leg 2 removed for census specimens. The criterion NAMES
   `@Fennwick Drostane.md`, which is why this is a note and not a finding — but the CONSTRAINT should
   read "and is not stem-divergent", because the constraint is what a builder reasons from when the named
   note stops being available. (The two notes that would actually have gone RED — `@Quillam Ostrivane.md`
   and `@Quillam Lumbrek.md`, whose `patterns[...] is None` is asserted at `:353-354` — are already
   excluded by the `shape_classes` clause.)
2. **A third in-tree reader of the representative's declared `whatsapp`, not on the touch list.**
   F17 leg 1 names `tests/test_writer.py:404-428` and `tests/test_fixture_vault.py:705-761`.
   `tests/test_parser.py:248-264` (`test_corpus_person_note_parses_to_its_declared_values`) is a third:
   it selects the person `roundtrip_representative` and compares `getattr(doc.entity, attribute)` against
   `spec.fields` for every declared field. It stays GREEN under the fold — the tolerant reader gives
   `["15555550142@lid"]`, which is what `:225` will declare — but a builder who changes `:225` to a
   scalar list-member string sees it red in a module `### Effort` does not mention. One line in the touch
   list.
3. **The other four corpus-reading modules are CLEAN under the two corpus edits, stated rather than left
   unsaid** (the conductor note asked for clean sweep results to be reported). `tests/test_repositories.py:2255`
   imports `LOADABLE`/`materialize_vault` only — cache quantities, unaffected by a field's value;
   `tests/test_provenance_write_seam.py:147-171` derives its subjects from stem≠name divergence and from
   name-sharing, and neither `@Thrandell Ibberly.md` nor `@Fennwick Drostane.md` is either;
   `tests/test_stem_name_divergence_detector.py`'s four divergent members all carry `whatsapp: ""` today
   and stay class Ø under the fold, so its marker equality is untouched by the edits themselves (note 1
   is about the CONSTRAINT, not the named receiver); `tests/test_lint_vault_fix_rules.py` plants its own
   notes over a materialized copy and hands `apply_fixes` explicit issue lists, so no corpus-wide count
   moves.
4. **Carried, not re-raised.** Rulings A, B and C are untouched by everything above — the refused
   population, the repair door and the migration's repair pass are all unchanged; only the REPORT half
   moves. The ordering the document states, settle A and B, measure the census, then freeze the frame, is
   still right, and this finding is upstream of the FREEZE and downstream of the rulings.

### On the class the conductor note ruled closed

Stated explicitly, because it is the discriminant the factory reads and not a rhetorical point. The
plant class — every plant literal × every contract of the frozen corpus, its manifest and the
declarations those walls derive from — is CLOSED. I re-drove F18's six legs against the code this round
and every one of them holds, including the three that report nothing; the two corpus edits, the five
minted digit runs and the two pinned two-JID literals are all admissible where the document now puts
them, and `tests/test_fixture_vault.py` needs no widening. This round's finding is not the seventh member
of that class: its subject is `scripts/lint_vault.py`, its generator is F9 — text that predates every
fold and that no gate round, mine included, has re-read against the tool's call graph — and its fold
lands in a file the plant matrix never had reason to open.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-26
model: claude-opus-5
note: F9 prices the linter's report path at zero, but `_gate_refusal_pattern` has ONE call site (`scripts/lint_vault.py:450`), inside the `stem_name_divergence` arm behind `stem != stored`, emitting a MARKER and never an issue — and WI-029 closed that live population to 0 (`docs/stem-divergence-live-baseline.md:191`), so the D+E residual that `## Intent`, F13 leg 3, Ruling B leg 2, AC-5 leg (e) and `### Examples of done` all promise is "reported and left" is left and never reported; AC-3 calls the consequence free, so two of the three self-consistent builds ship silent and one falsifies WI-029's own marker.
targets: AC-1, AC-3, AC-5, #intent, #exploration-notes
prior: held
basis: original
findings: 1/4
```


## Architectural Review — 2026-09-26 (round 7)

**Recommendation: REVISE — one blocking finding, and it is the THIRD artifact class rather than
the next member of either closed one**

Round 7, re-read at this worktree's HEAD (`c93006a` plus the seeded uncommitted delta). Every
citation below was read in the code THIS round. **The prior rounds' findings all HELD**, and both
classes the document has been closing are closed: the fixture-plant × corpus-contract matrix (F18)
and the linter's report surface (F19). What this round found is a class no round has opened: the
walls that read **`obsidian_schemas/repositories/person.py` itself** — the file this item edits
most heavily. `tests/test_identity_endgame.py` freezes that file's PROSE verbatim for every owner
outside a thirteen-member authorized list, and `PersonRepository.save` — the frame F11 and F13 make
this item's disclosure home and its refusal surface — is not on that list. The document names that
module exactly once, at `tests/test_identity_endgame.py:274`, for an unrelated phone literal (F17
leg 3 extended): it was opened for a digit grep and its walls were never read. No ruling is touched
and I raise no new question for Dave.

### Trigger check

Fired for the reasons rounds 1–6 recorded: a new persistent frontmatter shape across ~1,170 live
person notes; significant extension of three core systems (the WI-021 gate, the WI-125 identifier
index, `resolve_all`); >3 files in different concerns; cross-system consumers; effort > 1 day.

### The prior findings, re-read against this tree

**Round-1 findings 1 and 2 — still CLOSED.** Re-verified rather than carried: `identifier.py:271-275`
raises on `None` and on empty with no blank branch, `:276` tests the `@lid` SUBSTRING, `:278-280`
tests `normalize_phone(s)` against `Phone.MIN_DIGITS`, and a JID suffix is tested nowhere — so
`WhatsAppJID.parse("+44 7739 341679")` still succeeds and only STORABLE refuses it. The `List[str]`
stored field with a derived accessor is unchanged and still right.

**Round-6's finding (F19, the report surface) — CLOSED, and the fold's cost accounting is correct
where I re-drove it, including the two walls F19 does not name.** `_gate_refusal_pattern` is still
defined at `scripts/lint_vault.py:334-352` with its one call at `:450`, splicing
`NOT_RENAMEABLE_MARKER` (`:72`, `:452`) into the divergence ERROR's message and emitting no issue;
`auto_fixable: bool = False` is the dataclass default (`:96`). The new arm joins nothing it should
not: `auto_fixable_emitter_checks` collects only `LintIssue(...)` calls that pass an
`auto_fixable=` keyword and skips a construction with none at all
(`tests/derivations.py:1893-1906`), so a report-only arm is outside the WI-026 oracle table by
construction (`tests/test_lint_vault_fix_rules.py:599`, `:621-624`) exactly as F19 leg 4 claims. Two
walls F19 does not name are also clean, and I state them because an unstated clean result is
indistinguishable from an unswept one: `_check_the_corpus_is_a_false_positive_floor` filters
`observed` to the `pinned` seven before its equality against `CORPUS_PINNED_ISSUES`
(`tests/test_lint_vault_fix_rules.py:842-845`) and `set(subjects) == set(pinned)` at `:897` demands
a subject only for a pinned member — so a new check is invisible to both; and the divergence
module's own `triaged` dict over ALL structural issues (`tests/test_stem_name_divergence_detector.py:359-363`)
asserts only `@Isolde Varnholt.md`, an undecodable skip specimen carrying no frontmatter at all, so
the new arm cannot move it.

**Round-3's class-Ø finding and rounds 4–5's plant/census findings — CLOSED.** Re-verified the
load-bearing facts: `person.py:318-320`'s `add()` returns on a `None`-or-blank raw before parsing;
`writer.py:333-337` sets a field and there is no delete affordance; F18 leg 2's eight admissible
receivers are at `tests/fixture_vault.py:326-341`.

### Review (only where this round's finding bites)

**Fit, Duplication, Boundaries, Determinism, Reversibility, Generalization, Build-vs-extend, Prior
art.** Unchanged from rounds 2, 4, 5 and 6, re-spot-checked: `_index_entity` still feeds
`normalize_phone(entity.whatsapp)` into `_phone_index` unconditionally (`person.py:266-270`);
`resolve_all` still bails on a blank query before step 1 and still has no `whatsapp_jid` step;
`_RESOLVE_CASCADE_ORDER` is still four labels (`:145`) with an unknown label ranking last
(`:190-197`). Liberal-for-reach / conservative-for-storage remains the outside view; no cited
execution is owed.

**Cost & maintenance — the dimension that moves, for the third time and on the third artifact.**
Rounds 4–5 found the plan priced against the frozen corpus's bytes rather than its CONTRACTS; round
6 found a tool capability priced off a docstring rather than off a call graph. This round: the
package file the item edits most is priced as ordinary code, and it is not — its comment and
docstring text is a frozen fixture of another item.

### Blocking issue

**1. `PersonRepository.save`'s docstring is FROZEN VERBATIM by WI-024's prose wall, and it is
exactly where F11's write-back disclosure and F13's refusal disclosure have to land. The three
builds that resolve the red are all self-consistent and green on every criterion in this set; one
reverts a disclosure this document promises, and one has to DELETE prose to buy its green.**

The wall, each fact read this round. `prose_lines` (`tests/derivations.py:1773`) records EVERY
comment line and EVERY docstring line of a file with its owning definition's qualname
(`ProseLine`, `:1644-1648`). `tests/fixtures/identity_endgame/prose_surface_cut0.json` is that
surface over `person.py` recorded at Cut 0 — "Recorded ONCE, against unchanged code; never
re-recorded" (`tests/test_identity_endgame.py:402`). Clause (e1) of
`test_strangler_prose_class_is_closed_in_the_package` then asserts, on every run of the floor, that
every Cut-0 `(owner, text)` pair whose owner is NOT in `AUTHORIZED_PROSE_OWNERS` is still present in
the final text (`:1006-1019`), compared on `(owner, text)` so a reflow of the line itself is a loss.
`AUTHORIZED_PROSE_OWNERS` (`:359-373`) is thirteen members: `<module>`, `__init__`,
`_index_entity`, `_project_identifiers`, `_index_identifiers`, `_remove_entity_from_indexes`,
`get_by_phone`, `resolve`, `resolve_all`, `find_or_create_stub`, the deleted legacy stub,
`resolve_or_create`, `_resolve_identifier`. **`PersonRepository.save` is not among them, and it owns
31 Cut-0 lines** (`prose_surface_cut0.json:2401-2543`), which I compared against the file: they are
byte-identical to `person.py:1155-1196` today, so the wall is green now and goes red on an edit.

Two of those 31 lines are the frames this item's own findings point at:

- `person.py:1174-1178` / `prose_surface_cut0.json:2466-2488` — "The write-back is the IDENTIFIER
  fields ONLY and never `name`", the paragraph that enumerates what the rider writes back
  (`entity.emails`/`phones`/`aliases`, `:1192-1194`). F11 requires that write-back to grow
  `whatsapp`, so the enumeration becomes incomplete.
- `person.py:1180-1184` / `prose_surface_cut0.json:2491-2513` — the `phones[]` in-place-mutation
  disclosure, ending "Stated because it is one field wider than the consumer audit's grep list was
  written against." **F11 cites this exact range as the model for WI-032's disclosure** ("the same
  class of disclosure WI-021 made for `phones[]` (`person.py:1180-1184`)"), and `### Examples of
  done` promises of the new refusal surface that "it says so". The natural way to honour either
  sentence is to extend that paragraph, and extending it rewrites its lines.
- Also frozen and also on this item's turf: `person.py:1169-1172` explains `whole_record=True`'s
  consequence as "both cross-field migrations run here exactly as they ran before". After Ruling B
  leg 2 there is a third consequence — a REFUSAL — and this is the sentence that would state it.

**Why this is blocking rather than a build-time surprise: three routes, all green, and the AC set
cannot tell them apart.** No leg of AC-1 through AC-5 asserts anything about `person.py`'s prose;
AC-3's `save` arm asserts refusal BEHAVIOUR only.

- **Build A — append only.** Add the disclosure as a NEW paragraph and leave all 31 Cut-0 lines
  byte-identical. Correct, green, and free — (e1) is a presence test, not an equality on the whole
  surface. Nothing in the document says this is the constraint.
- **Build B — add `PersonRepository.save` to `AUTHORIZED_PROSE_OWNERS`.** This is the move a builder
  reaches for on reading (e1)'s own failure message ("either it is a member the plan missed … or
  revert it"), and it is worse than widening another item's wall: clause (e2) asserts that every
  authorized owner has at least one Cut-0 line MISSING from the final text (`:1021-1030`), so
  authorizing `save` is RED until one of its 31 lines is DELETED. Buying the green requires
  destroying prose — and it is the same widen-another-item's-wall move rejected item 11 refused for
  the privacy wall, here with a mandatory deletion attached.
- **Build C — revert the prose.** Green on (e1), green on every criterion, and it ships a `save`
  whose docstring enumerates a write-back that has grown a field and explains a `whole_record=True`
  that has grown a refusal. That silently withdraws `### Examples of done`'s "and it says so" — the
  same defect shape F19 closed one artifact over, arriving through prose instead of through a
  detector.

**The fold, and it is one clause plus one touch-list line.** State in `### Effort`'s touch list that
`person.py`'s prose surface is frozen for every owner outside WI-024's thirteen, that `save` is such
an owner, and that this item's disclosures are therefore **APPEND-ONLY in that frame** — new
paragraphs, every Cut-0 line byte-identical, `AUTHORIZED_PROSE_OWNERS` and
`prose_surface_cut0.json` untouched (the WI-016 privacy-wall precedent: arm (a), leave the other
item's wall alone). Add `tests/test_identity_endgame.py` to the touch list as a wall the item joins
rather than a file it edits. One clause in AC-3's `save` arm or in `## Approach` step (2) pins it if
the spec-writer wants it asserted rather than instructed; Build B is worth a rejected item, because
it is the move (e1)'s own message invites and the one that costs a prose deletion.

**And the class, swept to its end so this is the last round of it rather than the seventh of
something.** Every wall in the suite that reads `person.py`'s text or behaviour, against every frame
this item edits. Two bit (above); the rest are CLEAN and I state them as such:

- **The Cut-0 resolve golden — CLEAN, and this was the one most likely to bite.**
  `test_resolve_is_one_cascade_and_matches_the_pre_cut_golden` (`:672-729`) replays every golden
  query through `repo.resolve` over a roster-seeded vault and asserts NO answer moved, with an
  exception list the item declares CLOSED ("Cut 3 gets none of its own", `:722-724`). WI-032 changes
  what enters `_phone_index` (AC-1) and inserts a cascade step (AC-2), either of which could move an
  answer — but `tests/fixtures/identity_endgame/roster.json` carries no `whatsapp` at all (grep over
  `tests/fixtures` returns the field only in `tests/fixtures/vault/*.md` and in the prose surface),
  so every seeded note is class Ø, contributes no phone-index entry from this field and no `jid:`
  key. The golden cannot move, and `repo.load() == len(ROSTER_TABLE)` with `skipped_count == 0`
  (`:346-347`) survives the tolerant reader. Worth saying out loud because the remedy a builder
  would reach for — re-recording the golden — is the one `:434-436` names as "the one way this
  oracle can be defeated".
- **WI-024's item-wall membership rows — CLEAN.** `test_identity_endgame_wall_membership_is_closed`
  (`:1101`) pins `non_completed_write_sites` over `ITEM_EDITED_QUALNAMES` (`:1065-1080`, which
  contains `_index_entity`, `_project_identifiers`, `_remove_entity_from_indexes` and `resolve_all`
  — four frames this item edits) and asserts `frontmatter_write_arms([person_path]) == []`
  (`:1156`). Both hold as long as this item adds no write capability and no frontmatter payload
  binding to `person.py`, which the design does not: the gate call and the writer delegation are
  already there. Named so it stays true rather than discovered.
- **The `ast` single-home equality — CLEAN, and it has a second home.** `:1134-1135` asserts it over
  package + tests, which is the same requirement F18 leg 5 carried from
  `tests/test_fixture_vault.py:1383-1386`; the new test module satisfies both by routing derivations
  through `tests/derivations.py`. No new obligation, but the wall is now known to be asserted twice.
- **`phone_index_iteration_sites` — CLEAN, with one constraint worth carrying.** `:642-644` asserts
  every phone-index iteration site is classified `materialized`. `_index_entity`'s change is an
  insert rather than an iteration, so nothing moves — but a builder who adds a loop over
  `self._phone_index` while making `_remove_entity_from_indexes` its exact inverse (AC-1) must wrap
  it in one of `MATERIALIZING_WRAPPERS` (`tests/derivations.py:1620`). One line in the touch list.
- **`resolve`'s no-index-reads clause — CLEAN.** `:692-698` asserts `PersonRepository.resolve` reads
  none of the four indexes directly. The new cascade step lands in `resolve_all` and the new public
  door is its own method, so the clause is untouched — and it is the guard that would catch a
  builder putting `get_by_identifier`'s lookup inside `resolve`.

### Non-blocking notes (fold if cheap; no round is owed for them)

1. **`_IDENTIFIER_PRIORITY` is a SECOND ordering for `whatsapp_jid` and the document never cites
   it.** `person.py:778` declares `_IDENTIFIER_PRIORITY = {"email": 0, "phone": 1, "whatsapp_jid": 1}`
   — whatsapp_jid TIES with phone for the Branch-A best-hit — and the class-body comment above it
   (`:772-777`) explains why: "A phone-bearing WhatsAppJID resolves like a Phone (same number → same
   person), so it shares phone's priority." AC-2 requires the new cascade label ranked AHEAD of
   `phone` (F15). The two are different frames — a typed-identifier best-hit inside
   `resolve_or_create` versus a cascade-label rank in `select_resolution` — so this is not a
   contradiction, and the tie is right for its frame because a phone-bearing JID and a phone ARE the
   same key. But the item's own principle is "no second spelling anywhere", one of the two orderings
   is about to change and the other is not mentioned in the document at all, so the spec should say
   which frame owns which ordering and why they differ. Note the comment that explains the tie is
   owned by `PersonRepository` (the class, `prose_surface_cut0.json:1681-1683`) — also NOT an
   authorized owner, so it is frozen too, which is the blocking finding's second member and the
   reason this note is worth a sentence rather than nothing.
2. **One more in-tree reader of `WhatsAppJID.parse`'s boundary, not on the touch list and green by
   design.** `tests/test_phone_normalization.py:105-124` pins `parse` over
   `447990558521@s.whatsapp.net`, `12345@lid` and the raising `12345@s.whatsapp.net`, i.e. the
   `MIN_DIGITS` boundary. Ruling A's recommended arm leaves `parse` untouched, so the module stays
   green and needs no edit — worth naming only because it is the module that goes red if anyone
   revisits Ruling A's alternative (b), and rejected item 7's cost line ("four call sites plus two
   test premises") does not count it.
3. **Carried, not re-raised.** Rulings A, B and C are untouched by everything above — the refused
   population, the repair door, the migration's repair pass and the report arm are all unchanged;
   what moves is where a disclosure's TEXT may be written. The ordering the document states — settle
   A and B, measure the census, then freeze the frame — is still right, and this finding is upstream
   of the FREEZE and downstream of the rulings.

### On the two classes the document has closed, and why this is not a third instance of them

Stated explicitly because it is the discriminant the factory reads. The fixture-plant class (every
plant literal × every contract of the frozen corpus, its manifest and the declarations those walls
derive from) is closed — F18's six legs re-drove clean where I checked them. The report-surface
class is closed — F19's fold is sound and its cost accounting survives the two walls it does not
name. This round's subject is neither: it is `obsidian_schemas/repositories/person.py`, the file the
item edits most, and the wall is a PROSE fixture rather than a plant or a detector. The generator is
the same one the conductor note named — an artifact treated as ordinary material without reading the
contracts it carries — and the sweep above runs it to the end over every wall in the suite that
reads that file, stating the five clean results as well as the two that bit, so the next round has
no unopened artifact of this class to find.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-26
model: claude-opus-5
note: `PersonRepository.save`'s 31-line docstring is frozen verbatim by WI-024's prose wall — clause (e1) of `test_strangler_prose_class_is_closed_in_the_package` (`tests/test_identity_endgame.py:1006-1019`) requires every Cut-0 `(owner, text)` pair of an owner outside `AUTHORIZED_PROSE_OWNERS` (`:359-373`, which omits `save`) to survive, and `prose_surface_cut0.json:2401-2543` is byte-identical to `person.py:1155-1196` today — yet F11 names `person.py:1180-1184` as the home for the new write-back disclosure and `### Examples of done` promises the refusal surface "says so"; no AC touches that prose, so all three resolving builds are green and two are harmful (revert the disclosure, or authorize `save` and delete one of its lines to satisfy (e2)).
targets: AC-2, AC-3, #exploration-notes, #approach
prior: held
basis: original
findings: 1/3
```


## Architectural Review — 2026-09-26 (round 8)

**Recommendation: REVISE — one blocking finding, and it is the MIGRATION'S TERMINAL STATE rather than
another artifact whose contract nobody read**

Round 8, cold-start re-read at this worktree's HEAD (`c93006a` plus the seeded uncommitted delta, which
carries the round-7/red-team-round-6 fold). Every citation below was read in the code THIS round. **The
prior rounds' findings all HELD** — including round 7's, whose fold (F20) not only landed but CORRECTED
both arriving fences' line count, which I re-ran and confirm. What this round found is not the eighth
member of the wall-sweeping class: it is a contradiction between two conjuncts of AC-5 and the exit
numbers `## Approach` step (4) commits to the live bracket, and it is about what the vault LOOKS LIKE
when the migration has finished. No ruling is reopened, but the finding does correct a claim this
document makes about Ruling B's alternative arm.

### Trigger check

Fired for the reasons rounds 1–7 recorded: a new persistent frontmatter shape across ~1,170 live person
notes; significant extension of three core systems (the WI-021 gate, the WI-125 identifier index,
`resolve_all`); >3 files in different concerns; cross-system consumers; effort > 1 day.

### The prior findings, re-read against this tree

**Round-1 findings 1 and 2 — still CLOSED.** Re-verified rather than carried: `identifier.py:271-275`
raises on `None` and on empty through two lines with no blank branch, `:276` tests the `@lid` SUBSTRING,
`:278-281` tests `normalize_phone(s)` against `Phone.MIN_DIGITS`, and a JID suffix is tested nowhere —
so `WhatsAppJID.parse("+44 7739 341679")` still succeeds and only STORABLE refuses it. One fact worth
adding because it closes a latitude the STORABLE bullet leaves open in its wording: `.jid` holds the
**normalized** value, `str(raw).strip().lower()` (`identifier.py:266`, `:273`, `:277`, `:281`), so a
`jid_domain` property computed off `self.jid` is case-insensitive for free and `447700900321@S.WHATSAPP.NET`
is storable without a second rule. The bullet says "the raw value's JID DOMAIN"; the type has no raw
value to read, which makes the recommended spelling the only buildable one. Nothing to change.

**Round-3's class-Ø finding — CLOSED.** `person.py:318-320`'s `add()` returns on a `None`-or-blank raw
BEFORE calling any parser; `models.py:94` is still `whatsapp: str = ""`; `writer.py:333-337` sets a field
and there is no delete affordance. The six-cell table is a genuine partition, which I checked rather than
took: over a non-empty value the three booleans (parses? / `phone_digits` empty? / storable?) have exactly
five reachable combinations and the table names all five — a value like `447700900321@lid@s.whatsapp.net`
(the `@lid` substring with a storable LAST-`@` domain) falls in B by the table's own definition rather
than off the end of it.

**Rounds 4–6's plant, census and report-surface findings — CLOSED.** `_CONTAINER_KEYS` still excludes
`whatsapp` (`name_gate.py:84`); `_index_identifiers` still records a collision to `_conflict_sets` and
"never raises" (`person.py:336-344`), which is the fact F17 leg 3's silent-conflict argument rests on;
`_RESOLVE_CASCADE_ORDER` is still four labels (`person.py:145`) with `rank`'s unknown label falling to
`len(...)` (`:190-197`).

**Round-7's prose finding (F20) — CLOSED, and its own correction of the two arriving fences is right.**
Predicate re-run this round: `rg -c '"owner": "PersonRepository\.save"'
tests/fixtures/identity_endgame/prose_surface_cut0.json` → **29**, not the 31 the round-7 architect fence
and the red-team round-6 fence both state. I also checked the mapping F20 claims rather than the count
alone: `save`'s docstring is `person.py:1158-1189`, which is 32 lines carrying 5 blanks (`:1161`, `:1168`,
`:1173`, `:1179`, `:1185`), plus the two trailing comment lines at `:1195-1196` — 27 + 2 = 29. And the
fold's load-bearing claim that APPEND is FREE is true of the clause as written: (e1) builds
`final_pairs = {(r.owner, r.text) for r in final}` and asserts `unauthorized_losses == []` over Cut-0
pairs (`tests/test_identity_endgame.py:1006-1019`) — a PRESENCE test, so a new paragraph adds a pair
nobody reads and removes none. `AUTHORIZED_PROSE_OWNERS` (`:359-373`) omits `PersonRepository.save`, and
(e2) (`:1021-1030`) does demand an authorized owner LOSE a line, so rejected item 15's cost is real.

### Review (only where this round's finding bites)

**Fit, Duplication, Boundaries, Determinism, Reversibility, Generalization, Build-vs-extend, Prior art.**
Unchanged from rounds 2, 4, 5, 6 and 7 and re-spot-checked: `_index_entity` still feeds
`normalize_phone(entity.whatsapp)` into `_phone_index` unconditionally (`person.py:266-270`) with
`_remove_entity_from_indexes` its exact mirror (`:412-416`); the gate's refusal contract still admits no
note-derived value (`name_gate.py:142-174`). Liberal-for-reach / conservative-for-storage remains the
outside view — the standard identifier answer, not local machinery — and expand → migrate → defer-contract
remains the standard parallel-change answer, so no cited execution is owed.

**Reversibility — the dimension that moves this round, and it moves FORWARD rather than back.** F14
states the back-out correctly. What no round has asked is the mirror question: what does the vault look
like when the migration has SUCCEEDED? The answer the design forces is not the answer the document
commits to Dave, and the two are written three sentences apart.

### Blocking issue

**1. The gate refuses a class-D or class-E value in EITHER shape, so the migration cannot convert those
notes' shape at all — they are terminally scalar. Yet AC-5 leg (e), `## Approach` step (4)'s exit numbers
and `### Examples of done` all commit to "zero notes left in the scalar shape" in the same breath as
"the D+E residual reported and byte-identical". Those two conjuncts cannot both hold, and AC-5 mandates
the class-D plant that makes them collide, so NO build passes the criterion as written.**

The mechanism, in four read facts and one step:

- A shape conversion is a write that introduces `whatsapp`. For a class-D note the payload is
  `{"whatsapp": ["n/a"]}` — the list shape with one non-storable member, which AC-3 names explicitly
  ("a list containing one bad member among good ones") and refuses with **nothing written**.
- There is no arm that escapes it. AC-5 leg (b) asserts STRUCTURALLY that every write goes through
  `vault_io` *and through the gate*, no direct `write_text`; and the delta rule cannot help, because the
  delta rule (`name_gate.py:31-36`) keeps a stored-dirty note writable only for writes that do NOT
  re-introduce the field — and re-introducing the field is the entire content of a shape conversion.
- So the migration leaves every class-D and class-E note in the scalar shape, necessarily. That is not a
  build choice; it is forced by AC-3 plus AC-5 leg (b), and the document says as much where it describes
  the cells: class E is "left byte-identical by the migration like D", and AC-5 leg (e) asserts "its
  note's `whatsapp` bytes are asserted byte-identical".
- And the collision is present in AC-5's own fixture by mandate, not only on the live vault: leg (d)
  requires a planted class-E note asserted byte-identical after a repair-enabled run, and the plant list
  requires "at least one note per NON-Ø cell — A, B, C, D and E". So the class-D and class-E plants are
  scalar when the run ends, and leg (e)'s zero-scalar conjunct is red on the hermetic suite regardless of
  what the live census reports.

**Why this is blocking rather than a build-time surprise: every route out is red, which is worse than
buildable-two-ways.** Enumerated, because the four-way sweep is what shows the criterion is unsatisfiable
rather than merely ambiguous:

- **(a) let the gate accept D/E for the conversion** — red on AC-3, and it retires the item's own refusal.
- **(b) bypass the gate for the conversion** — red on AC-5 leg (b), which asserts the route structurally.
- **(c) CLEAR the D/E values so the note converts as class Ø** — the one route that reaches a
  zero-scalar vault, and it is silent data loss on exactly the population the item exists to preserve:
  rejected item 8's harm arriving through the migration instead of through the reader. It is caught, and
  I want to record WHY so the fold does not re-buy the guard: leg (c)'s TOTAL-value count per note (added
  in the first red-team round precisely so the parseable-only scoping could not become a licence to delete
  what it excludes) goes 1 → 0 and fails. That guard is load-bearing and, on this reading, it is the only
  thing standing between the criterion's own contradiction and erasure.
- **(d) honour byte-identity and report the residual** — the correct build, and red on leg (e)'s
  zero-scalar conjunct.

So the build-runner's real exits are to amend a FROZEN criterion (a D4b re-sign after Dave's signature,
which is exactly the cost this document elsewhere refuses to defer) or to reinterpret "zero notes left in
the scalar shape" as "zero of the notes the write COMMITS" — the charitable reading, which is correct and
which nothing in the text licenses. That second exit is the same defect SHAPE F19 closed one artifact over:
a clause satisfied by a reader's generosity rather than by construction, riding on a neighbouring
assertion. Here it is worse than in F19's case, because the clause is also an EXIT NUMBER: `## Approach`
step (4) commits it to the live bracket ("The exit numbers that matter: zero notes left in the scalar
shape, the class-C repair count equal to the census's class-C row, the D+E residual reported and
byte-identical"), and `### Examples of done` promises "the readback reports zero notes left in the old
shape". If the live class-D population is non-zero, the conductor performing the bracket cannot produce
the figure the item ships against and is left adjudicating it in prose — which is the one thing the
entry/exit discipline exists to prevent. If it happens to be zero, the figure works by luck, which is the
"stays green while unclassified" shape this document refuses everywhere else (it is the stated reason
class E is asserted rather than assumed).

**And it touches a claim about Ruling B, which is why it is not purely editorial.** AC-5 leg (d)'s
closing clause says a run invoked with repair disabled "leaves class C untouched and reports it (Ruling
B's alternative arm, so the criterion holds either way Dave rules)". It does not hold either way: under
the alternative arm class C is also unstorable at the gate, so class C joins the terminally-scalar
residual, the zero-scalar conjunct is further out of reach by the census's class-C count — the row the
document itself calls the load-bearing one — and N notes end the migration both scalar AND unsaveable
through the whole-record arms. Dave is entitled to that number when he rules on the repair, and today
the document tells him the criterion is arm-agnostic.

**The fold, and it is one clause plus one sentence in three places.** State the terminal state instead of
a number that assumes it away: the migration's exit condition is **zero notes left in the scalar shape
EXCEPT the reported D+E residual (C+D+E under Ruling B's alternative arm), whose scalar count EQUALS the
census's class-D and class-E rows** — still an oracle, still falsifiable, and now the same number the
`lint_vault` detector reports as an independent second witness, which is what AC-3's REPORT LEG was built
to buy. Scope leg (e)'s zero-scalar conjunct to the notes the write COMMITS, and add the conjunct that
keeps route (c) red by intent rather than by side effect: the migration never CLEARS a value to make a
note convert — clearing is a hand repair a person asks for through the delta arms (AC-3's CLEARING leg),
never something the run does. Then correct leg (d)'s arm-agnostic claim, and make the same edit in
`## Approach` step (4)'s exit numbers and in `### Examples of done`'s "zero notes left in the old shape".
One consequence worth stating in `## Exploration Notes` while the fold is open, because it is the honest
form of F7's "refusing the scalar form is a separate item or never": the tolerant reader can never be
contracted while any D+E note survives, so the CONTRACT phase of expand → migrate → contract is gated on
the residual reaching zero by hand, not on this item.

### Non-blocking notes (fold if cheap; no round is owed for them)

1. **The list flip turns one of the three whatsapp frames from loud to SILENT, and the touch list names
   the frame without naming the trap.** `### Effort` lists `_index_entity`, `_remove_entity_from_indexes`
   and `_project_identifiers` as frames to edit. Two of them fail LOUDLY on the new shape, which is fine:
   `normalize_phone` does `phone.split("@")` (`phone_normalization.py:52`), so `normalize_phone(<a list>)`
   raises `AttributeError` at `person.py:268` and `:414`. The third does not. `_project_identifiers` guards
   with `if entity.whatsapp:` and makes ONE `add(WhatsAppJID.parse, entity.whatsapp)` call
   (`person.py:330-331`); `add`'s blank guard tests `isinstance(raw, str)` (`:319`) so a list passes it, and
   `parse` does `s = str(raw).strip().lower()` (`identifier.py:273`) — so
   `WhatsAppJID.parse(["447700900321@s.whatsapp.net"])` SUCCEEDS with `phone_digits == "447700900321"`,
   because `normalize_phone` splits at the first `@` and strips non-digits and recovers the same digits from
   the list's repr. A build that forgets the loop therefore produces the CORRECT `phone:` key for a
   single phone-bearing value: AC-1's and AC-2's class-A legs pass. What catches it is the `jid:`-keyed
   cells (B and E get `jid:['15555550142@lid']`) and AC-5's two-JID note (one identifier where two are
   asserted). The suite does go red, which is why this is a note — but "iterate the list; never hand the
   list to `parse`" is one clause in the touch list, and it is cheaper than the diagnosis.
2. **After the fix the phone-pivot rule is computed in three frames from three separate `parse` calls,
   and the item's own principle is "no second spelling anywhere".** `_index_entity` (`:266-270`),
   `_remove_entity_from_indexes` (`:412-416`) and `_project_identifiers` (`:330-331`) each decide
   independently what a `whatsapp` value contributes, and after AC-1 all three need the same rule (only a
   non-empty `phone_digits` pivots). `_index_identifiers` already runs at the END of `_index_entity`
   (`:283-284`) over `_project_identifiers`' typed output, so the phone-index insert can be DERIVED from
   the projected identifiers rather than re-parsed beside them. AC-1's inverse-over-the-same-table
   assertion pins the behaviour either way, which is why this is a note and not a finding — but the spec
   should say which frame owns the pivot rule, or a builder writes it three times and the next item that
   widens it finds two of them.
3. **Carried, not re-raised.** Rulings A and C are untouched by everything above. Ruling B is not
   reopened either — the blocking finding does not change what the migration DOES to any cell, it changes
   what the document claims the vault looks like afterwards and corrects a sentence that tells Dave the
   criterion is indifferent to his answer on the repair. The ordering the document states — settle A and
   B, measure the census, then freeze the frame — is still right, and this finding is upstream of the
   FREEZE and downstream of the rulings.

### On the classes this document has closed, and why this is not another instance of them

Stated because it is the discriminant the factory reads. The three classes rounds 4–7 closed are
artifacts whose CONTRACTS were unread: the frozen corpus and its manifest (F17, F18), a tool's report
capability priced off a docstring (F19), and a package file's prose surface (F20). I re-drove each where
its load-bearing facts were cheap to check and all three hold. This round's subject is not a fourth
artifact and not a fixture: it is a contradiction between two conjuncts the document has carried since
its first draft — AC-5 leg (e)'s zero-scalar exit number against the byte-identity guarantee the class
table and leg (e) itself give class D and class E — made visible by nothing more than asking what the
vault looks like after a successful run. It is reachable from the criteria text alone without opening
another module, which is why it is `basis: original` and why the sweep that closed the artifact class
could not have surfaced it.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-26
model: claude-opus-5
note: AC-3 refuses a class-D/E value in BOTH shapes and AC-5 leg (b) asserts every migration write goes through the gate, so those notes are TERMINALLY SCALAR — yet AC-5 leg (e), `## Approach` step (4)'s exit numbers and `### Examples of done` all commit to "zero notes left in the scalar shape" alongside "the D+E residual reported and byte-identical", and AC-5 itself mandates the class-D plant that collides them; all four routes out are red (accept → AC-3, bypass → leg (b), clear → leg (c)'s total-value count, honour byte-identity → leg (e)), so no build passes and the real exits are a D4b re-sign or silently reinterpreting the exit number the live bracket ships against — and leg (d)'s claim to hold "either way Dave rules" is false, because under Ruling B's alternative arm class C joins the residual.
targets: AC-5, AC-3, #approach, #exploration-notes
prior: held
basis: original
findings: 1/3
```


## Threat Model — 2026-09-27

**Recommendation: PROMOTE to threat-modeled — with three required mitigations, every one landed on an
existing Implementation-Plan task and none of them touching a frozen criterion.**

Cold-start read at `specced`, round 1 — no prior threat-model verdict on this document. Carry-forward read
in full: architect rounds 1–9, AC red-team rounds 1–8, both conductor notes, the AC sign-off
(`ac_hash dd772c1183de`) and the data-premise round. Every in-tree citation below was re-read in this
worktree, and every census figure was re-derived from that artifact's own script rather than taken off its
summary table. Rulings A, B and C are Dave's and nothing here touches any of them; the AC frame stays
frozen, which is a constraint on what a mitigation may ask for and is honoured by all three below.

### Trigger check

Fires on four of the nine, and the first two are the substance of the review:

- **Persists data to state files** — this item WRITES 1168 live person notes, 82 of them semantic rewrites
  of a stored identifier, irreversibly.
- **Crosses trust boundaries (untrusted → trusted)** — Prerequisite 7 declares two, correctly: a caller's
  untyped value at the three dict-shaped write doors, and a note's own STORED value arriving back through a
  whole-record projection. A third the document does not name as a boundary but treats as one anyway:
  `lint_vault` reading untrusted vault bytes (§4's `try`).
- **Filesystem operations on user-owned files** — the migration walks and mutates the vault.
- **Handles input from external sources** — transitively, the values in this field are written by HAL9000's
  PATCH door, the `new-person` skill and the WhatsApp bridge sync.

No skip pattern applies. NOT triggered, and stated so the review's own scope is falsifiable: no secret,
credential, API key, OAuth scope or token anywhere in the design; no outbound API call; no MCP scope or
tool permission; no access-control or file-permission change. Prerequisite 7 asserts the same and is
correct.

### STRIDE review

**Spoofing — this item is a net REDUCTION, and the reduction is the point.** A `whatsapp` value is an
identity claim, and today a bare number in that field is indexed as a telephone number:
`_index_entity` feeds `normalize_phone(entity.whatsapp)` into `_phone_index` unconditionally
(`person.py:266-270`) while `normalize_phone` splits at the first `@` and strips non-digits
(`phone_normalization.py:52-55`), so a lid's opaque digits become a phone key that `get_by_phone`'s
permanent fuzzy arm can answer with (`person.py:481-496`). The census measures 26 live notes in that state
with **zero** currently-reachable harmful collisions, so the defect is latent rather than active — which
AC-1 handles by PLANTING the falsifying member rather than hoping for one. The new doors add no
false-positive path of their own: `get_by_identifier` takes an already-typed `Identifier` and
`_resolve_identifier` reads an EXACT `jid:` key (`person.py:902-908`), and `resolve_all`'s new step 4b is
guarded on `not candidate_jid.phone_digits` so a phone-bearing JID still routes to the phone door. The new
cascade label ranking ahead of `phone` (§5(e)) means an exact `jid:` hit beats a fuzzy phone hit, which is
the correct direction for an identity claim. One residual, pre-existing and adequately handled: making the
field list-shaped multiplies `jid:` keys, and `_index_identifiers` does not raise on a key mapping to two
entities (F17 leg 3) — but the package already SURFACES that as `IdentifierConflict`/`repo.conflicts`
(`identifier.py:96-108`), so an ambiguous claim is recorded rather than silently answered. No new
mitigation.

**Tampering — this is where the one real finding is.** Three sub-surfaces:

*(a) The write path itself is sound.* Every migration write is one
`writer.update_frontmatter_field` call, which takes `vault_io.note_lock`, reads inside the lock, gates the
delta with the note's own parsed `type:` and writes under a stamp precondition (`writer.py:359-393`). So
the migration introduces no new write arm, no direct `write_text`, and AC-5 leg (b) asserts that
STRUCTURALLY rather than by observing a result. A stamp mismatch surfaces as `WriteFailedError`
(`errors.py:80`) which the run does not catch — it aborts. Concurrency, retry and partial-failure are each
walked in `## Edge Cases` and each resolves to "reuse the one door, abort loudly, re-run the dry run",
which is the right answer for a one-shot corpus walk. Fail-closed throughout.

*(b) Erasure is walled in four independent places and I could not find a fifth route.* The stored field is
`List[str]` so nothing is dropped at READ time (§2); AC-4 leg (b) asserts the raw string survives by
equality against the note's bytes; AC-5 leg (c)'s TOTAL-value count catches a run that deleted what the key
oracle excludes; and AC-5 leg (e)'s never-clears conjunct makes the erase-to-convert build red BY INTENT.
Rejected items 8 and 17 name the two branches a build reaches by default. This is thorough and I am not
adding to it.

*(c) The 82 class-C repairs are an irreversible semantic rewrite whose oracle is structurally blind to a
wrong one, and the one member the grounding artifact flagged for human eyes has no channel to reach
them.* This is the finding, and it is M1.

The repair is spelled `f"{parse(v).phone_digits}@s.whatsapp.net"` (§7). AC-5 leg (d) asserts it
key-preserving — but key preservation is TRUE BY CONSTRUCTION of that spelling, not evidence about the
result: the pre-migration key is `phone:<normalize_phone(v)>` and the post-migration key is
`phone:<normalize_phone(f"{digits}@s.whatsapp.net")>`, and `normalize_phone` splits at the first `@`
(`phone_normalization.py:52`), so the two are equal for ANY digit run whatsoever. A value carrying two
numbers or a number plus an extension — `"+44 20 7946 0958 x212"` → digits `442079460958212` — is class C,
is phone-bearing, passes the guard, is rewritten into a fabricated JID that belongs to nobody, and passes
leg (c)'s multiset oracle and leg (d)'s key-preservation assertion identically. The readback cannot see it,
by construction.

How large is the exposure, measured rather than imagined: the census's `(c')` splits line
(`docs/wi-032-whatsapp-corpus-census.md:172`, and the script that produced it at `:96-101`) reports
`C:bare-number(no @)` **82** and `C:digits-already-in-own-phones[]` **81**. That second number is computed
with `phones_match` against the note's own `phones[]`, which demands full-digit-string equality modulo a UK
or US country-code prefix (`phone_normalization.py:58-90`) — so 81 of the 82 are independently corroborated
as single well-formed numbers, and **exactly one is not**. The census says so itself and prescribes the
remedy: "it is the one row worth eyeballing in the dry run" (`:207-208`). The design cannot deliver that.
`## Approach` step (4), AC-5 leg (a) and `## Verification`'s close-out step 2 all describe the dry run's
output as per-cell COUNTS, consistently and exclusively; nothing anywhere prints a proposed rewrite. So the
conductor takes an irreversible go/no-go on 82 rewrites off aggregate counts, and the single member the
audit-before-patching artifact singled out is invisible at the only moment a human is in the loop. Note
that the DATA already exists — `apply_migration(vault_path, plan)` consumes a `MigrationPlan` that must
already hold the per-note action — so this is a print, not a redesign.

The back-out makes this matter rather than being a second issue: reverting the library is not a back-out at
all (a list-shaped note against pre-WI-032 code raises `SchemaDriftError` and lands on the load skip
surface — INVISIBLE, `parser.py:203-208`), and the reverse migration is "exact up to 82 canonical
re-spellings" (F14, architect round-9 note 3, folded). There is no ledger of pre-migration bytes anywhere,
so a wrong repair is not recoverable from any artifact this item produces. M1.

**Repudiation — adequate, with one conflict M2 exists to stop.** Refusals carry a stable distinct
`pattern` so a bad JID is never routed or reported as a bad name (AC-3 conjunct 1, and F18 leg 4 is why it
is a gate-local literal rather than a Tier-1 branch record). The residual R has a PERSISTENT audit surface
— AC-3's REPORT LEG detector, `Severity.ERROR`, its own check name, `auto_fixable` at its `False` default —
which is a genuine improvement over VD-4's measured nothing, and the exit figure is taken twice by two
different tools that must agree rather than by the migrating process reporting on itself. The run's own
accountability is the bracketed entry/exit doc plus the triple reconciliation with a non-zero exit naming
the part that disagreed.

The conflict: M1 asks for more per-note detail at the go/no-go, and the natural place a conductor puts
detail they were shown is the tracked bracket document — where those pairs are 82 real telephone numbers.
Task 13 already says "Counts, classes and code paths only: no vault note name, no live identifier", and the
close-out replay says "Redact the transcript before it is recorded in any tracked document" — but nothing
mechanical enforces either, because `docs` is a member of `DOC_SCAN_EXCLUDED`
(`tests/test_vault_path_required.py:387`, re-read: `{".git", ".venv", "docs", "state", "node_modules"}`,
intersected against every path part at `:425`), so `docs/**` is outside that markdown scan's domain
entirely and the item's own `## Verification` table states as much. A transparency mitigation implemented
naively becomes an information-disclosure defect, so M1 ships with M2 rather than after it.

**Information disclosure — the one channel this item OPENS is correctly built, and I verified it rather
than accepting F4.** `_refuse` is the single refusal construction site and its rule 2 is explicit that no
note-derived value enters the CONSTRUCTOR (`name_gate.py:142-174`, read this round — the reason given is
that `NameValidationError` interpolates the raw name at all nine branch sites and at two of them that name
IS an email address). §3 adds `exc.refused_value = refused_value` set AFTER construction, exactly as
`pattern` already is, so: `str(exc)` is `_REFUSAL_REASON`; `repr(exc)` renders `args`, which the value is
not in; a default traceback renders neither; and `chainable_cause` suppression is inherited unchanged
because the arm passes no `cause` and raises from no handler. AC-3 conjunct (1) asserts "NOT in its
message" and `## Verification` asserts absent "from the message and from the traceback". Correctly
designed side channel, adequately asserted, no mitigation.

The other four channels, each checked: the detector's `LintIssue` message carries a COUNT and CLASS LETTERS
and no note-derived value (§4) — the same discipline `_refuse` keeps; `IdentifierError`'s message is
`f"{kind}: {detail}"` with the raw value on `.raw` as an attribute only (`identifier.py:76-80`), so the
container refusal leaks nothing either; `_gate_refusal_pattern` splices only a PATTERN into a lint message
and is left untouched by this item (`## Write Targets`); and the two grounding artifacts already in HEAD are
counts-and-code-paths with `$VAULT`/`$BRIDGE_DB` rendered. The live bracket doc is the one artifact with
real pressure on it, and that is M2.

**Denial of service — nothing to mitigate.** No outbound call, no credential, no third party, so no rate
limit, cost ceiling or backoff is in scope. The migration is a bounded single pass over ~1168 local files
taking one per-note lock and holding none across notes; `--apply` is ABSENT by default so the expensive,
irreversible arm requires an explicit flag. The one availability surface that would matter is the repair
tool crashing on the malformed data it exists to find, and that is closed on purpose: §4 wraps the
classifier call and reports the unclassifiable note under the SAME check, with a nested-container plant
exercising the arm rather than assuming it (Task 9), and Risk row 8 names it. I traced the type space into
`classify`/`classify_field` looking for an unhandled shape and found none — containers refuse, `None` and
blank file as Ø, and every other scalar reaches `parse` through `str(raw)`.

**Elevation of privilege — closed by an existing wall, and the item leans on it correctly.** The realistic
privilege case here is not a user gaining access, it is a PROCESS reaching the live vault when it was meant
to reach a temp one. Three things close it and all three are load-bearing rather than decorative: `--vault`
is `required=True` with `OBSIDIAN_VAULT_PATH` named nowhere in the module, so the live vault is
unreachable by OMISSION (§7, against `FORBIDDEN_DEFAULT_PATTERNS` — `expanduser`, `Path.home()`,
`/Users/` — which `tests/test_vault_path_required.py` asserts zero live matches of across
`obsidian_schemas/**` and `scripts/**`); the dry run is the default and `--apply` is opt-in; and Task 11
makes the containment wall NON-VACUOUS over the new module by adding `apply_migration` to
`MUTATING_DRIVE_VAULT_POSITIONS` before asserting six clauses over it, having noticed that
`mutating_drive_vault_args` collects nothing until the dict names the entry point (§8). That last one is
the mitigation a less careful spec would have shipped as an empty wall, and §8 also declares the ONE
sub-assertion it cannot take and replaces it with a strictly stronger one
(`not hasattr(migrate, "DEFAULT_VAULT")`). No new package capability: `ITEM_EDITED_QUALNAMES`' rows assert
the edited frames join no write universe and bind no frontmatter payload (F20 leg 5), which holds because
the gate call and the writer delegation were already there. Nothing to add.

### Mitigations verified in place

Stated so a later reader can tell what this gate CHECKED from what it merely did not object to.

1. **The enforcement point is the surface every writer shares, not the field type.** `gate_write` with
   `tests/test_name_gate_wall.py` proving by DERIVATION that no frontmatter-writing arm routes around it
   (F1), and AC-3's arm set derived from the tree and asserted in scope by EQUALITY rather than hand-listed.
   A pydantic validator would have missed the three dict doors — the exact class the incident value arrived
   through (`docs/write-door-bypasses.md:3993-3996`). Rejected item 1.
2. **Refusal names the value as an ATTRIBUTE and never in a message or traceback.** Verified above against
   `name_gate.py:142-174`, Design §3 and AC-3 conjunct (1).
3. **Fail-CLOSED at both trust boundaries.** A caller's bad value is refused with nothing written and the
   target note byte-identical and an absent target not created (AC-3 conjunct 2); a note's own stored bad
   value refuses the whole-record re-serialization while every delta write still succeeds
   (`name_gate.py:31-36`), so the remedy is not the disease.
4. **Absence is never a refusal, which is what keeps the repair channel open.** Class Ø accepted at every
   arm in every spelling, and CLEARING asserted at every delta arm in both of the package's spellings —
   the only repair a class-D value has, since the writer carries no delete affordance
   (`writer.py:333-337`). F16, AC-3's CLEARING and CLASS-Ø legs. This is a mitigation against a
   self-inflicted denial of repair and it is the strongest single correction in the document's history.
5. **Nothing dataclass-shaped reaches `yaml.dump`,** closed by construction rather than by a projection
   step someone must remember, with `no !!python/object in the bytes` retained as the guard that keeps it
   true whichever way a future implementation goes (F8, F13 leg 1, AC-4 leg b, rejected item 9). A note
   this package's own reader cannot load is a self-inflicted availability failure and it is walled.
6. **Verify-by-readback means a re-READ.** AC-5 leg (c)'s oracle is computed from the note BYTES by a load
   that did not exist before the write, never through the migrating process's own cache — the
   private-stale-replica shape, named and closed.
7. **No live identifier enters the frozen fixture corpus or its manifest.** WI-016's privacy wall is
   satisfied by yielding to it rather than by widening it (arm (a), rejected item 11), every planted digit
   run is an unused reserved-block member verified unclaimed tree-wide, and the one real identifier in the
   set is confined to a test module with an explicit never-move-it instruction (F17 leg 2, F18 leg 6).

### Required mitigations

Three. Each is additive to an existing task, none asks for a change to any `criteria` fence, and none
touches Ruling A, B or C — so no D4b re-sign is implied by any of them.

```mitigation
kind: required
id: M1
desc: The DRY RUN must print the class-C repair as per-note (stored value -> proposed JID) pairs and flag every member whose digits are not already in its own `phones[]`, so the 82 irreversible re-spellings are authorized with the rewrites VISIBLE rather than off aggregate per-cell counts — AC-5 leg (d)'s key-preservation is true by construction of the repair spelling (both keys derive from the same `normalize_phone` output, `phone_normalization.py:52`) and so is not evidence the digits are the right number, and the census itself singles out the one uncorroborated member as "the one row worth eyeballing in the dry run" (`docs/wi-032-whatsapp-corpus-census.md:207-208`) while nothing in the design can show it.
landed: Task 10
```

```mitigation
kind: required
id: M2
desc: The M1 pairs and the detector's per-note issue lines stay on stdout for the go/no-go and are NEVER written into `docs/wi-032-whatsapp-live-baseline.md` or any other tracked document, which carries counts, classes and code paths only — `docs` is a member of `DOC_SCAN_EXCLUDED` (`tests/test_vault_path_required.py:387`, intersected at `:425`) so `docs/**` is outside the markdown scan's domain and nothing mechanical catches a pasted live identifier.
landed: Task 13
```

```mitigation
kind: required
id: M3
desc: The bracket's ENTRY row must separate `orchestrator/bin/merge-duplicate-persons.py:380-384` from the two loud consumer breaks and state it as a DATA-LOSS HOLD rather than as the third item of one list — it regex-reads a single `whatsapp` line and re-emits a scalar through `Path.write_text` outside the package boundary, so against a migrated vault it can silently drop a person's second JID or blank the field, which is the exact harm this item exists to prevent and the only one of the three measured breaks that does not announce itself.
landed: Task 13
```

### Notes (non-blocking)

1. **The container refusal raises outside the documented catch hierarchy.** `classify`'s container guard
   raises `IdentifierError`, which is a plain `ValueError` (`identifier.py:67`) and NOT a member of the
   `LoudFailError` tree (`errors.py:37`, `:106`), and `## Edge Cases` decides the gate does not catch it.
   So one write door raises two exception types for two of its arms and only one is reachable by the
   estate's documented `except LoudFailError` idiom. Not raised as a mitigation because it fails CLOSED
   (nothing is written), leaks nothing (the message is `kind: detail` with the raw value on an attribute),
   and the shape can only arrive from a caller's raw dict — a stored container is rejected by
   `List[str]` validation and lands on the load skip surface long before `save`. Worth one sentence in
   `## Edge Cases`' error-propagation entry so a consumer author is not surprised.
2. **`_refuse` gains a keyword that accepts a note-derived value, on the site shared with the NAME arms.**
   The name arms pass nothing through it and are unchanged, so nothing leaks today. But the channel now
   exists on the one construction site whose rule 2 exists to keep note bytes off it, and the natural
   future edit is "the name refusal should name its value too" — which is the one refusal where the value
   can BE an email address. One line in the `_refuse` docstring saying the keyword is for the whatsapp arm
   and that the name arms deliberately pass nothing costs nothing and is where a future reader looks.
3. **AC-3 requires a real person's telephone number as a test-module literal, and it need not have.**
   `"+44 7739 341679"` is Kim Faura's number; F18 leg 6's argument for re-typing it is sound as far as it
   goes (already committed twice in this tree, admissible outside the wall's reach, zero marginal
   disclosure), but the criterion's own purpose — proving a parse-only door accepts a bare number — is
   served identically by a reserved-block bare number, so the real value is load-bearing for the NARRATIVE
   and not for the assertion. Deliberately not a mitigation: AC-3 is frozen by Dave's signature and this
   would be a D4b re-sign to buy a disclosure delta of zero. Recorded so the next item to touch this
   criterion prefers a reserved literal.
4. **One positive consequence worth naming because nobody claimed it.** A hand-edited
   `whatsapp: 447700900123` without quotes loads as a YAML int, which `whatsapp: str` rejects today — so the
   note raises `SchemaDriftError` and goes INVISIBLE, and the census's skip surface of 0 shows no live
   member. The new detector reads RAW frontmatter (`vf.frontmatter`), so it classifies that value and
   REPORTS the note. The report arm therefore gives this repo a discovery channel for a shape that is
   currently invisible to every consumer — an availability improvement the document does not claim.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-27
model: claude-opus-5
note: STRIDE-lite over the two declared trust boundaries plus the migration finds the design's security posture sound — the gate (not the field type) as the enforcement point proven by derivation, refusal-by-attribute verified against `_refuse`'s own rule 2 so the value reaches no message, repr or traceback, fail-closed at both boundaries with the delta arms deliberately left open so the repair channel is not bricked, erasure walled four independent ways, and privilege-by-default closed by a required `--vault` plus an opt-in `--apply` plus a containment wall Task 11 makes non-vacuous; the one real finding is Tampering, not a gap in the approach — the 82 class-C repairs are irreversible and AC-5 leg (d)'s key-preservation is true by construction of the repair spelling (both keys derive from the same `normalize_phone` output), so the readback is blind to a fabricated digit run, and the single member the census flagged as needing human eyes has no channel to reach them because every description of the dry run's output is per-cell counts — M1 folds the per-note repair disclosure into Task 10, M2 keeps it off the tracked bracket (`docs/**` is outside the markdown scan), and M3 promotes the one silent destructive consumer break to a data-loss hold; no criterion text moves and no ruling is touched.
```


## Spec Review — 2026-09-27

**Recommendation: REVISE — return to spec writer (two gaps to fix)**

Rulings on record: Rulings A, B and C are RULED (Dave, 2026-09-27) and the ACs are FROZEN by his signature (`ac_hash dd772c1183de`); nothing below reopens any of them, and both findings are plan-task and Design additions that move no `criteria` fence — the same shape the M1/M2/M3 folds already used.

Round 1 at this gate, cold-start read at `specced`. Read from line 1 in full, including the archived-rounds pointer's live carry-forward (architect rounds 1–3 and 9, AC red-team round 8, both conductor notes, the AC sign-off, the data audit and the threat model). Every in-tree citation below was resolved by reading the code at it, not by trusting the injected drift audit.

### Citation verification

**All verified ✓ — and re-read for the PROPERTY each claim asserts, not only for symbol existence.** The injected audit reported 13 symbol-anchored citations resolved with 0 findings; that is a floor. I read the code at every load-bearing citation in `## Problem / Motivation`, the two-predicate definition, F1–F21, `## Verified Diagnosis`, `## Design` §1–§10, `## Prerequisites`, `## Verification`'s regression census and all five `criteria` fences. Nothing is stale and nothing describes code that does something else. The ones most worth recording because a wrong reading would have changed a decision:

- `identifier.py:WhatsAppJID.parse:269-281` — tests the `@lid` SUBSTRING at `:276`, `Phone.MIN_DIGITS` at `:279`, a JID domain NOWHERE; raises on `None` and on blank through the same two lines it raises on `"n/a"` with (`:271-275`, no blank branch). VD-2 and F16 hold exactly. `parse` stores `str(raw).strip().lower()` (`:273`, `:277`, `:281`) and retains no raw value, so §1's "`jid_domain` off `self.jid` is the only buildable spelling" is right rather than merely convenient.
- `name_gate.py:31-36` reads verbatim "A stored-dirty note stays writable for every write that does not re-introduce its name" — F21's terminal-state derivation rests on this and it is faithful. `_refuse:142-174` admits no note-derived value into the constructor and sets `pattern` as an attribute after construction, so §3's `refused_value` keyword is the same channel and not a new one. `_shaped`/`_is_str_list:181-198` is the POSITIVE predicate F2 says it is; `result = dict(introduced)` at `:346` means §3's arm can assign `result[WHATSAPP_KEY]` without growing the key set.
- `person.py` — `_index_entity:257-284` with the whatsapp block at `:266-270` and `_index_identifiers` at `:283-284`; `add()`'s blank guard at `:319` is `isinstance(raw, str) and not raw.strip()`, which a list passes, so the round-8 iterate-the-list trap is real; `_remove_entity_from_indexes:404-439`; `get_by_phone`'s permanent fuzzy arm over a materialized snapshot at `:481-496`; `resolve_all`'s blank-query bail-out at `:608-609` and its step 4 at `:646-651`, so §5(e)'s "immediately after step 4, below the bail-out" is executable; `_IDENTIFIER_PRIORITY` at `:778` with its explaining comment at `:772-777`; `_resolve_identifier:886-909`; `_hydrate:931-936` is None-safe, so §5(d)'s one-liner is correct; `save:1155-1200` with the docstring at `:1158-1189`, the rider at `:1190-1194` and the two trailing comments at `:1195-1196`.
- `prose_surface_cut0.json` holds **29** `PersonRepository.save` records (re-run: `rg -c '"owner": "PersonRepository\.save"'` → 29), confirming round 7's correction against the two arriving fences' 31. `AUTHORIZED_PROSE_OWNERS` at `tests/test_identity_endgame.py:359-373` is thirteen members and contains neither `PersonRepository.save` nor the bare class; clause (e1) at `:1008-1019` compares on `(owner, text)` so an APPEND is free, and clause (e2) at `:1021-1030` does require an authorized owner to LOSE a Cut-0 line — rejected item 15's analysis is exactly right.
- The corpus contracts: `_person`'s `whatsapp: ""` default at `tests/fixture_vault.py:94`; Thrandell's override at `:225` with `roundtrip_representative=True` at `:232`, uniqueness asserted at `tests/test_fixture_vault.py:689-695`; the three whole-record readers at `tests/test_writer.py:421`, `tests/test_fixture_vault.py:753` and `tests/test_parser.py:263-266`; `@Fennwick Drostane.md:7` is `whatsapp: ""` and the note declares no `shape_classes`, no verdict and no divergence (`tests/fixture_vault.py:340-341`); the privacy wall at `tests/test_fixture_vault.py:302-319` with `RESERVED_PHONE_PATTERNS` at `:308-312` and `reach_files()` at `:386-392`. I drove every pinned literal through those patterns by hand: `15555550142`, `15555550163`, `5555550142` and `5555550163` match `^1?\d{3}55501\d{2}$`, and `447700900321`/`447700900654`/`447700900987` match `^447700900\d{3}$`. `rg 'whatsapp' tests/fixtures/vault` → 22 files, one line each, so F6's 22/21/1 is exact.
- The census's digest has no build-owned home: `declared_census_digest` reads it out of WI-016's SIGNED AC-3 fence (`tests/test_fixture_vault.py:217-254`) and the value stands at `docs/vault-fixtures.md:1418`. F18 leg 1's retraction is correct. `docs/vault-fixtures.md:5938-5948` records both precedents the fold copies (deviation 3's move-it-in-the-corpus, deviation 4's `@example.com` JID spelling).
- The census artifact's figures reconcile: `(a)` 1174, `(c)` Ø 1031 / A 35 / B 26 / C 82 / D 0 / E 0, `(c')` absent-key 6 + empty-string 1025 + null 0, `C:digits-already-in-own-phones[]` 81 of 82, `(b)` scalar 1168, `(f)` 51, `(g)` 172/26/0. Every derived partition figure the bracket carries is computable from `(a)`, `(c)` and `(c')` as Task 13 (ii) requires: 1168 = 1174 − 6, MIGRATED = 1168 − 0, shape-only 1025, repairs 82, `|R|` 0. The ~88% claim checks out (1025/1168 = 87.8%) and the 143-vs-1168 cost sentence is 35 + 26 + 82.
- The redaction wall's measured claims are true in this worktree, which matters because Task 13 ships them as fixtures: `rg '[0-9]{9,}'` over `docs/wi-032-consumer-audit.md` returns exactly two lines, `:92` and `:144`, and both runs (`984664193`, `5889539193`) sit INSIDE 40-hex HEADs; the same predicate over `docs/wi-032-whatsapp-corpus-census.md` returns nothing, and neither artifact carries a digit-immediately-before-`@`. So the MUST-NOT-match fixture `27cb78cc5a2099972dccea984664193e69414def` is the right specimen and the near-miss list is not imagined.
- `docs/stem-divergence-live-baseline.md:124` ("divergent rows the WRITE DOOR refuses (b3): 0 of 8") and `:191` (8 → 0) are verbatim; `docs/write-door-bypasses.md:3993-3996` carries the Kim Faura value at `:3994`; `docs/migration-support.md:20-22` carries WI-010's un-park criterion; `pipeline-runners.yaml:32-33` excludes the project root and `:34-38` includes `scripts/`.
- The containment wall's shape at `tests/test_stem_name_divergence_detector.py:141-192` is exactly the six clauses plus the runtime door, and its `_temp_vault` door reads `lint_vault.DEFAULT_VAULT` at `:128` alongside `os.environ.get("OBSIDIAN_VAULT_PATH", "")` — so §8's "the third token has no home in a script with no `DEFAULT_VAULT`, and its absence is PROVEN rather than omitted" is a correct reading of `LIVE_PATH_TOKENS` (`tests/derivations.py:2034`), not a narrowing.

One nit rather than drift: F5 brackets `resolve_all`'s cascade as `person.py:628-690` while VD-3 brackets the same frame as `:606-690`. Both contain it; neither misleads.

### Blocking issues

**1. AC-3's APPEND-ONLY conjunct (2) asks for an oracle no post-build hermetic check can compute, and no section names the computable form — so the one conjunct the criterion's own `why:` says does work WI-024's wall cannot is satisfiable by silence.** The conjunct is "`AUTHORIZED_PROSE_OWNERS` still has exactly its thirteen declared members **and `prose_surface_cut0.json` is byte-identical to its pre-build bytes**", and Task 8 orders all three conjuncts "computed through `prose_lines`". The first half is computable (import the tuple, assert its members). The second is not, twice over: `prose_lines` (`tests/derivations.py:1773`) reads SOURCE comments and docstrings and never that JSON, and a check running after the build has no referent for "pre-build bytes" — there is no shell in the check, the file is not a write target, and a digest literal the build itself takes is the self-certifying constant WI-016's own AC-3(iv) `why:` exists to refuse. So a builder has three self-consistent exits and the spec picks none: hardcode a build-taken digest (certifies nothing), re-read it as conjunct (1) (which reads its expected pairs FROM the same JSON, so a build that DELETED save records satisfies (e1), conjunct (1) and (e2) together — verbatim rejected item 15's sibling, and the exact route this conjunct exists to close), or drop it as unachievable. **Suggested fix, and it is one clause in `## Design` §6 plus one in Task 8:** state the computable form the document's own literals already support — the JSON holds exactly **29** records owned by `PersonRepository.save` (`prose_surface_cut0.json:2400-2544`, the figure four sections already print) and `AUTHORIZED_PROSE_OWNERS` equals its thirteen declared members, both read at test time. That is the same "assert the count of the frozen population, read from the artifact, against a literal the document states" move F18 leg 1 prescribes for the census, and it makes the delete-a-record build RED. This is the F19/F21 generator one artifact further on — a conjunct a fold ADDED whose oracle the fold never derived — which is why it is blocking rather than a note: the clause reads as already-guaranteed and two of the three builds that satisfy it do nothing.

**2. The migration's re-run behaviour is RESOLVED in `## Edge Cases` and asserted nowhere, and it is the remedy the same section promises a conductor mid-migration on the live vault.** `## Edge Cases`' "First-run vs subsequent-run" decides "the second run finds every convertible note already list-shaped, classifies it MIGRATED, and **writes nothing**", and "Retry semantics" makes that load-bearing for the irreversible half: "the run exits non-zero having written whatever it committed, and the REMEDY is to re-run the dry run… a partial run leaves a vault in which the same command computes the correct remaining work." Neither is behind a `check:`. The `## Edge Cases` "Idempotency" entry names three asserted levels — the dry run's digest, `gate_write`'s own idempotence, and load→save→load — and the migration's own re-run is not among them; AC-5's five legs assert a single pass; and `## Design` §7's action-table row "already a list, every member in `{A,B}` → **no write** — already migrated" is reached only by AC-5's two-JID plant (which must be list-shaped from the start), which discriminates ABORT-on-a-list from correct but cannot discriminate "no write" from "re-write the same bytes". So the behaviour the conductor's retry path depends on is decided in prose and unpinned, which is the class Check 4's test-coupling clause names and the class F19 closed one artifact over. **Suggested fix, three lines inside a task that already drives `apply_migration` and no criterion moved:** add to Task 10 that the check drives `apply_migration` a SECOND time over the already-migrated copy and asserts the tree digest is byte-identical across it (the same digest leg (a) already takes) and that the triple reports the residual R unchanged and zero notes converted — so a build that re-writes, or one that aborts on a list-shaped note, is RED by intent rather than by luck. Honest pricing, so the fix is not over-bought: the harm of the wrong build is write churn over ~1168 live notes and a broken retry promise, not data loss.

### Non-blocking notes

- **A blank member INSIDE a list is classified `Ø` per-value and therefore REFUSED by the gate arm, while AC-3's CLASS-Ø leg says class Ø is accepted "in every spelling … and in both shapes".** `classify_field`'s list branch maps `classify` over members with no falsiness filter, `classify("")` returns `CLASS_ABSENT`, and §3's arm refuses anything `not in ("A", "B")` — so `{"whatsapp": [""]}` is refused with the whatsapp pattern while `{"whatsapp": ""}` is accepted. The Design is internally determined and the criterion's five enumerated spellings (of which `[]` is the list-shaped one) are satisfiable as written, so nothing ships two ways; and no required fixture or migration arm produces `[""]`. But it diverges from the `emails[]` precedent this document cites for the rule (`name_gate.py:399` neither parses nor keeps a blank member), and a test author writing the CLASS-Ø leg's "both shapes" is the one reader who will reach for `[""]`. One sentence in §3 saying a blank member inside a list is refused (or filtering it in `classify_field`'s list branch) closes it.
- **Three imports the Design's code blocks use and no section names.** `identifier.py` imports `ClassVar, FrozenSet, Optional, Tuple` and not `List`, which §1's `classify_field(cls, stored) -> List[str]` needs (harmless at runtime under `from __future__ import annotations`, wrong for a type checker); `scripts/lint_vault.py` imports neither `WhatsAppJID` nor `IdentifierError`, which §4's arm calls; `models.py` needs `field_validator` for §2. All trivial, listed only so the builder is not the one to notice.
- **§1's `classify_field` tail comment says `# a non-str scalar: `parse` decides, →D` and the arrow is wrong for the one live shape it matters for.** An unquoted `whatsapp: 447700900123` loads as a YAML int, `str()`s to twelve digits and lands in class **C**, not D — which is the behaviour threat-model note 4 correctly claims as a new discovery channel. The code is right; the comment mis-states its own example.
- **Task 12 orders the `NO_ARG_CONSTRUCTION` sweep over "the two `docs/wi-032-*` files this item writes".** It writes one (`docs/wi-032-whatsapp-live-baseline.md`); the other two are conductor preconditions. Task 13's redaction duty gets the count right ("all THREE"). I ran `NO_ARG_CONSTRUCTION` (`\w+Repository\(\s*\)`) over this document by hand and it finds nothing, so the sweep is green either way.
- **F18 leg 2 is one word too strong about the census verdict loop.** It says the loop "writes EVERY shape-class specimen's whole declared field set through the gated door"; at `tests/test_fixture_vault.py:856-891` only the `kind == "refusal"` specimens are written (`:870`), the `cleaned` and `loads` arms never touch the door. The receiver constraint the leg derives from it is still right and is conservative in the right direction.
- **Task 10 is the one task that is not a sitting.** A new four-entry-point module with a seven-arm action table, the `RepairDisclosure` record and formatter, AC-5's five-leg check and M1's disclosure check, in one checkbox. It could not be split without breaking `landed: Task 10`, so this is an observation rather than a fix request — but it is the longest unresumable stretch in the plan and the abort ledger is per-checkbox.

### Bar check

Walked every check of `docs/spec-quality-bar.md` (the doc's own list is the count — never hardcoded). Satisfied except where the two blocking issues bite Checks 4 and 6.

- **Check 1 Self-containment** ✓ — nothing requires session memory; the three rulings, the class table, the six-cell classifier, the action table and the plant accounting are all in-document.
- **Check 2 Prerequisites** ✓ — nine stated, including the two trust boundaries, the `.venv` staleness, the `README.md` non-writability and an atomic-landing check that was RUN rather than assumed. Both `kind: precondition` fences carry `grounds:` naming one premise and both paths are in git HEAD, which is the WI-300 ordering satisfied rather than claimed.
- **Check 3 Interface contracts** ✓ — see above. No cross-doc `writes` fence, so no merge authorization is being held.
- **Check 4 Edge cases** — all ten categories walked in Case/Decision/Reasoning form, `OPEN: None`. The test-coupling cross-walk is where blocking issue 2 lands; every other resolved case maps to a named check.
- **Check 5 Implementation plan** ✓ — fourteen canonical `- [ ] **Task N — …**` definitions, ordinals 1–14 unique, dependency-ordered, parallelism noted. Every task carries a well-formed lowercase `verify:` declaration: eleven check arms (all names resolving, Task 5's three against existing checks `test_fixture_vault_is_frozen_and_materialized_by_byte_copy`, `test_corpus_note_round_trips_through_the_write_door`, `test_corpus_person_note_parses_to_its_declared_values`, each unique under `check_module`), one `baseline` and one `hand-run`, both reasons inside 200 characters. No illustrative declaration begins a segment. No verify command writes: every one is a check name or the declared floor command, and nothing orders a state-writing linter form, an `advance`, or a commit.
- **Check 6 Verification** ✓ except blocking issue 1 — happy path, graceful failures, integration and a DERIVED regression census with its floor caveat stated. Oracle derivation is unusually strong (every AC computes its expected value by CALLING the predicates; AC-5's readback is pinned as a re-READ from note bytes). The inbound WI-301 half is discharged by Task 12 RUNNING each wall's own predicate rather than reasoning about shapes. The three counting walls each ship match-shapes through the wall's own predicate: the arm set's are already standing (`tests/test_name_gate_wall.py:373-404` drives the three callee forms and two binding forms, with the four save-shaped non-members at `:362-370`), the containment scan's are ordered in Task 11, and the redaction predicate's MUST/MUST-NOT lists are ordered in Task 13 and are measured rather than imagined. The corpus-fixture arm is chosen and its coupling declared in one line.
- **Check 7 Scope boundary** ✓ — nine not-doing items and an unchanged-files list that says WHY per file, including the five walls the item JOINS.
- **Check 8 Pattern consistency** ✓ — every mechanism is this repo's own, with the model code cited: WI-029's detector shape for §4, WI-021's `_refuse` contract for §3, WI-016's deviation-3 fold for §9, WI-029's containment wall for §8, WI-033's derived-accessor precedent for §2.
- **Check 9 Risk analysis** ✓ — nine rows with honest likelihoods (row 4 is CERTAIN) and concrete mitigations naming criteria and rejected items.
- **Check 10 Acceptance criteria** ✓ — five well-formed fences, all `kind: test`, all `check:` bare function names that resolve uniquely; no `kind: command` and so no shell-safety question. Class-closing criteria derive their fixture space by calling the predicates and PLANT the discriminating members the corpus cannot supply (AC-1's class-B control, AC-5's two-JID note), which is WI-185 plus WI-286 both honoured.
- **Check 11 Verified diagnosis** ✓ and SUFFICIENT — four load-bearing diagnostic claims, each cited to a falsifiable artifact I read, and each artifact actually supports its specific claim: VD-1's zero-match grep and `_CONTAINER_KEYS`; VD-2's `parse` body plus 82 measured live members; VD-3's unconditional `normalize_phone` insert plus the permanent fuzzy arm plus 26 measured lids; VD-4's two-line `rg` plus the 8 → 0 bracket. The "Not claimed, and deliberately" paragraph correctly keeps the consumer-break claim out of this section.
- **Check 12 AC drift** — the frozen set is the `exploring` origination (`ESC-WI-032-exploring-awaiting-ac-signoff-eb28d58c`, `ac_hash dd772c1183de` with five per-AC hashes), and `## Acceptance Criteria` IS that set rather than an evolution of an earlier one, so there is no diff to classify. What I could check independently, I did: every post-signature fold landed as a plan-task rider or a `## Design` subsection and not as criterion text (the three mitigation folds say so and Task 10/Task 13 are where they landed); the four absolutes-sweep rows the spec-writer added QUOTE AC text without moving it; and the census fence's one wrong clause is corrected DOWNSTREAM with the fence left verbatim, which is the discipline this check exists to protect. No strength-weakening, actor-swap, scope-narrowing, oracle-swap or exception-carving-by-addition found. Two scopings inside AC descs (AC-4 leg (c)'s population, AC-5 leg (d)'s both-arms correction) predate the signature and are the round-8 fold, not drift.

**Printed HEAD literals.** Every number the bracket will print is computed under the census's own declared rules rather than off a raw match count — the census's `classify` calls `WhatsAppJID.parse` and reads the domain off `j.jid`, its class-Ø test precedes both predicate calls, and its `(c')` splits line is what makes the 1025-vs-1031 distinction available at all. The literals are not labeled FROZEN or LIVE in those words, but they are treated correctly: Task 13 (ii) pins the bracket by DERIVATION against the census's own verbatim stdout block rather than against the live vault, `## Approach` step (4) puts the live dry run's counts beside the census's in front of Dave so drift is surfaced to a human, and nothing this build does appends to the population the pin froze. So the failure this rule guards — an equality pin reddening against correct code because the item's own arc grew the population — cannot fire here.

### Build-runner dry-run

Walked the Implementation Plan top-to-bottom as the build-runner. Tasks 1–7, 9, 11, 12 and 14 execute without leaving the document: the code blocks are literal, the placements are prescribed (the gate arm between steps 3 and 4, the detector between `stem_name_divergence` and `field_type_mismatch`, the cascade step immediately after step 4 and below the blank-query bail-out), the corpus edit names the receiver AND the constraint behind it, and every assertion's oracle is a call rather than a literal. The ordering is sound, including the one transient red it creates (between Task 3 and Task 5 the corpus's declared `whatsapp` oracle is a scalar while the tolerant reader returns a collection — Task 5 closes it and Task 5's own verify is the three checks that go red on a half-done edit). I re-derived the four wall interactions a builder would otherwise discover: `apply_fixes` never buckets a non-auto-fixable issue (`scripts/lint_vault.py:1038`) so WI-026's four-bucket total is untouched; `_divergence_issues` filters on `issue.check` so the new detector is invisible to that module; `_door_refusal_pattern`'s five subjects in `tests/test_provenance_write_seam.py` are the four divergent notes plus the name-sharing group, all class Ø, so the seam battery is green under both corpus edits; and every `repo.save(person)` in `tests/test_repositories.py:644-725` is over a fresh `Person` whose `whatsapp` defaults to the empty collection, so the "predicted GREEN, run rather than edited" claim for the three undeclared test modules holds — `_note` and the John Smith fixture write raw bytes, and `tests/test_parser.py:153-180` asserts nothing about the field.

Three questions a build-runner would plausibly ask, and the two the document does not answer are blocking issues 1 and 2; the third is the blank-list-member note above.

**Write-Targets coverage.** Ran the per-task extraction. Fifteen builder fences, and every task's named target is present: Task 2 → `identifier.py` + `test_identifier.py` + `test_whatsapp_jid_storage.py`; Task 3 → `models.py`; Task 4 → `name_gate.py` + `test_whatsapp_write_door.py`; Task 5 → `fixture_vault.py` + the two corpus notes; Tasks 6–8 → `repositories/person.py`; Task 9 → `scripts/lint_vault.py`; Task 10 → `scripts/migrate_whatsapp_to_list.py` + `test_whatsapp_migration.py`; Task 11 → `tests/derivations.py`; Task 13 → `docs/wi-032-whatsapp-live-baseline.md`. No fence declares a path no task writes, and the three absences a reader looks for are each declared with a reason (`README.md` outside `write_authority`, `docs/vault-shape-census.md` another item's frozen artifact, `tests/test_fixture_vault.py` a wall the item joins). The declaration names the item's real touch surface, so the review-level selector reads neither more nor less than the build touches. No conscious-pin sweep is owed: the item alters no countable corpus of the `write_authority`/exam-item/gate-list kind, and the one count-bearing population it does touch — `MUTATING_DRIVE_VAULT_POSITIONS` — is enumerated in §8 with its two existing consumers checked (`tests/test_lint_vault_fix_rules.py:288`, `tests/test_stem_name_divergence_detector.py:144`, each scanning its own file only).

**Mitigation folds.** All three `kind: required` mitigations of the latest speaking `## Threat Model` round carry complete, fresh records. I compared each `desc` against the mitigation fence verbatim (all three match), then found each `design` and `work` quote where it claims to be and read the surrounding text rather than judging the pair alone: M1's design sentence is the bolded sentence of §10(a) and its work text is Task 10's M1 RIDER paragraph plus that task's verify line; M2's and M3's are §10(b) and §10(c) and Task 13's two rider paragraphs. All faithful. On satisfaction, which is mine: M1 is satisfied — the disclosure carries the per-note pair AND the corroboration flag computed by calling `phones_match` over the note's own raw `phones[]`, the formatter returns rather than prints so it is assertable in-process, and both arms of Ruling B print it, which is what makes the census's single uncorroborated member reach the human it was flagged for. M2 is satisfied and it keeps holding past close-out — the check pins the §5 HEADING and nothing about its content, while the redaction predicate still ranges over §5, so a conductor's later paste reddens the floor instead of being permanently invisible. M3 is satisfied — the HOLD row carries the pinned HEAD, the reaching callers, the measured `whatsapp: ""` clearing path and the one do-not-run instruction that makes it a hold, and the (iii) SHAPE assertions pin the separation rather than trusting the writer's prose.

### Carried-forward notes

- **Threat-model note 3 (2026-09-27) — STILL OPEN, and correctly deferred.** AC-3 requires `"+44 7739 341679"`, a real person's telephone number, as a test-module literal, and a reserved-block bare number would serve the criterion's own purpose identically. It is deferred because AC-3 is frozen by Dave's signature and the disclosure delta is zero — the value is already committed twice in this tree (`docs/write-door-bypasses.md:3994` and this document) and `## Design` §9 line 5 forbids it ever entering the corpus or its manifest. I re-defer it on the same reasoning and for one more: my own findings are additive and a D4b re-sign bought for a zero delta would be the more expensive error. Recorded so the next item to touch AC-3 prefers a reserved literal.
- Every other prior-round non-blocking note is CLOSED, and I verified each fold rather than taking the fence's word: architect round-9 note 1 (`## Approach` step (4)'s exit row now carries MIGRATED as part (2) with the repair count as a named sub-count), note 2 (the 1025-vs-1031 split stated where the numbers are used, with the census fence corrected downstream and left verbatim), note 3 (both back-out qualifiers, the class-C re-spelling one named first), note 4 (the shape-only population named as the run's one semantically empty part, with Dave's decision point), note 5 (the four sweep rows added); threat-model note 1 (the `IdentifierError`-outside-`LoudFailError` sentence is in `## Edge Cases`' error-propagation entry), note 2 (`_refuse`'s third numbered clause, appended beside rules 1 and 2 in §3), note 4 (informational, nothing to action); data-audit note (i) (the entry row now says "26 notes leave `_phone_index`, 0 live answers move" rather than "no lookup result changes"), note (ii) (the cardinality disclosure is in the ship condition and in §10(c)).

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-27
model: claude-opus-5
targets: AC-3, Task 8, Task 10, #design
prior: none
basis: folded-material
findings: 2/7
note: Citations all verified by reading the code at each (29 `save` prose records, `parse`'s normalize-then-store, `name_gate.py:31-36` verbatim, every pinned literal driven through the privacy wall's own patterns, both grounding artifacts' redaction claims re-measured) and the bar is met everywhere except two unpinned oracles, both landing on clauses earlier folds ADDED and both fixable as plan-task additions with no `criteria` fence moved: AC-3's APPEND-ONLY conjunct (2) asks that `prose_surface_cut0.json` be "byte-identical to its pre-build bytes", which `prose_lines` cannot compute and a post-build hermetic check has no referent for, so the one conjunct WI-024's own (e1)/(e2) cannot supply is satisfiable by silence and the delete-a-record build stays green — the computable form the document's own 29 literal already supports needs stating; and the migration's "a second run writes nothing" is resolved in `## Edge Cases` and asserted nowhere while the same section promises a conductor mid-migration that re-running computes the correct remaining work, with §7's already-a-list arm reached only by a plant that cannot tell "no write" from "re-write the same bytes".
```


## Adversarial Review — 2026-09-27

Cold-start injection-hunter read, model `claude-sonnet-5`, decorrelated from the spec-reviewer's `claude-opus-5`. Read the driven document end-to-end from `## Problem / Motivation` through the current `## Spec Review — 2026-09-27` (5283 lines total, all sections: Exploration Notes and its F1–F21 findings, the OPEN RULINGS and rejected items, Approach, Verified Diagnosis, Design §1–§10, Edge Cases, Implementation Plan, Write Targets, Mitigation Folds, Verification, Scope Boundary, Risk Analysis, Acceptance Criteria, the nine Architectural Review rounds, both Conductor Notes, the eight AC Red-Team rounds, AC Sign-off, Data Audit, Threat Model and Spec Review). Also read the two in-tree grounding artifacts this document's `## Write Targets` cites (`docs/wi-032-whatsapp-corpus-census.md`, `docs/wi-032-consumer-audit.md`). Ran a full-document regex/keyword sweep for injection indicators — imperative language addressed to a reviewer or agent, "ignore previous instructions"-style phrasing, pre-approval claims, zero-width/bidirectional Unicode, embedded URLs, shell/exec/subprocess patterns — over this document and both artifacts, with zero hits of concern.

**The one phrase that read as suspicious on first pass, resolved.** Line 5205: "Every in-tree citation below was resolved by reading the code at it, not by trusting the injected drift audit." "Injected drift audit" names an automated citation-verification pass the spec-reviewer chose to re-verify manually rather than trust — a methodological caution, not a prompt-injection payload. No text calling itself a "drift audit" or similar appears anywhere else in the document; there is nothing here for a gate to have trusted or been steered by.

**No planted steering found.** Every fold, ruling, rejected item and prior gate verdict argues its own technical merits via file:line citations and measured counts — none instructs a reviewer's verdict, addresses "the model" or "the AI" directly, or supplies pre-baked conclusions dressed as spec content. The document's dense self-referential voice (folds correcting folds, gates re-deriving prior findings from code rather than trusting fences) is a house style consistent across all nine architect rounds and eight red-team rounds, not an anomaly localized to one section. The current spec-reviewer REVISE verdict (two unpinned-oracle findings on AC-3's APPEND-ONLY conjunct and the migration's re-run assertion) reads as an independently-derived, well-grounded judgment on its own stated reasoning, not as the product of steered text.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-27
model: claude-sonnet-5
note: Full end-to-end read of the document (all sections, all nine architect rounds, all eight AC red-team rounds) plus both grounding artifacts and a targeted injection-indicator sweep found no planted steering, hidden instructions, or reviewer-directed manipulation; the one candidate phrase ("injected drift audit," line 5205) names a distrusted automated tool pass, not a prompt injection.
```

