---
id: WI-020
title: "Loud-fail hardening: parse, guard, and write-return boundaries"
project: obsidian-schemas
stage: idea
created: 2026-07-05
last_touched: 2026-07-24
stage_changed: 2026-07-05
touched_by: ideation-partner
tags: [corruption-class, loud-fail, parser, writer]
depends_on: []
---

# Loud-fail hardening: parse, guard, and write-return boundaries

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: —** (the 2026-07-05 code-health review is the exploration; findings C2/C3/C4/C5/N4 below are the target list).
> - **Spec: Opus / high** — the one real design decision is quarantine semantics for malformed notes: raise-and-abort breaks consumer batch loads (HAL9000 startup walks the whole vault); silent-quarantine recreates the bug. Workspace doctrine (default-loud-fail; silent must be explicit) constrains the space; the spec picks the mechanism (e.g. load survives, malformed notes land in a loudly-surfaced quarantine list + WARN, mutation paths REFUSE to write through a failed parse).
> - **Spec-review: Opus / high. Build: Opus / high** — corruption-class, touches parser + writer + base repository.
> - Sequencing: Phase 1, first in queue. WI-004 (atomic write primitive) builds on the loud floor this establishes.

## Problem / Motivation

Five silent-degrade sites at the package's safety boundaries, found and file:line-verified by the 2026-07-05 campaign review. The first two interact to destroy data:

1. **C2 — malformed YAML silently degrades to "no frontmatter"** (`parser.py:78-80`: `yaml.YAMLError` → `({}, content)`). Every rebuild path trusts it: `base.update_fields` (base.py:255-273) and `writer.update_frontmatter_field(s)` (writer.py:247-295) do `parse_frontmatter → rebuild → write`, so a note whose YAML doesn't parse at update time gets rewritten as `---\n{only the updates}\n---\n{whole original file as body}` — **original frontmatter destroyed and duplicated into the body, silently.**
2. **C3 — the WI-126 body-shrink guard disables itself on read error** (`writer.py:189-190`: `except Exception: existing_body = ""`). The one mechanism protecting against body-wipe turns off exactly when it can't verify. Must raise (or refuse the write), never assume-empty.
3. **C4 — un-loadable notes vanish at DEBUG** (`base.py:125-126`; also `meeting.py:70-83`). A person invisible to the cache → `resolve()` misses → `find_or_create_stub` mints a duplicate — the dup-proliferation class WI-119/WI-125 exist to fight. WARN + surfaced count.
4. **C5 — `parse_to_model` swallows all validation errors** (`parser.py:139-150`: `except Exception → (None, dict)`). Same duplicate-creation consequence; hides schema drift entirely.
5. **N4 — write paths return silent False** (`writer.py:259-260, 298-299`; five body-section writers `person.py:1500-1839`): "duplicate/not-found" and "disk full / torn write" are the same `False`. Failure must raise or be distinguishable.

**Sharpened by exploration (2026-07-24).** The five are not five bugs — they are **one defect class at five sites**: a failure at a safety boundary is rendered as a *success-shaped value*, so no caller can tell "nothing to do" from "I failed." The shapes are `({}, content)` (C2), `(None, dict)` (C5), `existing_body = ""` (C3), `return None` at DEBUG (C4), and `return False` (N4) — each is the value a *legitimate empty/absent* case would also produce. That collapse is what makes the class corruption-grade rather than untidy: C2's `({}, content)` is indistinguishable from a genuinely frontmatter-less file, so `update_fields`/`update_frontmatter_field(s)` rebuild `---\n{updates}\n---\n{whole original file}` and commit it.

The corruption chain is **confirmed live in this tree**, not inferred. `update_fields` (base.py:311) calls `parse_frontmatter`, which swallows `yaml.YAMLError` and hands back `({}, content)`; the rebuild at base.py:326-329 then writes the original file into the body. The one thing that might have caught it — the post-write reload at base.py:331-334 (`if updated_entity is None: raise`) — cannot, because the corrupt output *is* valid YAML (`---\n{updates}\n---\n…`), so `_load_file` reloads a stripped-but-valid entity and the guard passes. The write path's own safety check is defeated by the same swallow it sits downstream of.

The resolving asymmetry, which every fix below turns on: **on read/load, survive-but-surface; on write/mutate, refuse.** A batch load (HAL9000 walks the whole vault at startup) must not abort on one bad note, but the note must not vanish either. A mutation must never be built on a parse that failed. The two consumers of the same parse have opposite correct answers, and today both get the silent one.

## Intent

A malformed or unwritable note is loud at the boundary where it's met: loads surface what they skipped, guards refuse rather than assume, writes that fail raise. No vault mutation is ever built on a parse that failed. Every fix ships its invariant test (malformed-YAML round-trip protection is the keystone regression).

## Exploration Notes

Cold-start exploration, 2026-07-24. Every code claim below reads from the current tree at the file:line cited; the 2026-07-05 campaign review is the exploration input (findings C2/C3/C4/C5/N4), re-verified rather than trusted.

### The one real design decision: where does loud-fail live, and how do read and write get opposite answers from the same parse?

`parse_frontmatter` (parser.py:53-80) has two classes of caller with **opposite correct behaviours** on a bad note:

- **Read/load callers** — `base._load_file` (base.py:171-183), `meeting._load_file` (meeting.py:64-83), and every `resolve()`/`get_all()` path behind them — walk the whole vault. HAL9000 constructs a `PersonRepository` at startup and loads hundreds of notes. If one note's YAML is malformed, the *right* answer is "skip it, but make the skip visible" — not abort the batch (breaks startup), not vanish it silently (C4: `resolve()` misses → `find_or_create_stub` mints a duplicate, the exact WI-119/WI-125 class).
- **Write/mutate callers** — `update_fields` (base.py:278-334), `update_frontmatter_field` / `update_frontmatter_fields` (writer.py:222-299). Here the *right* answer is "refuse" — never rebuild a file from a frontmatter dict you failed to parse.

Today both get the same silent `({}, content)`, and it is wrong for each: the read path drops the note, the write path corrupts it. **The information that would let them diverge — "the YAML failed to parse" versus "there is genuinely no frontmatter" — exists at exactly one place (parser.py:78, the `except yaml.YAMLError`) and is thrown away there.** Any downstream attempt to re-detect it (a write path re-parsing, re-checking) would be reconstructing at read time what the seam discarded at write time — the WI-185 anti-pattern this role is warned about. **So the fix belongs at the seam: `parse_frontmatter` must stop conflating "absent" with "malformed," and let each caller choose.** That single decision cascades to four of the five findings.

### Per-finding: trigger predicate (verbatim) and direction

Each site is classified on its actual invoking code, read from the tree — not its name or its docstring's story.

**C2 — `parse_frontmatter` swallows `yaml.YAMLError` → `({}, content)` (parser.py:78-80).**
```python
    except yaml.YAMLError:
        # If YAML parsing fails, treat as no frontmatter
        return {}, content
```
The predicate: *"the YAML between the fences did not parse."* The return value is byte-identical to the genuinely-frontmatter-less case (parser.py:64-65, `if not content.startswith("---"): return {}, content`). **Direction:** make malformed distinguishable from absent — the write/rebuild paths must refuse (raise a typed error), the read paths must surface. This is the seam fix above; it is the keystone.

**C3 — the WI-126 body-shrink guard assumes-empty on read error (writer.py:184-195).**
```python
        try:
            _, existing_body = parse_frontmatter(file_path.read_text(...))
        except Exception:
            existing_body = ""
```
The predicate: *"reading or parsing the existing file raised."* The one mechanism protecting against body-wipe sets `existing_body = ""` — which makes `dropped = existing_lines - _body_content_lines(body)` empty, so the guard passes and the overwrite proceeds. **A guard that assumes the safe-looking value exactly when it cannot verify is not a guard.** Direction: can't-verify → refuse (raise), never assume-empty. (Note: once C2 makes `parse_frontmatter` raise on malformed YAML, this bare `except` starts catching it — so C3 and C2 must be designed together, or C3 will re-swallow C2's new signal.)

**C4 — un-loadable notes vanish at DEBUG (base.py:181-183; meeting.py:81-83).**
```python
        except Exception as e:
            logger.debug(f"Could not load {file_path}: {e}")
        return None
```
The predicate: *"loading this one file raised."* `None` is returned at DEBUG (invisible by default), and `load()` (base.py:158-165) simply doesn't add it to the cache — no count, no list, no trace. The note is now invisible to `resolve()`, which drives duplicate creation. Direction: WARN (not DEBUG) **plus** surface a queryable count/list of skipped files on the repository, so a caller — or Dave — can see what a load dropped. This is the read-half of the C2 asymmetry.

**C5 — `parse_to_model` swallows all validation errors → `(None, dict)` (parser.py:148-150).**
```python
    except Exception:
        # If model validation fails, return None with all fields as extra
        return None, frontmatter.copy()
```
The predicate: *"`model_class.model_validate` raised."* But `(None, extra)` is the **same value** returned for a legitimately unknown `type` (parser.py:135-137). So a `type: person` note that fails schema validation (drift) is indistinguishable from a `type: recipe` note we simply don't model. Direction: distinguish "known type, failed validation" (loud — schema drift) from "unknown type" (fine). Same shape as C2, one layer up.

**N4 — write paths collapse failure and no-op into one `False` (writer.py:259-260, 298-299; person.py body-section writers).**
`update_frontmatter_field` returns `True` on success and `False` from a blanket `except Exception` (writer.py:259-260) — the same `False` a caller would read for "file not found" (writer.py:242-243). Worse in `person.append_to_body_section` (person.py:1504-1607), which returns `False` for **five distinct reasons**: deduped (1584), missing-section-with-`create_if_missing=False` (1579), no frontmatter fence (1563), malformed frontmatter fence (1570), and `except Exception → return False` (1603-1607, catching disk-full / torn write / permission error). A caller cannot tell "I skipped because it was already there" from "the write failed and your data is gone." Direction: genuine I/O failure must **raise**; a legitimate no-op (dedup, absent section) may stay falsy but must be **distinguishable** from a failed write — not the same bare `False`.

N4 has **two independent trigger predicates**, and the campaign's enumeration only ever named one. Predicate 1 is the blanket `except Exception` (seven sites: writer.py:259, 298; person.py:1500, 1603, 1702, 1775, 1837). Predicate 2 is the **frontmatter-fence split** — `content.startswith("---")` then `split("---", 2)` — which `grep` puts at **five** sites in `person.py`, all read live: `append_to_body_section` (1558-1570), `add_to_discuss_item` (1675-1683), `update_to_discuss_item` (1734-1742), `remove_to_discuss_item` (1801-1809), and `_get_body_content` (1622-1626). The four writers are byte-for-byte the same shape and collapse "no fence" and "malformed fence" into the same `False` a legitimate "item text not found" also returns (1746-1747, 1759-1761, 1822-1824). The fifth, `_get_body_content`, is not a writer and fails differently and worse: on a fence it cannot split it falls through to `return content`, handing its caller the **whole file, frontmatter included, as body** — so `get_to_discuss_items` (1641) parses To-Discuss items out of YAML frontmatter text and reports the broken note as having no items. That is the class's signature move (a failure rendered as the value a legitimate empty case produces) at a *read* helper, so its direction is the read-side one: surface, not raise.

### Approaches considered

**A1 — fix at the seam (`parse_frontmatter` distinguishes malformed from absent), then let read and write callers choose. CHOSEN.** One change to the parse boundary supplies the signal; read paths surface it, write paths refuse. Solves C2 at its root and gives C4/C5 the same shape to follow. Matches "solve in one place" and the WI-185 seam rule (fix where the structure is discarded, not downstream). The exact mechanism — a typed `FrontmatterParseError` raised, versus a discriminated return (e.g. a `ParseResult` with a `malformed` flag / a sentinel) — is a **spec-writer decision**, deliberately left open here; the *property* (malformed ≠ absent) is what convergence fixes.

**A2 — guard each write path independently, leave `parse_frontmatter` as-is.** Rejected. The write paths would have to re-detect a malformed parse *after* `parse_frontmatter` already ate the evidence — either by re-parsing (double work, and the second parse can disagree with the first) or by heuristics on the returned `{}`. It also splits one predicate across three-plus doors. This is exactly the "reconstruct at read time what the seam discarded" trap.

**A3 — make `parse_frontmatter` raise unconditionally on `YAMLError`, full stop.** Rejected as the *sole* mechanism. It gives the write paths what they need, but it converts C2 into C4: `base._load_file`'s `except Exception` (base.py:181) catches the raise and returns `None` at DEBUG — the note vanishes silently on load, and the batch still needs the survive-but-surface behaviour. Raising is *part* of the answer (for write callers), but the read path still needs an explicit skip-and-surface. This interaction is the reason C2, C3, and C4 cannot be fixed in isolation.

**A4 — quarantine malformed notes to a sidecar / rename them.** Rejected for this item, routed to `lint_vault` (WI-026). Moving or renaming a live note is itself a vault mutation, and this item's whole thesis is "never mutate on a failed parse." Surfacing (a WARN + a list the caller can read) achieves visibility without the library silently relocating Dave's files. A *tool* invoked deliberately (`lint_vault --quarantine`, which already renames notes at lint_vault.py:1037) is the right home for physical quarantine, not the library read path.

**A5 — return `False`/`None` everywhere but add structured logging so failures are greppable.** Rejected. Logging is what C4 already does and it has never stopped anything (the WI-024 exploration made the same finding about `load()`'s warn-and-continue). A value a caller acts on must carry the failure; a log line the caller never reads does not.

### Constraints discovered

- **The hermetic floor must stay green.** Baseline **607 passed, exit 0** (CLAUDE.md, post-WI-024), ~1s, from a foreign cwd, no `conftest.py`. Every new invariant test must supply `tmp_path` and must not depend on ambient environment. A run that lands fewer than 607 pre-existing cases has silently lost a test file — stop and investigate.
- **The stale editable install is load-bearing.** `_obsidian_schemas.pth` points at a dead path; a bare `import obsidian_schemas` fails; the suite works because pytest prepends its rootdir (CLAUDE.md, `pipeline-runners.yaml`). This item lives entirely inside `obsidian_schemas/` and must not "fix" packaging.
- **Exception-type convention.** Boundary errors subclass `ValueError`: `IdentifierError` (identifier.py:58), `NameValidationError` / `WeakIdentityError` (name_validation.py:125,140), and WI-024's own `VaultPathNotConfiguredError`. A new `FrontmatterParseError` should follow suit so a consumer's existing `except ValueError` still catches it and the break degrades to a message change. (`BodyTruncationError(Exception)` at writer.py:30 is the lone deviation — do not follow it.)
- **HAL9000's batch load is the hardest constraint.** It is the reason A3-alone fails: read paths *must* survive a single bad note. Any AC that asserts "raise on malformed" must scope the raise to write/mutate paths, or it breaks startup — the same read/write asymmetry the campaign's own WI-024 rider tripped over.
- **C2 and C3 are coupled.** Once `parse_frontmatter` raises on malformed YAML, C3's bare `except Exception: existing_body = ""` catches it and re-buries it. They must land together, or C3 silently re-opens C2 on the overwrite path.
- **Every repository's glob is wider than its ownership set, and ownership is decided downstream of the parse.** `BaseRepository` globs `@*.md` (base.py:133-135) — shared by `PersonRepository` and `CompanyRepository`, since neither overrides it and `base.save` writes `@{name}.md` (base.py:256-258) — and checks no `type` at all (ownership falls out of `isinstance` at base.py:179, after the parse at 178). `MeetingRepository` globs `Meeting *.md` and type-checks at meeting.py:75, after the parse at 72. `BookRepository` globs the catch-all `*.md` (book.py:49-51) and type-checks at book.py:70-71, after the parse at 67. So the moment the load surfaces what it drops, the surface is scoped by the *glob*, not by ownership, unless the fix says otherwise — see the round-3 red-team subsection and AC-3. Note the class/path asymmetry this creates: there are **four** concrete repository classes but only **three** `_load_file` implementations, because `PersonRepository` and `CompanyRepository` both inherit `base`'s. Ownership is a per-class property (each class declares its own `type_name`, base.py:126-130), so a sweep counted in code paths tests it once for two classes with opposite answers — see the round-5 red-team subsection.
- **N4 is a return-contract change — the one place backward-compat bites.** Callers today branch on `if not repo.append_to_body_section(...)`. Turning the failure `False` into a raise changes control flow for existing consumers (HAL9000 enricher, introducer, scheduler). This is the only finding that is not purely internal; the spec must decide raise-vs-distinguishable-return with the three consumers' call sites in view, and it is why N4 may warrant its own AC and its own consumer audit.

### Inherited scope from WI-024 (its non-goals routed two findings here)

WI-024's "Relationship to other work" explicitly assigns WI-020 two items. Both are read from the current tree:

1. **The bare `except Exception` at person.py:1147-1160** (name-cleaning company set). Predicate: *"constructing `CompanyRepository` or reading its `get_all()` raised."* Today it swallows everything to DEBUG — including, post-WI-024, a genuine `VaultPathNotConfiguredError`. **In scope.** Same class as C4 (a read-side swallow that hides a real error); direction is narrow the except to the expected-unavailable cases (`ImportError`, and a deliberately-caught `VaultPathNotConfiguredError`) and let anything else surface. Small; folds under the read-surfacing AC.

2. **The "configured but wrong path" silent degrade** — `load()` on a non-existent vault warns and returns 0 (base.py:152-155), the repo then presents as *legitimately empty*, `resolve()` misses, and stub creation `mkdir(parents=True)`s a bogus tree. This is accident of *commission* (WI-024 shut accident of *omission*). **Recommend in scope for the surfacing half, defer the write half.** The surfacing ("a repo bound to a path that doesn't exist should be distinguishable from a repo bound to a real-but-empty vault") is the same C4 family and belongs here. The *write* half — that `save()`/writer `mkdir(parents=True)` will happily materialise a bogus tree — interacts with WI-004 (atomic write primitive), which builds on this floor. **Parked for a Dave call:** fold the mkdir-guard into WI-020, or let WI-004 own it. My recommendation: surface here (AC-3 family), let WI-004 own the write-side refusal, since WI-004 is the atomic-write boundary and "solve in one place" puts the write guard there. Not encoded as an AC below — flagged for sign-off.

### Red-team on the draft ACs

Not a subtraction item (this item *adds* guards, removes no mechanism), so the WI-123 REMOVE-audit rule does not fire. But N4 changes a return contract, and a decorrelated pass on the draft ACs still earned its keep:

1. **A naive keystone AC ("malformed YAML raises") would break HAL9000 startup.** If AC-1 asserted that *any* encounter with malformed YAML raises, a batch load of a vault with one bad note would abort. Corrected: AC-1 scopes the raise to **write/mutate** paths and asserts the on-disk file is **unchanged**; the read-path behaviour is a separate AC (survive-and-surface). The keystone is "no mutation writes through a failed parse," not "malformed always raises."
2. **"Surface the skip" is gameable by a log line.** An AC satisfied by `logger.warning(...)` is satisfied by C4's current DEBUG one level up — a log nobody reads. Corrected: AC-3 requires a **queryable** artifact (a count/list on the repository the test can assert on), not merely a log.
3. **The corruption regression must assert on bytes, not on a return value.** A test that only checks "raises" can pass while a *different* write path still corrupts. AC-1 pins the actual failure mode: after the refused mutation, the file's frontmatter and body are byte-identical to before — the original content is never duplicated into the body.
4. **N4's "distinguishable" is weaker than it sounds.** "Return a different value on failure" still lets a caller ignore it. The property that matters is that a genuine I/O failure **raises** (cannot be silently dropped), while a legitimate no-op stays a distinct, documented falsy signal. AC-5 states both halves.

### Decorrelated AC red-team (2026-07-24) — what it changed

A cold-start gate attacked the draft AC set; its findings are recorded verbatim in `## AC Red-Team — 2026-07-24` below. Four of the five were coverage gaps, closed by tightening the ACs. The CRITICAL one could not be closed as framed — and re-deriving it turned up two members of the defect class the campaign's own enumeration had missed. Every code claim here re-read live.

**The CRITICAL (AC-5's cross-repo consumer audit) cannot be an acceptance criterion in this repo — by either route the gate proposed.**

- Route (a), "a `kind: command` grep/lint rather than a local pytest test", is unavailable. A command AC's `check` must name an id in the merged command registry, and this project's `pipeline-runners.yaml` declares only `seed_deps` and `write_authority` — **no `runners:` key at all** — so the only reachable ids are the built-ins `lint-project` and `lint-boundary-reaches` (workshop `src/work_item_linter.py`, `COMMAND_REGISTRY`). Neither can audit another repository. Registering a new runner means editing `pipeline-runners.yaml`, which that file's own header declares deliberately NOT builder-writable.
- Route (b), "import and exercise those three call sites", breaks this item's hardest constraint: the floor is hermetic, ~1s, no ambient environment (CLAUDE.md). HAL9000 is confirmed absent from this tree.

So the audit is **removed from the AC set** rather than left standing as a clause nothing can check. What replaces it is a property that *is* locally verifiable and that meets the gate's own failure scenario head-on: **no consumer-visible return value changes except where it was reporting a failure as a no-op** (AC-5 below). Every legitimate falsy return that an existing `if not repo.append_to_body_section(...)` branch relies on keeps its exact value; the only behavioural change is that a genuine disk-full stops being misreported as a benign dedup. The gate's scenario — "a disk-full now raises uncaught through code written to treat falsy as no-op" — is the *intended* outcome of this item, and an uncaught raise is loud by construction. What it is not is *silent*, and silence is the property the audit existed to protect.

The residual risk the audit genuinely covered — a HAL9000 consumer that catches broadly and re-buries the raise — is irreducibly cross-repo. **Parked for Dave: mint a companion work item in HAL9000** to migrate the enricher/introducer/scheduler call sites. Named in Non-goals so it is deferred, not dropped.

**Two class members the named enumeration missed.** Found by deriving the fixture space from the code instead of trusting the campaign's list — which is the WI-185 class-closing rule, and which vindicates the gate's MATERIAL-1 finding concretely rather than in principle:

1. **`roundtrip_file` (writer.py:302-324) is a FOURTH write path** through the same `parse_frontmatter → rebuild → write` chain — and it carries no `try`/`except` at all, so on a malformed note it unconditionally rewrites `---\n{}\n---\n{whole original file}`. The doc named three write paths; the class has four.
2. **`book._load_file` (book.py:57-79) is a THIRD read-side swallow** (`except Exception: logger.debug(...)`), alongside `base.py:181-183` and `meeting.py:81-83`. The doc named two.

Both are now covered because AC-1 and AC-3 derive their sweeps from the package (callers of `parse_frontmatter` that re-serialize and write; overrides of `_load_file`) rather than naming a list — so a fifth write path or a fourth repository joins automatically.

**`parse_frontmatter` has four return sites, not two.** Deriving AC-2's fixture space from the function's own branch structure exposes a case nobody had classified: `parser.py:69-70` (`if not match: return {}, content`) fires when a file *opens* `---` but never closes the fence. Today that is silently "absent" — yet `append_to_body_section` already treats the same input as a distinct **malformed-fence** case (person.py:1564-1570). Two places in one package disagree about what that byte sequence means. AC-2 requires it be classified explicitly rather than defaulting by accident.

**Why six ACs, not five.** The gate asked that the `person.py` narrowing carry a mechanism-forcing assertion rather than riding on AC-3's "not swallowed to DEBUG" wording, which a builder satisfies by changing a log level — the move A5 already rejected. A separate assertion needs a separate `check`, and a `criteria` fence carries exactly one, so it split out as AC-6. Six stretches the role's 3–5 guidance; the alternative is a clause known to be gameable.

### Decorrelated AC red-team, round 2 (2026-07-24) — what it changed

The re-verify pass (recorded verbatim in `## AC Red-Team — 2026-07-24 (re-verify)` below) confirmed the four earlier folds and found two new MATERIAL gaps. Both are the *same* mistake in two places: an AC that derives one half of its property from the code and then hand-writes the other half. Both are now derived on both halves. Every claim below re-read live.

1. **AC-1's positive half covered 2 of the 4 paths its negative half derives over.** Confirmed live: `update_fields` (base.py:311-329) and `roundtrip_file` (writer.py:316-322) run the identical `parse_frontmatter → rebuild → write` shape and today both accept an absent-frontmatter note without complaint — `roundtrip_file` has no `try` at all and its docstring promises "preserving all content." A builder could therefore make `parse_frontmatter` raise on *absent* as well as malformed, special-case the two functions AC-1 named, and read green while ordinary field-setting on a fresh stub started raising. **Fixed by quantifying the absent-must-succeed half over the same derived list**, and by pinning the assertion to a pre-change baseline (same return value *and* same resulting bytes as the current tree) rather than to prose about what "expected" means. AC-1 now also states that malformed YAML is the **only** input the raise-half licenses.

2. **AC-5 reclassified the no-fence/malformed-fence branches for one function of a class of four.** Fixed by giving AC-5 an explicit second derivation predicate (the fence split) instead of a name list — and running that predicate turned up a **fifth site the campaign, the doc, and both red-team passes all missed**: `_get_body_content` (person.py:1622-1626), which on an unsplittable fence returns the whole file as body (see the N4 per-finding note above). It is not a writer, so it does not join the raise side; it joins the same AC because it is the same predicate at the same seam, and because leaving it out after deriving the sweep would repeat exactly the error being fixed.

This is the third time deriving a sweep from the code has found a member the prose enumeration missed (`roundtrip_file`, `book._load_file`, now `_get_body_content`). The pattern is now load-bearing enough to state plainly: **in this item, no AC names its sites — every AC names the predicate that yields them.**

### Decorrelated AC red-team, round 3 (2026-07-24) — what it changed

The round-3 pass (verbatim in `## AC Red-Team — 2026-07-24 (re-verify 2)` below) confirmed both round-2 folds and found one MATERIAL gap: **AC-3 derives its *repository* sweep from the code but hand-picks its *fixture space*.** `BookRepository.file_pattern` is `"*.md"` (book.py:49-51) — a catch-all that globs every markdown file in the vault — and its ownership test (`frontmatter.get("type") != "book"`, book.py:70-71) runs *after* the `parse_frontmatter` call at book.py:67 that this item makes loud. So a malformed note of any type lands in `BookRepository`'s skip-list. Confirmed live.

Re-deriving the fixture space from each repository's own `file_pattern` — the same move that found `roundtrip_file`, `book._load_file` and `_get_body_content` — turns one repository's quirk into a property of the whole sweep, and turns up two exposures larger than the reported one. Every claim re-read live.

**The general shape: every repository's glob admits files it does not own, and every repository decides ownership downstream of the parse this item makes loud.** `BookRepository` globs `*.md` and type-checks at book.py:70-71, after the parse at 67. `MeetingRepository` is the same shape (parse at meeting.py:72, type check at 75), narrower only because `"Meeting *.md"` (meeting.py:50-52) is a naming convention. `BaseRepository` globs `@*.md` (base.py:133-135) and has **no `type` check at all** — ownership is decided by `isinstance(doc.entity, self.entity_type)` at base.py:179, downstream of `parse_markdown_file` at 178.

**Exposure 1 — `PersonRepository` and `CompanyRepository` glob the SAME file set.** Neither overrides `file_pattern` (grep confirms only `base.py`, `book.py`, `meeting.py` define it), and `base.save` writes `@{name}.md` (base.py:256-258), so person and company notes share one namespace. `BookRepository`'s catch-all glob is the extreme case, not the only case.

**Exposure 2 — this fires on a perfectly healthy vault, and it is bigger than the reported case.** `Person.type` is `Literal["person"]` (models.py:78); `Company.type` is `Literal["company"]` (models.py:127). So `PersonRepository._load_file` on a *well-formed* `@Acme.md` calls `parse_markdown_file(path, Person)` → `parse_to_model(fm, Person)` → `model_validate` raises on the literal mismatch → today swallowed at parser.py:148-150 into `(None, extra)` → `doc.entity` is None → `_load_file` returns None silently. That is the *right* answer reached by the *wrong* mechanism, and this item removes the mechanism: once C5 makes "known type, failed validation" loud (AC-2) and AC-3 requires the load to surface what it dropped, **every company note in the vault becomes a "skipped person"** and every person note a "skipped company" — hundreds of entries on a vault with nothing wrong with it. AC-3 exists to make the skip signal trustworthy; implemented naively it makes it noise on day one, which fails the same way C4's unread DEBUG line fails.

**What the resolution turns on: ownership evidence, and the fact that there are two kinds of it — one of which cuts two ways.** A repository can establish a file is its own by (a) its glob being a **naming convention** (`@*.md`, `Meeting *.md`), or (b) the file's **`type` field being readable**. They fail in different cases, and separating them is what makes the property statable without picking a mechanism. Four cases, not three (the second was added in round 4 — see below):

- **`type` readable, not mine** → decidably foreign. Never enters the skip surface (exposure 2 — `@Acme.md` under `PersonRepository`). `meeting.py:75` and `book.py:70` already run this check; `base._load_file` does not, and must.
- **`type` readable AND mine, but `model_validate` fails on some other field** → decidably **owned**, and drifted. **Must be listed.** This is C5's actual duplicate-creation driver (`@Broken.md` carrying `type: person` with `emails: "not-a-list"`), and it is the *same code path* as the foreign case above — both are `parse_to_model` raising inside `model_validate` — with the opposite required answer. That is why ownership cannot be decided by "did model construction succeed"; see the round-4 subsection.
- **`type` unreadable (the malformed case), glob is a naming convention** → undecidable by type, owned by convention. **Must stay in the skip surface** — this is the C4 keystone (`@John.md` malformed → `resolve()` misses → `find_or_create_stub` mints a dup). Both `PersonRepository` and `CompanyRepository` will report it, since neither can tell which it was; that is honest, not a defect.
- **`type` unreadable AND glob is a catch-all** → no ownership evidence of either kind. This is `BookRepository` and only `BookRepository`, and it is why the finding cannot be closed by a fixture alone: on a malformed `Some Note.md` there is *nothing left to read* that says whether it is a book. It must not be counted in whatever a consumer reads as "N books need attention."

AC-3 now derives its fixture space per repository from that repository's `file_pattern`, requires a **heterogeneous** vault — the only kind that exists; Dave's vault mixes `@Name.md`, `Meeting *.md` and bare-titled notes in one directory — and asserts the skip surface in **both** directions: the convention-owned malformed note present, the decidably-foreign note absent. The **mechanism** is deliberately left to the spec-writer (a second "ownership undeterminable" bucket, a narrowed glob, or a type check ordered ahead of the loud parse); the AC pins the property and names `BookRepository` as the case where it cannot be met by accident.

The rule from round 2 needs its other half, which is this round's lesson: **no AC names its sites, and no AC hand-picks its fixture space either — both are derived from the code.** A derived sweep tested against a fixture someone chose is still a hand-picked AC; it just moves the sampling one level down. A builder who adds a sixth fence-split site joins the sweep automatically.

### Decorrelated AC red-team, round 4 (2026-07-24) — what it changed

The round-4 pass (verbatim in `## AC Red-Team — 2026-07-24 (re-verify 3)` below) confirmed the round-3 fold and found one MATERIAL gap: **AC-3's two required fixtures collide, because "known type fails Pydantic validation" names two mechanically identical cases with opposite required answers, and only one of them had a worked example.** Every claim below re-read live.

**The collision.** AC-3 required fixture (b) — "YAML parses cleanly but the known type fails Pydantic validation (schema drift, the C5 predicate)" — to *appear* in the skip surface. But the only worked example the doc gave anywhere for that phrase was `@Acme.md` (`type: company`) loaded under `PersonRepository`, which the same AC requires *not* to appear. Both are literally `parse_to_model(fm, Person)` raising inside `model_validate`; nothing in the doc separated them, and the round-3 ownership taxonomy had no bucket for the one that matters.

**Why the two are not the same case, verified in the models.** `BaseEntity` sets `model_config = ConfigDict(extra="allow")` (models.py:31-32), and every `Person` field beyond `type` is `str` or `List[str]` with **no** `@field_validator`/`@model_validator` anywhere in `models.py` (grep confirms; fields at models.py:78-90). So there are exactly two ways a note can fail `Person.model_validate`, and they carry opposite ownership evidence:

1. **`type` is not literally `"person"`** — `Literal["person"]` (models.py:78) rejects it. The raw `type` string says whose file it is: *someone else's*. Decidably **foreign**.
2. **`type` IS `"person"` and a `List[str]` field receives a non-list scalar** — `emails: "not-a-list"`, `roles: 3`. Pydantic v2 rejects rather than coerces; an unknown *extra* key cannot do it, because `extra="allow"`. The raw `type` string says *mine*. Decidably **owned**, and drifted.

Case 2 is the one Problem/Motivation describes as C5's consequence — a `type: person` note that never enters the cache, so `resolve()` misses and `find_or_create_stub` mints a duplicate. It is the reason fixture (b) exists, and it was the case with no worked example.

**The mechanism this forecloses, which is the real point.** The natural implementation of the round-3 taxonomy — the one that correctly excludes `@Acme.md` — is "attempt to build the model; if it fails, this file is not mine." That predicate returns the *same* failure for cases 1 and 2, so it would silently drop `@Broken.md` from `PersonRepository`'s skip-list while every AC read green. **Ownership therefore cannot be decided by whether model construction succeeded; it must be decided on the raw `type` value read from the parsed frontmatter, independently of and prior to `model_validate`.** `meeting.py:75` and `book.py:70` already read `frontmatter.get("type")` that way; `base._load_file` (base.py:177-183) reads no `type` at all and decides ownership from `isinstance` — i.e. from model construction — which is precisely the defective predicate. That is now stated as a property in AC-3 and in the Approach, mechanism still left open.

**What changed.** The ownership taxonomy above gained its fourth bucket; the Approach gained the same distinction; AC-3 now requires **three** distinct fixture files — (a) unparseable, (b) owned-and-drifted `type: person` + non-coercible field → MUST be listed, (c) well-formed foreign `type: company` → MUST NOT be listed — asserted in the same test, with (b) and (c) explicitly forbidden from being the same file; and a sixth Example of done pins (b) in Dave's terms.

This is the fourth time an AC read as satisfied while the case that motivated it went untested, and the shape has now repeated often enough to name: **two fixtures that share a code path but require opposite answers must be two files, asserted in one test.** One of them alone always looks like the property.

### Decorrelated AC red-team, round 5 (2026-07-24) — what it changed

The round-5 pass (verbatim in `## AC Red-Team — 2026-07-24 (re-verify 4)` below) confirmed the round-4 fold and found one MATERIAL gap: **AC-3 derived its fixture space per repository, but derived its *repository sweep* from `_load_file` overrides — which are code paths, not classes.** Every claim below re-read live.

**The collapse.** There are **four** concrete `BaseRepository` subclasses in the package — `PersonRepository` (person.py:159), `CompanyRepository` (company.py:46), `MeetingRepository` (meeting.py:21), `BookRepository` (book.py:21) — but only **three** `_load_file` implementations, because `company.py` overrides neither `_load_file` nor `file_pattern` (read in full: it defines `entity_type`, `type_name`, `_index_entity`, `_clear_indexes`, and lookup helpers, and no ownership check of any kind). AC-3's sweep sentence collapsed Person and Company into one entry with a parenthetical. Every worked example in the doc — fixture (c)'s `@Acme.md`, the Foreign-and-absent bucket, the fifth Example of done — was written from `PersonRepository`'s chair. `CompanyRepository`'s own skip-list was never queried anywhere.

**Why that is not pedantry: ownership is a per-class property, not a per-path one.** `type_name` is an abstract property (base.py:126-130) that each subclass answers differently — `"person"` (person.py:208-209), `"company"` (company.py:67-68), `"meeting"`, `"book"`. The shared `base._load_file` is exactly the place a fix must consult it. A builder writing the natural implementation — an `_owns(frontmatter)` helper on `BaseRepository` comparing `frontmatter.get("type")` against `self.type_name` — and parametrizing one test over `{PersonRepository, MeetingRepository, BookRepository}` (one instance per override, matching AC-3's literal three-item enumeration) reads green while a hardcoded `"person"` literal, an inverted `==`/`!=`, or a check ordered after model construction misbehaves under `CompanyRepository` and nothing catches it. And the case that ships unverified is the *larger* of round 3's two exposures — "every person note becomes a skipped company," firing on a vault with nothing wrong with it.

**The mirror fixtures, derived rather than transposed.** `CompanyRepository`'s (b) cannot be copied from `Person`'s `emails: "not-a-list"`, because `Company` declares no `List` field of its own (`name`/`website`/`industry`/`linkedin`/`created` are all `str`, models.py:127-132). Deriving from the model instead: `Company` inherits `tags: List[str]` from `BaseEntity` (models.py:40), so the owned-and-drifted company note is `type: company` with `tags: company` rather than `tags: [company]` — the actual hand-edit typo shape. Its (c) is the well-formed `@Sarah.md` (`type: person`), which `CompanyRepository` must **not** list.

**The cheap fix this also forecloses.** Making the company side pass by suppressing everything a repository cannot type-confirm would re-close the C4 keystone: a malformed `@John.md` is globbed by both repositories and readable by neither, so **both** must list it. That is honest, not a defect, and AC-3 now asserts it from both chairs so the mirror direction cannot be bought by silencing the undecidable case.

The rule this round adds, alongside "no AC names its sites" and "no AC samples its fixture space": **when two classes share one code path, the sweep counts the classes, not the path.** A shared implementation is verified once per class that inherits it, because the thing that varies is what each class declares itself to be.

### Non-goals (named so they are not re-explored or scope-crept)

- **Physical quarantine of bad notes** (rename/sidecar) — routed to `lint_vault` / WI-026; it is a deliberate tool action, not a library read behaviour. See A4.
- **Malformed-but-non-blank vault paths / the write-side `mkdir(parents=True)` bogus-tree** — the write half of WI-024's reroute #2; recommend WI-004 owns it (see Inherited scope). This item surfaces, it does not guard the write.
- **`lint_vault`'s import-time env read** (lint_vault.py:48) — latent, WI-026's territory (noted in WI-024).
- **Fixing the stale `_obsidian_schemas.pth`** — load-bearing as-is; explicitly out of scope (CLAUDE.md, `pipeline-runners.yaml`).
- **Migrating HAL9000's three N4 consumer call sites** (enricher, introducer, scheduler) — they live in another repository this project's hermetic floor cannot import or exercise, and no `kind: command` runner is registered here that could audit them (see the red-team response above). AC-5 instead pins the locally-verifiable backward-compat property: no legitimate no-op's return value changes. **Parked for Dave's call — mint a companion work item in HAL9000.**

## Approach

Fix the defect class at its seam and let the read/write asymmetry fall out of one distinction. Make `parse_frontmatter` stop conflating "no frontmatter" with "frontmatter that failed to parse": the malformed case becomes a distinct, loud signal (typed error or discriminated result — spec-writer's call). Write/mutate paths then **refuse** rather than rebuild — no file is ever rewritten from a frontmatter dict that did not parse, and the on-disk note is left byte-for-byte untouched (C2, the keystone). That set is *derived*, not named: every caller of `parse_frontmatter` in the package that re-serializes and writes — `update_fields` (base.py:312), `update_frontmatter_field` (writer.py:247), `update_frontmatter_fields` (writer.py:286), **and `roundtrip_file` (writer.py:317), which the campaign's enumeration missed and which has no `try`/`except` at all**. Symmetrically, the fix must not break the legitimate half **across that same derived set**: a genuinely fence-less note must still accept frontmatter exactly as today at all four paths — including `update_fields`, on which ordinary field-setting against a freshly-created stub depends, and `roundtrip_file`, whose contract is to preserve content while normalising YAML. Malformed frontmatter is the only thing that becomes loud; absent frontmatter is untouched everywhere. Read/load paths **survive but surface** — WARN, and record the skip in a queryable count/list on the repository so a dropped note cannot silently drive duplicate creation (C4) — swept across the **four concrete `BaseRepository` subclasses**, each independently instantiated — `PersonRepository`, `CompanyRepository`, `MeetingRepository`, `BookRepository` — rather than across the three `_load_file` overrides they share between them (`base.py:181`, inherited verbatim by both `PersonRepository` and `CompanyRepository`, since `company.py` overrides neither `_load_file` nor `file_pattern`; `meeting.py:81`; **`book.py:77`**, likewise missed), for both failure predicates: YAML that will not parse, and YAML that parses but fails validation for a known `type`. That surface is scoped by **ownership evidence, not by the glob** — every repository globs files it does not own and decides ownership downstream of the parse being made loud, so a naive surfacing turns the signal into noise on a healthy vault. A file whose `type` is readable and is not this repository's type is decidably foreign and never enters the skip surface (`base._load_file` checks no `type` at all today, so post-fix every well-formed `@Acme.md` would otherwise report as a skipped *person* — `Person.type` is `Literal["person"]`, models.py:78 — and every person note as a skipped company, since both repositories share the `@*.md` glob). That exposure runs **both ways over one shared implementation**, so the ownership comparison is made against each repository's **own** declared `type_name` (the abstract property at base.py:126-130) and has to be proved from both chairs — `CompanyRepository` instantiated on the same vault as `PersonRepository`, each asserting its own skip-list — because a shared `_owns()` that reads correctly for the class someone tested can be hardcoded, inverted or mis-ordered for the class they did not. Conversely a file whose `type` is readable and **is** this repository's type but which still fails `model_validate` on some other field — `type: person` with `emails: "not-a-list"`, the only other way to fail given `extra="allow"` (models.py:31-32) and no custom validators — is decidably **owned** and drifted, and **must** be listed: that is C5's own duplicate-creation case, the one C4's story is about. Those two are the same code path (`parse_to_model` raising inside `model_validate`) with opposite answers, so **ownership must be decided on the raw `type` value read from the parsed frontmatter, independently of and prior to model construction — never by "did `model_validate` succeed"**, which is exactly the predicate `base._load_file` uses today via `isinstance` (base.py:179) and which would silently drop the owned-and-drifted note. A file whose `type` is unreadable but whose glob is a naming convention (`@*.md`, `Meeting *.md`) **stays** in the surface, because that is precisely the C4 case it exists for. `BookRepository`, whose `file_pattern` is the catch-all `*.md` (book.py:49-51), has neither kind of evidence for a malformed file and must not report it as a skipped book; the mechanism is the spec-writer's call, but each repository's fixture vault is derived from its own `file_pattern` and is heterogeneous, never single-type. The body-shrink guard (C3) refuses when it cannot read the existing body instead of assuming it empty — and must be designed alongside C2 so it does not re-swallow the new parse signal. `parse_to_model` distinguishes "known type, failed validation" (loud — schema drift) from "unknown type" (fine), the same shape one layer up (C5). Write paths make a genuine I/O failure **raise** (a `ValueError` subclass, per the package convention) while every case that is a *legitimate* no-op today — dedup, absent section with `create_if_missing=False`, To-Discuss item text not found — keeps the exact falsy value it returns today (N4). That sweep is likewise derived rather than named, and by **two** predicates: the blanket `except Exception` in a writer, and the frontmatter-fence split (`content.startswith("---")` → `split("---", 2)`), which is copy-pasted across four writers — `append_to_body_section`, `add_to_discuss_item`, `update_to_discuss_item`, `remove_to_discuss_item` — so "no fence" and "malformed fence" stop being a `False` in all four, not just the one earlier rounds cited. Running that second predicate also exposed a fifth member nothing had seen: `_get_body_content` (person.py:1622-1626) answers an unsplittable fence by returning the whole file, frontmatter and all, as body — a read, so it surfaces rather than raises, but it must stop letting `get_to_discuss_items` report a broken note as "no items." Stated that way, the contract change is one-directional and locally provable: no consumer-visible return value changes except where it was reporting a failure as a no-op, so an existing `if not repo.append_to_body_section(...)` branch keeps its current meaning and only a genuine data-loss stops being silent. The cross-repo consumer migration this implies is parked — see Non-goals. Every fix ships its invariant test; the keystone is the malformed-YAML round-trip regression. The two WI-024 reroutes: narrow `_known_companies`' bare `except` at person.py:1147-1160 **at the except clause itself**, so a genuine `VaultPathNotConfiguredError` propagates rather than merely being re-logged (its own AC, since a log-level change would otherwise satisfy the wording); and surface the non-existent-vault load here, but recommend WI-004 owns the write-side `mkdir` guard (flagged for Dave's sign-off, not encoded below).

## Acceptance Criteria

Draft acceptance criteria — a convergence artifact ("what would prove this worked?"), to be reviewed and frozen with Dave via `/review-spec` before origination (the `ac-signoff` fence is written by code after his review, never here), then refined in place by the spec-writer. Each `check:` name is a proposed test the build will implement.

**Revised 2026-07-24** in response to the decorrelated red-team recorded below. Three structural changes: each AC that quantifies over a class now **derives** its sweep from the code rather than naming a list (which turned up two missed class members — see the red-team response in Exploration Notes); the malformed-must-raise half is now paired with the **absent-must-still-succeed** half so the fix cannot over-shoot; and AC-5's cross-repo consumer audit is **removed** — no check available in this repo can verify it (see Non-goals) — replaced by a backward-compat property that is locally provable.

**Revised again 2026-07-24 (round 2)** after the re-verify pass. Both remaining gaps were an AC deriving one half of its property and hand-writing the other. AC-1's absent-must-succeed half now quantifies over the **same** derived four-path list as its raise half; AC-5 now carries an explicit **second derivation predicate** (the frontmatter-fence split) instead of naming one function's branches — which turned up a fifth site (`_get_body_content`) that no prior pass had seen. Rule for anything added later: **an AC names its predicate, never its sites.**

**Revised again 2026-07-24 (round 3)** after the second re-verify. One gap, and it is the round-2 rule missing its other half: AC-3 derived its *repository* sweep from the code but hand-picked its *fixture space*, so `BookRepository`'s catch-all `"*.md"` glob (book.py:49-51) would have made every malformed note in the vault a "skipped book". Re-deriving the fixture space per repository from its own `file_pattern` also exposed a larger case on a **healthy** vault: `PersonRepository` and `CompanyRepository` share the `@*.md` glob and `base._load_file` checks no `type` at all, so post-fix every company note would report as a skipped person. AC-3 now derives its fixture vault per repository, requires it to be heterogeneous, and asserts the skip surface in both directions. Extended rule: **an AC names its predicate, never its sites — and derives its fixture space, never samples it.**

**Revised again 2026-07-24 (round 4)** after the third re-verify. One gap, inside AC-3's own fixture list: "a known type fails Pydantic validation" names two mechanically identical cases — a foreign `type: company` note under `PersonRepository`, and an owned `type: person` note that fails on another field — with **opposite** required answers, and the doc gave a worked example only for the one that must be *excluded*. So the owned-but-drifted note that is C5's actual duplicate-creation driver was never pinned as present, and the natural implementation ("if the model failed to build, it isn't mine") would drop it while every AC read green. AC-3 now requires **three distinct fixture files**, forbids (b) and (c) from being the same file, and states the mechanism-forcing property this turns on: **ownership is decided on the raw `type` value, never on whether `model_validate` succeeded.** Rule added: **two fixtures that share a code path but require opposite answers must be two files, asserted in one test.**

**Revised again 2026-07-24 (round 5)** after the fourth re-verify. One gap, and it is the round-4 rule one level out: AC-3 derived its fixture space per repository but derived its *repository sweep* from the three `_load_file` **overrides**, which collapses `PersonRepository` and `CompanyRepository` — two classes sharing one inherited implementation and one `@*.md` glob — into a single sweep entry. Every fixture, direction and Example of done in the doc was written from `PersonRepository`'s side, so a test parametrized over `{PersonRepository, MeetingRepository, BookRepository}` read as satisfying the AC while the *larger* half of round 3's healthy-vault exposure — "every person note becomes a skipped company" — shipped unverified, and a comparison hardcoded to one type literal instead of `self.type_name` would pass it. AC-3 now sweeps the **four concrete `BaseRepository` subclasses**, requires `PersonRepository` and `CompanyRepository` to be **independently instantiated** against the same shared vault and asserted in all three directions each, derives each class's own (b)/(c) fixtures from its own `type_name` and model fields, and a seventh Example of done pins the company side in Dave's terms. Rule added: **when two classes share one code path, the sweep counts the classes, not the path — a shared implementation is verified once per class that inherits it.**

```criteria
id: AC-1
desc: No write/mutate path rebuilds a note from a frontmatter parse that failed, and no legitimate parse loses its ability to write. The test parametrizes over the write paths DERIVED from the package itself — every caller of parse_frontmatter that then re-serializes and writes, today update_fields (base.py:312), update_frontmatter_field (writer.py:247), update_frontmatter_fields (writer.py:286) and roundtrip_file (writer.py:317) — enumerated from the code, never a hand-picked subset, so a fifth such caller added later joins the sweep. For EACH path, on a note whose frontmatter is malformed YAML the call raises a typed ValueError subclass AND the file on disk is byte-identical to before (original content never duplicated into the body, frontmatter never replaced by the partial updates). Conversely, and over the SAME derived path list rather than a subset of it, on a note with genuinely absent frontmatter (parser.py:64-65) NO path raises — each of the four still behaves exactly as it does today, asserted against a baseline captured from the current tree (same return value AND same resulting file bytes), so update_fields and update_frontmatter_field(s) still add the frontmatter and preserve the body, and roundtrip_file still honours its documented contract of preserving all content. Malformed YAML is the ONLY input the raise half licenses; a fix that also raises on absent frontmatter at ANY path in the sweep fails this criterion, and a fix that special-cases absent at some paths but not others fails it too.
kind: test
check: test_no_mutation_writes_through_failed_parse
```

why: this is the keystone — the C2 corruption chain, confirmed live, destroys and duplicates real note content silently; asserting on-disk bytes rather than merely "it raised" is what closes the door, deriving the path list is what stops the fix landing on one of four, and quantifying the absent-frontmatter half over that SAME derived list (not the two paths it originally named) is what stops a builder satisfying the raise-half by making parse_frontmatter refuse everything it cannot hand back a real dict for and then special-casing only the paths the AC happened to check — which would leave update_fields raising on every freshly-created stub and roundtrip_file raising on every frontmatter-less note it normalizes.

```criteria
id: AC-2
desc: The parse boundaries distinguish failure from a legitimate empty/unknown result, with a case per outcome DERIVED from each function's own branch structure rather than a sampled fixture. For parse_frontmatter that is one case per return site — no leading fence (parser.py:64-65), an opening fence with no closing fence (69-70), a fence present but empty (73-75), valid frontmatter (77), and YAMLError (78-80). Malformed YAML must never return the same value as a fence-less or empty-fence document, and the legitimate cases must keep returning today's value so existing callers are unchanged. The unclosed-fence case must be classified explicitly as absent or as malformed — not left to default by accident — because append_to_body_section already treats that same input as a distinct malformed-fence case (person.py:1564-1570). For parse_to_model, a known type whose model_validate raised (loud — schema drift) is distinguishable from a legitimately unknown or unmodelled type (returns None as today, parser.py:135-137). Every distinction is observable by the caller, not only in a log line.
kind: test
check: test_parse_boundaries_distinguish_failure_from_empty
```

why: C2 and C5 are the same defect one layer apart — a parse failure rendered as the success-shaped value a legitimate empty/unknown case also produces; enumerating the return sites is what makes the property total over the class instead of true for the one fixture someone picked, and it is what surfaced the unclosed-fence case two parts of this package already disagree about.

```criteria
id: AC-3
desc: A batch load survives a bad note, surfaces it at WARNING (never DEBUG), and surfaces ONLY the notes that repository owns — proven over the COMPLETE derived 4x3 matrix, one worked fixture set PER repository class, each derived from that class's OWN model fields and its OWN _load_file structure (never transposed by hand from a sibling): (1) PersonRepository (inherits base._load_file base.py:171-183, glob @*.md, isinstance-after-construction) — (a) malformed-YAML @-note in its skip surface; (b) own-type-drifted type person + emails "not-a-list" (Person.emails List[str], models.py:81) MUST be listed; (c) foreign readable type (@Acme.md type company) MUST NOT be listed. (2) CompanyRepository (same inherited path and glob, independently instantiated and independently asserted in BOTH directions — sharing code is not sharing proof) — (b) type company + tags "not-a-list" (its only list field is the INHERITED BaseEntity.tags, models.py:40 — derived, not transposed); (a) and (c) mirrored with company-owned fixtures. (3) MeetingRepository (OWN _load_file meeting.py:64-83, glob "Meeting *.md", raw-type prefilter meeting.py:72-75 BEFORE parse_markdown_file, own except meeting.py:81-83) — (a) malformed-YAML "Meeting X.md" listed; (b) type meeting + attendees "not-a-list" (Meeting.attendees List[str]) MUST be listed — this fixture passes the prefilter and fails only inside parse_markdown_file, exercising meeting.py's except under the new failure mode; (c) a "Meeting Y.md" with type person excluded via the prefilter (the naming-convention glob makes strays rare — asserted anyway, reasoning stated). (4) BookRepository (OWN _load_file book.py:57-79, CATCH-ALL glob *.md book.py:49-51, prefilter book.py:67-70, own except book.py:77-79) — (b) type book + tags "not-a-list" (Book declares NO own list field; the inherited tags is the derivation, stated explicitly) MUST be listed; (a)/(c) per the ownership-evidence buckets (readable-foreign excluded; unreadable-type under the catch-all glob per the four-bucket taxonomy); the heterogeneous-vault requirement stands (one vault mixing @-notes, Meeting-notes, and bare-titled book notes). For EVERY one of the twelve cells additionally assert NO-ABORT: the fixture's failure is caught inside that class's OWN _load_file and never propagates into BaseRepository.load()'s bare for-loop (base.py:157-165 has NO try/except — one escaped exception aborts the whole batch, the C4/HAL9000-startup regression), so any implementation that narrows meeting.py's or book.py's except clause must still catch the new typed validation failure, and the test proves it per class rather than assuming the base-path result transfers.
kind: test
check: test_batch_load_survives_and_surfaces_only_owned_bad_notes
```

why: C4 is the duplicate-creation engine — an invisible note makes resolve() miss and find_or_create_stub mint a dup; a queryable skip-list is required because a log line is exactly the mechanism that already failed, and the schema-drift fixture is required because "unparseable-or-invalid" otherwise reads satisfied while half the same consequence is never exercised at the repository level. That fixture has to be its OWN file, distinct from the foreign-type one, because the two are the same code path with opposite answers: the natural way to exclude a well-formed @Acme.md from PersonRepository's skip-list — "if the model failed to build, it isn't mine" — also excludes an owned @Broken.md carrying type: person with a non-coercible field, which is precisely the note whose disappearance mints the duplicate. One fixture cannot prove both halves; forcing three files and forbidding ownership to be read off model construction is what makes the skip-list mean "these are mine and they need attention" rather than "these are the ones I happened to be able to parse." Deriving the fixture space from each repository's own glob is what stops the surface being trustworthy in the test and noise in production: every repository globs files it does not own and decides ownership downstream of the parse this item makes loud, so on a real heterogeneous vault a naive fix reports every company note as a skipped person, every person note as a skipped company, and every malformed note anywhere in the vault as a skipped book. A signal that cries wolf on day one fails the same way the unread DEBUG line fails, and asserting the surface in both directions — owned bad note present, decidably-foreign note absent — is the only form a single-type fixture cannot fake. Sweeping the four repository CLASSES rather than the three `_load_file` code paths applies that same rule one level out: `PersonRepository` and `CompanyRepository` are two classes sharing one inherited implementation and one glob, and the healthy-vault exposure between them runs both ways, so a test that instantiates only the first proves half a property. The natural implementation — a shared `_owns()` on `BaseRepository` — is precisely the kind that reads `self.type_name` correctly for the class that was exercised while a hardcoded, inverted, or mis-ordered comparison goes unnoticed for the class that was not, which is why the AC counts instantiated classes and not code paths.

```criteria
id: AC-4
desc: The WI-126 body-shrink guard refuses when it cannot verify, and does not re-swallow the signal AC-1/AC-2 introduce. write_markdown_file's guard (writer.py:184-195) raises rather than setting existing_body = "" for BOTH required fixtures — (a) the existing file's frontmatter is malformed YAML, the coupling case the Constraints section flags as highest-risk, since post-AC-2 parse_frontmatter raises there and today's bare except Exception would re-bury it; and (b) the existing file cannot be read at all (permission or IO error). Naming (a) explicitly is required: a test built only around a generic read error would satisfy the guard's wording while never proving the coupling holds. The except clause is narrowed so neither case reaches existing_body = "", and the guard's refusal is distinguishable from BodyTruncationError.
kind: test
check: test_body_guard_refuses_when_unverifiable
```

why: C3 is the one mechanism protecting against body-wipe turning itself off exactly when it cannot confirm it is safe; it sits directly downstream of parse_frontmatter, so the malformed-YAML fixture is the whole point — without it C3 lands green and silently re-opens C2 on the overwrite path.

```criteria
id: AC-5
desc: Write paths make genuine failure raise while every legitimate no-op keeps its current return value. The test classifies every falsy-return site DERIVED from the package by TWO predicates rather than by a name list, so a site added later joins the sweep automatically. Predicate 1 is the blanket except Exception in a writer (writer.py:259 and 298; person.py:1500, 1603, 1702, 1775, 1837) - a genuine I/O failure (disk full, torn write, permission denied) raises a typed ValueError subclass, so it can no longer be misread as a no-op and a consumer's existing except ValueError still catches it. Predicate 2 is the frontmatter-fence split (content.startswith("---") followed by split("---", 2)), which yields FIVE sites in person.py rather than the single function earlier rounds named - append_to_body_section (1558-1570), add_to_discuss_item (1675-1683), update_to_discuss_item (1734-1742) and remove_to_discuss_item (1801-1809), where "no fence" and "malformed fence" are pseudo-no-ops that are really failures and move to the raise side for ALL FOUR, so neither can keep returning the same False a legitimate item-not-found returns; plus the read helper _get_body_content (1622-1626), which today falls through to return content and hands its caller the whole file, frontmatter included, as body. Being a read it surfaces rather than raises, but the test must assert a caller can distinguish an unsplittable fence from a genuinely empty body, so get_to_discuss_items can no longer report a broken-fence note as having no items. No-op half - every case that is a legitimate no-op today (deduplicated; absent section with create_if_missing=False; To-Discuss item text not found at 1746-1747, 1759-1761 and 1822-1824) returns the SAME falsy value it returns today, so an existing caller's `if not repo.append_to_body_section(...)` branch keeps its current meaning. Net contract change is one-directional - no consumer-visible return value changes except where it was reporting a failure as a no-op.
kind: test
check: test_write_failure_raises_and_noops_keep_their_return
```

why: N4 collapses "your data was skipped on purpose" and "your data was lost" into one bare False. The original wording bundled a cross-repo consumer audit that nothing in this repo can verify — HAL9000 is not in this tree, the floor is hermetic, and no runner is registered here that could lint another repo — so the audit is parked (Non-goals) and replaced by the strongest property that IS provable locally: the no-op returns are frozen, so the only behaviour any existing consumer sees change is a silent data-loss becoming loud. Naming a second derivation predicate rather than one function's branches is what makes that total: the fence-split shape is copy-pasted across four writers, so fixing only the one a prior round happened to cite would leave update_to_discuss_item still reporting a corrupted fence as "nothing matched" — and running the predicate is what exposed the fifth site, a read helper that answers a broken fence by returning the frontmatter as body.

```criteria
id: AC-6
desc: The bare except in _known_companies (person.py:1147-1160) is narrowed at the except clause itself, not merely re-logged. A VaultPathNotConfiguredError raised inside that try block PROPAGATES out of _known_companies rather than being swallowed — the WI-024 error this bare except currently buries — while the expected-unavailable case it exists for (ImportError on the CompanyRepository import) is still caught and still degrades to the person-company set. Changing logger.debug to logger.warning without narrowing the except clause does not satisfy this criterion.
kind: test
check: test_company_set_except_is_narrowed_not_just_logged
```

why: split out of AC-3 because riding on "not swallowed to DEBUG" is satisfiable by a log-level change on the same bare except — precisely the move A5 rejects; asserting that a specific unexpected exception propagates forces the mechanism rather than the symptom, and a criteria fence carries exactly one check.

### Examples of done

**Given** a person note whose frontmatter has a stray unquoted colon (invalid YAML), **when** a skill calls `update_frontmatter_field` to bump `last_contacted`, **then** it raises loudly and the note on disk is untouched — instead of silently rewriting the file with the whole original note dumped into the body and the frontmatter replaced by just `last_contacted`.

**Given** a vault where one of 400 notes has malformed frontmatter, **when** HAL9000 starts up and loads all people, **then** the other 399 load fine, startup logs a WARNING naming the one skipped file, and the repository reports a skip-list of length 1 — instead of the load aborting, or the bad note vanishing silently so `resolve()` later mints a duplicate.

**Given** an `append_to_body_section` write that fails midway because the disk is full, **when** the caller checks the result, **then** it sees a raised exception — instead of the same `False` it gets when the line was already present and deliberately skipped. **And given** that same caller's dedup path, **when** the line was already present, **then** it still gets exactly the `False` it gets today, so its existing `if not …:` branch is untouched.

**Given** a brand-new note with no frontmatter fence at all, **when** *anything* writes to it — `update_frontmatter_field` setting `last_contacted`, `update_fields` setting a field on a freshly-created stub, or `roundtrip_file` normalising it — **then** every one of them succeeds exactly as today, byte-for-byte, and the note gains (or keeps) its content unchanged. The hardening refuses malformed frontmatter, not absent frontmatter, and it refuses it at every write path or none.

**Given** Dave's real vault, where `@Sarah.md` (person), `@Acme Corp.md` (company), `Meeting 20260701 - Board.md` and `Four Thousand Weeks - Oliver Burkeman.md` all sit in one directory and exactly one person note has malformed frontmatter, **when** something asks `PersonRepository` what it skipped, **then** it names that one person note and nothing else — not the company notes it globbed and could plainly see were companies. **And when** something asks `BookRepository` what it skipped, **then** it does not claim that person note as a book it failed to load, even though its `*.md` glob matched it. The skip count means "these need attention", not "these are what my glob happened to catch."

**Given** `@Broken.md` — a real person note, `type: person`, that someone hand-edited so `emails:` holds a bare string instead of a list — sitting in that same vault next to `@Acme Corp.md`, **when** something asks `PersonRepository` what it skipped, **then** `@Broken.md` is on the list and `@Acme Corp.md` is not. The two notes fail the same way underneath — neither can be built into a `Person` — but one is Dave's contact with a typo in it and the other is a company that was never a person. Getting that backwards is how the duplicate gets minted: `@Broken.md` goes quiet, `resolve()` misses it, and a second Broken note appears.

**Given** that same vault, **when** something asks `CompanyRepository` — not `PersonRepository` — what *it* skipped, **then** it names `@Broken Corp.md` (the company note someone typed `tags: company` into instead of `tags: [company]`) and the malformed `@John.md` it globbed but genuinely cannot identify, and it does **not** name `@Sarah.md`, which plainly says `type: person`. The two repositories read the same `@*.md` files through the same inherited code, so "person notes are not skipped companies" has to be true from the company side too — a fix proven only from `PersonRepository`'s chair can still report all 400 people as companies that failed to load.

**Given** a person note whose frontmatter fence got truncated, **when** a skill calls `update_to_discuss_item` to tick an item off, **then** it fails loudly — instead of returning the same `False` it returns when the item text simply wasn't found, which would read as "nothing to tick" while the note sat corrupted. **And** `get_to_discuss_items` on that note says the file is unreadable rather than reporting it has no items.

## Relationship to other work

- **HAL9000 (companion item, not yet minted)** — the N4 return-contract change lands here, but the three consumer call sites (enricher, introducer, scheduler) live in HAL9000 and cannot be verified from this repo's hermetic floor. AC-5 freezes the no-op returns so nothing breaks silently; the migration itself is **parked for Dave's call** (see Non-goals). If minted, this item is its dependency.
- **WI-024 (remove hardcoded default vault path)** — done; its non-goals routed two findings here: the bare `except` at person.py:1147-1160 (in scope, now its own AC-6) and the "configured but wrong path" silent degrade (surfacing in scope; write-side `mkdir` guard recommended for WI-004). This item handles accident of *commission* at the note-parse boundary; WI-024 handled accident of *omission* at the vault-path boundary.
- **WI-004 (atomic write primitive)** — depends on the loud floor this item establishes; recommended owner of the write-side non-existent-vault `mkdir` guard (see Inherited scope). Sequencing: WI-020 first, then WI-004 builds on it.
- **WI-026 (lint_vault --fix safety)** — owns physical quarantine of bad notes (the deliberate-tool home for rename/sidecar, A4) and lint_vault's import-time env read.
- **Campaign** — Phase 1, first in queue (`docs/backlog-campaign-2026-07-05.md`); the 2026-07-05 code-health review is this item's exploration input.

## AC Red-Team — 2026-07-24

Decorrelated attack on the draft AC set (AC-1..AC-5), read Intent → Examples of done → Problem/Motivation → Exploration → Approach → ACs, in that order, per the gate's Step 2. Note: the doc already contains a "Red-team on the draft ACs" self-critique inside Exploration Notes (written by `ideation-partner` itself); that is the author checking their own work and is not a substitute for this decorrelated pass. Code claims below were re-verified against the current tree at the cited `file:line`, not trusted from the doc.

### CRITICAL — AC-5's cross-repo consumer audit is unverifiable by its own named check

AC-5 requires "the three consumer call sites (enricher/introducer/scheduler) are audited so the return-contract change breaks none of them silently," bundled into the single check `test_write_paths_distinguish_failure_from_noop`. I confirmed HAL9000 is not present in this tree (`Glob **/HAL9000/**` → no files found) — the enricher, introducer, and scheduler consumers live entirely in other repositories (HAL9000, per this project's own README "Used By" table and CLAUDE.md). `obsidian-schemas`' hermetic test floor (`.venv/bin/python -m pytest .../tests`) cannot import or exercise code in those repos.

**Concrete failure scenario:** a builder writes `test_write_paths_distinguish_failure_from_noop` against `obsidian_schemas`' own functions only (proving `append_to_body_section` now raises on I/O failure and stays falsy-but-distinct on dedup), ticks AC-5 green, and never opens HAL9000's enricher/introducer/scheduler source. Those three call sites still do `if not repo.append_to_body_section(...): <treat as dedup>` (per the Constraints section's own description of today's pattern) — and now a genuine disk-full raises an uncaught exception up through code that was written to treat any falsy return as a benign no-op. The "audit" — the one thing the doc calls out as this finding's differentiator from the other four ("the only finding that is not purely internal") — has no mechanism in the AC set that forces it to happen, let alone verifiably.

**What would have to change:** either (a) split the audit into its own AC with its own check that names a verifiable artifact — e.g. a written record of each of the three call sites with file:line and the before/after behavior, checked by a `kind: command` grep/lint rather than a local pytest test — or (b) if HAL9000 is a golden dependency reachable in the build environment, the check must actually import and exercise those three call sites (an un-stubbed integration per spec-quality-bar Check 10's WI-050 clause, since the consumer breakage IS the thing under test here), not merely assert on `obsidian_schemas`' own local behavior.

### MATERIAL — AC-1 quantifies over three write paths but names one check with no coverage requirement

AC-1's desc: "When `update_fields`, `update_frontmatter_field`, **or** `update_frontmatter_fields` is called on a note whose frontmatter is malformed YAML, the call raises..." — three distinct functions, one check: `test_no_mutation_writes_through_failed_parse`. Nothing pins the test to exercise all three call paths.

**Concrete failure scenario:** a builder fixes and tests `update_fields` (base.py) against a malformed-YAML fixture, and the single named check passes. `update_frontmatter_field`/`update_frontmatter_fields` (writer.py:247-295, the sibling rebuild path the doc itself cites at line 26 as part of the SAME corruption chain) are left un-fixed and still do `parse_frontmatter → rebuild → write` on the silent `({}, content)` — AC-1 reads satisfied while two of its three named functions still corrupt notes. This is the WI-185/WI-131 pattern the gate is chartered to hunt: the property quantifies over a class of three call sites; a single hand-picked fixture/check closes it on paper only.

**What would have to change:** either split into per-function checks (or a parametrized single test asserting all three), or state explicitly in `check:` / `desc:` that the test must cover all three named functions.

### MATERIAL — AC-1/AC-2 have no covering case for "absent frontmatter must still succeed"

The Approach section states the fix must make "malformed" distinguishable from "genuinely absent" so write paths can tell them apart — but every AC in the set only tests the malformed-and-must-raise half. Nothing in AC-1 through AC-5 asserts that a write/mutate call on a note with genuinely absent frontmatter (the legitimate case, `parser.py:64-65`) still succeeds and creates frontmatter as today.

**Concrete failure scenario:** a builder implements the simplest thing that makes AC-1 and AC-2 pass — `parse_frontmatter` raises on ANY case where it can't hand back a "real" frontmatter dict, absent included, not just on `yaml.YAMLError`. AC-1's raise-and-untouched assertion is satisfied (arguably over-satisfied), AC-2's "distinguishable" claim could even be read as satisfied by the presence of a new exception type. But a legitimately frontmatter-less note now can never have frontmatter added via `update_fields`/`update_frontmatter_field(s)` — a real regression on ordinary note creation — and no AC in the set would catch it, because none tests the absent-frontmatter write path at all. This is the "absence, not a wrong assertion" class the gate's Step 3 calls out as the one a checklist misses.

**What would have to change:** add an explicit positive case (to AC-1 or AC-2) asserting a write/mutate call on a genuinely-frontmatter-less note still succeeds and produces the expected frontmatter — pinning the "absent ≠ malformed" distinction from both directions, not just the malformed side.

### MATERIAL — AC-3 conflates two distinct failure predicates under one fixture word, and folds an unrelated narrowing into the same check with no mechanism-forcing assertion

Two separate issues in one AC:

1. **"unparseable-or-invalid"** covers both C2/C4's predicate (YAML that fails to parse) and C5's predicate (YAML that parses fine but fails Pydantic validation for a *known* `type`) — the doc's own Exploration Notes treat these as two different sites (parser.py:78 vs parser.py:148) with two different corruption/duplication stories. A single test fixture using only a malformed-YAML note would satisfy the literal text of AC-3 ("one unparseable-or-invalid note") while leaving the schema-drift-duplication path (C5, which the doc says drives the *same* WI-119/WI-125 duplicate-creation class) completely unexercised by this AC set — AC-2 tests `parse_to_model`'s distinction in isolation, but nothing requires AC-3's *repository-level* batch-load-and-surface behavior to be proven for a schema-validation-failure note, only for a parse-failure note.
2. The person.py:1147-1160 narrowing (re-verified live: still a bare `except Exception: logger.debug(...)`) is folded into the same check (`test_batch_load_survives_and_surfaces_bad_notes`) with a success condition of "not swallowed to DEBUG" — which a builder satisfies by changing `logger.debug` to `logger.warning` on the existing bare `except Exception`, without narrowing the except clause to let a genuine `VaultPathNotConfiguredError` (or anything unexpected) actually surface as the Approach section recommends ("narrow the except to the expected-unavailable cases... and let anything else surface"). The doc's own A5 rejects exactly this move ("Logging... has never stopped anything") for the sibling C4 finding, but AC-3's literal wording doesn't rule it out here.

**What would have to change:** (1) require a second fixture in AC-3 (or a companion AC) using a schema-validation-failure note, not only a YAML-parse-failure note; (2) reword the person.py:1147-1160 clause to require the except clause itself narrows (e.g., asserted by a test that a `VaultPathNotConfiguredError` raised inside the try block propagates rather than being swallowed), not merely that the log level changed.

### MINOR — AC-4's check doesn't force the fixture that exercises its own named coupling risk

AC-4's desc explicitly names the risk: "it does not re-swallow the malformed-parse signal AC-1/AC-2 introduce" — and the Constraints section calls this the one place "C2 and C3 are coupled," landing together or C3 "silently re-opens C2 on the overwrite path." But `test_body_guard_refuses_when_unverifiable` doesn't require the unverifiable-body fixture specifically be a malformed-YAML existing file (as opposed to a generic I/O read error, e.g. a mocked/permission-denied read) — a test built around the generic case would satisfy the AC's text while never actually proving the coupling holds.

**What would have to change:** name the malformed-YAML-existing-file case explicitly as one of the fixtures `test_body_guard_refuses_when_unverifiable` must cover, since it's the one the doc itself flags as highest-risk.

### What I attacked and found clean

- The keystone (AC-1's on-disk-byte-identity assertion, not merely "raises") correctly closes the WI-139-style "raise-only test stays green while a different path still corrupts" gap for whichever single path is tested.
- AC-2's framing of C2 and C5 as one property over both parse functions is sound and correctly scoped to the parser layer only (doesn't try to re-verify at the write layer, avoiding double-jeopardy with AC-1).
- No mutually unsatisfiable pair found among AC-1..AC-5.
- The non-goals and the two explicitly-parked items (physical quarantine; write-side `mkdir` guard) are honestly flagged as deferred rather than silently dropped, and are not re-litigated here.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-24
model: claude-sonnet-5
note: 1 CRITICAL (AC-5's cross-repo consumer audit unverifiable by its own local-suite check, HAL9000 confirmed absent from this tree) + 4 MATERIAL/MINOR class-closing and coverage gaps across AC-1/AC-3/AC-4 — draft not signable as-is.
```

## AC Red-Team — 2026-07-24 (re-verify)

Re-spawned to verify the fold that followed the pass above. Read Intent → Examples of done → Problem/Motivation → Exploration → Approach → the revised ACs (AC-1..AC-6), per Step 2, then re-read the prior fence's five findings against the current draft. Confirmed live against the tree at every cited `file:line`, not trusted from the doc: `obsidian_schemas/parser.py`, `repositories/base.py`, `writer.py`, `repositories/person.py`, and the `_load_file`/`Repository` class list (`Grep` for `def _load_file` and `class .*Repository` — confirms only `base.py`, `meeting.py`, `book.py` override it, matching AC-3's named sweep exactly; no missed repository).

### What the fold changed, and what it fixed cleanly

- **CRITICAL (AC-5 cross-repo audit)** — RESOLVED. The audit clause is gone; AC-5 now states a locally-provable, one-directional property ("no consumer-visible return value changes except where it was reporting a failure as a no-op"). This is verifiable from this repo's own hermetic floor. Correctly parked the migration in Non-goals rather than dropping it.
- **MATERIAL (AC-1 named three functions, one check, no coverage requirement)** — RESOLVED. AC-1 now reads "the test parametrizes over the write paths DERIVED from the package itself... For EACH path..." — mechanism-forcing, not satisfiable by fixing one of the four.
- **MATERIAL (AC-3 conflated two failure predicates, folded the person.py narrowing in with a gameable log-level fix)** — RESOLVED. AC-3 now names two required fixtures explicitly (parse-failure and schema-drift). The person.py:1147-1160 narrowing was split out into its own AC-6, which asserts a `VaultPathNotConfiguredError` PROPAGATES and explicitly rules out a `logger.debug`→`logger.warning` change as satisfying it. Re-read person.py:1147-1160 live: still the pre-fix bare `except Exception`, as expected pre-build.
- **MINOR (AC-4 didn't force the malformed-YAML fixture specifically)** — RESOLVED. AC-4 now names fixture (a) "the existing file's frontmatter is malformed YAML" explicitly as required, not just a generic read error.

### MATERIAL — AC-1's new absent-must-succeed half covers 2 of the 4 write paths its own raise-half quantifies over

AC-1's malformed-raise half is derived over all four write paths ("For EACH path..., every caller of parse_frontmatter that then re-serializes and writes... update_fields, update_frontmatter_field, update_frontmatter_fields, roundtrip_file"). Its new positive half — added specifically to close the previous round's "absent must still succeed" gap — only names two: "on a note with genuinely absent frontmatter, update_frontmatter_field and update_frontmatter_fields still succeed." `update_fields` (base.py:278-334) and `roundtrip_file` (writer.py:302-324) are absent from the positive half, even though both are named in the same sentence's negative half and both run the identical `parse_frontmatter → rebuild → write` shape on an absent-frontmatter file (re-read live: both would happily rebuild `{}`→`---\n---\n{body}` today).

**Concrete failure scenario:** a builder makes `parse_frontmatter` raise a typed error whenever it cannot hand back frontmatter it parsed from a real fence — malformed YAML *or* genuinely-absent frontmatter alike — but adds a special-cased early-return in `update_frontmatter_field`/`update_frontmatter_fields` for the absent case so those two still succeed (satisfying their explicit positive assertions). AC-1 reads fully green: the raise-half holds for all four paths (absent now raises too, which the AC never rules out), and the positive half holds for the two paths it actually checks. But `update_fields` now raises on any note that doesn't yet have frontmatter — breaking ordinary field-setting on a freshly-created stub — and `roundtrip_file` (whose own docstring is "read and re-write a file, preserving all content... normalizing YAML formatting") now raises on any frontmatter-less note it's asked to normalize. Nothing in the AC set catches either regression.

**What would have to change:** extend the positive half to the same derived list as the negative half — assert `update_fields` and `roundtrip_file` also still succeed (produce/preserve the expected content, unchanged) on a genuinely-absent-frontmatter fixture.

### MATERIAL — AC-5's failure/no-op reclassification is derived for one function and hand-applied to a sibling of four

AC-5 explicitly reclassifies two of `append_to_body_section`'s branches as "pseudo-no-ops that are really failures": no frontmatter fence (person.py:1558-1563) and malformed fence / `len(parts) < 3` (1564-1570) — both "move to the raise side" per the AC text. But `person.py` has three siblings with the byte-for-byte identical shape — `add_to_discuss_item` (1674-1683), `update_to_discuss_item` (1733-1742), `remove_to_discuss_item` (1800-1809) — each doing `if content.startswith("---"): parts = content.split("---", 2); if len(parts) >= 3: ... else: return False / else: return False`, i.e. the same "no fence" / "malformed fence" pseudo-no-op collapsed into the same `False` a legitimate "item text not found" also returns (1761, 1824 — via `logger.debug`, itself the C4 pattern one level up). AC-5's site list only pulls each function's `except Exception` block (1500, 1603, 1702, 1775, 1837); it never derives the no-fence/malformed-fence branches beyond the one function where the previous round happened to name them.

**Concrete failure scenario:** a builder fixes `append_to_body_section`'s two named pseudo-no-ops (they raise now) and makes the five `except Exception` sites raise per AC-5's explicit sweep. `test_write_failure_raises_and_noops_keep_their_return` passes. `update_to_discuss_item` on a person note with a corrupted/missing frontmatter fence still silently returns the same `False` a caller gets for "no To-Discuss item matched that text" (line 1746-1747, 1761) — a genuine anomalous-file state misreported as "nothing to do," the exact N4 conflation this item exists to close, in three functions AC-5 never looks at.

**What would have to change:** derive AC-5's no-fence/malformed-fence reclassification the same way its `except Exception` sweep is derived — across all four functions sharing the pattern (`append_to_body_section`, `add_to_discuss_item`, `update_to_discuss_item`, `remove_to_discuss_item`), not just the one the prior round named.

### What I attacked and found clean

- AC-2's four-way parser branch coverage: re-verified all five `parse_frontmatter` return sites (parser.py:64-65, 69-70, 73-75, 77, 78-80) map onto AC-2's five named cases; no branch left uncovered.
- AC-3's repository sweep: re-verified by grep that `base.py`, `meeting.py`, `book.py` are the only three `_load_file` overrides in the package — the named sweep is actually complete, not merely asserted.
- AC-6 is scoped to a single except clause with a mechanism-forcing assertion (propagation, not log-level) — no class-quantification exposure, no conflict with AC-3.
- No new mutually-unsatisfiable pair introduced by the fold (AC-6's split from AC-3 removes rather than creates a conflict).

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-24
model: claude-sonnet-5
note: Fold resolved 4/5 prior findings cleanly (CRITICAL AC-5 audit, AC-1 coverage requirement, AC-3 split/fixtures, AC-4 fixture naming); re-verify found 2 NEW MATERIAL gaps — AC-1's absent-must-succeed half covers 2 of the 4 paths its own raise-half derives over (update_fields, roundtrip_file uncovered), and AC-5's no-fence/malformed-fence reclassification was applied to append_to_body_section only, leaving 3 byte-identical sibling functions (add/update/remove_to_discuss_item) still collapsing that failure into the same False as a legitimate not-found — still not signable.
```

## AC Red-Team — 2026-07-24 (re-verify 2)

Re-spawned to verify the fold that followed the round-2 re-verify above. Read Intent → Examples of done → Problem/Motivation → Exploration → Approach → the current ACs (AC-1..AC-6), per Step 2, then re-read the prior fence's two findings against the current draft. Every code claim below re-read live against the current tree: `obsidian_schemas/parser.py`, `repositories/base.py`, `writer.py`, `repositories/person.py`, `repositories/meeting.py`, `repositories/book.py`; confirmed by `Grep` that only `base.py`, `meeting.py`, `book.py` override `_load_file` (matching AC-3's named sweep, no missed repository).

### What the fold changed, and what it fixed cleanly

- **MATERIAL (AC-1's absent-must-succeed half covered 2 of 4 derived paths)** — RESOLVED. AC-1 now reads "Conversely, and over the SAME derived path list rather than a subset of it, on a note with genuinely absent frontmatter... NO path raises — each of the four still behaves exactly as it does today... so `update_fields` and `update_frontmatter_field(s)` still add the frontmatter and preserve the body, and `roundtrip_file` still honours its documented contract." All four paths (`update_fields`, `update_frontmatter_field`, `update_frontmatter_fields`, `roundtrip_file`) are now named on both halves, closing the special-casing gap the prior round found.
- **MATERIAL (AC-5's fence-split reclassification applied to `append_to_body_section` only)** — RESOLVED. AC-5 now names all four sibling functions explicitly: "`append_to_body_section` (1558-1570), `add_to_discuss_item` (1675-1683), `update_to_discuss_item` (1734-1742) and `remove_to_discuss_item` (1801-1809)... move to the raise side for ALL FOUR" — re-verified live that all four share the byte-identical `content.startswith("---")` / `split("---", 2)` shape (person.py:1675-1683, 1734-1742, 1801-1809). The fold also correctly kept `_get_body_content` (1622-1626) on the surface side rather than the raise side, matching its status as a read helper.

### MATERIAL — AC-3's derived repository sweep is correct, but its fixture space isn't: `BookRepository`'s unscoped glob turns the fix into cross-type skip-list pollution

AC-3 derives its repository sweep correctly (`base.py:181-183`, `meeting.py:81-83`, `book.py:77-79` — re-verified as the only three `_load_file` overrides). But `BookRepository.file_pattern` is `"*.md"` (book.py:49-51: *"Books use 'Title - Author.md' format, not @prefix"*) — deliberately unscoped, matching **every** markdown file in the vault, not just book notes. Contrast `MeetingRepository` (`"Meeting *.md"`, meeting.py:50-52) and the base default (`"@*.md"`, base.py:133-135), both of which are scoped by naming convention.

`book.py`'s `_load_file` (book.py:57-79) calls `parse_frontmatter(content)` directly at line 67 to read the `type` field, and only *after* that call checks `if frontmatter.get("type") != "book": return None` (line 70-71) to exclude non-book files. Today this ordering is harmless: a malformed-YAML file of any type silently returns `({}, content)`, `frontmatter.get("type")` is `None`, the type check excludes it, `_load_file` returns `None` — no error, no log, correctly invisible to `BookRepository`. Once `parse_frontmatter` is fixed (per AC-1/AC-2) to raise/signal loudly on malformed YAML — the natural implementation, since AC-1 requires "the call raises a typed ValueError subclass" and the Constraints section recommends a single `FrontmatterParseError` raised at the seam — that raise now fires at line 67, **before** the type filter at line 70 ever runs. It is caught only by the outer `except Exception` (book.py:77-78), which AC-3 requires to move from `logger.debug` to `logger.warning` + a queryable skip-list entry.

**Concrete failure scenario:** a vault contains one malformed-YAML person note (`@John.md`, no actual book content) and zero malformed book notes. `BookRepository(vault).load()` globs `*.md`, matches `@John.md` (it matches every extension-`.md` file, not just `Title - Author.md` ones), `_load_file` calls `parse_frontmatter` on it, hits the new raise, is caught by the outer except, and — per AC-3's own required behavior — is logged at WARNING and added to `BookRepository`'s skip-list, even though `@John.md` was never a book and `BookRepository`'s skip-list is supposed to answer "which books failed to load." A builder satisfies AC-3's literal text ("the repository exposes a queryable count/list of skipped files that the test asserts contains exactly the bad notes") by testing each repository against a single-type vault fixture (a book-only vault for `BookRepository`, a person-only vault for `PersonRepository`) — the natural, minimal fixture — and never exercises the heterogeneous vault that is the *only* kind that actually exists (Dave's real vault mixes `@Name.md`, `Meeting *.md`, and bare-titled book files in one directory). Against that real vault, `BookRepository.get_skipped()` (or whatever AC-3's queryable surface is named) reports every malformed note in the entire vault as a "skipped book," inflating and misdirecting the signal AC-3 exists to make trustworthy — the same note gets reported as skipped by `PersonRepository` (correctly) and by `BookRepository` (incorrectly), and a consumer reading `BookRepository`'s count as "N books need attention" is misled.

**What would have to change:** AC-3 needs a fixture using a heterogeneous vault (at minimum: one malformed note of a type BookRepository does NOT own, sitting alongside legitimate book notes) and an assertion that `BookRepository`'s skip-list does NOT include it — or, if the chosen mechanism makes that unreachable without restructuring `book.py`'s check order (move the type-check before the raising parse, e.g. a cheap pre-check that the file even plausibly matches before invoking the loud parse), the AC must say so explicitly rather than leaving `BookRepository`'s glob-vs-type-filter mismatch to accident. This is the same "class-closing AC with a hand-picked fixture" pattern the role's Step 3 names (WI-185's AC-7): AC-3's DERIVED repository list is correct, but the FIXTURE SPACE per repository is not derived from each repository's actual glob scope, and the one repository with a genuinely mismatched scope (`BookRepository`) is exactly where the untested case lives.

### What I attacked and found clean

- AC-1's four-path derivation on both the raise-half and the absent-must-succeed half: re-verified `update_fields` (base.py:311-329), `update_frontmatter_field` (writer.py:245-260), `update_frontmatter_fields` (writer.py:284-299), and `roundtrip_file` (writer.py:302-324) are the complete, correct set of `parse_frontmatter` callers that re-serialize and write — no fifth caller found by grepping for `parse_frontmatter(` importers across the package.
- AC-5's five-site fence-split derivation: re-verified all five person.py sites (1558-1570, 1675-1683, 1734-1742, 1801-1809, 1622-1626) share the predicate and are now all named, with `_get_body_content` correctly kept on the surface (not raise) side.
- AC-4's malformed-YAML fixture requirement and the C2/C3 coupling it protects against: unchanged from the prior round's clean pass, still holds.
- AC-6's scope: a single narrowed except clause, mechanism-forcing (propagation, not log-level), no class-quantification exposure — re-verified person.py:1147-1160 is still the pre-fix bare `except Exception: logger.debug(...)`, as expected pre-build.
- No new mutually-unsatisfiable pair introduced by this fold.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-24
model: claude-sonnet-5
note: Both prior MATERIAL findings (AC-1's 2-of-4 absent-must-succeed gap; AC-5's single-function fence-split) are cleanly resolved. New MATERIAL finding: AC-3's repository sweep is correctly derived but BookRepository's unscoped "*.md" glob (vs. type-check ordering in book.py:67-71) means the fix will surface any malformed-YAML note of ANY type as a "skipped book" in a real heterogeneous vault, and AC-3's fixture wording doesn't force a multi-type vault test that would catch it — still not signable.
```

## AC Red-Team — 2026-07-24 (re-verify 3)

Re-spawned to verify the fold that followed the round-3 re-verify above (recorded as `## AC Red-Team — 2026-07-24 (re-verify 2)`). Read Intent → Examples of done → Problem/Motivation → Exploration → Approach → the current ACs (AC-1..AC-6), per Step 2, then re-read the prior fence's one finding against the current draft. Every code claim below re-read live against the current tree: `obsidian_schemas/models.py`, `obsidian_schemas/parser.py`, `repositories/base.py`, `repositories/book.py`, `repositories/person.py`. Confirmed live: `Person.type` is `Literal["person"] = "person"` and every other `Person` field (`name`, `aliases`, `emails`, `phones`, `whatsapp`, `company`, `title`, `linkedin`, `slack`, `roles`, `birthday`, `created`, models.py:78-90) is `str` or `List[str]` with no custom `@field_validator`/`@model_validator` anywhere in `models.py` — so the only way a `type: person` note fails `Person.model_validate` is (a) `type` itself not literally `"person"`, or (b) a field typed `List[str]` receiving a non-list scalar (e.g. `emails: "not-a-list"` or `roles: 3`), which Pydantic v2 rejects rather than coercing.

### What the fold changed, and what it fixed cleanly

- **MATERIAL (AC-3's fixture space was hand-picked; `BookRepository`'s unscoped `"*.md"` glob would surface any malformed note of any type as a "skipped book")** — RESOLVED. AC-3 now derives its fixture space per repository from that repository's own `file_pattern`, requires a heterogeneous vault, and states the `BookRepository` case explicitly ("neither kind of ownership evidence exists ... MUST NOT appear in whatever count a consumer would read as 'N books need attention'"). Re-verified live: `book.py:49-51` is still the catch-all `"*.md"`, `book.py:67-71` still parses before the type filter — the exposure is real and the AC's new wording forces a heterogeneous-vault test to catch it, not a single-type fixture. Correctly left the mechanism (ownership-undeterminable bucket, narrowed glob, or reordered check) to the spec-writer while pinning the property.

### MATERIAL — AC-3's fixture (b) is asked to both "appear in the skip surface" and, by its only worked example, NOT appear — the owned-schema-drift note that is C5's actual duplicate-creation driver is never pinned

AC-3's opening sentence states two required failure fixtures: "(a) a note whose YAML does not parse, and (b) a note whose YAML parses cleanly but whose known type fails Pydantic validation (schema drift, the C5 predicate) — **both must appear in the skip surface**." Read on its own, fixture (b) names exactly the C5 motivating case from Problem/Motivation: a `type: person` note that fails `Person.model_validate` for a reason *other than* the type field itself — the case I confirmed constructible above (e.g. `type: person\nemails: "not-a-list"`). This is genuinely **owned** (the raw `frontmatter.get("type")` a repository would read before/independent of model construction says `"person"`, matching `PersonRepository`), and per the sentence's own words it "must appear in the skip surface."

But the *only* worked example AC-3 gives anywhere for "known type fails Pydantic validation" is the "Foreign-and-absent" direction's `@Acme.md` — a well-formed `type: company` note loaded under `PersonRepository`, which fails `Person`'s `Literal["person"]` validation and, per that same AC, "MUST NOT be listed." Mechanically this is the identical code path as fixture (b) — `parse_to_model(fm, Person)` raising inside `model_validate` — but it is semantically a *different* case (foreign type, not owned-and-drifted), and AC-3 never disambiguates the two under the shared label "known type fails Pydantic validation." The Approach section's own ownership-evidence taxonomy (the three-bucket list: type readable-and-not-mine → foreign; type unreadable-and-naming-convention → surfaced; type unreadable-and-catch-all-glob → excluded) has no fourth bucket for "type readable AND mine, but another field fails validation" — the exact case fixture (b) is supposed to pin.

**Concrete failure scenario:** a builder reads AC-3, sees the single company-note-under-PersonRepository fixture satisfies both "(b) must appear in the skip surface" (it's a known-type validation failure) at a surface level and the explicit "Foreign-and-absent → MUST NOT be listed" assertion, ships that one fixture, and the test suite is green. The builder's ownership check — a natural, even likely implementation, since it reuses the exact mechanism that correctly excludes `@Acme.md` — is "attempt `parse_to_model(fm, Person)`; if it fails for any reason, this file is not mine, exclude it from the skip surface." A genuinely-owned `@Broken.md` (`type: person`, `emails: "not-a-list"`) now silently disappears from `PersonRepository`'s skip-list under this implementation too: `resolve()` misses it, `find_or_create_stub` mints a duplicate — the exact WI-119/WI-125 consequence AC-3's own `why:` text names as the reason fixture (b) exists ("the schema-drift fixture is required because 'unparseable-or-invalid' otherwise reads satisfied while half the same consequence is never exercised at the repository level") — and nothing in AC-3, the Examples of done, or the Approach section's ownership taxonomy would have caught it, because no worked example anywhere in the doc constructs an owned-but-drifted fixture and asserts it IS listed. AC-2 already forces `parse_to_model` itself to be loud on this exact fixture (it must not return the same `(None, dict)` as an unknown type) — but AC-2 only asserts on the parser function's return value in isolation; it never requires that signal survive into a repository's public skip-list, which is precisely the integration AC-3 exists to prove.

**What would have to change:** add an explicit fourth ownership-evidence case to the Approach's taxonomy and AC-3's "asserted in BOTH directions" list — "type readable AND matches this repository's type, but validation still fails on another field → decidably owned, MUST be listed" — with its own fixture (e.g. `type: person` plus a non-coercible field) distinct from the foreign-type example, so a single fixture can no longer discharge both the required-present and required-absent directions at once.

### What I attacked and found clean

- AC-1's four-path derivation on both halves: re-verified `update_fields` (base.py:311-329), `update_frontmatter_field` (writer.py:245-260), `update_frontmatter_fields` (writer.py:284-299), `roundtrip_file` (writer.py:302-324) are still the complete set; text unchanged since the round-2 fold, no regression.
- AC-2's five-return-site coverage of `parse_frontmatter` and its known-vs-unknown-type distinction for `parse_to_model`: unchanged, still total over the function's own branch structure. (AC-2 is the parser-level half of the gap above; it is not itself deficient — the gap is that AC-3 doesn't carry AC-2's owned-schema-drift fixture through to the repository layer.)
- AC-4's malformed-YAML-existing-file fixture requirement: unchanged, still names the coupling case explicitly.
- AC-5's five-site fence-split derivation across all four `person.py` siblings plus `_get_body_content` on the surface side: unchanged, still complete.
- AC-6's single narrowed except clause, mechanism-forcing (propagation, not log-level): unchanged, re-verified `person.py:1147-1160` is still the pre-fix bare `except Exception: logger.debug(...)`, as expected pre-build.
- No new mutually-unsatisfiable pair introduced by this fold.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-24
model: claude-sonnet-5
note: Prior MATERIAL finding (AC-3's fixture space hand-picked, BookRepository's unscoped glob) is cleanly resolved. New MATERIAL finding: AC-3's own two required fixtures collide — fixture (b) "must appear in the skip surface" but its only worked example (@Acme.md under PersonRepository) is also the AC's "Foreign-and-absent — MUST NOT be listed" case, so the owned-but-schema-drifted note (type: person, a field fails validation) that is C5's actual WI-119/WI-125 duplicate-creation driver is never pinned as present — still not signable.
```

## AC Red-Team — 2026-07-24 (re-verify 4)

Re-spawned to verify the fold that followed the round-4 re-verify above (recorded in Exploration
Notes as "Decorrelated AC red-team, round 4"). Read Intent → Examples of done → Problem/Motivation
→ Exploration → Approach → the current ACs (AC-1..AC-6), per Step 2, then re-read the prior
fence's one finding against the current draft. Every code claim below re-read live against the
current tree: `obsidian_schemas/models.py`, `obsidian_schemas/parser.py`,
`obsidian_schemas/repositories/base.py`, `repositories/book.py`, `repositories/meeting.py`,
`repositories/company.py`, `obsidian_schemas/writer.py`.

### What the fold changed, and what it fixed cleanly

- **MATERIAL (AC-3's fixture (b)/(c) collision — owned-and-drifted note never pinned as present
  because its only worked example was also the must-be-excluded foreign-type case)** — RESOLVED.
  AC-3 now requires **three distinct fixture files**, explicitly forbids (b) and (c) from being
  the same file, and states the mechanism-forcing property in full: ownership is decided on the
  raw `type` value read from the parsed frontmatter, "independently of and prior to model
  construction," never on whether `parse_to_model`/`model_validate` succeeded. Re-verified live in
  `models.py:31-32` (`extra="allow"`) and `models.py:78-90` (all `Person` fields beyond `type` are
  `str`/`List[str]`, no custom validators) that (b) and (c) are genuinely the same code path with
  opposite answers, confirming the fold's own reasoning is accurate, not just asserted. A sixth
  Example of done (the `@Broken.md` one, `emails: "not-a-list"` next to `@Acme Corp.md`) now pins
  fixture (b) in Dave's terms, matching the fold's own description.

### MATERIAL — AC-3's fixture/direction set is proven only from `PersonRepository`'s side; `CompanyRepository`, which shares the exact same `_load_file` code, is never independently exercised

AC-3's repository-sweep sentence reads: "The repository sweep is derived from the `_load_file`
overrides in the package (`base.py:181-183`, **used by both `PersonRepository` and
`CompanyRepository`**; `meeting.py:81-83`; `book.py:77-79`)." That parenthetical is doing real
work: it collapses `PersonRepository` and `CompanyRepository` into ONE entry in a three-item
sweep, because neither overrides `_load_file` — confirmed live, `repositories/company.py` (read in
full) defines no `_load_file`, no `file_pattern` override, and no ownership check of any kind; it
inherits `base.py:171-183` and `base.py:133-135` (`@*.md`) verbatim, exactly as `PersonRepository`
does.

But round 3's own finding (recorded above as "Exposure 2") stated the healthy-vault exposure is
**bidirectional**: "every company note becomes a skipped person and every person note a skipped
company." Every worked example anywhere in this document — AC-3's fixture (c) text ("a well-formed
note whose raw type field is a DIFFERENT repository's type (`@Acme.md` carrying `type: company`,
under `PersonRepository`)"), the "Foreign-and-absent" bucket text, and the fifth Example of done
("when something asks `PersonRepository` what it skipped, then it names that one person note and
nothing else — not the company notes it globbed") — exercises this **only from
`PersonRepository`'s side**. Nowhere in the doc — not in AC-3's fixture list, not in any Example of
done — is `CompanyRepository`'s own skip-list ever queried or asserted on. The mirror case (a
well-formed `@Sarah.md`, `type: person`, must NOT appear in `CompanyRepository`'s skip-list; an
owned `@Broken Corp.md`, `type: company`, with a non-coercible field, MUST appear in
`CompanyRepository`'s skip-list) has no worked example and no fixture requirement naming it.

**Concrete failure scenario:** a builder implements the ownership fix as a method on
`BaseRepository` — e.g. `self._owns(frontmatter) -> bool` reading `frontmatter.get("type")` against
`self.type_name` — and writes ONE test, parametrized (per AC-3's own "derive, don't name" rule) over
`{PersonRepository, MeetingRepository, BookRepository}`, i.e. one instance per `_load_file`
*override*, exactly matching the sweep sentence's literal enumeration of three. `CompanyRepository`
is never instantiated in the test at all. This reads as satisfying AC-3's text — the "repository
sweep" was explicitly defined as the three `_load_file` overrides, and this test covers all three —
while the specific consequence round 3 flagged as firing "on a perfectly healthy vault" (every
person note reported as a skipped company) ships completely unverified. This is not a purely
hypothetical mechanism gap either: `self.type_name` for `CompanyRepository` is `"company"`
(`company.py:67-68`) and for `PersonRepository` presumably `"person"` — a fix that hardcodes the
comparison value instead of reading `self.type_name` (or that has an off-by-one in a `!=`/`==`
somewhere) would pass a `PersonRepository`-only test and silently misreport under
`CompanyRepository`, and nothing in the current AC set would catch it. This is the same
single-instantiation-stands-for-a-class shape the gate's Step 3 names (the WI-131/WI-185 class:
"a class-closing AC with a hand-picked fixture" — here the fixture space per repository is
correctly class-derived per the round-3 fold, but the outer sweep over repository *classes*
sharing one code path is not).

**What would have to change:** either (a) reword the repository-sweep sentence so "for each
repository" is stated over the four concrete repository classes (`PersonRepository`,
`CompanyRepository`, `MeetingRepository`, `BookRepository`), not the three `_load_file`
*overrides*, with an explicit requirement that `PersonRepository` and `CompanyRepository` are each
independently instantiated and each asserted in all three directions against the shared
`@*.md`-globbed vault; or (b) if testing the shared code path once is judged sufficient, AC-3 must
say so explicitly and state why instantiating only one of the two suffices — as written, it reads
ambiguously and the narrower reading leaves an entire repository class's skip-list behavior
unverified, on exactly the healthy-vault case round 3 already flagged as the larger of the two
exposures found that round.

### What I attacked and found clean

- AC-1's four-path derivation on both halves: re-verified live in `writer.py:222-324` —
  `update_frontmatter_field` (222-260), `update_frontmatter_fields` (263-299), `roundtrip_file`
  (302-324) all still run the identical `parse_frontmatter → rebuild → write` shape with no change
  since the round-2 fold; `update_fields` (base.py:278-356) unchanged. No regression.
- AC-2's five-return-site coverage of `parse_frontmatter` (parser.py:64-80) and the
  known-vs-unknown-type distinction in `parse_to_model` (parser.py:108-150): re-read live, both
  unchanged and still total over each function's own branch structure.
- AC-3's newly-added three-fixture requirement and its ownership-evidence reasoning: verified the
  underlying claim about `Person`'s validation-failure surface against `models.py:31-90` directly
  rather than trusting the doc's restatement — correct. Also re-verified `meeting.py:75` and
  `book.py:70` already read `frontmatter.get("type")` ahead of model construction (the mechanism
  AC-3 requires `base.py` to adopt); `base.py:171-183` still has no such check, as the doc
  describes.
- AC-4's malformed-YAML-existing-file fixture requirement: re-verified live at
  `writer.py:184-195`, unchanged, still names the coupling case explicitly.
- AC-5's five-site fence-split derivation and the no-op/raise split: unchanged since round 3's
  fold; not re-litigated here as no new code or AC text touches it.
- AC-6's single narrowed except clause: unchanged, scope still limited to `person.py:1147-1160`.
- No new mutually-unsatisfiable pair introduced by this fold.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-24
model: claude-sonnet-5
note: Round-4 fold's fixture (b)/(c) collision is cleanly resolved (three distinct fixtures now required, ownership pinned to raw type read prior to model construction, verified against models.py directly). New MATERIAL finding: AC-3's repository-sweep sentence collapses PersonRepository and CompanyRepository into one sweep entry since both share base._load_file, so no fixture, direction, or Example of done in the doc ever independently exercises CompanyRepository's own skip-list — round 3's own "every person note becomes a skipped company" exposure ships unverified — still not signable.
```

## AC Red-Team — 2026-07-24 (re-verify 5)

Re-spawned to verify the fold that followed the round-5 re-verify above (recorded in Exploration
Notes as "Decorrelated AC red-team, round 5"). Read Intent → Examples of done → Problem/Motivation
→ Exploration → Approach → the current ACs (AC-1..AC-6), per Step 2, then re-read the prior
fence's one finding against the current draft. Every code claim below re-read live against the
current tree: `obsidian_schemas/repositories/base.py`, `repositories/company.py`,
`repositories/book.py`, `repositories/meeting.py`, `obsidian_schemas/models.py`.

### What the fold changed, and what it fixed cleanly

- **MATERIAL (AC-3's repository sweep collapsed `PersonRepository`/`CompanyRepository` into one
  entry; `CompanyRepository`'s own skip-list was never independently exercised)** — RESOLVED. AC-3
  now sweeps "the FOUR subclasses of BaseRepository," requires `PersonRepository` and
  `CompanyRepository` to be "independently instantiated against the SAME shared `@*.md`-globbed
  heterogeneous vault and each asserted in all three directions," derives `CompanyRepository`'s own
  fixture (b) (`@Broken Corp.md`, `type: company`, `tags: company` instead of `tags: [company]`,
  from the inherited `tags: List[str]` since `Company` declares no `List` field of its own) and (c)
  (`@Sarah.md`, `type: person`, must NOT appear), and explicitly rules out a test parametrized over
  `{PersonRepository, MeetingRepository, BookRepository}` as insufficient. Re-verified live:
  `company.py` (read in full) still defines no `_load_file`, no `file_pattern`, no ownership check —
  confirming the shared-code-path exposure the fold now covers is real — and `models.py:127-132`
  confirms `Company`'s own fields are all `str`, so the fold's derivation of fixture (b) from the
  inherited `tags` field is accurate, not just asserted.

### MATERIAL — AC-3 names "the four repository classes" but only derives worked fixtures for two of them; `MeetingRepository` gets no fixture at all, and `BookRepository` gets only its exclusion direction

AC-3's text requires, verbatim: "For each of the four repository classes, separately instantiated: every other note still loads, the load does not abort, a WARNING (not DEBUG) is emitted, and the queryable count/list that repository exposes contains EXACTLY the bad notes it owns — asserted in ALL THREE directions," and "EACH repository class in the sweep gets its own (b) and (c), derived from that class's own `type_name` and its own model's field declarations rather than transposed by hand." But grepping AC-3's own fence for `MeetingRepository` (confirmed live: appears exactly twice) finds it named only in the four-class enumeration and in the negative example of an *insufficient* test (`{PersonRepository, MeetingRepository, BookRepository}`) — nowhere in AC-3 is a fixture (b), a fixture (c), or a single one of the "three directions" ever worked out for `MeetingRepository`. `BookRepository` fares only slightly better: it gets one explicit clause (the malformed-note-of-another-type-must-not-count-as-a-skipped-book carve-out — the "Foreign-and-absent"-adjacent case for an *unreadable* type), but its own fixture (b) — a well-formed `type: book` note that fails `Book.model_validate` on a different field — is never constructed, unlike `CompanyRepository`'s explicitly-derived `tags: company` fixture.

This matters specifically because fixture (b) is the direction that exercises the *new* mechanism this item introduces (AC-2's fix making `parse_to_model` loud on a known-type validation failure) through each repository's *own*, structurally-different `_load_file`. `meeting.py:64-83` and `book.py:57-79` are not `base._load_file` — both already read the raw `type` field via a direct `parse_frontmatter` call *before* invoking `parse_markdown_file` (`meeting.py:72-75`, `book.py:67-70`, both re-read live), so a well-formed foreign-typed note is excluded today without ever reaching model construction (their "Foreign-and-absent" direction is structurally sound already, unlike `base._load_file`'s `isinstance`-after-construction check that motivated the round-4/5 folds). But a fixture with the *right* `type` and a *drifted* field — `type: book` with `tags: book`; `type: meeting` with `attendees: "not-a-list"` (`Meeting.attendees`/`topics` are `List[str]`, `models.py:261-262`, confirmed live, so unlike `Book`, `Meeting` has its own List field to derive from, not just the inherited `tags`) — passes each repository's raw-type prefilter and only fails *after* `parse_markdown_file` is called, landing in the exact same bare `except Exception` (`book.py:77-78`, `meeting.py:81-83`, both re-read live) that today swallows malformed YAML to DEBUG and that AC-3 requires to become a WARNING-plus-skip-list-entry.

**Concrete failure scenario:** critically, `BaseRepository.load()`'s for-loop (`base.py:157-165`, re-read live) calls `entity = self._load_file(file_path)` with **no `try`/`except` at all around the call** — `_load_file`'s own internal `except` is the *only* thing standing between one bad file and an aborted batch. A builder implementing AC-2's fix introduces a typed exception (say, raised inside `parse_to_model` for a known-type validation failure) and, reasonably, narrows `book.py`'s and `meeting.py`'s outer `except Exception` to something tighter — e.g. catching only the new parse-level error type, on the theory that AC-6 already establishes "narrow the except, don't just re-log" as this item's house style for `person.py:1147-1160`. If that narrower catch doesn't happen to cover whatever exception a Pydantic `ValidationError` surfaces as post-fix, a single `type: book` note with `tags: book` (or a single `type: meeting` note with `attendees: "not-a-list"`) now raises **uncaught** out of `_load_file`, straight through `load()`'s bare for-loop, aborting the *entire* `BookRepository`/`MeetingRepository` load — the exact "must not abort on one bad note" C4/HAL9000-startup regression this item exists to prevent (Constraints: "HAL9000's batch load is the hardest constraint... Any AC that asserts 'raise on malformed' must scope the raise to write/mutate paths, or it breaks startup"). AC-1 through AC-6 as currently worded would not catch this: AC-2 only asserts on `parse_to_model`'s return/raise behavior in isolation, and AC-3 — the AC that exists precisely to prove the parser-level signal survives into a repository's public, non-aborting skip-list — never constructs the one fixture (own-type-but-drifted) that would exercise `book.py`'s or `meeting.py`'s except clause under the new failure mode. This is the identical shape re-verify 3 named for `PersonRepository` ("AC-2 alone does not reach" the repository-level integration) and re-verify 4 named for `CompanyRepository` (the class sharing a code path never independently exercised) — recurring now for the two classes whose `_load_file` is neither `base`'s nor previously audited for this specific direction.

**What would have to change:** derive and require `MeetingRepository`'s own fixture (b) (e.g. `type: meeting`, `attendees: "not-a-list"`) and (c) (a well-formed non-meeting note under the `Meeting *.md`-globbed vault, or note that `Meeting *.md`'s naming convention already makes stray foreign-typed files rare — state the reasoning rather than omitting the class entirely), and require `BookRepository`'s own fixture (b) (`type: book`, `tags: book`) — each asserted, like `CompanyRepository`'s, to survive into that repository's own skip-list AND not abort that repository's `load()`. Without it, the AC set proves the new exception path is safely caught for two of the four classes it claims to sweep and leaves the other two — including the one repository (`Book`) already flagged as structurally the odd one out — resting on an untested except clause.

### What I attacked and found clean

- AC-1's four-path derivation on both halves: re-verified live in `writer.py:222-324` and
  `base.py:278-356` — unchanged since the round-2/4 folds, no regression.
- AC-2's five-return-site coverage of `parse_frontmatter` (`parser.py:64-80`) and the
  known-vs-unknown-type distinction in `parse_to_model` (`parser.py:108-150`): re-read live, both
  unchanged and still total over each function's own branch structure.
- AC-3's `PersonRepository`/`CompanyRepository` independent-instantiation requirement and
  `CompanyRepository`'s own derived (b)/(c) fixtures: the fold this round verifies — see above.
- AC-4's malformed-YAML-existing-file fixture requirement: re-verified live at `writer.py:184-195`,
  unchanged, still names the coupling case explicitly.
- AC-5's five-site fence-split derivation across all four `person.py` siblings
  (`person.py:1558-1570, 1675-1683, 1734-1742, 1801-1809`) plus `_get_body_content`
  (`person.py:1622-1626`) on the surface side: re-read live, unchanged, still complete.
- AC-6's single narrowed except clause: re-verified live, `person.py:1147-1160` is still the pre-fix
  bare `except Exception: logger.debug(...)`, as expected pre-build; scope still limited to that one
  clause, no class-quantification exposure.
- No new mutually-unsatisfiable pair introduced by this fold.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-24
model: claude-sonnet-5
note: Round-5 fold's PersonRepository/CompanyRepository split is cleanly resolved (independent instantiation required, CompanyRepository's own (b)/(c) fixtures derived and verified against models.py). New MATERIAL finding: AC-3 names "four repository classes" but derives worked (b)/(c) fixtures for only two — MeetingRepository gets no fixture anywhere in the fence, BookRepository gets only its exclusion direction — leaving the one new failure mode this item introduces (a schema-drift exception hitting book.py's/meeting.py's own except clause) unverified on two of four classes, with base.load()'s uninsulated for-loop meaning an uncaught miss there aborts the whole batch — still not signable.
```
