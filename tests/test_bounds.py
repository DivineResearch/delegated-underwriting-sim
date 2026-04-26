from __future__ import annotations

import pytest

from delegated_underwriting_lifetime import lifetime_bound, uniform_seed_credit, uniform_seed_lifetime_bound


def test_lifetime_bound_matches_floor_formula() -> None:
    assert lifetime_bound(initial_credit=10.0, threshold=2.0, max_principal=2.0) == 4
    assert lifetime_bound(initial_credit=10.0, threshold=0.0, max_principal=3.0) == 3


def test_lifetime_bound_is_zero_when_system_is_not_strictly_above_threshold() -> None:
    assert lifetime_bound(initial_credit=5.0, threshold=5.0, max_principal=1.0) == 0
    assert lifetime_bound(initial_credit=4.0, threshold=5.0, max_principal=1.0) == 0


def test_uniform_seed_formula_is_n_b() -> None:
    assert uniform_seed_credit(seed_count=5, seed_budget=10.0) == pytest.approx(50.0)
    assert uniform_seed_lifetime_bound(
        seed_count=5,
        seed_budget=10.0,
        threshold=12.0,
        max_principal=7.0,
    ) == 5


@pytest.mark.parametrize(
    ("initial_credit", "threshold", "max_principal"),
    [(-1.0, 0.0, 1.0), (1.0, -1.0, 1.0), (1.0, 0.0, 0.0)],
)
def test_lifetime_bound_rejects_invalid_inputs(
    initial_credit: float,
    threshold: float,
    max_principal: float,
) -> None:
    with pytest.raises(ValueError):
        lifetime_bound(initial_credit, threshold, max_principal)
