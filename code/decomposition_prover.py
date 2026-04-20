#!/usr/bin/env python3
"""Decomposition-based prover for the QED pipeline.

This module implements a sophisticated proof workflow that:
1. Decomposes a problem into intermediate steps
2. Proves each step individually (key steps first)
3. Verifies each step proof
4. Uses a regulator to decide when to revise or rewrite the decomposition
5. Aggregates all step proofs into a final proof.md

This is an optional alternative to the "simple" prover mode in pipeline.py.
"""

import asyncio
import json
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any

from model_runner import run_model, run_claude_agent, ModelRunnerError


# ---------------------------------------------------------------------------
# Configuration defaults
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "max_prover_rounds": 5,      # rounds per step before asking regulator
    "max_revisions": 3,          # local revisions per step
    "max_decompositions": 3,     # complete rewrites allowed
}

DEFAULT_MODELS = {
    "decomposer": "claude",
    "step_prover": "claude",
    "step_verifier": "claude",
    "regulator": "claude",
    "proof_aggregator": "claude",
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_prompt(prompts_dir: str, name: str, **kwargs) -> str:
    """Load a prompt template and fill placeholders."""
    path = os.path.join(prompts_dir, name)
    with open(path) as f:
        template = f.read()
    # Use safe formatting that doesn't fail on missing keys
    for key, value in kwargs.items():
        template = template.replace("{" + key + "}", str(value))
    return template


def read_file(path: str) -> str:
    """Read file contents, return empty string if not found."""
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return ""


def write_file(path: str, content: str) -> None:
    """Write content to file, creating directories as needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def parse_decomposition(yaml_content: str) -> dict:
    """Parse decomposition YAML from agent response.

    Extracts the YAML block from markdown code fences if present.
    """
    # Try to extract YAML from code block
    if "```yaml" in yaml_content:
        start = yaml_content.find("```yaml") + 7
        end = yaml_content.find("```", start)
        yaml_content = yaml_content[start:end].strip()
    elif "```" in yaml_content:
        start = yaml_content.find("```") + 3
        end = yaml_content.find("```", start)
        yaml_content = yaml_content[start:end].strip()

    return yaml.safe_load(yaml_content)


def parse_verdict(response: str) -> str:
    """Extract PASS or FAIL from verifier response."""
    response_upper = response.upper()
    # Look for verdict in markdown header
    if "### VERDICT: PASS" in response_upper or "**VERDICT**: PASS" in response_upper:
        return "PASS"
    if "### VERDICT: FAIL" in response_upper or "**VERDICT**: FAIL" in response_upper:
        return "FAIL"
    # Look for standalone PASS/FAIL
    if "VERDICT: PASS" in response_upper:
        return "PASS"
    if "VERDICT: FAIL" in response_upper:
        return "FAIL"
    # Default to FAIL if unclear
    return "FAIL"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

class DecompositionLogger:
    """Logger for decomposition prover that writes structured logs."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.decomp_dir = os.path.join(output_dir, "decomposition")
        os.makedirs(self.decomp_dir, exist_ok=True)

        # Main status and timeline log (top-level, not per-attempt)
        self.status_file = os.path.join(self.decomp_dir, "STATUS.md")
        self.main_log_file = os.path.join(self.decomp_dir, "log.txt")

        # Initialize status
        self._write_status({
            "state": "STARTING",
            "attempt": 1,
            "revision": 1,
            "current_step": None,
            "current_round": 0,
            "steps_proved": [],
            "steps_failed": [],
            "last_update": datetime.now().isoformat(),
        })

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write_status(self, status: dict) -> None:
        """Write current status to STATUS.md."""
        content = f"""# Decomposition Prover Status

**Last Updated:** {status.get('last_update', datetime.now().isoformat())}

## Current State

| Field | Value |
|-------|-------|
| State | {status.get('state', 'UNKNOWN')} |
| Decomposition Attempt | {status.get('attempt', 1)} |
| Revision | {status.get('revision', 0)} |
| Current Step | {status.get('current_step', 'None')} |
| Current Round | {status.get('current_round', 0)} |

## Progress

**Steps Proved:** {', '.join(status.get('steps_proved', [])) or 'None'}

**Steps Failed:** {', '.join(status.get('steps_failed', [])) or 'None'}

## Recent Activity

{status.get('recent_activity', '')}
"""
        write_file(self.status_file, content)

    def update_status(
        self,
        state: str = None,
        attempt: int = None,
        revision: int = None,
        current_step: str = None,
        current_round: int = None,
        steps_proved: list = None,
        steps_failed: list = None,
        recent_activity: str = None,
    ) -> None:
        """Update the status file with current state."""
        # Read existing status
        existing = {}
        if os.path.exists(self.status_file):
            # Parse existing values (simple approach)
            existing = {
                "state": "UNKNOWN",
                "attempt": 1,
                "revision": 1,
                "current_step": None,
                "current_round": 0,
                "steps_proved": [],
                "steps_failed": [],
                "recent_activity": "",
            }

        # Update with new values
        if state is not None:
            existing["state"] = state
        if attempt is not None:
            existing["attempt"] = attempt
        if revision is not None:
            existing["revision"] = revision
        if current_step is not None:
            existing["current_step"] = current_step
        if current_round is not None:
            existing["current_round"] = current_round
        if steps_proved is not None:
            existing["steps_proved"] = steps_proved
        if steps_failed is not None:
            existing["steps_failed"] = steps_failed
        if recent_activity is not None:
            existing["recent_activity"] = recent_activity

        existing["last_update"] = datetime.now().isoformat()
        self._write_status(existing)

    def log(self, message: str, agent: str = None) -> None:
        """Log a message to the main timeline log."""
        timestamp = self._timestamp()
        log_line = f"[{timestamp}] {message}\n"

        # Write to main log
        with open(self.main_log_file, "a") as f:
            f.write(log_line)

        # Print to console
        print(f"[DecompProver] {message}")

    def log_agent_call(
        self,
        agent: str,
        action: str,
        model: str,
        details: dict = None,
    ) -> None:
        """Log an agent call with details."""
        details_str = ""
        if details:
            details_str = " | " + " | ".join(f"{k}={v}" for k, v in details.items())
        message = f"[{agent.upper()}] {action} (model={model}){details_str}"
        self.log(message)

    def log_agent_result(
        self,
        agent: str,
        result: str,
        elapsed: float = None,
        tokens_in: int = None,
        tokens_out: int = None,
    ) -> None:
        """Log an agent result."""
        parts = [f"[{agent.upper()}] Result: {result}"]
        if elapsed is not None:
            parts.append(f"elapsed={elapsed:.1f}s")
        if tokens_in is not None:
            parts.append(f"tokens_in={tokens_in}")
        if tokens_out is not None:
            parts.append(f"tokens_out={tokens_out}")
        self.log(" | ".join(parts))

    def save_agent_output(
        self,
        output: str,
        path: str,
    ) -> None:
        """Save raw LLM response to a structured path."""
        write_file(path, output)


def parse_regulator_decision(response: str) -> str:
    """Extract decision from regulator response."""
    response_upper = response.upper()
    for decision in ["REVISE", "REWRITE"]:
        if f"DECISION: {decision}" in response_upper:
            return decision
        if f"## DECISION: {decision}" in response_upper:
            return decision
    # Default to REVISE if unclear (prefer local fix over full rewrite)
    return "REVISE"


# ---------------------------------------------------------------------------
# Decomposition state management
# ---------------------------------------------------------------------------

class DecompositionState:
    """Tracks the state of a decomposition-based proof attempt."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.decomp_dir = os.path.join(output_dir, "decomposition")
        self.attempt = 1
        self.revision = 1
        self.decomposition = None
        self.step_proofs = {}  # step_id -> proof content
        self.step_results = {}  # step_id -> "proved" | "failed"
        self.attempt_history = []  # list of failure info for rewrites

    def get_attempt_dir(self) -> str:
        """Get directory for current attempt."""
        return os.path.join(self.decomp_dir, f"attempt_{self.attempt}")

    def get_revision_dir(self) -> str:
        """Get directory for current revision."""
        return os.path.join(self.get_attempt_dir(), f"revision_{self.revision}")

    def save_decomposition(self, decomposition: dict) -> None:
        """Save decomposition to file."""
        self.decomposition = decomposition
        path = os.path.join(self.get_attempt_dir(), "decomposition.yaml")
        write_file(path, yaml.dump(decomposition, default_flow_style=False))

    def load_decomposition(self) -> dict | None:
        """Load decomposition from file."""
        path = os.path.join(self.get_attempt_dir(), "decomposition.yaml")
        content = read_file(path)
        if content:
            self.decomposition = yaml.safe_load(content)
            return self.decomposition
        return None

    def get_step_dir(self, step_id: str) -> str:
        """Get directory for a step under current revision."""
        return os.path.join(self.get_revision_dir(), f"step_{step_id}")

    def get_step_round_dir(self, step_id: str, round_number: int) -> str:
        """Get directory for a specific round of a step."""
        return os.path.join(self.get_step_dir(step_id), f"round_{round_number}")

    def save_step_proof(self, step_id: str, proof: str, round_number: int = None) -> None:
        """Save a step proof. Writes to step/round_N/proof.md and step/proof.md (latest)."""
        self.step_proofs[step_id] = proof
        step_dir = self.get_step_dir(step_id)
        os.makedirs(step_dir, exist_ok=True)
        # Always write the "latest" file (used for resume and verification)
        latest_path = os.path.join(step_dir, "proof.md")
        write_file(latest_path, proof)
        # Also write per-round file
        if round_number is not None:
            round_dir = self.get_step_round_dir(step_id, round_number)
            os.makedirs(round_dir, exist_ok=True)
            write_file(os.path.join(round_dir, "proof.md"), proof)

    def save_step_verification(self, step_id: str, verification: str, round_number: int = None) -> None:
        """Save a step verification result. Writes to step/round_N/verification.md and step/verification.md (latest)."""
        step_dir = self.get_step_dir(step_id)
        os.makedirs(step_dir, exist_ok=True)
        # Always write the "latest" file (used for resume)
        latest_path = os.path.join(step_dir, "verification.md")
        write_file(latest_path, verification)
        # Also write per-round file
        if round_number is not None:
            round_dir = self.get_step_round_dir(step_id, round_number)
            os.makedirs(round_dir, exist_ok=True)
            write_file(os.path.join(round_dir, "verification.md"), verification)

    def save_regulator_decision(self, step_id: str, decision: str, response: str) -> None:
        """Save regulator decision."""
        path = os.path.join(self.get_revision_dir(), "regulator_decisions.md")
        existing = read_file(path)
        entry = f"\n## Step {step_id}\n\n{response}\n\n---\n"
        write_file(path, existing + entry)

    def mark_step_proved(self, step_id: str) -> None:
        """Mark a step as proved."""
        self.step_results[step_id] = "proved"
        if self.decomposition:
            for step in self.decomposition.get("steps", []):
                if step["id"] == step_id:
                    step["status"] = "proved"
                    break
            self.save_decomposition(self.decomposition)

    def mark_step_failed(self, step_id: str) -> None:
        """Mark a step as failed."""
        self.step_results[step_id] = "failed"

    def new_revision(self) -> None:
        """Start a new revision - clear all step results and start fresh."""
        self.revision += 1
        self.step_proofs = {}
        self.step_results = {}
        os.makedirs(self.get_revision_dir(), exist_ok=True)

    def new_attempt(self) -> None:
        """Start a completely new decomposition attempt."""
        # Save failure history
        if self.decomposition:
            self.attempt_history.append({
                "attempt": self.attempt,
                "revision": self.revision,
                "decomposition": self.decomposition,
                "step_results": self.step_results.copy(),
            })
        # Reset for new attempt
        self.attempt += 1
        self.revision = 1
        self.decomposition = None
        self.step_proofs = {}
        self.step_results = {}
        os.makedirs(self.get_attempt_dir(), exist_ok=True)
        os.makedirs(self.get_revision_dir(), exist_ok=True)

    def get_failure_history(self) -> str:
        """Get formatted failure history for rewrite mode."""
        if not self.attempt_history:
            return "No previous attempts."

        lines = ["# Previous Attempt Failures\n"]
        for hist in self.attempt_history:
            lines.append(f"## Attempt {hist['attempt']}\n")
            lines.append(f"Revisions tried: {hist['revision']}\n")
            lines.append(f"Step results:\n")
            for step_id, result in hist["step_results"].items():
                lines.append(f"- {step_id}: {result}\n")
            lines.append("\n")
        return "".join(lines)


# ---------------------------------------------------------------------------
# Resume detection
# ---------------------------------------------------------------------------

def _file_nonempty(path: str) -> bool:
    """Check if a file exists and is non-empty."""
    return os.path.isfile(path) and os.path.getsize(path) > 0


def detect_decomposition_resume(output_dir: str) -> dict:
    """Scan the output directory for decomposition progress from a previous run.

    Returns a dict with resume information:
        {
            "has_progress": bool,       # True if any prior progress found
            "attempt": int,             # Attempt number to resume at
            "revision": int,            # Revision number to resume at
            "decomposition": dict|None, # Loaded decomposition (if exists)
            "proved_steps": list[str],  # Steps already proved in current revision
            "resume_point": str,        # Where to resume:
                                        #   "fresh" - no progress
                                        #   "decompose" - need decomposition
                                        #   "prove_steps" - have decomposition, resume proving
                                        #   "aggregate" - all steps proved, need aggregation
                                        #   "verify_structural" - aggregated, need structural verification
                                        #   "verify_detailed" - structural done, need detailed
                                        #   "done" - proof verified successfully
            "attempt_history": list,    # Previous attempt failures for REWRITE context
        }
    """
    decomp_dir = os.path.join(output_dir, "decomposition")
    result = {
        "has_progress": False,
        "attempt": 1,
        "revision": 1,
        "decomposition": None,
        "proved_steps": [],
        "resume_point": "fresh",
        "attempt_history": [],
    }

    if not os.path.isdir(decomp_dir):
        return result

    # Find the highest attempt directory
    attempt_nums = []
    for name in os.listdir(decomp_dir):
        if name.startswith("attempt_"):
            try:
                attempt_nums.append(int(name.split("_", 1)[1]))
            except ValueError:
                continue

    if not attempt_nums:
        return result

    attempt_nums.sort()

    # Build attempt history from completed (failed) attempts
    attempt_history = []
    latest_attempt = attempt_nums[-1]

    for att_num in attempt_nums[:-1]:
        # Previous attempts are considered failed
        att_dir = os.path.join(decomp_dir, f"attempt_{att_num}")
        decomp_path = os.path.join(att_dir, "decomposition.yaml")
        decomp_content = read_file(decomp_path)
        if decomp_content:
            decomp = yaml.safe_load(decomp_content)
            # Find the last revision in this attempt
            rev_nums = []
            for name in os.listdir(att_dir):
                if name.startswith("revision_"):
                    try:
                        rev_nums.append(int(name.split("_", 1)[1]))
                    except ValueError:
                        continue
            last_rev = max(rev_nums) if rev_nums else 1
            attempt_history.append({
                "attempt": att_num,
                "revision": last_rev,
                "decomposition": decomp,
                "step_results": {},  # Could scan but not critical for resume
            })

    result["attempt_history"] = attempt_history
    result["attempt"] = latest_attempt

    # Analyze the latest attempt
    att_dir = os.path.join(decomp_dir, f"attempt_{latest_attempt}")

    # Check if decomposition exists
    decomp_path = os.path.join(att_dir, "decomposition.yaml")
    decomp_content = read_file(decomp_path)
    if not decomp_content:
        result["has_progress"] = len(attempt_history) > 0
        result["resume_point"] = "decompose"
        return result

    decomposition = yaml.safe_load(decomp_content)
    result["decomposition"] = decomposition
    result["has_progress"] = True

    # Find the latest revision
    rev_nums = []
    for name in os.listdir(att_dir):
        if name.startswith("revision_"):
            try:
                rev_nums.append(int(name.split("_", 1)[1]))
            except ValueError:
                continue

    if not rev_nums:
        result["resume_point"] = "prove_steps"
        return result

    latest_revision = max(rev_nums)
    result["revision"] = latest_revision
    rev_dir = os.path.join(att_dir, f"revision_{latest_revision}")

    # Check proof verification status (post-aggregation)
    verify_dir = os.path.join(rev_dir, "proof_verification")
    if os.path.isdir(verify_dir):
        detailed_path = os.path.join(verify_dir, "detailed_verification.md")
        structural_path = os.path.join(verify_dir, "structural_verification.md")

        if _file_nonempty(detailed_path):
            # Check if it passed
            content = read_file(detailed_path)
            if "OVERALL VERDICT: PASS" in content.upper():
                result["resume_point"] = "done"
                return result
            # Detailed verification exists but FAILED — regulator should have been called
            # Check if combined_feedback exists (regulator was consulted)
            combined_path = os.path.join(verify_dir, "combined_feedback.md")
            if _file_nonempty(combined_path):
                # Regulator was consulted, but we got interrupted after.
                # The safest resume is to re-run from prove_steps with a new revision.
                # But we don't know the regulator decision. Start fresh from prove_steps
                # on the current decomposition (it may have been revised).
                result["resume_point"] = "prove_steps"
                result["proved_steps"] = []
                return result
            # No combined feedback — interrupted during/after verification before regulator
            # Re-run from verify_detailed (structural already done)
            result["resume_point"] = "verify_detailed"
            return result

        if _file_nonempty(structural_path):
            # Structural done, check if it passed
            content = read_file(structural_path)
            if "OVERALL VERDICT: PASS" in content.upper():
                # Structural passed, need detailed
                result["resume_point"] = "verify_detailed"
            else:
                # Structural failed — same situation as detailed fail without regulator
                result["resume_point"] = "prove_steps"
                result["proved_steps"] = []
            return result

    # Check if proof.md exists (aggregation done but verification not started)
    proof_file = os.path.join(output_dir, "proof.md")
    if _file_nonempty(proof_file):
        # Check if all steps in decomposition are proved by scanning step files
        steps = decomposition.get("steps", [])
        step_ids = [s["id"] for s in steps if s["id"] != "GOAL"]
        proved_steps = []
        for step_id in step_ids:
            step_dir = os.path.join(rev_dir, f"step_{step_id}")
            proof_path = os.path.join(step_dir, "proof.md")
            verify_path = os.path.join(step_dir, "verification.md")
            if _file_nonempty(proof_path) and _file_nonempty(verify_path):
                # Check if verification passed
                v_content = read_file(verify_path)
                if parse_verdict(v_content) == "PASS":
                    proved_steps.append(step_id)

        if len(proved_steps) == len(step_ids):
            # All steps proved — proof.md exists, need verification
            result["proved_steps"] = proved_steps
            result["resume_point"] = "verify_structural"
            return result

    # Check step-level progress
    steps = decomposition.get("steps", [])
    step_ids = [s["id"] for s in steps if s["id"] != "GOAL"]
    proved_steps = []
    for step_id in step_ids:
        step_dir = os.path.join(rev_dir, f"step_{step_id}")
        proof_path = os.path.join(step_dir, "proof.md")
        verify_path = os.path.join(step_dir, "verification.md")
        if _file_nonempty(proof_path) and _file_nonempty(verify_path):
            v_content = read_file(verify_path)
            if parse_verdict(v_content) == "PASS":
                proved_steps.append(step_id)

    result["proved_steps"] = proved_steps

    if len(proved_steps) == len(step_ids):
        # All steps proved but no proof.md — need aggregation
        result["resume_point"] = "aggregate"
    else:
        result["resume_point"] = "prove_steps"

    return result


# ---------------------------------------------------------------------------
# Helper to get model for an agent
# ---------------------------------------------------------------------------

def get_agent_model(config: dict, agent_name: str) -> str:
    """Get the model provider for a specific agent from config."""
    decomp_config = config.get("decomposition", {})
    models = decomp_config.get("models", DEFAULT_MODELS)
    return models.get(agent_name, DEFAULT_MODELS.get(agent_name, "claude"))


def get_claude_opts_for_model(config: dict, model_provider: str) -> dict:
    """Get claude_opts dict for the specified model provider."""
    if model_provider == "claude":
        claude_cfg = config.get("claude", {})
        provider = claude_cfg.get("provider", "subscription")
        if provider == "subscription":
            return {
                "cli_path": claude_cfg.get("cli_path", "claude"),
                "model": claude_cfg.get("subscription", {}).get("model", "opus"),
                "env": {},
            }
        elif provider == "bedrock":
            bedrock = claude_cfg.get("bedrock", {})
            return {
                "cli_path": claude_cfg.get("cli_path", "claude"),
                "model": bedrock.get("model", "us.anthropic.claude-sonnet-4-20250514"),
                "env": {
                    "CLAUDE_CODE_USE_BEDROCK": "1",
                    "AWS_PROFILE": bedrock.get("aws_profile", "default"),
                },
            }
        elif provider == "api_key":
            api_cfg = claude_cfg.get("api_key", {})
            return {
                "cli_path": claude_cfg.get("cli_path", "claude"),
                "model": api_cfg.get("model", "claude-sonnet-4-20250514"),
                "env": {
                    "ANTHROPIC_API_KEY": api_cfg.get("key", ""),
                },
            }
    # For codex/gemini, return empty dict - run_model will use config directly
    return {}


# ---------------------------------------------------------------------------
# Agent runners
# ---------------------------------------------------------------------------

async def run_decomposer(
    state: DecompositionState,
    problem_file: str,
    related_work_file: str,
    difficulty_file: str,
    prompts_dir: str,
    config: dict,
    claude_opts: dict,
    mode: str = "CREATE",
    failed_step_id: str = "",
    failure_feedback: str = "",
    prover_attempts_file: str = "",
    decomp_logger: DecompositionLogger = None,
    tracker=None,
) -> dict:
    """Run the decomposer agent to create/revise/rewrite a decomposition."""

    model_provider = get_agent_model(config, "decomposer")

    # Build revision context based on mode
    revision_context = ""
    if mode == "REVISE":
        # Use provided prover_attempts_file if available (caller captures path
        # before state.new_revision() changes the revision number)
        attempts_path = prover_attempts_file or (
            os.path.join(state.get_revision_dir(), "proof.md") if failed_step_id == "AGGREGATED_PROOF"
            else os.path.join(state.get_step_dir(failed_step_id), "proof.md") if failed_step_id else ""
        )
        revision_context = f"""
### Current Decomposition (to revise)
```
{state.get_attempt_dir()}/decomposition.yaml
```

### Failed Step
ID: {failed_step_id}

### Failure Feedback
{failure_feedback}

### Prover Attempts
```
{attempts_path}
```
"""
    elif mode == "REWRITE":
        revision_context = f"""
### Failure History
{state.get_failure_history()}

### Previous Decomposition Attempts
See {state.decomp_dir}/attempt_*/decomposition.yaml
"""

    # Resolve human help file (global prover guidance from user)
    project_root = os.path.dirname(prompts_dir)
    human_help_file = os.path.join(project_root, "human_help", "additional_prove_human_help_global.md")

    prompt = load_prompt(
        prompts_dir,
        "decomposition-prover/decomposition.md",
        mode=mode,
        problem_file=problem_file,
        related_work_file=related_work_file,
        difficulty_file=difficulty_file,
        revision_context=revision_context,
        problem_id=os.path.basename(problem_file),
        attempt_number=state.attempt,
        revision_number=state.revision,
        timestamp=datetime.now().isoformat(),
        output_file=os.path.join(state.get_attempt_dir(), "decomposition.yaml"),
        current_decomposition_file=os.path.join(state.get_attempt_dir(), "decomposition.yaml"),
        failed_step_id=failed_step_id,
        failure_feedback=failure_feedback,
        prover_attempts_file=prover_attempts_file or (os.path.join(state.get_revision_dir(), "proof.md") if failed_step_id == "AGGREGATED_PROOF" else (os.path.join(state.get_step_dir(failed_step_id), "proof.md") if failed_step_id else "")),
        failure_history_file=os.path.join(state.decomp_dir, "failure_history.md"),
        human_help_file=human_help_file,
    )

    if decomp_logger:
        decomp_logger.log_agent_call(
            "decomposer", f"{mode} mode",
            model_provider,
            {"attempt": state.attempt, "revision": state.revision}
        )
        decomp_logger.update_status(
            state="DECOMPOSING",
            attempt=state.attempt,
            revision=state.revision,
            recent_activity=f"Running decomposer in {mode} mode"
        )

    # Run the model
    response = await run_model(
        provider=model_provider,
        prompt=prompt,
        working_dir=state.output_dir,
        config=config,
        claude_opts=get_claude_opts_for_model(config, model_provider) if model_provider == "claude" else claude_opts,
        tracker=tracker,
        call_name=f"decomposer_{mode.lower()}",
    )

    # Save LLM response into structured path
    if decomp_logger:
        resp_path = os.path.join(state.get_attempt_dir(), "decomposer_response.md")
        decomp_logger.save_agent_output(response, resp_path)
        decomp_logger.log_agent_result("decomposer", f"{mode} completed")

    # Read the file the agent wrote via tool call
    decomp_file_path = os.path.join(state.get_attempt_dir(), "decomposition.yaml")
    decomposition = state.load_decomposition()
    if decomposition:
        return decomposition

    # Agent failed to write the file — fall back to parsing response text
    try:
        decomposition = parse_decomposition(response)
    except (yaml.YAMLError, AttributeError) as e:
        raise RuntimeError(
            f"Decomposer did not produce valid YAML and did not write to {decomp_file_path}.\n"
            f"Parse error: {e}\nResponse preview: {response[:500]}"
        ) from e

    state.save_decomposition(decomposition)
    return decomposition


async def run_step_prover(
    state: DecompositionState,
    step: dict,
    inputs: list[dict],
    problem_file: str,
    related_work_file: str,
    prompts_dir: str,
    config: dict,
    claude_opts: dict,
    round_number: int = 1,
    previous_attempts: str = "",
    proved_proofs: dict = None,
    decomp_logger: DecompositionLogger = None,
    tracker=None,
) -> str:
    """Run the step prover agent to prove a single step."""

    model_provider = get_agent_model(config, "step_prover")

    # Build step file content
    step_content = yaml.dump(step, default_flow_style=False)

    # Build inputs file content
    inputs_content = "# Input Statements\n\n"
    for inp in inputs:
        inputs_content += f"## {inp['id']}\n\n{inp.get('statement', '')}\n\n"

    # Build context of previously proved step proofs
    # This gives the step prover visibility into HOW earlier steps were proved,
    # not just WHAT they proved — critical for method compatibility.
    proved_context = ""
    if proved_proofs:
        proved_context = "\n\n---\n\n# Proofs of Previously Proved Steps\n\n"
        proved_context += "> These are the full proofs of steps that have already been verified. "
        proved_context += "You may rely on the techniques, constructions, and intermediate results established here.\n\n"
        for pid, pproof in proved_proofs.items():
            proved_context += f"## Proof of {pid}\n\n{pproof}\n\n---\n\n"

    # Build previous attempts context
    previous_attempts_context = ""
    if previous_attempts:
        previous_attempts_context = f"""
### Previous Attempts

This is round {round_number} of proving this step. Previous attempts:

{previous_attempts}

Use the verifier feedback to improve your proof.
"""

    # Resolve human help file (global prover guidance from user)
    project_root = os.path.dirname(prompts_dir)
    human_help_file = os.path.join(project_root, "human_help", "additional_prove_human_help_global.md")

    prompt = load_prompt(
        prompts_dir,
        "decomposition-prover/step_prover.md",
        step_file=step_content,
        step_id=step["id"],
        inputs_file=inputs_content,
        problem_file=problem_file,
        related_work_file=related_work_file,
        round_number=round_number,
        previous_attempts_context=previous_attempts_context,
        proved_steps_context=proved_context,
        human_help_file=human_help_file,
        output_file=os.path.join(state.get_step_dir(step["id"]), "proof.md"),
        output_dir=state.output_dir,
    )

    # Pre-create directories so the agent can write to them
    os.makedirs(state.get_step_dir(step["id"]), exist_ok=True)
    os.makedirs(state.get_step_round_dir(step["id"], round_number), exist_ok=True)

    if decomp_logger:
        decomp_logger.log_agent_call(
            "step_prover", f"Proving {step['id']}",
            model_provider,
            {"round": round_number, "is_key": step.get("is_key_step", False)}
        )
        decomp_logger.update_status(
            state="PROVING_STEP",
            current_step=step["id"],
            current_round=round_number,
            recent_activity=f"Proving step {step['id']} (round {round_number})"
        )

    response = await run_model(
        provider=model_provider,
        prompt=prompt,
        working_dir=state.output_dir,
        config=config,
        claude_opts=get_claude_opts_for_model(config, model_provider) if model_provider == "claude" else claude_opts,
        tracker=tracker,
        call_name=f"step_prover_{step['id']}_r{round_number}",
    )

    # Save LLM response into structured path
    if decomp_logger:
        resp_path = os.path.join(state.get_step_round_dir(step["id"], round_number), "prover_response.md")
        os.makedirs(os.path.dirname(resp_path), exist_ok=True)
        decomp_logger.save_agent_output(response, resp_path)
        decomp_logger.log_agent_result("step_prover", f"Step {step['id']} proof attempt complete")

    # Read the file the agent wrote via tool call
    expected_path = os.path.join(state.get_step_dir(step["id"]), "proof.md")
    content = read_file(expected_path)
    if not content:
        # Agent failed to write the file — fall back to response text
        content = response

    state.save_step_proof(step["id"], content, round_number=round_number)
    return content


async def run_step_verifier(
    state: DecompositionState,
    step: dict,
    proof: str,
    inputs: list[dict],
    prompts_dir: str,
    config: dict,
    claude_opts: dict,
    round_number: int = 1,
    decomp_logger: DecompositionLogger = None,
    tracker=None,
) -> tuple[str, str]:
    """Run the step verifier agent. Returns (verdict, full_response)."""

    model_provider = get_agent_model(config, "step_verifier")

    # Build step file content
    step_content = yaml.dump(step, default_flow_style=False)

    # Build inputs file content
    inputs_content = "# Input Statements\n\n"
    for inp in inputs:
        inputs_content += f"## {inp['id']}\n\n{inp.get('statement', '')}\n\n"

    prompt = load_prompt(
        prompts_dir,
        "decomposition-prover/step_verifier.md",
        step_file=step_content,
        step_id=step["id"],
        proof_file=proof,
        inputs_file=inputs_content,
        output_file=os.path.join(state.get_step_dir(step["id"]), "verification.md"),
        output_dir=state.output_dir,
    )

    if decomp_logger:
        decomp_logger.log_agent_call(
            "step_verifier", f"Verifying {step['id']}",
            model_provider,
            {}
        )
        decomp_logger.update_status(
            state="VERIFYING_STEP",
            current_step=step["id"],
            recent_activity=f"Verifying step {step['id']}"
        )

    # Pre-create directories so the agent can write to them
    os.makedirs(state.get_step_dir(step["id"]), exist_ok=True)
    os.makedirs(state.get_step_round_dir(step["id"], round_number), exist_ok=True)

    response = await run_model(
        provider=model_provider,
        prompt=prompt,
        working_dir=state.output_dir,
        config=config,
        claude_opts=get_claude_opts_for_model(config, model_provider) if model_provider == "claude" else claude_opts,
        tracker=tracker,
        call_name=f"step_verifier_{step['id']}",
    )

    # Save LLM response into structured path
    if decomp_logger:
        resp_path = os.path.join(state.get_step_round_dir(step["id"], round_number), "verifier_response.md")
        os.makedirs(os.path.dirname(resp_path), exist_ok=True)
        decomp_logger.save_agent_output(response, resp_path)

    # Read the file the agent wrote via tool call
    expected_path = os.path.join(state.get_step_dir(step["id"]), "verification.md")
    content = read_file(expected_path)
    if not content:
        # Agent failed to write the file — fall back to response text
        content = response

    state.save_step_verification(step["id"], content, round_number=round_number)
    verdict = parse_verdict(content)

    if decomp_logger:
        decomp_logger.log_agent_result("step_verifier", f"Step {step['id']} verdict: {verdict}")

    return verdict, content


async def run_regulator(
    state: DecompositionState,
    step: dict,
    attempts_history: str,
    latest_verification: str,
    config: dict,
    prompts_dir: str,
    claude_opts: dict,
    rounds_used: int,
    decomp_logger: DecompositionLogger = None,
    tracker=None,
) -> str:
    """Run the regulator agent to decide next action. Returns decision string."""

    model_provider = get_agent_model(config, "regulator")
    decomp_config = config.get("decomposition", DEFAULT_CONFIG)

    # Build state file content
    state_content = f"""
attempt: {state.attempt}
revision: {state.revision}
step_id: {step['id']}
rounds_for_step: {rounds_used}
max_prover_rounds: {decomp_config.get('max_prover_rounds', 5)}
max_revisions: {decomp_config.get('max_revisions', 3)}
max_decompositions: {decomp_config.get('max_decompositions', 3)}
"""

    prompt = load_prompt(
        prompts_dir,
        "decomposition-prover/regulator.md",
        state_file=state_content,
        step_file=yaml.dump(step, default_flow_style=False),
        attempts_file=attempts_history,
        verification_file=latest_verification,
        max_prover_rounds=decomp_config.get('max_prover_rounds', 5),
        max_revisions=decomp_config.get('max_revisions', 3),
        max_decompositions=decomp_config.get('max_decompositions', 3),
        output_file=os.path.join(state.get_revision_dir(), "regulator_decision.md"),
    )

    if decomp_logger:
        decomp_logger.log_agent_call(
            "regulator", f"Evaluating {step['id']}",
            model_provider,
            {"rounds_used": rounds_used}
        )
        decomp_logger.update_status(
            state="REGULATING",
            current_step=step["id"],
            recent_activity=f"Regulator evaluating step {step['id']} after {rounds_used} rounds"
        )

    response = await run_model(
        provider=model_provider,
        prompt=prompt,
        working_dir=state.output_dir,
        config=config,
        claude_opts=get_claude_opts_for_model(config, model_provider) if model_provider == "claude" else claude_opts,
        tracker=tracker,
        call_name=f"regulator_{step['id']}",
    )

    # Check if the agent wrote the decision file via tool call
    expected_path = os.path.join(state.get_revision_dir(), "regulator_decision.md")
    content = read_file(expected_path)
    if not content:
        content = response

    decision = parse_regulator_decision(content)
    state.save_regulator_decision(step["id"], decision, content)

    # Save LLM response into structured path
    if decomp_logger:
        resp_path = os.path.join(state.get_revision_dir(), f"regulator_{step['id']}_response.md")
        decomp_logger.save_agent_output(response, resp_path)
        decomp_logger.log_agent_result("regulator", f"Decision for {step['id']}: {decision}")

    return decision


async def run_proof_aggregator(
    state: DecompositionState,
    problem_file: str,
    prompts_dir: str,
    config: dict,
    claude_opts: dict,
    output_file: str,
    decomp_logger: DecompositionLogger = None,
    tracker=None,
) -> str:
    """Run the proof aggregator to combine step proofs into final proof.md."""

    model_provider = get_agent_model(config, "proof_aggregator")

    prompt = load_prompt(
        prompts_dir,
        "decomposition-prover/proof_aggregator.md",
        decomposition_file=os.path.join(state.get_attempt_dir(), "decomposition.yaml"),
        step_proofs_dir=state.get_revision_dir(),
        problem_file=problem_file,
        output_file=output_file,
    )

    if decomp_logger:
        decomp_logger.log_agent_call(
            "proof_aggregator", "Assembling final proof",
            model_provider,
            {}
        )
        decomp_logger.update_status(
            state="AGGREGATING",
            recent_activity="Assembling final proof from step proofs"
        )

    response = await run_model(
        provider=model_provider,
        prompt=prompt,
        working_dir=state.output_dir,
        config=config,
        claude_opts=get_claude_opts_for_model(config, model_provider) if model_provider == "claude" else claude_opts,
        tracker=tracker,
        call_name="proof_aggregator",
    )

    # Save LLM response into structured path
    if decomp_logger:
        resp_path = os.path.join(state.get_revision_dir(), "aggregator_response.md")
        decomp_logger.save_agent_output(response, resp_path)

    # Read the file the agent wrote via tool call
    content = read_file(output_file)
    if not content:
        # Agent failed to write the file — fall back to response text
        content = response
        if "# Proof" in content:
            proof_start = content.find("# Proof")
            if proof_start >= 0:
                content = content[proof_start:]
        write_file(output_file, content)

    return content


# ---------------------------------------------------------------------------
# Post-aggregation verification
# ---------------------------------------------------------------------------

async def run_structural_verification(
    state: DecompositionState,
    problem_file: str,
    proof_file: str,
    prompts_dir: str,
    config: dict,
    claude_opts: dict,
    decomp_logger: DecompositionLogger = None,
    tracker=None,
) -> tuple[str, str]:
    """Run structural verification on the aggregated proof.

    Returns (verdict, report_path) where verdict is "PASS" or "FAIL".
    """
    model_provider = get_agent_model(config, "step_verifier")

    verify_dir = os.path.join(state.get_attempt_dir(), f"revision_{state.revision}", "proof_verification")
    os.makedirs(verify_dir, exist_ok=True)

    output_file = os.path.join(verify_dir, "structural_verification.md")
    error_file = os.path.join(verify_dir, "error_structural_verification.md")
    decomposition_file = os.path.join(state.get_attempt_dir(), "decomposition.yaml")

    # Global verification rules and prover guidance from human_help/
    project_root = os.path.dirname(prompts_dir)
    additional_verify_rule_global_file = os.path.join(
        project_root, "human_help", "additional_verify_rule_global.md"
    )

    prompt = load_prompt(
        prompts_dir,
        "decomposition-prover/proof_verify_structural.md",
        problem_file=problem_file,
        proof_file=proof_file,
        decomposition_file=decomposition_file,
        output_file=output_file,
        error_file=error_file,
        output_dir=state.output_dir,
        additional_verify_rule_global_file=additional_verify_rule_global_file,
    )

    if decomp_logger:
        decomp_logger.log_agent_call(
            "step_verifier", "Structural verification of aggregated proof",
            model_provider,
            {}
        )
        decomp_logger.update_status(
            state="VERIFYING_PROOF_STRUCTURAL",
            recent_activity="Running structural verification on aggregated proof"
        )

    await run_model(
        provider=model_provider,
        prompt=prompt,
        working_dir=state.output_dir,
        config=config,
        claude_opts=get_claude_opts_for_model(config, model_provider) if model_provider == "claude" else claude_opts,
        tracker=tracker,
        call_name="proof_verify_structural",
    )

    # Parse verdict from the output file
    report = read_file(output_file)
    verdict = "FAIL"
    if report:
        report_upper = report.upper()
        # Look for overall verdict
        if "### OVERALL VERDICT: PASS" in report_upper or "OVERALL VERDICT: PASS" in report_upper:
            verdict = "PASS"

    if decomp_logger:
        decomp_logger.log_agent_result("step_verifier", f"Structural verification: {verdict}")

    return verdict, output_file


async def run_detailed_verification(
    state: DecompositionState,
    problem_file: str,
    proof_file: str,
    structural_report_file: str,
    prompts_dir: str,
    config: dict,
    claude_opts: dict,
    decomp_logger: DecompositionLogger = None,
    tracker=None,
) -> tuple[str, str]:
    """Run detailed verification on the aggregated proof.

    Returns (verdict, report_path) where verdict is "PASS" or "FAIL".
    """
    model_provider = get_agent_model(config, "step_verifier")

    verify_dir = os.path.join(state.get_attempt_dir(), f"revision_{state.revision}", "proof_verification")
    os.makedirs(verify_dir, exist_ok=True)

    output_file = os.path.join(verify_dir, "detailed_verification.md")
    error_file = os.path.join(verify_dir, "error_detailed_verification.md")
    decomposition_file = os.path.join(state.get_attempt_dir(), "decomposition.yaml")

    prompt = load_prompt(
        prompts_dir,
        "decomposition-prover/proof_verify_detailed.md",
        problem_file=problem_file,
        proof_file=proof_file,
        structural_report_file=structural_report_file,
        decomposition_file=decomposition_file,
        output_file=output_file,
        error_file=error_file,
        output_dir=state.output_dir,
    )

    if decomp_logger:
        decomp_logger.log_agent_call(
            "step_verifier", "Detailed verification of aggregated proof",
            model_provider,
            {}
        )
        decomp_logger.update_status(
            state="VERIFYING_PROOF_DETAILED",
            recent_activity="Running detailed verification on aggregated proof"
        )

    await run_model(
        provider=model_provider,
        prompt=prompt,
        working_dir=state.output_dir,
        config=config,
        claude_opts=get_claude_opts_for_model(config, model_provider) if model_provider == "claude" else claude_opts,
        tracker=tracker,
        call_name="proof_verify_detailed",
    )

    # Parse verdict from the output file
    report = read_file(output_file)
    verdict = "FAIL"
    if report:
        report_upper = report.upper()
        if "### OVERALL VERDICT: PASS" in report_upper or "OVERALL VERDICT: PASS" in report_upper:
            verdict = "PASS"

    if decomp_logger:
        decomp_logger.log_agent_result("step_verifier", f"Detailed verification: {verdict}")

    return verdict, output_file


async def run_proof_verification(
    state: DecompositionState,
    problem_file: str,
    proof_file: str,
    prompts_dir: str,
    config: dict,
    claude_opts: dict,
    decomp_logger: DecompositionLogger = None,
    tracker=None,
) -> tuple[str, str]:
    """Run full verification (structural + detailed) on the aggregated proof.

    Returns (final_verdict, combined_feedback) where final_verdict is "PASS" or "FAIL"
    and combined_feedback is the content of the verification reports for use by the
    decomposer on the next round.
    """
    # Step 1: Structural verification
    structural_verdict, structural_report_file = await run_structural_verification(
        state=state,
        problem_file=problem_file,
        proof_file=proof_file,
        prompts_dir=prompts_dir,
        config=config,
        claude_opts=claude_opts,
        decomp_logger=decomp_logger,
        tracker=tracker,
    )

    if structural_verdict == "FAIL":
        feedback = read_file(structural_report_file)
        if decomp_logger:
            decomp_logger.log("Structural verification FAILED — skipping detailed verification")
        return "FAIL", feedback

    # Step 2: Detailed verification (only if structural passed)
    detailed_verdict, detailed_report_file = await run_detailed_verification(
        state=state,
        problem_file=problem_file,
        proof_file=proof_file,
        structural_report_file=structural_report_file,
        prompts_dir=prompts_dir,
        config=config,
        claude_opts=claude_opts,
        decomp_logger=decomp_logger,
        tracker=tracker,
    )

    # Combine feedback from both reports
    structural_report = read_file(structural_report_file)
    detailed_report = read_file(detailed_report_file)
    combined_feedback = f"# Structural Verification\n\n{structural_report}\n\n---\n\n# Detailed Verification\n\n{detailed_report}"

    return detailed_verdict, combined_feedback


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def get_step_inputs(decomposition: dict, step_id: str) -> list[dict]:
    """Get the input statements for a step."""
    inputs = []
    step = None
    for s in decomposition.get("steps", []):
        if s["id"] == step_id:
            step = s
            break

    if not step:
        return inputs

    input_ids = step.get("inputs", [])

    # Check sources
    for source in decomposition.get("sources", []):
        if source["id"] in input_ids:
            inputs.append(source)

    # Check other steps
    for s in decomposition.get("steps", []):
        if s["id"] in input_ids:
            inputs.append(s)

    return inputs


async def prove_step_with_retries(
    state: DecompositionState,
    step: dict,
    inputs: list[dict],
    problem_file: str,
    related_work_file: str,
    config: dict,
    prompts_dir: str,
    claude_opts: dict,
    decomp_logger: DecompositionLogger = None,
    tracker=None,
) -> tuple[bool, str]:
    """Prove a single step with retries and regulator intervention.

    Returns (success, decision) where decision is the final regulator decision
    if the step failed, or "PROVED" if successful.
    """
    decomp_config = config.get("decomposition", DEFAULT_CONFIG)
    max_rounds = decomp_config.get("max_prover_rounds", 5)

    # Gather proofs of ALL previously proved steps so the prover can see
    # HOW they were proved — constructions, techniques, notation, and auxiliary
    # properties established. Even non-dependency proofs provide valuable context
    # about the overall proof strategy and available objects.
    proved_proofs = {}
    for sid, result in state.step_results.items():
        if result == "proved" and sid in state.step_proofs:
            proved_proofs[sid] = state.step_proofs[sid]

    attempts_history = ""
    verification = ""

    for round_num in range(1, max_rounds + 1):
        # Run step prover
        proof = await run_step_prover(
            state=state,
            step=step,
            inputs=inputs,
            problem_file=problem_file,
            related_work_file=related_work_file,
            prompts_dir=prompts_dir,
            config=config,
            claude_opts=claude_opts,
            round_number=round_num,
            previous_attempts=attempts_history,
            proved_proofs=proved_proofs,
            decomp_logger=decomp_logger,
            tracker=tracker,
        )

        # Run step verifier
        verdict, verification = await run_step_verifier(
            state=state,
            step=step,
            proof=proof,
            inputs=inputs,
            prompts_dir=prompts_dir,
            config=config,
            claude_opts=claude_opts,
            round_number=round_num,
            decomp_logger=decomp_logger,
            tracker=tracker,
        )

        if verdict == "PASS":
            state.mark_step_proved(step["id"])
            if decomp_logger:
                decomp_logger.update_status(
                    steps_proved=list(k for k, v in state.step_results.items() if v == "proved")
                )
            return True, "PROVED"

        # Add to attempts history for next round
        attempts_history += f"\n## Round {round_num}\n\n### Proof Attempt\n\n{proof[:2000]}...\n\n### Verification Result\n\n{verification[:1000]}...\n\n"

    # Step failed after max rounds - ask regulator
    decision = await run_regulator(
        state=state,
        step=step,
        attempts_history=attempts_history,
        latest_verification=verification,
        config=config,
        prompts_dir=prompts_dir,
        claude_opts=claude_opts,
        rounds_used=max_rounds,
        decomp_logger=decomp_logger,
        tracker=tracker,
    )

    state.mark_step_failed(step["id"])
    if decomp_logger:
        decomp_logger.update_status(
            steps_failed=list(k for k, v in state.step_results.items() if v == "failed")
        )
    return False, decision


async def run_decomposition_prover(
    problem_file: str,
    related_work_file: str,
    difficulty_file: str,
    output_dir: str,
    config: dict,
    prompts_dir: str,
    claude_opts: dict,
    logger=None,
    tracker=None,
) -> str:
    """Main entry point for decomposition-based proving.

    Returns the content of the final proof.md.
    """
    decomp_config = config.get("decomposition", DEFAULT_CONFIG)
    max_decompositions = decomp_config.get("max_decompositions", 3)
    max_revisions = decomp_config.get("max_revisions", 3)

    # Initialize state and logger
    state = DecompositionState(output_dir)

    decomp_logger = DecompositionLogger(output_dir)

    # Log model configuration
    models = decomp_config.get("models", DEFAULT_MODELS)
    decomp_logger.log(f"Model configuration: {models}")

    # --- Resume detection ---
    resume_info = detect_decomposition_resume(output_dir)
    resume_point = resume_info["resume_point"]

    # Handle already-done case
    if resume_point == "done":
        decomp_logger.log("RESUMING: Proof already verified successfully, nothing to do.")
        proof_file = os.path.join(output_dir, "proof.md")
        return read_file(proof_file)

    # Restore state from disk
    if resume_info["has_progress"]:
        state.attempt = resume_info["attempt"]
        state.revision = resume_info["revision"]
        state.attempt_history = resume_info["attempt_history"]
        if resume_info["decomposition"]:
            state.decomposition = resume_info["decomposition"]
        # Restore proved steps into state (both status and proof content)
        for step_id in resume_info["proved_steps"]:
            state.step_results[step_id] = "proved"
            # Also load the proof content from disk so subsequent step provers
            # can see how previously proved steps were proved
            proof_path = os.path.join(
                state.get_revision_dir(), f"step_{step_id}", "proof.md"
            )
            proof_content = read_file(proof_path)
            if proof_content:
                state.step_proofs[step_id] = proof_content

        decomp_logger.log(
            f"RESUMING: attempt={state.attempt}, revision={state.revision}, "
            f"resume_point={resume_point}, proved_steps={resume_info['proved_steps']}"
        )
        decomp_logger.update_status(
            state="RESUMING",
            attempt=state.attempt,
            revision=state.revision,
            steps_proved=resume_info["proved_steps"],
            recent_activity=f"Resuming from {resume_point}"
        )
    else:
        decomp_logger.log("Starting decomposition-based proof (fresh)")
        decomp_logger.update_status(
            state="INITIALIZING",
            attempt=1,
            revision=1,
            recent_activity="Initializing decomposition prover"
        )

    os.makedirs(state.get_attempt_dir(), exist_ok=True)
    os.makedirs(state.get_revision_dir(), exist_ok=True)

    # --- Handle mid-pipeline resume points ---
    # If we're resuming at aggregate/verify_structural/verify_detailed, jump directly there
    if resume_point in ("aggregate", "verify_structural", "verify_detailed"):
        decomposition = state.decomposition
        proof_file = os.path.join(output_dir, "proof.md")

        if resume_point == "aggregate":
            decomp_logger.log("RESUMING: Aggregating proof (all steps proved)")
            proof = await run_proof_aggregator(
                state=state,
                problem_file=problem_file,
                prompts_dir=prompts_dir,
                config=config,
                claude_opts=claude_opts,
                output_file=proof_file,
                decomp_logger=decomp_logger,
                tracker=tracker,
            )
            # Copy proof.md into the attempt/revision directory for record-keeping
            revision_proof_copy = os.path.join(state.get_revision_dir(), "proof.md")
            write_file(revision_proof_copy, proof)
        else:
            proof = read_file(proof_file)

        if resume_point in ("aggregate", "verify_structural"):
            decomp_logger.log("RESUMING: Running structural verification")
            structural_verdict, structural_report_file = await run_structural_verification(
                state=state,
                problem_file=problem_file,
                proof_file=proof_file,
                prompts_dir=prompts_dir,
                config=config,
                claude_opts=claude_opts,
                decomp_logger=decomp_logger,
                tracker=tracker,
            )
            if structural_verdict == "FAIL":
                # Fall through to the main loop for regulator handling
                resume_point = "prove_steps"
                state.step_results = {}
                decomp_logger.log("Structural verification FAILED on resume — will consult regulator")
                # Continue to main loop below
            else:
                resume_point = "verify_detailed"

        if resume_point == "verify_detailed":
            decomp_logger.log("RESUMING: Running detailed verification")
            verify_dir = os.path.join(state.get_attempt_dir(), f"revision_{state.revision}", "proof_verification")
            structural_report_file = os.path.join(verify_dir, "structural_verification.md")

            detailed_verdict, detailed_report_file = await run_detailed_verification(
                state=state,
                problem_file=problem_file,
                proof_file=proof_file,
                structural_report_file=structural_report_file,
                prompts_dir=prompts_dir,
                config=config,
                claude_opts=claude_opts,
                decomp_logger=decomp_logger,
                tracker=tracker,
            )

            if detailed_verdict == "PASS":
                decomp_logger.log("Proof verification PASSED on resume. Done!")
                decomp_logger.update_status(
                    state="COMPLETED",
                    recent_activity="Proof completed and verified successfully (resumed)"
                )
                return proof

            # FAIL — fall through to main loop for regulator
            decomp_logger.log("Detailed verification FAILED on resume — will consult regulator")
            resume_point = "prove_steps"
            state.step_results = {}

    # --- Main loop ---
    decomp_attempt = state.attempt - 1  # Will be incremented at top of loop
    initial_loop = True  # Flag: first iteration may skip decomposer if resuming

    while decomp_attempt < max_decompositions:
        decomp_attempt += 1

        if not initial_loop:
            # Normal new attempt
            state.new_attempt()
            decomp_logger.update_status(
                attempt=decomp_attempt,
                revision=1,
                steps_proved=[],
                steps_failed=[],
                recent_activity=f"Starting decomposition attempt {decomp_attempt}"
            )

        if not initial_loop or resume_point in ("fresh", "decompose"):
            # Create initial decomposition (or rewrite)
            mode = "CREATE" if decomp_attempt == 1 and not resume_info["has_progress"] else "REWRITE"
            decomposition = await run_decomposer(
                state=state,
                problem_file=problem_file,
                related_work_file=related_work_file,
                difficulty_file=difficulty_file,
                prompts_dir=prompts_dir,
                config=config,
                claude_opts=claude_opts,
                mode=mode,
                decomp_logger=decomp_logger,
                tracker=tracker,
            )
        else:
            # Resuming with existing decomposition
            decomposition = state.decomposition or state.load_decomposition()
            if not decomposition:
                # Safety fallback: no decomposition found, create fresh
                decomposition = await run_decomposer(
                    state=state,
                    problem_file=problem_file,
                    related_work_file=related_work_file,
                    difficulty_file=difficulty_file,
                    prompts_dir=prompts_dir,
                    config=config,
                    claude_opts=claude_opts,
                    mode="CREATE",
                    decomp_logger=decomp_logger,
                    tracker=tracker,
                )

        initial_loop = False  # After first iteration, normal flow

        key_steps = decomposition.get("key_steps", [])
        total_steps = len(decomposition.get("steps", []))
        decomp_logger.log(f"Decomposition: {total_steps} steps, {len(key_steps)} key steps")

        # Try to prove all steps (with revisions)
        all_proved = False
        # When resuming, start revision_count at the current revision so we don't
        # exceed max_revisions by miscounting prior revisions
        revision_count = state.revision if (decomp_attempt == resume_info["attempt"]) else 0
        decision = ""
        need_retry_same_attempt = True  # Controls re-entering the prove loop after verification REVISE

        while need_retry_same_attempt:
            need_retry_same_attempt = False  # Will be set to True if verification triggers REVISE
            all_proved = False  # Reset: only set True inside the proving loop
            decision = ""  # Reset stale decision from previous iteration

            # --- Prove all steps ---
            while revision_count <= max_revisions:
                all_proved = True

                # Get proof order: key steps first, then others
                key_steps = decomposition.get("key_steps", [])
                proof_order = decomposition.get("proof_order", [])

                # Reorder: key steps first (preserving their relative order
                # from proof_order), then non-key steps in proof_order
                key_ordered = [s for s in proof_order if s in key_steps]
                non_key_ordered = [s for s in proof_order if s not in key_steps]
                ordered_steps = key_ordered + non_key_ordered

                # Remove GOAL from proving (it's proved by combining steps)
                ordered_steps = [s for s in ordered_steps if s != "GOAL"]

                for step_id in ordered_steps:
                    # Skip already proved steps
                    if state.step_results.get(step_id) == "proved":
                        continue

                    # Find the step
                    step = None
                    for s in decomposition.get("steps", []):
                        if s["id"] == step_id:
                            step = s
                            break

                    if not step:
                        continue

                    inputs = get_step_inputs(decomposition, step_id)

                    success, decision = await prove_step_with_retries(
                        state=state,
                        step=step,
                        inputs=inputs,
                        problem_file=problem_file,
                        related_work_file=related_work_file,
                        config=config,
                        prompts_dir=prompts_dir,
                        claude_opts=claude_opts,
                        decomp_logger=decomp_logger,
                        tracker=tracker,
                    )

                    if not success:
                        all_proved = False

                        if decision == "REWRITE":
                            decomp_logger.log(f"Regulator requested rewrite")
                            break  # Exit step loop, trigger new decomposition

                        else:  # REVISE
                            decomp_logger.log(f"Regulator requested revision around step {step_id}")

                            # Capture paths BEFORE new_revision() changes state.revision
                            verify_path = os.path.join(state.get_step_dir(step_id), "verification.md")
                            feedback = read_file(verify_path)
                            old_prover_file = os.path.join(state.get_step_dir(step_id), "proof.md")

                            state.new_revision()
                            decomp_logger.update_status(
                                revision=state.revision,
                                recent_activity=f"Revising decomposition around step {step_id}"
                            )

                            decomposition = await run_decomposer(
                                state=state,
                                problem_file=problem_file,
                                related_work_file=related_work_file,
                                difficulty_file=difficulty_file,
                                prompts_dir=prompts_dir,
                                config=config,
                                claude_opts=claude_opts,
                                mode="REVISE",
                                failed_step_id=step_id,
                                failure_feedback=feedback,
                                prover_attempts_file=old_prover_file,
                                decomp_logger=decomp_logger,
                                tracker=tracker,
                            )
                            revision_count += 1
                            break  # Restart step proving with revised decomposition

                else:
                    # All steps proved successfully (for-else: no break)
                    break

                # Check if we need to break out for rewrite
                if decision == "REWRITE":
                    break

            # --- After step proving loop ---

            if not all_proved and decision != "REWRITE":
                decomp_logger.log(f"Max revisions ({max_revisions}) exhausted, triggering rewrite")
                decomp_logger.update_status(
                    state="REWRITING",
                    recent_activity=f"Max revisions exhausted, starting new decomposition attempt"
                )
                break  # Break out to trigger new attempt

            if not all_proved:
                # decision == "REWRITE"
                decomp_logger.log(f"Attempt {decomp_attempt} failed (steps not proved), trying new decomposition")
                break  # Break out to trigger new attempt

            # --- All steps proved: aggregate and verify ---

            decomp_logger.log("All steps proved! Aggregating final proof.")
            decomp_logger.update_status(
                state="AGGREGATING",
                recent_activity="All steps proved, aggregating final proof"
            )

            proof_file = os.path.join(output_dir, "proof.md")
            proof = await run_proof_aggregator(
                state=state,
                problem_file=problem_file,
                prompts_dir=prompts_dir,
                config=config,
                claude_opts=claude_opts,
                output_file=proof_file,
                decomp_logger=decomp_logger,
                tracker=tracker,
            )

            # Copy proof.md into the attempt/revision directory for record-keeping
            revision_proof_copy = os.path.join(state.get_revision_dir(), "proof.md")
            write_file(revision_proof_copy, proof)

            decomp_logger.log("Final proof aggregated. Running verification...")
            decomp_logger.update_status(
                state="VERIFYING_PROOF",
                recent_activity="Running structural + detailed verification on aggregated proof"
            )

            # Run full verification on the aggregated proof
            proof_verdict, verification_feedback = await run_proof_verification(
                state=state,
                problem_file=problem_file,
                proof_file=proof_file,
                prompts_dir=prompts_dir,
                config=config,
                claude_opts=claude_opts,
                decomp_logger=decomp_logger,
                tracker=tracker,
            )

            if proof_verdict == "PASS":
                decomp_logger.log("Proof verification PASSED. Done!")
                decomp_logger.update_status(
                    state="COMPLETED",
                    recent_activity="Proof completed and verified successfully"
                )
                return proof

            # Verification FAILED — ask regulator whether to REVISE or REWRITE
            decomp_logger.log("Proof verification FAILED. Consulting regulator...")
            decomp_logger.update_status(
                state="VERIFICATION_FAILED",
                recent_activity="Proof verification failed, consulting regulator"
            )

            # Save verification feedback for the decomposer
            feedback_path = os.path.join(
                state.get_attempt_dir(), f"revision_{state.revision}",
                "proof_verification", "combined_feedback.md"
            )
            write_file(feedback_path, verification_feedback)

            proof_step = {
                "id": "AGGREGATED_PROOF",
                "statement": "The aggregated proof as a whole",
                "difficulty": "hard",
                "is_key_step": True,
            }

            regulator_decision = await run_regulator(
                state=state,
                step=proof_step,
                attempts_history=f"The aggregated proof was assembled and verified.\n\nVerification result: FAIL\n\n{verification_feedback[:3000]}",
                latest_verification=verification_feedback[:2000],
                config=config,
                prompts_dir=prompts_dir,
                claude_opts=claude_opts,
                rounds_used=1,
                decomp_logger=decomp_logger,
                tracker=tracker,
            )

            if regulator_decision == "REWRITE":
                decomp_logger.log("Regulator decided REWRITE after proof verification failure")
                break  # Break out to trigger new attempt

            # REVISE after verification failure
            decomp_logger.log("Regulator decided REVISE after proof verification failure")

            if revision_count < max_revisions:
                # Capture proof path BEFORE new_revision() changes state.revision
                old_proof_file = os.path.join(state.get_revision_dir(), "proof.md")

                state.new_revision()
                state.step_proofs = {}
                state.step_results = {}
                revision_count += 1
                decomp_logger.update_status(
                    revision=state.revision,
                    steps_proved=[],
                    steps_failed=[],
                    recent_activity="Revising decomposition based on proof verification feedback"
                )

                decomposition = await run_decomposer(
                    state=state,
                    problem_file=problem_file,
                    related_work_file=related_work_file,
                    difficulty_file=difficulty_file,
                    prompts_dir=prompts_dir,
                    config=config,
                    claude_opts=claude_opts,
                    mode="REVISE",
                    failed_step_id="AGGREGATED_PROOF",
                    failure_feedback=verification_feedback[:4000],
                    prover_attempts_file=old_proof_file,
                    decomp_logger=decomp_logger,
                    tracker=tracker,
                )
                # Re-enter the prove loop with the revised decomposition
                need_retry_same_attempt = True
            else:
                decomp_logger.log("Max revisions exhausted after verification failure, triggering rewrite")
                break  # Break out to trigger new attempt

    decomp_logger.log("All decomposition attempts exhausted")
    decomp_logger.update_status(
        state="FAILED",
        recent_activity="All decomposition attempts exhausted"
    )

    return ""


# ---------------------------------------------------------------------------
# Entry point for testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    print("Decomposition prover module loaded.")
    print("Use run_decomposition_prover() from pipeline.py to run.")
