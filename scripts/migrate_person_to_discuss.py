#!/usr/bin/env python3
"""
Migration script to add 'To Discuss' section to existing Person files.

This script:
1. Scans the vault for person files (@*.md with type: person)
2. Checks if they have the "To Discuss" section
3. Adds the section if missing, in the correct position (first after frontmatter)
4. Preserves all existing content

Usage:
    # Dry run (preview changes)
    python scripts/migrate_person_to_discuss.py --vault /path/to/vault

    # Actually apply changes
    python scripts/migrate_person_to_discuss.py --vault /path/to/vault --apply

    # Use OBSIDIAN_VAULT_PATH environment variable
    python scripts/migrate_person_to_discuss.py --apply
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from obsidian_schemas import PersonRepository
# Module attribute call form throughout (WI-004 D7).
from obsidian_schemas import vault_io
from obsidian_schemas.body_sections import (
    parse_body_sections,
    ensure_sections_exist,
    get_expected_sections,
)


def migrate_person_file(file_path: Path, dry_run: bool = True) -> dict:
    """
    Migrate a single person file to include To Discuss section.

    Args:
        file_path: Path to the person markdown file
        dry_run: If True, don't actually modify the file

    Returns:
        dict with keys: 'path', 'status', 'message'
    """
    result = {
        'path': str(file_path),
        'status': 'unchanged',
        'message': '',
    }

    try:
        # Door 1 (WI-004): the read and the write share one lock, and the
        # write is preconditioned on that read.
        with vault_io.note_lock(file_path):
            content, _stamp = vault_io.read_note(file_path)

            # Check if it's a person file
            if 'type: person' not in content:
                result['status'] = 'skipped'
                result['message'] = 'Not a person file'
                return result

            # Split frontmatter and body
            if not content.startswith('---'):
                result['status'] = 'error'
                result['message'] = 'No frontmatter found'
                return result

            parts = content.split('---', 2)
            if len(parts) < 3:
                result['status'] = 'error'
                result['message'] = 'Invalid frontmatter format'
                return result

            frontmatter = parts[1]
            body = parts[2].lstrip('\n')

            # Check if To Discuss already exists
            if '## To Discuss' in body:
                result['status'] = 'unchanged'
                result['message'] = 'To Discuss section already exists'
                return result

            # Get expected sections for person
            expected_sections = get_expected_sections('person')

            # Use ensure_sections_exist to add missing sections in correct order
            new_body = ensure_sections_exist(body, expected_sections)

            # Check if anything changed
            if new_body == body:
                result['status'] = 'unchanged'
                result['message'] = 'No changes needed'
                return result

            # Build new content
            new_content = f"---{frontmatter}---\n{new_body}"

            if dry_run:
                result['status'] = 'would_update'
                result['message'] = 'Would add To Discuss section'
            else:
                vault_io.write_note(file_path, new_content, precondition=_stamp)
                result['status'] = 'updated'
                result['message'] = 'Added To Discuss section'

            return result

    except Exception as e:
        result['status'] = 'error'
        result['message'] = str(e)
        return result


def migrate_vault(vault_path: Path, dry_run: bool = True) -> list:
    """
    Migrate all person files in a vault.

    Args:
        vault_path: Path to the Obsidian vault
        dry_run: If True, don't actually modify files

    Returns:
        List of result dicts for each file processed
    """
    results = []

    # Find all @*.md files (person files use @ prefix)
    person_files = list(vault_path.glob('@*.md'))

    print(f"Found {len(person_files)} potential person files")
    print()

    for file_path in sorted(person_files):
        result = migrate_person_file(file_path, dry_run)
        results.append(result)

        # Print status
        status_emoji = {
            'updated': '✅',
            'would_update': '📝',
            'unchanged': '⏭️',
            'skipped': '⏭️',
            'error': '❌',
        }.get(result['status'], '❓')

        print(f"{status_emoji} {file_path.name}: {result['message']}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Migrate person files to include To Discuss section'
    )
    parser.add_argument(
        '--vault',
        type=str,
        default=os.environ.get('OBSIDIAN_VAULT_PATH', ''),
        help='Path to Obsidian vault (defaults to OBSIDIAN_VAULT_PATH env var)'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Actually apply changes (default is dry run)'
    )

    args = parser.parse_args()

    if not args.vault:
        print("Error: No vault path provided.")
        print("Use --vault /path/to/vault or set OBSIDIAN_VAULT_PATH environment variable")
        sys.exit(1)

    vault_path = Path(args.vault)
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)

    dry_run = not args.apply

    print("=" * 60)
    if dry_run:
        print("DRY RUN - No files will be modified")
        print("Use --apply to actually make changes")
    else:
        print("APPLYING CHANGES - Files will be modified")
    print("=" * 60)
    print(f"Vault: {vault_path}")
    print()

    results = migrate_vault(vault_path, dry_run)

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    status_counts = {}
    for r in results:
        status_counts[r['status']] = status_counts.get(r['status'], 0) + 1

    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    print(f"  Total: {len(results)}")

    if dry_run and status_counts.get('would_update', 0) > 0:
        print()
        print("Run with --apply to make these changes")


if __name__ == '__main__':
    main()
