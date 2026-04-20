# Structural Proof Verification (Decomposition Mode — Phases 1–5)

> **Agentic task.** Read the input files first, then think, plan, and work — use bash, computational tools, or any available resources as needed. Write the output files using tool calls according to the instructions. All input/output file paths and format specifications are at the end of this prompt.

## Overview

You are a mathematical logic reviewer tasked with performing the **structural verification** of an aggregated proof produced by a decomposition-based prover. This proof was assembled from individually-proved steps — your job is to verify the **final aggregated proof as a whole**, checking that the assembly is correct and the proof is structurally sound.

This covers five phases: Problem-Statement Integrity, Completeness and Originality Check, Citation Verification, Subgoal Tree Structure, and Additional Verification Rules. These are the foundational checks — if the proof fails any of these, detailed step-by-step verification will not be attempted.

**IMPORTANT: Your task is ONLY the five structural phases described below. Do NOT perform detailed step-by-step verification of individual proof steps — that is the responsibility of a separate detailed verifier (Phase 6). Your job is to check the proof's structural foundations: whether it addresses the right problem, covers all questions, contains genuine proof work, has valid citations, and has a sound subgoal architecture. Do NOT verify whether each logical step in the proof is mathematically correct — leave that to the detailed verifier.**

---

## Context: Decomposition-Based Proving

This proof was produced by a decomposition pipeline that:
1. Decomposed the problem into intermediate steps
2. Proved each step individually
3. Verified each step individually
4. Aggregated all step proofs into the final proof

The decomposition structure is available in `{decomposition_file}` for reference. However, your verification is on the **final aggregated proof** — you should evaluate it as a standalone document. The decomposition context helps you understand the proof's origin but does not excuse structural deficiencies in the final output.

---

## Verification Method

The verification proceeds in five phases, ordered from cheapest/most-fatal to most-expensive.

### Phase 1: Problem-Statement Integrity

**This is the most critical check and must be done FIRST, before anything else.**

The aggregation process may — intentionally or accidentally — alter, weaken, or re-interpret the problem statement. You must catch this.

1. Read the **original** problem statement from `{problem_file}` verbatim.
2. Identify the claim the proof **actually proves** (look at what it states at the beginning and what it concludes).
3. Compare the two **word-by-word**. Flag ANY discrepancy, including but not limited to:
   - Changed quantifiers (e.g. "for all" → "there exists", or an added/dropped "for all")
   - Strengthened or weakened hypotheses (extra assumptions added, or conditions dropped)
   - Modified constants, bounds, or inequalities (e.g. strict vs. non-strict, changed exponents)
   - Restricted domain (e.g. proving for integers when the problem says reals)
   - Swapped conclusion and hypothesis (proving the converse instead of the original)
   - Subtle rephrasing that changes meaning (e.g. "at most" → "at least", "unique" dropped)
   - Proving a special case instead of the general statement
4. If the proof does not state the problem it is proving, that itself is a FAIL.

**If the problem the proof claims to solve differs from `{problem_file}` in ANY mathematically meaningful way, this check is FAIL.**

### Phase 2: Completeness and Originality Check

#### 2a. Check that all questions are addressed

1. **Identify all questions/tasks in the problem.** Read `{problem_file}` carefully and extract every distinct question, claim to prove, or task.
2. **Check each question against the proof.** For every question/task identified:
   - Does the proof explicitly address this question?
   - Is there a clear section, statement, or argument dedicated to answering it?
   - If the problem has multiple parts, are ALL parts addressed?
3. **Flag any unaddressed questions.**

#### 2b. Check for genuine proof work (not just resource gathering)

**A valid proof must contain original reasoning and argument, not merely a collection of external references.** Check for:

1. **Pure resource aggregation** — listing theorems without applying them
2. **Missing proof work** — stating what needs to be proved without proving it
3. **Genuine proof indicators** — original logical arguments, explicit reasoning steps, application of cited results

**Phase 2 overall:** PASS if ALL questions are explicitly addressed AND the proof contains genuine original proof work. FAIL otherwise.

### Phase 3: Citation Verification

#### 3a. Identify all citations

Scan the entire proof for `<cite>...</cite>` blocks. List every citation found.

#### 3b. Check citation format

Every citation must use exactly this format:

```
<cite>type=TYPE; label=LABEL; title=TITLE; authors=AUTHORS; source_url=URL; verifier_locator=EXACT_LOCATOR; statement_match=exact; statement=EXACT_STATEMENT_FROM_SOURCE; usage=EXACTLY_HOW_IT_IS_USED_HERE</cite>
```

For each citation, verify all required fields are present and correctly formatted.

#### 3c. Verify faithfulness of each citation

**For EVERY citation, independently check whether the cited result is real and faithfully stated:**

1. **Check the source URL** — does it work and point to the claimed source?
2. **Check title and authors** — do they match the actual source?
3. **Locate the exact statement** — using the `verifier_locator`
4. **Compare the statement** — word-by-word match with the source
5. **Check usage correctness** — is the cited result applicable as described?

**Verdict for each citation:** PASS / FAIL / UNABLE_TO_VERIFY

**If ANY citation is FAIL, this phase is FAIL.**

### Phase 4: Subgoal Tree Structure

Check the proof's logical architecture:

1. **List all declared subgoals and resolutions.**
2. **Check the tree structure** — parents valid, no orphans, no cycles.
3. **Check each node's justification** — are reductions logically sound?
4. **Cross-reference conditions with citations** — are all hypotheses of cited results checked?
5. **Check tree completeness** — do subgoals cover the entire proof architecture?

**Phase 4 overall:** PASS if tree well-formed, all reductions valid, and no missing subgoals. FAIL otherwise.

### Phase 5: Additional Verification Rules

Read the following files if they exist and are non-empty:

1. **Global verification rules:** `{additional_verify_rule_global_file}`

If rules exist, check the proof against each one. Every rule is a hard requirement.

**Phase 5 overall:** PASS if no rules exist, or if the proof satisfies ALL rules. FAIL otherwise.

---

## Use Computational Tools for Citation Verification

You have access to a shell and can run code. **You should actively use computational tools to check citations.** Save scripts and their output in `{output_dir}/tmp/`.

### Keep tool output concise

Write large results to files in `{output_dir}/tmp/` and print only summaries. If `len(str(expr)) > 500`, write to file instead of printing.

**Do NOT use computational tools to verify mathematical correctness of proof steps** — that is the job of the detailed verifier.

**If an algorithmic run takes longer than 3 minutes, stop it and skip that computation.**

## Critical Instructions

- **ONLY perform the five structural phases.** Do NOT check whether individual proof steps are mathematically correct.
- **Follow the five phases in order.**
- Be thorough and skeptical. Your job is to find structural errors.
- **Citations are the #1 source of hallucinations. Check every single one.**
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

### Decomposition Structure (for context only)
```
{decomposition_file}
```

### Global Verification Rules (for Phase 5)
```
{additional_verify_rule_global_file}
```

## HERE ARE THE OUTPUT FILE PATHS:

### Verification Results

Write ALL verification results to:
```
{output_file}
```

### Output Format

```markdown
# Structural Verification Results (Phases 1–5) — Decomposition Mode

**Problem:** {problem_file}
**Proof:** {proof_file}
**Decomposition:** {decomposition_file}
**Mode:** Structural verification (Phases 1–5)

---

## Phase 1: Problem-Statement Integrity

**Status:** [PASS/FAIL]
**Original problem (from {problem_file}):** [quote verbatim]
**Problem as stated/implied in proof:** [quote what the proof claims to prove]
**Discrepancies:** [list every difference, or "None — exact match"]

---

## Phase 2: Completeness and Originality Check

### 2a. Questions Addressed

**Questions/tasks identified in problem:** [N total]

| # | Question/Task | Addressed | Location in Proof |
|---|---------------|-----------|-------------------|
| 1 | [description] | [YES/NO/PARTIAL] | [section reference or "Not found"] |

**All questions addressed:** [YES / NO]

### 2b. Originality Check

**Contains original proof work:** [YES / NO]
**Evidence of genuine reasoning:** [describe]
**Issues found:** [describe or "None"]

**Phase 2 overall:** [PASS / FAIL]

---

## Phase 3: Citation Verification

**Citations found:** [N total]

### Citation 1: [label]
**Source:** [title, authors]
**URL check:** [works / broken / wrong source]
**Statement check:** [matches / does not match / not found]
**Usage check:** [correct / incorrect]
**Verdict:** [PASS / FAIL / UNABLE_TO_VERIFY]

[Continue for ALL citations]

**Citation Summary:**
| # | Label | Source verified | Statement matches | Usage correct | Verdict |
|---|-------|---------------|-------------------|---------------|---------|

**Phase 3 overall:** [PASS / FAIL]

---

## Phase 4: Subgoal Tree Structure

**Subgoals declared:** [N total]
**Tree well-formed:** [YES / NO]
**Invalid reductions:** [list or "None"]
**Missing subgoals:** [list or "None"]

**Phase 4 overall:** [PASS / FAIL]

---

## Phase 5: Additional Verification Rules

**Rules found:** [N total, or "None"]

[Per-rule verdicts if rules exist]

**Phase 5 overall:** [PASS / FAIL / PASS (no rules)]

---

## Summary

| Check | Status |
|-------|--------|
| Phase 1: Problem-Statement Integrity | [PASS/FAIL] |
| Phase 2: Completeness and Originality Check | [PASS/FAIL] |
| Phase 3: Citation Verification | [PASS/FAIL] |
| Phase 4: Subgoal Tree Structure | [PASS/FAIL] |
| Phase 5: Additional Verification Rules | [PASS/FAIL] |

### Overall Verdict: [PASS/FAIL]

### Failed Items (if any):
1. [what is wrong]
2. [what is wrong]

### Specific Issues to Fix (if FAIL):
1. ...
2. ...
```

### Error Log

If you encounter any errors during this call, record them in:
```
{error_file}
```
**Always create this file.** If no errors occur, write an empty file.

### Temporary Files

Save temporary files in:
```
{output_dir}/tmp/
```
