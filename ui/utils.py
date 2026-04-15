"""Shared constants and helper functions for the QED Streamlit UI."""

import json
import os
import re

import yaml

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

UI_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(UI_DIR)
RUN_SH = os.path.join(PROJECT_ROOT, "run.sh")
HUMAN_HELP_DIR = os.path.join(PROJECT_ROOT, "human_help")
DEFAULT_OUTPUT_ROOT = os.path.join(UI_DIR, "proof_runs")
ACTIVE_CONFIG_PATH = os.path.join(PROJECT_ROOT, ".config_run_active.yaml")
ORIGINAL_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.yaml")

GLOBAL_PROVE_HH = os.path.join(HUMAN_HELP_DIR, "additional_prove_human_help_global.md")
GLOBAL_VERIFY_HH = os.path.join(HUMAN_HELP_DIR, "additional_verify_rule_global.md")

MODEL_PROVIDERS = ("claude", "codex", "gemini")


# ---------------------------------------------------------------------------
# YAML I/O
# ---------------------------------------------------------------------------

def load_config(path: str) -> dict:
    """Read a YAML config file and return the parsed dict."""
    with open(path) as f:
        return yaml.safe_load(f) or {}


def save_config(config: dict, path: str) -> None:
    """Write *config* dict to a YAML file at *path*."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def read_file(path: str) -> str:
    """Read a text file. Return ``""`` if missing or empty."""
    if not os.path.exists(path):
        return ""
    with open(path) as f:
        return f.read()


def write_file(path: str, content: str) -> None:
    """Write *content* to *path*, creating parent directories if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def file_nonempty(path: str) -> bool:
    """Return True if *path* exists and has non-whitespace content."""
    if not os.path.exists(path):
        return False
    with open(path) as f:
        return bool(f.read().strip())


# ---------------------------------------------------------------------------
# Verification-file helpers (mirrors pipeline.py)
# ---------------------------------------------------------------------------

def find_verification_files(directory: str) -> list[str]:
    """Find verification result files in *directory*.

    Returns the single-file path if ``verification_result.md`` exists,
    otherwise all ``verification_result_<provider>.md`` files.
    """
    single = os.path.join(directory, "verification_result.md")
    if file_nonempty(single):
        return [single]
    files = []
    if os.path.isdir(directory):
        for name in sorted(os.listdir(directory)):
            if name.startswith("verification_result_") and name.endswith(".md"):
                path = os.path.join(directory, name)
                if file_nonempty(path):
                    files.append(path)
    return files


def parse_verdict_from_file(path: str) -> str:
    """Parse the Overall Verdict from a verification_result file.

    Returns ``'PASS'``, ``'FAIL'``, or ``'UNKNOWN'``.
    """
    try:
        with open(path) as f:
            for line in f:
                if "overall verdict" in line.lower():
                    upper = line.upper()
                    if "PASS" in upper:
                        return "PASS"
                    if "FAIL" in upper:
                        return "FAIL"
    except OSError:
        pass
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Progress scanning helpers
# ---------------------------------------------------------------------------

def is_parallel_round(round_dir: str) -> bool:
    """Return True if *round_dir* contains per-model subdirectories."""
    return any(
        os.path.isdir(os.path.join(round_dir, m)) for m in MODEL_PROVIDERS
    )


def list_round_dirs(output_dir: str) -> list[int]:
    """Return sorted list of round numbers found in ``verification/``."""
    verify_dir = os.path.join(output_dir, "verification")
    if not os.path.isdir(verify_dir):
        return []
    nums: list[int] = []
    for name in os.listdir(verify_dir):
        if name.startswith("round_"):
            try:
                nums.append(int(name.split("_", 1)[1]))
            except ValueError:
                continue
    nums.sort()
    return nums


def is_survey_complete(output_dir: str) -> bool:
    """True if the literature survey stage completed."""
    ri = os.path.join(output_dir, "related_info")
    return (
        file_nonempty(os.path.join(ri, "difficulty_evaluation.md"))
        and file_nonempty(os.path.join(ri, "related_work.md"))
    )


def is_pipeline_complete(output_dir: str) -> bool:
    """True if the entire pipeline finished (summary exists)."""
    return file_nonempty(os.path.join(output_dir, "proof_effort_summary.md"))


def parse_difficulty(output_dir: str) -> str:
    """Parse difficulty classification. Returns easy/medium/hard/unknown."""
    path = os.path.join(output_dir, "related_info", "difficulty_evaluation.md")
    if not os.path.exists(path):
        return "unknown"
    with open(path) as f:
        for line in f:
            if "classification" in line.lower():
                upper = line.upper()
                if "EASY" in upper:
                    return "easy"
                if "MEDIUM" in upper:
                    return "medium"
                if "HARD" in upper:
                    return "hard"
    return "unknown"


def get_round_status(output_dir: str, round_num: int) -> dict:
    """Return status dict for a single round.

    Mirrors the file-existence checks in ``detect_resume_state()``
    (pipeline.py:367-562).

    Returns::

        {
            "num": int,
            "is_parallel": bool,
            "proof_done": bool,
            "structural_done": bool,
            "detailed_done": bool,
            "verdict": str,         # PASS / FAIL / UNKNOWN / ""
        }
    """
    round_dir = os.path.join(output_dir, "verification", f"round_{round_num}")
    result = {
        "num": round_num,
        "is_parallel": False,
        "proof_done": False,
        "structural_done": False,
        "detailed_done": False,
        "verdict": "",
    }
    if not os.path.isdir(round_dir):
        return result

    parallel = is_parallel_round(round_dir)
    result["is_parallel"] = parallel

    if parallel:
        # Check per-model status
        models_proof = []
        models_structural = []
        models_detailed = []
        for m in MODEL_PROVIDERS:
            mdir = os.path.join(round_dir, m)
            if not os.path.isdir(mdir):
                continue
            if file_nonempty(os.path.join(mdir, "proof_status.md")):
                models_proof.append(m)
            s_dir = os.path.join(mdir, "verification_file", "structural")
            d_dir = os.path.join(mdir, "verification_file", "detailed")
            if find_verification_files(d_dir) or find_verification_files(mdir):
                models_detailed.append(m)
            elif find_verification_files(s_dir):
                models_structural.append(m)

        result["proof_done"] = len(models_proof) > 0
        result["structural_done"] = (
            len(models_structural) + len(models_detailed) == len(models_proof)
            and len(models_proof) > 0
        )
        all_detailed = (
            len(models_detailed) == len(models_proof) and len(models_proof) > 0
        )
        # selection.md is only created when multiple providers ran;
        # with a single provider the pipeline skips selection.
        has_selection = file_nonempty(os.path.join(round_dir, "selection.md"))
        result["detailed_done"] = all_detailed and (
            has_selection or len(models_proof) == 1
        )
        # Verdict: parse from any available detailed verification file
        for m in models_detailed:
            d_dir = os.path.join(round_dir, m, "verification_file", "detailed")
            for vf in find_verification_files(d_dir):
                v = parse_verdict_from_file(vf)
                if v in ("PASS", "FAIL"):
                    result["verdict"] = v
                    break
            if result["verdict"]:
                break
    else:
        # Single-model round
        result["proof_done"] = file_nonempty(
            os.path.join(round_dir, "proof_status.md")
        )
        s_dir = os.path.join(round_dir, "verification_file", "structural")
        d_dir = os.path.join(round_dir, "verification_file", "detailed")
        result["structural_done"] = bool(find_verification_files(s_dir))
        result["detailed_done"] = bool(
            find_verification_files(d_dir)
            or find_verification_files(round_dir)  # legacy layout
        )
        # Parse verdict
        verify_files = (
            find_verification_files(d_dir)
            or find_verification_files(round_dir)
        )
        if verify_files:
            result["verdict"] = parse_verdict_from_file(verify_files[0])

    return result


def parse_token_usage(output_dir: str) -> dict | None:
    """Read ``token_usage.json`` if present. Return dict or None."""
    path = os.path.join(output_dir, "token_usage.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
