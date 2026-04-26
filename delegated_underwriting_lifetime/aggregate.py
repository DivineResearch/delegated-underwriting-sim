"""Scalar aggregate-credit accounting for delegated underwriting."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Round:
    """One completed loan round.

    A default burns principal from aggregate credit. A repayment mints the
    earned-credit increment. Delegation is intentionally absent because it only
    redistributes credit under the write-up's accounting identity.
    """

    principal: float
    defaulted: bool
    earned_credit: float = 0.0

    def __post_init__(self) -> None:
        if self.principal < 0:
            raise ValueError("principal must be non-negative")

        if self.earned_credit < 0:
            raise ValueError("earned_credit must be non-negative")

    @property
    def credit_delta(self) -> float:
        """Return this round's aggregate-credit change."""

        if self.defaulted:
            return -self.principal

        return self.earned_credit


@dataclass(frozen=True)
class CreditPath:
    """Aggregate-credit path after applying completed loan rounds."""

    initial_credit: float
    threshold: float
    rounds: tuple[Round, ...]
    credits: tuple[float, ...]

    @property
    def lifetime(self) -> int:
        """Number of completed rounds in the path."""

        return len(self.rounds)

    @property
    def final_credit(self) -> float:
        return self.credits[-1]

    @property
    def alive(self) -> bool:
        return self.final_credit >= self.threshold

    @property
    def default_loss(self) -> float:
        return sum(round.principal for round in self.rounds if round.defaulted)

    @property
    def minted_credit(self) -> float:
        return sum(round.earned_credit for round in self.rounds if not round.defaulted)

    @property
    def accounting_credit(self) -> float:
        """Reconstruct final credit from ``C_0 + minted credit - defaults``."""

        return self.initial_credit + self.minted_credit - self.default_loss


def apply_rounds(initial_credit: float, rounds: Iterable[Round], threshold: float = 0.0) -> CreditPath:
    """Apply completed rounds to the scalar aggregate-credit process."""

    if initial_credit < 0:
        raise ValueError("initial_credit must be non-negative")

    if threshold < 0:
        raise ValueError("threshold must be non-negative")

    credit = float(initial_credit)
    materialized_rounds: list[Round] = []
    credits = [credit]

    for round in rounds:
        credit += round.credit_delta
        materialized_rounds.append(round)
        credits.append(credit)

    return CreditPath(
        initial_credit=float(initial_credit),
        threshold=float(threshold),
        rounds=tuple(materialized_rounds),
        credits=tuple(credits),
    )


def all_default_rounds(count: int, principal: float) -> tuple[Round, ...]:
    """Return ``count`` worst-case rounds, each defaulting for ``principal``."""

    if count < 0:
        raise ValueError("count must be non-negative")

    return tuple(Round(principal=principal, defaulted=True) for _ in range(count))


def all_default_path(initial_credit: float, threshold: float, max_principal: float, rounds: int) -> CreditPath:
    """Apply the adversarial path used by the deterministic bound."""

    return apply_rounds(
        initial_credit=initial_credit,
        threshold=threshold,
        rounds=all_default_rounds(rounds, max_principal),
    )
