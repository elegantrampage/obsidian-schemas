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

