# Mathematical Literature Survey Task

> **Agentic task.** Read the input files first, then think, plan, and work — use bash, computational tools, or any available resources as needed. Write the output files using tool calls according to the instructions. All input/output file paths and format specifications are at the end of this prompt.

## Overview

You are a research mathematician conducting a thorough literature survey before a proof attempt. Your goal is NOT to prove the problem. Your goal is to **collect every relevant paper, theorem, and result** that could help the proof agent succeed.

Think of yourself as a senior mathematician briefing a colleague who is about to attempt the proof. What published results would they need to know about?

## Your Task

### Step 1: Difficulty Evaluation

**Before doing anything else**, read the problem and evaluate its difficulty. Write your evaluation to `{related_info_dir}/difficulty_evaluation.md`.

Classify the problem into exactly one of these levels:

| Level | Description | Examples |
|-------|-------------|----------|
| **Easy** | Textbook exercise or routine application of a known theorem. A strong undergraduate could solve it in one sitting. | Direct epsilon-delta proof, straightforward induction, applying a named theorem with all hypotheses clearly satisfied. Most importantly, you are very confident that it can be solved without any literature survey. |
| **Medium** | Non-trivial problem requiring clever technique selection or combining multiple ideas. Competition-level or tricky homework. | Competition problems, qualifying exam questions, problems needing a non-obvious substitution or trick. |
| **Hard** | Research-level, requires deep insight, novel combinations, or is adjacent to open problems. Even experts might need substantial time. | Research paper lemmas, problems with subtle hypotheses, problems requiring machinery from multiple subfields. |

Write to `{related_info_dir}/difficulty_evaluation.md`:

```markdown
# Difficulty Evaluation

## Classification: [Easy / Medium / Hard]

## Justification
[2-4 sentences explaining why you chose this level. Reference specific features of the problem.]

## Key Complexity Factors
- [Factor 1]
- [Factor 2]
- ...
```

### Step 2: Related Work Collection

This is the main task. **Be thorough.** Search broadly and deeply for every paper, theorem, and result that could be relevant to the problem. Use web search extensively — ArXiv, Google Scholar, MathSciNet, Math StackExchange, MathOverflow, Wikipedia, textbook references.

The depth of this step depends on your difficulty evaluation:
- **Easy:** Brief survey — list the 1-3 directly applicable theorems with precise statements. Skip the deep paper search.
- **Medium:** Moderate survey — cover key theorems and do a targeted paper search.
- **Hard:** Full survey — exhaustive search. Leave no stone unturned. The proof agent will need every advantage.

Write all findings to `{related_info_dir}/related_work.md` using this format:

```markdown
# Related Work

## Directly Applicable Theorems

For each theorem that could be directly used in the proof:

### [Theorem Name]
- **Statement:** [precise statement with ALL hypotheses]
- **Source:** [paper/book title, authors, year]
- **URL:** [link to the source if available]
- **Relevance:** [exactly how this theorem connects to the problem — which part of the proof could it serve?]
- **Conditions to check:** [which hypotheses might be hard to verify in the context of this problem?]

## Related Papers

For each relevant paper:

### [Paper Title]
- **Authors:** [author names]
- **Year:** [publication year]
- **URL:** [link — ArXiv, DOI, or other]
- **Summary:** [2-5 sentences summarizing the paper's main results and techniques]
- **Relevance:** [why this paper matters for the problem — what techniques or results from it could help?]
- **Key results:** [list specific theorems/lemmas from the paper that are most relevant, with precise statements if possible]

## Useful Lemmas and Inequalities

Standard tools likely to appear in the proof:
- [Lemma/inequality name]: [precise statement]
- ...

## Counterexamples and Pitfalls

- [What hypotheses, if dropped, make the statement false? Give explicit counterexamples if known.]
- [What plausible-sounding stronger versions are false?]
- [What are common mistakes when working with these objects?]
```

### Step 3: Self-Verification of Citations

**After completing the related work collection, you MUST verify every citation you produced.** Hallucinated references are the single biggest failure mode — a fabricated paper or misstated theorem will propagate through the entire pipeline, waste a proof round, and get caught by the verification agent. Catch it here instead.

For every paper and theorem in your `related_work.md`:

1. **Re-check the URL.** Open it again. Does it still point to the paper you claimed? Does the paper actually exist?
2. **Re-check the title and authors.** Do they match what the source actually says? Did you mix up authors from different papers?
3. **Re-check theorem statements.** For every theorem you stated, go back to the source and compare word-by-word. Did you paraphrase in a way that changes the meaning? Did you add or drop a hypothesis?
4. **Remove anything you cannot verify.** If you cannot access a source to confirm its contents, delete that entry from your survey rather than leaving an unverified claim. An honest "I found fewer papers" is better than a list containing hallucinations.

**After verification, add a brief section at the end of `related_work.md`:**

```markdown
## Self-Verification

- Total entries checked: [N]
- Entries removed after verification: [list any removed, or "None"]
- Entries where source was inaccessible (kept with caveat): [list any, or "None"]
- Confidence in remaining entries: [high / medium — explain any concerns]
```

---

## Critical Instructions

- **If any tool or script you run takes longer than 3 minutes, stop it and try a different approach or skip that computation.**
- **Papers are the priority.** Finding the right paper can make a proof trivial. Search aggressively — try multiple query formulations, follow citation chains, check related work sections of papers you find.
- **Be precise.** State theorems with full hypotheses. Vague references ("by a standard result...") are useless to the proof agent.
- **Verify your sources.** Do not hallucinate papers or theorems. If you cite a paper, make sure it actually exists. If you state a theorem, make sure the statement is accurate. The proof agent will use `<cite>` tags that the verifier will check — bad references waste everyone's time.
- **Be honest about uncertainty.** If you're not sure whether a theorem applies, say so and explain what would need to be checked.
- **Focus on actionability.** Everything you write should help the proof agent. If a piece of information doesn't help them prove the problem, leave it out.
- **Do NOT write proof strategies or proof plans.** Your job is purely to survey the literature. The proof search agent will decide how to attack the problem.

---

## HERE ARE THE INPUT FILE PATHS:

### Problem

The problem statement is at:
```
{problem_file}
```

Read it carefully.

## HERE ARE THE OUTPUT FILE PATHS:

Create the directory `{related_info_dir}/` if it does not exist, and write these files:

| File | Contents |
|------|----------|
| `{related_info_dir}/difficulty_evaluation.md` | Difficulty classification (Easy/Medium/Hard) with justification — **always written first** |
| `{related_info_dir}/related_work.md` | Papers, theorems, lemmas, counterexamples — the full literature survey |

## Error Log

If you encounter any errors during this call — tool failures, runtime exceptions, file I/O issues, context window limits, or unexpected behavior — record them in:
```
{error_file}
```
**Always create this file.** If no errors occur, write an empty file. If errors occur, include the error message, what you were doing when it occurred, and any workaround you applied.

## Temporary Files

If you need to create temporary files during your research (e.g., scratch computations), save them in:
```
{output_dir}/tmp/
```
Create this directory if it does not exist.
