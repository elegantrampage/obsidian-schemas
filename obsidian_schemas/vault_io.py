"""The vault's ONE write door — atomicity, locking and stale-read protection.

**This is the only file under `obsidian_schemas/` or `scripts/` permitted to
name a filesystem-mutation capability.** That is the same self-rule
`tests/derivations.py` applies to itself for `ast`, and `tests/test_write_routing.py`
enforces it here by scanning for the capability rather than for known copies.

Three layers over one seam (WI-004):

* **Layer 1 — atomicity.** Every commit writes a dot-prefixed temp file in the
  RESOLVED target's own directory, carries the target's mode onto that
  descriptor while the file is still empty, writes EVERY byte of the payload —
  a short `write(2)` refuses rather than committing a fragment, so "atomic"
  means a COMPLETE note and not merely an indivisible rename — `fsync`s, and
  only then takes a terminal form: `os.replace` when a derivation read exists,
  `os.link`+`unlink` (a kernel no-clobber guarantee, not a check) when none
  does. The parent directory is fsynced so the entry is durable.
* **Layer 2 — locking.** A per-path `threading.RLock` for in-process exclusion
  and reentrancy, under a per-path `filelock.FileLock` for cross-process
  exclusion. Cooperating writers never collide.
* **Layer 3 — the precondition.** Every write is preconditioned AT THE WRITE
  SYSCALL, against the target itself, on the read its bytes were derived from —
  and a write whose bytes derive from NO read of the target is preconditioned on
  the target's non-existence, enforced atomically. Absence of a stamp is the
  STRICTEST case, never the loosest.

**The residual, stated rather than hidden.** POSIX offers no compare-and-swap on
file content, so a microsecond-scale window remains between the final re-stat and
the `os.replace` in which an Obsidian write can still be lost. It is irreducible
from our side of the boundary. It is acceptable because the window shrinks from
"the entire read-modify-write span, seconds" to microseconds, and because
Obsidian only writes while Dave is actively editing THAT note. It is not zero:
Obsidian saves IN PLACE (truncate-and-write, same inode — observed 2026-08-09),
so a reader overlapping its truncate window can observe a truncated note. The
frequency is bounded; the shape is not.
"""

import hashlib
import logging
import os
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import filelock

from obsidian_schemas.errors import (
    ExternalWriteConflict,
    NoteAlreadyExists,
    StaleEntityWrite,
    WriteFailedError,
)

logger = logging.getLogger(__name__)

SENTINEL_DIR_NAME = ".obsidian-schemas-locks"
DEFAULT_LOCK_TIMEOUT = 10.0

_WRITE_INCOMPLETE = "write did not complete"


# --------------------------------------------------------------------------
# NoteStamp — the precondition token
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class NoteStamp:
    """What a note looked like when its bytes were read.

    Minted ONLY by `stat_stamp` (and therefore by `read_note` and
    `record_snapshot`). A caller cannot construct a passing stamp out of
    nothing, which is what makes "a caller structurally cannot write from a
    stale snapshot" a property of the type rather than of caller discipline.
    """

    mtime_ns: int
    size: int
    exists: bool


# --------------------------------------------------------------------------
# D6. Configuration — ONE reader, so a setting cannot skip validation by being
# forgotten. A second `os.environ` reference in this file is forbidden.
# --------------------------------------------------------------------------

def _bad_setting(name, cause=None) -> WriteFailedError:
    """The ONE refusal shape for a bad setting: the variable's NAME and nothing
    else from the environment.

    The name rides in `declared_type` because that is the only slot
    `bounded_message` renders verbatim, and a variable name is a source literal
    by construction. It deliberately does NOT ride in `path`: `path` renders the
    VALUE, and a lock directory can carry a person's name. `cause` cannot carry
    it either — `bounded_cause` projects an exception to its class name and
    never its `str()`. Task 3 forbids minting a fourth REASONS literal, so this
    is the bounded channel that remains.
    """
    return WriteFailedError(_WRITE_INCOMPLETE, declared_type=name, cause=cause)


def _env_setting(name, parse, validate, default):
    """The module's ONLY environment access.

    Returns `default` when the var is unset. Raises `WriteFailedError` naming
    NOTHING but the variable's own name for any value that fails `parse` or
    `validate` — never the value, which could carry a person's name into a
    message (WI-020's bounded_message contract).

    A setting added later cannot skip validation by being forgotten: it either
    routes through here and gets the rule, or it names `os.environ` a second
    time — which is a capability duplication inside the one file the routing
    wall excludes, and which the spec forbids in writing.
    """
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = parse(raw)
    except Exception as exc:
        raise _bad_setting(name, exc) from exc
    if not validate(value):
        raise _bad_setting(name)
    return value


def _lock_timeout() -> float:
    return _env_setting(
        "OBSIDIAN_SCHEMAS_LOCK_TIMEOUT",
        parse=float,
        validate=lambda v: v > 0,
        default=DEFAULT_LOCK_TIMEOUT,
    )


def _configured_lock_dir():
    """The sentinel home, or None for the default (the note's own directory).

    A relative, empty or unusable value RAISES rather than being resolved
    against the process CWD — which would key two writers' sentinels in
    different directories and evaporate Layer 2's mutual exclusion with no
    sound (M2).
    """
    value = _env_setting(
        "OBSIDIAN_SCHEMAS_LOCK_DIR",
        parse=str,
        validate=lambda v: bool(v) and Path(v).is_absolute(),
        default=None,
    )
    if value is None:
        return None
    home = Path(value)
    try:
        ensure_dir(home)
    except (OSError, WriteFailedError) as exc:
        # `ensure_dir` refuses as a WriteFailedError carrying the directory in
        # `path`, and `path` renders the VALUE — which is the one thing M2 will
        # not let out of this function. Re-raised through `_bad_setting`, the
        # message carries the variable's NAME and the projection of the cause to
        # its class name, and nothing else.
        raise _bad_setting("OBSIDIAN_SCHEMAS_LOCK_DIR", exc) from exc
    if not home.is_dir():
        raise _bad_setting("OBSIDIAN_SCHEMAS_LOCK_DIR",
                           NotADirectoryError())
    return home


def guard_mode() -> str:
    """`"enforce"` (default) or `"observe"`. Any other value raises.

    Read per call rather than cached at import, so a consumer can flip modes
    without a restart and a mid-run flip to an invalid value refuses at the NEXT
    door — the fail-closed direction.
    """
    return _env_setting(
        "OBSIDIAN_SCHEMAS_WRITE_GUARD",
        parse=str,
        validate=lambda v: v in ("enforce", "observe"),
        default="enforce",
    )


_ANNOUNCED = {"observe": False}
_ANNOUNCE_LOCK = threading.RLock()


def _refuse(exc, path):
    """Enforce the refusal, or downgrade it to a WARNING under `observe`.

    Returns True when the caller should PROCEED with today's semantics.
    """
    if guard_mode() == "enforce":
        raise exc
    logger.warning(
        "write guard is in observe mode: %s would have been raised for path=%s",
        type(exc).__name__, path,
    )
    return True


def _announce_mode_once():
    """ONE INFO line per process whose mode is `observe`, at its first write.

    Without it, `observe` is a security-relevant configuration with no signal at
    all while nothing is colliding — a consumer can leave it set indefinitely
    and believe the item shipped. One line per process, not per write, so it
    cannot become the noise that gets filtered.
    """
    if guard_mode() != "observe":
        return
    with _ANNOUNCE_LOCK:
        if _ANNOUNCED["observe"]:
            return
        _ANNOUNCED["observe"] = True
    logger.info(
        "obsidian_schemas write guard is in OBSERVE mode "
        "(OBSIDIAN_SCHEMAS_WRITE_GUARD=observe): write conflicts will be "
        "logged and the write will proceed with pre-WI-004 semantics"
    )


# --------------------------------------------------------------------------
# D5. The snapshot registry — keyed by the RESOLVED path, recorded ONLY where
# an entity is derived from a file's bytes, and by a successful door-2 write.
# A door-1 write does not touch it (LESSONS #43: two independently-correct
# guards must not read one field for different purposes).
# --------------------------------------------------------------------------

_SNAPSHOT_STAMPS: dict = {}
_REGISTRY_LOCK = threading.RLock()


def _resolved(path) -> Path:
    """The ONE resolution every door performs, exactly once, at entry (M3).

    Non-strict, so a not-yet-existing leaf resolves against its resolved parent
    and a create still keys on one value.
    """
    if path is None or (isinstance(path, str) and not path):
        raise WriteFailedError(_WRITE_INCOMPLETE,
                               cause=ValueError("path is empty"))
    return Path(path).resolve()


def stat_stamp(path) -> NoteStamp:
    """Pure observation. Does NOT touch the registry.

    Separate from `record_snapshot` because a read-side observation point must
    stat BEFORE it reads and record AFTER it knows an entity was derived, which
    one stat-now call cannot express. Stat-first makes the stamp OLDER than the
    payload under a race, and an older stamp fails the precondition — the
    failure direction is refusal. Stat-after would make it newer, and the
    failure direction would be a silent lost update.
    """
    target = _resolved(path)
    try:
        st = os.stat(target)
    except FileNotFoundError:
        return NoteStamp(mtime_ns=0, size=0, exists=False)
    except OSError as exc:
        raise WriteFailedError(_WRITE_INCOMPLETE, path=target, cause=exc) from exc
    return NoteStamp(mtime_ns=st.st_mtime_ns, size=st.st_size, exists=True)


def remember_snapshot(path, stamp: NoteStamp) -> None:
    """Commit an already-taken stamp to the registry."""
    key = str(_resolved(path))
    with _REGISTRY_LOCK:
        _SNAPSHOT_STAMPS[key] = stamp


def record_snapshot(path) -> NoteStamp:
    """`stat_stamp` + `remember_snapshot`, for the POST-WRITE case.

    Correct only where the bytes on disk are the ones this process just
    committed — D8 step 8. Every read-side point uses the two halves.
    """
    stamp = stat_stamp(path)
    remember_snapshot(path, stamp)
    return stamp


def snapshot_stamp(path) -> Optional[NoteStamp]:
    """The registered stamp for a path, or None.

    `None` is NOT a failure and is deliberately outside COMMIT_FUNCTION_NAMES:
    it IS the zero case the whole precondition rule is built on — an unstamped
    path must not exist.
    """
    key = str(_resolved(path))
    with _REGISTRY_LOCK:
        return _SNAPSHOT_STAMPS.get(key)


def forget_snapshot(path) -> None:
    key = str(_resolved(path))
    with _REGISTRY_LOCK:
        _SNAPSHOT_STAMPS.pop(key, None)


def clear_snapshots() -> None:
    """Test hygiene only."""
    with _REGISTRY_LOCK:
        _SNAPSHOT_STAMPS.clear()


# --------------------------------------------------------------------------
# D3. Layer 2 — locking
# --------------------------------------------------------------------------

_THREAD_LOCKS: dict = {}
_FILE_LOCKS: dict = {}
_LOCK_TABLE_LOCK = threading.RLock()
_HELD = threading.local()


def _held_depths() -> dict:
    depths = getattr(_HELD, "depths", None)
    if depths is None:
        depths = {}
        _HELD.depths = depths
    return depths


def _held_locks() -> dict:
    """The FileLock instance each held key was acquired through."""
    locks = getattr(_HELD, "locks", None)
    if locks is None:
        locks = {}
        _HELD.locks = locks
    return locks


def _sentinel_path(target: Path) -> Path:
    """`<home>/<sha256(str(target))[:32]>.lock`.

    BOTH halves derive from the one resolved target (M3): the hash from
    `str(target)`, and the HOME from `target.parent` — never from the caller's
    unresolved parent. Two paths naming one real note therefore compute ONE
    sentinel in ONE directory and Layer 2 excludes them; deriving the hash from
    the resolved path while leaving its directory unresolved is what let a
    symlink in directory A and the real file in directory B both acquire.

    Hashed rather than name-derived because the volume is case-insensitive APFS
    and note names carry spaces and punctuation.
    """
    digest = hashlib.sha256(str(target).encode("utf-8")).hexdigest()[:32]
    configured = _configured_lock_dir()
    home = configured if configured is not None else target.parent / SENTINEL_DIR_NAME
    return home / f"{digest}.lock"


def is_locked(path) -> bool:
    """Whether THIS process holds the note lock for `path`.

    Membership in the held-depth map, never a `flock` probe — which is what
    makes step-skipping loud instead of racy.
    """
    return _held_depths().get(str(_resolved(path)), 0) > 0


@contextmanager
def note_lock(path):
    """Layer 2. Reentrant within one thread, exclusive across threads AND
    processes.

    The `threading.RLock` comes first and gives in-process exclusion plus
    reentrancy — the role a hand-rolled depth registry would play, obtained from
    the standard library. `thread_local=False` on the `FileLock` is load-bearing:
    filelock's default thread-local acquisition counter would let two threads
    sharing one instance each believe they hold a lock the OS grants per
    descriptor and therefore per process. Step 1 already guarantees only one
    thread is inside, so the process-wide counter is the correct one.
    """
    target = _resolved(path)
    key = str(target)
    timeout = _lock_timeout()

    with _LOCK_TABLE_LOCK:
        thread_lock = _THREAD_LOCKS.get(key)
        if thread_lock is None:
            thread_lock = threading.RLock()
            _THREAD_LOCKS[key] = thread_lock

    if not thread_lock.acquire(timeout=timeout):
        raise WriteFailedError(_WRITE_INCOMPLETE, path=target,
                               cause=TimeoutError("note lock"))
    depths = _held_depths()
    holders = _held_locks()
    try:
        reentrant = depths.get(key, 0) > 0
        if not reentrant:
            # The sentinel is re-derived on every OUTERMOST acquisition, and the
            # FileLock cache is keyed on the SENTINEL rather than on the note —
            # so a changed OBSIDIAN_SCHEMAS_LOCK_DIR takes effect instead of
            # being masked by an instance cached under the old home.
            sentinel = _sentinel_path(target)
            try:
                ensure_dir(sentinel.parent)
            except (OSError, WriteFailedError) as exc:
                # Re-homed onto the NOTE rather than propagated as-is: under a
                # configured lock dir, `ensure_dir`'s own refusal carries that
                # configured value in `path`, and M2 keeps it out of messages.
                raise WriteFailedError(_WRITE_INCOMPLETE, path=target,
                                       cause=exc) from exc
            with _LOCK_TABLE_LOCK:
                file_lock = _FILE_LOCKS.get(str(sentinel))
                if file_lock is None:
                    file_lock = filelock.FileLock(str(sentinel),
                                                  thread_local=False)
                    _FILE_LOCKS[str(sentinel)] = file_lock
            try:
                file_lock.acquire(timeout=timeout)
            except filelock.Timeout as exc:
                raise WriteFailedError(_WRITE_INCOMPLETE, path=target,
                                       cause=exc) from exc
            except OSError as exc:
                raise WriteFailedError(_WRITE_INCOMPLETE, path=target,
                                       cause=exc) from exc
            holders[key] = file_lock
        depths[key] = depths.get(key, 0) + 1
        try:
            yield target
        finally:
            depths[key] -= 1
            if depths[key] <= 0:
                del depths[key]
                # Released through the instance THIS acquisition took, never a
                # re-derived one: the configured home could have moved under us.
                file_lock = holders.pop(key, None)
                if file_lock is not None:
                    file_lock.release()
    finally:
        thread_lock.release()


def _require_lock(target: Path) -> None:
    if _held_depths().get(str(target), 0) <= 0:
        raise WriteFailedError(_WRITE_INCOMPLETE, path=target,
                               cause=RuntimeError("note lock is not held"))


# --------------------------------------------------------------------------
# D2. Layer 1 — atomicity, and M1's ordering
# --------------------------------------------------------------------------

_TMP_COUNTER = [0]


def _next_temp(target: Path) -> Path:
    with _LOCK_TABLE_LOCK:
        _TMP_COUNTER[0] += 1
        counter = _TMP_COUNTER[0]
    return target.parent / f".{target.name}.{os.getpid()}.{counter}.tmp"


def _existing_mode(target: Path) -> Optional[int]:
    """The target's permission bits, and the hard-link refusal (D2.1).

    A replace gives the OTHER hard links the OLD bytes while today's
    truncate-in-place updates all of them — a silent divergence with no correct
    answer this package can pick, so every door refuses it.
    """
    try:
        st = os.stat(target)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise WriteFailedError(_WRITE_INCOMPLETE, path=target, cause=exc) from exc
    if st.st_nlink > 1:
        raise WriteFailedError(
            _WRITE_INCOMPLETE, path=target,
            cause=OSError("target has more than one hard link"),
        )
    return st.st_mode & 0o7777


def _commit(target: Path, text: str, *, no_clobber: bool) -> Path:
    """Write `text` and put it at `target` atomically.

    M1's ORDERING is the whole of this function's shape: the mode is applied to
    the temp file's OWN DESCRIPTOR, as the first operation on it, BEFORE a
    single note byte is written — so the note's content never exists on disk at
    a wider mode than the target's, not even for the span of the write and the
    fsync. There is NO chmod after the write: a chmod-before-replace passes
    every committed-mode assertion while leaving the whole note readable at the
    umask-derived create mode for the length of the write, which is precisely
    the disclosure M1 exists to prevent.

    `os.fchmod` rather than passing `mode` to `os.open`, because `os.open`'s
    mode argument is umask-masked and can only NARROW: a target at 0o666 under
    umask 0o022 would commit at 0o644, and the door would believe it preserved
    a mode nobody chose.
    """
    mode = _existing_mode(target)
    tmp = _next_temp(target)
    payload = text.encode("utf-8")

    try:
        # The narrowest possible starting point when there is a mode to carry;
        # the umask-derived mode Path.write_text gives a fresh file when there
        # is not. Never tempfile.mkstemp (0600 committed) and never a bare
        # open(tmp, "w") (umask-wide).
        create_mode = 0o600 if mode is not None else 0o666
        fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, create_mode)
    except OSError as exc:
        raise WriteFailedError(_WRITE_INCOMPLETE, path=target, cause=exc) from exc

    try:
        if mode is not None:
            os.fchmod(fd, mode)          # FIRST operation on the descriptor
        _write_all(fd, payload)
        os.fsync(fd)
    except OSError as exc:
        os.close(fd)
        _discard(tmp)
        raise WriteFailedError(_WRITE_INCOMPLETE, path=target, cause=exc) from exc
    else:
        os.close(fd)

    try:
        if no_clobber:
            # A kernel guarantee, not a check: os.link fails with EEXIST if the
            # destination exists, which is what makes the create free of the
            # check-then-mutate gap.
            try:
                os.link(tmp, target)
            except FileExistsError as exc:
                _discard(tmp)
                raise NoteAlreadyExists(
                    "a note already exists at the destination",
                    path=target, cause=exc,
                ) from exc
            _discard(tmp)
        else:
            os.replace(tmp, target)
    except NoteAlreadyExists:
        raise
    except OSError as exc:
        _discard(tmp)
        raise WriteFailedError(_WRITE_INCOMPLETE, path=target, cause=exc) from exc

    _fsync_dir(target.parent)
    return target


def _write_all(fd: int, payload: bytes) -> None:
    """Put EVERY byte of `payload` on `fd`, or refuse.

    `os.write` is the raw `write(2)` syscall and MAY RETURN SHORT. The realistic
    trigger is a volume filling mid-write: POSIX writes what fits and returns
    that count rather than failing with `ENOSPC`. A discarded return value would
    make `_commit` `fsync` the fragment, `os.replace` it over the target and
    fsync the directory entry — a truncated note committed atomically, durably
    and SILENTLY, with `write_markdown_file` then stamping a fresh snapshot over
    the corrupted bytes. That is the loss class Layer 1 exists to close,
    arriving through Layer 1's own commit.

    It is also the direction that matters: `Path.write_text`, what every routed
    site called before WI-004, loops on short writes inside `io.BufferedWriter`
    and surfaces the failure at flush. The old code was LOUD here, so an
    unchecked return would be a regression, not merely a gap. This restores that
    loudness at the raw descriptor, and the loop is what makes "atomic" mean a
    COMPLETE note rather than only an indivisible rename (AC-1).

    Raises `OSError` rather than `WriteFailedError` deliberately: `_commit`'s
    existing handler is the ONE place that closes the descriptor, discards the
    temp file and re-raises as `WriteFailedError`. Refusing here therefore
    cannot reach `os.replace`, so the target keeps its old bytes and no temp
    file survives.
    """
    written = 0
    total = len(payload)
    while written < total:
        count = os.write(fd, memoryview(payload)[written:])
        if count <= 0:
            raise OSError(
                f"write made no progress: {written} of {total} bytes written"
            )
        written += count


def _discard(tmp: Path) -> None:
    try:
        os.unlink(tmp)
    except OSError:
        logger.debug("could not remove the temp file at %s", tmp, exc_info=True)


def _fsync_dir(directory: Path) -> None:
    """Make the directory ENTRY durable, not just the bytes behind it.

    Best-effort, and it runs AFTER the commit succeeded, so it can never turn a
    failure into a success. But a directory entry that never became durable is
    exactly the class Layer 1 exists to bound, so it leaves a trace at DEBUG
    rather than none at all.
    """
    try:
        fd = os.open(directory, os.O_RDONLY)
    except OSError:
        logger.debug("could not open %s to fsync its entry", directory,
                     exc_info=True)
        return
    try:
        os.fsync(fd)
    except OSError:
        logger.debug("could not fsync the directory entry at %s", directory,
                     exc_info=True)
    finally:
        os.close(fd)


# --------------------------------------------------------------------------
# The public doors
# --------------------------------------------------------------------------

def ensure_dir(path) -> Path:
    """`mkdir(parents=True, exist_ok=True)` — the namespace cell.

    Carries NO precondition and NO lock, and that is a ruling rather than a gap
    (R5): it is idempotent and has no loss mode. It lives here for one reason —
    this module is the only place permitted to NAME a filesystem-mutation
    capability, and `mkdir` is one.

    It DOES carry the door contract, though: a permission or space failure
    refuses as a `WriteFailedError` rather than escaping as a raw `OSError`. A
    consumer's `except LoudFailError` — this package's documented "it refused"
    idiom — must catch every failure on every door, and this cell is reached
    from `write_markdown_file` and `quarantine_garbage` like any other.
    """
    directory = Path(path)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise WriteFailedError(_WRITE_INCOMPLETE, path=directory,
                               cause=exc) from exc
    return directory


def read_note(path) -> Tuple[str, NoteStamp]:
    """Read a note and mint the stamp its bytes derive from. Requires the lock.

    "Requires" here is a CALLER CONTRACT, not an enforced one: every write door
    below calls `_require_lock` and this one deliberately does not. A read
    outside the lock cannot lose a note — the worst it can do is mint a stamp
    that fails its own precondition later, which is the refusal direction — so
    enforcing it would buy nothing and would forbid the legitimate unlocked
    read. Every routed site nonetheless takes the lock across read-and-write,
    because a stamp read outside the lock is a refusal waiting to happen.

    **Wraps NOTHING.** A missing path raises `FileNotFoundError`; an `OSError`
    or a `UnicodeDecodeError` from the read propagates UNWRAPPED, with no
    `raise ... from`. That is not a convenience — it is what keeps a routed
    site's own `except` clause seeing the same exception class it sees today,
    and WI-020's error-chain contract is written on exactly that. Had this
    wrapped either into a LoudFailError, a routed site's `except LoudFailError:
    raise` arm would fire first and both halves of that contract would change
    silently.

    The doors below are the opposite: they are this package's own refusal
    surface, and every failure on them is a LoudFailError subclass.
    """
    target = _resolved(path)
    stamp = stat_stamp(target)
    text = target.read_text(encoding="utf-8")
    return text, stamp


def write_note(path, text, *, precondition: NoteStamp, origin: str = "content") -> Path:
    """Layers 3 + 1. Replace `path`'s bytes, preconditioned on `precondition`.

    Which exception fires is decided by WHERE THE PRECONDITION CAME FROM, not by
    inspecting the mismatch: `origin="content"` is door 1 and raises
    `ExternalWriteConflict`; `origin="entity"` is door 2u and raises
    `StaleEntityWrite`. Both are LoudFailError subclasses, so
    `except LoudFailError` catches "this package refused"; both are
    distinguishable from `WriteFailedError`, so a caller may retry a conflict
    without retrying a genuine IO failure.

    A stamp whose target no longer exists is a MISMATCH, not a create: the note
    was deleted under us, and silently resurrecting it from a stale snapshot is
    the same loss class this module exists to kill, in the other direction.
    """
    target = _resolved(path)
    _announce_mode_once()
    _require_lock(target)
    current = stat_stamp(target)
    if current != precondition:
        conflict = (
            StaleEntityWrite("entity write derives from a stale snapshot",
                             path=target)
            if origin == "entity"
            else ExternalWriteConflict("target changed since it was read",
                                       path=target)
        )
        _refuse(conflict, target)
    return _commit(target, text, no_clobber=False)


def create_note(path, text) -> Path:
    """The ZERO CASE: an atomic no-clobber create.

    No precondition argument exists, because an empty derivation read admits
    exactly one prior state of the target — absent. The terminal form is the
    no-clobber link, and the kernel's `FileExistsError` becomes
    `NoteAlreadyExists`.
    """
    target = _resolved(path)
    _announce_mode_once()
    _require_lock(target)
    if guard_mode() == "observe" and target.exists():
        logger.warning(
            "write guard is in observe mode: %s would have been raised for path=%s",
            "NoteAlreadyExists", target,
        )
        return _commit(target, text, no_clobber=False)
    return _commit(target, text, no_clobber=True)


def move_note(src, dest) -> Path:
    """Door 3 — a whole-file move that refuses an existing destination BY
    SYSCALL rather than by check.

    A symlinked SOURCE is refused rather than resolved: a whole-file move
    through a link has two defensible meanings — relocate the link, or relocate
    its target — and door 3's only caller quarantines garbage notes, so refusing
    is loud, costs nothing, and leaves the choice to whoever first needs it.
    This is the unenumerated case failing LOUD rather than being absorbed by the
    nearest-looking rule.

    Link-then-unlink, deliberately over unlink-then-link: a failure between the
    two leaves BOTH paths present, and a duplicate is recoverable by hand while
    a lost note is not.
    """
    if Path(src).is_symlink():
        raise WriteFailedError(
            _WRITE_INCOMPLETE, path=Path(src),
            cause=ValueError("refusing to move a symlinked source"),
        )
    source = _resolved(src)
    target = _resolved(dest)
    _announce_mode_once()
    # Door 3 is the only door taking TWO locks, so it takes them in a global
    # total order — sorted resolved posix strings — which is sufficient to make
    # deadlock impossible. The locks are reentrant, so a caller already holding
    # either is unaffected.
    first, second = sorted([str(source), str(target)])
    with note_lock(first), note_lock(second):
        return _move_locked(source, target)


def _move_locked(source: Path, target: Path) -> Path:
    _require_lock(source)
    _require_lock(target)

    try:
        os.link(source, target)
    except FileExistsError as exc:
        if guard_mode() == "observe":
            logger.warning(
                "write guard is in observe mode: %s would have been raised "
                "for path=%s", "NoteAlreadyExists", target,
            )
            os.replace(source, target)
            forget_snapshot(source)
            forget_snapshot(target)
            _fsync_dir(target.parent)
            return target
        raise NoteAlreadyExists("a note already exists at the destination",
                                path=target, cause=exc) from exc
    except OSError as exc:
        raise WriteFailedError(_WRITE_INCOMPLETE, path=target, cause=exc) from exc

    try:
        os.unlink(source)
    except OSError as exc:
        raise WriteFailedError(_WRITE_INCOMPLETE, path=source, cause=exc) from exc

    forget_snapshot(source)
    forget_snapshot(target)
    _fsync_dir(target.parent)
    return target
