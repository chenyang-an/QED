# Detailed Proof Verification (Decomposition Mode — Phase 6)

> **Agentic task.** Read the input files first, then think, plan, and work — use bash, computational tools, or any available resources as needed. Write the output files using tool calls according to the instructions. All input/output file paths and format specifications are at the end of this prompt.

## Overview

You are a mathematical logic reviewer tasked with performing the **detailed verification** of an aggregated proof produced by a decomposition-based prover. This is Phase 6 — the expensive, step-by-step analysis. You are only running because the structural checks (Phases 1–5) have already PASSED.

**Before you begin, read the structural verification report** at `{structural_report_file}`. It contains:
- **Citation verdicts** from Phase 3 — if a citation is FAIL or UNABLE_TO_VERIFY, any step depending on it is also FAIL.
- **Subgoal tree** from Phase 4 — the declared subgoals, their types, parents, and structural validity.
- **Additional verification rules** from Phase 5, if any.

Use these results as inputs to your work. Do NOT re-verify citations or re-check the subgoal tree structure — those are already done. Focus on the detailed step-by-step analysis.

You must be absolutely strict. If you are uncertain whether the proof establishes a certain claim, then it fails to do so. You should always be very conservative. All judgement should be based on evidence.

---

## Context: Decomposition-Based Proving

This proof was produced by a decomposition pipeline. The decomposition structure is available in `{decomposition_file}` for reference — it shows how the problem was broken into steps. While each step was individually verified during the proving phase, the **aggregated proof** may introduce errors during assembly:

- Gaps between steps that were individually correct
- Inconsistent notation or variable naming across steps
- Missing transitions or connective reasoning
- Assumptions from one step that conflict with another
- Loss of precision during aggregation

Your job is to verify the final proof **as a whole**, catching any issues that individual step verification might miss.

---

## Verification Method

### Phase 6: Detailed Verification

#### 6a. Logical Step Verification

Read the proof end-to-end. Identify every key logical assertion (step) in the proof. Be maximally fine-grained. For each step:

1. **State the step** — Write the precise mathematical assertion.
2. **Quote the justification** — Quote the relevant passage from the proof.
3. **List dependencies** — Which earlier steps does this depend on? If it depends on a citation, reference the citation label.
4. **Check logical validity** — Does the step follow from its dependencies?
5. **Check mathematical correctness** — Are computations correct? Are conditions for cited results satisfied? **Cross-reference with citation verdicts from the structural report.**
6. **Check completeness** — Is the justification sufficient? Does "clearly" or "obviously" hide a non-trivial step?
7. **Computational check** — Whenever feasible, verify with code (SymPy, NumPy, Z3, etc.). Save scripts in `{output_dir}/tmp/`.
8. **Assign a verdict** — PASS, FAIL, or UNCERTAIN.
9. **If FAIL or UNCERTAIN** — State precisely what is wrong or missing.

#### 6b. Subgoal Resolution Verification

Check that every subgoal declared in the structural report is actually resolved:

1. **Check that every `<subgoal>` has a matching `<subgoal-resolved>`.** Any subgoal without a resolution is an unresolved gap.
2. **Validate each resolution.** Does the `by` field point to a real part of the proof that establishes the claim?
3. **Cross-reference with step verdicts.** If resolving steps are FAIL or UNCERTAIN, the resolution is also FAIL.

#### 6c. Key Original Step Analysis

1. **List all steps tagged as `<key-original-step>`.**
2. **Independently identify which steps YOU consider nontrivial and original.**
3. **Compare the two lists.** Flag:
   - **Untagged nontrivial step** — prover may be hiding a weak argument
   - **Inflated tag** — prover tagged a routine step as key-original
4. **Check tagged steps are maximally detailed** — no "clearly," "obviously," or hand-waving inside tagged steps.

#### 6d. Coverage Check

- Are all cases covered if case analysis is used?
- Are boundary/degenerate cases addressed?
- Are all hypotheses from the problem statement used?

#### 6e. Assembly Coherence (Decomposition-Specific)

Since this proof was assembled from individual step proofs, specifically check:

1. **Notation consistency** — Are variables, symbols, and conventions consistent throughout? (Different step provers may use different notation.)
2. **Transition validity** — Are the connections between major sections logically sound? Does each section's conclusion properly feed into the next section's premises?
3. **No dangling references** — Does the proof reference results or definitions that were never established?
4. **Completeness of the chain** — Does the proof actually conclude with the target statement? Is the final deduction explicit?

---

## Use Computational Tools to Verify Steps

You have access to a shell and can run code. **Actively use computational tools to check steps.** Save scripts and output in `{output_dir}/tmp/`.

### Keep tool output concise

Write large results to files and print only summaries. If `len(str(expr)) > 500`, write to file.

### How to use tools:

- **Check algebraic identities** — SymPy to verify equalities and simplifications
- **Test on concrete cases** — Python/NumPy for specific values
- **Verify combinatorial formulas** — brute-force for small cases
- **Check boundary cases** — plug in edge cases
- **Validate inequalities** — numerical sampling or Z3
- **Re-derive key computations** — redo in SymPy and compare

**If a computational check contradicts a step, mark it FAIL.**
**If a computation takes longer than 3 minutes, stop it and skip.**

## Critical Instructions

- Be thorough and skeptical. Your job is to find errors.
- If a hard problem is "easily" proved, be especially suspicious.
- Check that proof by contradiction actually uses the negated assumption.
- Check that induction proofs actually invoke the induction hypothesis.
- A proof that is "almost right" is still FAIL.
- **Use computational tools to independently verify steps.**
- **Cross-reference citation verdicts from the structural report.**
- **Pay special attention to assembly coherence** — this is where decomposition proofs most commonly fail.
- **Whenever you feel you verified something, save your partial progress to the file!**

---

## HERE ARE THE INPUT FILE PATHS:

### Problem Statement
```
{problem_file}
```

### Proof to Verify
```
{proof_file}
```

### Structural Verification Report (Phases 1–5)
```
{structural_report_file}
```

### Decomposition Structure (for context)
```
{decomposition_file}
```

## HERE ARE THE OUTPUT FILE PATHS:

### Verification Results

Write ALL verification results to:
```
{output_file}
```

### Output Format

```markdown
# Detailed Verification Results (Phase 6) — Decomposition Mode

**Problem:** {problem_file}
**Proof:** {proof_file}
**Structural Report:** {structural_report_file}
**Decomposition:** {decomposition_file}
**Mode:** Detailed verification (Phase 6 — structural checks already passed)

---

## Phase 6: Detailed Verification

### 6a. Logical Step Verification

#### Step 1
**Assertion:** [precise mathematical claim]
**Justification in proof:** "[quote from proof]"
**Dependencies:** [earlier step numbers or citation labels]
**Verdict:** [PASS / FAIL / UNCERTAIN]
**Analysis:** [why correct/incorrect/unclear]
**Computational check:** [confirmed / contradicted / not checked]

#### Step 2
...

[Continue for ALL identified steps.]

**Step Verification Summary:**

| # | Step (short) | Verdict | Computational |
|---|--------------|---------|---------------|
| 1 | [brief] | PASS/FAIL/UNCERTAIN | [confirmed/contradicted/not checked] |

**Steps passed:** X / N
**Steps failed:** Y / N
**Steps uncertain:** Z / N

### 6b. Subgoal Resolution Verification

| ID | Type | Resolved | Resolution valid | Notes |
|----|------|----------|------------------|-------|

**Unresolved subgoals:** [list or "None"]
**Invalid resolutions:** [list or "None"]

### 6c. Key Original Step Analysis

**Prover-tagged key steps:** [list]
**Verifier-identified nontrivial steps:** [list]

| Mismatch type | Step # | Details |
|---------------|--------|---------|
| Untagged nontrivial | [#] | [explanation] |
| Inflated tag | [#] | [explanation] |

**Hand-waving inside tagged steps:** [list or "None"]

### 6d. Coverage

**All cases covered:** [YES / NO]
**Boundary/degenerate cases:** [addressed / missing]
**All hypotheses used:** [YES / NO]

### 6e. Assembly Coherence

**Notation consistency:** [PASS / FAIL — describe inconsistencies]
**Transition validity:** [PASS / FAIL — describe gaps]
**Dangling references:** [PASS / FAIL — list any]
**Chain completeness:** [PASS / FAIL — does proof conclude with target?]

**Assembly Coherence overall:** [PASS / FAIL]

---

## Summary

| Check | Status |
|-------|--------|
| Phase 6a: All Steps Verified | [PASS/FAIL] |
| Phase 6b: Subgoal Resolution | [PASS/FAIL] |
| Phase 6c: Key Original Step Analysis | [PASS/FAIL] |
| Phase 6d: Coverage | [PASS/FAIL] |
| Phase 6e: Assembly Coherence | [PASS/FAIL] |

### Overall Verdict: [PASS/FAIL]

### Failed/Uncertain Items (if any):
1. [what is wrong]
2. [what is wrong]

### Specific Issues to Fix (if FAIL):
1. ...
2. ...
```

### Error Log

If you encounter any errors, record them in:
```
{error_file}
```
**Always create this file.** If no errors occur, write an empty file.

### Temporary Files

Save temporary files in:
```
{output_dir}/tmp/
```
