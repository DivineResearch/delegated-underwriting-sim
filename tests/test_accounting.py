from __future__ import annotations

from itertools import product

import pytest

from delegated_underwriting_lifetime import Round, all_default_path, apply_rounds, lifetime_bound


def test_apply_rounds_matches_the_aggregate_accounting_identity() -> None:
    rounds = [
        Round(principal=100.0, defaulted=False, earned_credit=7.0),
        Round(principal=50.0, defaulted=True),
        Round(principal=25.0, defaulted=False, earned_credit=3.0),
    ]

    result = apply_rounds(initial_credit=1_000.0, rounds=rounds)

    assert result.credits == pytest.approx((1_000.0, 1_007.0, 957.0, 960.0))
    assert result.final_credit == pytest.approx(960.0)
    assert result.accounting_credit == pytest.approx(result.final_credit)
    assert result.default_loss == pytest.approx(50.0)
    assert result.minted_credit == pytest.approx(10.0)


def test_all_default_path_is_the_worst_case_for_the_bound() -> None:
    initial_credit = 10.0
    threshold = 2.0
    max_principal = 2.5
    bound = lifetime_bound(initial_credit, threshold, max_principal)

    through_bound = all_default_path(initial_credit, threshold, max_principal, bound)
    after_next_default = all_default_path(initial_credit, threshold, max_principal, bound + 1)

    assert bound == 3
    assert through_bound.final_credit == pytest.approx(2.5)
    assert through_bound.alive
    assert after_next_default.final_credit == pytest.approx(0.0)
    assert not after_next_default.alive


def test_any_round_sequence_with_losses_bounded_by_l_remains_alive_through_bound() -> None:
    initial_credit = 9.0
    threshold = 3.0
    max_principal = 2.0
    bound = lifetime_bound(initial_credit, threshold, max_principal)

    for default_pattern in product([False, True], repeat=bound):
        rounds = [
            Round(principal=max_principal, defaulted=defaulted, earned_credit=0.25)
            for defaulted in default_pattern
        ]
        result = apply_rounds(initial_credit, rounds, threshold)

        assert result.final_credit >= threshold
