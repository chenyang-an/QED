"""Sidebar configuration panel for decomposition-mode runs."""

import copy

import streamlit as st

from utils import (
    load_config,
    ORIGINAL_CONFIG_PATH,
    MODEL_PROVIDERS,
    AGENT_NAMES,
    PIPELINE_AGENT_NAMES,
    CODEX_EXECUTION_MODES,
    CODEX_REASONING_LEVELS,
    GEMINI_THINKING_LEVELS,
)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def _init_config() -> dict:
    """Load config.yaml once and cache in session state."""
    if "config_disk" not in st.session_state:
        try:
            st.session_state.config_disk = load_config(ORIGINAL_CONFIG_PATH)
        except Exception:
            st.session_state.config_disk = {}
    return st.session_state.config_disk


# ---------------------------------------------------------------------------
# Global provider blocks (adapted from archived config_panel.py)
# ---------------------------------------------------------------------------

def _render_claude_block(claude_cfg: dict) -> dict:
    st.sidebar.subheader("Claude (Anthropic)")
    sub_cfg = claude_cfg.get("subscription", {})
    bed_cfg = claude_cfg.get("bedrock", {})
    api_cfg = claude_cfg.get("api_key", {})

    provider_options = ["subscription", "bedrock", "api_key"]
    current_provider = claude_cfg.get("provider", "api_key")
    if current_provider not in provider_options:
        current_provider = "api_key"
    claude_provider = st.sidebar.selectbox(
        "Authentication",
        provider_options,
        index=provider_options.index(current_provider),
        key="claude_provider",
    )

    sub_model = sub_cfg.get("model", "opus")
    bed_model = bed_cfg.get("model", "us.anthropic.claude-opus-4-6-v1[1m]")
    bed_profile = bed_cfg.get("aws_profile", "default")
    api_model = api_cfg.get("model", "claude-opus-4-6")
    api_key_val = api_cfg.get("key", "")

    if claude_provider == "subscription":
        opts = ["opus", "sonnet", "haiku"]
        cur = sub_model if sub_model in opts else "opus"
        sub_model = st.sidebar.selectbox(
            "Model", opts, index=opts.index(cur), key="claude_sub_model",
        )
    elif claude_provider == "bedrock":
        bed_model = st.sidebar.text_input(
            "Bedrock model ID", value=bed_model, key="claude_bed_model",
        )
        bed_profile = st.sidebar.text_input(
            "AWS profile", value=bed_profile, key="claude_bed_profile",
        )
    else:
        api_model = st.sidebar.text_input(
            "API model", value=api_model, key="claude_api_model",
        )
        api_key_val = st.sidebar.text_input(
            "Anthropic API key", value=api_key_val, type="password",
            key="claude_api_key",
        )

    with st.sidebar.expander("Claude Advanced"):
        cli_path = st.text_input(
            "CLI path", value=claude_cfg.get("cli_path", "claude"),
            key="claude_cli",
        )
        perm_mode = st.text_input(
            "Permission mode",
            value=claude_cfg.get("permission_mode", "bypassPermissions"),
            key="claude_perm",
        )

    return {
        "cli_path": cli_path,
        "permission_mode": perm_mode,
        "provider": claude_provider,
        "subscription": {"model": sub_model},
        "bedrock": {"model": bed_model, "aws_profile": bed_profile},
        "api_key": {"model": api_model, "key": api_key_val},
    }


def _render_codex_block(codex_cfg: dict) -> dict:
    st.sidebar.subheader("Codex (OpenAI)")
    codex_model = st.sidebar.text_input(
        "Model", value=codex_cfg.get("model", "gpt-5.5"),
        key="codex_model",
    )
    cur_effort = codex_cfg.get("reasoning_effort", "xhigh")
    if cur_effort not in CODEX_REASONING_LEVELS:
        cur_effort = "xhigh"
    codex_effort = st.sidebar.selectbox(
        "Reasoning effort", list(CODEX_REASONING_LEVELS),
        index=CODEX_REASONING_LEVELS.index(cur_effort),
        key="codex_effort",
    )
    with st.sidebar.expander("Codex Advanced"):
        codex_cli = st.text_input(
            "CLI path", value=codex_cfg.get("cli_path", "codex"),
            key="codex_cli",
        )
    return {
        "cli_path": codex_cli,
        "model": codex_model,
        "reasoning_effort": codex_effort,
    }


def _render_chatgpt_browser_block(browser_cfg: dict) -> dict:
    st.sidebar.subheader("Codex Browser Mode")
    chatgpt_model = st.sidebar.text_input(
        "ChatGPT model note",
        value=browser_cfg.get("chatgpt_model", "ChatGPT selected model in browser"),
        key="chatgpt_browser_model_note",
    )
    project_context = st.sidebar.text_area(
        "ChatGPT project/context note",
        value=browser_cfg.get("project_context", ""),
        key="chatgpt_browser_project_context",
        height=80,
    )
    with st.sidebar.expander("Codex Browser Advanced"):
        chrome_invocation = st.text_input(
            "Chrome invocation",
            value=browser_cfg.get("chrome_invocation", "@Chrome"),
            key="chatgpt_browser_chrome_invocation",
        )
        max_retries = st.number_input(
            "Max retries",
            min_value=1,
            max_value=10,
            value=int(browser_cfg.get("max_retries", 2)),
            key="chatgpt_browser_max_retries",
        )
        retry_delay = st.number_input(
            "Retry delay seconds",
            min_value=0,
            max_value=300,
            value=int(browser_cfg.get("retry_delay_seconds", 10)),
            key="chatgpt_browser_retry_delay",
        )
        manual_wait = st.number_input(
            "Manual wait seconds",
            min_value=0,
            max_value=86400,
            value=int(browser_cfg.get("manual_wait_seconds", 0)),
            key="chatgpt_browser_manual_wait",
        )
        manual_poll = st.number_input(
            "Manual poll seconds",
            min_value=1,
            max_value=300,
            value=int(browser_cfg.get("manual_poll_seconds", 5)),
            key="chatgpt_browser_manual_poll",
        )

    supervisor = browser_cfg.get("supervisor", {})
    if not isinstance(supervisor, dict):
        supervisor = {}
    return {
        "supervisor": {
            "provider": "codex",
            "model": supervisor.get("model", "gpt-5.5"),
            "reasoning_effort": supervisor.get("reasoning_effort", "xhigh"),
        },
        "browser": browser_cfg.get("browser", "chrome"),
        "chrome_invocation": chrome_invocation,
        "chatgpt_model": chatgpt_model,
        "project_context": project_context,
        "max_retries": int(max_retries),
        "retry_delay_seconds": int(retry_delay),
        "fallback": browser_cfg.get("fallback", "manual"),
        "manual_wait_seconds": int(manual_wait),
        "manual_poll_seconds": int(manual_poll),
    }


def _render_gemini_block(gemini_cfg: dict) -> dict:
    st.sidebar.subheader("Gemini (Google)")
    gemini_model = st.sidebar.text_input(
        "Model", value=gemini_cfg.get("model", "gemini-3.1-pro-preview"),
        key="gemini_model",
    )
    cur_think = gemini_cfg.get("thinking_level", "HIGH")
    if cur_think not in GEMINI_THINKING_LEVELS:
        cur_think = "HIGH"
    gemini_think = st.sidebar.selectbox(
        "Thinking level", list(GEMINI_THINKING_LEVELS),
        index=GEMINI_THINKING_LEVELS.index(cur_think),
        key="gemini_think",
    )
    gemini_api = st.sidebar.text_input(
        "Gemini API key", value=gemini_cfg.get("api_key", ""),
        type="password", key="gemini_api",
    )
    with st.sidebar.expander("Gemini Advanced"):
        gemini_cli = st.text_input(
            "CLI path", value=gemini_cfg.get("cli_path", "gemini"),
            key="gemini_cli",
        )
        gemini_approval = st.text_input(
            "Approval mode",
            value=gemini_cfg.get("approval_mode", "yolo"),
            key="gemini_approval",
        )
    return {
        "cli_path": gemini_cli,
        "model": gemini_model,
        "approval_mode": gemini_approval,
        "thinking_level": gemini_think,
        "api_key": gemini_api,
    }


# ---------------------------------------------------------------------------
# Per-agent override blocks
# ---------------------------------------------------------------------------

_USE_GLOBAL = "(use global)"


def _agent_block(name: str, agent_cfg: dict) -> dict:
    """Render the per-agent override widgets for one agent.

    Returns a dict with at least ``provider`` and the optional ``model``,
    ``reasoning_effort``, ``thinking_level``, ``thinking_budget`` fields
    when the user has set them.
    """
    container = st.container(border=True)
    with container:
        st.markdown(f"**{name.replace('_', ' ').title()}**")
        cur_provider = agent_cfg.get("provider", "codex")
        cur_execution_mode = agent_cfg.get("execution_mode", "direct")
        # Backward compatibility with the earlier provider-level prototype.
        if cur_provider == "chatgpt_browser":
            cur_provider = "codex"
            cur_execution_mode = "browser"
        if cur_provider not in MODEL_PROVIDERS:
            cur_provider = "codex"
        provider = st.selectbox(
            "Provider",
            list(MODEL_PROVIDERS),
            index=MODEL_PROVIDERS.index(cur_provider),
            key=f"agent_{name}_provider",
        )
        model_default = agent_cfg.get("model", "")
        model_value = st.text_input(
            "Model override (blank = use global)",
            value=model_default,
            key=f"agent_{name}_model",
        )
        reasoning_value = None
        thinking_value = None
        thinking_budget = None
        execution_mode = None
        if provider == "codex":
            cur_mode = cur_execution_mode if cur_execution_mode in CODEX_EXECUTION_MODES else "direct"
            execution_mode = st.selectbox(
                "Codex execution",
                list(CODEX_EXECUTION_MODES),
                index=CODEX_EXECUTION_MODES.index(cur_mode),
                key=f"agent_{name}_codex_execution",
            )
            opts = [_USE_GLOBAL, *CODEX_REASONING_LEVELS]
            cur = agent_cfg.get("reasoning_effort", "")
            if cur not in CODEX_REASONING_LEVELS:
                idx = 0
            else:
                idx = 1 + CODEX_REASONING_LEVELS.index(cur)
            reasoning_value = st.selectbox(
                "Reasoning effort",
                opts, index=idx,
                key=f"agent_{name}_reasoning",
            )
        elif provider == "gemini":
            opts = [_USE_GLOBAL, *GEMINI_THINKING_LEVELS]
            cur = agent_cfg.get("thinking_level", "")
            if cur not in GEMINI_THINKING_LEVELS:
                idx = 0
            else:
                idx = 1 + GEMINI_THINKING_LEVELS.index(cur)
            thinking_value = st.selectbox(
                "Thinking level",
                opts, index=idx,
                key=f"agent_{name}_thinking",
            )
            cur_budget = agent_cfg.get("thinking_budget", 0)
            thinking_budget = st.number_input(
                "Thinking budget (0 = use global)",
                min_value=0, max_value=200_000,
                value=int(cur_budget) if isinstance(cur_budget, int) else 0,
                step=1024,
                key=f"agent_{name}_thinking_budget",
            )

    out: dict = {"provider": provider}
    if provider == "codex" and execution_mode:
        out["execution_mode"] = execution_mode
    if model_value.strip():
        out["model"] = model_value.strip()
    if reasoning_value and reasoning_value != _USE_GLOBAL:
        out["reasoning_effort"] = reasoning_value
    if thinking_value and thinking_value != _USE_GLOBAL:
        out["thinking_level"] = thinking_value
    if thinking_budget:
        out["thinking_budget"] = int(thinking_budget)
    return out


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------

def render_config_panel() -> dict:
    """Render the sidebar and return the full assembled config dict."""
    cfg = _init_config()

    st.sidebar.header("Global Provider Defaults")
    claude_block = _render_claude_block(cfg.get("claude", {}))
    codex_block = _render_codex_block(cfg.get("codex", {}))
    chatgpt_browser_block = _render_chatgpt_browser_block(cfg.get("chatgpt_browser", {}))
    gemini_block = _render_gemini_block(cfg.get("gemini", {}))

    st.sidebar.caption("Prover mode: decomposition (only mode supported)")

    # --- Decomposition agents ---
    decomp_cfg = cfg.get("decomposition", {})
    models_cfg = decomp_cfg.get("models", {})

    with st.sidebar.expander("Decomposition Agents", expanded=False):
        max_proof_attempts = st.number_input(
            "max_proof_attempts (REVISE_PROOF)",
            min_value=1, max_value=20,
            value=int(decomp_cfg.get("max_proof_attempts", 4)),
            key="decomp_max_proof_attempts",
        )
        max_revisions = st.number_input(
            "max_revisions (REVISE_PLAN)",
            min_value=1, max_value=20,
            value=int(decomp_cfg.get("max_revisions", 4)),
            key="decomp_max_revisions",
        )
        max_decompositions = st.number_input(
            "max_decompositions (REWRITE)",
            min_value=1, max_value=20,
            value=int(decomp_cfg.get("max_decompositions", 4)),
            key="decomp_max_decompositions",
        )
        decomp_agents = {
            name: _agent_block(name, models_cfg.get(name, {}))
            for name in AGENT_NAMES
        }

    # --- Pipeline (Stage 0 + Stage 2) agents ---
    pipeline_cfg = cfg.get("pipeline", {})
    with st.sidebar.expander("Pipeline Agents (Stage 0 & 2)", expanded=False):
        pipeline_agents = {
            name: _agent_block(name, pipeline_cfg.get(name, {}))
            for name in PIPELINE_AGENT_NAMES
        }

    # --- Assemble final dict; preserve unknown top-level keys ---
    result: dict = copy.deepcopy(cfg) if cfg else {}
    result["claude"] = claude_block
    result["codex"] = codex_block
    result["chatgpt_browser"] = chatgpt_browser_block
    result["gemini"] = gemini_block
    result["prover"] = {"mode": "decomposition"}
    result["pipeline"] = {
        **{name: pipeline_agents[name] for name in PIPELINE_AGENT_NAMES},
    }
    # Preserve any other keys that were originally under pipeline.
    for k, v in pipeline_cfg.items():
        if k not in PIPELINE_AGENT_NAMES:
            result["pipeline"][k] = v
    result["decomposition"] = {
        "max_proof_attempts": int(max_proof_attempts),
        "max_revisions": int(max_revisions),
        "max_decompositions": int(max_decompositions),
        "models": decomp_agents,
    }
    # Preserve other top-level decomposition keys (rare but defensive).
    for k, v in decomp_cfg.items():
        if k not in ("max_proof_attempts", "max_revisions",
                     "max_decompositions", "models"):
            result["decomposition"][k] = v

    return result
