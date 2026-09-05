"""WI-021 Task 2 — the phone authority's relocation to a stdlib-only leaf.

The relocation carries NO behaviour delta by construction (the two functions
moved byte-for-byte), so what is worth asserting is the three properties that
make the move safe rather than the arithmetic that did not change:

  1. the leaf is IMPORT-CLEAN — its module names no package sibling, which is
     the whole reason `name_gate.py` and `identifier.py` may name it at module
     scope without closing writer -> gate -> person -> base -> writer;
  2. `obsidian_schemas.repositories.person.normalize_phone` still resolves, and
     resolves to the RELOCATED function object rather than to a second copy —
     two live consumers import it by that path;
  3. `Phone.parse` / `WhatsAppJID.parse` behave identically on the `MIN_DIGITS`
     boundary, which is the one place their deleted deferred imports could have
     changed an answer.

`tests/test_repositories.py` staying green UNEDITED is the fourth proof and the
strongest one — it imports the re-exported name at seven sites and this module
deliberately does not duplicate what it already asserts.

Nothing here reads syntax (no `ast`): that capability is single-homed in
`tests/derivations.py`.
"""

import obsidian_schemas.phone_normalization as phone_leaf
import obsidian_schemas.repositories.person as person_module
from obsidian_schemas.identifier import IdentifierError, Phone, WhatsAppJID
from obsidian_schemas.phone_normalization import normalize_phone, phones_match

# The import direction the leaf exists to make possible. A name here is a name
# the leaf must NOT reach for; `re` is the whole of its permitted import set.
_PACKAGE_MODULES_THE_LEAF_MAY_NOT_NAME = (
    "obsidian_schemas.repositories",
    "obsidian_schemas.writer",
    "obsidian_schemas.parser",
    "obsidian_schemas.vault_io",
    "obsidian_schemas.models",
    "obsidian_schemas.identifier",
    "obsidian_schemas.name_gate",
    "obsidian_schemas.errors",
)


def test_phone_normalization_relocated_without_a_behaviour_delta():
    """Task 2's verify. Zero-arg and raising, per the check contract."""
    _check_the_leaf_is_import_clean()
    _check_the_compat_re_export_is_the_relocated_object()
    _check_the_min_digits_boundary_is_unchanged()
    _check_the_moved_behaviour_is_byte_for_byte()


def _check_the_leaf_is_import_clean():
    # Read off the module's own globals: an `import x` or `from x import y` at
    # module scope binds something whose __module__ / identity betrays it. The
    # positive form — enumerate what the module actually pulled in — is what
    # makes an unanticipated sibling import fail here rather than one from a
    # list somebody remembered to extend.
    imported_modules = {
        value.__name__
        for value in vars(phone_leaf).values()
        if getattr(value, "__name__", None) and type(value).__name__ == "module"
    }
    assert imported_modules == {"re"}, (
        "phone_normalization must stay stdlib-only: `re` and nothing else. A "
        "package import here re-closes the cycle the relocation exists to open. "
        f"Found: {sorted(imported_modules)}"
    )

    for forbidden in _PACKAGE_MODULES_THE_LEAF_MAY_NOT_NAME:
        assert forbidden not in phone_leaf.__dict__, (
            f"the leaf names {forbidden}, which it may not"
        )


def _check_the_compat_re_export_is_the_relocated_object():
    # Identity, not equality of behaviour: a second copy pasted back into
    # person.py would pass every behavioural assertion in this file and would be
    # exactly the divergence the relocation exists to prevent.
    assert person_module.normalize_phone is normalize_phone, (
        "obsidian_schemas.repositories.person.normalize_phone must BE the "
        "relocated function object — two live consumers import it by that path"
    )
    assert person_module.phones_match is phones_match
    assert normalize_phone.__module__ == "obsidian_schemas.phone_normalization"
    assert phones_match.__module__ == "obsidian_schemas.phone_normalization"


def _check_the_min_digits_boundary_is_unchanged():
    # The deferred imports lived inside these two parsers. If deleting them had
    # changed WHICH normalizer they reach, the floor is the place it shows.
    assert Phone.MIN_DIGITS == 7

    at_floor = "1234567"
    below_floor = "123456"

    assert Phone.parse(at_floor).digits == at_floor
    assert Phone.parse("+44 7990 558521").digits == "447990558521"
    try:
        Phone.parse(below_floor)
    except IdentifierError:
        pass
    else:
        raise AssertionError("Phone.parse must still raise below MIN_DIGITS")

    jid = WhatsAppJID.parse("447990558521@s.whatsapp.net")
    assert jid.phone_digits == "447990558521"
    assert jid.phone is not None and jid.phone.digits == "447990558521"

    lid = WhatsAppJID.parse("12345@lid")
    assert lid.phone_digits == "" and lid.phone is None

    try:
        WhatsAppJID.parse("12345@s.whatsapp.net")
    except IdentifierError:
        pass
    else:
        raise AssertionError(
            "WhatsAppJID.parse must still raise for a non-@lid JID below the floor"
        )


def _check_the_moved_behaviour_is_byte_for_byte():
    assert normalize_phone("+44 7990 558521") == "447990558521"
    assert normalize_phone("447990558521@s.whatsapp.net") == "447990558521"
    assert normalize_phone("(555) 123-4567") == "5551234567"
    assert normalize_phone("") == ""
    assert normalize_phone("n/a") == ""

    assert phones_match("+44 7990 558521", "447990558521") is True
    assert phones_match("447990558521", "07990558521") is True
    assert phones_match("15551234567", "5551234567") is True
    assert phones_match("447990558521", "447990558522") is False
    assert phones_match("", "447990558521") is False
