# Future Enhancements

Deferred features and improvements for obsidian-schemas.

## Repository Layer

### File Watching / Real-time Updates
- Integrate with `watchdog` for file system events
- Auto-refresh cache when vault files change
- Useful for long-running processes (HAL9000 server)

### TTL-based Cache
- Optional time-based cache invalidation
- Middle ground between manual refresh and file watching
- `PersonRepository(vault_path, cache_ttl=300)` # 5 minute TTL

### Lazy Loading
- Don't load all entities on first access
- Load individual files on demand
- Trade-off: faster startup vs slower first queries

### Concurrent Access
- Thread-safe cache operations
- Read-write locks for multi-threaded servers
- Currently assumes single-threaded use

## Entity Relationships

### Cross-Repository Linking
- `person.get_company() -> Company` instead of just string
- Requires passing company repo to person repo
- Consider a unified `VaultRepository` that manages all types

### Relationship Tracking
- Track "introduced by" relationships
- Track "works at" with dates (employment history)
- Graph-like queries: "Who do I know at Company X?"

## Additional Repositories

### ~~MeetingRepository~~ ✅ DONE (2026-01-11)
- ~~Load meeting notes~~
- ~~Query by date range, attendees, topics~~
- ~~Link to PersonRepository for attendee resolution~~

### ~~BookRepository~~ ✅ DONE (2026-01-11) / WatchRepository
- ~~Load reading list / watch list~~
- ~~Query by status (to-read, reading, read)~~
- ~~Useful for "what should I read next?" queries~~
- WatchRepository still TODO

## Person Schema Enhancements

### Professional Role & Seniority
- Add `profession` field: engineer, designer, product manager, etc.
- Add `seniority` field: junior, mid, senior, lead, director, VP, C-level
- Use case: match job opportunities to people in network
- Consider: list vs single value for profession (people wear multiple hats)
- Consider: free text vs enum for flexibility

## Schema Evolution

### Migration Support
- Detect files with outdated schema versions
- Provide migration scripts for schema changes
- `schema_version` field in frontmatter

### Validation Modes
- Strict: fail on unknown fields
- Lenient: preserve unknown fields (current)
- Warn: log unknown fields but continue

## Performance

### Index Persistence
- Save indexes to disk (pickle/JSON)
- Faster startup for large vaults
- Invalidate on file changes

### Incremental Loading
- Only reload changed files on refresh
- Track file modification times
- Currently reloads everything on refresh()

## Integration

### HAL9000 Singleton
- Global repository instances for HAL9000 server
- `get_person_repository()` factory function
- Environment-based configuration

### Obsidian Plugin Sync
- Detect when Obsidian has the vault open
- Coordinate writes to avoid conflicts
- Use Obsidian's API via MCP where possible

## Testing

### Vault Fixtures
- Shared test vault for integration tests
- Larger realistic dataset for performance testing
- Property-based testing for edge cases
