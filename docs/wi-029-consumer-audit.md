# WI-029 consumer audit — provenance-bound writes and rename-on-`update_fields`

Conductor-performed scan of the three consumer repos (2026-09-21, 16:20–16:45 BST), committed as WI-029's
second `kind: precondition` / `grounds:` fence (`docs/filename-name-divergence-repair.md` → `## Write
Targets`) BEFORE the criteria are frozen. The caged builder cannot reach these repos; this artifact is
the evidence the change's blast radius was measured. Precedent and shape: `docs/wi-024-consumer-audit.md`.
Method: one read-only sweep per repo (three parallel Explore agents on the same brief, each output
re-read by the conductor); per repo — 40-hex HEAD, dirty count, the literal commands, verbatim matching
lines, and a site table classifying each call's entity as LOADED (came out of `get`/`resolve`/
`get_by_*`/`get_all`) or CONSTRUCTED. Excluded everywhere: `.venv`, `archive/`, `node_modules`, `tests/`
(test sites listed separately). No vault note name, no live identifier appears here — code paths only.

**The nine changed paths** (obsidian-schemas HEAD `b7befd0c66460560c887549a2efc93b1e0f09451`):
`BaseRepository.save` (`base.py:367`), `BaseRepository.update_fields` (`base.py:414`),
`PersonRepository.save` (`person.py:1155`), `append_to_timeline` (`:1371`), `append_to_body_section`
(`:1471`), `add_to_discuss_item` (`:1631`), `update_to_discuss_item` (`:1692`), `remove_to_discuss_item`
(`:1772`), `BookRepository.save` (`book.py:144`, filename from `_get_file_name` `:340`),
`MeetingRepository.save` (`meeting.py:166`, `_get_file_name` `:208`). In-library `.save(` callers are the
three CREATE paths the fence names (`company.py:238`, `book.py:322`, `person.py:1340`) plus the
`super().save` in the Person override (`person.py:1197`); nothing in-library calls a body-writer.

---

## HAL9000

HEAD: `1abc55675cb9ede0ba93f9cfc35a9eef4fde04e1` — dirty: 7 (a doc, two state files, four untracked
lock/ledger files; none touch the audited paths). All production reaches go through
`backend_fastapi/core/entity_registry.get_repository` plus one legacy module the FastAPI router imports
at runtime (`backend/chat/commands/introduction_commands.py`).

### (1) Call sites of the nine paths

Commands (one per pattern, same excludes; `-g '!*_archive*'` also excludes `backend_fastapi/_archive/`):

```
rg -n '\.save\(' --glob '!.venv' --glob '!archive/**' --glob '!node_modules' --glob '!tests/**' -g '*.py' -g '!*_archive*'
rg -n '\.update_fields\('            (same excludes)
rg -n '\.append_to_timeline\('       (same excludes)
rg -n '\.append_to_body_section\('   (same excludes)
rg -n '\.add_to_discuss_item\('      (same excludes)
rg -n '\.update_to_discuss_item\('   (same excludes)
rg -n '\.remove_to_discuss_item\('   (same excludes)
rg -n 'BookRepository|MeetingRepository' (same excludes)
```

Verbatim matching lines:

```
=== .save( ===
backend_fastapi/services/notifications/state.py:172:        self.save(record)
backend_fastapi/services/notifications/service.py:137:        self.state.save(record)
backend_fastapi/services/notifications/service.py:158:            self.state.save(record)
=== .update_fields( ===
backend_fastapi/routers/entities.py:461:        updated = repo.update_fields(entity, body)
backend_fastapi/routers/introductions.py:569:    repo.update_fields(person, {"emails": new_emails})
backend_fastapi/routers/introductions.py:625:    repo.update_fields(person, {"linkedin": request.linkedin_url})
=== .append_to_timeline( ===
backend_fastapi/routers/introductions.py:433:                    result = repo.append_to_timeline(
backend/chat/commands/introduction_commands.py:88:                repo.append_to_timeline(person1, entry1)
backend/chat/commands/introduction_commands.py:93:                repo.append_to_timeline(person2, entry2)
backend_fastapi/skills/introductions_skill.py:134:                repo.append_to_timeline(
backend_fastapi/core/timeline_entry.py:211:    appended = repo.append_to_timeline(
=== .append_to_body_section( ===
backend_fastapi/routers/entities.py:345:        appended = repo.append_to_body_section(
=== .add_to_discuss_item( ===
backend_fastapi/skills/capture_router/destinations.py:197:    success = repo.add_to_discuss_item(person, topic)
backend_fastapi/skills/contacts_skill.py:262:            success = repo.add_to_discuss_item(person, text)
=== .update_to_discuss_item( / .remove_to_discuss_item( ===
no matches
=== BookRepository / MeetingRepository ===
backend_fastapi/core/entity_registry.py:47:    BookRepository,
backend_fastapi/core/entity_registry.py:48:    MeetingRepository,
backend_fastapi/core/entity_registry.py:65:    "book": BookRepository,
backend_fastapi/core/entity_registry.py:66:    "meeting": MeetingRepository,
backend_fastapi/core/artifact_writer.py:34:    (comment only)
```

The three `.save(` hits are `NotificationStateStore.save`, a JSON writer for `NotificationRecord`
(`services/notifications/state.py:1-40,81`) — not obsidian_schemas. `core/timeline_entry.py:211` is the
shared primitive; its three callers were traced.

| file:line | calls | entity origin |
|---|---|---|
| `routers/entities.py:461` | `repo.update_fields(entity, body)` | LOADED — `res.person` via `resolve_person(name)` (`:449`) or `repo.resolve(name)` (`:452`). **`body` is an arbitrary HTTP PATCH dict and may carry `name`** — the ONE consumer site that can trigger rename-on-`update_fields` from caller data, for person AND (via the generic route) book/meeting. Post-call path re-derived from `updated.name` (`:464`), not a stale pre-write path. |
| `routers/introductions.py:569` | `update_fields(person, {"emails": …})` | LOADED — `resolve_person(request.name)` `:561`. No name. |
| `routers/introductions.py:625` | `update_fields(person, {"linkedin": …})` | LOADED — `resolve_person` `:622`. No name. |
| `routers/introductions.py:433` | `append_to_timeline(person, entry, deduplicate_key=…)` | LOADED — `repo.resolve` `:409-410`. |
| `backend/chat/commands/introduction_commands.py:88`, `:93` | `append_to_timeline(personN, entryN)` | LOADED — `repo.resolve` `:85`, `:90`. |
| `skills/introductions_skill.py:134` | `append_to_timeline(person, entry, deduplicate_key=…)` | LOADED — `repo.resolve` `:120-121`. |
| `core/timeline_entry.py:211` ← `routers/entities.py:409`, `skills/contacts_skill.py:191`, `routers/introduce.py:487` | `append_to_timeline(person, rendered, deduplicate_key=…)` | LOADED at every caller — `resolve_person(...)` `:402`/`:173`; `candidate.person` from `person_resolution.resolve_person(query).candidates` (`introduce.py:340`, `:403`, `:405`). |
| `routers/entities.py:345` | `append_to_body_section(entity, section, content, …)` | LOADED — `resolve_person(name)` `:336`, `res.person` `:341`. |
| `skills/capture_router/destinations.py:197` | `add_to_discuss_item(person, topic)` | LOADED — `resolve_person` `:180`, `res.person` `:188`. |
| `skills/contacts_skill.py:262` | `add_to_discuss_item(person, text)` | LOADED — `resolve_person` `:250`, `res.person` `:258`. |

**13 production sites; 13 LOADED; 0 CONSTRUCTED; 0 UNCLEAR.** `find_or_create_stub`/`create_stub` at
`routers/entities.py:251`, `:276` are creation, outside the nine.

### (2) Path held across a write

No site captures a `Path` to a note, writes to THAT note through the library, then dereferences the
stale path. Three sites compose a wikilink from a fresh `repo.get_file_path(other)` immediately before an
`append_to_timeline` on a DIFFERENT person's note (`routers/introductions.py:428-434`,
`skills/introductions_skill.py:129-136`, `routers/introduce.py:483-490`): 0 defects, 3 nearest-edge sites.

### (3) `auto_load=False` / never `load()`

```
rg -n "auto_load"  → only a comment at core/entity_registry.py:339 (+ one test comment)
rg -n "PersonRepository\(|CompanyRepository\(|BookRepository\(|MeetingRepository\("  → tests and comments only
```
0 in production. ONE allow-listed construction site, `core/entity_registry.py:_build` (`:109-142`), default
`auto_load`; the ban elsewhere is enforced by `tests/test_person_repository_singleton.py:178-242`.

### (4) Reconstruction

```
rg -n "Person\(\*\*|Company\(\*\*|Book\(\*\*|Meeting\(\*\*|model_validate\(|model_copy\(|\.model_dump\("  (same excludes)
```
8 hits, all one-way `model_dump` for HTTP bodies or unrelated models (`routers/notifications.py:104,124,251`,
`routers/draft_queue.py:130,227`, `routers/introduce.py:398`, `routers/entities.py:60`,
`services/notifications/state.py:78`). **0 reconstructions feed a write.** Adjacent finding, outside the
nine: `backend/chat/commands/introduction_commands.py:lookup_contact_info` → `search_md_files_directly`
(`:273-350`) reads person notes directly with `yaml.safe_load` and returns dicts — a second, unmanaged
vault READER used by the `/preview` and `/draft` introduction endpoints (`routers/introductions.py:234-235`,
`:348-349`). Pre-existing; not a write-target defect.

### (5) Wikilink / `attendees:` / `company:` held across a rename

Wikilink composers: the same three sites as (2). `attendees` hits are all Google Calendar API lists
(`core/calendar_client.py`, `jobs/build_connections.py`, `jobs/sync_interactions.py`,
`scripts/meeting-notifier.py`). `company:` writes only in the legacy Flask `md_formatter.py:67`. **0 sites
rename what they link**; the three are latent under concurrent renames via `entities.py:461`.

### (6) `BookRepository.save` / `MeetingRepository.save`

**0 direct calls.** Both classes are registered in `REPOSITORY_CLASSES` and reachable ONLY through the
generic `PATCH /api/entities/{entity_type}/{name}` → `routers/entities.py:461` `update_fields` (entity
LOADED via `repo.resolve`), so a PATCH carrying a book `title` or meeting `meeting_id` would meet the new
rename semantics there. Book creation (`skills/capture_router/destinations.py:route_book`) writes files
directly via `core/artifact_writer.py:269` and never touches `BookRepository`.

Test sites (not counted): `test_book_skill.py`, `test_timeline_door.py`, `test_timeline_entry_wall.py`,
`test_person_repository_singleton.py`, `test_wi061_registry_freshness.py`, `test_entities.py`,
`test_introduce.py`, `test_wi034_acceptance.py`, `test_wi036_acceptance.py`, `test_contact_resolver.py`,
`test_contacts_router.py`, `test_artifact_writer_vault_boundary.py`.

---

## Exocortex

HEAD: `27cb78cc5a2099972dccea984664193e69414def` — dirty: 4 (SESSION_LOG, a state file, an untracked doc and
lock; none touch the audited paths).

### (1) Call sites of the nine paths

```
grep -rnF ".save(" --include="*.py" . | grep -v -E '\.venv/|archive/|node_modules/|(^|/)tests/'
(and the same for each of the other six patterns)
grep -rn "meeting_repo\|book_repo\|MeetingRepository\|BookRepository" --include="*.py" . | grep -v -E '\.venv/|archive/|node_modules/'
```

```
=== .save( ===
exocortex/ingestion/stages/resolve.py:259:        # person_repo.save(existing) rebuilds the file with the default empty   (COMMENT)
=== .update_fields( ===
exocortex/ingestion/stages/resolve.py:265:            proc.person_repo.update_fields(existing, {"emails": existing.emails})
jobs/validate_data.py:122:                person_repo.update_fields(person, {"needs_review": True})
=== .append_to_timeline( ===
exocortex/ingestion/stages/note.py:375:            proc.person_repo.append_to_timeline(
=== .append_to_body_section( / .add_to_discuss_item( / .update_to_discuss_item( / .remove_to_discuss_item( ===
no matches
=== MeetingRepository / BookRepository ===
no matches (including tests)
```

| file:line | calls | entity origin |
|---|---|---|
| `ingestion/stages/resolve.py:265` | `update_fields(existing, {"emails": …})` | LOADED — `get_by_email` `:247` or `resolve_all(...)[0].person` `:253`. Name untouched. The WI-126 door-B site, deliberately off `.save()`. |
| `jobs/validate_data.py:122` | `update_fields(person, {"needs_review": True})` | LOADED — `person_repo.resolve(entity["name"])` `:120`. |
| `ingestion/stages/note.py:375-379` | `append_to_timeline(person, entry, deduplicate_key=meeting_filename)` | LOADED — `person_repo.get(attendee.name)` `:355`, fetched immediately before the write. **The highest-volume writer**: once per attendee per meeting on the hourly transcript watcher (`jobs/watcher.py`). |

**3 sites; 3 LOADED; 0 `.save()`; 0 of the other four body-writers.**

### (2) Path held across a write — one STRUCTURAL exposure, no single-line bug

`exocortex/clients/contacts.py:107` builds its own private `PersonRepository` (`self._repo`), separate from
the processor's `proc.person_repo` (`ingestion/transcript.py:210`). `ContactResolver.resolve*` /
`get_all_contacts` (`contacts.py:109-147`) bake `self._repo.get_file_path(person.name)` into
`ContactInfo.obsidian_file` at resolution time. The resolver is a module-global singleton
(`contacts.py:158-163`, bound lazily at `transcript.py:197-200`); `jobs/watcher.py:54` holds ONE
`TranscriptProcessor` across its `while True` loop (`:214`), so that snapshot cache persists across every
`update_fields` performed through the OTHER instance. `ContactResolver.refresh()` (`contacts.py:149-151`)
is called only from `jobs/attribution_audit.py:1150`, never on the ingestion path. The snapshot is consumed
stages later at `ingestion/stages/graph.py:208-214` (company People-section wikilink) and
`ingestion/stages/note.py:206-209` (meeting-note attendee wikilinks). Also persisted OUT of the vault:
`graph/utils.py:249-252` and `stages/graph.py:164`, `:352` write `meta["obsidian_file"] = file_path.name`
into graph.db, read back unverified at `jobs/cleanup_persons.py:312,352,354,356,357` and
`jobs/validate_data.py:90-91`; no job resyncs it after a person rename (`jobs/backfill_state_note_paths.py`
covers meeting notes only). Today nothing in exocortex changes a `Person.name`, so this is dormant.

### (3) `auto_load=False` / never `load()`

```
grep -rn "auto_load" --include="*.py" .   → no matches
grep -rn "PersonRepository(\|CompanyRepository(\|BookRepository(\|MeetingRepository(" --include="*.py" .   (non-test)
```
```
exocortex/clients/contacts.py:107:        self._repo = PersonRepository(vault_root(vault_path))
exocortex/ingestion/transcript.py:210:            self._person_repo = PersonRepository(self.obsidian_vault_path)
exocortex/ingestion/transcript.py:221:            self._company_repo = CompanyRepository(self.obsidian_vault_path)
exocortex/api/dependencies.py:60:    return PersonRepository(vault_root(settings.obsidian_vault_path))
jobs/cleanup_persons.py:762:    person_repo = PersonRepository(vault_root())
jobs/cleanup_persons.py:806:    person_repo = PersonRepository(vault_root())
jobs/validate_data.py:241:    person_repo = PersonRepository(vault_root())
jobs/attribution_audit.py:1113:        repo = PersonRepository(vault)
jobs/attribution_audit.py:1278:    repo = PersonRepository(vault)
```
0 `auto_load=False`; 9 default constructions; no explicit `load()` anywhere (lazy default).

### (4) Reconstruction

```
grep -rn "Person(\*\*\|Company(\*\*\|Meeting(\*\*\|model_validate(\|model_copy(\|\.model_dump(\|pickle"   → no matches (non-test)
```
Two FRESH constructions, never a reload: `ingestion/stages/company.py:190-196` `Company(...)` only after
`file_path.exists()` is False (`:173-175`), written via `write_markdown_file` (`:209-214`);
`ingestion/stages/note.py:214-220` `MeetingEntity(...)`, always new (`:177-179` returns early on an existing
non-stub), written via `write_markdown_file` (`:265-277`). **0 reconstructions feed a repository write.**

### (5) Wikilink / `attendees:` / `company:`

```
grep -rn '\[\[' --include="*.py" exocortex/ jobs/
```
```
exocortex/ingestion/stages/company.py:260:        entry = f"- [[{person_link}]]{title_suffix}\n"
exocortex/ingestion/stages/company.py:320:        entry = f"\n### {date_heading}\n[[{meeting_filename}|Meeting]] - {topics_summary}.\n"
exocortex/ingestion/stages/note.py:209:            attendee_links.append(f"[[{link_name}]]")
exocortex/ingestion/stages/note.py:349:    entry = f"\n### {date_heading}\n[[{meeting_filename}|Meeting]] - {topics_summary}.\n"
```
Two carry rename-staleness via the `ContactInfo.obsidian_file` snapshot of (2): `company.py:258-260`
(company People section, written by hand-rolled `company_path.write_text` `:266`) and `note.py:204-209`
(meeting attendee links). Two are same-block meeting self-references (low risk). The meeting note's
`attendees:` frontmatter is a list of NAMES (`note.py:214-220`) that no code re-derives after a rename.
No `company:` value is carried across a write; company notes are never renamed by this codebase.

### (6) `BookRepository.save` / `MeetingRepository.save`

**Neither class is imported, constructed or called anywhere in exocortex, tests included.** Meeting notes:
`write_markdown_file(note_path, entity=meeting, body=…)` at `note.py:264-277`. Company notes:
`write_markdown_file` for creation (`company.py:209-214`) plus hand-rolled `read_text`/`write_text` string
surgery for updates (`company.py:220-270`, `:273-350`). The change to those two `.save` overrides has no
direct exocortex call site.

Test sites (not counted): no test calls the nine paths; one docstring reference `tests/test_wi126_door_b.py:4`;
18 files use `create_stub`/`get`/`get_file_path`/`resolve` read-side.

---

## orchestrator

HEAD: `96bcf39bef43784ee54a6de66151e1549fbbb7f8` — dirty: 0.

### (1) Call sites of the nine paths

```
grep -rn --include="*.py" -E "\.save\(|\.update_fields\(|\.append_to_timeline\(|\.append_to_body_section\(|\.add_to_discuss_item\(|\.update_to_discuss_item\(|\.remove_to_discuss_item\(" . \
  | grep -v "^\./\.venv/" | grep -v "^\./archive/" | grep -v "/node_modules/" | grep -v "^\./tests/" | grep -v "/tests/" | sort
```
```
bin/repair-field-rfc2822.py:13:Side effect: PersonRepository.save() also runs name validation via WI-105.   (docstring)
bin/repair-field-rfc2822.py:87:            # preserves the note BODY. The old `repo.save(p)` rebuilt the file   (comment)
bin/repair-field-rfc2822.py:92:            repo.update_fields(p, {"emails": p.emails, "aliases": p.aliases})
bin/wi120-merge-dups.py:301:            repo.update_fields(canonical, updates)  # canonical-write FIRST
bin/wi120-merge-dups.py:315:                repo.append_to_body_section(canonical, section=section, content=dup_body)
src/executor.py:185:        state.save(state_path)      (RunState JSON, src/models.py:196 — not a vault entity)
src/executor.py:250:        state.save(state_path)
src/executor.py:282:        state.save(state_path)
```

| file:line | calls | entity origin |
|---|---|---|
| `bin/repair-field-rfc2822.py:92` | `update_fields(p, {"emails": …, "aliases": …})` | LOADED — `repo.get_all()` `:56`. No name. |
| `bin/wi120-merge-dups.py:301` | `update_fields(canonical, updates)` | LOADED — `repo.get(canon_name)` `:240` after `repo.load()` `:214`; `updates` never carries `name`/`created` (`:289`). |
| `bin/wi120-merge-dups.py:315` | `append_to_body_section(canonical, …)` | LOADED — RE-FETCHED `repo.get(canon_name)` at `:302` after the `update_fields` — the correct pattern. |

**3 sites; 3 LOADED.** Five bin/ scripts mutate person notes WITHOUT the nine paths (raw
`parse_frontmatter`/`write_frontmatter`/`write_text`/`rename`): `bin/repair-person-names.py:342-366`
(rewrites `name:` in place, deliberately NO file rename, `:350-354`), `bin/apply-vault-review.py:76-98`
(rewrites `name:` AND `shutil.move`s to `@{new}.md`), `bin/merge-duplicate-persons.py:393-473` (regex
merge + `rename`, no repository import beyond `NameValidator`), `bin/fix-smushed-frontmatter-close.py:86`,
`bin/fix-quoted-yaml-bools.py:82-84`. The library change does not alter them; they duplicate (and partly
omit) the rename/backlink logic this item formalises.

### (2) Path held across a write

```
grep -rn --include="*.py" "get_file_path" . | grep -v "^\./\.venv/\|/tests/\|^\./archive/"
```
```
bin/generate-vault-review.py:187:    by_file = {repo.get_file_path(p.name): p for p in all_people}
bin/generate-vault-review.py:278:        file_path = repo.get_file_path(p.name)
bin/repair-person-names.py:274:        file_path = repo.get_file_path(p.name)
bin/wi120-merge-dups.py:214:    repo.load()  # eager so get_file_path is populated
src/enricher_preprocessor.py:256:            raw = repo.get_file_path(name)
src/invariants.py:912:        p = repo.get_file_path(person.name)
src/invariants.py:3745:            raw = repo.get_file_path(name)
```
Report-only / read-only: `generate-vault-review.py`, `enricher_preprocessor.py`, `invariants.py`.
Cached-then-used but no library write in between: `repair-person-names.py:274` → `:369-384`. **One real
latent bug, outside the nine:** `bin/merge-duplicate-persons.py:545-562` — the 3-way branch passes
`three_way_target` to two sequential `_execute_merge` calls; the first may `rename` it (`:437-451`) and
returns the new path only in its result dict, so the second re-reads the stale path (`:400`) and raises
`FileNotFoundError`, swallowed by `except Exception` at `:559-560` — the merge is left half-done, loudly
printed. `bin/apply-vault-review.py:110-260` applies decisions from a snapshot taken once (`:120`); the
cluster branch guards `.exists()` (`:198-200`), the pair (`:146-176`) and single (`:217-257`) branches do
not.

### (3) `auto_load=False` / never `load()`

```
grep -rn --include="*.py" "auto_load" .   → no matches
```
20 `PersonRepository()` constructions (non-test); explicit `.load()` at `bin/wi120-merge-dups.py:214`, `:358`,
`bin/identity-parity-replay.py:67,77,79`. **One construct-then-write with no explicit `load()`:**
`bin/repair-field-rfc2822.py:55` → `get_all()` `:56` → `update_fields` `:92` (relies on lazy load). One
more on an ephemeral temp vault (`src/invariants.py:807`, `:823`, `create_stub`/`find_or_create_stub`).
All other constructions are read-only.

### (4) Reconstruction

```
grep -rn --include="*.py" -E "Person\(\*\*|Company\(\*\*|Book\(\*\*|Meeting\(\*\*|model_validate\(|model_copy\(|\.model_dump\("   → no matches (non-test)
grep -rln --include="*.py" -E "pickle|json.dump.*person|json.load.*person|shelve" bin src roles routines migrations work eval config   → no matches
```
**0.**

### (5) Wikilink / `attendees:` / `company:`

```
grep -rn --include="*.py" -E "\[\[@|attendees\s*:|company\s*:" bin src
```
```
bin/find-duplicate-persons.py:309:company: {company}<br>
bin/repair-person-names.py:249:    # Check each known company: ...
bin/wi120-merge-dups.py:150:    (docstring) Rewrite [[@<dup>]] -> [[@<canonical>]] in NON-person notes only.
bin/wi120-merge-dups.py:158:    dup_link = f"[[@{dup_name}]]"
bin/wi120-merge-dups.py:159:    canon_link = f"[[@{canonical_name}]]"
src/morning_briefing.py:227:    attendees: list[str] = field(default_factory=list)
src/morning_briefing.py:230:    person_company: str | None = None
```
`bin/wi120-merge-dups.py:148-189` `_rewrite_backlinks` is the one real site and is correctly ordered
(backlinks first `:320`/`:232`, move second `:323`/`:233`). `bin/merge-duplicate-persons.py` renames notes
and rewrites NO backlinks anywhere — every `[[@old]]` elsewhere dangles after it (and after
`apply-vault-review.py`, which drives it). `morning_briefing.py` is read-only.

### (6) `BookRepository.save` / `MeetingRepository.save`

```
grep -rn --include="*.py" --include="*.md" --include="*.yaml" -iE "BookRepository|MeetingRepository" .   → no matches
```
**Neither class exists in this repo.**

Test sites (not counted): `tests/test_lint_vault_writers.py:143` (a string literal fed to the linter under
test), `tests/test_models.py:188,223` (`RunState.save`); six more files mock `PersonRepository` read paths.

---

## Reading, for the spec

1. **Every consumer write on the nine paths is on a LOADED entity — 19 of 19 sites** (HAL9000 13,
   exocortex 3, orchestrator 3). Provenance binding therefore reaches every one of them; AC-1(f)'s
   "reconstructed entity keeps today's name-bound behaviour" residual arm has an EMPTY consumer population
   (question 4: 0 / 0 / 0).
2. **`update_fields` is the only path that can RENAME from consumer data, and it has ONE such site:**
   HAL9000 `routers/entities.py:461`, the generic entity PATCH, which forwards an arbitrary body — for
   persons, books and meetings alike. Every other `update_fields` call fixes the field set
   (`emails`, `linkedin`, `needs_review`, `emails`+`aliases`, a name-free merge dict). So "update_fields
   moves the file on a name change" is consumer-visible at exactly one door, and that door already
   re-derives the path from the returned entity (`:464`).
3. **The body-writers' consumer population:** `append_to_timeline` at 7 sites (HAL9000 6 incl. the
   `timeline_entry` primitive's three callers, exocortex 1 — the hourly cron writer), `append_to_body_section`
   2 (HAL9000 1, orchestrator 1), `add_to_discuss_item` 2 (HAL9000), `update_/remove_to_discuss_item` 0.
   All on notes fetched immediately before the write.
4. **`BookRepository.save` / `MeetingRepository.save` have ZERO consumer call sites**, direct or indirect,
   in all three repos. HAL9000 reaches both types only via the generic PATCH `update_fields`. Exocortex
   writes meetings and companies through `write_markdown_file` and hand-rolled text surgery, never a
   repository. Bringing the two overrides inside the seam changes no consumer's behaviour today.
5. **`auto_load=False`: 0 uses anywhere.** One orchestrator script writes with no explicit `load()`
   (`repair-field-rfc2822.py:55`), relying on the lazy default — the seam converts that into a correct
   write rather than a fork.
6. **Stale-path / stale-link exposure is STRUCTURAL and lives in the consumers, not at a call site:**
   exocortex's second never-refreshed `PersonRepository` inside `ContactResolver` feeds filename snapshots
   into meeting-note and company-note wikilinks and into graph.db metadata that no job resyncs; HAL9000's
   three intro wikilink sites read the other party's path moments before writing; orchestrator's
   `merge-duplicate-persons.py` renames without rewriting backlinks and has a real latent 3-way-merge
   stale-path bug. None of these is this item's to fix — they are the population the "accepted noise"
   disposition and the alias-on-move rule protect, and each is named here so the next queue review can
   mint them where they belong (exocortex: resolver refresh + graph.db resync; orchestrator: the 3-way
   merge; HAL9000: the legacy YAML reader is a separate pre-existing finding).
7. **Five orchestrator repair scripts mutate person notes outside the library entirely** and are unaffected
   by this change; two of them (`apply-vault-review.py`, `merge-duplicate-persons.py`) already rename
   files by hand with their own rules — the very class of divergence WI-029 repairs. After this item ships,
   they are the remaining generators of the class and belong on the next review's leak list.
