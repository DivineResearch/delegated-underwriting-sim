"""Theoretical lower bounds for the aggregate-credit lifetime model."""

from __future__ import annotations

import math


def _validate_non_negative(name: str, value: float) -> None:
	if value < 0:
		raise ValueError(f"{name} must be non-negative")


def _validate_positive(name: str, value: float) -> None:
	if value <= 0:
		raise ValueError(f"{name} must be positive")


def risk_premium(principal: float, default_prob: float, risk_margin: float = 0.0) -> float:
	"""Return the earned-credit premium that prices default risk.

	At break-even, `(1 - p) * I_R = p * x`. A non-negative `risk_margin`
	multiplies this premium by `1 + risk_margin`.
	"""

	_validate_positive("principal", principal)

	if default_prob < 0 or default_prob >= 1:
		raise ValueError("default_prob must satisfy 0 <= default_prob < 1")

	if risk_margin < -1:
		raise ValueError("risk_margin must be greater than or equal to -1")

	return (1.0 + risk_margin) * default_prob * principal / (1.0 - default_prob)


def deterministic_survival_bound(
	initial_credit: float,
	threshold: float,
	max_loss: float,
	default_fraction: float = 1.0,
	min_repayment_credit: float = 0.0,
) -> int | float:
	"""Return the deterministic number of rounds guaranteed to preserve viability.

	The bound is the theorem's prefix condition under coarse assumptions:

	`C_m >= C_0 - rho * L * m + (1 - rho) * r * m`.

	The return value counts completed rounds after which credit is still at least
	`threshold`. If the aggregate drift is non-negative, the aggregate-credit
	bound is infinite.
	"""

	_validate_non_negative("initial_credit", initial_credit)
	_validate_non_negative("threshold", threshold)
	_validate_positive("max_loss", max_loss)
	_validate_non_negative("min_repayment_credit", min_repayment_credit)

	if default_fraction < 0 or default_fraction > 1:
		raise ValueError("default_fraction must satisfy 0 <= default_fraction <= 1")

	if initial_credit <= threshold:
		return 0

	alpha = default_fraction * max_loss - (1.0 - default_fraction) * min_repayment_credit

	if alpha <= 0:
		return math.inf

	return math.floor((initial_credit - threshold) / alpha)


def adversarial_survival_bound(
	n: int,
	seed_budget: float = 1.0,
	principal: float = 1.0,
	threshold: float | None = None,
) -> int:
	"""Return the worst-case all-default survival bound.

	This is `floor((C_0 - q) / L)`, where `C_0 = n * seed_budget`, `q` is
	the minimum viable credit threshold, and `L` is the per-round loss cap.
	"""

	if n <= 0:
		raise ValueError("n must be positive")

	_validate_positive("seed_budget", seed_budget)
	_validate_positive("principal", principal)

	q = principal if threshold is None else threshold

	return int(
		deterministic_survival_bound(
			initial_credit=n * seed_budget,
			threshold=q,
			max_loss=principal,
			default_fraction=1.0,
		)
	)


def theoretical_bound(
	n: int,
	seed_budget: float = 1.0,
	principal: float = 1.0,
	default_prob: float = 0.05,
	threshold: float | None = None,
	epsilon: float = 0.01,
	risk_margin: float = 0.0,
) -> int:
	"""Return the conservative high-probability stochastic lifetime lower bound.

	Under break-even-or-better pricing, total system credit is a submartingale.
	With one-round credit changes bounded by `M`, the maximal Azuma-Hoeffding
	bound gives:

	`T <= (C_0 - q)^2 / (2 M^2 log(1 / epsilon))`.
	"""

	if n <= 0:
		raise ValueError("n must be positive")

	_validate_positive("seed_budget", seed_budget)
	_validate_positive("principal", principal)

	if risk_margin < 0:
		raise ValueError("the stochastic lower bound assumes break-even-or-better pricing")

	if epsilon <= 0 or epsilon >= 1:
		raise ValueError("epsilon must satisfy 0 < epsilon < 1")

	q = principal if threshold is None else threshold
	_validate_non_negative("threshold", q)

	c0 = n * seed_budget

	if c0 <= q:
		return 0

	premium = risk_premium(principal=principal, default_prob=default_prob, risk_margin=risk_margin)
	max_step = max(principal, premium)

	return math.floor((c0 - q) ** 2 / (2.0 * max_step**2 * math.log(1.0 / epsilon)))

