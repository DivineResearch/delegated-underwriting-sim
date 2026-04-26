# Delegated Underwriting Simulations

This repo is intentionally scalar. It validates the deterministic lifetime bound
that follows from the aggregate-credit identity in delegated underwriting:

```text
C_t = sum(seed base budgets) + sum(earned credit)
```

Delegation is not modeled because it only redistributes credit. The only modeled
round events are:

```text
repayment: C <- C + earned_credit
default:   C <- C - principal
```

If every loan has principal at most `L` and the system is alive when `C_t >= q`,
then the all-default path gives the deterministic guarantee:

```text
T >= floor((C_0 - q) / L)
```

With `n` seeds and uniform seed budget `B`, `C_0 = nB`, so the worst-case lower
bound scales linearly in `n` for fixed `B`, `L`, and `q`.

## Setup

```bash
cd delegated_underwriting_sim
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
```

## Test

```bash
pytest
```

## Validate The Bound

```bash
delegated-underwriting-sim --n-values 10,20,40 --seed-budget 2 --max-principal 1 --threshold 0
```

To write a CSV:

```bash
delegated-underwriting-sim --output results/lifetime_scaling.csv
```
