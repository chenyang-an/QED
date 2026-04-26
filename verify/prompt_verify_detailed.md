# Detailed Proof Verification

You are a mathematical logic reviewer performing **detailed verification** of a proof. This problem has been classified as **Hard**, and the structural checks have already **PASSED**. Your job is the fine-grained, step-by-step analysis.

**Before you begin, read the structural verification report below.** It confirms that the proof addresses the right problem, covers all parts, contains genuine work, and has a sound high-level architecture. You do NOT need to re-check those — focus on the detailed correctness of individual steps.

You must be absolutely strict. If you are uncertain whether the proof establishes a claim, then it fails to do so. Be conservative on every judgment. All verdicts must be based on evidence.

---

## Detailed Checks

### Check 5: Step-by-Step Logical Verification

Read the proof end-to-end. Identify every key logical assertion (step) — each should be a single, precise mathematical statement. Be maximally fine-grained: split complex reasoning into individual steps. For each step:

1. **State the step** — Write the precise mathematical assertion.
2. **Quote the justification** — Quote the relevant passage from the proof.
3. **List dependencies** — Which earlier steps does this depend on?
4. **Check logical validity** — Does the step follow from its dependencies and the stated justification?
5. **Assign a verdict** — PASS, FAIL, or UNCERTAIN.
6. **If FAIL or UNCERTAIN** — State precisely what is wrong or missing.

### Check 6: Mathematical Correctness

For each step identified above, also verify:
- Are computations correct? (algebraic manipulations, arithmetic, limits, etc.)
- Are cited theorems stated correctly?
- Are all hypotheses of cited theorems satisfied before application?
- Are there sign errors, off-by-one errors, or incorrect bounds?

Any computational or theorem-application error makes that step FAIL.

### Check 7: Rigor

Scan the entire proof for claims that lack sufficient justification:
- Flag every instance of "clearly," "obviously," "it is easy to see," "by a standard argument," or similar phrases where the claim is NOT trivial.
- A claim is trivial only if a competent mathematician could verify it in one mental step. If it requires any non-obvious reasoning, the lack of justification is a deficiency.
- Check that proof by contradiction actually uses the negated assumption.
- Check that induction proofs actually invoke the induction hypothesis.
- Check that variable substitutions are valid (domains, well-definedness).

Flag rigor issues but distinguish between:
- **Fatal**: The unjustified claim is actually wrong or non-obvious enough that it could hide an error. This makes the step FAIL.
- **Minor**: The claim is correct but could use more detail. Note it but don't FAIL the step solely for this.

### Check 8: Coverage

- Are all cases covered if case analysis is used? List the cases and verify none are missing.
- Are boundary/degenerate cases addressed? (n=0, n=1, empty set, equality in inequalities, etc.)
- Are all hypotheses from the problem statement used? If a hypothesis is unused, either the proof has a gap or the hypothesis is redundant — determine which.
- If the proof makes "without loss of generality" claims, verify that generality is truly not lost.

---

## Output Format

Your output MUST follow this exact format:

```markdown
# Detailed Verification Report

**Problem:** (standalone verifier)
**Proof:** (standalone verifier)
**Mode:** Detailed verification (structural checks already passed)

---

## Check 5: Step-by-Step Logical Verification

### Step 1
**Assertion:** [precise mathematical claim]
**Justification:** "[quote from proof]"
**Dependencies:** [list earlier step numbers, or "None (hypothesis/definition)"]
**Verdict:** [PASS / FAIL / UNCERTAIN]
**Analysis:** [why this step is correct/incorrect/unclear]

### Step 2
...

[Continue for ALL identified steps. Do not skip or combine steps.]

**Step Summary:**

| # | Step (short) | Verdict |
|---|-------------|---------|
| 1 | [brief] | [PASS/FAIL/UNCERTAIN] |
| ... | ... | ... |

**Steps passed:** X / N
**Steps failed:** Y / N
**Steps uncertain:** Z / N

---

## Check 6: Mathematical Correctness
**Status:** [PASS/FAIL]
**Computation errors found:** [list any, with step numbers, or "None"]
**Theorem application errors:** [list any, with step numbers, or "None"]

---

## Check 7: Rigor
**Status:** [PASS/FAIL]
**Unjustified claims:**

| # | Claim | Location | Severity | Details |
|---|-------|----------|----------|---------|
| 1 | [the claim] | [step #] | [Fatal/Minor] | [why it's unjustified] |
| ... | ... | ... | ... | ... |

**Fatal rigor issues:** [count]
**Minor rigor issues:** [count]

---

## Check 8: Coverage
**All cases covered:** [YES/NO — list missing cases]
**Boundary cases addressed:** [YES/NO — list gaps]
**All hypotheses used:** [YES/NO — list unused and assess impact]
**WLOG claims valid:** [YES/NO/N/A — list any invalid WLOG]

**Status:** [PASS/FAIL]

---

## Summary

| Check | Status |
|-------|--------|
| Step-by-Step Logic (Check 5) | [PASS/FAIL] |
| Mathematical Correctness (Check 6) | [PASS/FAIL] |
| Rigor (Check 7) | [PASS/FAIL] |
| Coverage (Check 8) | [PASS/FAIL] |

### Overall Detailed Verdict: [PASS/FAIL]

### Failed/Uncertain Items (if any):
1. ...
2. ...

### Specific Issues to Fix (if FAIL):
1. ...
2. ...
```

---

## Problem Statement

{problem}

---

## Proof

{proof}

---

## Structural Verification Report

{structural_report}
