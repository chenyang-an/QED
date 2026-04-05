# Proof

## Problem Statement
Compute what is 5th Fibonacci number.

## Proof
The Fibonacci sequence $(F_n)$ is defined by the recurrence relation:
$$F_n = F_{n-1} + F_{n-2}$$
with the standard initial conditions $F_1 = 1$ and $F_2 = 1$.

We compute the terms iteratively up to the 5th term:
- By definition, the first Fibonacci number is $F_1 = 1$.
- By definition, the second Fibonacci number is $F_2 = 1$.
- Applying the recurrence for $n=3$, the third Fibonacci number is $F_3 = F_2 + F_1 = 1 + 1 = 2$.
- Applying the recurrence for $n=4$, the fourth Fibonacci number is $F_4 = F_3 + F_2 = 2 + 1 = 3$.
- Applying the recurrence for $n=5$, the fifth Fibonacci number is $F_5 = F_4 + F_3 = 3 + 2 = 5$.

Even if we consider the convention where the sequence starts with $F_0 = 0$ and $F_1 = 1$, the index $n=5$ yields the same result:
- $F_0 = 0$
- $F_1 = 1$
- $F_2 = F_1 + F_0 = 1 + 0 = 1$
- $F_3 = F_2 + F_1 = 1 + 1 = 2$
- $F_4 = F_3 + F_2 = 2 + 1 = 3$
- $F_5 = F_4 + F_3 = 3 + 2 = 5$

Thus, under either standard convention, the 5th Fibonacci number is $5$.

## Key Ideas
The result is obtained by directly applying the definition of the Fibonacci sequence and computing its terms iteratively up to the 5th index.
