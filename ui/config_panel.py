"""Sidebar configuration panel for the QED Streamlit UI."""

import streamlit as st

from utils import load_config, ORIGINAL_CONFIG_PATH, MODEL_PROVIDERS


def _init_config() -> dict:
    """Load config from disk on first run, cache in session state."""
    if "config" not in st.session_state:
        try:
            st.session_state.config = load_config(ORIGINAL_CONFIG_PATH)
        except Exception:
            st.session_state.config = {}
    return st.session_state.config


def _enabled_providers() -> list[str]:
    """Return list of provider names whose toggle is on."""
    providers = []
    if st.session_state.get("use_claude", True):
        providers.append("claude")
    if st.session_state.get("use_codex", False):
        providers.append("codex")
    if st.session_state.get("use_gemini", False):
        providers.append("gemini")
    return providers


def _filter_providers(selected: list[str], available: list[str]) -> list[str]:
    """Remove providers that are no longer enabled."""
    return [p for p in selected if p in available]


def render_config_panel() -> dict:
    """Render the sidebar configuration form and return the full config dict."""
    cfg = _init_config()
    pipeline_cfg = cfg.get("pipeline", {})
    claude_cfg = cfg.get("claude", {})
    codex_cfg = cfg.get("codex", {})
    gemini_cfg = cfg.get("gemini", {})

    st.sidebar.header("Model Providers")

    # --- Provider toggles ---
    st.sidebar.checkbox(
        "Claude (Anthropic)",
        value=st.session_state.get("use_claude", True),
        key="use_claude",
    )
    st.sidebar.checkbox(
        "Codex (OpenAI)",
        value=st.session_state.get("use_codex", False),
        key="use_codex",
    )
    st.sidebar.checkbox(
        "Gemini (Google)",
        value=st.session_state.get("use_gemini", False),
        key="use_gemini",
    )

    enabled = _enabled_providers()
    if not enabled:
        st.sidebar.error("At least one provider must be enabled.")

    # --- Claude settings ---
    sub_cfg = claude_cfg.get("subscription", {})
    bed_cfg = claude_cfg.get("bedrock", {})
    api_cfg = claude_cfg.get("api_key", {})

    if "claude" in enabled:
        st.sidebar.subheader("Claude")
        provider_options = ["subscription", "bedrock", "api_key"]
        current_provider = claude_cfg.get("provider", "bedrock")
        if current_provider not in provider_options:
            current_provider = "bedrock"
        claude_provider = st.sidebar.selectbox(
            "Authentication",
            provider_options,
            index=provider_options.index(current_provider),
            key="claude_provider",
        )

        if claude_provider == "subscription":
            model_opts = ["opus", "sonnet", "haiku"]
            cur = sub_cfg.get("model", "opus")
            if cur not in model_opts:
                cur = "opus"
            sub_model = st.sidebar.selectbox(
                "Model", model_opts, index=model_opts.index(cur), key="claude_sub_model"
            )
        elif claude_provider == "bedrock":
            bed_model = st.sidebar.text_input(
                "Model ID",
                value=bed_cfg.get("model", "us.anthropic.claude-opus-4-6-v1"),
                key="claude_bed_model",
            )
            bed_profile = st.sidebar.text_input(
                "AWS Profile",
                value=bed_cfg.get("aws_profile", "default"),
                key="claude_bed_profile",
            )
        else:  # api_key
            api_model = st.sidebar.text_input(
                "Model ID",
                value=api_cfg.get("model", "claude-opus-4-6"),
                key="claude_api_model",
            )
            api_key_val = st.sidebar.text_input(
                "API Key",
                value=api_cfg.get("key", ""),
                type="password",
                key="claude_api_key",
            )

        with st.sidebar.expander("Claude Advanced"):
            cli_path = st.text_input(
                "CLI path",
                value=claude_cfg.get("cli_path", "claude"),
                key="claude_cli",
            )
            perm_mode = st.text_input(
                "Permission mode",
                value=claude_cfg.get("permission_mode", "bypassPermissions"),
                key="claude_perm",
            )

    # --- Codex settings ---
    if "codex" in enabled:
        st.sidebar.subheader("Codex (OpenAI)")
        codex_model = st.sidebar.text_input(
            "Model",
            value=codex_cfg.get("model", "gpt-5.4"),
            key="codex_model",
        )
        effort_opts = ["xhigh", "high", "medium", "low"]
        cur_effort = codex_cfg.get("reasoning_effort", "xhigh")
        if cur_effort not in effort_opts:
            cur_effort = "xhigh"
        codex_effort = st.sidebar.selectbox(
            "Reasoning effort",
            effort_opts,
            index=effort_opts.index(cur_effort),
            key="codex_effort",
        )
        with st.sidebar.expander("Codex Advanced"):
            codex_cli = st.text_input(
                "CLI path",
                value=codex_cfg.get("cli_path", "codex"),
                key="codex_cli",
            )

    # --- Gemini settings ---
    if "gemini" in enabled:
        st.sidebar.subheader("Gemini (Google)")
        gemini_model = st.sidebar.text_input(
            "Model",
            value=gemini_cfg.get("model", "gemini-3.1-pro-preview"),
            key="gemini_model",
        )
        think_opts = ["HIGH", "MEDIUM", "LOW", "NONE"]
        cur_think = gemini_cfg.get("thinking_level", "HIGH")
        if cur_think not in think_opts:
            cur_think = "HIGH"
        gemini_think = st.sidebar.selectbox(
            "Thinking level",
            think_opts,
            index=think_opts.index(cur_think),
            key="gemini_think",
        )
        gemini_api = st.sidebar.text_input(
            "API Key",
            value=gemini_cfg.get("api_key", ""),
            type="password",
            key="gemini_api",
        )
        with st.sidebar.expander("Gemini Advanced"):
            gemini_cli = st.text_input(
                "CLI path",
                value=gemini_cfg.get("cli_path", "gemini"),
                key="gemini_cli",
            )
            gemini_approval = st.text_input(
                "Approval mode",
                value=gemini_cfg.get("approval_mode", "yolo"),
                key="gemini_approval",
            )

    # --- Pipeline settings ---
    st.sidebar.divider()
    st.sidebar.header("Pipeline Settings")

    max_iter = st.sidebar.number_input(
        "Max proof iterations",
        min_value=1,
        max_value=20,
        value=int(pipeline_cfg.get("max_proof_iterations", 9)),
        key="max_iter",
    )

    with st.sidebar.expander("Multi-model & Verification"):
        mm_cfg = pipeline_cfg.get("multi_model", {})
        mm_enabled = st.checkbox(
            "Multi-model proof search",
            value=mm_cfg.get("enabled", False),
            key="mm_enabled",
        )
        mm_providers = st.multiselect(
            "Proof search providers",
            options=enabled,
            default=_filter_providers(
                mm_cfg.get("providers", ["claude"]), enabled
            ),
            key="mm_providers",
        )

        va_cfg = pipeline_cfg.get("verification_agents", {})
        va_enabled = st.checkbox(
            "Multi-model verification",
            value=va_cfg.get("enabled", True),
            key="va_enabled",
        )
        va_providers = st.multiselect(
            "Verification providers",
            options=enabled,
            default=_filter_providers(
                va_cfg.get("providers", ["claude"]), enabled
            ),
            key="va_providers",
        )

        ps_cfg = pipeline_cfg.get("proof_select", {})
        ps_provider = st.selectbox(
            "Proof selector",
            options=enabled,
            index=max(0, enabled.index(ps_cfg.get("provider", "claude")) if ps_cfg.get("provider", "claude") in enabled else 0),
            key="ps_provider",
        )

    with st.sidebar.expander("Brainstorm & Other"):
        bs_cfg = pipeline_cfg.get("brainstorm", {})
        bs_enabled = st.checkbox(
            "Brainstorm session",
            value=bs_cfg.get("enabled", False),
            key="bs_enabled",
        )
        bs_providers = st.multiselect(
            "Brainstorm providers",
            options=enabled,
            default=_filter_providers(
                bs_cfg.get("providers", ["claude"]), enabled
            ),
            key="bs_providers",
        )

        ls_cfg = pipeline_cfg.get("literature_survey", {})
        ls_provider = st.selectbox(
            "Literature survey provider",
            options=enabled,
            index=max(0, enabled.index(ls_cfg.get("provider", "claude")) if ls_cfg.get("provider", "claude") in enabled else 0),
            key="ls_provider",
        )

        ps_sum_cfg = pipeline_cfg.get("proof_summary", {})
        ps_sum_provider = st.selectbox(
            "Summary provider",
            options=enabled,
            index=max(0, enabled.index(ps_sum_cfg.get("provider", "claude")) if ps_sum_cfg.get("provider", "claude") in enabled else 0),
            key="ps_sum_provider",
        )

    # --- Build and return the full config dict ---
    default_provider = enabled[0] if enabled else "claude"

    result = {
        "pipeline": {
            "max_proof_iterations": int(st.session_state.max_iter),
            "multi_model": {
                "enabled": st.session_state.mm_enabled,
                "providers": st.session_state.mm_providers or [default_provider],
            },
            "verification_agents": {
                "enabled": st.session_state.va_enabled,
                "providers": st.session_state.va_providers or [default_provider],
            },
            "proof_select": {
                "provider": st.session_state.ps_provider,
            },
            "brainstorm": {
                "enabled": st.session_state.bs_enabled,
                "providers": st.session_state.bs_providers or [default_provider],
            },
            "literature_survey": {
                "provider": st.session_state.ls_provider,
            },
            "proof_summary": {
                "provider": st.session_state.ps_sum_provider,
            },
        },
        "claude": {
            "cli_path": st.session_state.get("claude_cli", claude_cfg.get("cli_path", "claude")),
            "permission_mode": st.session_state.get("claude_perm", claude_cfg.get("permission_mode", "bypassPermissions")),
            "provider": st.session_state.get("claude_provider", claude_cfg.get("provider", "bedrock")),
            "subscription": {
                "model": st.session_state.get("claude_sub_model", sub_cfg.get("model", "opus")),
            },
            "bedrock": {
                "model": st.session_state.get("claude_bed_model", bed_cfg.get("model", "us.anthropic.claude-opus-4-6-v1")),
                "aws_profile": st.session_state.get("claude_bed_profile", bed_cfg.get("aws_profile", "default")),
            },
            "api_key": {
                "model": st.session_state.get("claude_api_model", api_cfg.get("model", "claude-opus-4-6")),
                "key": st.session_state.get("claude_api_key", api_cfg.get("key", "")),
            },
        },
        "codex": {
            "cli_path": st.session_state.get("codex_cli", codex_cfg.get("cli_path", "codex")),
            "model": st.session_state.get("codex_model", codex_cfg.get("model", "gpt-5.4")),
            "reasoning_effort": st.session_state.get("codex_effort", codex_cfg.get("reasoning_effort", "xhigh")),
        },
        "gemini": {
            "cli_path": st.session_state.get("gemini_cli", gemini_cfg.get("cli_path", "gemini")),
            "model": st.session_state.get("gemini_model", gemini_cfg.get("model", "gemini-3.1-pro-preview")),
            "approval_mode": st.session_state.get("gemini_approval", gemini_cfg.get("approval_mode", "yolo")),
            "thinking_level": st.session_state.get("gemini_think", gemini_cfg.get("thinking_level", "HIGH")),
            "api_key": st.session_state.get("gemini_api", gemini_cfg.get("api_key", "")),
        },
    }

    st.session_state.config = result
    return result
