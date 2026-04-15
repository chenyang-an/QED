"""File-system scanner and Streamlit renderer for pipeline progress."""

import os

import streamlit as st

from utils import (
    is_survey_complete,
    is_pipeline_complete,
    parse_difficulty,
    list_round_dirs,
    get_round_status,
    parse_token_usage,
    read_file,
    write_file,
    file_nonempty,
    find_verification_files,
    MODEL_PROVIDERS,
)


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

def scan_progress(output_dir: str) -> dict:
    """Scan the output directory and return a progress snapshot."""
    result = {
        "exists": False,
        "survey_complete": False,
        "difficulty": "unknown",
        "rounds": [],
        "pipeline_complete": False,
        "current_stage": "idle",
        "proof_content": "",
        "token_usage": None,
    }

    if not os.path.isdir(output_dir):
        return result

    result["exists"] = True
    result["survey_complete"] = is_survey_complete(output_dir)
    result["difficulty"] = parse_difficulty(output_dir)
    result["pipeline_complete"] = is_pipeline_complete(output_dir)

    rounds = list_round_dirs(output_dir)
    for r in rounds:
        result["rounds"].append(get_round_status(output_dir, r))

    result["proof_content"] = read_file(os.path.join(output_dir, "proof.md"))
    result["token_usage"] = parse_token_usage(output_dir)

    # Determine current stage
    if result["pipeline_complete"]:
        result["current_stage"] = "complete"
    elif result["rounds"]:
        last = result["rounds"][-1]
        if last["verdict"] == "PASS":
            result["current_stage"] = "summary"
        else:
            result["current_stage"] = "proof_loop"
    elif result["survey_complete"]:
        result["current_stage"] = "proof_loop"
    elif result["exists"]:
        result["current_stage"] = "survey"
    else:
        result["current_stage"] = "idle"

    return result


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

import re

def parse_smoke_test_status(output_dir: str) -> dict:
    """Parse smoke test status from pipeline_stdout.log.

    Returns::

        {
            "started": bool,     # log file exists with content
            "finished": bool,    # SMOKE TEST RESULTS line found
            "passed": int,
            "failed": int,
            "ok": bool,          # finished and failed == 0
            "log": str,          # full smoke test output
        }
    """
    result = {
        "started": False,
        "finished": False,
        "passed": 0,
        "failed": 0,
        "ok": False,
        "log": "",
    }
    log_path = os.path.join(output_dir, "pipeline_stdout.log")
    content = read_file(log_path)
    if not content.strip():
        return result

    result["started"] = True

    # Extract everything up to (and including) the SMOKE TEST RESULTS block
    # The results line looks like: SMOKE TEST RESULTS: 42 passed, 0 failed
    match = re.search(
        r"SMOKE TEST RESULTS:\s*(\d+)\s*passed,\s*(\d+)\s*failed", content
    )
    if match:
        result["finished"] = True
        result["passed"] = int(match.group(1))
        result["failed"] = int(match.group(2))
        result["ok"] = result["failed"] == 0
        # Grab log up to end of the results block (next === line after results)
        end_pos = content.find("=" * 20, match.end())
        if end_pos != -1:
            # Include up to end of that === line
            nl = content.find("\n", end_pos)
            result["log"] = content[: nl + 1 if nl != -1 else end_pos + 60]
        else:
            result["log"] = content[: match.end() + 100]
    else:
        # Still running — show what we have so far
        result["log"] = content

    return result


def render_smoke_test(output_dir: str, run_active: bool) -> dict:
    """Render smoke test status. Returns the parsed status dict."""
    status = parse_smoke_test_status(output_dir)

    if not status["started"]:
        if run_active:
            st.info("Starting pipeline...")
        return status

    if status["finished"]:
        if status["ok"]:
            st.success(
                f"Smoke test **passed** ({status['passed']} checks passed)"
            )
        else:
            st.error(
                f"Smoke test **failed** ({status['passed']} passed, "
                f"{status['failed']} failed)"
            )
            with st.expander("Smoke Test Log", expanded=True):
                st.code(status["log"], language="text")
    else:
        if run_active:
            st.info("Running smoke tests...")
            with st.expander("Smoke Test Output (live)", expanded=True):
                st.code(status["log"], language="text")

    return status


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tail_file(path: str, max_bytes: int = 20_000, max_lines: int = 80) -> str:
    """Read the tail of a file efficiently."""
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            read_from = max(0, size - max_bytes)
            f.seek(read_from)
            raw = f.read().decode("utf-8", errors="replace")
        lines = raw.splitlines()
        if read_from > 0:
            lines = lines[1:]
        return "\n".join(lines[-max_lines:])
    except OSError:
        return ""


def _file_link(path: str, output_dir: str) -> str:
    """Return a relative path string for display."""
    try:
        return os.path.relpath(path, output_dir)
    except ValueError:
        return path


def _show_file(label: str, path: str, output_dir: str,
               expanded: bool = False, as_code: bool = False) -> None:
    """Show a file in an expander with its relative path."""
    content = read_file(path)
    if not content.strip():
        return
    rel = _file_link(path, output_dir)
    with st.expander(f"{label}  `{rel}`", expanded=expanded):
        if as_code:
            st.code(content, language="text")
        else:
            st.markdown(content)


# ---------------------------------------------------------------------------
# Stage indicator
# ---------------------------------------------------------------------------

def _render_stage_indicator(scan: dict) -> None:
    """Render the three-stage progress indicator."""
    stage = scan["current_stage"]
    cols = st.columns(3)
    stages = [
        ("Survey", "survey"),
        ("Proof Loop", "proof_loop"),
        ("Summary", "summary"),
    ]
    for col, (label, stage_key) in zip(cols, stages):
        with col:
            if stage == "complete":
                st.success(f"**{label}** -- Done")
            elif stage_key == stage:
                st.info(f"**{label}** -- Running...")
            elif (
                (stage_key == "survey" and scan["survey_complete"])
                or (stage_key == "proof_loop" and scan["rounds"]
                    and stage in ("summary", "complete"))
            ):
                st.success(f"**{label}** -- Done")
            else:
                st.markdown(f"**{label}** -- Pending")


def _render_metrics(scan: dict) -> None:
    """Render the metrics row."""
    token = scan["token_usage"]
    cols = st.columns(4)
    cols[0].metric("Rounds", len(scan["rounds"]))
    cols[1].metric("Difficulty", scan["difficulty"].capitalize())
    if token:
        cols[2].metric("Input Tokens", f"{token.get('total_input_tokens', 0):,}")
        cols[3].metric("Output Tokens", f"{token.get('total_output_tokens', 0):,}")
    else:
        cols[2].metric("Input Tokens", "--")
        cols[3].metric("Output Tokens", "--")


# ---------------------------------------------------------------------------
# Pipeline status & event history
# ---------------------------------------------------------------------------

def _render_status_and_history(output_dir: str) -> None:
    """Render current status table and event timeline."""
    # Current status — pick the latest active stage
    status_files = [
        os.path.join(output_dir, "summary_log", "AUTO_RUN_STATUS.md"),
        os.path.join(output_dir, "verification", "AUTO_RUN_STATUS.md"),
        os.path.join(output_dir, "literature_survey_log", "AUTO_RUN_STATUS.md"),
    ]
    for sf in status_files:
        content = read_file(sf).strip()
        if content:
            rel = _file_link(sf, output_dir)
            with st.expander(f"Current Status  `{rel}`", expanded=True):
                st.markdown(content)
            break

    # Event history — concatenate all stages
    history_files = [
        os.path.join(output_dir, "literature_survey_log", "AUTO_RUN_STATUS.md.history"),
        os.path.join(output_dir, "verification", "AUTO_RUN_STATUS.md.history"),
        os.path.join(output_dir, "summary_log", "AUTO_RUN_STATUS.md.history"),
    ]
    parts = []
    for hf in history_files:
        content = read_file(hf).strip()
        if content:
            parts.append(content)
    if parts:
        history = "\n".join(parts)
        with st.expander("Event History", expanded=True):
            st.code(history, language="text")


# ---------------------------------------------------------------------------
# Stage 0: Survey
# ---------------------------------------------------------------------------

def _render_survey(output_dir: str, scan: dict) -> None:
    """Render literature survey outputs."""
    ri_dir = os.path.join(output_dir, "related_info")
    if not os.path.isdir(ri_dir):
        return

    st.subheader("Stage 0: Literature Survey")

    _show_file("Difficulty Evaluation",
               os.path.join(ri_dir, "difficulty_evaluation.md"), output_dir)
    _show_file("Related Work",
               os.path.join(ri_dir, "related_work.md"), output_dir)
    _show_file("Survey Log (tail)",
               os.path.join(output_dir, "literature_survey_log", "AUTO_RUN_LOG.txt"),
               output_dir, as_code=True)


# ---------------------------------------------------------------------------
# Stage 1: Rounds
# ---------------------------------------------------------------------------

def _step_badge(done: bool, label: str) -> str:
    if done:
        return f":green[{label}: Done]"
    return f":orange[{label}: Pending]"


def _render_model_files(model_dir: str, model_name: str,
                        output_dir: str) -> None:
    """Render all files for a single model within a round."""
    _show_file(f"Proof ({model_name})",
               os.path.join(model_dir, "proof.md"), output_dir)
    _show_file(f"Proof Status ({model_name})",
               os.path.join(model_dir, "proof_status.md"), output_dir)
    _show_file(f"Scratch Pad ({model_name})",
               os.path.join(model_dir, "scratch_pad.md"), output_dir)

    # Structural verification
    s_dir = os.path.join(model_dir, "verification_file", "structural")
    for vf in find_verification_files(s_dir):
        _show_file(f"Structural Verification ({model_name})", vf, output_dir)

    # Detailed verification
    d_dir = os.path.join(model_dir, "verification_file", "detailed")
    for vf in find_verification_files(d_dir):
        _show_file(f"Detailed Verification ({model_name})", vf, output_dir)


def _render_round_human_help(round_dir: str, round_num: int,
                             output_dir: str) -> None:
    """Render guidance used by this round and editable help for the next round."""
    verify_dir = os.path.join(output_dir, "verification")
    global_hh_dir = os.path.join(output_dir, "human_help")

    # --- 1. Guidance used by THIS round's prover/verifier (read-only) ---
    # The pipeline reads: global help + round_{N-1}/human_help/
    with st.expander(
        f"Guidance Used by Round {round_num} (read-only)",
        expanded=False,
    ):
        st.caption(
            f"Round {round_num}'s prover reads the **global** human help "
            f"plus **round {round_num - 1}**'s per-round help."
            if round_num > 1
            else f"Round {round_num}'s prover reads the **global** human help "
                 f"(no previous round)."
        )

        # Global prove help
        global_prove = os.path.join(global_hh_dir, "additional_prove_human_help_global.md")
        global_prove_content = read_file(global_prove).strip()
        st.markdown(f"**Global Prove Guidance** `{_file_link(global_prove, output_dir)}`")
        if global_prove_content:
            st.code(global_prove_content, language="markdown")
        else:
            st.caption("(empty)")

        # Global verify rules
        global_verify = os.path.join(global_hh_dir, "additional_verify_rule_global.md")
        global_verify_content = read_file(global_verify).strip()
        st.markdown(f"**Global Verify Rules** `{_file_link(global_verify, output_dir)}`")
        if global_verify_content:
            st.code(global_verify_content, language="markdown")
        else:
            st.caption("(empty)")

        # Previous round's per-round help (read by this round)
        if round_num > 1:
            prev_hh_dir = os.path.join(verify_dir, f"round_{round_num - 1}", "human_help")
            prev_prove = os.path.join(prev_hh_dir, "additional_prove_human_help_per_round.md")
            prev_verify = os.path.join(prev_hh_dir, "additional_verify_rule_per_round.md")

            prev_prove_content = read_file(prev_prove).strip()
            st.markdown(
                f"**Per-Round Prove Guidance from Round {round_num - 1}** "
                f"`{_file_link(prev_prove, output_dir)}`"
            )
            if prev_prove_content:
                st.code(prev_prove_content, language="markdown")
            else:
                st.caption("(empty)")

            prev_verify_content = read_file(prev_verify).strip()
            st.markdown(
                f"**Per-Round Verify Rules from Round {round_num - 1}** "
                f"`{_file_link(prev_verify, output_dir)}`"
            )
            if prev_verify_content:
                st.code(prev_verify_content, language="markdown")
            else:
                st.caption("(empty)")

    # --- 2. Editable per-round help for the NEXT round ---
    hh_dir = os.path.join(round_dir, "human_help")
    prove_path = os.path.join(hh_dir, "additional_prove_human_help_per_round.md")
    verify_path = os.path.join(hh_dir, "additional_verify_rule_per_round.md")

    prove_rel = _file_link(prove_path, output_dir)
    verify_rel = _file_link(verify_path, output_dir)

    with st.expander(
        f"Human Help for Round {round_num + 1} (editable)  "
        f"`{_file_link(hh_dir, output_dir)}/`",
        expanded=False,
    ):
        st.caption(
            f"This guidance will be read by **round {round_num + 1}**'s prover "
            f"and verifier. Click **Save** to write changes to disk."
        )

        prove_content = read_file(prove_path)
        new_prove = st.text_area(
            f"Prove guidance  `{prove_rel}`",
            value=prove_content,
            height=150,
            key=f"hh_prove_r{round_num}",
        )

        verify_content = read_file(verify_path)
        new_verify = st.text_area(
            f"Verify rules  `{verify_rel}`",
            value=verify_content,
            height=150,
            key=f"hh_verify_r{round_num}",
        )

        if st.button(f"Save Round {round_num} Human Help",
                      key=f"hh_save_r{round_num}"):
            write_file(prove_path, new_prove)
            write_file(verify_path, new_verify)
            st.success(f"Saved human help for round {round_num}.")


def _render_rounds(scan: dict, output_dir: str) -> None:
    """Render the round-by-round timeline with all files."""
    if not scan["rounds"]:
        return

    st.subheader("Stage 1: Proof Loop")

    for r in scan["rounds"]:
        num = r["num"]
        verdict = r["verdict"]
        if verdict == "PASS":
            status_text = "PASS"
        elif verdict == "FAIL":
            status_text = "FAIL"
        elif r["detailed_done"]:
            status_text = "Verified"
        elif r["proof_done"]:
            status_text = "Verifying..."
        else:
            status_text = "In Progress..."

        parallel_tag = " (parallel)" if r["is_parallel"] else ""
        round_dir = os.path.join(output_dir, "verification", f"round_{num}")
        rel_round = _file_link(round_dir, output_dir)

        with st.expander(
            f"Round {num}{parallel_tag} -- {status_text}  `{rel_round}/`",
            expanded=(num == len(scan["rounds"])),
        ):
            # Step badges
            c1, c2, c3 = st.columns(3)
            c1.markdown(_step_badge(r["proof_done"], "Proof Search"))
            c2.markdown(_step_badge(r["structural_done"], "Structural Verify"))
            c3.markdown(_step_badge(r["detailed_done"], "Detailed Verify"))
            if verdict:
                st.markdown(f"**Verdict:** {verdict}")

            # Per-model files (parallel) or single-model files
            if r["is_parallel"]:
                for m in MODEL_PROVIDERS:
                    mdir = os.path.join(round_dir, m)
                    if os.path.isdir(mdir):
                        st.markdown(f"---\n**Model: {m}**")
                        _render_model_files(mdir, m, output_dir)
                # Selection
                _show_file("Selection",
                           os.path.join(round_dir, "selection.md"), output_dir)
            else:
                # Single-model: files are directly in round_dir
                _show_file("Proof",
                           os.path.join(round_dir, "proof.md"), output_dir)
                _show_file("Proof Status",
                           os.path.join(round_dir, "proof_status.md"), output_dir)
                _show_file("Scratch Pad",
                           os.path.join(round_dir, "scratch_pad.md"), output_dir)
                # Verification
                s_dir = os.path.join(round_dir, "verification_file", "structural")
                for vf in find_verification_files(s_dir):
                    _show_file("Structural Verification", vf, output_dir)
                d_dir = os.path.join(round_dir, "verification_file", "detailed")
                for vf in find_verification_files(d_dir):
                    _show_file("Detailed Verification", vf, output_dir)
                # Legacy layout
                for vf in find_verification_files(round_dir):
                    _show_file("Verification", vf, output_dir)

            # Per-round human help — editable
            _render_round_human_help(round_dir, num, output_dir)

    # Proof loop agent logs
    _show_file("Proof Loop Log (tail)",
               os.path.join(output_dir, "verification", "AUTO_RUN_LOG.txt"),
               output_dir, as_code=True)


# ---------------------------------------------------------------------------
# Final proof & summary
# ---------------------------------------------------------------------------

def _render_proof(output_dir: str, scan: dict) -> None:
    """Render the current proof."""
    if not scan["proof_content"]:
        return
    proof_path = os.path.join(output_dir, "proof.md")
    rel = _file_link(proof_path, output_dir)
    with st.expander(f"Current Proof  `{rel}`", expanded=False):
        st.markdown(scan["proof_content"])


def _render_summary(output_dir: str) -> None:
    """Render proof effort summary."""
    _show_file("Proof Effort Summary",
               os.path.join(output_dir, "proof_effort_summary.md"), output_dir)
    _show_file("Summary Log (tail)",
               os.path.join(output_dir, "summary_log", "AUTO_RUN_LOG.txt"),
               output_dir, as_code=True)


# ---------------------------------------------------------------------------
# Token usage
# ---------------------------------------------------------------------------

def _render_token_usage(output_dir: str, scan: dict) -> None:
    """Render token usage from TOKEN_USAGE.md."""
    tu_path = os.path.join(output_dir, "TOKEN_USAGE.md")
    _show_file("Token Usage", tu_path, output_dir)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def render_progress(output_dir: str, run_active: bool = False) -> dict:
    """Main progress rendering function. Returns the scan result dict."""
    scan = scan_progress(output_dir)

    if not scan["exists"]:
        if run_active:
            st.info("Starting pipeline...")
        else:
            st.info("Output directory does not exist yet. Click **Run** to start.")
        return scan

    # Smoke test status (always shown first)
    smoke = render_smoke_test(output_dir, run_active)

    # If smoke test hasn't finished yet, don't render pipeline progress
    if not smoke["finished"]:
        return scan

    # If smoke test failed, stop here
    if not smoke["ok"]:
        return scan

    _render_stage_indicator(scan)
    _render_metrics(scan)
    _render_status_and_history(output_dir)
    _render_survey(output_dir, scan)
    _render_rounds(scan, output_dir)
    _render_proof(output_dir, scan)
    _render_summary(output_dir)
    _render_token_usage(output_dir, scan)

    return scan
