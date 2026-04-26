"""Reusable experiment runners for lifetime scaling checks."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

import pandas as pd

from delegated_underwriting_sim.aggregate import simulate_many

if TYPE_CHECKING:
	from matplotlib.figure import Figure


DEFAULT_N_VALUES = (10, 20, 40, 80, 160, 320)


def lifetime_scaling_table(
	n_values: Sequence[int] = DEFAULT_N_VALUES,
	trials: int = 10_000,
	seed_budget: float = 1.0,
	principal: float = 1.0,
	default_prob: float = 0.05,
	max_rounds: int = 10_000_000,
	epsilon: float = 0.01,
	seed: int | None = 0,
) -> pd.DataFrame:
	"""Return the main lifetime scaling experiment table."""

	return simulate_many(
		n_values=n_values,
		trials=trials,
		seed_budget=seed_budget,
		principal=principal,
		default_prob=default_prob,
		max_rounds=max_rounds,
		epsilon=epsilon,
		seed=seed,
	)


def plot_lifetime_scaling(results: pd.DataFrame) -> "Figure":
	"""Plot adversarial linear scaling and stochastic quadratic scaling diagnostics."""

	import matplotlib.pyplot as plt

	fig, axes = plt.subplots(ncols=2, figsize=(12, 4), constrained_layout=True)

	axes[0].plot(results["n"], results["adversarial_over_n"], marker="o")
	axes[0].set_title("Adversarial survival / n")
	axes[0].set_xlabel("n seeds")
	axes[0].set_ylabel("rounds / n")

	axes[1].plot(results["n"], results["p01_over_n2"], marker="o", label="empirical p01 / n^2")
	axes[1].plot(
		results["n"],
		results["theoretical_bound"] / (results["n"] ** 2),
		marker="o",
		label="bound / n^2",
	)
	axes[1].set_title("Stochastic lower-tail lifetime / n^2")
	axes[1].set_xlabel("n seeds")
	axes[1].set_ylabel("rounds / n^2")
	axes[1].legend()

	return fig


def _parse_n_values(raw: str) -> list[int]:
	values = [int(value.strip()) for value in raw.split(",") if value.strip()]

	if not values:
		raise argparse.ArgumentTypeError("provide at least one n value")

	return values


def main() -> None:
	parser = argparse.ArgumentParser(description="Run simulations for the delegated underwriting lending model.")
	parser.add_argument("--n-values", type=_parse_n_values, default=list(DEFAULT_N_VALUES))
	parser.add_argument("--trials", type=int, default=10_000)
	parser.add_argument("--seed-budget", type=float, default=1.0)
	parser.add_argument("--principal", type=float, default=1.0)
	parser.add_argument("--default-prob", type=float, default=0.05)
	parser.add_argument("--max-rounds", type=int, default=10_000_000)
	parser.add_argument("--epsilon", type=float, default=0.01)
	parser.add_argument("--seed", type=int, default=0)
	parser.add_argument("--output", type=Path)
	parser.add_argument("--plot", type=Path)
	args = parser.parse_args()

	results = lifetime_scaling_table(
		n_values=args.n_values,
		trials=args.trials,
		seed_budget=args.seed_budget,
		principal=args.principal,
		default_prob=args.default_prob,
		max_rounds=args.max_rounds,
		epsilon=args.epsilon,
		seed=args.seed,
	)

	if args.output is not None:
		args.output.parent.mkdir(parents=True, exist_ok=True)
		results.to_csv(args.output, index=False)
	else:
		print(results.to_string(index=False))

	if args.plot is not None:
		args.plot.parent.mkdir(parents=True, exist_ok=True)
		fig = plot_lifetime_scaling(results)
		fig.savefig(args.plot, dpi=160)


if __name__ == "__main__":
	main()
