from __future__ import annotations

from delegated_underwriting_sim import simulate_many


def test_simulate_many_returns_expected_scaling_columns() -> None:
	results = simulate_many(
		n_values=[4, 8],
		trials=32,
		seed_budget=1.0,
		principal=1.0,
		default_prob=0.05,
		max_rounds=250,
		seed=123,
	)

	assert list(results["n"]) == [4, 8]
	assert set(
		[
			"mean_lifetime",
			"p10_lifetime",
			"p01_lifetime",
			"theoretical_bound",
			"adversarial_survival_bound",
			"p01_over_n2",
			"adversarial_over_n",
		]
	).issubset(results.columns)
	assert (results["trials"] == 32).all()
	assert (results["p01_lifetime"] >= results["theoretical_bound"]).all()


def test_simulate_many_is_reproducible_with_a_seed() -> None:
	first = simulate_many(n_values=[4], trials=16, max_rounds=100, seed=7)
	second = simulate_many(n_values=[4], trials=16, max_rounds=100, seed=7)

	assert first.equals(second)

