# WI-032 consumer audit — who reads or writes `Person.whatsapp`, and what the scalar→list flip breaks

Conductor-performed scan of the three consumer repos (2026-09-27, 07:20–07:50 BST), committed as WI-032's
second `kind: precondition` / `grounds:` fence (`docs/whatsapp-jid-value-type.md` → `## Write Targets`)
BEFORE the criteria are frozen. The caged builder cannot reach these repos; this artifact is the evidence
the change's blast radius was measured. Precedent and shape: `docs/wi-029-consumer-audit.md`,
`docs/wi-024-consumer-audit.md`. Method: one read-only sweep per repo (three parallel Explore agents on the
same brief, each output re-read by the conductor); per repo — 40-hex HEAD, dirty count, the literal
commands, verbatim matching lines, and a site table classifying each production site on THREE axes: READ or
WRITE; scalar-assuming or shape-agnostic; element-type-assuming (would it still break if elements stopped
being `str`). Excluded everywhere: `.venv`, `archive/`, `node_modules`; `tests/` listed separately. No
vault note name, no live identifier, no phone number or JID value appears here — code paths only.

**The question this settles** (the fence's `grounds:` line): whether any consumer reads or writes
`Person.whatsapp` as a scalar string, and so what the flip breaks outside this repository the moment
migrated notes land in the shared vault. **Answer: yes — seven scalar-assuming READ sites across the three
repos (two of them hard breaks on the day), ONE raw-file WRITE that would collapse or clear a list, ONE
LLM-prompt WRITE that clobbers with a scalar; ZERO element-type assumptions anywhere; ZERO whole-record
person re-serializations anywhere.** Detail and the ordered break list in §4.

---

## HAL9000

HEAD: `fb2b6c431d9edb639ba9b9ab79ab5f9a5ad1307d` — dirty: 9. `WhatsAppJID`: zero hits repo-wide.
`MCP-server-POC/`, `gateway/`, `bin/`, `dev_tools/`, legacy `backend/`: zero `Person.whatsapp` hits.
Non-`.py` hits (`frontends/drafts/src/*.tsx`) are channel-name literals, not the field.

Commands:
```
grep -rn --include='*.py' --exclude-dir=.venv --exclude-dir=archive --exclude-dir=node_modules -E '\.whatsapp|"whatsapp"|'"'"'whatsapp'"'"'' .
for pat in 'ContactInfo' 'get_by_phone' 'whatsapp_jid' 'WhatsAppJID' '@lid' 's\.whatsapp\.net'; do grep -rn --include='*.py' --exclude-dir=.venv --exclude-dir=archive --exclude-dir=node_modules -- "$pat" .; done
grep -rn --include='*.py' --exclude-dir=.venv --exclude-dir=archive --exclude-dir=node_modules -E 'obsidian_schemas|PersonRepository|write_markdown_file|update_fields|\.save\(' .
grep -rn --include='*.py' --exclude-dir=.venv --exclude-dir=archive --exclude-dir=node_modules -iE 'jid' .
```

Verbatim production lines touching the field:
```
backend_fastapi/core/contact_resolver.py:31:    whatsapp: Optional[str] = None
backend_fastapi/core/contact_resolver.py:40:    def get_whatsapp_jid(self) -> Optional[str]:
backend_fastapi/core/contact_resolver.py:47:        if self.whatsapp:
backend_fastapi/core/contact_resolver.py:48:            return self.whatsapp
backend_fastapi/core/contact_resolver.py:78:            whatsapp=person.whatsapp,
backend_fastapi/core/contact_resolver.py:279:        person = repo.get_by_phone(phone)
backend_fastapi/core/contact_resolver.py:296:    def resolve_by_whatsapp(self, jid: str) -> Optional[ContactInfo]:
backend_fastapi/core/contact_resolver.py:299:        return self.resolve_by_phone(jid)
backend_fastapi/routers/contacts.py:41:    whatsapp: Optional[str] = None
backend_fastapi/routers/contacts.py:50:        return cls(**dataclasses.asdict(ci))
backend_fastapi/routers/entities.py:60:    return entity.model_dump()
backend_fastapi/routers/entities.py:251:            entity, created_new = repo.find_or_create_stub(**body)
backend_fastapi/routers/entities.py:461:        updated = repo.update_fields(entity, body)
```

| site | R/W | scalar-assuming? | element-type? | notes |
|---|---|---|---|---|
| `core/contact_resolver.py:31` | decl | scalar (`Optional[str]`), unenforced dataclass | no | `ContactInfo` mirror; a list flows in silently |
| `core/contact_resolver.py:78` | READ | shape-agnostic pass-through | no | the ONE read of `person.whatsapp` off a `Person` |
| `core/contact_resolver.py:47-48` | READ | scalar by contract (`-> Optional[str]` returns the raw value) | no | `get_whatsapp_jid`; **no production caller** — latent |
| `routers/contacts.py:41` + `:50` | wire WRITE | **scalar, HARD** — Pydantic `Optional[str]` fed by `asdict` splat | no | **every `/api/contacts` response 500s for a person with a list** |
| `routers/entities.py:60` | wire WRITE | shape-agnostic (`model_dump`) | no | list serializes as a JSON array |
| `routers/entities.py:461` | **vault WRITE** | shape-agnostic — raw request `dict` → `update_fields` | no | PATCH door: no allowlist, no coercion |
| `routers/entities.py:251` | **vault WRITE** | shape-agnostic — raw `dict` → `find_or_create_stub` | no | POST door |

(a) JID → phone lookup: **yes, one path, dead caller** — `resolve_by_whatsapp` (`:296-299`) hands the whole
JID to `get_by_phone` (`:279`) with no `@`-stripping; no production caller. Near-miss:
`skills/imessage_skill.py:59-62` routes any `@`-bearing contact to `get_by_email`, so a JID misses silently.
(b) Bare number written: **no dedicated writer; the two generic doors (`entities.py:251`, `:461`) forward
whatever the client sends** — these are the class-C producers (the 2026-09-09 hand repair went through
`:461`). `jobs/sync_interactions.py` writes only the interactions DB, never a note. Planned, not code:
WI-074 (`docs/whatsapp-identifier-backfill-from-bridge-store.md`, stage `idea`) will bulk-write JIDs of BOTH
forms through the PATCH door — the exact multi-JID case the list type exists for; it must land AFTER WI-032.
(c) Clearing: **no production writer**; `entities.py:461` forwards `""`/`null` unmodified; the create path
never sets the field. Ten test fixtures write `whatsapp: ""` (scalar-empty) — class Ø must keep succeeding.
(d) Whole-record: **`PersonRepository.save` / `repo.save(person)` / `write_markdown_file(entity=…)`: ZERO
call sites.** Field-level doors with provenance: `entities.py:461` LOADED (`resolve_person`),
`introductions.py:569` / `:625` LOADED (`emails` / `linkedin` only), `entities.py:251` CONSTRUCTED from the
request dict, `entities.py:345` and `core/timeline_entry.py:229` body-append on LOADED entities. **No
read-modify-write round-trip can down-convert a list to a scalar.**
(e) Mirrors: `core/contact_resolver.py:18/:31` `Optional[str]`; `routers/contacts.py:34/:41` Pydantic
`Optional[str]` (the enforcing one). `routers/introductions.py:60` `ContactInfo` is a name collision with
no whatsapp attribute.
(f) Local JID rule: **no regex, no validator.** `services/channels/whatsapp.py:42` substring-tests a
`thread_id`, not the field; f-string constructors at `core/contact_resolver.py:53`,
`core/whatsapp_client.py:48,110`, `services/channels/whatsapp.py:50` assume the phone form; SQL `LIKE
'%@s.whatsapp.net'` at `jobs/sync_interactions.py:362,373` excludes `@lid`. Tests: `tests/test_contact_resolver.py:78,92`
is the one scalar construct + equality assert.

---

## exocortex

HEAD: `27cb78cc5a2099972dccea984664193e69414def` — dirty: 4. Production hits confined to ONE file,
`exocortex/clients/contacts.py`; tests to `tests/test_contacts.py`. `WhatsAppJID`, `@lid`: zero hits.
WhatsApp ingestion is spec-only (`docs/whatsapp-ingestion.md`; `CLAUDE.md:233` "planned, not started").

Commands:
```
grep -rn --include='*.py' -E '\.whatsapp|"whatsapp"|'"'"'whatsapp'"'"'' . --exclude-dir=.venv --exclude-dir=archive --exclude-dir=node_modules
grep -rn --include='*.py' -E 'ContactInfo|get_by_phone|whatsapp_jid|WhatsAppJID|@lid|s\.whatsapp\.net' . --exclude-dir=.venv --exclude-dir=archive --exclude-dir=node_modules
grep -rn --include='*.py' -E 'write_markdown_file|update_fields|\.save\(|PersonRepository|create_stub|find_or_create_stub' . --exclude-dir=.venv --exclude-dir=archive --exclude-dir=node_modules
```

Verbatim production lines:
```
exocortex/clients/contacts.py:35:    whatsapp: Optional[str] = None
exocortex/clients/contacts.py:47:    def get_whatsapp_jid(self) -> Optional[str]:
exocortex/clients/contacts.py:49:        if self.whatsapp:
exocortex/clients/contacts.py:51:            if "@" in self.whatsapp:
exocortex/clients/contacts.py:52:                return self.whatsapp
exocortex/clients/contacts.py:53:            return f"{self.whatsapp}@s.whatsapp.net"
exocortex/clients/contacts.py:56:            digits = normalize_phone(self.phones[0])
exocortex/clients/contacts.py:58:                return f"{digits}@s.whatsapp.net"
exocortex/clients/contacts.py:74:            whatsapp=person.whatsapp,
exocortex/clients/contacts.py:131:    def resolve_by_phone(self, phone: str) -> Optional[ContactInfo]:
exocortex/clients/contacts.py:133:        person = self._repo.get_by_phone(phone)
```

| site | R/W | scalar-assuming? | element-type? | notes |
|---|---|---|---|---|
| `clients/contacts.py:35` | decl | scalar (`Optional[str]`), unenforced | no | `ContactInfo` mirror |
| `clients/contacts.py:74` | READ | shape-agnostic pass-through (no `or None` unlike siblings) | no | the single `Person→ContactInfo` ingress |
| `clients/contacts.py:49-53` | READ | **scalar, silent wrong value** — `"@" in self.whatsapp` becomes list-MEMBERSHIP on a list (always False) and the f-string emits a garbage JID; no exception, no log | implicit | `get_whatsapp_jid`; **zero production callers** — latent, live as public API |
| `clients/contacts.py:55-58` | READ (`phones`) | n/a fallback arm | `phones[0]` str | untouched |

(a) JID → phone lookup: no direct site; `resolve_by_phone` (`:131-133`) has zero callers and would pass a
JID straight to `get_by_phone` if one ever did. (b) Bare number written: **no** — no production write of the
field besides the mirror at `:74`; `create_stub` calls (`ingestion/stages/resolve.py:283-289`,
`jobs/attribution_audit.py:1083,1115,1121`) carry no `whatsapp`. (c) Clearing: **no**. (d) Whole-record:
**ZERO** — `update_fields` at `ingestion/stages/resolve.py:265` (LOADED, `emails` only) and
`jobs/validate_data.py:122` (LOADED, `needs_review` only); `append_to_timeline` at `ingestion/stages/note.py:375`
(LOADED); `write_markdown_file` at `ingestion/stages/company.py:209`, `note.py:265,273` writes Company/Meeting,
never Person; `repo.save(person)` has no call site (`resolve.py:259` records its WI-126 removal). (e) Mirror:
`clients/contacts.py:21/:35` `Optional[str] = None` (default already diverges from the model's `""`).
(f) graph.db / Chroma: **the field is never stored** — `graph/utils.py:222-254` and `:257-295` omit it;
`graph/db.py:19` `_LIST_FIELDS` omits it (flag: if ever added, it would merge last-write-wins, not union).
Local JID rule: no regex; the `"@"`-substring heuristic at `:51` plus two domain-hardcoding constructors
(`:53`, `:58`). `docs/value-types-at-boundaries.md:17` already records the intent to adopt the foundation's
`Identifier` union; `contacts.py` is the un-migrated holdout.

---

## orchestrator

HEAD: `58aaac03386a7a9e20ef5889539193b5e58c1a36` — dirty: 1. No `ContactInfo`, no `WhatsAppJID` anywhere.
`bin/*.sh` clean. Two bridge-store readers that disagree on file and column names (see (f)).

Commands:
```
grep -rn --include='*.py' --exclude-dir=.venv --exclude-dir=archive --exclude-dir=node_modules -E '\.whatsapp|"whatsapp"|'"'"'whatsapp'"'"'' .
grep -rn --include='*.py' --exclude-dir=.venv --exclude-dir=archive --exclude-dir=node_modules -E 'ContactInfo|get_by_phone|whatsapp_jid|WhatsAppJID|find_or_create_stub|@lid|s\.whatsapp\.net' .
grep -rn --include='*.py' --exclude-dir=.venv --exclude-dir=archive --exclude-dir=node_modules -E '\.save\(|update_fields|write_markdown_file|PersonRepository' .
grep -rn --exclude-dir=.venv --exclude-dir=archive --exclude-dir=node_modules --exclude-dir=.git --exclude='*.py' -E '\bwhatsapp:|\.whatsapp\b|whatsapp_jid' .
```

Verbatim production lines (the field; bridge-store plumbing omitted here, listed under (f)):
```
src/contact_normalizer.py:277:        if person.whatsapp:
src/contact_normalizer.py:278:            result["whatsapp_phone"] = person.whatsapp
src/invariants.py:593:_FS_WHATSAPP_RE = re.compile(r"^\d+@(s\.whatsapp\.net|lid)$")
src/invariants.py:614:def _fs_whatsapp_ok(w) -> bool:
src/invariants.py:617:    return isinstance(w, str) and bool(_FS_WHATSAPP_RE.match(w.strip()))
src/invariants.py:663:    w = getattr(person, "whatsapp", None)
src/invariants.py:665:        bad.append({"field": "whatsapp", "value": w, "reason": "not a WhatsApp JID (@s.whatsapp.net or @lid)"})
bin/generate-vault-review.py:54:        "whatsapp": getattr(p, "whatsapp", "") or "",
bin/generate-vault-review.py:215:            "whatsapp": fm_raw.get("whatsapp", ""),
bin/generate-vault-review.py:450:      <tr><th>whatsapp</th><td>${p.whatsapp ? `<code>${escapeHtml(p.whatsapp)}</code>` : ...
bin/find-duplicate-persons.py:76:                  "contact_context_checked", "created", "whatsapp"):
bin/find-duplicate-persons.py:141:        wa = (p.get("whatsapp") or "").strip()
bin/find-duplicate-persons.py:143:            phone_index[wa].append(p)
bin/find-duplicate-persons.py:298:        wa = escape(p.get("whatsapp") or "—")
bin/merge-duplicate-persons.py:380:    for field in ("whatsapp", "company", "title", "linkedin", "slack"):
bin/merge-duplicate-persons.py:383:        merged = _merge_scalar(c_val, d_val) or ""
bin/merge-duplicate-persons.py:384:        out = _write_fm_field(out, field, merged)
bin/merge-duplicate-persons.py:230:    line = f'{field}: "{value}"' if value else f'{field}: ""'
bin/audit-clobbered-notes.py:50:SIGNAL_FIELDS = ("company", "linkedin", "title", "aliases", "roles", "whatsapp")
bin/audit-enricher-orphans.py:126:            "whatsapp": has_value(fm, "whatsapp"),
roles/enricher.yaml:163:  - **Exactly one match:** Patch `whatsapp` frontmatter with the contact's JID.
roles/enricher.yaml:172:    -d '{"whatsapp": "<jid>@s.whatsapp.net"}'
```

| site | R/W | scalar-assuming? | element-type? | notes |
|---|---|---|---|---|
| `src/contact_normalizer.py:277-278` | READ | shape-agnostic (truthiness + opaque pass-through) | no | `whatsapp_phone` has no consumer — dead egress |
| `src/invariants.py:663-665` (+ `:593`, `:614-617`) | READ | **scalar, HARD** — `isinstance(w, str)` + `.strip()` + regex | **yes** | invariant `person_field_shapes_correct` (`:680`) goes red vault-wide on migration day; `src/field_shape_baseline.json` ratchets only 82 already-known `(name, field)` scalar-era entries |
| `bin/generate-vault-review.py:54`, `:215` | READ | partly agnostic (`[]`→`""`, `["x"]`→list into JSON) | no | list leaks into the payload |
| `bin/generate-vault-review.py:450` | READ (emitted JS) | **scalar** — `escapeHtml` string ops | yes | review page throws on an array |
| `bin/find-duplicate-persons.py:76-79` | READ | **scalar** — single-line regex parse, quote-strip | yes | block-YAML list captures `""` → field silently LOST from dedupe; `_read_fm_list` exists (`:82`) but the field is not routed to it |
| `bin/find-duplicate-persons.py:141-143`, `:298` | READ | **scalar** — `.strip()`, `html.escape` | yes | `AttributeError` on a list; feeds the HIGH-confidence dup edge (`:183-189`) |
| `bin/merge-duplicate-persons.py:380-384` (+ `:192-198`, `:229-234`, `:355`) | **raw-file WRITE** | **scalar, DESTRUCTIVE** — regex read, `.strip()` merge, `whatsapp: "<v>"` emit | yes | collapses a list to one quoted scalar, or writes `whatsapp: ""` when the regex misses a block list; `Path.write_text`, bypasses `PersonRepository`; reached from `bin/apply-vault-review.py:152,158` |
| `bin/audit-clobbered-notes.py:50,81-83` | READ | shape-agnostic (comment: str or list both truthy) | no | survives |
| `bin/audit-enricher-orphans.py:126`, `:67-75` | READ | shape-agnostic (`has_value` handles str and list) | no | survives |
| `roles/enricher.yaml:163-176` | **WRITE** (LLM → HAL9000 PATCH) | **scalar** — body `{"whatsapp": "<jid>@s.whatsapp.net"}` | n/a | clobbers a migrated list with one scalar; also overwrites rather than appends |
| `bin/apply-vault-review.py:86-95`, `bin/repair-person-names.py:356-366` | WRITE (frontmatter round-trip) | shape-agnostic (`parse_frontmatter`/`write_frontmatter`, only `name` mutated) | no | list round-trips safely |

(a) JID → phone lookup: **no** — always stripped first (`phone_from_jid` `:194-195`; `resolve_lid_to_phone`
`:72-90`), but inconsistently: `:233` passes bare digits, `:388` passes `"+"+digits` for the same JID.
(b) Bare number written: **no** — `find_or_create_stub` (`:428-434`) routes the derived phone to `phones[]`
by design (`docs/contact-detector-no-phone-name-guessing.md:252`); the enricher role writes a full phone-form
JID; `merge-duplicate-persons.py:384` propagates whatever shape it read. The 82 baselined violations in
`src/field_shape_baseline.json` ARE the class-C population (bare numbers written by an external repo — the
census's class-C row is 82, the same number by a different route). (c) Clearing: **yes, one site** —
`merge-duplicate-persons.py:383-384` rewrites the whatsapp line on every merge and emits `whatsapp: ""` when
both sides read empty, INCLUDING when the single-line regex failed to parse a block-YAML list — the concrete
post-migration data-loss path. (d) Whole-record: **`repo.save(person)` / `write_markdown_file(entity=…)`:
ZERO** (`bin/repair-field-rfc2822.py:86-91` records the WI-126 replacement by `update_fields`);
`update_fields` at `bin/repair-field-rfc2822.py:92` (LOADED, `emails`/`aliases`) and `bin/wi120-merge-dups.py:301`
(LOADED, `aliases`/`emails`/`phones` only); the one whatsapp-writing path is the raw-file merge above,
CONSTRUCTED from a regex-parsed string. (e) Mirrors: none typed; untyped dicts at
`bin/generate-vault-review.py:48-61`, `:208-219`, `bin/find-duplicate-persons.py:70-80`,
`src/contact_normalizer.py:263-278`. (f) Bridge stores: `src/contact_normalizer.py:52` reads
`…/whatsapp-bridge/store/whatsapp.db` (`whatsmeow_lid_map.pn`); `src/queue_writer.py:62` reads
`…/whatsapp-bridge/store/messages.db` (`whatsmeow_lid_map.phone_jid`, `:583`) — two readers, two files, two
column names; neither is written by this repo. Local JID rule: **yes** — `src/invariants.py:593` regex
(the repo's authoritative rule, the hard break) plus substring predicates `is_whatsapp_jid` (`:189`),
`is_group_jid` (`:184`), `phone_from_jid` (`:194-195`), and `src/feedback_collector.py:105`.

---

## 4. Cross-repo reading

**The third axis came back the way the fence hoped.** Across 20 production sites in three repos, NOT ONE
assumes the element type in a way the cardinality flip does not already expose: every `.strip()`, regex,
`isinstance(str)` and `html.escape` breaks because the VALUE becomes a list, and would be equally happy with
`List[str]` elements once it indexes one. That is evidence FOR Ruling B's recommended arm — `List[str]`
stored, typed access derived — and against any element-typed annotation.

**Ordered break list** (what the flip breaks the moment migrated notes land, however the package is installed):
1. `orchestrator/src/invariants.py:663-665` — `person_field_shapes_correct` red for every person with a
   non-empty list; the baseline ratchet does not cover shape.
2. `HAL9000/backend_fastapi/routers/contacts.py:41,50` — `/api/contacts` 500s for every such person.
3. `orchestrator/bin/merge-duplicate-persons.py:380-384` — the ONE write that can destroy a list (collapse
   to scalar, or clear to `""`); raw-file, outside the repository boundary (already named by the WI-029 audit
   as a divergence generator).
4. `orchestrator/bin/find-duplicate-persons.py:76-79,141-143,298` — `AttributeError` or silent field loss.
5. `orchestrator/bin/generate-vault-review.py:450` — review page throws on an array.
6. `orchestrator/roles/enricher.yaml:163-176` — the LLM-driven PATCH clobbers a list with one scalar JID.
7. `HAL9000/backend_fastapi/core/contact_resolver.py:31,47-48` and `exocortex/exocortex/clients/contacts.py:35,49-53`
   — the two `ContactInfo` mirrors lie about the type; both `get_whatsapp_jid` helpers are latent (zero
   callers) and the exocortex one emits a garbage JID silently.

**The fence's specific questions, answered across repos:**
- **JID fed to `get_by_phone`:** one dead path in HAL9000 (`resolve_by_whatsapp`); none live. orchestrator
  strips first but with an inconsistent `+`. `README.md:238`'s "look a JID up via `get_by_phone`" documents
  a route nothing takes.
- **Class-C producers (bare number into the field):** no consumer CODE synthesizes one. The producers are
  HAL9000's two generic entity doors forwarding raw client dicts (`entities.py:251`, `:461`) — the disclosed
  break in `## Approach` step (2) is exactly those two doors starting to refuse. The census's 82 and
  orchestrator's 82 baselined violations are the same population seen from two sides.
- **Clearing (`""`/`None`):** one production writer, orchestrator's raw-file merge; HAL9000's PATCH door
  forwards it; ten HAL9000 test fixtures write `whatsapp: ""`. Class Ø MUST keep succeeding everywhere —
  a refusing build would break every one of these.
- **Whole-record projection (`save` / `write_markdown_file(entity=…)`):** ZERO call sites in all three
  repos. The whole-record refusal arms AC-3 names have NO consumer caller today; the residual they refuse
  is also zero on the live vault (census). The arms are walls, not incidents.
- **Element-type assumptions:** none. (Third axis empty, as above.)

**Sequencing the audit surfaces:** HAL9000 WI-074 (bridge-store backfill, mixed phone-form and `@lid` JIDs
through the PATCH door) is the first real multi-JID writer and must land AFTER WI-032's type and doors,
which its own doc already states. The orchestrator enricher role's PATCH body needs the list shape (append,
not overwrite) at the same time.

**Not this repo's to fix, relayed for the next cross-project review:** orchestrator's raw-file
`merge-duplicate-persons.py` (already on the WI-029 list); the two bridge-store readers disagreeing on file
and column; exocortex's `"@"`-substring JID heuristic; HAL9000's `resolve_by_whatsapp`.

---

## Addendum — 2026-09-27, after `done`: a fourth reader, and the follow-through readback

The three-repo sweep above was the declared population. A wider grep at exit (every `Workspaces/*` repo plus
`~/.claude/skills` and `~/.claude/agents`) found ONE more reader: **mainspring's dispatch cockpit**
(`prototype/dispatch/server.py:306-307`, `:826-833`; `prototype/dispatch/workset.py:148`, `:188`) — a
scalar-assuming READ (`.endswith` on the value, string equality against a new JID) and a scalar WRITE
(`fields["whatsapp"] = c`, overwrite rather than append). It reaches the field ONLY through HAL9000's
doors (`hal_resolve`, `hal_person_get`, `hal_person_patch`), so it inherits whatever shape HAL9000 serves.
Also noted: `~/.claude/skills/new-person/SKILL.md:75-82` PATCHes a scalar JID — accepted by the door (a
storable scalar coerces) but an overwrite, not an append; low priority.

**Readback of the consumer follow-through, verified by re-running each suite against the committed
library (2e20c81), not taken from reports:**

| repo | fix | state at readback |
|---|---|---|
| HAL9000 | `ContactInfo.whatsapp` + `ContactInfoResponse.whatsapp` → `List[str]`; `get_whatsapp_jid` picks an element | committed on HAL9000 main (`b24d6f1`); 650 passed |
| orchestrator | WI-195: all five sites — the field-shape invariant accepts list AND pre-migration scalar; dedupe/merge/review/enricher list-aware | committed on orchestrator main (`2506a78`); 1502 passed, 1 skipped |
| exocortex | `ContactInfo.whatsapp` → `List[str]`; `get_whatsapp_jid` returns the first storable element; substring heuristic and both hardcoded constructors removed | working tree, awaiting Dave's commit; 660 passed (only the two pre-existing `test_wi054_key_table` failures) |
| mainspring dispatch | `whatsapp_jids()`/`whatsapp_jid()` accept list or str; routing read and both row sites use them; pin-time write appends on the list door | working tree, awaiting Dave's commit; cockpit restarted on the patched code |

The migration gate (`## 4`'s break list, items 1–7) is CLEAR. orchestrator prunes its 82 baselined
`whatsapp` entries after the migration write.
