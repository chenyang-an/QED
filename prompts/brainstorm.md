# Brainstorm: Proof Strategy Ideas

> **Non-agentic task.** Read the input context, think creatively, and write your brainstorm output to the specified file. This is a SHORT creative brainstorming task (300-500 words), not a proof-writing task.

## Overview

You are one of several independent models brainstorming proof strategies for a mathematical problem. Your goal is to propose **original, diverse, and creative** high-level proof ideas that will inspire the actual proof-writing agent in the next step.

**This is NOT a proof.** Do not write proofs, do not execute computations, do not verify anything. Just brainstorm strategy ideas — the key insights, tricks, or approaches that might unlock the proof.

## Round Context

This is **round {round_num}** of the proof search loop.

### Problem Statement

The problem is located at:
```
{problem_file}
```

Read this file carefully.

### Related Work

A literature survey with difficulty evaluation and related results is at:
```
{related_info_dir}/
```

Read `difficulty_evaluation.md` and `related_work.md` for context on what techniques and theorems may be relevant.

### Current Proof Draft

The current proof draft (if any) is at:
```
{proof_file}
```

If this file is empty or contains only a placeholder, this is the first attempt — no prior proof exists.

### Previous Round's Verification Feedback

```
{prev_verification_dir}
```

If the path above is non-empty, read the verification result files in that directory. They contain detailed feedback on what went wrong with the previous proof attempt — which steps failed, which arguments had gaps, and what the verifier flagged.

## Your Task

Based on the round number and available context, brainstorm proof strategies:

**If this is round 1** (no previous proof or verification feedback):
- Suggest 3-5 diverse initial proof strategies
- Consider different proof techniques: direct proof, contradiction, induction, construction, probabilistic method, algebraic approaches, geometric intuition, etc.
- Look at the related work — which known theorems or techniques could be the key ingredient?
- Think about what makes this problem hard and what insight could crack it

**If this is round N > 1** (previous proof and verification feedback exist):
- Read the verification feedback carefully — what specifically went wrong?
- Suggest 2-4 strategies that address the identified failures. 
- Include at least one approach that is **completely different** from what was tried before
- Think about whether the previous approach was fundamentally flawed or just had a fixable gap
- Do NOT repeat approaches that already failed — propose fixes or entirely new angles

## Rules

- **Be creative.** The whole point of having multiple models brainstorm independently is diversity. Don't play it safe.
- **Be concise.** 300-500 words total. Each idea should be 2-5 sentences.
- **Focus on the key insight.** What is the one trick, observation, or connection that makes each approach work?
- **No computation, no execution.** Just ideas.
- **No full proofs.** Strategy sketches only.

## Output

Write your brainstorm to:
```
{output_file}
```

Use this format:

```markdown
# Brainstorm: Proof Strategy Ideas

## Idea 1: [short title]
[2-5 sentences describing the approach, the key insight, and why it might work]

## Idea 2: [short title]
[2-5 sentences describing the approach, the key insight, and why it might work]

## Idea 3: [short title]
...
```

## Error Log

If you encounter any errors, record them in:
```
{error_file}
```

If no errors, write an empty file.
