from __future__ import annotations

import math

import pytest

from delegated_underwriting_simulations import (
	adversarial_survival_bound,
	deterministic_survival_bound,
	risk_premium,
	simulate_path,
	theoretical_bound,
)


def test_risk_premium_is_break_even_without_margin() -> None:
	principal = 100.0
	default_prob = 0.05

	premium = risk_premium(principal=principal, default_prob=default_prob)

	assert (1 - default_prob) * premium == pytest.approx(default_prob * principal)


def test_theoretical_bound_matches_azuma_formula() -> None:
	n = 10
	seed_budget = 1.0
	principal = 1.0
	default_prob = 0.05
	epsilon = 0.01
	threshold = 1.0
	premium = risk_premium(principal=principal, default_prob=default_prob)
	max_step = max(principal, premium)
	expected = math.floor(((n * seed_budget) - threshold) ** 2 / (2 * max_step**2 * math.log(1 / epsilon)))

	assert (
		theoretical_bound(
			n=n,
			seed_budget=seed_budget,
			principal=principal,
			default_prob=default_prob,
			epsilon=epsilon,
		)
		== expected
	)


def test_adversarial_bound_counts_rounds_that_remain_viable() -> None:
	bound = adversarial_survival_bound(n=10, seed_budget=1.0, principal=2.0)
	result = simulate_path(
		n=10,
		seed_budget=1.0,
		principal=2.0,
		default_prob=0.5,
		default_indicators=[True] * 10,
	)

	assert bound == 4
	assert result.lifetime == bound + 1
	assert result.stopped_by == "threshold"


def test_deterministic_survival_bound_is_infinite_when_repayments_cover_losses() -> None:
	assert (
		deterministic_survival_bound(
			initial_credit=10.0,
			threshold=1.0,
			max_loss=1.0,
			default_fraction=0.25,
			min_repayment_credit=1.0,
		)
		== math.inf
	)

