# WI-033 precondition 4 — the HAL9000 cutover is MINTED: HAL9000 WI-082

Conductor record, 2026-09-28, committed as WI-033's fourth `kind: precondition` fence
(`docs/timeline-entry-relocation.md` → `## Write Targets`). It records an ACT, not a plan: the second half of
the relocation was minted in HAL9000's own backlog at this pause, through workshop's locked mint CLI, before
WI-033's criteria are frozen. No vault note name, no live identifier.

## The minted item

- **Id and project:** `WI-082`, project **HAL9000** (`/Users/davewascha/Workspaces/HAL9000`).
- **Doc:** `HAL9000/docs/timeline-entry-cutover-to-library.md`, stage `idea`, created 2026-09-28.
- **Owner:** HAL9000's backlog (its conductor / porter), not this tree. Minted by the obsidian-schemas
  conductor because D7 makes the mint this pause's act.
- **How it was minted, and read back:**

```
cd /Users/davewascha/Workspaces/workshop-stable && .venv/bin/python bin/mint-work-item.py \
    --project /Users/davewascha/Workspaces/HAL9000 \
    --title "Cutover: import obsidian_schemas.timeline_entry and delete core/timeline_entry.py (obsidian-schemas WI-033 second half)" \
    --filename timeline-entry-cutover-to-library.md --touched-by session --body-file <body>
→ INFO: Regenerated /Users/davewascha/Workspaces/HAL9000/state/work-items.json (82 items)
→ {"wi_id": "WI-082", "path": "/Users/davewascha/Workspaces/HAL9000/docs/timeline-entry-cutover-to-library.md"}
readback: state/work-items.json → WI-082 idea docs/timeline-entry-cutover-to-library.md; next_id 83
```

  The mint lives in HAL9000's WORKING TREE as of this record (the doc untracked, `state/work-items.json`
  regenerated); committing it is HAL9000's act, on Dave's word, and does not change the id — the locked
  mint advanced `next_id` to 83.

## One-line scope

Delete `backend_fastapi/core/timeline_entry.py` and repoint the WI-058 door (`routers/entities.py`), the
WI-077 router (`routers/introduce.py`) and `skills/contacts_skill.py` to `obsidian_schemas.timeline_entry`,
keeping HAL9000's HTTP surface, readback, resolution seam and kind choices unchanged.

## Re-entry condition (verbatim, D7's three clauses)

(1) This item is `done` and the library exports `TimelineEntry`, `render`, `parse_markers` and
`dedupe_key`; (2) the parity capture is re-run at HAL9000's then-HEAD and diffed against
`HAL9000_PARITY_ANCHOR` — a non-empty diff is the cutover's first finding and its scope grows to cover it;
(3) the cutover ships when HAL9000's own floor is green with its module deleted, its imports repointed, and
one live readback through its door showing bytes unchanged.

("This item" in clause (1) is obsidian-schemas WI-033.)

## The pin

HAL9000 HEAD the anchor pins: `d54430da9547a93525c6cc1b20cf781c9a63f82e` — the same value
`docs/wi-033-hal9000-timeline-entry-capture.md` declares and the library's `HAL9000_PARITY_ANCHOR` must equal.
The drift window a later reader can compute is `git -C HAL9000 log d54430da9547..<then-HEAD> --
backend_fastapi/core/timeline_entry.py backend_fastapi/routers/introduce.py`.
