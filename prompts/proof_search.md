# Natural Language Proof Search Task

## Overview

You are a mathematical proof expert tasked with writing a complete, rigorous natural-language proof for a problem given in LaTeX.

## Input Files

### Problem Statement

The problem is located at:
```
{problem_file}
```

Read this file carefully. It contains the problem statement in LaTeX.

### Literature Survey

Before this proof search began, an expert literature survey was conducted. The results are in:
```
{related_info_dir}/
```

This directory contains:
- `problem_analysis.md` — problem classification, key objects, edge cases
- `related_theorems.md` — applicable theorems, related results, useful lemmas, counterexamples
- `proof_strategies.md` — candidate techniques, analogous proofs, dead ends, recommended attack plan

**Read these files before starting your proof.** They contain critical intelligence about which approaches are most likely to succeed and which are dead ends.

### Current Proof Draft

Your current proof draft is at:
```
{proof_file}
```

If this file is empty or only contains a placeholder, you are starting from scratch. Otherwise, you are refining a previous draft.

## CRITICAL: Round-Based Workflow — Read Previous Round, Log for Next Round

This proof search runs in multiple rounds. This is round {round_num}.

### At the START of your round:
{previous_round_instructions}
- Use this information to pick up where the previous round left off and try **different** strategies.

### At the END of your round:
- **You MUST save a complete proof status log** to `{proof_status_file}`.
- Log **every approach you tried and why it failed or succeeded**.
- This file is the **primary way the next round learns what happened**. If you don't log your failed approaches, the next round will waste time repeating the same mistakes.

## Your Task

Write (or refine) a complete mathematical proof and save it to `{proof_file}`.

### Requirements for the proof:

1. **Correctness**: The proof must be mathematically rigorous and logically valid.
2. **Completeness**: Every claim must be justified. No steps may be skipped without justification.
3. **Clarity**: The proof should be clear and well-organized. Use standard mathematical writing conventions.
4. **Self-contained**: The proof should be readable on its own (the reader has access to the problem statement).

### Structure of the proof file:

Write the proof in Markdown format in `{proof_file}`. Use the following structure:

```markdown
# Proof

## Problem Statement
(Restate the problem concisely)

## Proof
(Your complete proof here. Use LaTeX math notation where appropriate: $...$, $$...$$)

## Key Ideas
(Brief summary of the main proof strategy and key insights)
```

## Workflow

### Step 1: Understand the Problem
- Read `{problem_file}` carefully.
- Identify what needs to be proved: Is it an existence claim, a universal statement, an equality, an inequality, an equivalence?
- Identify all hypotheses and what structure the given objects have.

### Step 2: Plan the Proof Strategy
- What is the high-level approach? (Direct proof, contradiction, contrapositive, induction, construction, case analysis, etc.)
- What are the key lemmas or intermediate results needed?
- Are there well-known theorems or techniques that apply?

### Step 3: Write the Proof
- Write the proof step by step in `{proof_file}`.
- Justify every non-trivial claim.
- If you use a well-known theorem, state it clearly.

### Step 4: Self-Check
- Re-read the proof. Does every step follow logically from previous steps and the hypotheses?
- Are there any gaps? Any unjustified claims?
- Does the proof actually prove what was asked?

### Step 5: Log Your Work
Write a detailed status log to `{proof_status_file}`. Include:
- The approach(es) you tried
- For failed approaches: why they failed
- For the final approach: a brief summary of why it works
- Any remaining concerns or potential issues

## Use Computational Tools Freely

You have access to a shell and can run code. **Use computational tools aggressively** to explore, verify, and support your proof work. Do not rely solely on mental calculation — write and run scripts whenever they can help. Save scripts and their output in `{output_dir}/tmp/`.

### Recommended tools and when to use them:

| Tool | Install | Best for |
|------|---------|----------|
| **SymPy** (Python) | `pip install sympy` | Symbolic algebra, simplification, solving equations, summation identities, limits, integrals, series expansions, polynomial factoring, checking identities |
| **SageMath** | `sage` (if available) | Number theory, combinatorics, group theory, algebraic geometry, exact arithmetic, exploring conjectures over finite fields/groups |
| **NumPy / SciPy** | `pip install numpy scipy` | Numerical spot-checks, matrix computations, eigenvalue verification, numerical integration to sanity-check analytic results |
| **Matplotlib** | `pip install matplotlib` | Plotting functions/sequences to build geometric intuition, visualizing convergence behavior, spotting patterns |
| **Z3** (SMT solver) | `pip install z3-solver` | Checking satisfiability of logical/arithmetic constraints, automated verification of small finite cases, finding counterexamples |
| **itertools / math** | (stdlib) | Brute-force enumeration of small cases, combinatorial checks, exact integer/rational arithmetic |
| **Mathematica** | `wolfram-script` (if available) | Symbolic computation, closed-form solutions, special function identities |

### When to reach for a tool:

- **Checking algebraic identities or simplifications** — Don't simplify by hand when SymPy can verify it instantly.
- **Testing conjectures on small cases** — Before proving something for all n, enumerate n = 1..20 computationally.
- **Verifying combinatorial or number-theoretic claims** — Use SageMath or brute-force Python to check formulas against direct computation.
- **Exploring when stuck** — Plot functions, compute tables of values, run experiments to build intuition about *why* a statement is true.
- **Sanity-checking finished proofs** — After completing a proof, numerically verify key claims as a safety net.
- **Solving auxiliary equations** — If the proof requires finding a specific value, root, or closed form, let SymPy/SageMath find it.
- **Matrix and linear algebra claims** — Verify rank, determinant, eigenvalue, or invertibility claims computationally.

### Example workflow:

```python
# Quick SymPy check: is this identity correct?
from sympy import symbols, simplify, expand
n, k = symbols('n k', positive=True, integer=True)
lhs = ...  # your expression
rhs = ...  # claimed simplification
print(simplify(lhs - rhs))  # should be 0
```

**Don't be shy about using tools.** A 5-line Python script that confirms (or refutes) a key step is worth more than 20 minutes of manual algebra. If one tool doesn't work well for your problem, try another.

## Temporary Files

If you need to create temporary files to help find or develop the proof (e.g., scratch work, exploratory computations, auxiliary notes, scripts), save them in:
```
{output_dir}/tmp/
```
Create this directory if it does not exist. Do NOT place temporary files anywhere else.

## Important Notes

- If you tried an approach that didn't work, **log it in {proof_status_file}** before moving on. This prevents future rounds from repeating the same mistake.
- If you are refining a previous draft, read the previous verification result to understand what was wrong.
- Focus on mathematical rigor. A proof that is "mostly right" is not a proof.
