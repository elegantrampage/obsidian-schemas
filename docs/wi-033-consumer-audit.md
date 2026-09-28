# WI-033 consumer audit — who writes or reads a vault timeline entry, and what the typed overload + marker-anchored dedupe changes

Conductor-performed scan of the whole estate (2026-09-28), committed as WI-033's third `kind: precondition`
fence (`docs/timeline-entry-relocation.md` → `## Write Targets`) BEFORE the criteria are frozen. The caged
builder cannot reach these repos; this artifact is the evidence that the change's blast radius was measured.
Precedent and shape: `docs/wi-032-consumer-audit.md`. Scope: EVERY git repo directly under
`/Users/davewascha/Workspaces/` (36 repos; `workshop-stable` skipped because it is a `git worktree` of
`workshop`, gitdir `workshop/.git/worktrees/workshop-stable`), plus `~/.claude/skills` and
`~/.claude/agents` (neither is a git repo). Method: one pattern sweep per repo, then every production hit
read at its call site (not inferred from the grep line). Per repo: 40-hex HEAD, dirty count, the literal
commands, verbatim matching production lines, and a site table whose load-bearing column is whether a call
passes a dedupe key that DISAGREES with the marker it writes. Excluded everywhere: `.venv`, `venv`,
`archive/`, `_archive/`, `node_modules`, `.git`; HAL9000's `zips/` (frozen 2025 tarball snapshots) also
excluded; `tests/` listed separately; `docs/`, `SESSION_LOG.md` and `state/` prose read for context only,
never counted as a site. No vault note name, no live identifier — code paths only.

**The question this settles** (the fence's `grounds:` line): which consumers write or read a vault timeline
entry today (or the `introduced_by` frontmatter key), whether any would break when `append_to_timeline`
grows a typed overload and the dedupe narrows to the marker form, and which of them is waiting on the
accessor.

**Answer: nothing breaks on WI-033's landing.** SIX production call sites of
`PersonRepository.append_to_timeline` exist estate-wide, in TWO repos (five in HAL9000 across four files,
one in exocortex), and EVERY ONE passes a `str` entry — so every one stays on the unchanged string+key path;
the typed overload has ZERO callers on the day and the marker-anchored narrowing touches no live call. Of
the six: ONE passes a key that agrees with the marker it writes (HAL9000's `core/timeline_entry.py:229`, by
construction — it fronts FOUR in-process producers: the WI-058 door, the contacts skill's free-text note,
the WI-036 outbound intro, the WI-077 observed intro); THREE pass a prose key while writing NO marker
(HAL9000's two retired `[intro]` writers and exocortex's meeting-link writer — these are the sites whose
behaviour WOULD change if migrated to the typed path, and they are the ones that must not be migrated
blindly); TWO pass no key (HAL9000's legacy `backend/` chat intro command). Beside the primitive: ONE second
timeline door (HAL9000's `section-append` with `section="Timeline"`, a different primitive WI-033 does not
touch) with FOUR hand-composing LLM/skill callers, FOUR raw-file timeline writers (all legacy or one-shot),
and FOUR prose readers of `## Timeline` — none parses the `<!-- … -->` marker, and none keys on
`[intro]` or `intro-by` except by prose regex. The WI-058 HTTP door (`POST …/timeline`) and the WI-077
door (`POST /api/introduce/observed`) have ZERO out-of-process code callers. **`introduced_by` as a
frontmatter key: ZERO readers and ZERO writers in code anywhere** — every `introduced_by` in the estate is
the HAL9000 `/api/contact-context` RESPONSE field (email-regex derived) or prose about it. **Waiting on the
accessor:** HAL9000 WI-078 (idea — retire `core/intro_extractor.py` + the WI-129 T9 path) and orchestrator
WI-194 (idea — inbound-intro events; retires the enricher's T9 Notes write). **Exocortex is NOT waiting in
code:** its WI-006 is "Email ingestion (Gmail threads)", stage `idea`, not parked relationship edges —
the WI-033 doc's naming of "exocortex's parked WI-006 (relationship edges)" (lines 30 and 492) does not
match exocortex's tree. Detail and the ordered list in `## Cross-repo reading`.

---

## HAL9000

HEAD: `d54430da9547a93525c6cc1b20cf781c9a63f82e` — dirty: 9 (the count moved 6 → 9 during the scan; a
session is live in this tree). Launchd serves `backend_fastapi/` only (`com.davewascha.hal9000.plist`:
`uvicorn main:app`, cwd `backend_fastapi`); the legacy `backend/` tree is not served but is still importable
and still reaches the real vault (HAL9000 `CLAUDE.md:142`, WI-062 / WI-063 deferrals, both stage `idea`).
`frontends/basereact/src/types.ts:11` `TimelineEntry` is a TypeScript name collision (a legacy
frontend's `{timestamp,type,content}` JSON row), not the vault entry.

Commands:
```
PAT='append_to_timeline|append_timeline_entry|TimelineEntry|timeline_entry|/timeline|## Timeline|introduced_by|introduced-by|intro-by|intro-to|\[intro\]|deduplicate_key'
grep -rnE --exclude-dir=.venv --exclude-dir=venv --exclude-dir=archive --exclude-dir=_archive --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=zips --exclude-dir=tests --exclude-dir=docs -I "$PAT" . | grep -vE '\.md:|state/'
grep -rnE --include='*.py' --exclude-dir=.venv --exclude-dir=archive --exclude-dir=_archive --exclude-dir=node_modules --exclude-dir=zips --exclude-dir=tests -E 'append_to_timeline\(|append_timeline_entry\(|deduplicate_key=|introduced_by = |f"### |append_entry\(|timeline_header|OBSERVED_KIND_ON_|^INTRO_KIND|extract_intro\(' .
grep -rniE "timeline|<!--|\"### |'### |f\"### " --include='*.py' backend_fastapi gateway bin MCP-server-POC dev_tools | grep -v "/tests/"
grep -rnE --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=archive --exclude-dir=docs --exclude-dir=tests -I "api/introduce|/timeline\b|/timeline\"|/timeline'" .
```

Verbatim production lines:
```
backend_fastapi/core/timeline_entry.py:184:    heading = f"### {entry.when.strftime('%B %-d, %Y')} [{entry.kind}]\n"
backend_fastapi/core/timeline_entry.py:192:def append_timeline_entry(
backend_fastapi/core/timeline_entry.py:229:    appended = repo.append_to_timeline(
backend_fastapi/core/timeline_entry.py:232:        deduplicate_key=dedupe_probe(entry),
backend_fastapi/routers/entities.py:350:            deduplicate_key=body.get("deduplicate_key"),
backend_fastapi/routers/entities.py:358:@router.post("/person/{name}/timeline")
backend_fastapi/routers/entities.py:409:        appended, rendered, _key = append_timeline_entry(
backend_fastapi/skills/contacts_skill.py:191:            success, _entry, _key = append_timeline_entry(
backend_fastapi/routers/introduce.py:70:INTRO_KIND = "intro"                      # OUTBOUND (WI-036) — the slug this router has always written
backend_fastapi/routers/introduce.py:71:OBSERVED_KIND_ON_INTRODUCEE = "intro-by"  # inbound, on the note of the person Dave was introduced TO
backend_fastapi/routers/introduce.py:72:OBSERVED_KIND_ON_INTRODUCER = "intro-to"  # inbound, on the note of the person who made the intro
backend_fastapi/routers/introduce.py:707:                written, _rendered, written_key = append_timeline_entry(
backend_fastapi/routers/introduce.py:727:                    deduplicate_key=key,
backend_fastapi/routers/introduce.py:735:                deduplicate_key=written_key,
backend_fastapi/routers/introduce.py:1058:            written, rendered, written_key = append_timeline_entry(
backend_fastapi/routers/introduce.py:1087:                deduplicate_key=None,
backend_fastapi/routers/introduce.py:1096:            deduplicate_key=written_key,
backend_fastapi/routers/introductions.py:431:                entry = f"### {date_str} [intro]\nIntroduced to [[{other_stem}|{other_display}]] via email{context_suffix}\n"
backend_fastapi/routers/introductions.py:433:                    result = repo.append_to_timeline(
backend_fastapi/routers/introductions.py:434:                        person, entry, deduplicate_key=f"Introduced to [[{other_stem}"
backend_fastapi/skills/introductions_skill.py:132:            entry = f"### {date_str} [intro]\nIntroduced to [[{other_stem}|{other_display}]] via email\n"
backend_fastapi/skills/introductions_skill.py:134:                repo.append_to_timeline(
backend_fastapi/skills/introductions_skill.py:135:                    person, entry, deduplicate_key=f"Introduced to [[{other_stem}"
backend_fastapi/skills/email_skill.py:121:            from core.writer import append_entry
backend_fastapi/skills/email_skill.py:203:            append_entry(
backend_fastapi/skills/email_skill.py:210:            append_entry(
backend_fastapi/routers/contact_context.py:70:    introduced_by: Optional[IntroducedBy] = None
backend_fastapi/routers/contact_context.py:241:    introduced_by = None
backend_fastapi/routers/contact_context.py:248:                intro_result = extract_intro(body)
backend_fastapi/routers/contact_context.py:250:                    introduced_by = IntroducedBy(
backend/chat/commands/introduction_commands.py:87:                entry1 = f"### {timestamp} [intro]\nIntroduced to {contact2_display} via email\n"
backend/chat/commands/introduction_commands.py:88:                repo.append_to_timeline(person1, entry1)
backend/chat/commands/introduction_commands.py:92:                entry2 = f"### {timestamp} [intro]\nIntroduced to {contact1_display} via email\n"
backend/chat/commands/introduction_commands.py:93:                repo.append_to_timeline(person2, entry2)
backend/core/writer.py:139:            timeline_header = '\n## Timeline\n'
backend/core/writer.py:143:            insert_position = content.find(timeline_header, frontmatter_end) + len(timeline_header)
backend/api/api-server.py:76:        append_entry(name, entry_type="note", text=data["text"])
backend/chat/commands/contact_commands.py:26:        append_entry(contact_name, entry_type="note", text=note_text)
frontends/basechat/chat_crm.py:168:                append_entry(
dev_tools/main.py:48:        append_entry(args.name, args.type, args.text)
bin/introduce.py:114:    url = f"{args.api_base}/api/introduce"
```

| site | R/W | door used | dedupe key passed | key agrees with marker written? | affected by typed overload or marker-anchored dedupe? | notes |
|---|---|---|---|---|---|---|
| `core/timeline_entry.py:229` (`append_timeline_entry`) | W | library primitive (string path) | `dedupe_probe(entry)` = `<!-- kind:YYYY-MM-DD:disc -->`, or `None` without a discriminator | **yes, by construction** — probe and embedded comment derive from the same `TimelineEntry` | **no on landing** — passes a `str`, stays on the unchanged path. On a future swap to the typed overload the only behaviour delta is span: a marker that sits OUTSIDE `## Timeline` (hand-moved entry) stops deduping | THE renderer; the relocation source. Its `render()` bytes are the parity target |
| `routers/entities.py:409` (WI-058 `POST /person/{name}/timeline`) | W | HAL9000 in-process → `append_timeline_entry` | derived from `discriminator` (wire field) | yes (inherits) | no | **zero out-of-process code callers** estate-wide (only `CLAUDE.md` rows name it) |
| `skills/contacts_skill.py:191` (`kind="note"`) | W | HAL9000 in-process → `append_timeline_entry` | none (no discriminator by design) | no key | no | free-text note; renders without a comment |
| `routers/introduce.py:707` (WI-036 outbound, `kind="intro"`, disc = counterparty canonical name) | W | HAL9000 in-process → `append_timeline_entry` | derived | yes | no | the `:727` literal `intro:{date}:{name}` is only the FAILURE-row record, never passed to the primitive. Reached by `bin/introduce.py` and mainspring's cockpit |
| `routers/introduce.py:1058` (WI-077 observed, `intro-by` / `intro-to`, disc = counterparty canonical name, `when` = observed day) | W | HAL9000 in-process → `append_timeline_entry` | derived | yes | no | **the only producer of the markers `introduced_by(person)` will read**; `when` ≠ clock, so a back-dated entry is prepended above newer ones (documented at `:1021-1025`) |
| `routers/introductions.py:433` (`/api/introductions/draft`, still mounted `main.py:77`) | W | library primitive, hand-composed `[intro]` entry | `Introduced to [[<stem>` (prose, undated) | **no** — writes NO marker; key is a prose substring | not on landing (string path). **Would change if migrated**: the typed path matches only markers, so this undated whole-file prose dedupe would vanish | retired flow (WI-036 Phase 2 / WI-062 `idea`); AC-1 wall exemption entry 2. The undated prose key ALSO matches WI-036 outbound entries (`Introduced to [[<stem>|…`) anywhere in the file, on any date — a cross-producer suppression. Emits the legacy `[intro]`-without-marker shape lint check (1) will report |
| `skills/introductions_skill.py:134` | W | library primitive, hand-composed `[intro]` | `Introduced to [[<stem>` | **no** — no marker | not on landing; same migration caveat | registered chat skill; same WI-062 exemption; entry lacks the context suffix the router adds |
| `backend/chat/commands/introduction_commands.py:88`, `:93` | W | library primitive, hand-composed `[intro]` with `%Y-%m-%d %H:%M:%S` heading | none | no key | not on landing | legacy tree (WI-062 exemption entry 3); non-canonical date heading — `parse_markers()` must treat it as markerless legacy, lint check (1) catches it |
| `backend/core/writer.py:120-150` (`append_entry`) + callers `backend/api/api-server.py:76`, `backend/chat/commands/contact_commands.py:26`, `frontends/basechat/chat_crm.py:168`, `dev_tools/main.py:48`, `skills/email_skill.py:203,210` | W | raw file write (`open r+` / `write`) | none | no key | no (never touches the primitive) | WI-063 (`idea`); heading `### YYYY-MM-DD HH:MM:SS [<type>]`, kinds include `intro`. `email_skill.py` reaches it by `sys.path` insertion of `backend/` then `from core.writer import …` — see "unsure" below |
| `routers/entities.py:350` (`POST /person/{name}/section-append`) | W | HAL9000 in-process → `append_to_body_section` (NOT the timeline primitive) | caller-supplied, SECTION-scoped | n/a — writes no marker; the caller composes the whole entry | **no** — WI-033 does not touch `append_to_body_section` | a SECOND timeline door: any HTTP client may hand-compose a `### …` entry into `Timeline`; AC-1 wall arm B(ii) only sees a CONSTANT `section="Timeline"` keyword, and here `section` is a variable. Four hand-composing callers below (orchestrator enricher, new-person skill, scheduler agent, personal-assistant doc) |
| `routers/contact_context.py:241-250` | R (email, not vault) | n/a | n/a | n/a | no | the `introduced_by` RESPONSE field, from `core/intro_extractor.extract_intro` over the first inbound email — NOT a frontmatter read. The "second reader" HAL9000 WI-078 retires once the accessor ships |
| `bin/introduce.py:114` | W (indirect) | HAL9000 HTTP (`POST /api/introduce`) | n/a | n/a | no | thin client of `introduce.py:707` |

Tests (listed separately, not sites): `backend_fastapi/tests/test_timeline_entry_wall.py` (AC-1 wall;
arm B(i) flags ANY attribute call named `append_to_timeline` with ≥1 positional arg outside four exemption
entries — `core/timeline_entry.py`, the two retired intro modules, `backend/chat/commands/introduction_commands.py`,
`backend/core/writer.py`), `test_timeline_door.py` (pins the delimited-probe M1 behaviour against the
WHOLE-FILE primitive at `:409-425`), `test_wi077_observed_intro.py`, `test_introduce.py`,
`test_wi036_acceptance.py`, `test_contacts_skill.py`, `test_contact_context.py`, `test_entities.py`,
`test_artifact_writer_vault_boundary.py`, `test_vault_root_capability_wall.py`,
`test_person_repository_singleton.py`, `test_wi061_registry_freshness.py`,
`test_person_resolution_doors.py`, `test_wi073_placeholder_outcome.py`; fixtures `conftest.py:632,657`,
`tests/person_resolution_vault.py`. Consequence for the later HAL9000 swap (not this item): a typed call
`repo.append_to_timeline(person, TimelineEntry(...))` from any module other than `core/timeline_entry.py`
trips arm B(i) — the swap must keep the call inside the exempt renderer module or amend the wall.

---

## exocortex

HEAD: `170dee8f1845b971d252b35029b6c22e97b498d1` — dirty: 2. One person-timeline writer, one
company-timeline writer; no timeline reader; no `introduced_by`, `intro-by`, `IntroRecord` or marker
reference anywhere in code. `who_can_intro` (`mcp_server.py:161`, `api/routers/relationships.py:39`) is
graph-derived (shared meetings), not vault-timeline-derived.

Commands:
```
PAT='append_to_timeline|append_timeline_entry|TimelineEntry|timeline_entry|/timeline|## Timeline|introduced_by|introduced-by|intro-by|intro-to|\[intro\]|deduplicate_key'
grep -rnE --exclude-dir=.venv --exclude-dir=archive --exclude-dir=_archive --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=tests --exclude-dir=docs -I "$PAT" . | grep -vE 'SESSION_LOG|state/|\.md:'
grep -rniE "timeline|introduc" --include='*.py' exocortex mcp_server.py scripts bin jobs
grep -rniE "INTRODUCED|intro edge|introduction edge|introduced_by" --include='*.md' --include='*.py' --include='*.json' .
```

Verbatim production lines:
```
exocortex/ingestion/stages/note.py:349:    entry = f"\n### {date_heading}\n[[{meeting_filename}|Meeting]] - {topics_summary}.\n"
exocortex/ingestion/stages/note.py:375:            proc.person_repo.append_to_timeline(
exocortex/ingestion/stages/note.py:376:                person,
exocortex/ingestion/stages/note.py:377:                entry,
exocortex/ingestion/stages/note.py:378:                deduplicate_key=meeting_filename
exocortex/ingestion/stages/company.py:317:        timeline_marker = "## Timeline"
exocortex/ingestion/stages/company.py:320:        entry = f"\n### {date_heading}\n[[{meeting_filename}|Meeting]] - {topics_summary}.\n"
```

| site | R/W | door used | dedupe key passed | key agrees with marker written? | affected by typed overload or marker-anchored dedupe? | notes |
|---|---|---|---|---|---|---|
| `ingestion/stages/note.py:375` | W | library primitive (string path), hand-composed kindless `### Month D, YYYY` entry | `meeting_filename` (the meeting note's stem, bare) | **no** — writes NO marker; the key is a substring of the entry's own wikilink, matched WHOLE-FILE (a mention of the meeting anywhere in the note, e.g. `## Notes`, suppresses the timeline entry) | **not on landing** (passes `str`). **Would change if migrated**: the typed path would find no marker and never dedupe — every hourly Granola re-run would then duplicate the meeting line | the largest automated writer by volume (every transcript, every attendee); pinned by exocortex WI-045 (`tests/test_transcript_pipeline.py:724+`) |
| `ingestion/stages/company.py:300-346` | W | raw file write (`Path.write_text`), company notes | whole-file `meeting_filename in content` | n/a — company note, no marker | no | outside `PersonRepository`; untouched by WI-033 |

Tests: `tests/test_transcript_pipeline.py` (WI-045 pin of the WI-020 `append_to_timeline` contract),
`tests/test_wi126_door_b.py` (`## Timeline` fixture bytes).

WI-006 premise check: `state/work-items.json` → `WI-006 idea "Email ingestion (Gmail threads)"`
(`docs/email-ingestion.md`); no exocortex work item or code builds relationship edges from vault intros.
The only relationship-flavoured items are WI-010 / WI-015 / WI-017 (all `idea`, scoring/dashboard). The
"first consumer" named at `docs/timeline-entry-relocation.md:492` has no code and no matching work item
in this tree today.

---

## orchestrator

HEAD: `5a2049e3c67f4cf9acd5e5e518cfdf1ced2e7c1b` — dirty: 0. No `append_to_timeline`, no
`append_timeline_entry`, no HTTP caller of `…/timeline` or `/api/introduce*`, no `introduced_by`
frontmatter read or write. Timeline writes go through HAL9000's `section-append` (LLM role) or a raw file
write (one-shot batch script). "Capture path": no timeline or intro write in `src/` (the
`contact_normalizer` / `queue_writer` capture writes frontmatter identifiers only — covered by the WI-032
audit).

Commands:
```
PAT='append_to_timeline|append_timeline_entry|TimelineEntry|timeline_entry|/timeline|## Timeline|introduced_by|introduced-by|intro-by|intro-to|\[intro\]|deduplicate_key'
grep -rnE --exclude-dir=.venv --exclude-dir=archive --exclude-dir=_archive --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=tests -I "$PAT" . | grep -vE '^\./docs/|SESSION_LOG|^\./state/'
grep -rniE "timeline|section-append|introduc" src/*.py bin/*.py bin/*.sh roles/*.yaml
```

Verbatim production lines:
```
roles/enricher.yaml:69:      -d '{"section": "<Timeline|Notes>", "content": "<text>", "operation": "append", "deduplicate_key": "<optional>"}'
roles/enricher.yaml:114:    -d '{"section": "Timeline", "operation": "append", "content": "### <Month Year>\n- <Date>: First interaction via <channel> — <summary>"}'
roles/enricher.yaml:129:  **WI-129 T9 — corroboration gate on `introduced_by`.** Append the introducer to
roles/enricher.yaml:140:    -d '{"section": "Notes", "operation": "append", "content": "\n- Introduced by [[<Introducer Name>]]", "deduplicate_key": "Introduced by [[<Introducer Name>]]"}'
bin/batch-contact-context.py:102:    return f"### {heading}\n- {date_fmt}: {summary}"
bin/batch-contact-context.py:107:    return "First interaction via" in body
bin/batch-contact-context.py:110:def extract_introducer_name(introduced_by) -> str | None:
bin/batch-contact-context.py:128:    return introducer.lower() in body.lower()
bin/batch-contact-context.py:256:                patch_vault_file(filename, "Timeline", "heading", "append", entry, args.dry_run)
bin/batch-contact-context.py:265:            introducer_name = extract_introducer_name(ctx.get("introduced_by"))
bin/batch-contact-context.py:268:                patch_vault_file(filename, "Notes", "heading", "append", content, args.dry_run)
src/morning_briefing.py:135:def parse_latest_meeting_filename(timeline_text: str) -> str | None:
```

| site | R/W | door used | dedupe key passed | key agrees with marker written? | affected by typed overload or marker-anchored dedupe? | notes |
|---|---|---|---|---|---|---|
| `roles/enricher.yaml:108-116` (first interaction → Timeline) | W | HAL9000 HTTP `section-append` (LLM curl), hand-composed kindless `### <Month Year>` | none | n/a — no marker | no | appends to the END of a newest-at-top section; WI-129 T9 readback |
| `roles/enricher.yaml:129-141` (WI-129 T9 introducer → **Notes**) | W | HAL9000 HTTP `section-append` | `Introduced by [[<name>]]` (section-scoped, Notes) | n/a — Notes, not Timeline | no | consumes contact-context's `introduced_by` RESPONSE field; the "dormant half-feature" WI-194 / HAL9000 WI-078 retire in favour of the accessor (fired zero times per WI-194's own log reading) |
| `bin/batch-contact-context.py:256`, `:268` | W | raw file write (`patch_vault_file` = regex splice + `write_text`, despite the name) | whole-body substring pre-checks `:107`, `:128` | n/a — no marker | no | one-shot March 2026 batch (last touched 2026-03-13); reads the contact-context RESPONSE `introduced_by`, not frontmatter; writes introducer to Notes |
| `src/morning_briefing.py:135-141` | R | prose (meeting-wikilink regex over the Timeline section text) | n/a | n/a | no | reads only meeting links; the `morning-briefing` skill calls it |

Tests: `tests/test_phase3_repair_scripts.py`, `tests/test_invariants.py`,
`tests/test_enricher_preprocessor.py` (`## Timeline` fixture bytes only).

---

## obsidian-schemas

HEAD: `bc2f11e23df9af2b1635c97ba0be7940a8ab2184` — dirty: 4. The primitive itself plus the linter's
timeline checks and its one timeline-writing fixer. `introduced_by`: zero hits in `obsidian_schemas/` and
`scripts/` (the key is not declared on `Person`).

Commands:
```
PAT='append_to_timeline|append_timeline_entry|TimelineEntry|timeline_entry|/timeline|## Timeline|introduced_by|introduced-by|intro-by|intro-to|\[intro\]|deduplicate_key'
grep -rnE --exclude-dir=.venv --exclude-dir=archive --exclude-dir=_archive --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=tests --exclude-dir=docs -I "$PAT" . | grep -vE '\.md:|state/'
grep -n "Timeline\|timeline" scripts/lint_vault.py
```

Verbatim production lines:
```
obsidian_schemas/repositories/person.py:1452:    def append_to_timeline(
obsidian_schemas/repositories/person.py:1456:        deduplicate_key: Optional[str] = None,
obsidian_schemas/repositories/person.py:1502:                if deduplicate_key and deduplicate_key in content:
obsidian_schemas/repositories/person.py:1640:                if deduplicate_key and existing_section and deduplicate_key in existing_section:
scripts/lint_vault.py:314:    timeline_headings = len(re.findall(r'^### ', timeline, re.MULTILINE))
scripts/lint_vault.py:768:            if mstem not in WIKILINK_PATTERN.findall(timeline):
scripts/lint_vault.py:816:    intro_pattern = re.compile(r"[Ii]ntroduc(?:ed|tion)[^[]*\[\[(@[^\]|]+)")
scripts/lint_vault.py:957:def _build_timeline_entry(meeting_vf: VaultFile) -> str:
scripts/lint_vault.py:975:        return f"### {heading}\n{link} - {topic_str}.\n"
scripts/lint_vault.py:1180:                            entry = _build_timeline_entry(mvf)
```

| site | R/W | door used | dedupe key passed | key agrees with marker written? | affected by typed overload or marker-anchored dedupe? | notes |
|---|---|---|---|---|---|---|
| `repositories/person.py:1452-1560` `append_to_timeline` | W (the primitive) | — | whole-file substring (`:1502`) | n/a | **this is the change site** | string+key path must stay byte-for-byte; every live caller uses it |
| `repositories/person.py:1640` `append_to_body_section` | W (sibling primitive) | — | section-scoped substring | n/a | no | backs HAL9000's `section-append`; not in WI-033 |
| `scripts/lint_vault.py:1176-1192` fixer `meeting_missing_from_timeline` | W | library `body_sections` round-trip through `vault_io` | none (the detector's own "stem not in Timeline links" is the guard) | n/a — kindless `### Month D, YYYY`, no marker | no | APPENDS to the end of Timeline (not prepend); a third heading shape the new report-only checks must not flag |
| `scripts/lint_vault.py:739-835` `check_timeline` (meeting links, `timeline_meeting_not_found`, `intro_not_symmetric`) + `:290-333` noise heuristic | R | prose regex over the Timeline section | n/a | n/a | no | `intro_not_symmetric` keys on the prose `Introduc(ed|tion) … [[@stem` — satisfied by BOTH WI-077 sentences (`Introduced by [[…` / `Introduced Dave to [[…`) and by legacy `[intro]` lines; no marker parsing. The three new WI-033 checks land beside these |

Tests (not sites): `tests/test_repositories.py:939-1051` (whole-file dedupe of the string path, and the
section-scoped sibling), `test_loud_fail_write.py:226`, `test_provenance_write_seam.py`,
`test_write_target_seam_wall.py`, `test_lint_vault_fix_rules.py`, `test_name_gate_wall.py`,
`test_name_gate_delta_rule.py`, `test_parser.py`, `fixture_vault.py`, `derivations.py`. The string-path
whole-file pins in `test_repositories.py` are the regression guard for "the existing signature keeps
working unchanged".

---

## mainspring

HEAD: `5fda1752a4640a46ad970d2e788e352d7e8ccbe7` — dirty: 0. The pattern sweep hits only `docs/`
(the identity recommendation that ruled "no stored field"). Widened sweep (`timeline|section-append|introduc|/api/entities`)
finds the dispatch cockpit's indirect intro writer; no timeline reader; its PATCH door
(`clients.py:152`, called from `server.py:852`) sends only `whatsapp` / `emails` / `phones`.

Commands:
```
PAT='append_to_timeline|append_timeline_entry|TimelineEntry|timeline_entry|/timeline|## Timeline|introduced_by|introduced-by|intro-by|intro-to|\[intro\]|deduplicate_key'
grep -rnE --exclude-dir=.venv --exclude-dir=venv --exclude-dir=archive --exclude-dir=_archive --exclude-dir=node_modules --exclude-dir=.git -I "$PAT" .
grep -rniE "timeline|section-append|introduc|/api/entities" --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=archive --exclude-dir=docs -I . | grep -v "SESSION_LOG\|\.md:"
```

Verbatim production lines:
```
prototype/dispatch/clients.py:21:INTRODUCE = "/Users/davewascha/Workspaces/HAL9000/bin/introduce.py"
prototype/dispatch/clients.py:201:    r = subprocess.run([INTRODUCE, *names], capture_output=True, text=True, timeout=120)
prototype/dispatch/server.py:431:        code, out, err = clients.introduce(job["names"])
prototype/dispatch/server.py:438:        # exit 1 = draft queued but a timeline write failed; the draft is real, so record it and surface the error
prototype/dispatch/server.py:444:            log("error", where="intro_timeline", task_id=tid, draft_id=out, error=err[-300:])
```

| site | R/W | door used | dedupe key passed | key agrees with marker written? | affected by typed overload or marker-anchored dedupe? | notes |
|---|---|---|---|---|---|---|
| `prototype/dispatch/server.py:431` → `clients.py:201` | W (indirect) | published CLI `HAL9000/bin/introduce.py` → HAL9000 HTTP `POST /api/introduce` → `introduce.py:707` | derived in HAL9000 | yes (inherits) | no | treats `introduce.py` exit 1 as "timeline write failed" — unchanged by WI-033 |

---

## personal-assistant

HEAD: `c3d760d8136e3656027fc1590681ee96d99b4004` — dirty: 3. Markdown-only repo of channel/agent rules;
no code. One instruction teaches a hand-composed Timeline write.

Commands:
```
PAT='append_to_timeline|append_timeline_entry|TimelineEntry|timeline_entry|/timeline|## Timeline|introduced_by|introduced-by|intro-by|intro-to|\[intro\]|deduplicate_key'
grep -rnE --exclude-dir=.venv --exclude-dir=venv --exclude-dir=archive --exclude-dir=_archive --exclude-dir=node_modules --exclude-dir=.git -I "$PAT" .
```

Verbatim production line:
```
channels/obsidian.md:103:  -d '{"section": "Timeline", "content": "### January 2026\n- 2026-01-13: First meeting", "deduplicate_key": "2026-01-13: First meeting"}'
```

| site | R/W | door used | dedupe key passed | key agrees with marker written? | affected by typed overload or marker-anchored dedupe? | notes |
|---|---|---|---|---|---|---|
| `channels/obsidian.md:100-104` | W (instruction) | HAL9000 HTTP `section-append` | prose, section-scoped | n/a — no marker | no | kindless month heading; bypasses the WI-058 renderer. `docs/intro-timeline-guarantee*.md` are historical design docs for what became `routers/introductions.py:433` |

---

## ~/.claude/skills and ~/.claude/agents

Not git repos (no HEAD). Only `.md` instruction files plus `agents/data/*.json` state.

Commands:
```
cd /Users/davewascha/.claude
PAT='append_to_timeline|append_timeline_entry|TimelineEntry|timeline_entry|/timeline|## Timeline|introduced_by|introduced-by|intro-by|intro-to|\[intro\]|deduplicate_key|section-append|Timeline'
grep -rnE --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=archive --exclude-dir=_archive -I "$PAT" skills agents
find skills agents -type f ! -name '*.md' | grep -v synced
```

Verbatim lines:
```
skills/new-person/SKILL.md:95:- **introduced_by** — who introduced you (extracted from first inbound email)
skills/new-person/SKILL.md:106:curl -s -X POST "http://localhost:8002/api/entities/person/<URL-encoded Name>/section-append" \
skills/new-person/SKILL.md:108:  -d '{"section": "Timeline", "content": "### <Month Year of first interaction>\n- <Date>: First interaction via <channel> — <subject/snippet summary>"}'
skills/new-person/SKILL.md:114:curl -s -X POST "http://localhost:8002/api/entities/person/<URL-encoded Name>/section-append" \
skills/morning-briefing/SKILL.md:91:- Find the Timeline section and extract meeting wikilinks using `parse_latest_meeting_filename()` from the helpers module
agents/scheduler.md:174:curl -s -w "\n%{http_code}" -X POST "http://localhost:8002/api/entities/person/<Name>/section-append" \
agents/scheduler.md:176:  -d '{"section": "Timeline", "operation": "prepend", "content": "### <Month Day, Year>\nScheduled call via email — <topic or '\''catch-up'\''>"}'
agents/introducer.md:131:Timelines are updated automatically by the HAL9000 `/api/introductions/draft` endpoint when `update_timelines` is `true` (the default). You do NOT need to manually patch Obsidian timeline entries.
agents/introducer.md:174:curl -s -w "\n%{http_code}" -X POST "http://localhost:8002/api/entities/person/<Name>/section-append" \
```

| site | R/W | door used | dedupe key passed | key agrees with marker written? | affected by typed overload or marker-anchored dedupe? | notes |
|---|---|---|---|---|---|---|
| `skills/new-person/SKILL.md:103-109` | W (instruction) | HAL9000 HTTP `section-append` | none | n/a — kindless month heading | no | bypasses the WI-058 renderer |
| `skills/new-person/SKILL.md:95`, `:111-116` | R (contact-context response) → W Notes | HAL9000 HTTP | none | n/a | no | the `introduced_by` RESPONSE field written as a Notes line; a third "Introduced by" prose writer beside enricher T9 and batch-contact-context |
| `agents/scheduler.md:171-177` | W (instruction) | HAL9000 HTTP `section-append`, `prepend` | none | n/a — `### Month Day, Year` with NO `[kind]` | no | same heading date form as the renderer but kindless — a note that `parse_markers()` must treat as unmarked |
| `agents/introducer.md:131`, `:172-176` | W (indirect / Notes) | HAL9000 HTTP `/api/introductions/draft` (→ `routers/introductions.py:433`) + `section-append` to Notes | prose (in HAL9000) | **no** (inherits `introductions.py:433`) | not on landing | retired agent (`CLAUDE.md`: "do not invoke") |
| `skills/morning-briefing/SKILL.md:91` | R | orchestrator `src/morning_briefing.py:135` | n/a | n/a | no | meeting-link reader only |

---

## Zero-hit repos

Command for each (run from `/Users/davewascha/Workspaces`):
`grep -rlE --exclude-dir=.venv --exclude-dir=venv --exclude-dir=archive --exclude-dir=_archive --exclude-dir=node_modules --exclude-dir=.git -I "$PAT" <repo>` → 0 files.

- Atlas — `af6ff7e3392e56d001ca61e4ac72dc7c1221c2a5`
- bike-transit-app — no commits (unborn HEAD)
- career — `e24295673c88c22deef779cdb00b328f33ea97bc`
- claude-harness — `c59b351f943b427f11ede4593ce3a9ee8edf39ab`
- claude-usage — `8bac924b1b4f0a37728556f4649fb6695817f508`
- clocktest — `657511d082f81fa2a82061c3d0c24cc245499525`
- coaching — `0293d9a4cf3875fbbc1900c20274ab4067d8f771`
- codebot — `60158ceb92d204395a6abd51ebf546b796ade3f1`
- context-efficiency — `929c37fae6bf2e17711ccdce808b23d90d08097f`
- control-room — `9d24bb529ca59477c167f7a55f495ae6032d4bfc`
- crawlers — no commits (unborn HEAD)
- gcse-revision — `244060be2563a41e2cf48b0c3cf44b5f52a80baa`
- gym-app — `4e5d37f641f0ff26872cf4dd17672150496507f9`
- HA — `7011498397365e85dee60c8a1ddb56f21003cefe`
- heatmiser — `b19b0dc225a8c32becc3f24537629883332c4803`
- mcp_excalidraw — `ec609277683d83da32bdcdf7ea7611fe87240be5`
- mini-infra — `1c9b08264915d6d15a4df56b7af8cf0d0193b8f2`
- photomanagement — `7b488ab00fe87e9e81a4f3f12be0afed89d5f438`
- publisher — `1ef34eb8d9cb973489ffc4562da6ffc80ae8524c`
- review-doc — `3de8f3f45a65f31e5589d4e8fb47138bb73e1d17`
- rooms — `750cea392ff5b90c80df3de68ddc5d892202368d`
- slidebot — `9f21716b1b824a67539c1bd7e5f40a9d65a3f18a`
- starlingexpenses — `557e33cd8bf5d1dbfd9780a1710eeedfc69074a2`
- the-system-explained — `8a305fd187770799898500ea209bd3e313625a88`
- todoist-to-obsidian — `3b06c973afcaaf7cddbed9bb0e4d1afdbcc22e8e`
- train-times — `ae3747f9307118d58270dd1b1eaf112655923c95`
- video-organizer — `f62868b7817f0a213e34eb2d7a2ee13e37be3566`
- watchers — `05b69a992db4ae019ca94adfc76463de6c936916`
- survey-tool — `f8e42ab89433c8a7e7a85cb3d3713e56561421ec` (one hit, `docs/BUILD_PLAN.md:497` `## Timeline Estimate` — a project-plan heading, not a vault section)
- workshop — `1f0e456f5b4912d573e86cb20490324a78f29abd` (hits only in `state/manifests/` / `state/manifest-runs/` prose naming the observed-intro door; widened `### `/`<!--` sweep hits are workshop's own doc-frame markers, unrelated)
- workshop-stable — skipped: worktree of `workshop`

---

## Cross-repo reading

**What breaks on WI-033's landing — ordered:**
1. **Nothing.** Every live `append_to_timeline` call passes a `str` entry; the typed overload and its
   marker-anchored dedupe have zero callers on the day. The one real obligation is the one the item already
   states: the string+key path must stay byte-identical, INCLUDING its whole-file substring semantics,
   because three live callers depend on that looseness (below). `tests/test_repositories.py:939-943`
   pins it.
2. **Latent, on migration (not on landing) — the three key/marker-disagreeing callers must NOT be moved to
   the typed path without a marker:** exocortex `ingestion/stages/note.py:375` (every Granola re-run would
   duplicate meeting lines — it relies on the prose key to be idempotent), HAL9000
   `routers/introductions.py:433` and `skills/introductions_skill.py:134` (retired, WI-062; undated prose
   key). Their correct fate is re-rendering through `TimelineEntry` with a discriminator (exocortex: the
   meeting stem is a natural one) or archival — never "same call, typed argument".
3. **Latent, on HAL9000's swap to the library `TimelineEntry`:** `core/timeline_entry.py:229` agrees by
   construction, so the only delta is SPAN — a marker a human moved out of `## Timeline` stops deduping.
   The AC-1 wall arm B(i) will flag a typed `append_to_timeline(person, entry)` call anywhere outside the
   exempt renderer module.
4. **Not affected, but a hole in the "one vocabulary" claim:** the `section-append` door accepts
   hand-composed Timeline entries from four instruction-driven callers (orchestrator enricher first
   interaction, new-person skill, scheduler agent, personal-assistant channel doc) and the linter's own
   fixer writes a fifth heading shape. All produce kindless, markerless headings; none is `[intro]` or
   `intro-by`, so WI-033's three report-only checks will not flag them — and `parse_markers()` /
   `introduced_by()` must return nothing for them (they are not intros).

**Who is waiting on `introduced_by(person)`:**
- **HAL9000 WI-078** (`idea`, `docs/retire-intro-extractor-one-reader.md`): retire
  `core/intro_extractor.py` and `routers/contact_context.py:241-250` "once the derived accessor exists" —
  the direct consumer.
- **orchestrator WI-194** (`idea`, `docs/inbound-introductions-typed-event.md`): retires
  `roles/enricher.yaml`'s T9 Notes write; the accessor is its premise (the write itself goes through
  HAL9000's WI-077 door).
- Downstream of WI-078 the three "Introduced by [[X]]" Notes writers (enricher T9, `new-person` skill,
  `bin/batch-contact-context.py`) lose their source field.
- **exocortex: no code and no work item waiting.** The WI-033 doc's "exocortex's parked WI-006
  (relationship edges)" does not match the tree (WI-006 = email ingestion, `idea`).
- mainspring, obsidian-schemas' own scripts: not waiting.

**Readers of the `introduced_by` FRONTMATTER key: ZERO, estate-wide.** Writers in code: ZERO. Every
`introduced_by` identifier in code is the `/api/contact-context` response field (HAL9000
`routers/contact_context.py:70`) or a consumer of that response (orchestrator
`bin/batch-contact-context.py:110,265`, `roles/enricher.yaml:129-141`, `skills/new-person/SKILL.md:95`).
The only path by which the key could re-enter a note is a client sending it through HAL9000's
generic PATCH (`routers/entities.py`, raw dict → `update_fields`) or POST create door — exactly what
WI-033's write-gate refusal closes. No live instruction tells any agent to do so.

**Unsure / flagged:**
- HAL9000 `skills/email_skill.py:121,203,210` — inserts `backend/` on `sys.path` then
  `from core.writer import append_entry`; inside the `backend_fastapi` process `core` (and `services`)
  are likely already bound to `backend_fastapi`'s own packages, so the import probably raises and the
  intro command fails before sending. Classified as a raw-file writer that is **probably unreachable** —
  not verified by running it.
- HAL9000 `routers/introductions.py:433` is on a mounted route (`/api/introductions/draft`) and
  `IntroductionsSkill` is a registered skill; both are "retired" by policy (CLAUDE.md, WI-036 Phase 2)
  but not mechanically dead. Classified as live-but-retired.
