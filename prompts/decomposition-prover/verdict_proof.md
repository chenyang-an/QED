# Verdict Task: Decomposition Proof Verification

> **Decision task.** Read the verification result file(s), then make a verdict.

## Mode: {mode}

You are operating in **{mode}** mode:

- **STRUCTURAL**: Check structural verification (Phases 1-5) only. Decide if proof can proceed to detailed verification.
- **FINAL**: Check both structural and detailed verification. Make final PASS/FAIL decision.

---

## STRUCTURAL Mode

Read the structural verification report and decide whether to proceed.

### Decision Criteria

Reply with ONLY the single word **'DONE'** if:
1. **Overall Verdict in structural verification is PASS**
2. **All five phases passed** (Problem Integrity, Completeness, Citations, Decomposition Adherence, Additional Rules)

Reply with ONLY the single word **'CONTINUE'** otherwise.

### Input File (STRUCTURAL mode)

```
{structural_verification_file}
```

---

## FINAL Mode

Read both verification reports and make a final decision.

### Decision Criteria

Reply with ONLY the single word **'DONE'** if ALL of the following are satisfied:
1. **Structural Verification PASSED:** Overall Verdict = PASS
2. **Detailed Verification PASSED:** Overall Verdict = PASS
3. **No Unresolved Issues:** Neither report flags critical issues that remain unaddressed

Reply with ONLY the single word **'CONTINUE'** otherwise.

### Input Files (FINAL mode)

Structural Verification Result (Phases 1-5):
```
{structural_verification_file}
```

Detailed Verification Result (Phase 6):
```
{detailed_verification_file}
```

---

## Important Rules

- **If any verification report has Overall Verdict = FAIL, reply CONTINUE**
- **If any verification report is empty or missing, reply CONTINUE**
- Your response must be exactly one word: either `DONE` or `CONTINUE`
- Do not include any explanation or additional text
- Be strict and conservative — when in doubt, reply CONTINUE

---

## Decision Logic

### STRUCTURAL Mode
```
IF structural_verification.overall_verdict == PASS
THEN Reply: DONE
ELSE Reply: CONTINUE
```

### FINAL Mode
```
IF structural_verification.overall_verdict == PASS
   AND detailed_verification.overall_verdict == PASS
THEN Reply: DONE
ELSE Reply: CONTINUE
```
