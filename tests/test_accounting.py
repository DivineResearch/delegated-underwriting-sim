from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from delegated_underwriting_sim import Round, apply_rounds, risk_premium, simulate_path


def test_apply_rounds_updates_credit_by_the_accounting_identity() -> None:
	rounds = [
		Round(defaulted=False, principal=100.0, repayment_credit=7.0),
		Round(defaulted=True, principal=50.0, repayment_credit=7.0),
		Round(defaulted=False, principal=25.0, repayment_credit=3.0),
	]

	result = apply_rounds(initial_credit=1_000.0, rounds=rounds, stop_at_threshold=False)

	assert result.final_credit == pytest.approx(960.0)
	assert result.accounting_credit == pytest.approx(result.final_credit)
	assert result.default_loss == pytest.approx(50.0)
	assert result.minted_credit == pytest.approx(10.0)


@given(
	initial_cents=st.integers(min_value=0, max_value=1_000_000),
	round_specs=st.lists(
		st.tuples(
			st.booleans(),
			st.integers(min_value=0, max_value=100_000),
			st.integers(min_value=0, max_value=100_000),
		),
		max_size=100,
	),
)
def test_accounting_identity_holds_for_generated_round_sequences(
	initial_cents: int,
	round_specs: list[tuple[bool, int, int]],
) -> None:
	initial_credit = initial_cents / 100.0
	rounds = [
		Round(defaulted=defaulted, principal=principal_cents / 100.0, repayment_credit=repayment_cents / 100.0)
		for defaulted, principal_cents, repayment_cents in round_specs
	]

	result = apply_rounds(initial_credit=initial_credit, rounds=rounds, stop_at_threshold=False)
	expected = initial_credit + sum(
		-repayment_round.principal if repayment_round.defaulted else repayment_round.repayment_credit
		for repayment_round in rounds
	)

	assert result.accounting_credit == pytest.approx(expected)
	assert result.final_credit == pytest.approx(expected)


def test_simulate_path_accepts_explicit_default_sequence() -> None:
	principal = 10.0
	default_prob = 0.2
	premium = risk_premium(principal=principal, default_prob=default_prob)

	result = simulate_path(
		n=3,
		seed_budget=10.0,
		principal=principal,
		default_prob=default_prob,
		default_indicators=[False, True, False],
		stop_at_threshold=False,
	)

	assert result.lifetime == 3
	assert result.final_credit == pytest.approx(30.0 + premium - principal + premium)
	assert result.accounting_credit == pytest.approx(result.final_credit)

