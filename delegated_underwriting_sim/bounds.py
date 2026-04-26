"""Deterministic lifetime bounds from aggregate-credit accounting."""

from __future__ import annotations

import math


def _require_non_negative(name: str, value: float) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def _require_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def lifetime_bound(initial_credit: float, threshold: float, max_principal: float) -> int:
    """Return the all-default lifetime lower bound.

    From the aggregate-credit identity, each default can reduce total credit by
    at most ``max_principal`` and repayments only increase total credit. The
    system is therefore guaranteed alive for every
    ``T <= floor((initial_credit - threshold) / max_principal)`` completed
    round, clamped to zero if it is not alive initially.
    """

    _require_non_negative("initial_credit", initial_credit)
    _require_non_negative("threshold", threshold)
    _require_positive("max_principal", max_principal)

    if initial_credit <= threshold:
        return 0

    return math.floor((initial_credit - threshold) / max_principal)


def uniform_seed_credit(seed_count: int, seed_budget: float) -> float:
    """Return ``C_0 = nB`` for ``n`` seeds with equal budget ``B``."""

    if seed_count <= 0:
        raise ValueError("seed_count must be positive")

    _require_positive("seed_budget", seed_budget)

    return seed_count * seed_budget


def uniform_seed_lifetime_bound(
    seed_count: int,
    seed_budget: float,
    threshold: float,
    max_principal: float,
) -> int:
    """Return ``floor((nB - q) / L)`` for uniform seed budgets."""

    return lifetime_bound(
        initial_credit=uniform_seed_credit(seed_count, seed_budget),
        threshold=threshold,
        max_principal=max_principal,
    )
