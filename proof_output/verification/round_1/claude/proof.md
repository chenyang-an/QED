# Proof

## Problem Statement

Compute what is 5th Fibonacci number.

## Proof

We compute the 5th Fibonacci number using the standard recursive definition.

**Definition (Fibonacci Sequence):** The Fibonacci sequence $\{F_n\}_{n \geq 1}$ is defined by:
- $F_1 = 1$
- $F_2 = 1$
- $F_n = F_{n-1} + F_{n-2}$ for all $n \geq 3$

**Computation:**

We apply the recurrence relation step by step:

**Step 1:** $F_1 = 1$ (by definition)

**Step 2:** $F_2 = 1$ (by definition)

**Step 3:** Compute $F_3$.
By the recurrence relation with $n = 3$:
$$F_3 = F_2 + F_1 = 1 + 1 = 2$$

**Step 4:** Compute $F_4$.
By the recurrence relation with $n = 4$:
$$F_4 = F_3 + F_2 = 2 + 1 = 3$$

**Step 5:** Compute $F_5$.
By the recurrence relation with $n = 5$:
$$F_5 = F_4 + F_3 = 3 + 2 = 5$$

**Conclusion:** The 5th Fibonacci number is $\boxed{5}$.

---

**Verification via Binet's Formula (Alternative Method):**

For completeness, we verify the answer using Binet's closed-form formula:
$$F_n = \frac{\phi^n - \psi^n}{\sqrt{5}}$$
where $\phi = \frac{1 + \sqrt{5}}{2}$ (the golden ratio) and $\psi = \frac{1 - \sqrt{5}}{2}$.

For $n = 5$:
- $\phi^5 = \left(\frac{1 + \sqrt{5}}{2}\right)^5$
- $\psi^5 = \left(\frac{1 - \sqrt{5}}{2}\right)^5$

Computing numerically: $\phi \approx 1.6180339887$ and $\psi \approx -0.6180339887$.
- $\phi^5 \approx 11.0901699437$
- $\psi^5 \approx -0.0901699437$
- $\phi^5 - \psi^5 \approx 11.1803398875$
- $\frac{\phi^5 - \psi^5}{\sqrt{5}} \approx \frac{11.1803398875}{2.2360679775} = 5$

This confirms $F_5 = 5$.

---

**Note on Indexing Convention:**

Some authors use the convention $F_0 = 0$, $F_1 = 1$, which shifts all indices by 1. Under this convention, the sequence begins:
- $F_0 = 0, F_1 = 1, F_2 = 1, F_3 = 2, F_4 = 3, F_5 = 5, \ldots$

In this case, $F_5 = 5$ as well, so the answer is the same regardless of whether we use 0-indexing or 1-indexing.

## Key Ideas

1. **Direct application of the recursive definition:** The Fibonacci sequence is uniquely determined by its initial conditions ($F_1 = 1$, $F_2 = 1$) and the recurrence relation ($F_n = F_{n-1} + F_{n-2}$). We simply iterate the recurrence three times starting from the base cases.

2. **The computation is straightforward:** $F_1 = 1 \to F_2 = 1 \to F_3 = 2 \to F_4 = 3 \to F_5 = 5$.

3. **The answer is 5:** This is confirmed both by direct computation from the definition and by Binet's closed-form formula.
