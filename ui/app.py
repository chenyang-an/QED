"""QED — Mathematical Proof Pipeline UI.

Launch with:  streamlit run ui/app.py
"""

import datetime
import os
import sys

# Ensure the ui/ directory is on the import path so sibling modules resolve.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from utils import (
    PROJECT_ROOT,
    DEFAULT_OUTPUT_ROOT,
    read_file,
    write_file,
)

# Helpers to resolve human_help paths inside the output directory
def _prove_hh_path(out_dir: str) -> str:
    return os.path.join(out_dir, "human_help", "additional_prove_human_help_global.md")

def _verify_hh_path(out_dir: str) -> str:
    return os.path.join(out_dir, "human_help", "additional_verify_rule_global.md")

from config_panel import render_config_panel
from progress_monitor import render_progress, scan_progress
from process_manager import (
    start_pipeline,
    kill_pipeline,
    is_alive,
    get_resume_options,
    prepare_resume,
)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="QED Proof Pipeline",
    page_icon="Q",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------

_DEFAULTS = {
    "process": None,
    "output_dir": "",
    "problem_text": "",
    "global_prove_hh": "",
    "global_verify_hh": "",
    "run_active": False,
    "paused_for_hh": False,
    "paused_round": 0,
    "prev_completed_rounds": 0,
    "show_resume": False,
}

for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ---------------------------------------------------------------------------
# Auto-refresh while pipeline is running
# ---------------------------------------------------------------------------

if st.session_state.run_active:
    st_autorefresh(interval=4000, key="auto_refresh")
    # Check if process is still alive
    if not is_alive(st.session_state.process):
        # Close the log file handle
        proc = st.session_state.process
        if proc is not None and hasattr(proc, "_log_fh"):
            try:
                proc._log_fh.close()
            except OSError:
                pass
        st.session_state.run_active = False
        st.session_state.process = None


# ---------------------------------------------------------------------------
# Sidebar: configuration
# ---------------------------------------------------------------------------

config = render_config_panel()


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

st.title("QED -- Mathematical Proof Pipeline")

# ---------------------------------------------------------------------------
# Input section
# ---------------------------------------------------------------------------

st.subheader("Input")

# Output directory with Load button
default_out = os.path.join(
    DEFAULT_OUTPUT_ROOT,
    datetime.datetime.now().strftime("run_%Y%m%d_%H%M%S"),
)
dir_col, load_col = st.columns([4, 1])
with dir_col:
    output_dir = st.text_input(
        "Output directory",
        value=st.session_state.output_dir or default_out,
        key="output_dir_input",
        disabled=st.session_state.run_active,
    )
with load_col:
    st.markdown("")  # vertical spacer to align with text_input
    load_clicked = st.button(
        "Load",
        disabled=st.session_state.run_active,
        use_container_width=True,
    )

# Always sync the typed path back
st.session_state.output_dir = output_dir

# Load existing run data when Load is clicked
if load_clicked:
    out = st.session_state.output_dir
    if out and os.path.isdir(out):
        existing_problem = os.path.join(out, "problem.tex")
        if os.path.exists(existing_problem):
            loaded = read_file(existing_problem)
            if loaded.strip():
                st.session_state.problem_text = loaded
                # Write to the widget key so the text_area picks it up after rerun
                st.session_state.problem_input = loaded
        st.session_state.global_prove_hh = read_file(_prove_hh_path(out))
        st.session_state.prove_hh_input = st.session_state.global_prove_hh
        st.session_state.global_verify_hh = read_file(_verify_hh_path(out))
        st.session_state.verify_hh_input = st.session_state.global_verify_hh
        st.rerun()
    else:
        st.warning("Directory does not exist. Enter a valid path or click Run to create it.")

# Show current output directory
if st.session_state.output_dir and os.path.isdir(st.session_state.output_dir):
    st.caption(f"Current output: `{st.session_state.output_dir}`")

# Problem statement
st.warning(
    "The **problem statement** and **global human help** are locked once the pipeline starts. "
    "To change them, specify a **new** output directory and run the pipeline afresh. "
    "Do not run a new problem on an existing directory."
)
problem_text = st.text_area(
    "Problem statement (LaTeX)",
    value=st.session_state.problem_text,
    height=200,
    key="problem_input",
    disabled=st.session_state.run_active,
)
st.session_state.problem_text = problem_text

# Global human help
with st.expander("Global Human Help", expanded=False):
    prove_hh = st.text_area(
        "Prove guidance (additional_prove_human_help_global.md)",
        value=st.session_state.global_prove_hh,
        height=150,
        key="prove_hh_input",
        disabled=st.session_state.run_active,
    )
    st.session_state.global_prove_hh = prove_hh

    verify_hh = st.text_area(
        "Verify rules (additional_verify_rule_global.md)",
        value=st.session_state.global_verify_hh,
        height=150,
        key="verify_hh_input",
        disabled=st.session_state.run_active,
    )
    st.session_state.global_verify_hh = verify_hh


# ---------------------------------------------------------------------------
# Control bar
# ---------------------------------------------------------------------------

st.divider()

c_run, c_stop, c_resume, c_status = st.columns([1, 1, 1, 2])

with c_run:
    run_clicked = st.button(
        "Run",
        type="primary",
        disabled=st.session_state.run_active or st.session_state.paused_for_hh,
        use_container_width=True,
    )

with c_stop:
    stop_clicked = st.button(
        "Stop",
        disabled=not st.session_state.run_active,
        use_container_width=True,
    )

with c_resume:
    resume_toggle = st.button(
        "Resume From...",
        disabled=st.session_state.run_active or st.session_state.paused_for_hh,
        use_container_width=True,
    )

with c_status:
    if st.session_state.run_active:
        st.info("Pipeline is **running**...")
    elif st.session_state.paused_for_hh:
        st.warning("**Paused** for human help. Edit below and click Continue.")
    elif st.session_state.output_dir and os.path.isdir(st.session_state.output_dir):
        scan = scan_progress(st.session_state.output_dir)
        if scan["pipeline_complete"]:
            st.success("Pipeline **complete**.")
        elif scan["rounds"]:
            st.warning(f"Pipeline **stopped** at round {scan['rounds'][-1]['num']}.")
        else:
            st.markdown("Pipeline **idle**.")
    else:
        st.markdown("Pipeline **idle**.")


# ---------------------------------------------------------------------------
# Handle Run
# ---------------------------------------------------------------------------

if run_clicked:
    if not st.session_state.problem_text.strip():
        st.error("Please enter a problem statement.")
        st.stop()

    out_dir = st.session_state.output_dir
    os.makedirs(out_dir, exist_ok=True)

    # Write problem file into output dir
    problem_file = os.path.join(out_dir, "problem.tex")
    write_file(problem_file, st.session_state.problem_text)

    # Write global human help files into output dir
    write_file(_prove_hh_path(out_dir), st.session_state.global_prove_hh)
    write_file(_verify_hh_path(out_dir), st.session_state.global_verify_hh)

    # Start pipeline
    proc = start_pipeline(problem_file, out_dir, config)
    st.session_state.process = proc
    st.session_state.run_active = True
    st.session_state.show_resume = False
    st.session_state.paused_for_hh = False

    # Capture current round count for pause detection
    init_scan = scan_progress(out_dir)
    st.session_state.prev_completed_rounds = len(init_scan["rounds"])

    st.rerun()


# ---------------------------------------------------------------------------
# Handle Stop
# ---------------------------------------------------------------------------

if stop_clicked:
    kill_pipeline(st.session_state.process)
    st.session_state.run_active = False
    st.session_state.process = None
    st.session_state.show_resume = True
    st.rerun()


# ---------------------------------------------------------------------------
# Handle Resume toggle
# ---------------------------------------------------------------------------

if resume_toggle:
    st.session_state.show_resume = not st.session_state.show_resume

if st.session_state.show_resume and not st.session_state.run_active:
    out_dir = st.session_state.output_dir
    if out_dir and os.path.isdir(out_dir):
        options = get_resume_options(out_dir)
        if options:
            st.subheader("Resume From")
            labels = [o["label"] for o in options]
            choice = st.selectbox("Select resume point", labels, key="resume_choice")
            selected = options[labels.index(choice)]

            if st.button("Resume Pipeline", type="primary"):
                prepare_resume(out_dir, selected["round"], selected["step"])

                # Problem file should already exist in output dir
                problem_file = os.path.join(out_dir, "problem.tex")
                if not os.path.exists(problem_file):
                    write_file(problem_file, st.session_state.problem_text)

                # Write human help into output dir
                write_file(_prove_hh_path(out_dir), st.session_state.global_prove_hh)
                write_file(_verify_hh_path(out_dir), st.session_state.global_verify_hh)

                proc = start_pipeline(problem_file, out_dir, config)
                st.session_state.process = proc
                st.session_state.run_active = True
                st.session_state.show_resume = False
                st.session_state.paused_for_hh = False

                resume_scan = scan_progress(out_dir)
                st.session_state.prev_completed_rounds = len(resume_scan["rounds"])

                st.rerun()
        else:
            st.info("No resume points available.")


# ---------------------------------------------------------------------------
# Per-round human help (paused between rounds)
# ---------------------------------------------------------------------------

if st.session_state.paused_for_hh:
    rnd = st.session_state.paused_round
    out_dir = st.session_state.output_dir
    hh_dir = os.path.join(out_dir, "verification", f"round_{rnd}", "human_help")

    st.subheader(f"Human Help After Round {rnd}")
    st.markdown(
        "Edit guidance below. The proof search agent in the **next round** "
        "will read these files."
    )

    prove_path = os.path.join(hh_dir, "additional_prove_human_help_per_round.md")
    verify_path = os.path.join(hh_dir, "additional_verify_rule_per_round.md")

    per_prove = st.text_area(
        "Prove guidance (per-round)",
        value=read_file(prove_path),
        height=200,
        key="per_prove_hh",
    )
    per_verify = st.text_area(
        "Verify rules (per-round)",
        value=read_file(verify_path),
        height=200,
        key="per_verify_hh",
    )

    col_cont, col_skip = st.columns(2)
    with col_cont:
        if st.button("Continue Pipeline", type="primary", use_container_width=True):
            # Write per-round human help
            write_file(prove_path, per_prove)
            write_file(verify_path, per_verify)

            # Restart pipeline (it auto-resumes)
            problem_file = os.path.join(out_dir, "problem.tex")
            write_file(_prove_hh_path(out_dir), st.session_state.global_prove_hh)
            write_file(_verify_hh_path(out_dir), st.session_state.global_verify_hh)

            proc = start_pipeline(problem_file, out_dir, config)
            st.session_state.process = proc
            st.session_state.run_active = True
            st.session_state.paused_for_hh = False

            scan = scan_progress(out_dir)
            st.session_state.prev_completed_rounds = len(scan["rounds"])

            st.rerun()

    with col_skip:
        if st.button("Continue Without Editing", use_container_width=True):
            problem_file = os.path.join(out_dir, "problem.tex")
            write_file(_prove_hh_path(out_dir), st.session_state.global_prove_hh)
            write_file(_verify_hh_path(out_dir), st.session_state.global_verify_hh)

            proc = start_pipeline(problem_file, out_dir, config)
            st.session_state.process = proc
            st.session_state.run_active = True
            st.session_state.paused_for_hh = False

            scan = scan_progress(out_dir)
            st.session_state.prev_completed_rounds = len(scan["rounds"])

            st.rerun()


# ---------------------------------------------------------------------------
# Progress section
# ---------------------------------------------------------------------------

st.divider()

out_dir = st.session_state.output_dir
if out_dir and os.path.isdir(out_dir):
    scan = render_progress(out_dir, run_active=st.session_state.run_active)

    # Detect round completion for human help pause
    if st.session_state.run_active and not st.session_state.paused_for_hh:
        completed_rounds = len([
            r for r in scan["rounds"]
            if r["detailed_done"] or r["verdict"]
        ])
        prev = st.session_state.prev_completed_rounds

        if completed_rounds > prev and scan["current_stage"] == "proof_loop":
            # A new round just completed — pause for human help
            kill_pipeline(st.session_state.process)
            st.session_state.run_active = False
            st.session_state.process = None
            st.session_state.paused_for_hh = True
            st.session_state.paused_round = scan["rounds"][-1]["num"]
            st.session_state.prev_completed_rounds = completed_rounds
            st.rerun()
