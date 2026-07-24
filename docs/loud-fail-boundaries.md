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
- **`load()`'s batch loop has no insulation of its own — each `_load_file`'s `except` is the entire safety margin.** `BaseRepository.load()` (base.py:157-165) calls `entity = self._load_file(file_path)` with **no `try`/`except` around the call**; the three `_load_file` implementations' own `except Exception` (base.py:181-183, meeting.py:81-83, book.py:77-79) are the only thing between one bad note and an aborted batch. This matters because the item asks builders to make failures loud *and* (AC-6) to narrow bare excepts rather than re-log them: narrowing meeting.py's or book.py's clause to a type that misses whatever the new validation failure surfaces as converts "one note skipped" into "the whole repository failed to load." Any AC touching those clauses must assert the no-abort property **per class**, not infer it from the base path passing — see the round-6 red-team subsection and AC-3.
- **N4 is a return-contract change — the one place backward-compat bites.** Callers today branch on `if not repo.append_to_body_section(...)`. Turning the failure `False` into a raise changes control flow for existing consumers (HAL9000 enricher, introducer, scheduler). N4 is not the only externally-visible change — the parse seam's new loudness also cascades to the public parse surface (`parse_markdown_file`, `parse_markdown_content`, the four typed conveniences), which post-fix PROPAGATES the typed error rather than swallowing it (AC-2's invocation-surface clause; corrected per the round-14 finding) — but N4 is the only *return-contract* change at an existing consumer branch point; the spec must decide raise-vs-distinguishable-return with the three consumers' call sites in view, and it is why N4 may warrant its own AC and its own consumer audit.

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

Both are now covered because AC-1 and AC-3 derive their sweeps from the package (callers of `parse_frontmatter` that re-serialize and write; overrides of `_load_file`) rather than naming a list — so a fifth write path or a fourth repository joins automatically. *(Two later corrections to this sentence, recorded here so it is not read as still-current: round 5 replaced the `_load_file`-override sweep with one over the four repository **classes**; and round 12 found that "joins automatically" was a property of this prose and of no check — AC-1's and AC-3's sweeps were derived once, by a human, and frozen into the test. It is true as of round 12, which requires both derivations be executed by the test at test time.)*

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

### Decorrelated AC red-team, round 6 (2026-07-24) — what it changed

The round-6 pass (verbatim in `## AC Red-Team — 2026-07-24 (re-verify 5)` below) confirmed the round-5 fold and found one MATERIAL gap: **AC-3 swept four repository classes but worked fixtures for only two of them.** `MeetingRepository` appeared in the fence exactly twice — once in the four-class enumeration, once inside a *counter*-example of an insufficient test — with no fixture (b), no fixture (c), and not one of the three directions ever stated. `BookRepository` had only its exclusion clause. Every claim below re-read live.

**Why those two looked already-covered, and why that reading was half right.** `meeting._load_file` (meeting.py:64-83) and `book._load_file` (book.py:57-79) are not `base._load_file`. Both read the raw `type` themselves — a direct `parse_frontmatter` at meeting.py:72 / book.py:67, then `frontmatter.get("type") != "meeting"` / `!= "book"` at meeting.py:75 / book.py:70 — **before** calling `parse_markdown_file` (meeting.py:78, book.py:74). So their *foreign-type* direction already is, structurally, the thing rounds 4 and 5 spent two folds forcing into `base._load_file`: ownership decided on the raw `type` value, prior to and independent of model construction. That is genuinely covered, and it is why the two classes read as safe. The direction that was missing is the other one — and it is the one this item creates.

**The missing direction is the new failure mode itself.** A note with the *right* `type` and a *drifted* field passes the raw-type prefilter, reaches `parse_markdown_file`, and fails inside `model_validate`. Derived per class rather than transposed:

- `MeetingRepository` — `type: meeting` with `attendees: "not-a-list"`. `Meeting` has its own `List[str]` fields to drift (`attendees`, `topics`, models.py:261-262), so the fixture comes from the class's own declaration.
- `BookRepository` — `type: book` with `tags: book` instead of `tags: [book]`. `Book` declares **no** `List` field of its own — every field at models.py:159-170 is `str` — so the derivation is the inherited `BaseEntity.tags` (models.py:40), exactly the move `CompanyRepository`'s fixture needed in round 5, reached independently from `Book`'s own field list rather than copied from `Company`'s.

Today both are swallowed to DEBUG by each class's **own** bare `except Exception` (meeting.py:81-83, book.py:77-79). Post-AC-2 they arrive at those same two clauses as a loud typed failure — the clauses AC-3 requires to become WARNING-plus-skip-list-entry, and which no fixture in the set had ever reached.

**Why an untested except clause is worse here than anywhere else in this item: the batch loop has no insulation of its own.** `BaseRepository.load()` (base.py:157-165) calls `entity = self._load_file(file_path)` with **no `try`/`except` around the call**. Each `_load_file`'s internal `except` is the entire safety margin between one bad note and an aborted load — there is no second net. AC-6 makes "narrow the except clause, don't merely re-log" this item's house style, so a builder narrowing meeting.py's and book.py's bare `except Exception` to the new typed error is following the item's own grain; and if that narrowed catch misses whatever a Pydantic validation failure surfaces as post-fix, a single drifted note aborts the entire `MeetingRepository`/`BookRepository` load. That is the HAL9000-startup regression Constraints names as the hardest one, reached by a change this item asks for. So the no-abort property has to be **asserted per class**, not inferred from the base path passing.

**The matrix is not uniform — which is precisely why it has to be written out rather than parametrized over a shared expectation table.** The four-bucket ownership taxonomy gives `BookRepository` the *opposite* answer to the other three on fixture (a): a malformed note under `@*.md` or `Meeting *.md` is owned-by-convention and MUST be listed (the C4 keystone), while a malformed note under `BookRepository`'s catch-all `*.md` (book.py:49-51) has no ownership evidence of either kind and MUST NOT be. A test written as `for cls in (Person, Company, Meeting, Book): assert malformed in repo.skipped` is wrong for one of its four members — and wrong in the direction that turns the skip signal into vault-wide noise. Fixture (b), by contrast, is MUST-be-listed for all four, including `BookRepository`: with `type: book` readable, the catch-all glob is irrelevant, because ownership is read off the raw `type`, not the glob. Stating both keeps a builder from "solving" the book glob by suppressing everything `BookRepository` cannot type-confirm — which would drop the one book fixture that matters.

**What changed.** AC-3 is restated as the complete derived 4×3 matrix: one worked fixture set per class, each derived from that class's own `type_name`, its own model's field declarations, and its own `_load_file` structure — twelve cells, plus a NO-ABORT assertion on every one of them (the failure is caught inside that class's own `_load_file` and never reaches `load()`'s bare for-loop). Constraints gains a bullet recording the uninsulated loop; the Approach carries the per-class (b) requirement and the no-abort property; an eighth Example of done pins the meeting and book cases in Dave's terms.

This is the third consecutive round in which the *class* an AC quantified over was correct and the *members* were not — `PersonRepository` alone (round 4), then `Person`+`Company` (round 5), now `Person`+`Company`+two-thirds of the rest. The rule that falls out, alongside the four already standing: **when a sweep's members do not all have the same answer, the AC writes each member out — a quantifier with one shared expectation table silently asserts uniformity that was never checked.** And its companion, which is what the no-abort clause encodes: **prove the insulation, not only what the insulation produces** — a per-class `except` is a per-class safety property, and here it is the only one there is.

### Decorrelated AC red-team, round 7 (2026-07-24) — what it changed

The round-7 pass (verbatim in `## AC Red-Team — 2026-07-24 (re-verify 6)` below) confirmed the round-6 fold — the complete 4×3 matrix verified clean against meeting.py/book.py/models.py — and found one MATERIAL gap on a *different* AC: AC-5 derived its falsy-site sweep from exactly two predicates, and `append_to_timeline` (person.py:1444-1502) collapses a third, un-derived predicate into the same `False`. Per the standing audit-fold discipline (Dave-ruled, as in round 6), the conductor did not patch the found site alone: the whole falsy-return classification was re-derived from scratch at source, over every write path and section-read helper in the package. Every claim below re-read live.

**The found member, worked out.** `append_to_timeline` returns `False` from four distinct conditions: (i) dedup-key match (1476-1478 — a legitimate no-op), (ii) `## Timeline` marker absent (1482-1484), (iii) the `len(parts) != 2` guard (1491-1492 — structurally dead: the marker was confirmed present two lines up, so `split(timeline_marker, 1)` always yields exactly two parts; a dead guard is still a silent third door and is classified, not ignored), and (iv) its P1 blanket except (1500-1502). The package's own person template guarantees `## Timeline` (`ENTITY_BODY_CONFIG["person"]`, body_sections.py:305-306, written by `create_stub` via `get_default_body`, person.py:1440) — so on any note this package created, marker-absent is corruption, and the caller's entry is silently discarded into the very `False` that means "already there, skipped on purpose." That is N4's data-loss shape exactly. The deriving predicate (P3): *a writer that inserts caller-supplied content at a named section marker and returns falsy when the marker is absent.* Run over the package it yields exactly this one member — `append_to_body_section` governs absence explicitly via `create_if_missing`, and the To-Discuss match-mutation writers drop no payload (below).

**What the full re-derivation found beyond the finding (two more gaps).** First: writer.py's existence pre-checks — `update_frontmatter_field` returns `False` at writer.py:242-243 and `update_frontmatter_fields` at 281-282 when the target file does not exist, the same condition person.py's five writers raise `ValueError` for (e.g. 1469-1470) and `base.update_fields` raises `FileNotFoundError` for (base.py:305-308). A failure reported as a no-op, in AC-5's own words — and a package-internal inconsistency both prior passes read past because neither predicate reached it (the sites sit *before* the `try`, so P1 never saw them, and there is no fence split). Predicate P4: *an existence pre-check in a writer returning falsy where the package's sibling writers raise for the same condition.* Second: the no-op half's citation list was itself wrong in both directions — it labeled `update_to_discuss_item`'s SECTION-absent site (1746-1747) as "item text not found," and omitted `remove_to_discuss_item`'s section-absent site (1813-1814) entirely. The no-op half is now derived by predicate like the raise half.

**Why the To-Discuss section-absent sites stay no-ops while Timeline's moves off the no-op side.** *(Round 7 wrote "moves to the raise side"; round 9's Dave ruling changed the disposition to ACCOMMODATE — the reasoning below for why the To-Discuss sites stay no-ops is unaffected and still governs, only Timeline's remedy changed.)* The person template guarantees `## To Discuss` too, so the naive reading says treat them alike. The dividing predicate is whether the falsy return leaves caller-supplied content unwritten. `update_to_discuss_item`/`remove_to_discuss_item` are *match-mutation* writers: the caller names an existing item; section-absent means the item is not there, which is the same answer as item-not-found — degraded state, but no payload dropped by the call, and the return is truthful ("nothing matched"). `append_to_timeline` is an *insertion* writer: the caller hands over new content, and marker-absent silently discards it — the data loss happens BY the call. One is an answer; the other is a swallowed write. (The fence-corruption route into all of these is already P2's, handled separately and loudly.)

**What changed.** AC-5 restated as a FOUR-predicate derivation, both halves derived (raise side: P1 blanket-except, P2 fence-split, P3 guaranteed-section insertion, P4 existence pre-check; no-op side: dedup, governed absence, match-not-found). The Approach carries the four-predicate sweep; a tenth Example of done pins the dropped-timeline-entry case in Dave's terms; and a check-strategy note applies Dave's 2026-07-23 property-testing ruling (Hypothesis for the input-quantified ACs; AC-3's non-uniform matrix stays explicit). The rule that falls out: **when a round shows a derivation's predicate list incomplete, re-run the whole derivation at source and fold once — the found member is a symptom, and patching it alone is the treadmill.**

### Round-8 audit-fold (2026-07-24) — the round-7 derivation re-verified at source, and closed

Every claim the round-7 fold makes was re-read live against the current tree, and all of them hold:
`append_to_timeline`'s four falsy returns (person.py:1476-1478 dedup, 1482-1484 marker-absent,
1491-1492 split guard — confirmed structurally dead, since `split(marker, 1)` on a string just
verified to contain the marker always yields exactly two parts, and 1500-1502 blanket except);
`ENTITY_BODY_CONFIG["person"]["default_body"] == "## To Discuss\n\n## Timeline\n\n## Notes\n"`
(body_sections.py:305-306) written unconditionally by `create_stub` (person.py:1440); writer.py's
existence pre-checks at 242-243 and 281-282 against the five `ValueError` raises in person.py
(1469-1470, 1551-1552, 1668-1669, 1727-1728, 1794-1795) and `base.update_fields`' `ValueError` /
`FileNotFoundError` (base.py:304-308); and the corrected no-op citations (`update_to_discuss_item`
section-absent at 1746-1747, `remove_to_discuss_item` section-absent at 1813-1814). No regression,
no mis-citation.

**What the re-derivation found that round 7 did not state: the predicate list is asserted total, not
proven total.** Rounds 2, 3, 5, 6 and 7 each ended the same way — the *class* an AC quantified over
was right and its *members* were incomplete — and AC-5's answer each time was to add the predicate
the round found. Four predicates is the count as of this round; nothing in the AC tells a builder
whether it is the whole count. That is the treadmill the round-7 rule names, one level up: patching
the predicate *list* is the same move as patching the found *member*.

The closure is cheap here because the universe is small and enumerable. Swept live over the whole
package, the complete set of return sites in write paths and shared section-read helpers that do not
report a completed write is **28** — writer.py 243, 260, 282, 299, and person.py 1478, 1484, 1492,
1502, 1563, 1570, 1579, 1584, 1607, 1617, 1626, 1681, 1683, 1704, 1740, 1742, 1747, 1761, 1777,
1807, 1809, 1814, 1824, 1839 — and nothing else: `company.py`, `meeting.py` and `book.py` declare no
bool-returning writer at all (no `return False` anywhere in any of the three), so `append_to_timeline`
really is P3's only member, by enumeration rather than by inspection. Classifying all 28 against the
round-7 predicates leaves exactly one residue: `_get_body_content`'s missing-file `None`
(person.py:1616-1617), which is neither a raise-side predicate nor any of the three no-op classes —
its sole caller, `get_to_discuss_items`, already converts it to a `ValueError` (person.py:1641-1643),
so it is a fourth no-op class ("a helper's falsy return that its only caller already makes loud"),
not a gap. Naming it is what lets the count come out even.

**What changed.** AC-5 gains no-op class (d) and a **CLOSURE** clause: the test enumerates the 28-site
universe and asserts every member falls into exactly one of P1-P4 or (a)-(d), with a site matching
none of the eight failing the criterion. The out-of-universe returns are named explicitly too — pure
predicates (`phones_match`, person.py:136,156) and lookup-miss `None`s (person.py 429/441/498/530/
1012/1065; company.py 114/134; meeting.py 357/387; book.py 243/269) — so the scope boundary is
stated rather than assumed: a lookup miss is an answer to a question, not an unreported write. The
rule that falls out, and the last one this AC needs: **a derived sweep is finished when its universe
is enumerated and every member is classified — until then "derived by N predicates" is still a
sample, just a principled one.** The next un-derived predicate now arrives as a red test rather than
as another red-team round.

### Decorrelated AC red-team, round 9 (2026-07-24) — what it changed

Round 9 (verbatim in the fence below the round-8 pass) confirmed the round-7/8 fold whole — the 28-site universe independently re-derived from source and matched exactly — and raised the arc's first *design* finding: P3's raise remedy rested on a premise ("this note was created by our template") that the runtime check cannot confirm, and would convert a legitimately Timeline-less note — hand-created in Obsidian, or predating the convention — into an uncaught exception through HAL9000's exocortex meeting sync, the function's own named primary consumer. The gate offered two remedies; **Dave ruled (a): accommodate.** `append_to_timeline` auto-creates the `## Timeline` section on insert, mirroring the `create_if_missing=True` default its sibling `append_to_body_section` already has for the identical ambiguity. This is strictly stronger against the original defect (N4 silent data loss): the caller's entry can no longer be dropped *at all* — not by corruption, not by structural absence — and no new failure mode is invented. Dedup keeps its exact current `False`. AC-5's P3 disposition, the Approach clause, the CLOSURE bucket naming, and the Example of done are restated accordingly; nothing else in the fold moved.

### Round-10 audit-fold (2026-07-24) — the accommodation inherits the sibling's implementation, so the sibling had to be read, not cited

Per the standing audit-fold discipline, the round-9 ruling was not recorded and left there: the remedy Dave chose — "mirror `append_to_body_section`'s `create_if_missing=True`" — was re-derived at source by reading what that sibling actually *does* on an absent section, rather than trusting the round-9 fold's (and the gate's) description of it. It does something the accommodation cannot afford unqualified, and every claim below was read live.

**The sibling's absent-section path round-trips the whole body through a section parser that discards everything it cannot name.** `append_to_body_section` with `create_if_missing=True` calls `append_to_section` / `prepend_to_section` (person.py:1586-1593), which are `parse_body_sections(body)` → mutate the dict → `write_body_sections(sections)` (body_sections.py:241-252, 209-220). `parse_body_sections` (body_sections.py:74-97) begins its first section at the first `^## ` match and keeps **only** heading-delimited spans; `write_body_sections` (100-134) rebuilds the body from that dict alone. Two consequences, both verified by reading the two functions against each other:

1. **Body text above the first `## ` heading is deleted.** A body of `Some intro line\n\n## Notes\nfoo\n` parses to `{"Notes": "foo\n"}` — the intro line is in no section — and writes back as `## Notes\nfoo\n\n## Timeline\n<entry>\n`. The preamble is gone.
2. **A body with no `## ` heading at all is destroyed entirely.** `parse_body_sections` returns an empty `OrderedDict` (body_sections.py:76-78), `create_if_missing` sets the single new key (217-218 / 249-250), and `write_body_sections` returns `## Timeline\n<entry>\n` — the original body replaced wholesale.

**Why that lands precisely on the note class the accommodation exists to serve.** Round 9's whole point is the note that legitimately never had a `## Timeline` heading — "hand-created directly in Obsidian… imported from elsewhere… predating the convention." That is exactly the note least likely to be `## `-sectioned at all, and most likely to carry free text above its first heading. So the naive mirror of the sibling converts round 9's "the entry always lands" into a *new* body-wipe on the one input the ruling was written to protect — trading a silent dropped entry for a silent dropped note body, which is strictly worse.

**And this write path is guard-exempt by design, so nothing downstream catches it.** `append_to_timeline` writes with a raw `file_path.write_text` (person.py:1495), as does `append_to_body_section` (person.py:1597); neither goes through `write_markdown_file`, and writer.py:178-183 says so in as many words — "Body-preserving paths (update_fields, the section writers) do their own read+write and never reach here, so they are guard-exempt." The WI-126 body-shrink guard that AC-4 is hardening (writer.py:184-195) never runs on this path. The exemption is sound for the section writers *as they behave today* (they carry the untouched body through by string surgery); it stops being sound the moment a section writer starts rebuilding the body from a lossy parse.

**So the accommodation is kept and given its preservation property.** Dave's ruling stands unchanged — auto-create and insert, no raise, dedup frozen. What round 10 adds is the property that makes it safe: the auto-create must leave every pre-existing byte of the body present, the frontmatter byte-identical, and must be asserted on the two bodies that break the naive implementation (heading-less, and preamble-above-first-heading). Whether the implementation reaches that by string insertion (`append_to_timeline`'s existing shape, extended) or by making the `body_sections` round-trip lossless is the spec-writer's call; the AC pins only that content cannot vanish. Note this also puts a floor under the sibling: an implementation that fixes `parse_body_sections`/`write_body_sections` to be content-preserving repairs `append_to_body_section`'s identical latent wipe at the same time — the "solve in one place" answer, and the reason the property is stated over the *behaviour* rather than over `append_to_timeline`'s code.

**One correction the same read forced: "the drop is impossible" was an overclaim.** Round 9's fold and the tenth Example of done both said the entry can no longer be dropped *at all*. It can: dedup (no-op class (a)) is whole-file, not section-scoped — `deduplicate_key in content` at person.py:1476 tests the entire file, and person.py:1521-1524 records that as deliberate ("Deliberately distinct from `append_to_timeline` (which prepends and dedups whole-file)… so e.g. 'Introduced by [[X]]' may legitimately appear in both Timeline and Notes"). So an entry whose key already appears in `## Notes` returns `False` and never reaches the Timeline — on a Timeline-less note, the section is not created either. That behaviour is **frozen on purpose** by AC-5's no-op half (changing it would break the backward-compat property this item is built on), so it is not a defect to fix here; it is a claim to state accurately. The corrected claim: *structural* absence can no longer drop the entry, and dedup is the only remaining falsy path, deliberately unchanged.

The rule that falls out: **when a fold converges on a sibling's semantics, it inherits the sibling's implementation — read the sibling, don't cite it.** "Mirror what X already does" is a name-level argument of exactly the shape the WI-123 REMOVE-audit rule forbids; the sibling's *predicate* here (round-trip through a lossy section parser) is not what its *contract* ("creates the section if missing") advertises.

### Decorrelated AC red-team, round 10 → fold 11 (2026-07-24) — what it changed

Round 10 (fence below) confirmed the round-9/10 accommodate-with-preservation fold whole — re-verified live that the sibling's `body_sections` round-trip is exactly as lossy as claimed and that the PRESERVATION clause forecloses it — and found the arc's last structural gap: the CLOSURE clause and AC-1's sweep language *promised ongoing* completeness while their checks only required completeness *as of build time*. The concrete failure: both tests ship green as faithful implementations; a later work item copy-pastes a sixth match-mutation writer into person.py with the same fence-split `False`-collapse; nothing re-derives; the new silent `False` ships as invisibly as the original five findings this arc caught by hand-reading. Dave ruled remedy (a) on a one-line single-gap ask: **the test performs the derivation, live, at test time** — an AST/inspect scan of the swept surface, an explicit in-test classification map, and any unclassified site is a red test. Both AC-1 and AC-5 restated; frozen name/line lists explicitly do not satisfy either. Nothing else moved.

### Round-12 audit-fold (2026-07-24) — round 11's remedy re-derived at source: a live scan is a predicate plus a proven negative, and two more ACs carried the same overclaim

Per the standing audit-fold discipline, round 11's ruling was not recorded and left there. The clause it added — "the test performs the derivation, live" — was re-derived at source two ways: by running AC-1's own scan predicate against the current tree to see what it actually returns, and by re-running the *shape* of the gate's finding (a completeness claim whose check only guarantees completeness as of build time) over the whole AC set rather than over the two ACs the gate happened to name. Both halves found something. Every claim below read live.

**The scan AC-1 specified returns five functions, not four — and the fifth was excluded by name.** AC-1's predicate as round 11 wrote it is "callers of `parse_frontmatter` that subsequently write." Run literally over the package that yields `update_fields` (parse base.py:312, write 329), `update_frontmatter_field` (247, 256), `update_frontmatter_fields` (286, 295), `roundtrip_file` (317, 322) — **and `write_markdown_file`** (parse writer.py:186, write 217), which AC-1 does not name and must not sweep: its own malformed-existing-file behaviour is AC-4's, and it is the guard AC-4 hardens. A builder implementing the stated predicate gets five, sees the AC names four, and drops the fifth by name. That is the frozen hand-curation round 11 existed to abolish, reintroduced one level down — inside the scan itself.

**What separates them is data flow, and it is readable in the source.** Each of the four sweep members feeds the dict `parse_frontmatter` returned back through `write_frontmatter` and into the bytes it writes (base.py:312 → 324 → 327-329; writer.py:247 → 250 → 253-256, 286 → 289 → 292-295, 317 → 319-322). `write_markdown_file` discards it: `_, existing_body = parse_frontmatter(...)` (writer.py:186) keeps only the body, and only to compute the shrink guard, while the frontmatter it writes is built independently from its own `entity`/`frontmatter` arguments (writer.py:197-205). So the discriminating predicate is not "parses, then writes" but **"the parsed frontmatter is re-serialized into what gets written"** — which is also exactly the predicate the corruption chain runs on, since C2's damage *is* the emptied parse becoming the file's new frontmatter.

**And a scan is only as trustworthy as its ability to exclude.** A scan asserted only against the members it returns is indistinguishable from a function that returns those four names. The negative is what proves it discriminates. So AC-1 now requires `write_markdown_file` be **reached by the scan's traversal and rejected by the scan's predicate**, asserted in the same test — a proven negative, not an omission. That is round 4's rule ("two cases that share a code path but require opposite answers must be two fixtures, asserted in one test") applied to the derivation instead of to the fixtures.

**Re-running the finding's shape over the AC set: two more ACs claim a completeness their checks never re-derive.** Round 11 fixed AC-1 and AC-5. The gate's own generalization — if an AC promises future instances join the sweep, the check must run the derivation rather than remember its output — fires unrepaired on two others:

- **AC-3.** The Exploration Notes have said since round 1 that AC-1 and AC-3 derive their sweeps "so a fifth write path **or a fourth repository** joins automatically." AC-3 is a hand-written 4×3 matrix and nothing in it discovers a fifth `BaseRepository` subclass. It is discoverable: `BaseRepository` is an ABC whose `entity_type` and `type_name` are `@abstractmethod` (base.py:120-130), so concreteness is decidable at runtime. Round 6's ruling is untouched — the twelve **cells** stay explicit because their answers are non-uniform — and deriving the **class list** is precisely what stops that explicit map going stale: the map is keyed by class, the scan supplies the keys, an unmapped key fails. A fifth repository arrives as a red test that forces whoever adds it to state its three answers.
- **AC-2.** "One case per return site" of `parse_frontmatter` (five today) and per outcome of `parse_to_model` is a completeness claim over code sites — and this item's own fix **changes that site list**, since the malformed branch no longer returning `({}, content)` is the whole point. A five-case test frozen at build time reads green against a six-return-site post-fix function. Same clause, same cost.

**One tightening round 11's own clause needs in order to be implementable.** AC-5 requires "an explicit in-test classification map (site → P1..P4/(a)-(d))" and rightly forbids hardcoding the 28 line numbers — but never says what a *site* is keyed by. Line numbers are the obvious key and the fix itself shifts every one of them in `person.py`, so a line-keyed map turns unrelated edits red; a function name alone is too coarse, since `append_to_timeline` holds four sites across three different buckets. The key has to be a source-stable identity: module, qualified function, and the site's ordinal within that function.

The rule that falls out, and the last rung this ladder needed: **a live derivation is a predicate plus a proven negative — a scan that only ever confirms what it returns has not been shown to discriminate — and the clause belongs to every AC that claims a class is complete, not to the ones a round happened to name.**

### Decorrelated AC red-team, round 12 → fold 13 (2026-07-24) — what it changed

Round 12 (fence below) confirmed the round-11/12 fold whole — AC-1's data-flow predicate with `write_markdown_file` as its proven negative re-verified live, AC-2/AC-5's scans accurate — and found the derivation-mechanism class's last member: AC-3's class-list scan was specified against the *import graph* (`__subclasses__()`) where its siblings scan *source*, and the import graph only answers for modules already imported — a fifth repository module not wired into `repositories/__init__.py` ships with zero AC-3 coverage and a green suite, the exact silent-gap shape, inside the discovery clause built to prevent it. Dave ruled the fold on a one-line ask; per the totality discipline the fix is the class, not the instance: **all four derived sweeps now name one uniform mechanism — AST over the package's module files on disk, the test importing what it discovers — and AC-3 explicitly rejects the runtime check.** Nothing else moved.

### Round-14 audit-fold (2026-07-24) — round 13's remedy run at source: the scans' surface was still hand-named, and AC-2's map is keyed to a site that does not exist

Per the standing audit-fold discipline, round 13's ruling was not recorded and left there. Its clause — "discovery means SOURCE, AST over the package's module files on disk, uniformly across all four sweeps" — was re-derived two ways: by *running* each of the four scans against the current tree to see what it actually returns, and by re-reading the four AC fences to check that they say what the fold's own summary claims they say. Both halves found something, and the second one found that the round-13 note is an overclaim about its own fold. Every claim below read live.

**The round-13 fold changed two ACs and claimed it changed four.** Its revision note says "ALL four derived sweeps … now state one uniform mechanism — discovery from source, AST over the package's module files on disk," and the Approach says the same. Read live, AC-3 was rewritten (AST over module files, `__subclasses__()` explicitly rejected) and AC-2 already said "an AST scan". **AC-1 and AC-5 still read "an AST *or inspect-based* scan"** — the alternative round 13's own rule forbids, because `inspect.getmembers`/`getsource` enumerate what a module object holds, and a module object exists only for a module something imported. An inspect-based sweep inherits the identical import-completeness gap `__subclasses__()` has; AST over files on disk is the only one of the two that does not. So the doc asserts a uniformity two of its four ACs do not carry — the overclaim shape rounds 10 and 12 each caught once, now in the fold that was written to close it.

**And it reads green today for an accidental reason, which is the tell.** Walked live, every one of the package's fourteen `.py` files is transitively imported by `obsidian_schemas/__init__.py` — including `name_validation.py`, which the top-level `__init__` never names and which arrives only via `repositories/person.py:22`. So an inspect-based scan would find every module in the package right now, exactly as `__subclasses__()` finds all four repositories right now because `repositories/__init__.py` eagerly imports them. Round 12 named that tell in as many words: *the mechanism works today for reasons that have nothing to do with the property the clause claims to guarantee.*

**The same finding one level down, which is what makes it a class rather than a leftover: three of the four scans still hand-write their file set.** AC-3 scans "the repository package's module files"; AC-5 scans "the swept modules" — writer.py and person.py, the two modules its own 28-site enumeration happens to live in; AC-1 says "the package" without saying what that walks. A source scan is only as complete as the file set it walks, so scoping one to a directory or a module list reproduces the frozen list precisely as an import-graph scan does — the frozen list wearing a path. Nothing requires a fifth repository to live under `repositories/`, and nothing requires a sixth To-Discuss-style writer to be pasted into `person.py` rather than into a new module beside it; adding an isolated module is the *ordinary* way to add code, and it is the same omission round 12 predicted a builder would make with `repositories/__init__.py`. **All four sweeps now walk one derived file set: every `.py` under `obsidian_schemas/`, discovered recursively on disk.** The predicate is the filter; the directory is not.

**MATERIAL, and the one a citation-check could not have caught: AC-2's map is keyed by return site and enumerates outcome classes, and the two are not in bijection.** AC-2 says "one case per return site" and lists five, citing `parser.py:64-65`, `69-70`, **`73-75`**, `77`, `78-80`. Read at source, `parse_frontmatter` (parser.py:53-80) contains **four** `return` statements — 65, 70, 77, 80. Lines 73-75 are `frontmatter = yaml.safe_load(...)` / `if frontmatter is None: frontmatter = {}`: a normalisation branch with no `return` of its own, which falls through to the site at 77 and *shares* it with the valid-frontmatter case. There are five outcome classes and four return sites. Round 9's re-verify pass recorded this list as "matching the doc's citations exactly" — which it does; what it did not do is run the scan the AC specifies against the function, and a citation check is not a scan run.

**Concrete failure scenario.** A builder implements AC-2 as written: `ast.walk` `parse_frontmatter`, collect `ast.Return` nodes, assert the discovered set equals the keys of the in-test map. The scan returns four sites; the map has five entries, one of them keyed at 73-75 matching nothing. The assertion is red **on a correct implementation**. The cheap repair — delete the entry with no matching site — is the one a builder reaches for, and it deletes the *empty-fence* case, whose entire reason for being in AC-2 is that it is a distinct outcome reached through a shared return. AC-2 then ships green having stopped requiring a case for one of the five outcomes it exists to separate. The alternative repair (map empty-fence onto site 77 alongside valid-frontmatter) is correct, and nothing in the AC asks for it or notices if a single case closes both classes at that site.

**The fix keeps both halves of what AC-2 wanted.** The map is keyed by return site (the thing the scan can return, so site-set equality stays a real completeness check over code), each site carries one *or more* named outcome classes, and the test additionally asserts every named class is exercised by at least one input — so a site carrying two classes cannot be closed with one case. Both counts are restated as baselines rather than answers: four return sites and five outcome classes today, and the fix changes both (the malformed branch stops returning `({}, content)`; the unclosed-fence case may gain a site once classified).

The rule that falls out, and the one round 13 needed to state about its own remedy: **a source scan is only as complete as the file set it walks and as honest as the key it maps to — derive the file set too, and never key a map to a construct the scan cannot return.** Its companion, unchanged from round 10 and earned again here: a fold's summary of itself is a claim about text, and the text has to be re-read, not remembered.

### Decorrelated AC red-team, round 14 → fold 15 (2026-07-24) — what it changed

Round 14 (fence below) confirmed the round-13/14 fold whole — the AST uniformity, the derived file set, AC-2's site-vs-class keying all re-derived live with zero discrepancies — and found the last uncovered surface: the seam's own *callers*. Post-fix, `parse_frontmatter` raises where it used to normalise, and that new loudness travels through `parse_markdown_content` (README-documented) and the four typed conveniences — an invocation layer that is neither an AC-1 write path nor an AC-3 loader, so no existing sweep could ever discover it. This is the **uncovered-invocation-layer class** the WI-158 arc scarred into the record, and the fold applied its proven cure: enumerate the whole invocation surface at source, classify totally. Every package caller of the seam now lands in exactly one of four named caller classes (refuse / insulate / discard / propagate), the propagating class is asserted member-by-member from the same test-time AST scan *(one correction, recorded here so this is not read as still-current: the scan that discovers that caller set was specified as direct-call adjacency, which cannot return four of the six propagating members — the round-16 audit-fold below replaces it with a transitive closure)*, the export facts are stated from source (correcting the finding's own "all package-exported" overclaim), and the falsified Constraints claim is fixed. Dave ruled the fold on a one-line ask; nothing else moved.

### Round-16 audit-fold (2026-07-24) — round 15's remedy run at source: the invocation-surface scan cannot return four of the six members it names

Per the standing audit-fold discipline, round 15's ruling was not recorded and left there. Its clause — "the test derives, at test time by AST over the package's module files on disk, EVERY caller of `parse_frontmatter` and `parse_to_model` in the package, and classifies each into exactly ONE of four caller classes" — was re-derived at source the only way that tests a scan: by *running* it against the current tree and comparing what it returns against the members AC-2's own map names. Every claim below read live (`parser.py` in full, `obsidian_schemas/__init__.py:35-39`, `README.md:138-180`, `tests/test_parser.py:1-30`, plus a package-wide grep for all eight parse symbols).

**What round 15 got right, re-verified.** The export facts are exact: `__init__` imports `parse_frontmatter`, `parse_markdown_file`, `ParsedDocument` from `parser` and nothing else (`__init__.py:35-39`), and `__all__` carries the first two (102-103). `parse_markdown_content` is README-documented at exactly the cited lines (`README.md:160` import, `176` call, under "Parsing Content Strings"). `parse_markdown_file` (parser.py:153-184) and `parse_markdown_content` (187-210) each call the seam with no `try`/`except` of their own, and the four conveniences (216-237) are two-line wrappers with none either — so the propagating *disposition* is correct for all six. The Constraints bullet's correction holds: it no longer claims N4 is the only externally-visible change.

**MATERIAL — the scan's predicate is direct-call adjacency, and four of the six propagating members are not direct callers.** Run literally, "every caller of `parse_frontmatter` and `parse_to_model` in the package" returns nine functions: `parse_markdown_file` (parser.py:174, 176), `parse_markdown_content` (201, 202), `write_markdown_file` (writer.py:186), `update_frontmatter_field` (247), `update_frontmatter_fields` (286), `roundtrip_file` (317), `update_fields` (base.py:312), `meeting._load_file` (meeting.py:72), `book._load_file` (book.py:67). **`parse_person`, `parse_company`, `parse_book` and `parse_meeting` are not among them** — they name neither seam symbol, reaching it only through `parse_markdown_content` (parser.py:218, 224, 230, 236). Nor is **`base._load_file`**, which reaches it only through `parse_markdown_file` (base.py:178). So the scan AC-2 specifies cannot return four of the six functions AC-2's propagating class enumerates, nor the loader that serves two of AC-3's four classes.

**Concrete failure scenario.** A builder implements the clause as written: `ast.walk` every `.py` under `obsidian_schemas/`, collect functions whose bodies contain a `Call` to `parse_frontmatter`/`parse_to_model`, assert the discovered set equals the classification map's keys. The scan returns nine; the map holds thirteen; the four convenience entries and `base._load_file` match nothing. The assertion is red **on a correct implementation** — and the cheap repair is the one round 14 already named: delete the entries with no matching discovered function. That deletes `parse_person`/`parse_company`/`parse_book`/`parse_meeting`, which are the *entire* reason round 14's finding was raised — the README-shaped, `None`-on-failure-contracted surface (`tests/test_parser.py:14` imports and exercises `parse_person`; 13 imports `parse_markdown_content`). The clause also says the propagating property is "asserted by invoking each DISCOVERED member," so the four are never invoked on the malformed fixture, and AC-2 ships green having stopped covering the layer it was written to cover. This is round 14's own rule — *never key a scan's map to a construct the scan cannot return* — recurring inside the remedy that rule produced, which is the shape rounds 10, 12 and 14 each caught once: a fold's summary of its own mechanism is a claim about text, and the mechanism has to be *run*, not re-read.

**The fix: an invocation surface is a transitive closure, and its stop rule is what makes it terminate.** The members are the fixpoint of "package functions that reach the seam": seed with the functions naming `parse_frontmatter`/`parse_to_model` directly, then add the callers of everything already in the set until it stops growing. The closure **stops at any function another criterion has already assigned a disposition to** — AC-1's data-flow write set, AC-3's per-class `_load_file` set, AC-4's `write_markdown_file` — because those criteria own what those functions do under the new failure, and without the stop rule the closure would climb through `load()`, `resolve()` and every consumer-facing method in the package. Computed live today it terminates in three levels and yields exactly the map AC-2 wants: level 1 the nine above (six of them terminal by the stop rule, `parse_markdown_file` and `parse_markdown_content` propagating); level 2 `base._load_file` via `parse_markdown_file` (terminal, AC-3) and the four conveniences via `parse_markdown_content` (propagating); level 3 empty, since no function in the package calls any of the four conveniences. Residue = the six propagating members, discovered rather than named. And the equality assertion has to run in **both** directions — a discovered function with no class fails, *and* a class member the closure does not discover fails — because the one-directional form is exactly what let this gap read as satisfied.

**One more correction the same read forced: a cross-repo claim this floor cannot make.** AC-2 asserted the four conveniences have "no external consumer today (verified against HAL9000 and exocortex source at fold time)." Neither repo is in this tree, the floor is hermetic, and the first fold *removed* an AC clause for precisely that reason (the CRITICAL response above; Non-goals). Stating it as verified re-imports the unverifiable check under a different AC. Restated to what source here does prove — no `__init__` export, one convenience exercised by the suite — with external-consumer status explicitly parked alongside N4's companion item.

The rule that falls out: **a caller sweep is a transitive closure, not an adjacency list — a seam's invocation surface is every function that REACHES it, and the closure is well-founded only because it stops where another criterion has already assigned a disposition.** Its companion, earned for the third time: a scan is specified correctly only when someone has run it and diffed its output against the map it is checked against.

### Decorrelated AC red-team, round 16 → fold 17 (2026-07-24) — what it changed

Round 16 (fence below) confirmed the transitive-closure correction factually sound — the six-member propagating residue independently recomputed from source, matching exactly — and found the last named set in the document: the closure's STOP SET, stated by example where everything else is derived. The fold composes the criteria: AC-2's stop set is now the union of AC-1's, AC-3's and AC-4's own live derivations consumed as computed inputs, and a partition assertion makes the four class sets cover the closure exactly-once by computation. The derivation system is now closed under its own checks — each sweep is derived from source, the file set is derived, the caller closure is derived, and the boundaries between criteria are the criteria's own outputs. Dave ruled the fold on a one-line ask; nothing else moved.

### Round-18 audit-fold (2026-07-24) — round 17's composition run instead of re-read: two of the three stop contributions are not in the closure's domain, and one of them does not exist

Per the standing audit-fold discipline, round 17's ruling was not recorded and left there. Its remedy — "the stop set is CONSUMED as the live output of AC-1's, AC-3's and AC-4's own test-time derivations" — is a claim about what three sibling criteria *produce*, so it was checked the only way that tests a composition: by reading what each sibling's `check:` actually derives, and asking whether that value can be a member of the set AC-2 subtracts it from. Every claim below read live (`repositories/base.py`, `company.py`, `person.py:159`, `meeting.py`, `book.py`, `writer.py:178-217`, plus AC-1/AC-3/AC-4's `desc:` text as committed at round 17).

**What round 17 got right, re-verified.** The direction is correct and it is the right level of the ladder: composing criteria so one consumes another's derivation *is* the only way a shared boundary stays true when either side moves, and the PARTITION assertion is a genuine new property — nothing before it checked that the four caller classes cover the closure exactly once. The refuse-vs-propagate collision it forecloses is real (round 16's failure scenario), and the "today's baseline listing, not the specification" framing correctly demotes every function name in the clause.

**MATERIAL — a set of classes cannot be subtracted from a set of functions, and AC-4 has no derivation at all.** AC-2's closure is over *functions* (AST-discovered, by module + qualified name). Of the three contributions round 17 composes:

- **AC-1's** output is a function set. Consumable as-is. Clean.
- **AC-3's** is not. Read at source, AC-3's test-time derivation "scans their AST for classes deriving (directly or transitively) from `BaseRepository` … and asserts that discovered set equals exactly the classes its matrix holds cells for" — it discovers **classes**, and its map is keyed by class. Consumed literally, AC-2's stop set receives four class keys, which match no member of a closure over functions: the intersection is empty, the closure never stops at `base._load_file`, and it climbs into `load()` → `get_all()` → `resolve()` and the whole public repository surface — the exact unbounded walk round 16 introduced the stop rule to prevent, now reachable *through* the rule. The conversion needed is not cosmetic, because the map is many-to-one: verified at source, `PersonRepository` (person.py:159) and `CompanyRepository` (company.py:46) declare no `_load_file` and both resolve to `base.py:171`, while `meeting.py:64` and `book.py:57` are their own — **four classes, three functions**, the same class/path asymmetry round 5 established in the opposite direction (there it forced the sweep to count classes, here it forces the stop set to count functions). A builder who notices the type error and "fixes" it by asserting one loader per discovered class goes red on a correct implementation — round 14's never-key-a-map-to-what-the-scan-cannot-return, one level inside round 17's own remedy.
- **AC-4's does not exist.** AC-4 (`test_body_guard_refuses_when_unverifiable`) runs no scan whatsoever: it names `write_markdown_file`, names two fixtures, and asserts the guard raises. There is no live output to consume, so a builder implementing AC-2's clause literally finds nothing to call and the only repair on offer is to hardcode `write_markdown_file` — reintroducing, inside the clause written to abolish frozen name-lists, the frozen name-list. (The round-16 gate anticipated this and carved AC-4 out as "may stay named" — but the round-17 fold folded it into the computed union anyway, which is strictly worse than leaving it named, because a named exception is visible and a fictitious derivation is not.)

**Concrete failure scenario.** A builder implements AC-2 faithfully: calls AC-1's scan (gets four function identities), calls AC-3's scan (gets four *class* objects), and finds nothing in AC-4 to call. The stop set is four functions plus four unrelated class objects. The closure seeds with the nine direct callers and walks: `base._load_file` is not in the stop set, so it is added, then `load()` (base.py:158), then `get_all()`, `resolve()`, `find_or_create_stub`, `_known_companies` — the closure terminates only when it exhausts the package, and AC-2's map, which holds thirteen entries, matches almost none of what the walk returns. Meanwhile the PARTITION assertion is satisfiable in the *other* direction on a different implementation: normalise the closure to strings, leave the stop contributions as class objects, and all three stop sets are empty, so the residue is the entire closure, every member lands in exactly one class (propagating), the partition holds — and AC-2 now asserts that `update_fields`, `base._load_file` and `write_markdown_file` PROPAGATE the typed error to their callers, which is the refuse-vs-propagate collision round 17 built the partition to catch, reached through the partition itself. Both outcomes ship from a literal reading; neither is a builder error.

**The fix, and why it is a composition rather than a carve-out.** Each contribution states its own conversion into the closure's domain, and none may be repaired by naming. AC-1's arrives as functions. AC-3's is resolved per discovered class through the MRO to the function implementing that class's `_load_file`, then deduplicated (4 → 3 today, both counts baselines). AC-4's guard is taken not from AC-4 but from a derivation that *is* required to run: AC-1's discrimination proof already evaluates two predicates over one traversal — the loose "calls `parse_frontmatter` and later writes" and the data-flow one — and their **set difference** is exactly the function AC-1 must reach and reject, today `write_markdown_file` alone. AC-4 keeps its disposition and its name; AC-1's scan supplies the identity. All three, and the closure, are normalised to one source-stable function identity (module + qualified name — the function-level half of AC-5's site identity) before any set operation, because a partition over mixed identity domains is vacuously true. And each contribution is asserted **non-empty and a subset of the closure**, which is the assertion that fails on the four-class-objects implementation instead of letting it degrade into "everything is residue."

The rule that falls out: **consuming a sibling criterion's derivation is a typed operation, not a cross-reference — state what the sibling produces, what this criterion needs, and the conversion between them; a sibling that derives nothing cannot be consumed, and its member must be sourced from a derivation that actually runs.** Its companion, and the reason this round exists: **a composition is checked by running it, not by reading the sentence that composes it** — the same discipline rounds 12, 14 and 16 each earned one level lower down.

### Decorrelated AC red-team, round 18 → fold 19 (2026-07-24) — what it changed

Round 18 (fence below) confirmed the composition folds whole — the class-to-function MRO resolution and the AC-4-from-set-difference conversion both independently re-derived — and found the composition's last degree of freedom: output agreement without implementation identity. The fold is two-part, both Dave-ruled. **Part 1:** the shared scan module — every derivation in the AC set is one importable implementation, identity-asserted by the partition test; duplicate predicates that agree today and diverge tomorrow are the collision one level down. **Part 2, one-off by design:** the specification-altitude declaration in the preamble. Four consecutive rounds found real defects in the harness's own architecture, each fix minting the next round's surface — an unbounded regress. The AC set now declares its floor (behaviour, derivation obligations, composition) and routes sub-floor findings to the gates that already own harness quality (build-exit) and desc-vs-test fidelity (intent-check). Scoped to this document; the general ruling stays with WI-187, for which this is the first live specimen.

### Non-goals (named so they are not re-explored or scope-crept)

- **Physical quarantine of bad notes** (rename/sidecar) — routed to `lint_vault` / WI-026; it is a deliberate tool action, not a library read behaviour. See A4.
- **Malformed-but-non-blank vault paths / the write-side `mkdir(parents=True)` bogus-tree** — the write half of WI-024's reroute #2; recommend WI-004 owns it (see Inherited scope). This item surfaces, it does not guard the write.
- **`lint_vault`'s import-time env read** (lint_vault.py:48) — latent, WI-026's territory (noted in WI-024).
- **Fixing the stale `_obsidian_schemas.pth`** — load-bearing as-is; explicitly out of scope (CLAUDE.md, `pipeline-runners.yaml`).
- **Migrating HAL9000's three N4 consumer call sites** (enricher, introducer, scheduler) — they live in another repository this project's hermetic floor cannot import or exercise, and no `kind: command` runner is registered here that could audit them (see the red-team response above). AC-5 instead pins the locally-verifiable backward-compat property: no legitimate no-op's return value changes. **Parked for Dave's call — mint a companion work item in HAL9000.**

## Approach

Fix the defect class at its seam and let the read/write asymmetry fall out of one distinction. Make `parse_frontmatter` stop conflating "no frontmatter" with "frontmatter that failed to parse": the malformed case becomes a distinct, loud signal (typed error or discriminated result — spec-writer's call). Write/mutate paths then **refuse** rather than rebuild — no file is ever rewritten from a frontmatter dict that did not parse, and the on-disk note is left byte-for-byte untouched (C2, the keystone). That set is *derived*, not named: every caller of `parse_frontmatter` in the package that re-serializes and writes — `update_fields` (base.py:312), `update_frontmatter_field` (writer.py:247), `update_frontmatter_fields` (writer.py:286), **and `roundtrip_file` (writer.py:317), which the campaign's enumeration missed and which has no `try`/`except` at all**. The deriving predicate is **data flow, not adjacency**: a member is a function in which the dict `parse_frontmatter` returned is re-serialized into the bytes that same function writes (base.py:312 → 324 → 327-329; writer.py:247 → 250 → 253-256, 286 → 289 → 292-295, 317 → 319-322). "Parses, then writes" is a *different* predicate and returns a fifth function that must not be swept — `write_markdown_file` (parse at writer.py:186, write at 217) — which discards the parsed frontmatter (`_, existing_body`) and builds what it writes from its own `entity`/`frontmatter` arguments (writer.py:197-205); it is the derivation's **proven negative**, excluded by the predicate rather than by name, and its own malformed-existing-file behaviour belongs to C3/AC-4. Symmetrically, the fix must not break the legitimate half **across that same derived set**: a genuinely fence-less note must still accept frontmatter exactly as today at all four paths — including `update_fields`, on which ordinary field-setting against a freshly-created stub depends, and `roundtrip_file`, whose contract is to preserve content while normalising YAML. Malformed frontmatter is the only thing that becomes loud; absent frontmatter is untouched everywhere. Read/load paths **survive but surface** — WARN, and record the skip in a queryable count/list on the repository so a dropped note cannot silently drive duplicate creation (C4) — swept across the **four concrete `BaseRepository` subclasses**, each independently instantiated — `PersonRepository`, `CompanyRepository`, `MeetingRepository`, `BookRepository` — rather than across the three `_load_file` overrides they share between them (`base.py:181`, inherited verbatim by both `PersonRepository` and `CompanyRepository`, since `company.py` overrides neither `_load_file` nor `file_pattern`; `meeting.py:81`; **`book.py:77`**, likewise missed), for both failure predicates: YAML that will not parse, and YAML that parses but fails validation for a known `type`. That surface is scoped by **ownership evidence, not by the glob** — every repository globs files it does not own and decides ownership downstream of the parse being made loud, so a naive surfacing turns the signal into noise on a healthy vault. A file whose `type` is readable and is not this repository's type is decidably foreign and never enters the skip surface (`base._load_file` checks no `type` at all today, so post-fix every well-formed `@Acme.md` would otherwise report as a skipped *person* — `Person.type` is `Literal["person"]`, models.py:78 — and every person note as a skipped company, since both repositories share the `@*.md` glob). That exposure runs **both ways over one shared implementation**, so the ownership comparison is made against each repository's **own** declared `type_name` (the abstract property at base.py:126-130) and has to be proved from both chairs — `CompanyRepository` instantiated on the same vault as `PersonRepository`, each asserting its own skip-list — because a shared `_owns()` that reads correctly for the class someone tested can be hardcoded, inverted or mis-ordered for the class they did not. Conversely a file whose `type` is readable and **is** this repository's type but which still fails `model_validate` on some other field — `type: person` with `emails: "not-a-list"`, the only other way to fail given `extra="allow"` (models.py:31-32) and no custom validators — is decidably **owned** and drifted, and **must** be listed: that is C5's own duplicate-creation case, the one C4's story is about. Those two are the same code path (`parse_to_model` raising inside `model_validate`) with opposite answers, so **ownership must be decided on the raw `type` value read from the parsed frontmatter, independently of and prior to model construction — never by "did `model_validate` succeed"**, which is exactly the predicate `base._load_file` uses today via `isinstance` (base.py:179) and which would silently drop the owned-and-drifted note. A file whose `type` is unreadable but whose glob is a naming convention (`@*.md`, `Meeting *.md`) **stays** in the surface, because that is precisely the C4 case it exists for. `BookRepository`, whose `file_pattern` is the catch-all `*.md` (book.py:49-51), has neither kind of evidence for a malformed file and must not report it as a skipped book; the mechanism is the spec-writer's call, but each repository's fixture vault is derived from its own `file_pattern` and is heterogeneous, never single-type. That owned-and-drifted case is required from **every** one of the four chairs, derived from each class's own model rather than transposed from a sibling — `type: person` + `emails: "not-a-list"` (models.py:81), `type: company` + `tags: company` (the inherited `BaseEntity.tags`, models.py:40, since `Company`'s own fields are all `str`), `type: meeting` + `attendees: "not-a-list"` (`Meeting`'s own `List[str]`, models.py:261-262), `type: book` + `tags: book` (again the inherited `tags`, `Book` declaring no `List` field of its own, models.py:159-170) — because it is the direction that carries the *new* signal through each class's *own* `_load_file`, and `meeting._load_file` and `book._load_file` are structurally unlike `base`'s: both already read the raw `type` ahead of model construction (meeting.py:72-75, book.py:67-70), so their foreign-type direction is sound today while their own-type-drifted note passes that prefilter and lands, post-fix, in their own bare `except Exception` (meeting.py:81-83, book.py:77-79) that nothing has ever exercised under this failure mode. The four classes do **not** share one expectation table: the malformed-YAML fixture must be listed by `PersonRepository`, `CompanyRepository` and `MeetingRepository` (owned by naming convention) and must **not** be listed by `BookRepository` (no ownership evidence under a catch-all glob), while the owned-and-drifted fixture must be listed by all four, `BookRepository` included — its glob is irrelevant once `type: book` is readable, since ownership is read off the raw `type`. And because `BaseRepository.load()`'s for-loop (base.py:157-165) wraps `_load_file` in no `try`/`except` at all, each class's own `except` clause *is* the no-abort guarantee: whatever narrowing the fix performs there must still catch the new typed validation failure, proven once per class rather than assumed to transfer from the base path. The body-shrink guard (C3) refuses when it cannot read the existing body instead of assuming it empty — and must be designed alongside C2 so it does not re-swallow the new parse signal. `parse_to_model` distinguishes "known type, failed validation" (loud — schema drift) from "unknown type" (fine), the same shape one layer up (C5). Write paths make a genuine I/O failure **raise** (a `ValueError` subclass, per the package convention) while every case that is a *legitimate* no-op today — dedup, absent section with `create_if_missing=False`, To-Discuss item text not found — keeps the exact falsy value it returns today (N4). That sweep is likewise derived rather than named, and by **four** predicates: the blanket `except Exception` in a writer; the guaranteed-section insertion writer (`append_to_timeline`'s marker-absent branch and its structurally-dead split guard, person.py:1482-1484 and 1491-1492 — the caller's entry is today silently dropped into the dedup no-op's `False`; resolved by ACCOMMODATION per the round-9 finding and Dave's ruling: the `## Timeline` section is auto-created and the entry inserted, mirroring the sibling's `create_if_missing=True`, since a raw-content check cannot distinguish corruption from a legitimately Timeline-less note — and, per round 10, that accommodation carries an explicit **preservation** property, because the sibling's absent-section path round-trips the body through `parse_body_sections`/`write_body_sections` (person.py:1586-1593 → body_sections.py:74-97, 100-134), which keeps only `^## `-delimited spans and therefore deletes any preamble above the first heading and destroys a heading-less body outright, on a raw `write_text` (person.py:1495, 1597) that writer.py:178-183 explicitly exempts from the WI-126 body-shrink guard: the auto-create must leave every pre-existing body byte present and the frontmatter byte-identical, proved on a heading-less body and a preamble body, which are exactly the hand-created-in-Obsidian notes the accommodation exists for; the mechanism — string insertion, or making the section round-trip lossless, which would repair the sibling's identical latent wipe at the same time — is the spec-writer's call. Dedup stays whole-file and frozen (person.py:1476, deliberate per person.py:1521-1524), so the honest claim is that *structural* absence can no longer drop the entry, not that a drop is impossible); the existence pre-check returning falsy where every sibling writer raises (writer.py:242-243, 281-282 vs. person.py's five `ValueError` raises and base.update_fields' `FileNotFoundError`); and the frontmatter-fence split (`content.startswith("---")` → `split("---", 2)`), which is copy-pasted across four writers — `append_to_body_section`, `add_to_discuss_item`, `update_to_discuss_item`, `remove_to_discuss_item` — so "no fence" and "malformed fence" stop being a `False` in all four, not just the one earlier rounds cited. Running that second predicate also exposed a fifth member nothing had seen: `_get_body_content` (person.py:1622-1626) answers an unsplittable fence by returning the whole file, frontmatter and all, as body — a read, so it surfaces rather than raises, but it must stop letting `get_to_discuss_items` report a broken note as "no items." And because a predicate list is itself a sample until its universe is enumerated, that sweep is **closed rather than merely derived**: the package's complete set of non-completed-write returns across its write paths and shared section-read helpers is 28 sites (writer.py 243/260/282/299 and person.py's 24, `company.py`/`meeting.py`/`book.py` declaring no bool-returning writer at all), every one of which must land in exactly one of the four raise predicates or the four no-op classes — the fourth being `_get_body_content`'s missing-file `None`, already made loud by its only caller's `ValueError` (person.py:1641-1643) — so a site matching none of the eight is a test failure rather than a future red-team finding. Stated that way, the contract change is one-directional and locally provable: no consumer-visible return value changes except where it was reporting a failure as a no-op, so an existing `if not repo.append_to_body_section(...)` branch keeps its current meaning and only a genuine data-loss stops being silent. The cross-repo consumer migration this implies is parked — see Non-goals. And every one of those sweeps is **executed by its test rather than remembered by it**: the write-path set, `parse_frontmatter`'s return sites, the concrete `BaseRepository` subclasses and the 28-site falsy universe are each discovered from the live source at test time and checked against an explicit in-test map, so a member added later arrives as a red test rather than as a twelfth red-team round — and discovery means SOURCE, uniformly across all four sweeps: an AST scan over a file set the test itself walks (every `.py` under `obsidian_schemas/`, recursively), never the import graph and never `inspect`, whose blind spots are the same one (`__subclasses__()` and `inspect.getmembers` both see only modules something imported; today every module in this package is transitively imported — `name_validation.py` only via `repositories/person.py:22` — so an import-based scan reads complete for a reason that has nothing to do with the property), and never a file set named by hand either: scoping a source scan to `repositories/` or to "the swept modules" is the frozen list wearing a path, and a fifth repository or a sixth silent-`False` writer put in a new module beside them is exactly as invisible to it as to the import graph. Each scan must also be shown to *discriminate*, `write_markdown_file` being the write-path scan's required negative, since a scan asserted only against what it returns is indistinguishable from a hardcoded list of those names. And a scan's map is keyed only by what the scan can actually return: `parse_frontmatter` carries five outcome classes on **four** `return` statements (parser.py:65, 70, 77, 80 — the empty-fence case is the `safe_load`-returns-`None` normalisation at 74-75, which has no return of its own and shares site 77 with the valid case), so the map is keyed by return site, a site may carry more than one named outcome class, and every class is separately required to be exercised — otherwise the site/class conflation makes the enumeration red on a correct implementation and green once the unmatched class is dropped. The same rule governs the seam's own **invocation surface**, which is swept too rather than assumed internal: the loudness travels to every function that reaches `parse_frontmatter`/`parse_to_model`, so those callers are derived as a **transitive closure** — the fixpoint of "package functions that reach the seam", not the functions that name it, because `parse_person`/`parse_company`/`parse_book`/`parse_meeting` (parser.py:216-237) reach it only through `parse_markdown_content` and `base._load_file` only through `parse_markdown_file` (base.py:178), and an adjacency scan returns none of them — and the closure stops at any function another criterion has already dispositioned, which is what makes it terminate. That stop set is itself computed rather than listed: it is the three sibling criteria's own live derivations consumed as inputs, each converted into the closure's own domain (a source-stable module + qualified-function identity) rather than assumed to already be in it — AC-1's write set arrives as functions and needs none; AC-3 derives *classes*, so each is resolved through its MRO to the function implementing its `_load_file` and deduplicated, four classes collapsing to three functions today; and AC-4 derives nothing at all, so the guard is taken from the set difference AC-1's own discrimination proof already computes (its loose "parses then writes" predicate minus its data-flow predicate, which is exactly the function AC-1 must reach and reject). The three contributions plus the propagating residue must then partition the closure exactly, each contribution non-empty and inside it, so that a mis-typed or empty contribution fails loudly instead of quietly making everything residue. Its residue is the **public parse layer** — `parse_markdown_file`, `parse_markdown_content` and the four typed conveniences, none behind a `try`/`except` — which post-fix PROPAGATES the typed error on malformed input while keeping today's exact returns for absent frontmatter and unknown types, so the item's externally-visible surface is an enumerated caller set rather than a claim of internality. Deriving the class list does not soften the round-6 ruling that AC-3's twelve cells stay explicit: the cells are the map, the scan supplies its keys, and an unmapped key fails. Every fix ships its invariant test; the keystone is the malformed-YAML round-trip regression. The two WI-024 reroutes: narrow `_known_companies`' bare `except` at person.py:1147-1160 **at the except clause itself**, so a genuine `VaultPathNotConfiguredError` propagates rather than merely being re-logged (its own AC, since a log-level change would otherwise satisfy the wording); and surface the non-existent-vault load here, but recommend WI-004 owns the write-side `mkdir` guard (flagged for Dave's sign-off, not encoded below).

## Acceptance Criteria

Draft acceptance criteria — a convergence artifact ("what would prove this worked?"), to be reviewed and frozen with Dave via `/review-spec` before origination (the `ac-signoff` fence is written by code after his review, never here), then refined in place by the spec-writer. Each `check:` name is a proposed test the build will implement.

**Specification altitude (Dave-ruled 2026-07-24, a one-off scope declaration for THIS document — it amends no role or bar and is recorded as a specimen for the WI-187 altitude session):** this AC set specifies three things — (a) observable behaviour at the package's boundaries, (b) the derivation obligations that keep its sweeps live rather than frozen, and (c) the composition of those derivations: shared outputs (round 17), one shared implementation (round 19), and the partition they must jointly satisfy. Concerns BELOW that line — how the shared scan module is factored or named, how it is itself unit-tested, and any further property of the harness's internal architecture — are the declared jurisdiction of the pipeline's existing later gates (build-exit review for harness code quality; intent-check for desc-vs-test fidelity), not of this AC set or its red-team pass. A finding at that altitude is real but routed: it belongs to those gates' reviews, not to another fold here.

**Revised 2026-07-24** in response to the decorrelated red-team recorded below. Three structural changes: each AC that quantifies over a class now **derives** its sweep from the code rather than naming a list (which turned up two missed class members — see the red-team response in Exploration Notes); the malformed-must-raise half is now paired with the **absent-must-still-succeed** half so the fix cannot over-shoot; and AC-5's cross-repo consumer audit is **removed** — no check available in this repo can verify it (see Non-goals) — replaced by a backward-compat property that is locally provable.

**Revised again 2026-07-24 (round 2)** after the re-verify pass. Both remaining gaps were an AC deriving one half of its property and hand-writing the other. AC-1's absent-must-succeed half now quantifies over the **same** derived four-path list as its raise half; AC-5 now carries an explicit **second derivation predicate** (the frontmatter-fence split) instead of naming one function's branches — which turned up a fifth site (`_get_body_content`) that no prior pass had seen. Rule for anything added later: **an AC names its predicate, never its sites.**

**Revised again 2026-07-24 (round 3)** after the second re-verify. One gap, and it is the round-2 rule missing its other half: AC-3 derived its *repository* sweep from the code but hand-picked its *fixture space*, so `BookRepository`'s catch-all `"*.md"` glob (book.py:49-51) would have made every malformed note in the vault a "skipped book". Re-deriving the fixture space per repository from its own `file_pattern` also exposed a larger case on a **healthy** vault: `PersonRepository` and `CompanyRepository` share the `@*.md` glob and `base._load_file` checks no `type` at all, so post-fix every company note would report as a skipped person. AC-3 now derives its fixture vault per repository, requires it to be heterogeneous, and asserts the skip surface in both directions. Extended rule: **an AC names its predicate, never its sites — and derives its fixture space, never samples it.**

**Revised again 2026-07-24 (round 4)** after the third re-verify. One gap, inside AC-3's own fixture list: "a known type fails Pydantic validation" names two mechanically identical cases — a foreign `type: company` note under `PersonRepository`, and an owned `type: person` note that fails on another field — with **opposite** required answers, and the doc gave a worked example only for the one that must be *excluded*. So the owned-but-drifted note that is C5's actual duplicate-creation driver was never pinned as present, and the natural implementation ("if the model failed to build, it isn't mine") would drop it while every AC read green. AC-3 now requires **three distinct fixture files**, forbids (b) and (c) from being the same file, and states the mechanism-forcing property this turns on: **ownership is decided on the raw `type` value, never on whether `model_validate` succeeded.** Rule added: **two fixtures that share a code path but require opposite answers must be two files, asserted in one test.**

**Revised again 2026-07-24 (round 5)** after the fourth re-verify. One gap, and it is the round-4 rule one level out: AC-3 derived its fixture space per repository but derived its *repository sweep* from the three `_load_file` **overrides**, which collapses `PersonRepository` and `CompanyRepository` — two classes sharing one inherited implementation and one `@*.md` glob — into a single sweep entry. Every fixture, direction and Example of done in the doc was written from `PersonRepository`'s side, so a test parametrized over `{PersonRepository, MeetingRepository, BookRepository}` read as satisfying the AC while the *larger* half of round 3's healthy-vault exposure — "every person note becomes a skipped company" — shipped unverified, and a comparison hardcoded to one type literal instead of `self.type_name` would pass it. AC-3 now sweeps the **four concrete `BaseRepository` subclasses**, requires `PersonRepository` and `CompanyRepository` to be **independently instantiated** against the same shared vault and asserted in all three directions each, derives each class's own (b)/(c) fixtures from its own `type_name` and model fields, and a seventh Example of done pins the company side in Dave's terms. Rule added: **when two classes share one code path, the sweep counts the classes, not the path — a shared implementation is verified once per class that inherits it.**

**Revised again 2026-07-24 (round 6)** after the fifth re-verify. One gap, and it is the round-5 rule left half-applied: AC-3 named four repository classes but worked out fixtures for two — `MeetingRepository` appeared only in the enumeration and in a counter-example, `BookRepository` only in its exclusion clause. The direction never reached was fixture (b), the owned-but-drifted note, which is the one that carries this item's *new* signal into each class's *own* `_load_file` — and `meeting.py`/`book.py` are structurally unlike `base.py` (both prefilter on the raw `type` at meeting.py:72-75 / book.py:67-70, so their foreign-type direction is already sound, while a `type: meeting` + `attendees: "not-a-list"` or `type: book` + `tags: book` note passes that prefilter and fails only inside `parse_markdown_file`, landing in their own untested `except`). Since `BaseRepository.load()` (base.py:157-165) wraps `_load_file` in no `try`/`except` at all, a narrowed catch that misses the new error there aborts the entire batch — the HAL9000-startup regression, reached by exactly the narrowing AC-6 asks for elsewhere. AC-3 is now the complete derived **4×3 matrix**: one fixture set per class, each derived from that class's own `type_name`, model fields and `_load_file` structure, with a NO-ABORT assertion on all twelve cells; and it records that the matrix is **not uniform** — fixture (a) is must-be-listed for three classes and must-NOT-be-listed for `BookRepository`, while fixture (b) is must-be-listed for all four. Rules added: **when a sweep's members do not all have the same answer, the AC writes each member out — a quantifier with one shared expectation table silently asserts uniformity nobody checked**; and **prove the insulation, not only what it produces.**

**Revised again 2026-07-24 (round 7)** after the sixth re-verify — the audit-fold applied to AC-5's own derivation, per the same Dave ruling that produced round 6's. The finding: AC-5 swept by TWO predicates, and `append_to_timeline` collapses a third — marker-absent (person.py:1482-1484) and a structurally-dead split guard (1491-1492) return the same `False` as the legitimate dedup no-op, on notes whose own template guarantees `## Timeline` exists (body_sections.py:305-306), so a caller's timeline entry is silently dropped. Instead of adding the found predicate alone, the falsy-site classification was re-derived from scratch over the whole write-path surface at source, which found two more gaps the finding did not name: writer.py's existence pre-checks (243, 282) return `False` for the file-missing condition every sibling writer in the package raises for, and the no-op half's citation list was wrong in both directions (update_to_discuss_item's section-absent site 1746-1747 mislabeled as "item text not found"; remove_to_discuss_item's 1813-1814 missing entirely). AC-5 is now a FOUR-predicate derivation with the no-op half derived by predicate too, split on whether a falsy return drops a caller's payload (failure) or answers "the thing you named is not here" (no-op). Rule added: **when a round shows a derivation's predicate list incomplete, re-run the whole derivation at source and fold once — the found member is a symptom, and patching it alone is the treadmill.**

**Revised again 2026-07-24 (round 8)** after re-verifying the round-7 fold at source. Every round-7 claim holds live (`append_to_timeline`'s four falsy returns including the structurally-dead split guard, the person template's guaranteed `## Timeline`, writer.py's existence pre-checks against the package's five sibling `ValueError` raises and `base.update_fields`' `FileNotFoundError`, and the corrected no-op citations). What the re-derivation exposed is one level up from any single predicate: AC-5 *asserted* its predicate list exhaustive rather than proving it, which is the same treadmill as patching a found member — five consecutive rounds had the class right and the members short. Swept live, the package's complete universe of non-completed-write returns in write paths and shared section-read helpers is **28 sites** and nothing else (`company.py`, `meeting.py` and `book.py` declare no bool-returning writer at all, which is also what makes `append_to_timeline` P3's only member by enumeration rather than inspection). Classifying all 28 left exactly one residue — `_get_body_content`'s missing-file `None`, already converted to a `ValueError` by its only caller — now no-op class **(d)**. AC-5 gains that class and a **CLOSURE** clause requiring the test to enumerate the universe and land every member in exactly one of P1-P4 or (a)-(d), with the out-of-universe returns named explicitly. Rule added: **a derived sweep is finished when its universe is enumerated and every member classified — until then "derived by N predicates" is still a sample, just a principled one.**

**Revised again 2026-07-24 (round 9)** after the eighth re-verify — the first round whose finding was a *design* objection rather than an enumeration gap (the 28-site universe was independently re-derived and confirmed exact). The finding: P3 forced `append_to_timeline`'s marker-absent case to raise on a raw-content check that cannot distinguish "corrupted since creation by this package" from "legitimately never had a Timeline section" (hand-created in Obsidian, or predating the template convention — a scenario round 6's own prose named), while the sibling `append_to_body_section` already handles the identical ambiguity with a caller-facing `create_if_missing` lever that P3 gave `append_to_timeline` no equivalent of. Dave ruled remedy (a): **accommodate** — auto-create the section and insert, mirroring the sibling's default, so the entry always lands and the drop becomes impossible without manufacturing a failure out of a structural variant. P3's disposition changes from raise to accommodate (the CLOSURE taxonomy stays eight buckets: three raise predicates, one accommodate predicate, four no-op classes); dedup keeps its exact `False`; the Example of done is restated in both directions. Rule added: **when a raise remedy rests on a premise the runtime check cannot confirm, and a sibling already solves the same ambiguity by accommodation, converge on the sibling — refusal is only loud-fail when the thing refused is actually a failure.**

**Revised again 2026-07-24 (round 10)** — the audit-fold applied to round 9's own remedy, since a ruling that says "mirror the sibling" is a name-level argument until the sibling is read. It was, and it is lossy in exactly the case the ruling serves: `append_to_body_section`'s `create_if_missing=True` route rebuilds the body via `parse_body_sections`/`write_body_sections` (person.py:1586-1593 → body_sections.py:74-97, 100-134), which retain only `^## `-delimited spans — so a preamble above the first heading is deleted and a heading-less body is destroyed outright, written by a raw `write_text` (person.py:1495, 1597) that writer.py:178-183 deliberately exempts from the WI-126 body-shrink guard AC-4 is hardening. The note least likely to have `##` headings is the hand-created-in-Obsidian note round 9 ruled the accommodation in for, so the naive mirror would trade a silently dropped entry for a silently dropped note body. Dave's ruling is unchanged; AC-5's P3 gains a **PRESERVATION** clause (pre-existing body entirely present, frontmatter byte-identical, proved on a heading-less fixture and a preamble fixture, with today's `body_sections` round-trip explicitly failing it) plus an idempotence assertion, the CLOSURE clause now says it is evaluated against the **post-fix** package (28 is a baseline, not the expected answer — P3's own remedy adds code), and the "the drop is impossible" claim is corrected to *structural* absence, since whole-file dedup (person.py:1476, deliberate per person.py:1521-1524) is frozen by this AC's backward-compat half and remains the one falsy path. Rule added: **when a fold converges on a sibling's semantics it inherits the sibling's implementation — read the sibling, don't cite it; a contract ("creates the section if missing") is not a predicate (round-trips the body through a lossy parser).**

**Revised again 2026-07-24 (round 11)** after the tenth re-verify, Dave-ruled remedy (a) on a single-gap ask. The finding: AC-1's "a fifth caller joins the sweep" and AC-5's CLOSURE both promised a *forward-looking* completeness property — a future silent-`False` writer or `parse_frontmatter`-calling write path gets caught by the suite going red — but neither `check:` required the derivation to be performed by the test against live source; a hand-derived enumeration frozen at build time satisfied both as written, and a sixth To-Discuss-style writer copy-pasted in next month would ship green and invisible, which is the original five findings' failure mode reproduced by the very clause built to prevent it. Both ACs now require the derivation be EXECUTED at test time (AST/inspect scan of the swept surface, checked against an explicit in-test classification map; unclassified site = red), and state that a hardcoded name/line list does not satisfy them. This is the terminus of the item's derive-don't-name ladder: sites → predicates → universe → disposition → preservation → the test itself performs the derivation. Rule added: **a completeness claim is only as durable as the process that re-checks it — if the AC promises "future instances join the sweep," the check must run the derivation, not remember its output.**

**Revised again 2026-07-24 (round 12)** — the audit-fold applied to round 11's own remedy, since "the test performs the derivation" is a promise about a predicate until the predicate is run. It was, against the live tree, and it returns a member AC-1 does not sweep: `write_markdown_file` calls `parse_frontmatter` (writer.py:186) and then writes (217), satisfying round 11's literal "callers of parse_frontmatter that subsequently write" — so a builder implementing that scan gets five paths, sees the AC names four, and drops the fifth by name, which is the frozen curation round 11 abolished, moved inside the scan. What actually separates them is data flow: the four members re-serialize the dict `parse_frontmatter` returned into the bytes they write, while `write_markdown_file` discards it and builds its output from its own arguments (writer.py:197-205). AC-1 now states the predicate that way and requires `write_markdown_file` be **reached and rejected by the scan**, asserted as a negative — a scan that only confirms what it returns has not been shown to discriminate. Re-running the finding's shape over the whole AC set (rather than the two ACs the gate named) found the same overclaim standing in two more places: **AC-3**, whose "a fourth repository joins automatically" has been in the Exploration Notes since round 1 with no check behind it, now derives its **class list** live from the concrete `BaseRepository` subclasses (ABC with abstract `entity_type`/`type_name`, base.py:120-130) while round 6's non-uniform twelve cells stay explicit — the cells are the map, the scan supplies its keys, an unmapped key fails; and **AC-2**, whose "one case per return site" is a completeness claim over a function this item's own fix edits, now scans `parse_frontmatter`'s post-fix return sites (five is a baseline, not the answer). AC-5's classification map gains the key it was missing: a source-stable site identity (module + qualified function + ordinal within that function), since line numbers all shift in `person.py` when the fix lands and a function name alone cannot separate `append_to_timeline`'s four sites across three buckets. Rule added: **a live derivation is a predicate plus a proven negative, and the clause belongs to every AC that claims a class is complete — not to the ones a round happened to name.**

**Revised again 2026-07-24 (round 13)** after the twelfth re-verify, Dave-ruled on a single-gap ask with a totality upgrade. The finding: AC-3's class-list derivation was specified as a runtime `__subclasses__()`-style check while its sibling sweeps are AST-based — and the import graph is a weaker oracle than the source: a fifth repository module not imported by `repositories/__init__.py` by test time is invisible to `__subclasses__()`, so the discovery clause itself reproduces the green-suite/zero-coverage gap it was added to close. The fold applied the class fix, not the instance fix: ALL four derived sweeps (write paths, parse return sites, repository classes, the falsy-site universe) now state one uniform mechanism — discovery from source, AST over the package's module files on disk, with the test importing what it discovers — and AC-3 explicitly rejects the runtime check. Rule added: **a sweep derived from the import graph inherits the import graph's blind spots — derive from source; the set of modules that happen to be imported is itself an unproven premise.**

**Revised again 2026-07-24 (round 14)** — the audit-fold applied to round 13's own remedy, by running the four scans it unified rather than re-reading its summary of them. Two findings, one class. First, round 13's note claims all four sweeps now state one mechanism; read live, it rewrote AC-3 and AC-2 already said "AST", while **AC-1 and AC-5 still read "AST *or inspect-based*"** — and `inspect` enumerates module objects, which exist only for imported modules, so it carries the identical blind spot `__subclasses__()` was rejected for. It reads green today only because every module in this package happens to be transitively imported (`name_validation.py` solely via `repositories/person.py:22`), which is round 12's own tell. Second, the same gap one level down: three of the four scans hand-write their **file set** — AC-3 walks `repositories/`, AC-5 walks "the swept modules" (the two its 28-site count lives in), AC-1 says "the package" — and a source scan scoped by a directory or a module list misses a fifth repository or a sixth silent-`False` writer added in a new module exactly as the import graph does. All four now walk one derived file set: every `.py` under `obsidian_schemas/`, recursively, discovered by the test. Third and separately, running AC-2's scan exposed a keying error nothing had caught: AC-2 says "one case per return site" and lists five, but `parse_frontmatter` has **four** `return` statements (parser.py:65, 70, 77, 80) carrying five outcome classes — the empty-fence case is the `safe_load`-returns-`None` normalisation at 74-75, which shares site 77 with the valid case — so the AC's own site-set equality assertion is red on a correct implementation, and the cheap repair drops the unmatched *class*. AC-2 now keys its map by return site, allows a site to carry more than one named outcome class, and requires each class exercised. Rules added: **a source scan is only as complete as the file set it walks — derive the file set too; naming a directory is the frozen list wearing a path**; and **never key a scan's map to a construct the scan cannot return.**

**Revised again 2026-07-24 (round 15)** after the fourteenth re-verify, Dave-ruled on a one-line ask. The finding: the parse seam's loudness change cascades to callers no derived sweep could discover — `parse_markdown_content` and the four typed conveniences (parser.py:216-237), none behind a `try`/`except` — the uncovered-invocation-layer class (WI-158's, LESSONS #7 corollary). The fold enumerated the seam's COMPLETE invocation surface at source: every package caller of `parse_frontmatter`/`parse_to_model` classified into exactly one of four caller classes — refusing writer (AC-1), insulated loader (AC-3), the discarding guard (AC-4), and the previously unnamed fourth class, the PROPAGATING PUBLIC PARSE SURFACE, now covered by AC-2's invocation-surface clause (malformed propagates the typed error, asserted per discovered member; absent/unknown keep today's returns exactly). Export status was verified at source rather than trusted from the finding (the gate's "all package-exported" was an overclaim: `__init__` exports `parse_frontmatter`/`parse_markdown_file`/`ParsedDocument` only; `parse_markdown_content` is README-documented; the four conveniences are public-by-module-path with zero external consumers today), and the Constraints bullet claiming N4 "the only finding that is not purely internal" is corrected — false once the public surface propagates. Rule added: **an item that changes a seam's failure behaviour sweeps the seam's callers, not only the code it edits — every caller lands in a named class or the suite is red; "internal-only" is a claim about an enumerated caller set, never about intent.**

**Revised again 2026-07-24 (round 16)** — the audit-fold applied to round 15's own remedy, by running the invocation-surface scan it added rather than re-reading its description of it. The finding: that scan is specified as "every caller of `parse_frontmatter` and `parse_to_model`", which is direct-call **adjacency**, and four of the six functions AC-2's own map calls propagating members are not direct callers — `parse_person`/`parse_company`/`parse_book`/`parse_meeting` (parser.py:216-237) reach the seam only through `parse_markdown_content`, and `base._load_file` only through `parse_markdown_file` (base.py:178). Run live the scan returns nine functions containing none of those five, so a faithful implementation goes red against its own map and the cheap repair deletes precisely the README-documented conveniences the round-14 finding was raised about — round 14's "never key a map to what the scan cannot return" recurring inside the remedy that rule produced. AC-2's invocation surface is now a **transitive closure** (fixpoint of "functions that REACH the seam") whose stop rule is "another criterion has already assigned this function a disposition" — which terminates it and makes "exactly one class" well-defined — with the map equality asserted in **both** directions, and the six-member residue computed rather than named. The same read also retired an unverifiable claim: AC-2 asserted the conveniences have no external consumer "verified against HAL9000 and exocortex source", which this hermetic floor cannot check and which the first fold already removed a clause for; export status is now stated only from in-repo source, with external consumers parked alongside N4's companion item. Rule added: **a caller sweep is a transitive closure, not an adjacency list — a seam's invocation surface is every function that REACHES it, and the closure is well-founded only because it stops where another criterion has already assigned a disposition.**

**Revised again 2026-07-24 (round 17)** after the sixteenth re-verify, Dave-ruled on a one-line ask. The finding: the closure's own stop set — the one construct that makes the walk terminate — was named by example (AC-1's four writers, AC-3's three loaders, AC-4's guard) in a document where every other set forbids a hardcoded list; a future writer or loader those ACs auto-discover would fall outside the frozen stop list, unbounding the closure or leaving one function claimed by two ACs with incompatible dispositions. The fold composes rather than restates: the stop set is now CONSUMED as the live output of AC-1's, AC-3's and AC-4's own test-time derivations, and a PARTITION assertion requires the three computed stop sets plus the propagating residue to partition the computed closure exactly — a member in no class or in two is red by computation. This closes the derivation system under its own checks: there is no set left in the AC set that is named rather than derived, and the sweeps now verify each other's boundaries. Rule added: **when criteria share a boundary, one criterion consumes the other's derivation as input — restating a sibling's set is a frozen list wearing a cross-reference, and the partition of the whole surface is itself an assertable property.**

**Revised again 2026-07-24 (round 18)** — the audit-fold applied to round 17's own remedy, by running the composition it introduced rather than re-reading the sentence that composes it. The finding: AC-2's stop set is specified as the union of AC-1's, AC-3's and AC-4's live derivations, but only AC-1's is a set of *functions*. AC-3's derivation discovers **classes** (its whole map is keyed by class), and a class is not a member of a closure over functions — consumed literally the intersection is empty, so the closure never stops at `base._load_file` and climbs through `load()`, `get_all()` and `resolve()`, the unbounded walk the stop rule exists to prevent, now reached *through* the rule. And AC-4 runs no derivation at all — it names `write_markdown_file` and asserts two fixtures — so "AC-4's live output" is fictitious and the only repair available is the hardcoded name the clause abolished. Worse, the PARTITION assertion is satisfiable on the broken implementation: empty stop sets make the residue the whole closure, every member lands in exactly one class, and AC-2 ends up asserting that AC-1's writers PROPAGATE — the refuse-vs-propagate collision the partition was built to catch, reached through the partition. The fold makes each contribution state its own conversion: AC-1's arrives as functions; AC-3's is resolved per discovered class through the MRO to its `_load_file` implementation and deduplicated (four classes → three functions, both baselines); AC-4's guard is sourced instead from AC-1's discrimination proof, whose two predicates' **set difference** already computes it. All three plus the closure are normalised to one source-stable function identity before any set operation, and each contribution must be non-empty and a subset of the closure. Rules added: **consuming a sibling criterion's derivation is a typed operation, not a cross-reference — state what the sibling produces, what this criterion needs, and the conversion between them; a sibling that derives nothing cannot be consumed**; and **a composition is checked by running it, not by reading the sentence that composes it.**

**Revised again 2026-07-24 (round 19)** after the eighteenth re-verify, Dave-ruled as a TWO-PART fold on a framed ask. Part one, the finding's fix: nothing required the scans the stop set consumes to be one implementation — a builder could satisfy every fence with independently-written duplicate predicates that agree on today's tree and diverge on the first future write path, the refuse-vs-propagate collision reappearing one level down. AC-2 now requires ONE shared importable scan module consumed by every test that derives, with implementation identity asserted (same callables, not same-typed outputs) — solve-in-one-place applied to the harness. Part two, Dave-ruled and explicitly one-off: a **specification-altitude declaration** in the AC preamble. The last four rounds' findings all concerned the checking machinery's own architecture, each fold's fix creating the surface the next round examined — a regress with no natural floor. The declaration scopes THIS AC set to observable behaviour + derivation obligations + their composition, and routes findings below that line (harness factoring, the scan module's own tests) to the pipeline's existing later gates (build-exit review, intent-check) where they already have an owner. It amends no role or bar; it is recorded as the first live specimen for the WI-187 altitude session. Rule added: **an AC set needs a declared floor as much as a derived sweep needs a declared universe — without one, the red-team's regress is unbounded by construction, and every fix mints the next finding's surface.**

**Check strategy (Dave's 2026-07-23 testing ruling, applied at round 7):** this is a pytest-floor project with Pydantic schemas and a parse/serialize inverse pair, so checks whose properties quantify over *inputs* are implemented as Hypothesis property tests over generated note contents — AC-1 (any generated note with malformed frontmatter: every derived write path raises and the file is byte-identical; any generated note with absent frontmatter: none raises and behaviour matches the captured baseline), AC-2 (generated inputs per return-site class; malformed never returns a legitimate case's value), and AC-5's two halves (generated failure inputs raise; generated legitimate no-ops keep today's exact returns). AC-3's twelve cells stay explicit hand-derived fixtures — the cells have non-uniform, opposite answers and the matrix IS the specification; property generation there would re-introduce the shared-expectation-table error the round-6 rule forbids. Property tests quantify over inputs; they do not substitute for the site/predicate derivations above, which quantify over code.

```criteria
id: AC-1
desc: No write/mutate path rebuilds a note from a frontmatter parse that failed, and no legitimate parse loses its ability to write. The test parametrizes over the write paths DERIVED from the package itself — every caller of parse_frontmatter that then re-serializes and writes, today update_fields (base.py:312), update_frontmatter_field (writer.py:247), update_frontmatter_fields (writer.py:286) and roundtrip_file (writer.py:317) — and the derivation is PERFORMED BY THE TEST AT TEST TIME against the live source — an AST scan over a file set the test WALKS rather than names (every .py under obsidian_schemas/, recursively, discovered on disk), never an inspect-based scan (inspect.getmembers/getsource enumerate module OBJECTS, which exist only for modules something imported, so an inspect sweep carries the exact import-graph blind spot AC-3 rejects; it happens to read complete today only because every module in this package is transitively imported, name_validation.py solely via repositories/person.py:22) and never a file set scoped by hand to a directory or a module list (a sixth such caller added in a NEW module beside writer.py is as invisible to a directory-scoped source scan as to the import graph — the frozen list wearing a path), never a hand-derived list frozen at build time: the test asserts its scan finds exactly the paths it then parametrizes over, so a fifth such caller added later is DISCOVERED by the suite going red, not by a human noticing — that forward-looking property is what this clause guarantees, and a check that hardcodes the four names does not satisfy it. The scan's predicate is DATA FLOW, not adjacency — a member is a function in which the dict returned by parse_frontmatter is re-serialized into the bytes that same function writes (base.py:312 -> 324 -> 327-329; writer.py:247 -> 250 -> 253-256, 286 -> 289 -> 292-295, 317 -> 319-322). "Calls parse_frontmatter and later writes" is NOT the predicate and returns a FIFTH function that must not be swept: write_markdown_file (parse at writer.py:186, write at 217) discards the parsed frontmatter (it binds only existing_body, for the WI-126 shrink guard) and builds what it writes from its own entity/frontmatter arguments (writer.py:197-205); its malformed-existing-file behaviour is AC-4's, not this criterion's. The test must therefore prove its scan DISCRIMINATES rather than merely enumerates: write_markdown_file is REACHED by the scan's traversal and REJECTED BY ITS PREDICATE, asserted as a negative case in the same test. A scan that excludes it by name, or that never visits it, does NOT satisfy this criterion — a scan asserted only against the members it returns is indistinguishable from a function that returns those four names, which is the frozen list this clause exists to forbid. For EACH path, on a note whose frontmatter is malformed YAML the call raises a typed ValueError subclass AND the file on disk is byte-identical to before (original content never duplicated into the body, frontmatter never replaced by the partial updates). Conversely, and over the SAME derived path list rather than a subset of it, on a note with genuinely absent frontmatter (parser.py:64-65) NO path raises — each of the four still behaves exactly as it does today, asserted against a baseline captured from the current tree (same return value AND same resulting file bytes), so update_fields and update_frontmatter_field(s) still add the frontmatter and preserve the body, and roundtrip_file still honours its documented contract of preserving all content. Malformed YAML is the ONLY input the raise half licenses; a fix that also raises on absent frontmatter at ANY path in the sweep fails this criterion, and a fix that special-cases absent at some paths but not others fails it too.
kind: test
check: test_no_mutation_writes_through_failed_parse
```

why: this is the keystone — the C2 corruption chain, confirmed live, destroys and duplicates real note content silently; asserting on-disk bytes rather than merely "it raised" is what closes the door, deriving the path list is what stops the fix landing on one of four, and quantifying the absent-frontmatter half over that SAME derived list (not the two paths it originally named) is what stops a builder satisfying the raise-half by making parse_frontmatter refuse everything it cannot hand back a real dict for and then special-casing only the paths the AC happened to check — which would leave update_fields raising on every freshly-created stub and roundtrip_file raising on every frontmatter-less note it normalizes. And pinning the scan's predicate to data flow with a proven negative is what makes "the test performs the derivation" mean something: the loose predicate ("parses, then writes") returns write_markdown_file, which this criterion must not sweep, so a builder running it as written would exclude the fifth member by name — re-freezing the list inside the very scan that was supposed to abolish the frozen list. Requiring the scan to visit that function and reject it on the predicate is the only form the exclusion can take that a future fifth member cannot slip past, and it is the difference between a scan that discriminates and one that recites.

```criteria
id: AC-2
desc: The parse boundaries distinguish failure from a legitimate empty/unknown result, with a case per outcome DERIVED from each function's own branch structure rather than a sampled fixture. For parse_frontmatter that is one case per OUTCOME CLASS, mapped onto the function's actual RETURN SITES — which are NOT in bijection with them and must not be conflated (round-14 finding). Five outcome classes: no leading fence (parser.py:64-65), an opening fence with no closing fence (69-70), a fence present but empty (the safe_load-returns-None normalisation at 74-75), valid frontmatter (77), and YAMLError (78-80). FOUR return sites carry them: parser.py 65, 70, 77 and 80 are the only ast.Return nodes in the function, because the empty-fence class has no return of its own and falls through to site 77, which it SHARES with the valid-frontmatter class. Malformed YAML must never return the same value as a fence-less or empty-fence document, and the legitimate cases must keep returning today's value so existing callers are unchanged. The unclosed-fence case must be classified explicitly as absent or as malformed — not left to default by accident — because append_to_body_section already treats that same input as a distinct malformed-fence case (person.py:1564-1570). For parse_to_model, a known type whose model_validate raised (loud — schema drift) is distinguishable from a legitimately unknown or unmodelled type (returns None as today, parser.py:135-137). Every distinction is observable by the caller, not only in a log line. The return-site enumeration is PERFORMED BY THE TEST AT TEST TIME against the live POST-FIX source — an AST scan of parse_frontmatter for its ast.Return nodes, found by walking the package's module files on disk (the same derived file set AC-1, AC-3 and AC-5 walk; never an inspect-based scan, never a hand-named module) — checked against an explicit in-test map KEYED BY RETURN SITE, where a site maps to ONE OR MORE named outcome classes. Keying the map by outcome class instead FAILS this criterion and is the round-14 finding: five classes against four sites means an entry keyed at 73-75 matches no site the scan can return, the site-set equality assertion goes red on a CORRECT implementation, and the cheap repair — delete the entry with no matching site — silently drops the empty-fence class, which is in this AC precisely because it is a distinct outcome reached through a shared return. So the test asserts BOTH halves: the discovered site set equals the map's keys exactly, AND every named outcome class in the map is exercised by at least one input, so a site carrying two classes cannot be closed with one case. Neither count is the expected answer — four sites and five classes are today's baselines, and this item's own fix changes both (the malformed case stops returning ({}, content), and the unclosed-fence case may gain its own site once classified). A return site the scan finds with no case mapped to it, or a named class no input exercises, FAILS this criterion rather than passing unnoticed. A five-case list frozen at build time does not satisfy it. Same reason as AC-1 and AC-5: an enumeration that is remembered rather than re-run stops being true the first time the function it describes is edited, and this fix edits it. INVOCATION SURFACE (round-14 finding; its derivation corrected round 16): the seam this item makes loud has callers outside the sweeps above, and they are covered by the same derivation discipline — but the derivation is a TRANSITIVE CLOSURE over the call graph, never a direct-caller list. The test computes, at test time by AST over the package's module files walked on disk (the same derived file set AC-1, AC-3 and AC-5 walk), the FIXPOINT of "package functions that REACH parse_frontmatter or parse_to_model": seed the set with the functions that name either symbol directly, then repeatedly add the callers of everything already in the set until it stops growing. Direct-call ADJACENCY is NOT the predicate and cannot return this class — parse_person, parse_company, parse_book and parse_meeting (parser.py:216-237) name neither seam symbol, reaching it only through parse_markdown_content (218, 224, 230, 236), and base._load_file reaches it only through parse_markdown_file (base.py:178) — so an adjacency scan returns nine functions containing none of those five while this criterion's map names four of them as propagating members and one as an insulated loader, which is red on a correct implementation and whose cheap repair deletes the four conveniences that are the whole reason this clause exists (the round-14 keying error, recurring inside round 14's own remedy). The closure STOPS at any function another criterion has already assigned a disposition to, and the STOP SET IS COMPUTED, NEVER NAMED (round-16 finding): it is the union of THREE contributions, each CONSUMED AS THE LIVE OUTPUT of a derivation another criterion's test already runs — those scans reused as inputs, never re-stated as a list here. A live output is only consumable in the domain the closure is computed in, and two of the three are NOT in that domain as their own AC produces them (round-18 audit-fold), so each contribution carries its own conversion and none may be repaired by naming. (i) REFUSING WRITERS: AC-1's data-flow scan output, taken directly — already a set of functions, no conversion. (ii) INSULATED LOADERS: NOT AC-3's output as AC-3 produces it. AC-3's test-time derivation discovers CLASSES (an AST scan for BaseRepository subclasses, checked against its 4x3 matrix's class keys), and a class is not a member of a closure over functions — so consuming AC-3's output literally contributes NOTHING to the stop set, the closure never stops at base._load_file, and it climbs through load(), get_all() and resolve() into every consumer-facing method, which is the unbounded walk the stop rule exists to prevent. The conversion is REQUIRED and belongs to this criterion: resolve each class AC-3 discovers to the function implementing its _load_file through that class's MRO, then DEDUPLICATE, because the map is many-to-one. Four discovered classes resolve to THREE functions today — PersonRepository (person.py:159) and CompanyRepository (company.py:46) declare no _load_file and both resolve to base.py:171, while meeting.py:64 and book.py:57 are their own — so a check asserting one loader per discovered class is RED on a correct implementation (the round-14 keying error in the shape this document has carried since round 5's class/path asymmetry), and both counts are today's baseline, not the answer. (iii) The C3 GUARD: likewise not consumable from AC-4, which runs NO scan at all — it names write_markdown_file and asserts two fixtures — so "AC-4's live output" does not exist, and the only repair available to a builder reading it that way is to hardcode the name, which is the frozen list this clause abolished reappearing inside the clause itself. It IS computed, from a derivation already required to run: AC-1's discrimination proof evaluates TWO predicates over one traversal — the loose "calls parse_frontmatter and later writes" and the data-flow one — and this contribution is their SET DIFFERENCE (loose MINUS data-flow), which is precisely the function AC-1 must REACH and REJECT, today write_markdown_file alone. AC-4 dispositions that function; AC-1's scan derives it; neither names it into this stop set. IDENTITY DOMAIN: all three contributions, and the closure itself, are normalised to ONE source-stable function identity before any set operation — module path plus qualified function name (the function-level half of AC-5's site identity) — never a line number, and never AST nodes for one set against imported objects or classes for another, because a partition asserted across mixed identity domains is vacuously satisfiable: nothing in one domain ever equals anything in another, so the assertion passes while proving nothing. The function names in this document (update_fields, update_frontmatter_field(s), roundtrip_file; base/meeting/book _load_file; write_markdown_file) are today's baseline listing, not the specification; a check that hardcodes them does not satisfy this criterion, because a fifth writer AC-1's scan auto-discovers would fall outside a frozen stop list and either unbound the closure or leave one function claimed by two ACs with incompatible dispositions (refuse vs. propagate). This is the last named set in the document made derived: every other sweep already forbids a hardcoded list, and the stop set is those sweeps' own outputs composed. That is what makes the closure terminate and what makes "exactly one class" well-defined; without the stop rule it climbs through load(), resolve() and every consumer-facing method in the package. PARTITION: the three computed stop sets plus the propagating residue must partition the computed closure EXACTLY, asserted by computation over the normalised identity above — a closure member landing in no class, or in two (the refuse-vs-propagate collision), FAILS this criterion; the partition assertion is what makes the four ACs' sweeps verify each other's boundaries instead of merely coexisting. Because a partition over an empty or mis-domained contribution degenerates into "everything is residue" while still reading green, each of the three contributions must additionally be asserted NON-EMPTY and asserted to be a SUBSET of the computed closure — that is the assertion that catches a loader contribution left as four class objects, and it is why the conversions above are stated as requirements rather than as implementation notes. ONE IMPLEMENTATION (round-18 finding): the derivations this criterion consumes and the derivations their home criteria run are THE SAME CODE, never same-typed reimplementations — the file-set walk, the loose and data-flow write-path scans, the subclass scan and its MRO resolution, and the closure computation live in ONE shared importable scan module, and every consuming test imports it from there; the partition test asserts IMPLEMENTATION IDENTITY (the callables it consumes are the same objects the sibling tests invoke), not merely output-type or output-value agreement. Two independently-written predicates that agree on today's tree can silently diverge on the first future write path, reproducing the exact refuse-vs-propagate collision this composition exists to prevent while every fence reads satisfied — output agreement today is not implementation identity tomorrow; solve-in-one-place applies to the harness. Every member of the closure is classified into exactly ONE of four caller classes: refusing writer (AC-1's data-flow sweep), insulated repository loader (AC-3's per-class except + skip surface), the C3 guard (AC-4's write_markdown_file, which discards the parse), or PROPAGATING PUBLIC PARSE SURFACE — the closure's residue, today exactly six and computed rather than named: parse_markdown_file (parser.py:174-176), parse_markdown_content (201-202) and the four typed conveniences (216-237), none behind a try/except. Six is today's baseline, not the expected answer. The test asserts the computed closure equals the classification map's keys in BOTH directions — a discovered function fitting no class FAILS this criterion, AND a class member the closure does not discover FAILS it too, because the one-directional form is exactly what lets an under-generating scan read as satisfied. For every member of the propagating class: on malformed frontmatter the typed parse error PROPAGATES to the caller — asserted by invoking each DISCOVERED member on the malformed fixture and catching the typed error, never assumed from the call graph — and on absent frontmatter and on a legitimately unknown/unmodelled type each keeps today's return exactly (parse_person on fence-less non-person content returns None today and still does; malformed stops being conflated with either). Export status is stated from source, never from reputation and never from a repository this floor cannot read: __init__ exports parse_frontmatter, parse_markdown_file and ParsedDocument only (__init__.py:35-39, 102-103); parse_markdown_content is README-documented (README.md:160, 176) and exercised by this suite (tests/test_parser.py:13); the four conveniences carry no __init__ export and parse_person is exercised by this suite (tests/test_parser.py:14). Whether any consumer OUTSIDE this repo calls them is NOT asserted here — that audit is cross-repo, unavailable to a hermetic floor, and parked with N4's companion item (Non-goals); claiming it verified would re-import the unverifiable clause the first fold removed. The propagating class is swept regardless, because importable-by-module-path is public.
kind: test
check: test_parse_boundaries_distinguish_failure_from_empty
```

why: C2 and C5 are the same defect one layer apart — a parse failure rendered as the success-shaped value a legitimate empty/unknown case also produces; enumerating the return sites is what makes the property total over the class instead of true for the one fixture someone picked, and it is what surfaced the unclosed-fence case two parts of this package already disagree about. Separating the return sites from the outcome classes is what makes that enumeration runnable rather than merely stated: the function has four `return` statements and five outcomes, so an AC that calls all five "return sites" is red against a faithful scan and green the moment the builder deletes the outcome that has no site of its own — which is the empty-fence case, the one that only exists in the list because it is reached through a shared return. Keying the map by what the scan can return, letting a site carry several classes, and requiring each class its own input is the only shape that keeps both halves honest. And walking the package's files on disk rather than its imported modules is what stops the whole clause resting on a coincidence: every module here is transitively imported today, so an `inspect`-based scan would look complete while proving nothing about the next module nobody wires up. The invocation-surface clause is the round-14 finding folded under totality: the seam's loudness travels to every caller, and the other sweeps each cover a class of caller — writers that refuse (AC-1), loaders that insulate (AC-3), a guard that must not re-swallow (AC-4) — so the remaining class, the public parse functions that neither refuse nor insulate, had to be named and asserted as PROPAGATING, or the item ships a README-documented entry point whose behaviour under the new failure mode nobody specified. Classifying every discovered caller into exactly one class is what makes the coverage claim checkable: a future caller lands in a class or turns the suite red, instead of waiting for a fifteenth red-team round to notice it. And making that sweep a transitive CLOSURE rather than a list of direct callers is what makes it return the members it was written for at all: four of the six propagating functions never name the seam — `parse_person` and its three siblings reach it through `parse_markdown_content`, one call away — so an adjacency scan discovers neither them nor `base._load_file`, leaves four map entries matching nothing, goes red on a faithful implementation, and is repaired by deleting exactly the README-shaped entry points round 14 was raised about. A closure with a stated stop rule (another criterion has already dispositioned this function) terminates, covers them, and keeps "exactly one class" meaningful; asserting the equality in both directions is what stops an under-generating scan from reading as satisfied, which is the same lesson as AC-1's proven negative seen from the other side — a scan has to be shown both to reach what it must classify and to reject what it must not. And spelling out how each stop contribution is *obtained* is what makes "consume the sibling's derivation" executable rather than aspirational: two of the three siblings cannot hand this closure a set of functions as they stand — AC-3 derives classes, and AC-4 derives nothing at all — so a builder reading round 17's clause literally gets an empty stop set from AC-3 (the closure then eats `load()`, `resolve()` and the whole public repository surface) and, from AC-4, nothing to call but the hardcoded name the clause exists to forbid. Naming the MRO resolution and the many-to-one collapse for the loaders, and sourcing the guard from the set difference AC-1's discrimination proof already computes, is what turns the composition into an operation instead of a cross-reference; requiring each contribution to be non-empty and inside the closure is what stops a mis-typed contribution from degrading the partition into a tautology that passes.

```criteria
id: AC-3
desc: A batch load survives a bad note, surfaces it at WARNING (never DEBUG), and surfaces ONLY the notes that repository owns — proven over the COMPLETE derived 4x3 matrix, one worked fixture set PER repository class, each derived from that class's OWN model fields and its OWN _load_file structure (never transposed by hand from a sibling): (1) PersonRepository (inherits base._load_file base.py:171-183, glob @*.md, isinstance-after-construction) — (a) malformed-YAML @-note in its skip surface; (b) own-type-drifted type person + emails "not-a-list" (Person.emails List[str], models.py:81) MUST be listed; (c) foreign readable type (@Acme.md type company) MUST NOT be listed. (2) CompanyRepository (same inherited path and glob, independently instantiated and independently asserted in BOTH directions — sharing code is not sharing proof) — (b) type company + tags "not-a-list" (its only list field is the INHERITED BaseEntity.tags, models.py:40 — derived, not transposed); (a) and (c) mirrored with company-owned fixtures. (3) MeetingRepository (OWN _load_file meeting.py:64-83, glob "Meeting *.md", raw-type prefilter meeting.py:72-75 BEFORE parse_markdown_file, own except meeting.py:81-83) — (a) malformed-YAML "Meeting X.md" listed; (b) type meeting + attendees "not-a-list" (Meeting.attendees List[str]) MUST be listed — this fixture passes the prefilter and fails only inside parse_markdown_file, exercising meeting.py's except under the new failure mode; (c) a "Meeting Y.md" with type person excluded via the prefilter (the naming-convention glob makes strays rare — asserted anyway, reasoning stated). (4) BookRepository (OWN _load_file book.py:57-79, CATCH-ALL glob *.md book.py:49-51, prefilter book.py:67-70, own except book.py:77-79) — (a) a malformed-YAML note of any type under the catch-all glob (the @John.md of fixture (1)(a)) MUST NOT be listed, since neither kind of ownership evidence survives — the glob is not a naming convention and the type is unreadable; (b) type book + tags "not-a-list" (Book declares NO own list field — models.py:159-170 are all str — so the inherited BaseEntity.tags at models.py:40 is the derivation, reached from Book's own field list rather than copied from Company's) MUST be listed, the catch-all glob being irrelevant once the raw type reads "book"; (c) a well-formed foreign note (@Sarah.md type person) MUST NOT be listed, excluded by the prefilter at book.py:70. The twelve cells do NOT share one expectation table and a test that parametrizes over the four classes against a single expected result is wrong by construction — fixture (a) is MUST-be-listed for PersonRepository, CompanyRepository and MeetingRepository (owned by naming convention, the C4 keystone) and MUST-NOT-be-listed for BookRepository alone, while fixture (b) is MUST-be-listed for all four and fixture (c) MUST-NOT-be for all four. The heterogeneous-vault requirement stands (one vault mixing @-notes, Meeting-notes, and bare-titled book notes). For EVERY one of the twelve cells additionally assert NO-ABORT — the fixture's failure is caught inside that class's OWN _load_file and never propagates into BaseRepository.load()'s bare for-loop (base.py:157-165 has NO try/except — one escaped exception aborts the whole batch, the C4/HAL9000-startup regression), so any implementation that narrows meeting.py's or book.py's except clause must still catch the new typed validation failure, and the test proves it per class rather than assuming the base-path result transfers. The CLASS LIST itself is DERIVED BY THE TEST AT TEST TIME, not written into it — and derived at SOURCE level, never from the import graph: the test enumerates the PACKAGE's module files on disk — every .py under obsidian_schemas/, walked recursively, the SAME derived file set AC-1, AC-2 and AC-5 walk, and NOT the repositories/ subdirectory alone (round-14: nothing requires a fifth repository to live under repositories/, and a source scan scoped to a directory is the frozen list wearing a path — as blind to a module outside it as __subclasses__() is to a module nobody imported) — and scans their AST for classes deriving (directly or transitively) from BaseRepository, importing each discovered module itself, and asserts that discovered set equals exactly the classes its matrix holds cells for — so a fifth subclass added later arrives as a key with no entry and turns the suite red, forcing whoever adds it to state its three answers. A runtime __subclasses__()-style check does NOT satisfy this clause (round-12 finding): __subclasses__() sees only classes whose modules happen to be imported by test time, so a fifth repository module not wired into repositories/__init__.py would be silently invisible — reproducing, inside the discovery clause itself, the exact green-suite/zero-coverage gap it exists to close. Concreteness is still decided by the ABC contract (abstract entity_type/type_name, base.py:120-130), but membership is decided by the source on disk. This is the property the Exploration Notes have claimed since round 1 ("a fourth repository joins automatically") and that no check enforced until now; a check that hardcodes the four class names does not satisfy it. Round 6's ruling is untouched: the twelve CELLS stay explicit and hand-derived because their answers are non-uniform and the matrix IS the specification — deriving the class list is precisely what keeps that explicit map from silently going stale. The map is keyed by class, the scan supplies the keys, and an unmapped key FAILS rather than passes.
kind: test
check: test_batch_load_survives_and_surfaces_only_owned_bad_notes
```

why: C4 is the duplicate-creation engine — an invisible note makes resolve() miss and find_or_create_stub mint a dup; a queryable skip-list is required because a log line is exactly the mechanism that already failed, and the schema-drift fixture is required because "unparseable-or-invalid" otherwise reads satisfied while half the same consequence is never exercised at the repository level. That fixture has to be its OWN file, distinct from the foreign-type one, because the two are the same code path with opposite answers: the natural way to exclude a well-formed @Acme.md from PersonRepository's skip-list — "if the model failed to build, it isn't mine" — also excludes an owned @Broken.md carrying type: person with a non-coercible field, which is precisely the note whose disappearance mints the duplicate. One fixture cannot prove both halves; forcing three files and forbidding ownership to be read off model construction is what makes the skip-list mean "these are mine and they need attention" rather than "these are the ones I happened to be able to parse." Deriving the fixture space from each repository's own glob is what stops the surface being trustworthy in the test and noise in production: every repository globs files it does not own and decides ownership downstream of the parse this item makes loud, so on a real heterogeneous vault a naive fix reports every company note as a skipped person, every person note as a skipped company, and every malformed note anywhere in the vault as a skipped book. A signal that cries wolf on day one fails the same way the unread DEBUG line fails, and asserting the surface in both directions — owned bad note present, decidably-foreign note absent — is the only form a single-type fixture cannot fake. Sweeping the four repository CLASSES rather than the three `_load_file` code paths applies that same rule one level out: `PersonRepository` and `CompanyRepository` are two classes sharing one inherited implementation and one glob, and the healthy-vault exposure between them runs both ways, so a test that instantiates only the first proves half a property. The natural implementation — a shared `_owns()` on `BaseRepository` — is precisely the kind that reads `self.type_name` correctly for the class that was exercised while a hardcoded, inverted, or mis-ordered comparison goes unnoticed for the class that was not, which is why the AC counts instantiated classes and not code paths. Writing all twelve cells out rather than parametrizing over four is the same rule once more: the members do not share an answer — `BookRepository`'s malformed-note cell is MUST-NOT-be-listed where the other three are MUST-be-listed — so a sweep with one shared expectation table asserts a uniformity nobody checked, and gets the one member wrong in the direction that floods the surface with every bad note in the vault. And fixture (b) is required from every chair, not just the two whose `_load_file` is `base`'s, because it is the only cell that carries this item's *new* signal through `meeting.py`'s and `book.py`'s own except clauses: those two already prefilter on the raw `type` (meeting.py:72-75, book.py:67-70), so their foreign-type direction is sound today and their own-type-drifted note is the one that reaches code no fixture has ever exercised. The NO-ABORT half is there because `BaseRepository.load()` (base.py:157-165) wraps `_load_file` in no `try`/`except` at all — each class's own clause is the entire safety margin, AC-6 makes narrowing such clauses this item's house style, and a narrowed catch that misses the new typed failure turns "one note skipped" into a dead `BookRepository`/`MeetingRepository` load. That is the startup regression the whole item exists to prevent, so it is asserted per class rather than inferred from the base path passing.

```criteria
id: AC-4
desc: The WI-126 body-shrink guard refuses when it cannot verify, and does not re-swallow the signal AC-1/AC-2 introduce. write_markdown_file's guard (writer.py:184-195) raises rather than setting existing_body = "" for BOTH required fixtures — (a) the existing file's frontmatter is malformed YAML, the coupling case the Constraints section flags as highest-risk, since post-AC-2 parse_frontmatter raises there and today's bare except Exception would re-bury it; and (b) the existing file cannot be read at all (permission or IO error). Naming (a) explicitly is required: a test built only around a generic read error would satisfy the guard's wording while never proving the coupling holds. The except clause is narrowed so neither case reaches existing_body = "", and the guard's refusal is distinguishable from BodyTruncationError.
kind: test
check: test_body_guard_refuses_when_unverifiable
```

why: C3 is the one mechanism protecting against body-wipe turning itself off exactly when it cannot confirm it is safe; it sits directly downstream of parse_frontmatter, so the malformed-YAML fixture is the whole point — without it C3 lands green and silently re-opens C2 on the overwrite path.

```criteria
id: AC-5
desc: Write paths make genuine failure raise while every legitimate no-op keeps its current return value. The test classifies every falsy-return site in the package's write paths and section-read helpers, DERIVED by FOUR predicates rather than by a name list, so a site added later joins the sweep automatically. Predicate 1 is the blanket except Exception in a writer (writer.py:259 and 298; person.py:1500, 1603, 1702, 1775, 1837) - a genuine I/O failure (disk full, torn write, permission denied) raises a typed ValueError subclass, so it can no longer be misread as a no-op and a consumer's existing except ValueError still catches it. Predicate 2 is the frontmatter-fence split (content.startswith("---") followed by split("---", 2)), which yields FIVE sites in person.py rather than the single function earlier rounds named - append_to_body_section (1558-1570), add_to_discuss_item (1675-1683), update_to_discuss_item (1734-1742) and remove_to_discuss_item (1801-1809), where "no fence" and "malformed fence" are pseudo-no-ops that are really failures and move to the raise side for ALL FOUR, so neither can keep returning the same False a legitimate item-not-found returns; plus the read helper _get_body_content (1622-1626), which today falls through to return content and hands its caller the whole file, frontmatter included, as body. Being a read it surfaces rather than raises, but the test must assert a caller can distinguish an unsplittable fence from a genuinely empty body, so get_to_discuss_items can no longer report a broken-fence note as having no items. Predicate 3 is the guaranteed-section insertion writer - a writer that inserts caller-supplied content at a named section marker and returns falsy when the marker is absent - which run over the package yields exactly ONE member, append_to_timeline (marker-absent branch person.py:1482-1484, plus its structurally-dead split guard 1491-1492 - the marker was just confirmed present, so split(timeline_marker, 1) cannot yield fewer than two parts). Disposition (round-9 finding, Dave-ruled 2026-07-24): ACCOMMODATE, not raise - on a note without a "## Timeline" marker the call auto-creates the section, inserts the entry, and returns True with the entry readable back, mirroring the create_if_missing=True default its sibling append_to_body_section already has for the identical ambiguity. The person template guarantees "## Timeline" on package-created notes (body_sections.py:305-306, written by create_stub via get_default_body, person.py:1440), but a raw-content check cannot distinguish "corrupted since creation" from "legitimately never had one" (hand-created in Obsidian, or predating the template convention - the scenario round 6 itself named), so refusal would manufacture a failure out of a structural variant; accommodation eliminates the STRUCTURAL drop - the caller's entry can no longer vanish into the same False the dedup no-op returns because the section was missing - without inventing a new failure mode. Marker-absent must never again return False, and the dedup branch (1476-1478) stays a legitimate no-op with its exact current False. PRESERVATION (round-10 audit-fold, and non-negotiable, because the sibling this disposition mirrors is lossy in exactly the case the disposition serves): the auto-create must leave the note's pre-existing body content ENTIRELY present and its frontmatter BYTE-IDENTICAL, asserted on two fixtures derived from the failure mode of the naive implementation rather than from a convenient note - (i) a person note whose body has NO "## " heading at all (free text only), and (ii) a person note with body text ABOVE its first "## " heading. Both are destroyed today by the sibling's own absent-section route: append_to_body_section with create_if_missing=True calls append_to_section/prepend_to_section (person.py:1586-1593), which are parse_body_sections -> mutate -> write_body_sections (body_sections.py:241-252, 209-220); parse_body_sections keeps ONLY "^## "-delimited spans (body_sections.py:74-97) and returns an empty OrderedDict when there are no headings (76-78), and write_body_sections rebuilds the body from that dict alone (100-134), so fixture (ii) loses its preamble and fixture (i) loses its whole body. Nothing downstream catches it: append_to_timeline and append_to_body_section both write via a raw file_path.write_text (person.py:1495, 1597) and writer.py:178-183 exempts exactly these "section writers" from the WI-126 body-shrink guard (writer.py:184-195) that AC-4 hardens. A fix that satisfies "the entry lands" by routing the absent-section case through today's body_sections round-trip FAILS this criterion. The mechanism is open (string insertion, or making the section round-trip content-preserving - the latter repairs the sibling's identical latent wipe at the same time and is the "solve in one place" answer), and adding a caller-facing create_if_missing-style parameter to append_to_timeline is permitted but NOT required: Dave's ruling is that the default accommodates. Also assert idempotence - after the auto-create, a second call with the same deduplicate_key returns the frozen dedup False and the note holds exactly ONE "## Timeline" section. append_to_body_section is NOT a P3 member (its absent-section behaviour is already an explicit contract governed by create_if_missing), and the To-Discuss match-mutation writers are not members because a falsy return there drops no caller payload (see the no-op half). Predicate 4 is the existence pre-check returning falsy in a writer whose package siblings raise for the same condition - update_frontmatter_field (writer.py:242-243) and update_frontmatter_fields (writer.py:281-282) return False for a missing file where person.py's five writers raise ValueError (e.g. 1469-1470) and base.update_fields raises FileNotFoundError (base.py:305-308); both move to the raise side, converging on the convention the package already has. No-op half - DERIVED by predicate as well, never by a citation list: (a) dedup-key match (append_to_timeline 1476-1478; append_to_body_section 1583-1584) - noting explicitly that append_to_timeline's dedup is WHOLE-FILE (deduplicate_key in content, person.py:1476) while the sibling's is section-scoped, deliberately per person.py:1521-1524, so a key already present in another section still returns False and still writes nothing even on a Timeline-less note; that is frozen by this AC's own backward-compat half and is therefore the ONE remaining falsy path by which an entry does not land, which is why the P3 claim is scoped to STRUCTURAL absence rather than stated as "a drop is impossible"; (b) governed absence - create_if_missing=False with the section absent (append_to_body_section 1578-1579); (c) match-not-found in a match-mutation writer, where a section-absent return is the degenerate case of the named item not being there and no caller payload is dropped (update_to_discuss_item 1746-1747 section-absent and 1759-1761 item-not-found; remove_to_discuss_item 1813-1814 section-absent and 1822-1824 item-not-found). (d) a helper's falsy return that its ONLY caller already makes loud - _get_body_content's missing-file None (person.py 1616-1617), which get_to_discuss_items converts to a ValueError at person.py 1641-1643, so it is already distinguishable at every call site there is. Every (a)-(d) case returns the SAME falsy value it returns today, so an existing caller's `if not repo.append_to_body_section(...)` branch keeps its current meaning. Net contract change is one-directional - no consumer-visible return value changes except where it was reporting a failure as a no-op. CLOSURE - the four derivation predicates are not merely asserted exhaustive, the test PROVES them so, because a predicate list is itself a sample until its universe is enumerated. The test enumerates every return site in the package's write paths and shared section-read helpers that does NOT report a completed write - the falsy returns plus _get_body_content's whole-file fall-through at person.py 1626 - which today is exactly 28 sites (writer.py 243, 260, 282, 299; person.py 1478, 1484, 1492, 1502, 1563, 1570, 1579, 1584, 1607, 1617, 1626, 1681, 1683, 1704, 1740, 1742, 1747, 1761, 1777, 1807, 1809, 1814, 1824, 1839) and nothing else in the package, since company.py, meeting.py and book.py declare no bool-returning writer at all - which is also what makes append_to_timeline P3's only member by enumeration rather than by inspection. Every one of the 28 must fall into exactly ONE of the raise predicates P1, P2 and P4, the accommodate predicate P3, or the no-op classes (a)-(d), and a site matching none of the eight FAILS this criterion rather than passing unnoticed, so the next un-derived predicate arrives as a red test instead of as another red-team round. The enumeration is performed BY THE TEST, AT TEST TIME, against the LIVE POST-FIX source - an AST scan (NEVER inspect-based: inspect enumerates module objects, which exist only for modules something imported, so it carries the identical blind spot AC-3 rejects __subclasses__() for, and reads complete today only because every module in this package happens to be transitively imported) over the package's module files WALKED ON DISK (every .py under obsidian_schemas/, recursively - the same derived file set AC-1, AC-2 and AC-3 walk, and NOT the two modules today's 28 sites happen to live in: a sixth To-Discuss-style writer copy-pasted into a NEW module beside person.py is exactly as invisible to a scan scoped by a hand-written module list as it is to the import graph) for return sites in write paths and shared section-read helpers that do not report a completed write, checked against an explicit in-test classification map (site -> P1/P2/P3/P4/(a)-(d)) keyed by a SOURCE-STABLE site identity - module, plus qualified function name, plus the site's ordinal within that function - never by line number (this fix shifts every line number in person.py, so a line-keyed map turns unrelated edits red) and never by function name alone (append_to_timeline holds four sites landing in three different buckets, so a function-keyed map cannot express the classification at all) - and never a hand-derived list frozen at build time: 28 is today's baseline count, not the expected answer, because the fix itself adds code (P3's accommodation gives append_to_timeline an absent-section branch it does not have today, and any frontmatter-fence split it acquires on the way joins P2 by predicate rather than becoming a 29th silent False), and because the forward-looking guarantee is the point - a sixth To-Discuss-style writer copy-pasted into person.py next month must turn the suite red by appearing in the scan unclassified, not wait for a human to re-read the module; a check that hardcodes the 28 line numbers reads green on that future writer and therefore does not satisfy this criterion. Out of universe by construction, and named so the exclusion is explicit rather than silent - pure predicates (phones_match, person.py 136 and 156) and lookup-miss None returns (person.py 429, 441, 498, 530, 1012, 1065; company.py 114, 134; meeting.py 357, 387; book.py 243, 269), which are AC-2/AC-3 territory - a lookup miss is an answer to a question, not an unreported write.
kind: test
check: test_write_failure_raises_and_noops_keep_their_return
```

why: N4 collapses "your data was skipped on purpose" and "your data was lost" into one bare False. The original wording bundled a cross-repo consumer audit that nothing in this repo can verify — HAL9000 is not in this tree, the floor is hermetic, and no runner is registered here that could lint another repo — so the audit is parked (Non-goals) and replaced by the strongest property that IS provable locally: the no-op returns are frozen, so the only behaviour any existing consumer sees change is a silent data-loss becoming loud. Naming a second derivation predicate rather than one function's branches is what makes that total: the fence-split shape is copy-pasted across four writers, so fixing only the one a prior round happened to cite would leave update_to_discuss_item still reporting a corrupted fence as "nothing matched" — and running the predicate is what exposed the fifth site, a read helper that answers a broken fence by returning the frontmatter as body. The third and fourth predicates are the round-7 re-derivation's, and both are the same lesson at new seams: append_to_timeline's marker-absent False is the only falsy return in the package that silently discards caller-supplied content on a note whose own template guarantees the write target exists — the N4 story in one line, indistinguishable today from "already there, skipped on purpose" — with accommodation rather than raise as its remedy, because round 9 showed a raw-content check cannot tell "corrupted since creation" from "legitimately never had one" while the sibling writer already solves that exact ambiguity with create_if_missing, so P3 converges on the sibling's semantics (the entry lands whatever the note's structure, and no legitimate structural variant is manufactured into a failure). The PRESERVATION half is what makes that convergence safe rather than merely recorded: read at source rather than taken from its contract, the sibling's absent-section route rebuilds the body from `parse_body_sections`, which keeps only `^## `-delimited spans — so it deletes a preamble and destroys a heading-less body outright, on a write path writer.py:178-183 deliberately exempts from the WI-126 body-shrink guard. That is the body-wipe class AC-4 exists to harden, reached by this item's own remedy, and it lands on precisely the hand-created-in-Obsidian note the accommodation was ruled in to serve — so mirroring the sibling naively would trade a silently dropped entry for a silently dropped note body, which is worse than the defect. Pinning the two fixtures that break the naive implementation (heading-less body, preamble body) is what forces the implementation to be content-preserving rather than merely section-creating, and fixing it at the `body_sections` round-trip repairs the sibling's identical latent wipe in the same move. The same read forced the honest scoping of the claim: dedup is whole-file by deliberate design (person.py:1476, 1521-1524) and is frozen by this AC's own backward-compat half, so *structural* absence can no longer drop an entry — a drop is not "impossible", and saying so would have been the kind of overclaim a later round finds. And writer.py's existence pre-checks report as a no-op the exact condition every sibling writer in the package already raises for, so moving them is convergence on an existing convention, not a new contract. Deriving the no-op half by predicate rather than by citation list is what caught the old list being wrong in both directions — one section-absent site mislabeled as item-not-found, one missing entirely — and the match-mutation/insertion distinction is what makes the classification principled rather than curated: a falsy return that drops a caller's payload is a failure, a falsy return that reports "the thing you named is not here" is an answer. The CLOSURE clause is what stops the predicate list itself being the next thing a round finds incomplete: five consecutive rounds ended with the class right and the members short, and each was answered by adding the predicate that round happened to find — which leaves a builder no way to know whether four is the whole count. Enumerating the 28-site universe and requiring every member to land in exactly one bucket converts that from a promise into an assertion, and it is only affordable because the universe is this small: three of the package's four repository modules contain no bool-returning writer at all, so the sweep is a closed set rather than an open-ended hunt. The residue it turned up — `_get_body_content`'s missing-file `None`, already made loud by its only caller — is precisely the kind of case that reads as a gap until someone checks the call site, which is why the count has to come out even rather than approximately.

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

**Given** that same directory, where `Meeting 20260701 - Board.md` has `attendees:` holding one bare name instead of a list, and `Four Thousand Weeks - Oliver Burkeman.md` has `tags: book` where it should be `tags: [book]`, **when** anything loads meetings or books, **then** each load finishes — every other meeting and every other book still comes back, neither repository dies partway through the vault — and each names its *own* broken note: the meeting repo reports the meeting, the book repo reports the book. Both notes plainly say what they are, so both get claimed. **And when** the malformed `@John.md` from the earlier example sits in that same directory, **then** `BookRepository` does not claim it as a book it failed to load, even though its `*.md` glob matched it — it cannot read that file's type, and nothing else about it says "book." A repository claims what it can prove is its own; where it can prove nothing, it stays quiet rather than guessing. The point of the list is that Dave can act on every line of it.

**Given** a person note whose frontmatter fence got truncated, **when** a skill calls `update_to_discuss_item` to tick an item off, **then** it fails loudly — instead of returning the same `False` it returns when the item text simply wasn't found, which would read as "nothing to tick" while the note sat corrupted. **And** `get_to_discuss_items` on that note says the file is unreadable rather than reporting it has no items.

**Given** a person note with no `## Timeline` heading — whether someone hand-deleted it or the note was created by hand in Obsidian and never had one — **when** the exocortex meeting sync calls `append_to_timeline` to record yesterday's meeting, **then** the note gains a `## Timeline` section with the entry in it and the call returns `True` — instead of returning the same `False` it returns when the entry was already there, so the sync believed it deduplicated while the meeting record was silently thrown away. A missing section is no longer a reason for an entry to vanish.

**And given** that the hand-made note is a hand-made note — it opens with a couple of lines of free text before any heading, or has no `##` headings at all, because nobody made it from our template — **when** that same sync adds the Timeline section to it, **then** every word Dave already wrote in that note is still there afterwards, in the same order, with the frontmatter untouched. Gaining a Timeline section must never cost the note its contents: fixing "your meeting note went missing" by losing the page it was going onto is a worse trade than the bug. **And given** a note whose Timeline already contains that entry's dedup key, **when** the sync retries it, **then** it still gets exactly the `False` it gets today, and the note still has exactly one `## Timeline` section.

**Given** a script of Dave's that never touches a Repository — it reads a note it downloaded into a string and calls `parse_markdown_content` on it, the way the README says to, or `parse_person` the way the tests do — **when** that string's frontmatter is malformed YAML, **then** it gets the same loud typed error every write path gets, rather than a document claiming the note has no frontmatter and a body that is quietly the entire file. **And when** the string simply has no frontmatter fence, or is a book where a person was expected, **then** it gets back exactly what it gets today — `None`, an empty frontmatter dict, the whole string as body — because absent and wrong-type were never failures. The parse functions are a supported way in; they do not get a quieter version of the truth than the repositories do.

**Given** someone six months from now — not Dave, not anyone who has read this document — who adds a fifth repository class, or copy-pastes a sixth To-Discuss-style writer into `person.py`, or adds a branch to `parse_frontmatter`, **when** they run the suite, **then** it goes red and names the thing they added and did not classify: a repository with no answers for the three fixtures, a write path in no bucket, a return site with no case. **And given** that they did the ordinary thing and put it in a new file of its own — `repositories/recipe.py`, or a `timeline_writer.py` next to `writer.py` — wiring it into no `__init__.py` and importing it from nothing, **then** the suite still goes red, because the sweeps walk the package's files on disk rather than the modules that happen to be imported or the folder someone expected the code to land in. **And given** they added a branch that reuses an existing `return` rather than writing a new one — the shape the empty-fence case already has — **then** the suite still names it, because a return site is allowed to carry more than one outcome and each outcome has to be exercised on its own. **And given** a new function that reads a note's frontmatter and then writes the file but does not write that frontmatter back — the shape `write_markdown_file` already has — **then** the suite stays green, because the sweep excluded it on what it does, not on its name. **And given** they wrap one of the parse functions in a friendlier helper of their own rather than calling the parser seam directly — the shape `parse_person` already has, one call away from anything that mentions `parse_frontmatter` — **then** the suite still names it, because the caller sweep follows what *reaches* the seam rather than what mentions it. Every finding in this document was caught by a person re-reading the source by hand, twelve times running. The thirteenth should be caught by the tests.

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

## AC Red-Team — 2026-07-24 (re-verify 6)

Re-spawned to verify the fold that followed the round-6 re-verify above (recorded in Exploration
Notes as "Decorrelated AC red-team, round 6"). Read Intent → Examples of done → Problem/Motivation
→ Exploration → Approach → the current ACs (AC-1..AC-6), per Step 2, then re-read the prior fence's
one finding against the current draft. Every code claim below re-read live against the current
tree: `obsidian_schemas/repositories/base.py` (full), `repositories/meeting.py` (full),
`repositories/book.py` (full), `repositories/company.py` (full), `obsidian_schemas/parser.py`
(full), `obsidian_schemas/writer.py` (full), `obsidian_schemas/models.py` (`BaseEntity`, `Person`,
`Company`, `Book`, `Meeting`), `obsidian_schemas/repositories/person.py:1130-1839` (`_known_companies`
plus all six body-section/To-Discuss write paths), `obsidian_schemas/body_sections.py:301-338`
(`ENTITY_BODY_CONFIG`).

### What the fold changed, and what it fixed cleanly

- **MATERIAL (AC-3 named four repository classes but worked fixtures for only two;
  `MeetingRepository` had none, `BookRepository` had only its exclusion direction)** — RESOLVED.
  AC-3 is now the complete derived 4×3 matrix: re-verified live that `MeetingRepository`'s fixture
  (b) — `type: meeting` + `attendees: "not-a-list"` — is a genuine drift fixture, since
  `Meeting.attendees`/`topics` are `List[str]` (`models.py:261-262`, confirmed) and `meeting.py:75`
  prefilters on the raw `type` before `parse_markdown_file` at `meeting.py:78`, so this fixture
  passes the prefilter and reaches `meeting.py`'s own `except Exception` at `meeting.py:81-83` for
  the first time. Same check for `BookRepository`'s fixture (b) — `type: book` + `tags: book`
  (instead of `tags: [book]`) — confirmed `Book` (`models.py:159-170`) declares no field of its own
  typed `List`, so the derivation correctly falls back to the inherited `BaseEntity.tags`
  (`models.py:40`), reaching `book.py`'s own except at `book.py:77-78`. The NO-ABORT assertion is
  now required on all twelve cells, matching the real constraint that `BaseRepository.load()`
  (`base.py:157-165`, re-read live, confirmed still no `try`/`except` around the `_load_file` call)
  gives each class's own `except` zero backup.

### MATERIAL — AC-5 derives its no-op/raise split from two predicates, but a sixth `person.py` write path collapses a third, undered predicate into the same `False` — and AC-5's own Predicate-1 sweep already touches this function without ever inspecting its other branch

AC-5's desc is explicit that its coverage is *derived*, by exactly two predicates: "Predicate 1 is
the blanket `except Exception` in a writer (`writer.py:259` and `298`; `person.py:1500, 1603, 1702,
1775, 1837`)" and "Predicate 2 is the frontmatter-fence split... which yields FIVE sites in
`person.py`... `append_to_body_section` (1558-1570), `add_to_discuss_item` (1675-1683),
`update_to_discuss_item` (1734-1742) and `remove_to_discuss_item` (1801-1809)... plus... —
`_get_body_content` (1622-1626)."

`person.py:1500` — the fifth citation in Predicate 1's own list — is `append_to_timeline`'s except
clause (`person.py:1444-1502`, read in full). That citation proves the fold already looked at this
function once, for Predicate 1. It never looked again for a Predicate-2-shaped collapse local to
*this* function, and there is one: re-read live, `append_to_timeline` does **not** do the
frontmatter-fence split (it never calls `content.startswith("---")`) — it searches the raw file
`content` for the literal substring `"## Timeline"` (`person.py:1481-1484`):

```python
timeline_marker = "## Timeline"
if timeline_marker not in content:
    logger.warning(f"No Timeline section found in {person.name}")
    return False
```

immediately after a *separate* dedup check three lines above (`person.py:1476-1478`):

```python
if deduplicate_key and deduplicate_key in content:
    logger.debug(f"Timeline entry already exists for {person.name}: {deduplicate_key}")
    return False
```

Both return the bare `False` a caller cannot tell apart. This is a **third** pseudo-no-op predicate
— "expected section marker absent from the raw content" — sharing neither Predicate 1's shape
(there's no exception here; both branches return cleanly) nor Predicate 2's (there's no
`"---"`-split; `content` is searched whole, frontmatter included). Because AC-5's derivation is
scoped to exactly two named predicates, a sweep that finds every site matching either one
mechanically stops at four fence-split functions plus one read helper and never reaches this site,
even though the very same function is already on Predicate 1's own citation list.

**Why "missing Timeline section" is not a benign case here, unlike "no To Discuss section" is
for the To-Discuss functions.** Confirmed live in `body_sections.py:303-307`:
`ENTITY_BODY_CONFIG["person"]["default_body"] == "## To Discuss\n\n## Timeline\n\n## Notes\n"` —
every person note created through this package's own `create_stub` (`person.py:1440`,
`self.save(person, body=get_default_body("person"), ...)`) is given a Timeline section
unconditionally. Unlike `append_to_body_section`, which exposes `create_if_missing` so a caller can
explicitly opt out of requiring the section, `append_to_timeline` has no such parameter — it always
assumes the section exists. So on a note produced by this package's own stub-creation path, a
missing `"## Timeline"` marker is not an expected content variation (the way "no To Discuss section"
legitimately is — plenty of people have nothing to discuss); it is exactly the kind of anomaly this
item's defect class targets, and it is returned as the identical `False` a legitimate,
caller-requested dedup skip returns.

**Concrete failure scenario:** a builder implements AC-5 exactly as derived — narrows the five
Predicate-1 `except Exception` blocks (including `append_to_timeline`'s at line 1500) to raise on
genuine I/O failure, and reclassifies the four Predicate-2 fence-split functions' no-fence/
malformed-fence branches to raise. `test_write_failure_raises_and_noops_keep_their_return` passes:
every site named in AC-5's text now behaves as specified. HAL9000's enricher calls
`repo.append_to_timeline(person, meeting_summary, deduplicate_key=meeting_id)` after a call; the
person note's Timeline section was, for whatever reason (a hand-edited note, a note created before
WI-111, a note whose body was directly edited in Obsidian and the heading renamed), missing the
literal string `"## Timeline"`. The call returns `False` — indistinguishable, by AC-5's own
resolved contract, from "already recorded, skip it." The caller's existing `if not
repo.append_to_timeline(...): <treat as already-done>` pattern (the same pattern the doc's own
Approach section describes for the sibling functions) silently drops the meeting summary. Nothing in
the AC set catches this: AC-5's check only exercises the sites its two named predicates produce, and
this function's third branch is neither.

**What would have to change:** derive AC-5's coverage over a third predicate — "an early return
guarding on a required substructure being present in raw content, sitting beside a `deduplicate_key`
dedup check in the same function" — or, more simply, require that `append_to_timeline`'s own
no-Timeline-marker branch (`person.py:1481-1484`) is reclassified the same way the fence-split
functions' no-fence branch was: distinguishable from the dedup no-op it currently shares a return
value with, so a caller can tell "already recorded" from "this note has no Timeline section to write
into." The fix needn't be "raise" (a missing section may be a legitimate state for a hand-created
note, unlike a malformed fence) — but it must stop being the same `False` as the dedup skip, which
is exactly N4's original defect shape one function over.

### What I attacked and found clean

- AC-1's four-path derivation on both halves: re-verified live, `update_fields` (`base.py:278-356`),
  `update_frontmatter_field` (`writer.py:222-260`), `update_frontmatter_fields` (`writer.py:263-299`),
  `roundtrip_file` (`writer.py:302-324`) — unchanged, still the complete set, no regression.
- AC-2's five-return-site coverage of `parse_frontmatter` (`parser.py:64-80`) and the
  known-vs-unknown-type distinction in `parse_to_model` (`parser.py:108-150`): re-read live, both
  unchanged and still total over each function's own branch structure.
- AC-3's complete 4×3 matrix and its NO-ABORT clause: the fold this round verifies — see above. Also
  independently re-verified `company.py` (full file) still defines no `_load_file`, no
  `file_pattern`, no ownership check, confirming `CompanyRepository` still shares `base.py`'s
  code path as the AC assumes.
- AC-4's malformed-YAML-existing-file fixture requirement: re-verified live at `writer.py:184-195`,
  unchanged, still names the coupling case explicitly.
- AC-5's five-site fence-split derivation (Predicate 2) and its five-site blanket-except derivation
  (Predicate 1): both re-verified live and both internally accurate — the gap found above is a third,
  undered predicate, not an error in the two that are named.
- AC-6's single narrowed except clause: re-verified live, `person.py:1147-1160` is still the pre-fix
  bare `except Exception: logger.debug(...)`, as expected pre-build; scope still limited to that one
  clause.
- No new mutually-unsatisfiable pair introduced by this fold.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-24
model: claude-sonnet-5
note: Round-6 fold's complete 4x3 AC-3 matrix (MeetingRepository/BookRepository fixtures + per-cell NO-ABORT) is cleanly resolved and verified against meeting.py/book.py/models.py directly. New MATERIAL finding: AC-5 derives coverage from exactly two named predicates (blanket except; frontmatter-fence split), but append_to_timeline (person.py:1444-1502) — already on Predicate 1's own citation list at line 1500 — collapses a third, undered predicate ("## Timeline" marker absent vs. deduplicate_key match) into the same False, on notes this package's own create_stub guarantees should have that section; nothing in AC-5's text reaches it — still not signable.
```

## AC Red-Team — 2026-07-24 (re-verify 7)

Re-spawned to verify the fold that followed the round-7 re-verify above (recorded as `## AC Red-Team
— 2026-07-24 (re-verify 6)`, the `append_to_timeline` third-predicate finding). The response is
recorded in Exploration Notes as "Decorrelated AC red-team, round 7" (the four-predicate
re-derivation) followed by "Round-8 audit-fold" (a further author self-check that added the CLOSURE
clause and no-op class (d)) — both authored between that fence and this one, per `touched_by:
ideation-partner` and `last_touched: 2026-07-24` in the frontmatter. Read Intent → Examples of done →
Problem/Motivation → Exploration → Approach → the current ACs (AC-1..AC-6), per Step 2, then re-read
the prior fence's finding against the current draft. Every code claim below was re-read live against
the current tree, not trusted from the doc's restatement: full reads of `obsidian_schemas/parser.py`,
`obsidian_schemas/writer.py`, `repositories/base.py`, `repositories/meeting.py`, `repositories/book.py`,
`repositories/company.py`, `repositories/person.py:1130-1840` (`_known_companies` through
`remove_to_discuss_item`), `obsidian_schemas/models.py` (`BaseEntity`, `Person`, `Company`, `Book`,
`Meeting`), and `body_sections.py:298-324` (`ENTITY_BODY_CONFIG`).

### What the fold changed, and what it fixed cleanly

- **MATERIAL (AC-5 derived coverage from two predicates; `append_to_timeline` collapsed a third,
  undered predicate — "## Timeline" marker absent vs. dedup-match — into the same `False`)** —
  RESOLVED, and re-verified beyond the fold's own claim. AC-5 is now an explicit four-predicate
  derivation (P1 blanket-except, P2 fence-split, P3 guaranteed-section-insertion, P4
  existence-pre-check) with a four-class no-op side ((a) dedup, (b) governed absence, (c)
  match-not-found, (d) a helper's falsy return already made loud by its only caller) and a CLOSURE
  clause requiring the test to enumerate the package's complete non-completed-write-return universe
  and land every member in exactly one bucket. I independently re-derived this universe from source
  rather than trusting the doc's count: re-reading `writer.py` in full and `person.py:1444-1839` in
  full, and grepping `company.py`, `meeting.py`, `book.py` for `return False` (zero hits in all
  three, confirmed — neither declares a bool-returning writer), the complete site list is exactly the
  28 AC-5 names — `writer.py` 243, 260, 282, 299 and `person.py` 1478, 1484, 1492, 1502, 1563, 1570,
  1579, 1584, 1607, 1617, 1626, 1681, 1683, 1704, 1740, 1742, 1747, 1761, 1777, 1807, 1809, 1814,
  1824, 1839 — and every one of the 28 matches the exact current-tree line I read it at, including
  the split between except-clause citation lines (e.g. `1500`) and their return-statement lines
  (`1502`) used consistently across P1's five sites. No 29th site found, no cited site found stale.
  `append_to_timeline`'s three branches (dedup at 1476-1478, marker-absent at 1481-1484, the
  structurally-dead `len(parts) != 2` guard at 1490-1492 — confirmed dead: `content.split(marker, 1)`
  on a string just verified to contain `marker` always yields exactly two parts) are now all
  classified, and the `## Timeline` guarantee (`body_sections.py:303-307`, `create_stub` at
  `person.py:1440`) is accurately cited.

### MATERIAL — AC-5's Predicate 3 forces `append_to_timeline`'s marker-absent case to raise unconditionally, but the raw-content check that implements it cannot tell "corrupted since creation by us" from "legitimately never had one" — and the sibling function in the same predicate class handles that exact ambiguity differently

AC-5's Predicate 3 text is unconditional: `append_to_timeline`'s marker-absent branch
(`person.py:1481-1484`) "moves to the raise side" because "the package's own person template
guarantees `## Timeline` exists... so marker-absent is corruption." The tenth Example of done gives
the only worked justification anywhere in the doc for this direction: "The note was created by this
package's own template, which always writes a `## Timeline` section — its absence means the note is
damaged, not that there was nothing to do."

That justification is a claim about **how the note came to exist**, but the mechanism AC-5 specifies
— and the only mechanism `append_to_timeline` could possibly implement, since it takes a `Person` and
a `file_path` and nothing else — is a raw substring check on file content (`person.py:1482`:
`if timeline_marker not in content`). That check cannot observe provenance. It returns the identical
signal for two cases the doc itself has, at different points, both acknowledged as real:

1. **A note this package created, whose `## Timeline` heading was later damaged** — the case the
   Example of done and AC-5's rationale are written for. Raising here is correct.
2. **A note that legitimately never had a `## Timeline` heading** — hand-created directly in
   Obsidian (nothing in `CLAUDE.md` or this package restricts Dave to creating notes only through
   `create_stub`), imported from elsewhere, or predating whatever work item introduced the Timeline
   convention to the person template. The prior fence's own finding (`## AC Red-Team — 2026-07-24
   (re-verify 6)`) named this scenario explicitly and in these words: "a hand-edited note, a note
   created before WI-111, a note whose body was directly edited in Obsidian and the heading
   renamed" — offered there as *why* the collapse mattered, not as a case to be foreclosed. Raising
   here is wrong: there was nothing to do, or nothing repairable by this call, and the caller gets an
   uncaught exception instead of the informative "I couldn't do this" the rest of AC-5 exists to
   provide via a *typed*, catchable signal.

**The sibling in the very same predicate class already solved this ambiguity, and Predicate 3 doesn't reuse the solution.** `append_to_body_section` — cited in AC-5 as governing its own absent-section case via `create_if_missing` (default `True`, `person.py:1511`) rather than via raise-or-silent-no-op — treats "section absent" as a **structural variant to accommodate** (auto-create, or an explicit caller-controlled no-op when `create_if_missing=False`), not as a failure. `append_to_timeline` has no equivalent parameter and no way for a caller to say "this note may legitimately lack a Timeline section; treat that as a no-op or create one" versus "this note should always have one; raise if it doesn't." AC-5 gives every other writer's absence-handling a caller-facing lever and gives this one none, while asserting by narrative (the Example of done) rather than by any code-observable distinction that the marker-absent case is always corruption.

**Concrete failure scenario:** a builder implements AC-5 exactly as specified — `append_to_timeline`'s marker-absent branch raises a typed exception, `test_write_failure_raises_and_noops_keep_their_return` passes because its fixture is (correctly, per the Example of done) a note built via `create_stub` and then hand-damaged. Ship it. HAL9000's exocortex meeting-sync — the doc's own named primary consumer for this exact function (Constraints: "the exocortex meeting sync calls `append_to_timeline`") — runs its normal loop over meeting attendees after a call, as it does today. One attendee's person note predates the Timeline-section convention (a real possibility in a vault this package didn't originate, per the round-6 finding's own naming of that scenario) or was manually created in Obsidian without one. That single call now raises, uncaught, through code the doc's own Constraints section says still does `if not repo.append_to_body_section(...): <treat as no-op>` — the exact pattern this item's Non-goals concedes is unaudited for HAL9000's three consumers and "parked for Dave's call." The difference from the residual risk already accepted there: for every *other* raise conversion in this item (malformed YAML, disk-full, missing file), the parked risk is "a consumer catches too broadly and re-buries a genuine failure" — an acceptable trade because the underlying event really is a failure. Here the parked risk absorbs a case that was never a failure to begin with, on the one function whose failure mode this AC set cannot actually distinguish from a legitimate structural variant using the information available to it.

**What would have to change:** either (a) give `append_to_timeline` the same caller-facing lever `append_to_body_section` already has for the identical ambiguity — e.g. auto-create the `## Timeline` section on insert (mirroring `create_if_missing=True`'s default behavior) rather than raise, so a legitimately-Timeline-less note gains one instead of blocking the call; or (b) if raising is still the chosen mechanism, AC-5 must say why a note-provenance ambiguity that the fix's own rationale (and the prior round's own finding) acknowledges is real doesn't warrant the same opt-out its sibling function has, rather than resting the whole justification on an Example of done whose premise ("the note was created by this package's own template") the runtime check has no way to confirm.

### What I attacked and found clean

- AC-1's four-path derivation on both halves: re-verified live, `update_fields` (`base.py:278-356`),
  `update_frontmatter_field` (`writer.py:222-260`), `update_frontmatter_fields` (`writer.py:263-299`),
  `roundtrip_file` (`writer.py:302-324`) — unchanged since the round-2/4 folds, no regression, still
  the complete derived set (no fifth `parse_frontmatter`-calling write path found).
- AC-2's five-return-site coverage of `parse_frontmatter` (`parser.py:64-80`, re-read: no-fence 64-65,
  unclosed-fence 68-70, empty-fence-via-`None` 72-75, valid 76-77, `YAMLError` 78-80) and the
  known-vs-unknown-type distinction in `parse_to_model` (`parser.py:123-150`): unchanged, still total
  over each function's own branch structure.
- AC-3's complete 4x3 matrix and its NO-ABORT clause: re-verified `BaseRepository.load()`
  (`base.py:142-169`) still wraps `_load_file` in no `try`/`except` at all, and `company.py` (full
  file, re-read) still defines no `_load_file`, no `file_pattern`, no ownership check of any kind —
  the shared-code-path property the matrix depends on still holds.
- AC-4's malformed-YAML-existing-file fixture requirement: re-verified live at `writer.py:184-195`,
  unchanged, still names the coupling case explicitly, `except Exception: existing_body = ""` still
  present pre-build exactly where cited.
- AC-5's Predicate 1/2/4 sites and all four no-op classes: independently re-derived from source (see
  above) and confirmed to match the doc's 28-site enumeration exactly — no error found in the three
  predicates and classes not touched by this round's finding.
- AC-6's single narrowed except clause: re-verified live, `person.py:1147-1160` is still the pre-fix
  bare `except Exception: logger.debug(...)`, as expected pre-build; scope still limited to that one
  clause, no class-quantification exposure.
- No new mutually-unsatisfiable pair introduced by this fold.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-24
model: claude-sonnet-5
note: Round-7/round-8 fold's four-predicate AC-5 derivation + CLOSURE clause is cleanly resolved — independently re-derived the 28-site universe from source and it matches exactly, no stale citation, no missed site. New MATERIAL finding: Predicate 3 forces append_to_timeline's Timeline-marker-absent case to raise unconditionally on a raw-content check that cannot distinguish "corrupted since creation by this package" from "legitimately never had one" (hand-edited in Obsidian, predates the convention — a scenario the round-7 finding itself named), while the sibling append_to_body_section already handles the identical ambiguity via a create_if_missing opt-out that append_to_timeline lacks entirely — still not signable.
```

## AC Red-Team — 2026-07-24 (re-verify 8)

Re-spawned to verify the fold that followed the round-7 re-verify above (recorded as `## AC Red-Team
— 2026-07-24 (re-verify 7)`, the P3 raise-vs-accommodate design finding). The response is recorded in
Exploration Notes as "Decorrelated AC red-team, round 9" (Dave's accommodate ruling) followed by
"Round-10 audit-fold" (the preservation property, since the accommodation mirrors a sibling whose
absent-section route is lossy). Read Intent → Examples of done → Problem/Motivation → Exploration →
Approach → the current ACs (AC-1..AC-6), per Step 2, then re-read the prior fence's finding against
the current draft. Every code claim below re-read live against the current tree:
`obsidian_schemas/repositories/person.py:1444-1610` (`append_to_timeline`, `append_to_body_section` in
full), `obsidian_schemas/body_sections.py:1-260` (`parse_body_sections`, `write_body_sections`,
`prepend_to_section`, `append_to_section`), `obsidian_schemas/writer.py:160-200` (the WI-126 guard and
its guard-exempt comment).

### What the fold changed, and what it fixed cleanly

- **MATERIAL (P3 forced `append_to_timeline`'s marker-absent case to raise unconditionally on a
  raw-content check that cannot distinguish corruption from a legitimately Timeline-less note)** —
  RESOLVED, and the remedy's own risk was independently re-verified rather than trusted. AC-5's P3
  disposition is now ACCOMMODATE: on marker-absent, auto-create `## Timeline` and insert, returning
  `True`. Confirmed live that the mirrored sibling, `append_to_body_section`'s `create_if_missing=True`
  route (`person.py:1586-1593` → `body_sections.py`'s `parse_body_sections`/`write_body_sections`), is
  exactly as lossy as the round-10 fold describes: `parse_body_sections` (`body_sections.py:68-78`)
  keeps only `^## `-delimited spans and returns an empty `OrderedDict` when no heading matches at all,
  and `write_body_sections` (`body_sections.py:117-134`) rebuilds the body from that dict alone — so a
  body with text above its first heading loses the preamble, and a heading-less body is replaced
  outright. AC-5's PRESERVATION clause (pre-existing body entirely present, frontmatter byte-identical,
  proved on a heading-less fixture and a preamble fixture, "a fix that satisfies 'the entry lands' by
  routing... through today's body_sections round-trip FAILS this criterion") correctly forecloses the
  naive mirror. Also confirmed live: both `append_to_timeline` (`person.py:1495`) and
  `append_to_body_section` (`person.py:1597`) write via raw `file_path.write_text`, and
  `writer.py:178-183`'s comment states in as many words that "body-preserving paths... do their own
  read+write and never reach [`write_markdown_file`'s guard], so they are guard-exempt" — confirming
  the WI-126 guard genuinely does not backstop this path, which is what makes the PRESERVATION clause
  non-optional rather than belt-and-suspenders. The corrected "structural absence, not impossibility"
  scoping (dedup remains the one frozen falsy path, per `person.py:1476, 1521-1524`) is stated
  accurately in both AC-5 and the Approach section.

### MATERIAL — AC-5's CLOSURE clause, and AC-1's parallel "a fifth caller joins the sweep automatically" claim, promise a forward-looking completeness property that their `check:` names do not obviously deliver

AC-5's `desc:` states, inside the criteria fence itself (not just the surrounding narrative): "a site
matching none of the eight FAILS this criterion rather than passing unnoticed, **so the next un-derived
predicate arrives as a red test instead of as another red-team round**." AC-1 makes the same shape of
claim: the write-path list is "enumerated from the code, never a hand-picked subset, **so a fifth such
caller added later joins the sweep**." Both are promises about what happens *after* this item ships —
a future PR that adds a 29th silent-`False` site, or a fifth `parse_frontmatter`-calling write path,
should be caught by the test suite this item produces, not merely by a future red-team pass reading the
source by hand (the way every round in this document's own history, including this one, has verified
the doc's counts).

Neither AC's `desc:` says how the `check:` achieves that. The single named check per AC
(`test_write_failure_raises_and_noops_keep_their_return` for AC-5,
`test_no_mutation_writes_through_failed_parse` for AC-1) is a pytest test function — nothing in either
`desc:` requires it to perform live introspection of the current source (e.g., an AST walk of
`writer.py`/`person.py` collecting every `return False`/`return None` not already tagged, or
`inspect`-based discovery of every module-level caller of `parse_frontmatter`) at test-run time, as
opposed to a hand-written enumeration the builder derives once, by reading the code, and bakes into the
test as a fixed list of fixtures/assertions — which is the natural, minimal way to satisfy "the test
enumerates every return site... [and] every one of the 28 must fall into exactly one of...". Every
prior round's own verification method — mine included, above — has been exactly this manual
re-grep-and-recount, never a demonstration that the shipped test performs it automatically.

**Concrete failure scenario:** a builder implements AC-5 by writing 28 individually-cited assertions
(one per site named in the AC's own text, each pinned to a fixture proving its bucket), plus an
assertion that the total is 28. `test_write_failure_raises_and_noops_keep_their_return` passes — it
does classify every currently-named site, and reads as a faithful implementation of the desc. AC-1's
analogous test parametrizes over exactly the four named write paths. Both are shipped. Some time later,
a new work item adds a sixth To-Discuss-style match-mutation writer to `person.py` (copy-pasted from
`update_to_discuss_item`, the exact "N4 shape" this item catalogs as recurring) with the identical
fence-split `False`-collapse this item just finished fixing on its four siblings. Nothing in either
test re-derives the site/path list from the current source, so nothing fails — the new writer's silent
`False` ships exactly as invisible as the original five findings were, and the CLOSURE clause's stated
purpose (catching this as "a red test instead of another red-team round") does not fire, even though
the test suite is green and both ACs read as satisfied.

**What would have to change:** either (a) AC-1 and AC-5 state explicitly that the `check:` must perform
the derivation programmatically against the live source at test time — e.g., an AST/`inspect`-based
scan for the two predicate shapes (calls to `parse_frontmatter` followed by a write, for AC-1; `return
False`/`return None` in the swept modules not covered by an explicit allow-list, for AC-5) — so a new
instance is discovered rather than requiring a human to notice and hand-add it; or (b) if a
build-time-only enumeration (hand-derived once, frozen into the test) is what's actually intended, the
"so a fifth caller joins the sweep" / "so the next un-derived predicate arrives as a red test" language
is an overclaim and should be corrected to describe what the check actually guarantees (completeness as
of build time, verified by the same manual process this red-team has used every round) rather than an
ongoing structural guarantee it does not enforce.

### What I attacked and found clean

- AC-5's P3 accommodate/preservation fold: re-verified live against `body_sections.py` and `person.py`
  as above — the lossy-sibling risk it's designed to close is real and correctly closed.
- AC-2, AC-3, AC-4, AC-6: unchanged since the round-6/7 folds; not re-litigated here as no new code or
  AC text touches them this round, and re-verify 6/7 already confirmed each live.
- Dedup's frozen `False` (`person.py:1476, 1521-1524`) and the "structural absence, not impossibility"
  correction: accurately scoped in both AC-5 and the Approach.
- No new mutually-unsatisfiable pair introduced by this fold.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-24
model: claude-sonnet-5
note: Round-9/10 fold's P3 accommodate-with-preservation is cleanly resolved — re-verified live that the mirrored sibling's body_sections round-trip is exactly as lossy as claimed, and the PRESERVATION clause correctly forecloses it. New MATERIAL finding: AC-5's CLOSURE clause and AC-1's "a fifth caller joins the sweep" claim promise a forward-looking completeness property (a future silent-False/write-path addition gets caught by the test suite, not by a future hand-read) that neither AC's check: requires be delivered by live source-derivation rather than a build-time-frozen hand enumeration — still not signable.
```

## AC Red-Team — 2026-07-24 (re-verify 9)

Re-spawned cold-start to verify the fold that followed the round-8 re-verify above (recorded as
`## AC Red-Team — 2026-07-24 (re-verify 8)`, the forward-looking-completeness finding). The response
is recorded in Exploration Notes as "round 11" (Dave-ruled: checks perform the derivation live) and
"Round-12 audit-fold" (round 11's own remedy re-derived at source: `write_markdown_file` as a proven
negative for AC-1, the same overclaim-shape re-run over AC-2 and AC-3). Read Intent → Examples of
done → Problem/Motivation → Exploration → Approach → the current ACs (AC-1..AC-6), per Step 2, then
re-read the prior fence's finding against the current draft. Every code claim below re-read live
against the current tree, not trusted from the doc: `Grep 'parse_frontmatter\('` across the whole
`obsidian_schemas` package (not just the previously-cited modules), `obsidian_schemas/writer.py:178-220`
(`write_markdown_file` in full), `obsidian_schemas/parser.py:53-81` (`parse_frontmatter` in full),
`obsidian_schemas/repositories/base.py:80-134` (`BaseRepository`'s ABC declaration and abstract
properties), `obsidian_schemas/repositories/__init__.py` (in full).

### What the fold changed, and what it fixed cleanly

- **MATERIAL (AC-5's CLOSURE and AC-1's "a fifth caller joins the sweep" promised a forward-looking
  completeness property with no `check:` requirement that it be delivered by live derivation rather
  than a build-time-frozen hand enumeration)** — RESOLVED for the two ACs the finding named. Round 11
  added the requirement explicitly to both, and round 12 (the audit-fold applying round 11's own
  remedy to itself) found and closed a real gap inside AC-1's new scan predicate: run literally, "callers
  of `parse_frontmatter` that subsequently write" returns FIVE functions, not four — `write_markdown_file`
  (`writer.py:186` parse, `217` write) satisfies that loose predicate too. Re-verified live: `writer.py:186`
  does `_, existing_body = parse_frontmatter(...)` — the frontmatter half is explicitly discarded via `_`,
  used only to compute the WI-126 shrink guard, and the bytes written at `writer.py:217` are built from
  `fm` (`writer.py:198-208`), never from the parsed frontmatter. AC-1 now states the true predicate as
  data flow ("the dict parse_frontmatter returned is re-serialized into the bytes that same function
  writes") and requires `write_markdown_file` be reached by the scan and rejected by the predicate,
  asserted as a negative in the same test — closing exactly the kind of by-name exclusion round 11 was
  meant to abolish. Grepping the whole package (not the subset of modules prior rounds had cited) for
  every `parse_frontmatter(` call site turns up nothing beyond the five already named (`writer.py:186,
  247, 286, 317`; `base.py:312`) plus two purely-read call sites inside `parser.py` itself
  (`parser.py:174` in `parse_markdown_file`, `201` in `parse_markdown_content` — neither writes to disk,
  correctly out of scope for AC-1 by the same data-flow predicate). AC-2's parallel fix (scanning
  `parse_frontmatter`'s own return sites against the post-fix source rather than a frozen five-case list)
  and AC-5's site-key fix (module + qualified function + ordinal, replacing line numbers) are also
  unchanged since round 12 and, on inspection, correctly worded — no regression.

### MATERIAL — AC-3's live class-list derivation is specified as a runtime `__subclasses__()`-style check, which silently fails to discover exactly the scenario it exists to catch

AC-3's round-12 addition reads: "the test discovers the concrete `BaseRepository` subclasses from the
live package (`BaseRepository` is an ABC whose `entity_type` and `type_name` are abstract properties,
`base.py:120-130`, so concreteness is decidable **at runtime**) and asserts that discovered set equals
exactly the classes its matrix holds cells for... a fifth subclass added later arrives as a key with no
entry and turns the suite red." Re-verified live: `base.py:80` is `class BaseRepository(ABC,
Generic[T])`, and `entity_type`/`type_name` are `@property @abstractmethod` at `base.py:120-130` —
the doc's premise is accurate. But "decidable at runtime" describes exactly one mechanism —
`BaseRepository.__subclasses__()` (optionally filtered through `inspect.isabstract`) — and that
mechanism has a specific, well-known Python gap AC-3's text never addresses: a class is only registered
as a subclass once its `class Foo(BaseRepository[...]):` statement has actually **executed**, i.e. once
the module defining it has been imported somewhere in the process. `__subclasses__()` does not scan the
filesystem or the package; it reads a list Python already built from import side effects.

Confirmed live in `repositories/__init__.py` (read in full): today it eagerly imports all four —
`from .person import PersonRepository`, `.company`, `.book`, `.meeting` — which is precisely why a
`__subclasses__()`-based scan would find all four right now and read as satisfying AC-3. That is also
what hides the gap: the mechanism works today for reasons that have nothing to do with the property
AC-3 claims to guarantee.

**Concrete failure scenario:** a builder implements AC-3's class-list derivation as
`BaseRepository.__subclasses__()` filtered to non-abstract members — the direct, minimal reading of "the
test discovers the concrete `BaseRepository` subclasses... concreteness is decidable at runtime," with
no AST alternative offered anywhere in AC-3's text (unlike AC-1, AC-2 and AC-5, which all explicitly name
"AST or inspect-based scan" as the mechanism). The test passes today: four subclasses, four matrix keys,
matched. Six months from now someone adds `RecipeRepository(BaseRepository[Recipe])` in a new
`repositories/recipe.py` — a plausible, ordinary way to add a fifth repository, and not obviously wrong,
since nothing forces a new module to also touch `__init__.py`. If `recipe.py` is not imported by
`repositories/__init__.py` (the exact omission a builder adding a new isolated module is likely to make)
and nothing else in the test suite imports it before the class-list scan runs, `RecipeRepository` is
never registered on `BaseRepository.__subclasses__()` at test time — regardless of whether the test
imports `obsidian_schemas.repositories` for `PersonRepository` etc., because subclass registration is
per-module, not per-package. The scan finds the same four classes it found before, the discovered set
still equals the four-key matrix, and the suite stays green. This is not "a fifth key with no entry
turning the suite red" — it is the fifth repository shipping with **zero** AC-3 coverage while every AC
reads satisfied, the identical silent-gap shape the whole item exists to close, now reproduced inside the
very clause round 11/12 added to prevent it.

**What would have to change:** require AC-3's class-list derivation to be AST/source-scan-based —
walk the `repositories/` package's `.py` files on disk for `class X(BaseRepository...)` (or
`class X(BaseRepository[...]):`) definitions, matching AC-1/AC-2/AC-5's own AST approach — rather than
runtime `__subclasses__()`, which is import-order-dependent and therefore not actually "decidable" from
the class hierarchy alone. If a runtime mechanism is kept, AC-3 must additionally require the test to
force-import every module under `repositories/` first (e.g. `pkgutil.walk_packages` + `importlib.import_module`
over the package, not merely `import obsidian_schemas.repositories`) and assert that step happens, or the
"a fifth subclass added later joins automatically" guarantee is not actually guaranteed. The same caveat
applies wherever AC-1/AC-2/AC-5 permit "inspect-based" as an alternative to "AST": an inspect-based scan
inherits the identical import-completeness gap; AST is the only one of the two that is genuinely immune,
so the "AST or inspect-based" framing across all four ACs should read as "AST (preferred) or an
inspect-based scan that first forces-imports every module in the swept surface."

### What I attacked and found clean

- AC-1's `write_markdown_file`-as-proven-negative and its data-flow predicate: re-verified live against
  `writer.py:178-220` and the full-package grep for `parse_frontmatter(` — the five-caller set (four
  positive, one negative) is exactly complete; no sixth caller found anywhere in the package.
- AC-2's post-fix return-site scan: re-verified `parse_frontmatter`'s five current return sites
  (`parser.py:64-65, 69-70, 73-75, 77, 78-80`) match the doc's citations exactly; the AC's own framing
  (five is a baseline, not the answer, since the fix changes the branch structure) is accurate given the
  malformed branch is slated to stop returning a value at all.
- AC-3's twelve non-uniform cells and the NO-ABORT clause: unchanged since round 6/7's folds, not
  re-litigated here as no new text touches them this round — only the class-list derivation clause is
  new, and that is the finding above.
- AC-5's site-key change (module + qualified function + ordinal, replacing line numbers): text-only
  clarification, internally consistent with the round-10/11 CLOSURE requirements; no regression.
- AC-4, AC-6: unchanged since round 4/6's folds; not re-litigated here as no new code or AC text touches
  them this round.
- No new mutually-unsatisfiable pair introduced by this fold.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-24
model: claude-sonnet-5
note: Round-11/12 fold's forward-looking-completeness fix is cleanly resolved for AC-1 (write_markdown_file confirmed a proven negative via live data-flow re-check) and AC-2/AC-5 (unchanged, still accurate). New MATERIAL finding: AC-3's own class-list derivation, specified as "decidable at runtime" (a __subclasses__()-style check) rather than AST-based like its siblings, silently fails to discover a fifth repository module that isn't imported by repositories/__init__.py by test time — reproducing, inside the very clause added to prevent silent gaps, the exact silent-gap shape (suite stays green, new class ships with zero AC-3 coverage) this item exists to close — still not signable.
```

## AC Red-Team — 2026-07-24 (re-verify 10)

Re-spawned cold-start to verify the fold that followed the round-9 re-verify above (recorded as
`## AC Red-Team — 2026-07-24 (re-verify 9)`, the AST-vs-`__subclasses__()` finding). The response is
recorded in Exploration Notes as "round 13" (Dave-ruled: all four sweeps discover from source, never
the import graph) and "Round-14 audit-fold" (round 13's own remedy re-derived at source: AC-1/AC-5
still permitted "inspect-based" as an alternative, three of the four scans hand-wrote their file set,
and AC-2's map was keyed to a return site that doesn't exist for one of its five outcome classes). Read
Problem/Motivation → Intent → Exploration Notes in full (all fourteen rounds) → Non-goals → Approach →
the current ACs (AC-1..AC-6) → Examples of done → Relationship to other work → this section's own prior
history, per Step 2's spirit (Intent read before the ACs, ACs read last, not anchored to the author's
framing). Every code claim below was re-read live against the current tree, not trusted from the doc —
`obsidian_schemas/parser.py` in full, `writer.py:160-325` in full, `repositories/base.py:1-340`,
`repositories/company.py`, `repositories/meeting.py:1-95`, `repositories/book.py:1-85`,
`repositories/person.py:1120-1840`, `body_sections.py:60-200`, `models.py:20-170`, `README.md:140-180`,
`obsidian_schemas/__init__.py`, and `tests/test_parser.py` — a full-package `Grep` for
`parse_markdown_content` was also run, not assumed from the doc's own citation of it.

### What the fold changed, and what it fixed cleanly

Re-verified live, all three round-14 fixes hold exactly as claimed:

- **AC-3's class-list derivation is now AST-over-disk, not `__subclasses__()`.** AC-3's text: "derived at
  SOURCE level, never from the import graph... A runtime `__subclasses__()`-style check does NOT satisfy
  this clause." Confirmed the underlying facts are unchanged since re-verify 9 — `base.py:80` is
  `class BaseRepository(ABC, Generic[T])`, `company.py` overrides neither `_load_file` nor `file_pattern`
  (read in full) — and the fix now matches its own siblings' mechanism.
- **AC-1 and AC-5 no longer permit an inspect-based scan as an alternative to AST.** AC-1: "never an
  inspect-based scan (`inspect.getmembers`/`getsource` enumerate module OBJECTS, which exist only for
  modules something imported...)". AC-5: "AST scan (NEVER inspect-based: inspect enumerates module
  objects...)". Both now read uniformly with AC-2/AC-3.
- **All four ACs now walk the same derived file set** ("every `.py` under `obsidian_schemas/`,
  recursively") rather than a directory or a hand-named module list — confirmed in AC-1, AC-2 (by
  cross-reference), AC-3, and AC-5's text.
- **AC-2's site/class keying bug is fixed.** Re-verified `parse_frontmatter` (`parser.py:53-80`) live: it
  has exactly four `ast.Return` nodes — lines 65, 70, 77, 80 — and the `safe_load`-returns-`None`
  normalisation at 73-75 has no return of its own, falling through to share site 77 with the
  valid-frontmatter case. AC-2 now keys its map by return site, allows a site to carry more than one
  outcome class, and requires every named class be separately exercised — the fix precisely closes the
  gap round 14 found (five classes, four sites, no longer conflated).

### MATERIAL — an uncovered invocation layer: `parse_frontmatter`'s public callers outside any write path or repository load are never assigned a behaviour, and the doc's own backward-compat framing says this can't happen

The Approach section states the mechanism plainly: "the fix belongs at the seam: `parse_frontmatter`
must stop conflating 'absent' with 'malformed,' and let each caller choose. That single decision
cascades to four of the five findings" — i.e., the loud signal originates once, inside
`parse_frontmatter` itself, and every caller inherits it. AC-1 enumerates and pins behaviour for the
four write callers (`update_fields`, `update_frontmatter_field`, `update_frontmatter_fields`,
`roundtrip_file`), with `write_markdown_file` carved out by name as the negative case AC-4 owns. AC-3
enumerates and pins behaviour for the read side, but *only* for the four concrete `BaseRepository`
subclasses' `_load_file` methods.

Neither sweep — nor AC-2, AC-4, AC-5, or AC-6 — reaches `parse_frontmatter`'s other callers, and there
are more of them than the doc has ever named. Re-read live: `parse_markdown_file` (`parser.py:153-184`,
parse at 174) and `parse_markdown_content` (`parser.py:187-210`, parse at 201) are two *separate*
publicly-reachable read entry points, neither behind any `try`/`except` of its own — a raise from
`parse_frontmatter` propagates straight out of both, uncaught, to whatever calls them.
`parse_markdown_file` is at least swept as a read path via `base._load_file`, `meeting._load_file`,
`book._load_file` (all three wrap the call in their own `except`). `parse_markdown_content` is not: its
only callers inside the package are the four convenience functions `parse_person`, `parse_company`,
`parse_book`, `parse_meeting` (`parser.py:216-237`), each a two-line wrapper with **no**
`try`/`except` at all — `doc = parse_markdown_content(content, Person); return doc.entity if
isinstance(doc.entity, Person) else None`. None of the four is a write path (nothing here writes to
disk — confirmed by reading all four in full) and none is a `BaseRepository` subclass method, so neither
AC-1's data-flow predicate nor AC-3's class sweep can ever discover them; they are invisible to both
derivations by construction, not merely unlisted.

These are not obscure internals. `parse_frontmatter` itself is exported at the package's top level
(`obsidian_schemas/__init__.py:36,102` — `from obsidian_schemas.parser import parse_frontmatter` /
`"parse_frontmatter"` in `__all__`), and `README.md:156-179` documents exactly this call shape under
"Parsing Content Strings" — `from obsidian_schemas.parser import parse_markdown_content; doc =
parse_markdown_content(content)` — as the supported way to parse a raw content string that did **not**
come from a vault file via a Repository. `tests/test_parser.py` imports and exercises `parse_person`
directly (line 14). This project's own CLAUDE.md lists HAL9000, Exocortex and orchestrator as consumers
of "Parser/writer for markdown frontmatter" specifically — i.e. of this surface, not only of the
Repository classes.

**Concrete failure scenario.** A builder implements exactly what AC-1/AC-2 specify: `parse_frontmatter`
raises a typed `FrontmatterParseError(ValueError)` when the YAML between the fences fails to parse — the
natural, in fact the only economical, way to give all four AC-1 write paths the same raise without
duplicating detection logic at each call site, and the seam fix the Approach section itself argues for.
Every named check passes: AC-1 through AC-6 are all green. But `parse_frontmatter(content)` called
directly by an external consumer, `parse_markdown_content(content)`, and all four of `parse_person`,
`parse_company`, `parse_book`, `parse_meeting` — called exactly the way `README.md`'s own example shows,
on a raw string that is not necessarily a vault file at all — now raise uncaught on malformed YAML where
today they return `({}, content)` / `None`. A caller written against the documented contract (`doc.entity
is None on failure`, per every one of the four convenience functions' own bodies) gets an unhandled
exception in production instead. Nothing in this item's test suite, Examples of done, or the Constraints
section's own accounting ever exercises this path, because nothing in the doc has ever named it.

This is the exact shape the role exists to hunt (WI-099/WI-100's "an uncovered invocation layer" — the
ACs cover the function `parse_frontmatter` in exhaustive, AST-derived detail, but nothing covers three of
the surfaces that call it), and it directly contradicts a specific claim already in the doc: Constraints
states "N4 is a return-contract change — **the one place backward-compat bites**... the only finding that
is not purely internal." That sentence is false the moment AC-1/AC-2 land as specified — the seam fix
changes an exported, README-documented function's observable behaviour on bad input with zero
backward-compat treatment, zero consumer accounting (contrast AC-5's careful "no consumer-visible return
value changes except where it was reporting a failure as a no-op"), and zero test coverage.

**What would have to change:** either (a) scope the raise explicitly — state that `parse_frontmatter`'s
loud signal is surfaced only through the four AC-1 write paths and the AC-3 repository read paths, and
that `parse_markdown_content`/`parse_person`/`parse_company`/`parse_book`/`parse_meeting` keep today's
tuple/`None`-returning contract on malformed input (making them a third, explicitly-named "survive but
surface silently by design" bucket, parallel to but distinct from AC-3's queryable-skip-list bucket, with
its own fixture proving the old behaviour is preserved) — or (b) add these five functions to a sweep (an
AC, or an extension of AC-1/AC-3's derived-caller lists) that requires them to raise the same typed error
and pins that as an intentional, tested, README-updating contract change, parked alongside N4's HAL9000
companion item if their external consumers can't be audited from this repo. Either way, the Constraints
section's "N4 is the only finding that is not purely internal" needs correcting — it is no longer true
once AC-1/AC-2 ship as currently specified.

### What I attacked and found clean

- AC-1's write-path sweep and `write_markdown_file`-as-proven-negative: re-verified live against
  `writer.py:160-325` and `base.py:278-339` — `update_fields` (parse 312, write 329),
  `update_frontmatter_field` (parse 247, write 256), `update_frontmatter_fields` (parse 286, write 295),
  `roundtrip_file` (parse 317, write 322) all re-serialize the parsed dict into what they write;
  `write_markdown_file` (parse 186, write 217) discards it via `_, existing_body = parse_frontmatter(...)`
  and builds its output from `fm` (198-208) — the data-flow predicate is exactly as claimed.
- AC-2's four-return-site/five-outcome-class split: re-verified live against `parser.py:53-80` — exact
  line match (65, 70, 77, 80; the empty-fence normalisation at 73-75 has no return of its own).
- AC-3's 4×3 matrix citations: re-verified live against `base.py:80-183` (no type check, `isinstance`
  ownership at 179, `load()`'s bare `for` loop at 157-165 with no `try`/`except` around `_load_file`),
  `company.py` (no `_load_file`/`file_pattern` override, confirmed reading the whole file),
  `meeting.py:64-83` (raw-type prefilter at 75, own `except` at 81-83), `book.py:57-79` (catch-all glob
  at 49-51, prefilter at 70, own `except` at 77-79), and `models.py` (`extra="allow"` at 31-32,
  `Person.type`/`emails` at 78/81, `Company.type` at 127, `BaseEntity.tags` at 40, `Meeting.attendees`/
  `topics` at 261-262, `Book`'s fields all `str` at 159-170) — every citation exact.
- AC-4's guard fixture and AC-6's `_known_companies` narrowing: re-verified live against
  `writer.py:178-195` and `person.py:1131-1161` — both match the doc's description exactly (the guard's
  `except Exception: existing_body = ""` at 189-190; `_known_companies`' blanket `except Exception` at
  1156 degrading to DEBUG at 1157-1160).
- AC-5's 28-site enumeration: independently re-counted, not merely re-cited — every one of the 28 line
  numbers in `writer.py` (243, 260, 282, 299) and `person.py` (1478, 1484, 1492, 1502, 1563, 1570, 1579,
  1584, 1607, 1617, 1626, 1681, 1683, 1704, 1740, 1742, 1747, 1761, 1777, 1807, 1809, 1814, 1824, 1839)
  matches a `return False`/`return None` at exactly that line, classified exactly as the doc's predicate
  assigns it (P1/P2/P3/P4/(a)-(d)); no 29th site found and no cited site found wrongly classified.
- AC-5's PRESERVATION clause: re-verified live against `body_sections.py:60-134` —
  `parse_body_sections` keeps only `^## `-delimited spans and returns an empty `OrderedDict` on no match
  (68-78), `write_body_sections` rebuilds solely from that dict (100-134); the lossy-mirror risk is real
  and the clause correctly forecloses it.
- No new mutually-unsatisfiable AC pair; no regression in any of the round 1-14 folds' prior fixes.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-24
model: claude-sonnet-5
note: Round-13/14 fold's AST-uniformity and AC-2 site/class-keying fixes are cleanly resolved — independently re-derived live (parser.py's 4 return sites, the 28-site AC-5 universe, the 4x3 AC-3 matrix citations) with zero discrepancies. New MATERIAL finding: parse_frontmatter's loud-seam change cascades to parse_markdown_content and the four public parse_person/company/book/meeting convenience functions (parser.py:216-237, none behind a try/except, all README-documented and package-exported), which no AC's derived sweep can discover since they are neither AC-1 write paths nor AC-3 repository _load_file overrides — an uncovered invocation layer that also falsifies the Constraints section's own claim that N4 is "the only finding that is not purely internal" — still not signable.
```

## AC Red-Team — 2026-07-24 (re-verify 11)

Decorrelated cold-start pass over round 15's committed fold and round 16's uncommitted audit-fold (the
working-tree diff against HEAD `1ab054c` — five hunks, all inside the History narrative, `## Approach`,
and AC-2's `desc:`/`why:` fields; no `## AC Red-Team` section touched). Read in order: Intent, Problem/
Motivation, Exploration Notes (including every prior red-team and audit-fold subsection), Approach,
Acceptance Criteria, Examples of done, Relationship to other work — then the code: `parser.py` in full,
`obsidian_schemas/__init__.py:1-45`, `repositories/base.py`, `repositories/meeting.py`,
`repositories/book.py`, `writer.py`, `tests/test_parser.py:1-20`, plus a package-wide grep for all eight
parse-seam symbols to independently recompute the closure round 16 claims, rather than trust its prose.

### What the round-15/16 folds changed, and what re-derived clean

Round 16's core factual claims about the transitive closure hold under independent re-computation. Grepping
every call site of `parse_frontmatter`/`parse_to_model`/`parse_markdown_file`/`parse_markdown_content`/
`parse_person`/`parse_company`/`parse_book`/`parse_meeting` across `obsidian_schemas/**/*.py` gives exactly
the level-1 set round 16 names (`parse_markdown_file`, `parse_markdown_content`, `write_markdown_file`,
`update_frontmatter_field`, `update_frontmatter_fields`, `roundtrip_file`, `update_fields`,
`meeting._load_file` — via its own direct prefilter call at `meeting.py:72`, not only through
`parse_markdown_file` — and `book._load_file`, same shape at `book.py:67`); level 2 adds exactly
`base._load_file` (via `parse_markdown_file`, `base.py:178` — it has no direct call of its own, unlike its
meeting/book siblings) and the four conveniences (via `parse_markdown_content`, `parser.py:218/224/230/236`);
level 3 is empty — no other package file calls `parse_person`/`parse_company`/`parse_book`/`parse_meeting`.
That is exactly the six-member propagating residue AC-2 now claims, computed independently rather than
re-read. The export claims are also exact: `__init__.py:35-39` imports only `parse_frontmatter`,
`parse_markdown_file`, `ParsedDocument`; `tests/test_parser.py:13-14` imports `parse_markdown_content` and
`parse_person` verbatim as cited. The retired "verified against HAL9000 and exocortex source" clause is
correctly gone from AC-2 with no replacement claim standing in its place.

### MATERIAL — AC-2's closure STOP RULE is the one derived set in this document not required to be derived

Every other swept set in this AC file is pinned, repeatedly and explicitly, against being satisfied by a
hardcoded list: AC-1 ("a check that hardcodes the four names does not satisfy it"), AC-3 ("a check that
hardcodes the four class names does not satisfy it"), AC-5 ("a check that hardcodes the 28 line numbers
… does not satisfy this criterion"), and AC-2's own return-site half ("A five-case list frozen at build
time does not satisfy it"). Round 16's fix to AC-2's invocation-surface half introduces a second derived
artifact the closure depends on — the STOP SET that halts the fixpoint — and neither the round-16 narrative
nor the AC-2 `desc:` text states that this set must itself be computed live from AC-1's and AC-3's own
derivations, rather than named. The text: *"The closure STOPS at any function another criterion has
already assigned a disposition to — AC-1's data-flow write set (update_fields, update_frontmatter_field,
update_frontmatter_fields, roundtrip_file), AC-3's per-class `_load_file` set (base, meeting, book),
AC-4's `write_markdown_file`"* — lists eight concrete names in parentheses and never says "computed by
invoking AC-1's/AC-3's own scan function" or forbids a hardcoded stop-list the way every sibling clause
forbids one for its own swept set. Read literally, a test that hardcodes those eight names as the stop
condition satisfies AC-2 exactly as written today.

**Concrete failure scenario.** A builder implements AC-2's closure with the stop set as a literal frozen
tuple of the eight names quoted above (which is what a plain reading of the clause licenses, and it
reproduces today's six-member residue correctly — the test is green at ship time). AC-1's own scan is
separately, correctly, designed to auto-discover a future fifth write path (round 11/12's guarantee). Six
months later a fifth caller of `parse_frontmatter` that re-serializes and writes — say
`merge_frontmatter_field` — lands in a new module. AC-1's live derivation picks it up automatically and
requires it to refuse (raise) on malformed input, exactly as designed. AC-2's closure, whose stop set is
still the frozen eight names, does not recognize `merge_frontmatter_field` as already-dispositioned: the
fixpoint either climbs past it into whatever calls it (reproducing the "climbs through `load()`, `resolve()`
… every consumer-facing method" blowup round 16's own prose says the stop rule exists to prevent), or, if
nothing calls it, the closure adds it to its own residue as an undispositioned "propagating" member — at
which point AC-2 asserts `merge_frontmatter_field` PROPAGATES the typed error to its caller, while AC-1
simultaneously asserts the same function REFUSES (raises without depending on a caller to observe it) —
two acceptance criteria requiring incompatible behaviour of the same function, the WI-139 mutually-
unsatisfiable-AC shape, reached only once a function nobody has written yet gets added, so nothing in the
suite today can catch it. This is round 11's own rule ("a completeness claim is only as durable as the
process that re-checks it — the check must run the derivation, not remember its output") applying to the
closure's own boundary condition, one level upstream of the six-member set that rule was written to protect.

**What would have to change.** State explicitly, in AC-2's `desc:`, that the stop set is computed at AC-2's
test time by invoking (or replicating) AC-1's data-flow scan and AC-3's per-class `_load_file` scan
directly — never by naming their current membership — mirroring the "same derived file set AC-1, AC-3 and
AC-5 walk" pattern this AC already uses for the file-walk half of its own derivation. `AC-4`'s single named
function (`write_markdown_file`) is not itself a derived sweep and may stay named, since AC-4 doesn't
enumerate a class.

### What I attacked and found clean

- Independently recomputed the six-member propagating residue from source (above) rather than trusting
  round 16's restatement of it — exact match, including the two members (`meeting._load_file`,
  `book._load_file`) round 16's own prose correctly places at level 1 via their direct prefilter calls
  rather than only through `parse_markdown_file`.
- Verified `base._load_file` has no direct call to `parse_frontmatter`/`parse_to_model` of its own
  (`base.py:171-183`) — it is a level-2 member exclusively through `parse_markdown_file`, as claimed.
- Verified the export/consumer claims in AC-2's revised text against `__init__.py` and
  `tests/test_parser.py` line-for-line; no overclaim survives this round's rewrite.
- Checked the "level 3 empty" claim (no package function calls the four conveniences) against the same
  package-wide grep — holds.
- Read the "script of Dave's" and "wrap one of the parse functions in a friendlier helper" additions to
  Examples of done against AC-2's propagating-class disposition — consistent, no drift from Intent.
- No regression found in any round 1-15 fold's prior fixes (AC-1 data-flow predicate, AC-3's 4×3 matrix,
  AC-4/AC-5/AC-6) — round 16's diff touches only the History narrative, `## Approach`'s closure clause and
  AC-2's `desc:`/`why:` fields.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-24
model: claude-sonnet-5
note: Round 16's fix to AC-2 (adjacency scan -> transitive closure) is factually sound — independently recomputed the six-member propagating residue from source (package-wide grep of all eight parse-seam symbols) and it matches exactly, including meeting._load_file/book._load_file's direct-call classification. New MATERIAL finding one level up: the closure's own STOP SET (AC-1's write set, AC-3's loader set, AC-4's guard) is named by example in AC-2's text rather than required to be computed live from AC-1's/AC-3's own derivations, unlike every other swept set in this document (all of which explicitly forbid a hardcoded list) -- so a future write path or loader AC-1/AC-3 auto-discovers can silently fall outside AC-2's frozen stop-list, producing either an unbounded closure or two ACs asserting incompatible dispositions (refuse vs. propagate) for the same function -- still not signable.
```

## AC Red-Team — 2026-07-24 (re-verify 12)

Decorrelated cold-start pass over the round-17 fold (committed, `a57c453`, "the stop set is computed,
never named — criteria consume each other's derivations; partition asserted") and the round-18 audit-fold
layered on top of it in the working tree (uncommitted at spawn time — `git status` shows only this file
modified). Read in full, in order: Intent, Problem/Motivation, Exploration Notes end to end (every prior
fold and audit-fold subsection, rounds 1–18), Approach, Acceptance Criteria (AC-1 through AC-6, all
`desc:`/`why:` text), Examples of done, Relationship to other work — then every prior `## AC Red-Team`
section, all eleven re-verifies, to confirm this round is not re-litigating a settled finding. No shell/git
diff tool was available in this environment, so the round-17→18 change was located by reading the
Exploration Notes' own fold narratives (lines 393–413) against the live AC-2 `desc:` text, not inferred from
a diff.

### What round 17 and the round-18 audit-fold got right, re-verified

Round 17's composition move is the correct next step on this document's own ladder: once every other swept
set in this file was pinned against a hardcoded list, the closure's stop set was the last named set standing,
and naming it by AC-1/AC-3/AC-4's *current* membership is exactly the frozen-list failure mode this item
exists to abolish everywhere else. The round-18 audit-fold's finding — that AC-3's contribution is a set of
**classes** where the closure needs **functions**, and that AC-4 runs no scan at all so "AC-4's live output"
was fictitious — is confirmed correct by independent re-derivation: `PersonRepository` (person.py:159) and
`CompanyRepository` (company.py:46) declare no `_load_file` of their own and both resolve through the MRO to
`base.py:171`; `meeting.py:64` and `book.py:57` are their own. Four classes collapse to three functions, as
claimed. And AC-4 (line 496 fence) genuinely names `write_markdown_file` and asserts two fixtures — it
derives nothing — so sourcing that stop-set member from AC-1's own two-predicate set difference
("calls-then-writes" minus "data-flow") instead of from AC-4 is the right fix in principle: `write_markdown_file`
really is the proven negative AC-1's discrimination clause already requires, and reusing it avoids
re-introducing a hardcoded name. The PARTITION assertion, and requiring each contribution to be non-empty and
a subset of the computed closure, are sound guards against the degenerate all-residue reading round 18 caught.

### MATERIAL — the stop set's three contributions are typed correctly now, but nothing requires them to be the SAME code AC-1/AC-3 run, so "consume" can be satisfied by an independent re-derivation that silently diverges from the original

AC-2's `desc:` (line 480) states the conversions round 18 added — resolve AC-3's discovered classes through
the MRO to their `_load_file` implementation and dedupe; source the AC-4 contribution from AC-1's own loose-
minus-data-flow set difference — as properties a compliant implementation must have. What it does not state,
and what nothing anywhere in AC-1, AC-2, AC-3 or AC-4 states, is **where the code that computes the loose
set, the data-flow set, and the per-class `_load_file` resolution actually lives**, such that AC-2's test can
literally invoke the same function object AC-1's and AC-3's tests invoke, rather than re-derive an
independently-written copy that is merely supposed to compute the same thing.

Nothing in this project's conventions forces sharing: Constraints (line 111) states the floor runs with **no
`conftest.py`**, so there is no established fixture location this item can lean on by convention, and no AC
fence requires the scan/predicate functions to be defined in an importable module (as opposed to a private
helper nested inside the test function that computes them, which is the ordinary, lowest-effort way to write
a self-contained pytest test). AC-1's own text only requires that "write_markdown_file is REACHED by the
scan's traversal and REJECTED BY ITS PREDICATE, asserted as a negative case in the same test" — an outcome
assertion, not a requirement that the "loose" candidate set and the "data-flow" subset be materialized as two
named, externally-importable artifacts whose difference is a computable, reusable value. A builder can satisfy
AC-1 exactly as written with a single-pass filter (`[f for f in candidates if data_flow_predicate(f)]`) plus
one inline membership assertion on `write_markdown_file`, never constructing "the loose set" as a distinct
object at all. AC-3's class→`_load_file` MRO resolution has the identical property: nothing requires it to be
importable by AC-2's test rather than computed inline inside AC-3's own test body.

**Concrete failure scenario.** A builder implements AC-1's test with its scan as a function-local closure
(never exported), and implements AC-2's test needing "AC-1's data-flow scan output, taken directly" and the
"set difference" for the AC-4 contribution — since nothing is importable, the builder writes a **second,
independent** implementation of the same two predicates inside AC-2's test module, matching AC-1's four
write-paths and `write_markdown_file`'s exclusion today (both copies agree at ship time, so both test suites
pass). This is not a hypothetical shape of error for this predicate specifically: rounds 12, 14, 16 and 18 of
this same document each found a subtle, previously-unnoticed defect in how "which functions satisfy the
data-flow predicate" was specified or scanned — direct evidence that two independent hand-writings of this
particular predicate are exactly where divergence is likely, unlike the "walk every .py file on disk" half of
the derivation, which is mechanical enough that restating it identically in prose across AC-1/AC-2/AC-3/AC-5
(as this document already does, e.g. "the SAME derived file set AC-1, AC-3 and AC-5 walk") carries much lower
risk. Six months later a fifth write path, `merge_frontmatter_field`, lands in a new module. AC-1's original
scan discovers it and correctly requires it to raise (round 11/12's guarantee, still live). AC-2's
independently-maintained copy of the same two predicates was written with a subtly different AST-walk (say it
matches only `ast.Attribute`-style calls and misses a `Name`-only call node) and does not add
`merge_frontmatter_field` to its stop set: the closure either climbs past it into whatever calls it — the
unbounded walk the stop rule exists to prevent — or, if nothing calls it, the closure's residue absorbs it as
an undispositioned "propagating" member, so AC-2 asserts `merge_frontmatter_field` PROPAGATES the typed error
while AC-1 simultaneously asserts it REFUSES (raises without depending on a caller to observe it) — the exact
refuse-vs-propagate collision round 16, 17 and 18 were each built, in turn, to prevent, reached not because a
set was named instead of derived, but because two derivations of the same property were never required to be
one derivation. Nothing in the suite today can catch this, because both copies agree on the current four-path
baseline; it manifests only the day a real fifth write path is added, exactly the kind of gap this document's
own "a completeness claim is only as durable as the process that re-checks it" rule (round 11) was written to
close, one level below where round 18 closed it.

Examples of done has no worked scenario for this either: the closing "someone six months from now" example
(covering repository discovery, write-path discovery, return-site discovery, `write_markdown_file`'s exclusion
by predicate, and caller-sweep via closure) never demonstrates the cross-AC consistency property itself — that
adding a function makes AC-1 say refuse **and, via the same computation**, makes AC-2's residue not include it.
That is precisely the property the stop-set composition exists to guarantee, and it is the one direction none
of the twelve worked Examples pins.

**What would have to change.** AC-1's, AC-3's and AC-4's fences (or a shared clause naming all of them) must
require the data-flow scan, the loose-predicate scan, and the class→`_load_file` MRO resolution to be defined
as single, importable functions — in one module all four ACs' tests import and call by name — so that AC-2's
stop set is invoking the literal same code object AC-1's and AC-3's own tests invoke, never a second
hand-written implementation asserted only to agree. Absent that, "consume, don't restate" is a property about
prose, not about the tests: two texts that describe the same predicate are not the same predicate, and this
document's own history (rounds 12/14/16/18) is the evidence that this specific predicate is exactly where two
independent hand-writings diverge.

### What I attacked and found clean

- Independently re-derived the six-member propagating residue and the four-classes-collapse-to-three-functions
  fact from source (`person.py:159`, `company.py:46`, `meeting.py:64`, `book.py:57`) — both match round 16's
  and round 18's claims exactly.
- Confirmed AC-4 (line 496 fence) genuinely names `write_markdown_file` and runs no scan of its own — round
  18's diagnosis that "AC-4's live output" was fictitious holds.
- Confirmed the PARTITION, non-empty, and subset-of-closure assertions (round 18's fix) correctly foreclose
  the degenerate "empty stop sets → everything is residue" reading round 18 caught.
- Checked AC-3's twelve-cell matrix (all four repository classes, all three fixture directions) for internal
  consistency against round 6's non-uniform-answers ruling — `BookRepository`'s fixture (a) is still the sole
  MUST-NOT-be-listed cell, correctly asymmetric; no regression.
- Checked AC-5's four-predicate CLOSURE, the P3 ACCOMMODATE/PRESERVATION clauses, and AC-6's narrowed-except
  assertion against the current text — unchanged since round 11's fold, no drift.
- Checked Examples of done against Intent and against every AC's current text — no example asserts something
  the criteria no longer promise, and no drift from Intent found.
- Confirmed AC-1's absent-frontmatter-must-still-succeed half still quantifies over the same four-path derived
  list as its raise half (round 2's fix) — untouched by rounds 17/18, no regression.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-24
model: claude-sonnet-5
note: Round 17's composition move and the round-18 audit-fold's class-vs-function/AC-4-has-no-derivation fix are both confirmed correct by independent re-derivation (four classes collapse to three _load_file functions; AC-4 genuinely derives nothing and is correctly re-sourced from AC-1's set difference). New MATERIAL finding one level below round 18: nothing requires the loose/data-flow/MRO-resolution scans AC-2's stop set consumes to be ONE importable implementation AC-1/AC-3/AC-2's tests all call — only that their outputs have the right type. A builder can satisfy every fence with independently-written duplicate predicates that agree today and silently diverge on a future write path, reproducing the exact refuse-vs-propagate collision the stop-set composition exists to prevent -- not caught by any test or Example of done today -- still not signable.
```
