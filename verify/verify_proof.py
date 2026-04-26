#!/usr/bin/env python3
"""Standalone proof verifier — difficulty-adaptive verification pipeline.

Takes a problem file and a proof file, classifies difficulty, then routes
through a 1-agent (Easy) or 3-agent (Hard) verification pipeline.

Usage:
    python verify/verify_proof.py problem.txt proof.txt
    python verify/verify_proof.py problem.txt proof.txt -o report.md
    python verify/verify_proof.py problem.txt proof.txt --provider gemini
    python verify/verify_proof.py problem.txt proof.txt --model sonnet
    python verify/verify_proof.py problem.txt proof.txt --config /path/to/config.yaml
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

import yaml


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_CONFIG = os.path.join(REPO_ROOT, "config.yaml")

PROMPT_JUDGE = os.path.join(SCRIPT_DIR, "prompt_judge.md")
PROMPT_STRUCTURAL = os.path.join(SCRIPT_DIR, "prompt_verify_structural.md")
PROMPT_DETAILED = os.path.join(SCRIPT_DIR, "prompt_verify_detailed.md")


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def make_claude_options(claude_cfg: dict) -> dict:
    """Build options dict for the Claude CLI (mirrors pipeline.py)."""
    provider = claude_cfg.get("provider", "subscription")
    env = {}

    if provider == "subscription":
        sub_cfg = claude_cfg.get("subscription", {})
        model = sub_cfg.get("model", "opus")
    elif provider == "api_key":
        api_cfg = claude_cfg.get("api_key", {})
        model = api_cfg.get("model", "claude-opus-4-6")
        key = api_cfg.get("key", "")
        if not key:
            raise ValueError("config.yaml: claude.api_key.key is empty. "
                             "Set your Anthropic API key.")
        env["ANTHROPIC_API_KEY"] = key
    elif provider == "bedrock":
        bedrock_cfg = claude_cfg.get("bedrock", {})
        model = bedrock_cfg.get("model", "us.anthropic.claude-opus-4-6-v1[1m]")
        env["CLAUDE_CODE_USE_BEDROCK"] = "1"
        env["AWS_PROFILE"] = bedrock_cfg.get("aws_profile", "default")
    else:
        raise ValueError(f"Unknown claude.provider '{provider}'.")

    return {
        "cli_path": claude_cfg.get("cli_path", "claude"),
        "model": model,
        "env": env,
    }


def resolve_provider_and_model(config: dict, agent_name: str,
                               cli_provider: str | None,
                               cli_model: str | None) -> tuple[str, str | None]:
    """Determine provider and optional model override for an agent.

    Priority: CLI --provider/--model > standalone_verifier config > default "claude".
    Returns (provider, model_override_or_None).
    """
    sv_cfg = config.get("standalone_verifier", {})
    provider = cli_provider or sv_cfg.get(agent_name, "claude")
    model = cli_model  # None means "use config default"
    return provider, model


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------

def load_prompt(path: str, **kwargs) -> str:
    with open(path) as f:
        template = f.read()
    return template.format(**kwargs)


# ---------------------------------------------------------------------------
# Model invocation (mirrors model_runner.py, synchronous for simplicity)
# ---------------------------------------------------------------------------

def run_claude(prompt: str, claude_opts: dict, model_override: str | None = None) -> str:
    """Invoke Claude CLI and return response text."""
    cli_path = claude_opts.get("cli_path", "claude")
    model = model_override or claude_opts.get("model", "opus")
    extra_env = claude_opts.get("env", {})

    cmd = [
        cli_path,
        "-p",
        "--output-format", "json",
        "--dangerously-skip-permissions",
        "--model", model,
        prompt,
    ]

    _PROVIDER_VARS = ("CLAUDE_CODE_USE_BEDROCK", "ANTHROPIC_API_KEY",
                      "AWS_PROFILE", "ANTHROPIC_MODEL")
    env = {k: v for k, v in os.environ.items() if k not in _PROVIDER_VARS}
    env.update(extra_env)

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, env=env)

    if result.returncode != 0:
        print(f"[Claude] Non-zero exit code: {result.returncode}", file=sys.stderr)
        if result.stderr.strip():
            print(f"[Claude] stderr: {result.stderr.strip()[:500]}", file=sys.stderr)

    try:
        data = json.loads(result.stdout)
        response = data.get("result", "")
    except (json.JSONDecodeError, ValueError):
        response = result.stdout.strip()

    if not response.strip():
        raise RuntimeError(f"Claude returned empty response. "
                           f"Exit code: {result.returncode}")
    return response


def run_codex(prompt: str, codex_cfg: dict, model_override: str | None = None) -> str:
    """Invoke Codex CLI and return response text."""
    cli_path = codex_cfg.get("cli_path", "codex")
    model = model_override or codex_cfg.get("model", "gpt-5.5")
    reasoning = codex_cfg.get("reasoning_effort", "xhigh")

    cmd = [
        cli_path,
        "--search",
        "-m", model,
        "-c", f'model_reasoning_effort="{reasoning}"',
        "exec",
        "--json",
        "--dangerously-bypass-approvals-and-sandbox",
        "-C", os.getcwd(),
        prompt,
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)

    if result.returncode != 0:
        print(f"[Codex] Non-zero exit code: {result.returncode}", file=sys.stderr)
        if result.stderr.strip():
            print(f"[Codex] stderr: {result.stderr.strip()[:500]}", file=sys.stderr)

    response = ""
    try:
        lines = result.stdout.strip().split("\n")
        events = [json.loads(line) for line in lines if line.strip()]
        for event in events:
            if event.get("type") == "item.completed":
                item = event.get("item", {})
                if item.get("type") == "agent_message":
                    response = item.get("text", "")
    except (json.JSONDecodeError, ValueError):
        response = result.stdout.strip()

    if not response.strip():
        raise RuntimeError(f"Codex returned empty response. "
                           f"Exit code: {result.returncode}")
    return response


def run_gemini(prompt: str, gemini_cfg: dict, model_override: str | None = None) -> str:
    """Invoke Gemini CLI and return response text."""
    cli_path = gemini_cfg.get("cli_path", "gemini")
    model = model_override or gemini_cfg.get("model", "gemini-3.1-pro-preview")
    api_key = gemini_cfg.get("api_key", "")
    approval_mode = gemini_cfg.get("approval_mode", "yolo")
    thinking_level = gemini_cfg.get("thinking_level", "")
    thinking_budget = gemini_cfg.get("thinking_budget")

    cmd = [
        cli_path,
        "-m", model,
        "--approval-mode", approval_mode,
        "-o", "json",
        "-p", prompt,
    ]

    env = os.environ.copy()
    if api_key:
        env["GEMINI_API_KEY"] = api_key

    thinking_config = {}
    if thinking_level:
        thinking_config["thinkingLevel"] = thinking_level
    if thinking_budget is not None:
        thinking_config["thinkingBudget"] = thinking_budget

    if thinking_config:
        with tempfile.TemporaryDirectory(prefix="qed-gemini-home-") as gemini_home:
            settings_dir = os.path.join(gemini_home, ".gemini")
            os.makedirs(settings_dir, exist_ok=True)
            settings_path = os.path.join(settings_dir, "settings.json")
            settings = {
                "modelConfigs": {
                    "overrides": [{
                        "match": {"model": model},
                        "modelConfig": {
                            "generateContentConfig": {
                                "thinkingConfig": thinking_config,
                            }
                        },
                    }]
                }
            }
            with open(settings_path, "w") as f:
                json.dump(settings, f)
            env["GEMINI_CLI_HOME"] = gemini_home
            result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True, env=env)
    else:
        result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, env=env)

    if result.returncode != 0:
        print(f"[Gemini] Non-zero exit code: {result.returncode}", file=sys.stderr)
        if result.stderr.strip():
            print(f"[Gemini] stderr: {result.stderr.strip()[:500]}", file=sys.stderr)

    try:
        data = json.loads(result.stdout)
        response = data.get("response", "")
    except (json.JSONDecodeError, ValueError):
        response = result.stdout.strip()

    if not response.strip():
        raise RuntimeError(f"Gemini returned empty response. "
                           f"Exit code: {result.returncode}")
    return response


def run_model(provider: str, prompt: str, config: dict,
              model_override: str | None = None) -> str:
    """Dispatch to the appropriate model runner."""
    if provider == "claude":
        claude_opts = make_claude_options(config.get("claude", {}))
        return run_claude(prompt, claude_opts, model_override)
    elif provider == "codex":
        return run_codex(prompt, config.get("codex", {}), model_override)
    elif provider == "gemini":
        return run_gemini(prompt, config.get("gemini", {}), model_override)
    else:
        raise ValueError(f"Unknown provider: {provider!r}. "
                         f"Expected 'claude', 'codex', or 'gemini'.")


# ---------------------------------------------------------------------------
# Output parsing
# ---------------------------------------------------------------------------

def parse_difficulty(judge_output: str) -> str:
    """Extract 'Easy' or 'Hard' from the judge output."""
    match = re.search(r'\*\*Difficulty:\*\*\s*(Easy|Hard)', judge_output, re.IGNORECASE)
    if match:
        return match.group(1).capitalize()
    # Fallback: look for the word in the first few lines
    for line in judge_output.split("\n")[:20]:
        if "easy" in line.lower() and "difficult" in line.lower():
            continue
        if re.search(r'\bEasy\b', line):
            return "Easy"
        if re.search(r'\bHard\b', line):
            return "Hard"
    # Default to Hard (safer — triggers full pipeline)
    return "Hard"


def parse_structural_verdict(structural_output: str) -> str:
    """Extract PASS/FAIL from structural verification output."""
    match = re.search(r'Overall Structural Verdict:\s*(PASS|FAIL)',
                      structural_output, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    # Fallback: look for any Overall Verdict
    match = re.search(r'Overall\s+Verdict:\s*(PASS|FAIL)',
                      structural_output, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    # Default to FAIL (safer)
    return "FAIL"


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------

def assemble_report(difficulty: str, judge_output: str,
                    structural_output: str | None = None,
                    structural_verdict: str | None = None,
                    detailed_output: str | None = None) -> str:
    """Combine agent outputs into a single final report."""
    sections = []

    if difficulty == "Easy":
        # Judge output already contains the full report
        sections.append(judge_output)
    else:
        # Hard path: combine all available outputs
        sections.append("# Standalone Proof Verification Report")
        sections.append("")
        sections.append("**Difficulty:** Hard")
        sections.append("**Pipeline:** Judge -> Structural -> Detailed")
        sections.append("")

        # Extract judge rationale
        rationale_match = re.search(
            r'\*\*Rationale:\*\*\s*(.+)', judge_output)
        if rationale_match:
            sections.append(f"**Rationale:** {rationale_match.group(1).strip()}")
            sections.append("")

        sections.append("---")
        sections.append("")

        if structural_output:
            sections.append("# Structural Verification")
            sections.append("")
            sections.append(structural_output)
            sections.append("")

        if structural_verdict == "FAIL":
            sections.append("---")
            sections.append("")
            sections.append("*Detailed verification skipped — "
                            "structural verification FAILED.*")
        elif detailed_output:
            sections.append("---")
            sections.append("")
            sections.append("# Detailed Verification")
            sections.append("")
            sections.append(detailed_output)

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Standalone proof verifier — "
                    "difficulty-adaptive verification pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("problem", help="Path to problem statement file")
    parser.add_argument("proof", help="Path to proof file")
    parser.add_argument("-o", "--output", default=None,
                        help="Write report to file (default: stdout)")
    parser.add_argument("--provider", default=None,
                        choices=["claude", "codex", "gemini"],
                        help="Override all agents to one provider")
    parser.add_argument("-m", "--model", default=None,
                        help="Override model name for all agents")
    parser.add_argument("-c", "--config", default=DEFAULT_CONFIG,
                        help="Path to config.yaml "
                             f"(default: {DEFAULT_CONFIG})")

    args = parser.parse_args()

    # --- Load inputs ---
    if not os.path.isfile(args.problem):
        print(f"Error: problem file not found: {args.problem}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.proof):
        print(f"Error: proof file not found: {args.proof}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isfile(args.config):
        print(f"Error: config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    with open(args.problem) as f:
        problem_text = f.read()
    with open(args.proof) as f:
        proof_text = f.read()

    config = load_config(args.config)

    # --- Agent 1: Difficulty Judge ---
    judge_provider, judge_model = resolve_provider_and_model(
        config, "judge", args.provider, args.model)

    print(f"[Agent 1] Difficulty Judge ({judge_provider})", file=sys.stderr)
    judge_prompt = load_prompt(PROMPT_JUDGE,
                               problem=problem_text, proof=proof_text)
    judge_output = run_model(judge_provider, judge_prompt, config, judge_model)

    difficulty = parse_difficulty(judge_output)
    print(f"[Agent 1] Difficulty: {difficulty}", file=sys.stderr)

    # --- Easy path: done ---
    if difficulty == "Easy":
        report = assemble_report("Easy", judge_output)
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"Report written to {args.output}", file=sys.stderr)
        else:
            print(report)
        return

    # --- Hard path: Agent 2 (structural) ---
    struct_provider, struct_model = resolve_provider_and_model(
        config, "structural_verifier", args.provider, args.model)

    print(f"[Agent 2] Structural Verifier ({struct_provider})", file=sys.stderr)
    struct_prompt = load_prompt(PROMPT_STRUCTURAL,
                                problem=problem_text, proof=proof_text)
    structural_output = run_model(struct_provider, struct_prompt,
                                  config, struct_model)

    structural_verdict = parse_structural_verdict(structural_output)
    print(f"[Agent 2] Structural Verdict: {structural_verdict}", file=sys.stderr)

    # --- Gate: if structural FAIL, skip detailed ---
    if structural_verdict == "FAIL":
        report = assemble_report("Hard", judge_output,
                                 structural_output, structural_verdict)
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"Report written to {args.output}", file=sys.stderr)
        else:
            print(report)
        return

    # --- Hard path: Agent 3 (detailed) ---
    detail_provider, detail_model = resolve_provider_and_model(
        config, "detailed_verifier", args.provider, args.model)

    print(f"[Agent 3] Detailed Verifier ({detail_provider})", file=sys.stderr)
    detail_prompt = load_prompt(PROMPT_DETAILED,
                                problem=problem_text, proof=proof_text,
                                structural_report=structural_output)
    detailed_output = run_model(detail_provider, detail_prompt,
                                config, detail_model)

    print(f"[Agent 3] Done", file=sys.stderr)

    # --- Assemble final report ---
    report = assemble_report("Hard", judge_output,
                             structural_output, structural_verdict,
                             detailed_output)

    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
