# Proof Agent

A multi-agent pipeline that takes a mathematical problem statement in LaTeX and produces a rigorous natural-language proof. The pipeline uses Claude as the underlying LLM, orchestrated through the [Agent Framework](https://github.com/microsoft/agent-framework).

## How It Works

The pipeline runs in two stages:

**Stage 0 — Literature Survey.** A survey agent reads the problem and conducts a deep investigation of the mathematical landscape: classifying the problem, identifying applicable theorems, cataloguing proof techniques, and flagging likely dead ends. The results are saved to `related_info/` for the proof agent to reference.

**Stage 1 — Proof Search Loop.** An iterative loop of three agents runs up to `max_proof_iterations` rounds (default 9):

1. **Proof Search Agent** — Reads the problem, the literature survey, and any previous-round feedback. Writes or refines a complete natural-language proof in `proof.md`.
2. **Verification Agent** — Independently reviews the proof for logical validity, completeness, correctness of cited results, and alignment with the problem statement. Writes a structured verdict to a per-round verification result file.
3. **Verdict Agent** — Reads the verification result and returns a single word: `DONE` (proof is correct) or `CONTINUE` (try again).

If the verdict is `DONE`, the pipeline stops. Otherwise the next round begins, with the proof search agent reading the previous round's verification feedback and proof status log to avoid repeating failed approaches.

All agents receive `skill/super_math_skill.md` as a system-level instruction — a 35-principle guide to mathematical proof methodology.

Token usage is tracked across all agent calls and written to `TOKEN_USAGE.md` (human-readable) and `token_usage.json` (machine-readable) after every call.

## File Structure

```
proof_agent/
├── README.md                          # This file
├── config.yaml                        # Pipeline and Claude provider configuration
├── run.sh                             # Entry point shell script
│
├── code/
│   ├── pipeline.py                    # Main orchestrator (all stages, logging, token tracking)
│   └── smoke_test.py                  # Quick validation (prompts, skills, agent connectivity)
│
├── prompts/
│   ├── literature_survey.md           # Stage 0: literature survey agent prompt
│   ├── proof_search.md               # Stage 1, Step 1: proof search agent prompt
│   ├── proof_verify.md               # Stage 1, Step 2: verification agent prompt
│   └── verdict_proof.md              # Stage 1, Step 3: verdict agent prompt
│
└── skill/
    └── super_math_skill.md            # System prompt: 35 principles for proof construction
```

### Prompt Templates

Each prompt file in `prompts/` is a Markdown template with `{placeholder}` variables that are filled at runtime by `pipeline.py`. The placeholders for each prompt:

| Prompt | Placeholders |
|--------|-------------|
| `literature_survey.md` | `problem_file`, `related_info_dir`, `output_dir` |
| `proof_search.md` | `problem_file`, `proof_file`, `output_dir`, `related_info_dir`, `round_num`, `proof_status_file`, `previous_round_instructions` |
| `proof_verify.md` | `problem_file`, `proof_file`, `output_file`, `output_dir` |
| `verdict_proof.md` | `verification_result_file` |

## Output Structure

Given an output directory `<output>/`, a complete run produces:

```
<output>/
├── problem.tex                        # Copy of the input problem
├── proof.md                           # The final proof (written/refined by proof search agent)
├── TOKEN_USAGE.md                     # Human-readable token usage summary table
├── token_usage.json                   # Machine-readable token usage data
│
├── related_info/                      # Stage 0: literature survey output
│   ├── problem_analysis.md            #   Problem classification, key objects, edge cases
│   ├── related_theorems.md            #   Applicable theorems, lemmas, counterexamples
│   └── proof_strategies.md            #   Candidate techniques, analogous proofs, dead ends
│
├── literature_survey_log/             # Stage 0: agent logs
│   ├── AUTO_RUN_STATUS.md             #   Current status snapshot
│   ├── AUTO_RUN_STATUS.md.history     #   Timestamped event history
│   └── AUTO_RUN_LOG.txt               #   Full text log (streaming agent output)
│
├── verification/                      # Stage 1: proof loop logs
│   ├── AUTO_RUN_STATUS.md             #   Current status snapshot
│   ├── AUTO_RUN_STATUS.md.history     #   Timestamped event history
│   ├── AUTO_RUN_LOG.txt               #   Full text log
│   ├── round_1/
│   │   ├── proof_status.md            #   Proof search agent's log of what it tried
│   │   └── verification_result.md     #   Verification agent's structured verdict
│   ├── round_2/
│   │   ├── proof_status.md
│   │   └── verification_result.md
│   └── ...                            #   One directory per round
│
└── tmp/                               # Temporary files created by agents (scratch work)
```

### Log Files

Each stage writes three log files:

| File | Purpose |
|------|---------|
| `AUTO_RUN_STATUS.md` | Current status table (iteration, step, state, timestamps, PID). Overwritten each update. |
| `AUTO_RUN_STATUS.md.history` | Append-only timestamped event log (e.g., "Iteration 2: Proof search started"). |
| `AUTO_RUN_LOG.txt` | Full streaming output from all agent calls — tool invocations, text output, token stats. |

### Token Usage

`TOKEN_USAGE.md` is updated after every agent call and contains:

- **Summary table**: total input/output tokens, total elapsed time, estimated cost, number of agent calls.
- **Per-call breakdown**: each agent call with its token counts, elapsed time, cumulative totals, and estimated cost.

Pricing is looked up from `MODEL_PRICING` in `pipeline.py`. Subscription models (`opus`, `sonnet`, `haiku`) show `subscription` instead of a dollar amount. API/Bedrock models show USD estimates.

`token_usage.json` contains the same data in JSON format for programmatic consumption.

## Dependencies

### System Requirements

| Dependency | Purpose | Install |
|------------|---------|---------|
| Python 3.11+ | Pipeline runtime | `conda create -n agent python=3.11` |
| [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) | Agent execution backend | `npm install -g @anthropic-ai/claude-code` |

### Python Packages

| Package | Purpose | Install |
|---------|---------|---------|
| `pyyaml` | Config file parsing | `pip install pyyaml` |
| `agent_framework` | ClaudeAgent orchestration | See below |

The `agent_framework` package must be importable as `from agent_framework.anthropic import ClaudeAgent`. This is the [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) with the Anthropic/Claude integration. Install per its documentation.

### Claude Provider Setup

The pipeline supports three Claude providers. Configure exactly one in `config.yaml`:

#### Option 1: Claude Subscription (Pro/Max)

If you purchased a Claude plan through the [Anthropic website](https://claude.ai) (i.e., you log in at claude.ai and pay for Claude Pro or Claude Max), you are a **subscription** user — use this option. No API key is needed; the Claude CLI authenticates through your browser session. Claude Max is required for `opus`; Claude Pro supports `sonnet`.

```yaml
claude:
  provider: "subscription"
  subscription:
    model: "opus"    # or "sonnet", "haiku"
```

#### Option 2: AWS Bedrock

Requires AWS credentials configured (e.g., via `aws configure`).

```yaml
claude:
  provider: "bedrock"
  bedrock:
    model: "us.anthropic.claude-opus-4-6-v1[1m]"
    aws_profile: "default"
```

#### Option 3: Anthropic API Key

Requires an Anthropic API key.

```yaml
claude:
  provider: "api_key"
  api_key:
    model: "claude-opus-4-6-20250609"
    key: "sk-ant-..."
```

## Installation

```bash
# 1. Clone or copy the proof_agent directory

# 2. Create and activate conda environment
conda create -n agent python=3.11 -y
conda activate agent

# 3. Install Python dependencies
pip install pyyaml

# 4. Install agent_framework (adjust path as needed)
pip install -e /path/to/agent-framework

# 5. Install Claude CLI
npm install -g @anthropic-ai/claude-code

# 6. Configure your Claude provider in config.yaml
#    Edit config.yaml and set `provider` to one of:
#    "subscription", "bedrock", or "api_key"
#    Then fill in the corresponding section.

# 7. Run the smoke test to verify everything works
conda activate agent
python code/smoke_test.py
```

## Usage

### Quick Start

```bash
# Using the shell script (uses conda env "agent")
bash run.sh /path/to/problem.tex

# With a custom output directory
bash run.sh /path/to/problem.tex /path/to/output

# Directly via Python
python code/pipeline.py \
    --input /path/to/problem.tex \
    --output /path/to/output \
    --config config.yaml
```

### Input Format

The input is a single `problem.tex` file containing a mathematical problem statement in LaTeX. For example:

```latex
\begin{problem}
Let $f: [0,1] \to \mathbb{R}$ be a continuous function satisfying
$f(0) = f(1) = 0$ and $f(x) > 0$ for all $x \in (0,1)$.
Prove that there exists $c \in (0,1)$ such that
\[
  \frac{f'(c)}{f(c)} = \frac{1}{1-c}.
\]
\end{problem}
```

The file can use any LaTeX formatting — theorem environments, custom macros, etc. The agents read the raw LaTeX source directly.

### Smoke Test

The smoke test validates the setup without making expensive agent calls (except one short connectivity check):

```bash
python code/smoke_test.py
```

It checks:
1. All prompt files exist
2. All skill files exist
3. Prompt templates render without unresolved placeholders
4. Skill file loads correctly
5. ClaudeAgent can connect and respond
6. Config file has required fields

### Monitoring a Run

While the pipeline is running, you can check progress:

```bash
# Current status
cat <output>/verification/AUTO_RUN_STATUS.md

# Event history
cat <output>/verification/AUTO_RUN_STATUS.md.history

# Token usage so far
cat <output>/TOKEN_USAGE.md

# Full streaming log
tail -f <output>/verification/AUTO_RUN_LOG.txt

# Literature survey log
cat <output>/literature_survey_log/AUTO_RUN_LOG.txt
```

## Configuration Reference

`config.yaml` fields:

```yaml
pipeline:
  max_proof_iterations: 9    # Maximum rounds of proof search/verify/verdict
                              # before the pipeline stops. Default: 9.

claude:
  cli_path: "claude"          # Path to the Claude CLI binary.
  permission_mode: "bypassPermissions"  # Permission mode for Claude CLI.

  provider: "subscription"    # One of: "subscription", "bedrock", "api_key"

  subscription:
    model: "opus"             # Shorthand: "opus", "sonnet", or "haiku"

  bedrock:
    model: "us.anthropic.claude-opus-4-6-v1[1m]"
    aws_profile: "default"    # AWS profile name for credentials

  api_key:
    model: "claude-opus-4-6-20250609"
    key: ""                   # Your Anthropic API key
```

## Architecture

```
                          problem.tex
                              |
                              v
                 +------------------------+
                 |  Literature Survey      |   Stage 0
                 |  Agent                  |
                 +------------------------+
                              |
                    related_info/ (3 files)
                              |
          +-------------------+-------------------+
          |                                       |
          v                                       |
+-------------------+                             |
| Proof Search      |  <-- reads related_info/    |
| Agent             |  <-- reads prev round       |
+-------------------+  --> writes proof.md        |
          |                                       |
          v                                       |
+-------------------+                             |
| Verification      |                             |
| Agent             |                             |
+-------------------+  --> verification_result.md |
          |                                       |
          v                                       |
+-------------------+                             |
| Verdict Agent     |                             |
+-------------------+                             |
     |         |                                  |
   DONE    CONTINUE ------> next round -----------+
     |
     v
  proof.md (final)
```
