"""Subprocess management: launch, kill, and resume the QED pipeline."""

import os
import shutil
import signal
import subprocess

from utils import (
    PROJECT_ROOT,
    RUN_SH,
    ACTIVE_CONFIG_PATH,
    save_config,
    file_nonempty,
    find_verification_files,
    is_parallel_round,
    list_round_dirs,
    is_survey_complete,
)


# ---------------------------------------------------------------------------
# Launch / kill
# ---------------------------------------------------------------------------

def start_pipeline(
    problem_file: str,
    output_dir: str,
    config: dict,
) -> subprocess.Popen:
    """Start the pipeline as a background subprocess.

    1. Writes *config* to ``.config_run_active.yaml`` at project root.
    2. Invokes ``run.sh <problem_file> <output_dir> <config_path>``.
    3. Returns the ``Popen`` object.

    stdout/stderr are redirected to a log file inside *output_dir* to avoid
    blocking on a full pipe buffer.
    """
    save_config(config, ACTIVE_CONFIG_PATH)
    config_abs = os.path.abspath(ACTIVE_CONFIG_PATH)
    problem_abs = os.path.abspath(problem_file)
    output_abs = os.path.abspath(output_dir)

    os.makedirs(output_abs, exist_ok=True)
    log_path = os.path.join(output_abs, "pipeline_stdout.log")
    log_fh = open(log_path, "a")

    proc = subprocess.Popen(
        ["bash", RUN_SH, problem_abs, output_abs, config_abs],
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
        cwd=PROJECT_ROOT,
    )
    # Attach the file handle so we can close it later
    proc._log_fh = log_fh
    return proc


def kill_pipeline(proc: subprocess.Popen) -> None:
    """Kill the pipeline and its entire process tree."""
    if proc is None or proc.poll() is not None:
        _close_log(proc)
        return
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(pgid, signal.SIGKILL)
            proc.wait(timeout=3)
    except (ProcessLookupError, OSError):
        pass
    _close_log(proc)


def _close_log(proc: subprocess.Popen | None) -> None:
    """Close the log file handle attached by start_pipeline."""
    if proc is not None and hasattr(proc, "_log_fh"):
        try:
            proc._log_fh.close()
        except OSError:
            pass


def is_alive(proc: subprocess.Popen | None) -> bool:
    """Return True if *proc* is still running."""
    if proc is None:
        return False
    return proc.poll() is None


# ---------------------------------------------------------------------------
# Resume options
# ---------------------------------------------------------------------------

def get_resume_options(output_dir: str) -> list[dict]:
    """Scan the output directory and return valid resume points.

    Each item: ``{"round": int, "step": str, "label": str}``.
    """
    options: list[dict] = []

    # Always offer "from scratch"
    options.append({
        "round": 0,
        "step": "start",
        "label": "From scratch (delete everything)",
    })

    if is_survey_complete(output_dir):
        options.append({
            "round": 0,
            "step": "after_survey",
            "label": "After survey (start Round 1)",
        })

    rounds = list_round_dirs(output_dir)
    for r in rounds:
        round_dir = os.path.join(output_dir, "verification", f"round_{r}")
        parallel = is_parallel_round(round_dir)

        # Offer "redo this round from proof search"
        options.append({
            "round": r,
            "step": "proof_search",
            "label": f"Round {r}: Proof Search (redo round)",
        })

        # Check if proof search done
        if parallel:
            any_proof = any(
                file_nonempty(os.path.join(round_dir, m, "proof_status.md"))
                for m in ("claude", "codex", "gemini")
                if os.path.isdir(os.path.join(round_dir, m))
            )
        else:
            any_proof = file_nonempty(
                os.path.join(round_dir, "proof_status.md")
            )

        if any_proof:
            options.append({
                "round": r,
                "step": "verification",
                "label": f"Round {r}: Verification (keep proof, redo verification)",
            })

            # Check structural done
            if parallel:
                s_dir = os.path.join(round_dir, "claude", "verification_file", "structural")
            else:
                s_dir = os.path.join(round_dir, "verification_file", "structural")
            if find_verification_files(s_dir):
                options.append({
                    "round": r,
                    "step": "detailed_verification",
                    "label": f"Round {r}: Detailed Verification (keep structural, redo detailed)",
                })

    return options


# ---------------------------------------------------------------------------
# Resume cleanup
# ---------------------------------------------------------------------------

def prepare_resume(output_dir: str, target_round: int, target_step: str) -> None:
    """Clean up the output directory so ``detect_resume_state()`` resumes correctly.

    The pipeline's own resume logic reads file-system state, so we just need
    to delete files/dirs that represent progress past the desired resume point.
    """
    # Always remove Stage 2 outputs (will be regenerated)
    for name in ("proof_effort_summary.md",):
        path = os.path.join(output_dir, name)
        if os.path.exists(path):
            os.remove(path)
    summary_log = os.path.join(output_dir, "summary_log")
    if os.path.isdir(summary_log):
        shutil.rmtree(summary_log)

    # "From scratch" — wipe everything
    if target_step == "start":
        for d in ("verification", "related_info", "literature_survey_log"):
            path = os.path.join(output_dir, d)
            if os.path.isdir(path):
                shutil.rmtree(path)
        proof = os.path.join(output_dir, "proof.md")
        if os.path.exists(proof):
            os.remove(proof)
        for name in ("TOKEN_USAGE.md", "token_usage.json"):
            path = os.path.join(output_dir, name)
            if os.path.exists(path):
                os.remove(path)
        return

    # "After survey" — keep survey, wipe rounds
    if target_step == "after_survey":
        verify_dir = os.path.join(output_dir, "verification")
        if os.path.isdir(verify_dir):
            shutil.rmtree(verify_dir)
        proof = os.path.join(output_dir, "proof.md")
        if os.path.exists(proof):
            os.remove(proof)
        return

    verify_dir = os.path.join(output_dir, "verification")
    if not os.path.isdir(verify_dir):
        return

    # Delete rounds after the target
    rounds = list_round_dirs(output_dir)
    for r in rounds:
        if r > target_round:
            rd = os.path.join(verify_dir, f"round_{r}")
            if os.path.isdir(rd):
                shutil.rmtree(rd)

    round_dir = os.path.join(verify_dir, f"round_{target_round}")
    if not os.path.isdir(round_dir):
        return

    if target_step == "proof_search":
        # Delete the entire round — pipeline will redo from proof search
        # First restore proof.md from backup if available
        backup = os.path.join(round_dir, "proof_before_round.md")
        proof_file = os.path.join(output_dir, "proof.md")
        if os.path.exists(backup):
            shutil.copy2(backup, proof_file)
        shutil.rmtree(round_dir)

    elif target_step == "verification":
        # Keep proof_status.md and proof files, delete all verification
        if is_parallel_round(round_dir):
            for m in ("claude", "codex", "gemini"):
                vf_dir = os.path.join(round_dir, m, "verification_file")
                if os.path.isdir(vf_dir):
                    shutil.rmtree(vf_dir)
        else:
            vf_dir = os.path.join(round_dir, "verification_file")
            if os.path.isdir(vf_dir):
                shutil.rmtree(vf_dir)
            # Also clean legacy verification files in round dir itself
            for name in os.listdir(round_dir):
                if name.startswith("verification_result"):
                    os.remove(os.path.join(round_dir, name))
        # Remove selection.md for parallel rounds
        sel = os.path.join(round_dir, "selection.md")
        if os.path.exists(sel):
            os.remove(sel)

    elif target_step == "detailed_verification":
        # Keep structural, delete detailed
        if is_parallel_round(round_dir):
            for m in ("claude", "codex", "gemini"):
                d_dir = os.path.join(round_dir, m, "verification_file", "detailed")
                if os.path.isdir(d_dir):
                    shutil.rmtree(d_dir)
        else:
            d_dir = os.path.join(round_dir, "verification_file", "detailed")
            if os.path.isdir(d_dir):
                shutil.rmtree(d_dir)
        sel = os.path.join(round_dir, "selection.md")
        if os.path.exists(sel):
            os.remove(sel)
