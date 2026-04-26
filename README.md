# Delegated Underwriting Lifetime

> We derive a deterministic lifetime bound for the system in [Unsecured Lending via Delegated Underwriting](https://writing.divine.inc/delegated-underwriting/), using only the write-up’s aggregate-credit accounting identity

Let

$$
C_t := \sum_u c_u(t)
$$

denote total system credit after $t$ completed loan rounds. The key accounting identity from the Sybil-resistance proof is

$$
C_t = \sum_{s \in S} \widehat E_s + \sum_u G_u(t).
$$

Thus delegation itself does not create credit; it only redistributes it. The only two events that change aggregate credit are repayment and default. A repayment increases $G_v$, and hence $C_t$, by the earned-credit increment. A default of principal $x_v$ decreases aggregate credit by exactly $x_v$.

Assume every loan has principal at most $L$, and say the system is alive whenever

$$
C_t \ge q
$$

for some viability threshold $q \ge 0$. Since repayments only increase $C_t$, the worst case for lifetime is that every round defaults. Therefore, after $T$ rounds,

$$
C_T \ge C_0 - TL.
$$

Hence the system is guaranteed to remain alive through every

$$
T \le \left\lfloor \frac{C_0 - q}{L} \right\rfloor
$$

round. Equivalently, the deterministic lifetime is at least

$$
\left\lfloor \frac{C_0 - q}{L} \right\rfloor .
$$

If the system begins with no earned credit, then

$$
C_0 = \sum_{s \in S} \widehat E_s.
$$

If there are $n$ seeds, each with seed budget $B$, then

$$
C_0 = nB,
$$

so the guaranteed lifetime is at least

$$
\left\lfloor \frac{nB - q}{L} \right\rfloor .
$$

Thus, for constant $B$, $L$, and $q$, the worst-case lifetime lower bound is

$$
\Omega(n).
$$

## Simulation Check

We also run a minimal simulation to check the bound. The simulation tracks only aggregate credit,

$$
C_t = C_0 + \text{repaid earned credit} - \text{defaulted principal},
$$

rather than the full sponsor forest, so it matches exactly the scalar quantity used in the proof.

In the all-default path, it initializes $C_0 = nB$, subtracts $L$ each round, and checks when credit falls below $q$. The implemented adversarial bound is precisely

$$
\left\lfloor \frac{C_0 - q}{L} \right\rfloor .
$$

With $B = 2$, $L = 1$, and $q = 0$, the theorem predicts

$$
\left\lfloor \frac{nB - q}{L} \right\rfloor = 2n.
$$

The simulation returns

$$
n = 10 \mapsto 20, \qquad
n = 20 \mapsto 40, \qquad
n = 40 \mapsto 80.
$$

At those times, aggregate credit is exactly $0$, so the system is still alive because $q = 0$. One additional default sends aggregate credit to $-1$, so the system is no longer alive. Thus the deterministic bound is tight.

## Setup

```bash
cd /Users/diego/Projects/delegated-underwriting-lifetime
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
```

## Test

```bash
pytest
```

## Run The Check

```bash
delegated-underwriting-lifetime --n-values 10,20,40 --seed-budget 2 --max-principal 1 --threshold 0
```
