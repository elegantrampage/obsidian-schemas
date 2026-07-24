"""Fixture-free equivalents of the pytest fixtures the WI-020 AC checks need.

The acceptance-criteria battery invokes each `check:` function DIRECTLY —
`getattr(module, name)()` — with no pytest fixture machinery in the loop. A
check written to take `tmp_path` / `monkeypatch` / `caplog` is therefore not a
runnable criterion at all: it fails with `TypeError: missing 1 required
positional argument` before a single assertion is reached, which grades the
signature rather than the property.

So every AC-named test in this build takes NO arguments and acquires its own
temp directory, attribute patches and log capture through the context managers
here. Under pytest they behave exactly as before; invoked bare, they still run.
The non-AC tests in the same modules keep the pytest fixtures — they are graded
by the floor, which always has the fixture machinery available.

Nothing here reads syntax (no `ast`): AC-7 single-homes that capability in
`tests/derivations.py`, and a second module touching it would be the copy that
criterion exists to forbid.
"""

import logging
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

_UNSET = object()


@contextmanager
def temp_dir():
    """A `tmp_path` stand-in: a fresh directory, removed on exit."""
    path = Path(tempfile.mkdtemp(prefix="wi020-"))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


class Patcher:
    """A `monkeypatch` stand-in covering the two forms the AC checks use.

    Undo runs in reverse order on exit, including when the body raises, so a
    check that patches `Path.write_text` cannot leak that patch into whatever
    the battery runs next.
    """

    def __init__(self):
        self._undo = []

    def setattr(self, target, name, value):
        original = getattr(target, name, _UNSET)
        self._undo.append(lambda: (
            delattr(target, name) if original is _UNSET
            else setattr(target, name, original)
        ))
        setattr(target, name, value)

    def setitem(self, mapping, key, value):
        original = mapping.get(key, _UNSET)
        self._undo.append(lambda: (
            mapping.pop(key, None) if original is _UNSET
            else mapping.__setitem__(key, original)
        ))
        mapping[key] = value

    def undo(self):
        while self._undo:
            self._undo.pop()()


@contextmanager
def patcher():
    p = Patcher()
    try:
        yield p
    finally:
        p.undo()


class _RecordCollector(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


@contextmanager
def captured_logs(logger_name="obsidian_schemas", level=logging.WARNING):
    """A `caplog.at_level(...)` stand-in scoped to one logger subtree.

    Yields the live record list. The package's loggers are all NOTSET children
    of `obsidian_schemas`, so a handler on the parent sees everything they
    emit; the parent's level is raised for the duration and restored after.
    """
    logger = logging.getLogger(logger_name)
    handler = _RecordCollector()
    handler.setLevel(level)
    previous_level = logger.level
    previously_disabled = logging.root.manager.disable
    logging.disable(logging.NOTSET)
    logger.setLevel(level)
    logger.addHandler(handler)
    try:
        yield handler.records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)
        logging.disable(previously_disabled)
