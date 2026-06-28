"""Tests for item_exists() and resolve_item() eventual-consistency behaviour.

Four scenarios:

1. nonexistent  — item never created; must return False/None in a single fast list call
2. after_create — item just created; resolve_item(after="create") uses GET polling
3. after_delete — item just deleted; resolve_item(after="delete") uses list polling
4. speed        — after=None must be significantly faster than get_signal on a 404
"""

import time
import uuid

from petrovisor import PetroVisor, ItemType, Signal, SignalType


PFX = "IE Test"


def _sig_name() -> str:
    return f"{PFX} {uuid.uuid4().hex[:8]}"


def _make_signal(api: PetroVisor, name: str) -> None:
    api.add_signal(
        Signal(
            name=name,
            type=SignalType.Static.name,
            unit=" ",
            unit_measurement="Dimensionless",
        )
    )


def _poll(condition, retries: int = 30, delay: float = 1.0) -> bool:
    for _ in range(retries):
        if condition():
            return True
        time.sleep(delay)
    return False


# ── 1. nonexistent ────────────────────────────────────────────────────────────


def test_nonexistent(api: PetroVisor):
    """item_exists() and resolve_item() both return False/None for a name that
    was never created — with a single fast list call, not the ~10 s GET 404 path."""
    name = _sig_name()

    assert not api.item_exists(ItemType.Signal, name)

    t0 = time.time()
    result = api.resolve_item(ItemType.Signal, name)
    elapsed = time.time() - t0

    assert result is None
    assert elapsed < 5.0, (
        f"resolve_item(nonexistent) took {elapsed:.1f}s — expected <5 s (single list call)"
    )


# ── 2. after create ───────────────────────────────────────────────────────────


def test_after_create(api: PetroVisor):
    """resolve_item(after='create') picks up a just-created signal using GET
    polling, which converges faster than the list endpoint after a creation."""
    name = _sig_name()
    try:
        _make_signal(api, name)

        result = api.resolve_item(
            ItemType.Signal, name, after="create", max_retries=30, retry_delay=1.0
        )
        assert result is not None, (
            f"resolve_item(after='create') still None for '{name}' within 30 retries"
        )
        assert result.get("Name", "").strip() == name.strip()

        # item_exists (list-based) should also agree once propagation settles
        assert _poll(lambda: api.item_exists(ItemType.Signal, name)), (
            f"item_exists() never True for '{name}' within 30 s of creation"
        )
    finally:
        try:
            api.delete_signal(name)
        except Exception:
            pass


# ── 3. after delete ───────────────────────────────────────────────────────────


def test_after_delete(api: PetroVisor):
    """resolve_item(after='delete') returns None once the list reflects the
    deletion, without paying the ~10 s GET 404 penalty per poll."""
    name = _sig_name()
    try:
        _make_signal(api, name)
        # Wait until creation is stable before deleting
        _poll(lambda: api.item_exists(ItemType.Signal, name))

        api.delete_signal(name)

        t0 = time.time()
        result = api.resolve_item(
            ItemType.Signal, name, after="delete", max_retries=30, retry_delay=1.0
        )
        elapsed = time.time() - t0

        assert result is None, (
            f"resolve_item(after='delete') returned {result!r} for '{name}' — expected None"
        )
        # Each poll is a cheap list call; 30 × 1 s is the ceiling, not the norm
        assert elapsed < 60.0, (
            f"resolve_item(after='delete') took {elapsed:.1f}s — expected <60 s"
        )
        print(f"\n  resolve_item(after='delete') converged in {elapsed:.2f}s")
    finally:
        try:
            api.delete_signal(name)
        except Exception:
            pass


# ── 4. resolve_item — nonexistent and after_create ───────────────────────────


def test_resolve_item(api: PetroVisor):
    """resolve_item returns None quickly for a missing item (single list call)
    and returns the full dict after creation (after='create' GET polling)."""
    name = _sig_name()

    # nonexistent: single list call, no 404 penalty
    t0 = time.time()
    result = api.resolve_item(ItemType.Signal, name)
    t_none = time.time() - t0

    assert result is None
    assert t_none < 5.0, (
        f"resolve_item(nonexistent) took {t_none:.1f}s — expected <5 s (single list call)"
    )
    print(f"\n  resolve_item(nonexistent): {t_none:.2f}s")

    # after_create: GET polling, returns full dict once item propagates
    try:
        _make_signal(api, name)

        t0 = time.time()
        result = api.resolve_item(
            ItemType.Signal, name, after="create", max_retries=30, retry_delay=1.0
        )
        t_found = time.time() - t0

        assert result is not None, (
            f"resolve_item(after='create') still None for '{name}' within 30 retries"
        )
        assert result.get("Name", "").strip() == name.strip()
        print(f"  resolve_item(after='create'): {t_found:.2f}s")
    finally:
        try:
            api.delete_signal(name)
        except Exception:
            pass
