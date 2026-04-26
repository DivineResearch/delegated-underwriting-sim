from __future__ import annotations

from delegated_underwriting_lifetime.experiments import validation_rows


def test_validation_rows_show_linear_worst_case_scaling() -> None:
    rows = validation_rows(n_values=[10, 20, 40], seed_budget=2.0, max_principal=1.0, threshold=0.0)

    assert [row.lifetime_bound for row in rows] == [20, 40, 80]
    assert [row.bound_over_n for row in rows] == [2.0, 2.0, 2.0]
    assert all(row.alive_after_bound for row in rows)
    assert not any(row.alive_after_next_default for row in rows)


def test_validation_rows_use_threshold_in_the_formula() -> None:
    rows = validation_rows(n_values=[4], seed_budget=10.0, max_principal=3.0, threshold=7.0)

    row = rows[0]

    assert row.initial_credit == 40.0
    assert row.lifetime_bound == 11
    assert row.credit_after_bound == 7.0
    assert row.alive_after_bound
    assert row.credit_after_next_default == 4.0
    assert not row.alive_after_next_default
