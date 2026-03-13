#!/usr/bin/env python3
"""
Obsidian Vault Linter — checks completeness, link integrity, timeline
consistency, noise/garbage, and structural issues across all vault notes.

Usage:
    python scripts/lint_vault.py                          # Full report
    python scripts/lint_vault.py --category completeness  # Just completeness
    python scripts/lint_vault.py --type person             # Person notes only
    python scripts/lint_vault.py --severity warning        # Skip INFO
    python scripts/lint_vault.py --fix                     # Apply safe auto-fixes
    python scripts/lint_vault.py --report                  # JSON output
    python scripts/lint_vault.py -q                        # Summary only
"""

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml

from obsidian_schemas.body_sections import (
    ENTITY_BODY_CONFIG,
    ensure_sections_exist,
    get_expected_sections,
    parse_body_sections,
)
from obsidian_schemas.models import TYPE_TO_MODEL
from obsidian_schemas.parser import parse_frontmatter
from obsidian_schemas.writer import update_frontmatter_fields

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_VAULT = os.environ.get(
    "OBSIDIAN_VAULT_PATH",
    os.path.expanduser("~/Documents/Obsidian/DaveRemoteVault"),
)

SKIP_DIRS = {".obsidian", "Templates", "src", ".trash", "_quarantine", "_merged_dupes"}

WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]")

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @property
    def rank(self) -> int:
        return {"error": 0, "warning": 1, "info": 2}[self.value]


@dataclass
class LintIssue:
    file_path: Path
    check: str
    severity: Severity
    message: str
    category: str
    auto_fixable: bool = False
    suggested_fix: str = ""


@dataclass
class VaultFile:
    path: Path
    stem: str  # filename without .md
    frontmatter: dict[str, Any]
    body: str
    entity_type: str  # from frontmatter 'type', or ""
    is_at_prefixed: bool
    raw_content: str
    parse_error: Optional[str] = None


# ---------------------------------------------------------------------------
# Pass 1: Read & index the vault
# ---------------------------------------------------------------------------


def should_skip(path: Path, vault_root: Path) -> bool:
    rel = path.relative_to(vault_root)
    return any(part in SKIP_DIRS for part in rel.parts)


def read_vault(vault_path: Path) -> list[VaultFile]:
    files: list[VaultFile] = []
    for md in sorted(vault_path.rglob("*.md")):
        if should_skip(md, vault_path):
            continue
        try:
            raw = md.read_text(encoding="utf-8")
        except Exception:
            continue

        stem = md.stem
        is_at = stem.startswith("@")
        parse_error = None

        # Parse frontmatter
        try:
            fm, body = parse_frontmatter(raw)
        except Exception as exc:
            fm, body = {}, raw
            parse_error = str(exc)

        # Detect malformed frontmatter (starts with --- but didn't parse)
        if raw.startswith("---") and not fm and parse_error is None:
            # Could be bad YAML — try to get a better error
            match = re.match(r"^---\n(.*?)\n---", raw, re.DOTALL)
            if match:
                try:
                    yaml.safe_load(match.group(1))
                except yaml.YAMLError as ye:
                    parse_error = str(ye)

        etype = fm.get("type", "") if isinstance(fm, dict) else ""

        files.append(
            VaultFile(
                path=md,
                stem=stem,
                frontmatter=fm if isinstance(fm, dict) else {},
                body=body,
                entity_type=str(etype) if etype else "",
                is_at_prefixed=is_at,
                raw_content=raw,
                parse_error=parse_error,
            )
        )
    return files


MEETING_DATE_PATTERN = re.compile(r"^Meeting (\d{8})\b")


def build_indexes(files: list[VaultFile]) -> dict[str, Any]:
    # All stems (for wikilink resolution)
    all_stems: set[str] = set()
    # Stem → VaultFile
    stem_to_file: dict[str, VaultFile] = {}
    # Person index: stem → VaultFile (type=person)
    persons: dict[str, VaultFile] = {}
    # Company index: stem → VaultFile (type=company)
    companies: dict[str, VaultFile] = {}
    # Meeting index: stem → VaultFile (type=meeting)
    meetings: dict[str, VaultFile] = {}
    # Incoming wikilinks: stem → set of stems that link to it
    incoming_links: dict[str, set[str]] = defaultdict(set)
    # Stripped stem → actual stem (handles trailing whitespace in filenames)
    stripped_to_stem: dict[str, str] = {}
    # Meeting date → list of meeting stems (for date-based lookup)
    meeting_date_index: dict[str, list[str]] = defaultdict(list)

    for vf in files:
        all_stems.add(vf.stem)
        stem_to_file[vf.stem] = vf
        # Index stripped stem for fuzzy wikilink matching
        stripped = vf.stem.strip()
        if stripped != vf.stem:
            stripped_to_stem[stripped] = vf.stem

        if vf.entity_type == "person":
            persons[vf.stem] = vf
        elif vf.entity_type == "company":
            companies[vf.stem] = vf
        elif vf.entity_type == "meeting":
            meetings[vf.stem] = vf
            # Extract date for date-based lookup
            m = MEETING_DATE_PATTERN.match(vf.stem)
            if m:
                meeting_date_index[m.group(1)].append(vf.stem)

    # Build incoming links from body wikilinks
    for vf in files:
        for target in WIKILINK_PATTERN.findall(vf.body):
            target = target.strip()
            incoming_links[target].add(vf.stem)

    # Reverse index: company stem → set of person stems whose company field matches
    persons_by_company: dict[str, set[str]] = defaultdict(set)
    for pstem, pvf in persons.items():
        company_val = str(pvf.frontmatter.get("company", "")).strip()
        if company_val:
            # Try exact match first, then @-prefixed
            for cstem in [f"@{company_val}", company_val]:
                if cstem in companies:
                    persons_by_company[cstem].add(pstem)
                    break

    return {
        "all_stems": all_stems,
        "stem_to_file": stem_to_file,
        "persons": persons,
        "companies": companies,
        "meetings": meetings,
        "incoming_links": incoming_links,
        "persons_by_company": persons_by_company,
        "stripped_to_stem": stripped_to_stem,
        "meeting_date_index": meeting_date_index,
    }


# ---------------------------------------------------------------------------
# Person tier classification
# ---------------------------------------------------------------------------


def classify_person_tier(vf: VaultFile) -> str:
    """Return 'active' or 'stub'.

    A person is 'active' (not garbage) if ANY of:
      - auto_created is false/missing
      - 2+ meeting wikilinks in Timeline
      - manual content in To Discuss or Notes
      - 1+ meeting AND has a real email address
      - 1+ meeting AND has a company set
      - 2+ plain-text timeline entries (### headings — calendar events, intros)
    """
    fm = vf.frontmatter
    auto = fm.get("auto_created")
    # Normalize auto_created
    if isinstance(auto, str):
        auto = auto.lower() in ("true", "yes", "1")
    elif auto is None:
        auto = False

    if not auto:
        return "active"

    # Count meetings in timeline
    sections = parse_body_sections(vf.body)
    timeline = sections.get("Timeline", "")
    meeting_links = WIKILINK_PATTERN.findall(timeline)
    meeting_count = len(meeting_links)

    # Count all ### headings (includes plain-text entries from calendar/intros)
    timeline_headings = len(re.findall(r'^### ', timeline, re.MULTILINE))

    # Check for manual content
    to_discuss = sections.get("To Discuss", "").strip()
    notes = sections.get("Notes", "").strip()
    has_manual = bool(to_discuss) or bool(notes)

    # Check for real contact data
    emails = fm.get("emails", []) or []
    has_email = len(emails) > 0
    company = str(fm.get("company", "")).strip()
    has_company = bool(company)

    if meeting_count >= 2 or has_manual:
        return "active"
    # 1 meeting + real contact data = legitimate, not a stub
    if meeting_count >= 1 and (has_email or has_company):
        return "active"
    # Plain-text timeline entries (calendar events, intros) count too
    if timeline_headings >= 2:
        return "active"
    return "stub"


# ---------------------------------------------------------------------------
# Checks — organized by category
# ---------------------------------------------------------------------------

# Each check function yields LintIssue instances.


def check_structural(files: list[VaultFile], idx: dict) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for vf in files:
        # parse_error
        if vf.parse_error:
            issues.append(
                LintIssue(
                    vf.path, "parse_error", Severity.ERROR,
                    f"YAML parse error: {vf.parse_error}",
                    "structural",
                )
            )
            continue

        # no_frontmatter — @ prefixed with no frontmatter
        if vf.is_at_prefixed and not vf.frontmatter:
            issues.append(
                LintIssue(
                    vf.path, "no_frontmatter", Severity.ERROR,
                    "@ prefixed file with no frontmatter",
                    "structural",
                )
            )
            continue

        # missing_type — @ prefixed with frontmatter but no type
        if vf.is_at_prefixed and vf.frontmatter and not vf.entity_type:
            issues.append(
                LintIssue(
                    vf.path, "missing_type", Severity.ERROR,
                    "@ prefixed file with frontmatter but no 'type' field",
                    "structural",
                )
            )
            continue

        if not vf.entity_type:
            continue

        # Skip types the linter doesn't model (moc, recipe, project, etc.)
        if vf.entity_type not in TYPE_TO_MODEL:
            continue

        # field_type_mismatch — auto_created as string
        raw_auto = vf.frontmatter.get("auto_created")
        if isinstance(raw_auto, str):
            issues.append(
                LintIssue(
                    vf.path, "field_type_mismatch", Severity.WARNING,
                    f"auto_created is string '{raw_auto}' instead of bool",
                    "structural",
                    auto_fixable=True,
                    suggested_fix=f"auto_created: {raw_auto.lower() in ('true', 'yes', '1')}",
                )
            )

        # missing_body_sections
        expected = get_expected_sections(vf.entity_type)
        if expected:
            sections = parse_body_sections(vf.body)
            missing = [s for s in expected if s not in sections]
            if missing:
                issues.append(
                    LintIssue(
                        vf.path, "missing_body_sections", Severity.WARNING,
                        f"Missing sections: {', '.join(missing)}",
                        "structural",
                        auto_fixable=True,
                        suggested_fix=f"Add sections: {', '.join(missing)}",
                    )
                )

    return issues


def check_completeness(files: list[VaultFile], idx: dict) -> list[LintIssue]:
    issues: list[LintIssue] = []

    for vf in files:
        if vf.parse_error:
            continue

        if vf.entity_type == "person":
            tier = classify_person_tier(vf)
            if tier != "active":
                continue  # stubs handled in noise

            fm = vf.frontmatter
            name = fm.get("name", "")
            if not name or not str(name).strip():
                suggested_name = vf.stem.lstrip("@")
                issues.append(
                    LintIssue(
                        vf.path, "person_missing_name", Severity.ERROR,
                        f"Empty name (suggest: '{suggested_name}')",
                        "completeness",
                        auto_fixable=True,
                        suggested_fix=f"name: \"{suggested_name}\"",
                    )
                )

            emails = fm.get("emails", [])
            if not emails or (isinstance(emails, list) and not any(emails)):
                issues.append(
                    LintIssue(
                        vf.path, "person_no_email", Severity.WARNING,
                        "Active person with no email",
                        "completeness",
                    )
                )

            linkedin = fm.get("linkedin", "")
            if not linkedin or not str(linkedin).strip():
                issues.append(
                    LintIssue(
                        vf.path, "person_no_linkedin", Severity.INFO,
                        "No LinkedIn URL",
                        "completeness",
                    )
                )

            company = fm.get("company", "")
            if not company or not str(company).strip():
                issues.append(
                    LintIssue(
                        vf.path, "person_no_company", Severity.INFO,
                        "No company",
                        "completeness",
                    )
                )

        elif vf.entity_type == "company":
            fm = vf.frontmatter
            name = fm.get("name", "")
            if not name or not str(name).strip():
                issues.append(
                    LintIssue(
                        vf.path, "company_missing_name", Severity.ERROR,
                        "Empty company name",
                        "completeness",
                    )
                )

            website = fm.get("website", "")
            if not website or not str(website).strip():
                issues.append(
                    LintIssue(
                        vf.path, "company_no_website", Severity.INFO,
                        "No website",
                        "completeness",
                    )
                )

    return issues


def check_links(files: list[VaultFile], idx: dict) -> list[LintIssue]:
    issues: list[LintIssue] = []
    all_stems = idx["all_stems"]
    companies = idx["companies"]

    for vf in files:
        if vf.parse_error:
            continue

        # person_company_not_found
        if vf.entity_type == "person":
            company_name = vf.frontmatter.get("company", "")
            if company_name and str(company_name).strip():
                company_stem = f"@{company_name}"
                if company_stem not in all_stems:
                    issues.append(
                        LintIssue(
                            vf.path, "person_company_not_found", Severity.WARNING,
                            f"Company '{company_name}' not found (no @{company_name}.md)",
                            "links",
                        )
                    )

        # meeting_attendee_not_found
        if vf.entity_type == "meeting":
            attendees = vf.frontmatter.get("attendees", [])
            if isinstance(attendees, list):
                for att in attendees:
                    att_str = str(att).strip()
                    if not att_str:
                        continue
                    att_stem = f"@{att_str}"
                    if att_stem not in all_stems:
                        issues.append(
                            LintIssue(
                                vf.path, "meeting_attendee_not_found", Severity.WARNING,
                                f"Attendee '{att_str}' not found (no @{att_str}.md)",
                                "links",
                            )
                        )

        # company_people_link_broken
        if vf.entity_type == "company":
            sections = parse_body_sections(vf.body)
            people_section = sections.get("People", "")
            for link_target in WIKILINK_PATTERN.findall(people_section):
                link_target = link_target.strip()
                if link_target not in all_stems:
                    issues.append(
                        LintIssue(
                            vf.path, "company_people_link_broken", Severity.WARNING,
                            f"People section links to [[{link_target}]] but it doesn't exist",
                            "links",
                        )
                    )

        # broken_wikilink — any wikilink in body that doesn't resolve
        if vf.is_at_prefixed:
            stripped_to_stem = idx.get("stripped_to_stem", {})
            meeting_date_idx = idx.get("meeting_date_index", {})
            for raw_target in WIKILINK_PATTERN.findall(vf.body):
                link_target = raw_target.strip()
                # Resolve: exact match, or trailing-whitespace match
                # (Obsidian strips trailing whitespace from link targets)
                if link_target in all_stems:
                    continue
                if link_target in stripped_to_stem:
                    continue  # valid — resolves after stripping

                # Truly broken — try date-based match for meeting links
                correct_stem = None
                m = MEETING_DATE_PATTERN.match(link_target)
                if m:
                    date_key = m.group(1)
                    candidates = meeting_date_idx.get(date_key, [])
                    if len(candidates) == 1:
                        correct_stem = candidates[0]

                if correct_stem:
                    issues.append(
                        LintIssue(
                            vf.path, "broken_wikilink", Severity.WARNING,
                            f"[[{link_target}]] doesn't resolve (fixable → [[{correct_stem}]])",
                            "links",
                            auto_fixable=True,
                            suggested_fix=json.dumps({
                                "old": link_target, "new": correct_stem,
                            }),
                        )
                    )
                else:
                    issues.append(
                        LintIssue(
                            vf.path, "broken_wikilink", Severity.WARNING,
                            f"[[{link_target}]] doesn't resolve to any vault file",
                            "links",
                        )
                    )

        # person_not_in_company_people
        if vf.entity_type == "person":
            company_name = vf.frontmatter.get("company", "")
            if company_name and str(company_name).strip():
                company_stem = f"@{company_name}"
                if company_stem in companies:
                    company_vf = companies[company_stem]
                    sections = parse_body_sections(company_vf.body)
                    people_section = sections.get("People", "")
                    people_links = WIKILINK_PATTERN.findall(people_section)
                    if vf.stem not in people_links:
                        issues.append(
                            LintIssue(
                                vf.path, "person_not_in_company_people", Severity.INFO,
                                f"Lists company '{company_name}' but not in that company's People section",
                                "links",
                            )
                        )

    return issues


def check_timeline(files: list[VaultFile], idx: dict) -> list[LintIssue]:
    issues: list[LintIssue] = []
    meetings = idx["meetings"]
    persons = idx["persons"]
    all_stems = idx["all_stems"]

    # meeting_missing_from_timeline: person in meeting attendees but meeting
    # not in person's timeline
    for mstem, mvf in meetings.items():
        attendees = mvf.frontmatter.get("attendees", [])
        if not isinstance(attendees, list):
            continue
        for att in attendees:
            att_str = str(att).strip()
            if not att_str:
                continue
            person_stem = f"@{att_str}"
            if person_stem not in persons:
                continue  # already caught by meeting_attendee_not_found
            pvf = persons[person_stem]
            sections = parse_body_sections(pvf.body)
            timeline = sections.get("Timeline", "")
            # Check if meeting stem appears as a wikilink in timeline
            if mstem not in WIKILINK_PATTERN.findall(timeline):
                issues.append(
                    LintIssue(
                        pvf.path, "meeting_missing_from_timeline", Severity.WARNING,
                        f"Attended [[{mstem}]] but it's not in Timeline",
                        "timeline",
                        auto_fixable=True,
                        suggested_fix=mstem,  # meeting stem, used by fixer
                    )
                )

    # timeline_meeting_not_found: timeline references a meeting that doesn't exist
    stripped_to_stem = idx.get("stripped_to_stem", {})
    for pstem, pvf in persons.items():
        sections = parse_body_sections(pvf.body)
        timeline = sections.get("Timeline", "")
        for link in WIKILINK_PATTERN.findall(timeline):
            link = link.strip()
            if link.startswith("Meeting ") and link not in all_stems:
                # Check if it resolves after stripping (trailing-space filenames)
                if link in stripped_to_stem:
                    continue
                issues.append(
                    LintIssue(
                        pvf.path, "timeline_meeting_not_found", Severity.WARNING,
                        f"Timeline references [[{link}]] but meeting doesn't exist",
                        "timeline",
                    )
                )

    # meeting_empty_content
    for mstem, mvf in meetings.items():
        sections = parse_body_sections(mvf.body)
        content_sections = ["Summary", "Decisions", "Actions", "Commitments", "Key Topics"]
        all_empty = all(
            not sections.get(s, "").strip() for s in content_sections
        )
        if all_empty:
            issues.append(
                LintIssue(
                    mvf.path, "meeting_empty_content", Severity.WARNING,
                    "Meeting note has no content in any body section",
                    "timeline",
                )
            )

    # intro_not_symmetric: A's timeline mentions introducing B but B doesn't
    # mention A.  Pattern: "Introduced [[target]]" in timeline.
    intro_pattern = re.compile(r"[Ii]ntroduc(?:ed|tion)[^[]*\[\[(@[^\]|]+)")
    for pstem, pvf in persons.items():
        sections = parse_body_sections(pvf.body)
        timeline = sections.get("Timeline", "")
        for match in intro_pattern.finditer(timeline):
            target_stem = match.group(1).strip()
            if target_stem in persons:
                target_vf = persons[target_stem]
                target_sections = parse_body_sections(target_vf.body)
                target_timeline = target_sections.get("Timeline", "")
                # Check if person stem appears in target's timeline near "intro"
                if pstem not in target_timeline:
                    issues.append(
                        LintIssue(
                            pvf.path, "intro_not_symmetric", Severity.WARNING,
                            f"Introduces [[{target_stem}]] but {target_stem}'s timeline doesn't mention {pstem}",
                            "timeline",
                        )
                    )

    return issues


def check_noise(files: list[VaultFile], idx: dict) -> list[LintIssue]:
    issues: list[LintIssue] = []
    incoming = idx["incoming_links"]
    companies = idx["companies"]

    for vf in files:
        if vf.parse_error:
            continue

        # garbage_candidate_person — stub person
        if vf.entity_type == "person":
            tier = classify_person_tier(vf)
            if tier == "stub":
                issues.append(
                    LintIssue(
                        vf.path, "garbage_candidate_person", Severity.INFO,
                        "Auto-created stub: 0-1 meetings, no manual content",
                        "noise",
                    )
                )

        # garbage_candidate_company — tiered criteria:
        # auto_created AND no website AND no industry AND no notes
        # AND no people links AND no persons referencing it
        # AND 0-1 timeline meetings (drive-by mentions from transcripts)
        if vf.entity_type == "company":
            fm = vf.frontmatter
            auto = fm.get("auto_created")
            if isinstance(auto, str):
                auto = auto.lower() in ("true", "yes", "1")
            if auto:
                website = str(fm.get("website", "")).strip()
                industry = str(fm.get("industry", "")).strip()
                sections = parse_body_sections(vf.body)
                notes = sections.get("Notes", "").strip()
                # Check timeline for meeting links
                timeline = sections.get("Timeline", "")
                timeline_links = WIKILINK_PATTERN.findall(timeline)
                # Check People section for person links
                people_section = sections.get("People", "")
                people_links = WIKILINK_PATTERN.findall(people_section)
                # Check if any person notes have company field pointing here
                persons_by_co = idx.get("persons_by_company", {})
                referencing_persons = persons_by_co.get(vf.stem, set())

                has_people = bool(people_links) or bool(referencing_persons)

                if not website and not industry and not notes and not has_people:
                    if len(timeline_links) <= 1:
                        issues.append(
                            LintIssue(
                                vf.path, "garbage_candidate_company", Severity.INFO,
                                "Auto-created company: 0-1 meetings, no people, no data",
                                "noise",
                            )
                        )

        # orphaned_note — @ prefixed with zero incoming wikilinks
        if vf.is_at_prefixed and vf.entity_type:
            if not incoming.get(vf.stem):
                issues.append(
                    LintIssue(
                        vf.path, "orphaned_note", Severity.INFO,
                        "Zero incoming wikilinks from any other note",
                        "noise",
                    )
                )

    # possible_duplicate — two @ files with very similar names
    at_stems = sorted(
        vf.stem for vf in files if vf.is_at_prefixed and vf.entity_type
    )
    seen_pairs: set[tuple[str, str]] = set()
    for i, s1 in enumerate(at_stems):
        name1 = s1.lstrip("@").lower().strip()
        if len(name1) < 3:
            continue
        for s2 in at_stems[i + 1 : i + 20]:  # only check nearby (sorted)
            name2 = s2.lstrip("@").lower().strip()
            if len(name2) < 3:
                continue
            pair = (s1, s2)
            if pair in seen_pairs:
                continue
            # Check similarity
            ratio = SequenceMatcher(None, name1, name2).ratio()
            if ratio >= 0.80 and name1 != name2:
                # Also check if one is prefix/abbreviation of the other
                seen_pairs.add(pair)
                issues.append(
                    LintIssue(
                        idx["stem_to_file"][s1].path,
                        "possible_duplicate",
                        Severity.INFO,
                        f"Similar to [[{s2}]] (similarity: {ratio:.0%})",
                        "noise",
                    )
                )

    return issues


# ---------------------------------------------------------------------------
# Auto-fix
# ---------------------------------------------------------------------------


def _format_date_heading(date_str: str) -> str:
    """Convert '2026-01-23' to 'January 23, 2026'."""
    from datetime import datetime as _dt

    try:
        d = _dt.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%B %-d, %Y")
    except (ValueError, TypeError):
        return date_str


def _build_timeline_entry(meeting_vf: VaultFile) -> str:
    """Build a timeline entry string from a meeting VaultFile.

    Format:
        ### January 23, 2026
        [[Meeting 20260123 - Title|Meeting]] - topic1, topic2, topic3.
    """
    fm = meeting_vf.frontmatter
    date_str = str(fm.get("date", ""))
    heading = _format_date_heading(date_str)
    topics = fm.get("topics", [])
    if isinstance(topics, list) and topics:
        topic_str = ", ".join(str(t) for t in topics[:3])
    else:
        topic_str = ""

    link = f"[[{meeting_vf.stem}|Meeting]]"
    if topic_str:
        return f"### {heading}\n{link} - {topic_str}.\n"
    else:
        return f"### {heading}\n{link}\n"


def apply_fixes(issues: list[LintIssue], vault_path: Path,
                idx: Optional[dict] = None) -> int:
    fixed = 0
    # Group by file to batch fixes
    by_file: dict[Path, list[LintIssue]] = defaultdict(list)
    for issue in issues:
        if issue.auto_fixable:
            by_file[issue.file_path].append(issue)

    meetings = idx.get("meetings", {}) if idx else {}

    for fpath, file_issues in by_file.items():
        try:
            content = fpath.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(content)
            changed = False

            # Collect wikilink replacements (applied on raw content)
            wikilink_replacements: list[tuple[str, str]] = []

            for issue in file_issues:
                if issue.check == "field_type_mismatch":
                    raw = fm.get("auto_created")
                    if isinstance(raw, str):
                        fm["auto_created"] = raw.lower() in ("true", "yes", "1")
                        changed = True
                        fixed += 1

                elif issue.check == "person_missing_name":
                    name = fpath.stem.lstrip("@")
                    fm["name"] = name
                    changed = True
                    fixed += 1

                elif issue.check == "missing_body_sections":
                    etype = fm.get("type", "")
                    expected = get_expected_sections(etype)
                    if expected:
                        body = ensure_sections_exist(body, expected)
                        changed = True
                        fixed += 1

                elif issue.check == "meeting_missing_from_timeline":
                    mstem = issue.suggested_fix  # meeting stem
                    if mstem and mstem in meetings:
                        mvf = meetings[mstem]
                        entry = _build_timeline_entry(mvf)
                        sections = parse_body_sections(body)
                        timeline = sections.get("Timeline", "")
                        # Append entry to timeline
                        if timeline and not timeline.endswith("\n"):
                            timeline += "\n"
                        timeline += "\n" + entry
                        sections["Timeline"] = timeline
                        from obsidian_schemas.body_sections import write_body_sections

                        body = write_body_sections(sections)
                        changed = True
                        fixed += 1

                elif issue.check == "broken_wikilink":
                    try:
                        fix_data = json.loads(issue.suggested_fix)
                        old_link = fix_data["old"]
                        new_link = fix_data["new"]
                        wikilink_replacements.append((old_link, new_link))
                    except (json.JSONDecodeError, KeyError):
                        pass

            if changed:
                # Write the full file with updated frontmatter + body
                from obsidian_schemas.writer import write_frontmatter as _wfm

                yaml_str = _wfm(fm)
                content = f"---\n{yaml_str}---\n{body}"
                fpath.write_text(content, encoding="utf-8")

            # Apply wikilink replacements on the current file content
            if wikilink_replacements:
                content = fpath.read_text(encoding="utf-8")
                wl_changed = False
                for old_link, new_link in wikilink_replacements:
                    # Replace both [[old]] and [[old|alias]] forms
                    for old_pat, new_pat in [
                        (f"[[{old_link}]]", f"[[{new_link}]]"),
                        (f"[[{old_link}|", f"[[{new_link}|"),
                    ]:
                        if old_pat in content:
                            content = content.replace(old_pat, new_pat)
                            wl_changed = True
                            fixed += 1
                            break  # only count once per replacement pair
                if wl_changed:
                    fpath.write_text(content, encoding="utf-8")

        except Exception as exc:
            print(f"  Fix error on {fpath.name}: {exc}", file=sys.stderr)

    return fixed


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

CATEGORY_ORDER = ["completeness", "links", "timeline", "noise", "structural"]
CATEGORY_LABELS = {
    "completeness": "COMPLETENESS",
    "links": "LINK INTEGRITY",
    "timeline": "TIMELINE",
    "noise": "NOISE & GARBAGE",
    "structural": "STRUCTURAL",
}


def print_summary(issues: list[LintIssue], vault_path: Path, file_count: int,
                   elapsed: float) -> None:
    errors = sum(1 for i in issues if i.severity == Severity.ERROR)
    warnings = sum(1 for i in issues if i.severity == Severity.WARNING)
    infos = sum(1 for i in issues if i.severity == Severity.INFO)
    fixable = sum(1 for i in issues if i.auto_fixable)

    print(f"\nVault Lint Report — {vault_path}")
    print("=" * 72)
    print(
        f"{file_count:,} files scanned in {elapsed:.1f}s | "
        f"{len(issues):,} issues ({errors} errors, {warnings} warnings, {infos} info)"
    )

    # Group by category then check
    by_cat: dict[str, dict[str, list[LintIssue]]] = defaultdict(lambda: defaultdict(list))
    for issue in issues:
        by_cat[issue.category][issue.check].append(issue)

    for cat in CATEGORY_ORDER:
        checks = by_cat.get(cat)
        if not checks:
            continue
        total = sum(len(v) for v in checks.values())
        print(f"\n{CATEGORY_LABELS.get(cat, cat.upper())} ({total:,} issues)")
        for check_name, check_issues in sorted(
            checks.items(), key=lambda x: (x[1][0].severity.rank, x[0])
        ):
            count = len(check_issues)
            sev = check_issues[0].severity.value
            fix_note = ""
            fix_count = sum(1 for i in check_issues if i.auto_fixable)
            if fix_count:
                fix_note = f"  [{fix_count} auto-fixable]"
            pad = 36 - len(check_name)
            dots = "." * max(pad, 2)
            print(f"  {check_name} {dots} {count:,} {sev}s{fix_note}")

    if fixable:
        print(f"\nAuto-fixable: {fixable} issues. Run with --fix to apply.")
    print()


def print_full_report(issues: list[LintIssue], vault_path: Path,
                       file_count: int, elapsed: float) -> None:
    print_summary(issues, vault_path, file_count, elapsed)

    # Also list individual issues per category, limited
    by_cat: dict[str, list[LintIssue]] = defaultdict(list)
    for issue in issues:
        by_cat[issue.category].append(issue)

    for cat in CATEGORY_ORDER:
        cat_issues = by_cat.get(cat, [])
        if not cat_issues:
            continue

        # Show errors and warnings individually (not info — too many)
        important = [i for i in cat_issues if i.severity != Severity.INFO]
        if not important:
            continue

        print(f"\n--- {CATEGORY_LABELS.get(cat, cat.upper())} details ---")
        for issue in sorted(important, key=lambda i: (i.severity.rank, i.check)):
            sev = issue.severity.value.upper()[:4]
            rel = issue.file_path.name
            print(f"  [{sev}] {rel}: {issue.message}")

        if len(important) > 100:
            print(f"  ... and {len(important) - 100} more")


def print_json(issues: list[LintIssue], vault_path: Path, file_count: int,
                elapsed: float) -> None:
    data = {
        "vault": str(vault_path),
        "files_scanned": file_count,
        "elapsed_seconds": round(elapsed, 2),
        "total_issues": len(issues),
        "issues": [
            {
                "file": str(i.file_path),
                "check": i.check,
                "severity": i.severity.value,
                "message": i.message,
                "category": i.category,
                "auto_fixable": i.auto_fixable,
            }
            for i in issues
        ],
    }
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def quarantine_garbage(
    issues: list[LintIssue], vault_path: Path,
) -> int:
    """Move garbage candidates to _quarantine/ subfolders for review."""
    quarantine_dir = vault_path / "_quarantine"
    moved = 0
    for issue in issues:
        if not issue.check.startswith("garbage_candidate_"):
            continue
        src = issue.file_path
        if not src.exists():
            continue
        # Determine subfolder by entity type
        if issue.check == "garbage_candidate_company":
            dest_dir = quarantine_dir / "companies"
        elif issue.check == "garbage_candidate_person":
            dest_dir = quarantine_dir / "persons"
        else:
            dest_dir = quarantine_dir / "other"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        if dest.exists():
            continue
        src.rename(dest)
        moved += 1
    return moved


def run_lint(
    vault_path: Path,
    categories: Optional[list[str]] = None,
    entity_types: Optional[list[str]] = None,
    min_severity: Optional[Severity] = None,
    do_fix: bool = False,
    do_quarantine: bool = False,
    quiet: bool = False,
    json_report: bool = False,
) -> list[LintIssue]:
    t0 = time.time()

    # Pass 1: read vault
    all_files = read_vault(vault_path)

    # Build indexes from ALL files (needed for link resolution)
    idx = build_indexes(all_files)

    # Filter by entity type if requested (for check execution only)
    files = all_files
    if entity_types:
        files = [f for f in all_files if f.entity_type in entity_types]

    # Pass 2: run checks
    all_issues: list[LintIssue] = []

    check_fns = {
        "structural": check_structural,
        "completeness": check_completeness,
        "links": check_links,
        "timeline": check_timeline,
        "noise": check_noise,
    }

    for cat, fn in check_fns.items():
        if categories and cat not in categories:
            continue
        all_issues.extend(fn(files, idx))

    # Filter by severity
    if min_severity:
        all_issues = [i for i in all_issues if i.severity.rank <= min_severity.rank]

    # Fix, then re-scan to show post-fix state
    if do_fix:
        fixable = [i for i in all_issues if i.auto_fixable]
        if fixable:
            fixed = apply_fixes(fixable, vault_path, idx)
            print(f"Fixed {fixed} issues. Re-scanning...\n")
            # Re-scan to report post-fix state
            all_files = read_vault(vault_path)
            idx = build_indexes(all_files)
            files = all_files
            if entity_types:
                files = [f for f in all_files if f.entity_type in entity_types]
            all_issues = []
            for cat, fn in check_fns.items():
                if categories and cat not in categories:
                    continue
                all_issues.extend(fn(files, idx))
            if min_severity:
                all_issues = [i for i in all_issues if i.severity.rank <= min_severity.rank]
        else:
            print("No auto-fixable issues found.")

    # Quarantine garbage candidates
    if do_quarantine:
        garbage = [i for i in all_issues if i.check.startswith("garbage_candidate_")]
        if garbage:
            moved = quarantine_garbage(garbage, vault_path)
            print(f"Quarantined {moved} files to _quarantine/. Re-scanning...\n")
            # Re-scan to report post-quarantine state
            all_files = read_vault(vault_path)
            idx = build_indexes(all_files)
            files = all_files
            if entity_types:
                files = [f for f in all_files if f.entity_type in entity_types]
            all_issues = []
            for cat, fn in check_fns.items():
                if categories and cat not in categories:
                    continue
                all_issues.extend(fn(files, idx))
            if min_severity:
                all_issues = [i for i in all_issues if i.severity.rank <= min_severity.rank]
        else:
            print("No garbage candidates to quarantine.")

    elapsed = time.time() - t0

    # Report
    file_count = len(all_files)
    if json_report:
        print_json(all_issues, vault_path, file_count, elapsed)
    elif quiet:
        print_summary(all_issues, vault_path, file_count, elapsed)
    else:
        print_full_report(all_issues, vault_path, file_count, elapsed)

    return all_issues


def main():
    parser = argparse.ArgumentParser(description="Obsidian Vault Linter")
    parser.add_argument(
        "--vault", type=str, default=DEFAULT_VAULT,
        help="Path to Obsidian vault",
    )
    parser.add_argument(
        "--category", type=str, action="append", dest="categories",
        choices=["completeness", "links", "timeline", "noise", "structural"],
        help="Limit to specific category (repeatable)",
    )
    parser.add_argument(
        "--type", type=str, action="append", dest="types",
        help="Limit to entity type (person, company, meeting, etc.)",
    )
    parser.add_argument(
        "--severity", type=str, default=None,
        choices=["error", "warning", "info"],
        help="Minimum severity to show",
    )
    parser.add_argument("--fix", action="store_true", help="Apply safe auto-fixes")
    parser.add_argument(
        "--quarantine", action="store_true",
        help="Move garbage candidates to _quarantine/ folder for review",
    )
    parser.add_argument("--report", action="store_true", help="JSON output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Summary only")

    args = parser.parse_args()

    vault_path = Path(args.vault)
    if not vault_path.exists():
        print(f"Error: vault not found: {vault_path}", file=sys.stderr)
        sys.exit(1)

    sev_map = {"error": Severity.ERROR, "warning": Severity.WARNING, "info": Severity.INFO}
    min_sev = sev_map.get(args.severity) if args.severity else None

    issues = run_lint(
        vault_path,
        categories=args.categories,
        entity_types=args.types,
        min_severity=min_sev,
        do_fix=args.fix,
        do_quarantine=args.quarantine,
        quiet=args.quiet,
        json_report=args.report,
    )

    # Exit code: 1 if errors found
    if any(i.severity == Severity.ERROR for i in issues):
        sys.exit(1)


if __name__ == "__main__":
    main()
