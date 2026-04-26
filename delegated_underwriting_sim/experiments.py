"""Deterministic validation table for the lifetime bound."""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from collections.abc import Sequence

from delegated_underwriting_sim.aggregate import all_default_path
from delegated_underwriting_sim.bounds import lifetime_bound, uniform_seed_credit

DEFAULT_N_VALUES = (10, 20, 40, 80, 160, 320)


@dataclass(frozen=True)
class ValidationRow:
    seed_count: int
    seed_budget: float
    initial_credit: float
    threshold: float
    max_principal: float
    lifetime_bound: int
    credit_after_bound: float
    alive_after_bound: bool
    credit_after_next_default: float
    alive_after_next_default: bool
    bound_over_n: float


def validation_rows(
    n_values: Sequence[int] = DEFAULT_N_VALUES,
    seed_budget: float = 1.0,
    max_principal: float = 1.0,
    threshold: float = 0.0,
) -> list[ValidationRow]:
    """Return rows that validate ``floor((nB - q) / L)`` for each seed count."""

    if not n_values:
        raise ValueError("n_values must not be empty")

    rows: list[ValidationRow] = []

    for seed_count in n_values:
        initial_credit = uniform_seed_credit(seed_count, seed_budget)
        bound = lifetime_bound(initial_credit, threshold, max_principal)
        through_bound = all_default_path(initial_credit, threshold, max_principal, bound)
        after_next_default = all_default_path(initial_credit, threshold, max_principal, bound + 1)

        rows.append(
            ValidationRow(
                seed_count=seed_count,
                seed_budget=seed_budget,
                initial_credit=initial_credit,
                threshold=threshold,
                max_principal=max_principal,
                lifetime_bound=bound,
                credit_after_bound=through_bound.final_credit,
                alive_after_bound=through_bound.alive,
                credit_after_next_default=after_next_default.final_credit,
                alive_after_next_default=after_next_default.alive,
                bound_over_n=bound / seed_count,
            )
        )

    return rows


def write_csv(rows: Sequence[ValidationRow], path: Path) -> None:
    """Write validation rows to CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)


def format_table(rows: Sequence[ValidationRow]) -> str:
    """Return a small fixed-width table for terminal output."""

    dict_rows = [asdict(row) for row in rows]
    headers = list(dict_rows[0].keys())
    rendered_rows = [[_format_cell(row[header]) for header in headers] for row in dict_rows]
    widths = [
        max(len(header), *(len(rendered_row[index]) for rendered_row in rendered_rows))
        for index, header in enumerate(headers)
    ]
    header_line = "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    body = [
        "  ".join(value.ljust(widths[index]) for index, value in enumerate(rendered_row))
        for rendered_row in rendered_rows
    ]

    return "\n".join([header_line, *body])


def _format_cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:g}"

    return str(value)


def _parse_n_values(raw: str) -> list[int]:
    values = [int(value.strip()) for value in raw.split(",") if value.strip()]

    if not values:
        raise argparse.ArgumentTypeError("provide at least one n value")

    return values


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the deterministic delegated-underwriting lifetime bound."
    )
    parser.add_argument("--n-values", type=_parse_n_values, default=list(DEFAULT_N_VALUES))
    parser.add_argument("--seed-budget", type=float, default=1.0)
    parser.add_argument("--max-principal", type=float, default=1.0)
    parser.add_argument("--threshold", type=float, default=0.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rows = validation_rows(
        n_values=args.n_values,
        seed_budget=args.seed_budget,
        max_principal=args.max_principal,
        threshold=args.threshold,
    )

    if args.output is not None:
        write_csv(rows, args.output)
    else:
        print(format_table(rows))


if __name__ == "__main__":
    main()
