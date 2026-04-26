# Delegated Underwriting Simulations

The model tracks total system credit:

```text
C_t = C_0 + repaid earned credit - defaulted principal
```

It is intentionally scalar and theorem-facing. It does not simulate the sponsor forest, behavioral agents, or overlapping loan maturities yet.

## Setup

```bash
cd delegated_underwriting_simulations
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
```

## Run Tests

```bash
pytest
```

## Run The Default Experiment

```bash
delegated-underwriting-simulations --trials 5000 --output results/lifetime_scaling.csv
```

The output table includes empirical lifetime quantiles, the conservative high-probability theoretical bound, and normalized values for checking linear versus quadratic scaling.

