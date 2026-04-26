"""Aggregate-credit simulation for protocol lifetime experiments."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from itertools import islice

import numpy as np
import pandas as pd

from delegated_underwriting_simulations.bounds import adversarial_survival_bound, risk_premium, theoretical_bound


RngLike = np.random.Generator | int | None


@dataclass(frozen=True)
class Round:
	"""One completed lending round in the aggregate-credit process."""

	defaulted: bool
	principal: float
	repayment_credit: float

	def __post_init__(self) -> None:
		if self.principal < 0:
			raise ValueError("principal must be non-negative")

		if self.repayment_credit < 0:
			raise ValueError("repayment_credit must be non-negative")


@dataclass(frozen=True)
class SimulationParams:
	"""Parameters for a fixed-size aggregate-credit lifetime simulation."""

	n: int
	seed_budget: float = 1.0
	principal: float = 1.0
	default_prob: float = 0.05
	threshold: float | None = None
	max_rounds: int = 10_000_000
	risk_margin: float = 0.0

	def __post_init__(self) -> None:
		if self.n <= 0:
			raise ValueError("n must be positive")

		if self.seed_budget <= 0:
			raise ValueError("seed_budget must be positive")

		if self.principal <= 0:
			raise ValueError("principal must be positive")

		if self.default_prob < 0 or self.default_prob >= 1:
			raise ValueError("default_prob must satisfy 0 <= default_prob < 1")

		if self.max_rounds < 0:
			raise ValueError("max_rounds must be non-negative")

		if self.risk_margin < -1:
			raise ValueError("risk_margin must be greater than or equal to -1")

		if self.threshold is not None and self.threshold < 0:
			raise ValueError("threshold must be non-negative")

	@property
	def initial_credit(self) -> float:
		return self.n * self.seed_budget

	@property
	def resolved_threshold(self) -> float:
		return self.principal if self.threshold is None else self.threshold

	@property
	def repayment_credit(self) -> float:
		return risk_premium(
			principal=self.principal,
			default_prob=self.default_prob,
			risk_margin=self.risk_margin,
		)


@dataclass(frozen=True)
class PathResult:
	"""Result of applying a finite sequence of lending rounds."""

	initial_credit: float
	threshold: float
	credits: np.ndarray
	defaulted: np.ndarray
	principals: np.ndarray
	repayment_credits: np.ndarray
	stopped_by: str

	@property
	def lifetime(self) -> int:
		"""Completed rounds in this path."""

		return int(self.defaulted.size)

	@property
	def final_credit(self) -> float:
		return float(self.credits[-1])

	@property
	def default_loss(self) -> float:
		return float(self.principals[self.defaulted].sum())

	@property
	def minted_credit(self) -> float:
		return float(self.repayment_credits[~self.defaulted].sum())

	@property
	def accounting_credit(self) -> float:
		"""Credit reconstructed from the theorem's aggregate accounting identity."""

		return self.initial_credit + self.minted_credit - self.default_loss


def _coerce_rng(rng: RngLike) -> np.random.Generator:
	if isinstance(rng, np.random.Generator):
		return rng

	return np.random.default_rng(rng)


def apply_rounds(
	initial_credit: float,
	rounds: Iterable[Round],
	threshold: float = 0.0,
	stop_at_threshold: bool = True,
) -> PathResult:
	"""Apply explicit rounds and return the aggregate-credit path."""

	if initial_credit < 0:
		raise ValueError("initial_credit must be non-negative")

	if threshold < 0:
		raise ValueError("threshold must be non-negative")

	credit = float(initial_credit)
	credits = [credit]
	defaulted: list[bool] = []
	principals: list[float] = []
	repayment_credits: list[float] = []
	stopped_by = "rounds"

	if stop_at_threshold and credit < threshold:
		return PathResult(
			initial_credit=float(initial_credit),
			threshold=float(threshold),
			credits=np.array(credits, dtype=float),
			defaulted=np.array(defaulted, dtype=bool),
			principals=np.array(principals, dtype=float),
			repayment_credits=np.array(repayment_credits, dtype=float),
			stopped_by="threshold",
		)

	for lending_round in rounds:
		if lending_round.defaulted:
			credit -= lending_round.principal
		else:
			credit += lending_round.repayment_credit

		credits.append(credit)
		defaulted.append(lending_round.defaulted)
		principals.append(lending_round.principal)
		repayment_credits.append(lending_round.repayment_credit)

		if stop_at_threshold and credit < threshold:
			stopped_by = "threshold"
			break

	return PathResult(
		initial_credit=float(initial_credit),
		threshold=float(threshold),
		credits=np.array(credits, dtype=float),
		defaulted=np.array(defaulted, dtype=bool),
		principals=np.array(principals, dtype=float),
		repayment_credits=np.array(repayment_credits, dtype=float),
		stopped_by=stopped_by,
	)


def simulate_path(
	n: int,
	seed_budget: float = 1.0,
	principal: float = 1.0,
	default_prob: float = 0.05,
	threshold: float | None = None,
	max_rounds: int = 10_000_000,
	risk_margin: float = 0.0,
	rng: RngLike = None,
	default_indicators: Iterable[bool] | None = None,
	stop_at_threshold: bool = True,
) -> PathResult:
	"""Simulate one aggregate-credit path.

	When `default_indicators` is provided, `True` means default and `False`
	means repayment. Otherwise the function draws defaults from `default_prob`.
	"""

	params = SimulationParams(
		n=n,
		seed_budget=seed_budget,
		principal=principal,
		default_prob=default_prob,
		threshold=threshold,
		max_rounds=max_rounds,
		risk_margin=risk_margin,
	)

	premium = params.repayment_credit

	if default_indicators is None:
		generator = _coerce_rng(rng)

		def generated_rounds() -> Iterable[Round]:
			for _ in range(params.max_rounds):
				yield Round(
					defaulted=bool(generator.random() < params.default_prob),
					principal=params.principal,
					repayment_credit=premium,
				)

		rounds = generated_rounds()
	else:
		rounds = (
			Round(defaulted=bool(defaulted), principal=params.principal, repayment_credit=premium)
			for defaulted in islice(default_indicators, params.max_rounds)
		)

	return apply_rounds(
		initial_credit=params.initial_credit,
		rounds=rounds,
		threshold=params.resolved_threshold,
		stop_at_threshold=stop_at_threshold,
	)


def _simulate_lifetimes_vectorized(
	params: SimulationParams,
	trials: int,
	rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
	if trials <= 0:
		raise ValueError("trials must be positive")

	threshold = params.resolved_threshold
	credits = np.full(trials, params.initial_credit, dtype=float)
	lifetimes = np.zeros(trials, dtype=np.int64)
	alive = credits >= threshold
	premium = params.repayment_credit

	if not alive.any():
		return lifetimes, np.zeros(trials, dtype=bool)

	for round_number in range(1, params.max_rounds + 1):
		alive_indices = np.flatnonzero(alive)
		defaults = rng.random(alive_indices.size) < params.default_prob
		credits[alive_indices] += np.where(defaults, -params.principal, premium)

		newly_dead_mask = credits[alive_indices] < threshold

		if newly_dead_mask.any():
			newly_dead = alive_indices[newly_dead_mask]
			lifetimes[newly_dead] = round_number
			alive[newly_dead] = False

		if not alive.any():
			break

	lifetimes[alive] = params.max_rounds

	return lifetimes, alive


def simulate_many(
	n_values: Sequence[int],
	trials: int = 10_000,
	seed_budget: float = 1.0,
	principal: float = 1.0,
	default_prob: float = 0.05,
	threshold: float | None = None,
	max_rounds: int = 10_000_000,
	risk_margin: float = 0.0,
	epsilon: float = 0.01,
	seed: int | None = 0,
) -> pd.DataFrame:
	"""Run Monte Carlo lifetime trials for multiple seed counts."""

	if not n_values:
		raise ValueError("n_values must not be empty")

	rng = np.random.default_rng(seed)
	rows = []

	for n in n_values:
		params = SimulationParams(
			n=n,
			seed_budget=seed_budget,
			principal=principal,
			default_prob=default_prob,
			threshold=threshold,
			max_rounds=max_rounds,
			risk_margin=risk_margin,
		)
		lifetimes, censored = _simulate_lifetimes_vectorized(params=params, trials=trials, rng=rng)
		p01 = float(np.quantile(lifetimes, 0.01))
		p10 = float(np.quantile(lifetimes, 0.10))
		median = float(np.median(lifetimes))
		bound = theoretical_bound(
			n=n,
			seed_budget=seed_budget,
			principal=principal,
			default_prob=default_prob,
			threshold=threshold,
			epsilon=epsilon,
			risk_margin=risk_margin,
		)
		adversarial_bound = adversarial_survival_bound(
			n=n,
			seed_budget=seed_budget,
			principal=principal,
			threshold=threshold,
		)

		rows.append(
			{
				"n": n,
				"trials": trials,
				"censored_trials": int(censored.sum()),
				"mean_lifetime": float(lifetimes.mean()),
				"median_lifetime": median,
				"p10_lifetime": p10,
				"p01_lifetime": p01,
				"theoretical_bound": bound,
				"adversarial_survival_bound": adversarial_bound,
				"p01_over_n": p01 / n,
				"p01_over_n2": p01 / (n**2),
				"median_over_n2": median / (n**2),
				"adversarial_over_n": adversarial_bound / n,
			}
		)

	return pd.DataFrame(rows)

