#!/usr/bin/env python3
"""Unified multi-model runner for Claude, Codex, Gemini, and ChatGPT browser.

Provides async wrappers around each provider's CLI, returning response text
and feeding token usage into the pipeline's TokenTracker.

Claude, Codex, and Gemini are invoked via their respective CLIs (subprocess),
wrapped in ``asyncio`` executors so the main event loop stays non-blocking.
The ChatGPT browser provider is a Codex-supervised bridge: Codex handles the
local QED task structure and delegates full QED agent steps to ChatGPT via
Chrome when available, with a manual file handoff fallback.
"""

import asyncio
import json
import os
import subprocess
import tempfile
import time
import re
import hashlib
from datetime import datetime


class ModelRunnerError(Exception):
    """Raised when a model runner encounters a fatal error.

    Attributes:
        provider: The model provider (claude, codex, gemini, chatgpt_browser).
        error_type: Category of error (subprocess_error, non_zero_exit, json_parse_error, empty_response).
        message: Human-readable error message.
        exit_code: Process exit code (if applicable).
        stderr: Stderr output from the CLI (if any).
        stdout: Raw stdout (for debugging).
    """

    def __init__(
        self,
        provider: str,
        error_type: str,
        message: str,
        exit_code: int | None = None,
        stderr: str = "",
        stdout: str = "",
    ):
        self.provider = provider
        self.error_type = error_type
        self.exit_code = exit_code
        self.stderr = stderr
        self.stdout = stdout
        super().__init__(message)

    def __str__(self):
        parts = [f"[{self.provider}] {self.error_type}: {self.args[0]}"]
        if self.exit_code is not None:
            parts.append(f"exit_code={self.exit_code}")
        if self.stderr:
            # Truncate stderr for display
            stderr_preview = self.stderr[:500] + ("..." if len(self.stderr) > 500 else "")
            parts.append(f"stderr={stderr_preview!r}")
        return " | ".join(parts)

    def full_details(self) -> str:
        """Return full error details for logging to file."""
        lines = [
            f"# Model Runner Error",
            f"",
            f"**Provider:** {self.provider}",
            f"**Error Type:** {self.error_type}",
            f"**Message:** {self.args[0]}",
        ]
        if self.exit_code is not None:
            lines.append(f"**Exit Code:** {self.exit_code}")
        if self.stderr:
            lines.extend(["", "## Stderr", "```", self.stderr, "```"])
        if self.stdout:
            lines.extend(["", "## Stdout (first 2000 chars)", "```", self.stdout[:2000], "```"])
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Claude wrapper
# ---------------------------------------------------------------------------

async def run_claude_agent(
    prompt: str,
    working_dir: str,
    claude_opts: dict,
    logger=None,
    tracker=None,
    call_name: str = "",
    instructions: str | None = None,
) -> str:
    """Run the Claude CLI as a proof-search agent. Returns response text.

    Args:
        prompt: The full prompt string to send.
        working_dir: Directory the agent operates in (cwd for subprocess).
        claude_opts: Dict with keys: cli_path, model, env.
        logger: Optional PipelineLogger for streaming output.
        tracker: Optional TokenTracker for recording token usage.
        call_name: Human-readable label for this call.
        instructions: Optional system prompt to append.
    """
    cli_path = claude_opts.get("cli_path", "claude")
    model = claude_opts.get("model", "opus")
    extra_env = claude_opts.get("env", {})

    cmd = [
        cli_path,
        "-p",
        "--output-format", "json",
        "--dangerously-skip-permissions",
        "--model", model,
    ]
    if instructions:
        cmd += ["--append-system-prompt", instructions]
    cmd.append(prompt)

    # Build environment: start from inherited env, strip vars that cause
    # provider cross-contamination, then add back only the configured ones.
    _PROVIDER_VARS = ("CLAUDE_CODE_USE_BEDROCK", "ANTHROPIC_API_KEY",
                      "AWS_PROFILE", "ANTHROPIC_MODEL")
    env = {k: v for k, v in os.environ.items() if k not in _PROVIDER_VARS}
    env.update(extra_env)

    def _call():
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=working_dir,
            env=env,
        )

    MAX_RETRIES = 3
    RETRY_BACKOFF = [30, 60, 120]  # seconds between retries

    start = datetime.now()
    if logger:
        logger.log(f"[Claude] Starting {call_name} (model={model})")

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        attempt_start = datetime.now()

        try:
            result = await asyncio.get_event_loop().run_in_executor(None, _call)
        except Exception as exc:
            elapsed = (datetime.now() - attempt_start).total_seconds()
            if logger:
                logger.log(f"[Claude] EXCEPTION (attempt {attempt}/{MAX_RETRIES}): "
                           f"{type(exc).__name__}: {exc}")
            last_error = ModelRunnerError(
                provider="claude",
                error_type="subprocess_error",
                message=f"Failed to execute Claude CLI: {type(exc).__name__}: {exc}",
            )
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF[attempt - 1]
                if logger:
                    logger.log(f"[Claude] Retrying in {wait}s...")
                await asyncio.sleep(wait)
                continue
            if tracker:
                tracker.record(call_name or "claude", 0, 0,
                               (datetime.now() - start).total_seconds(),
                               provider="claude", model=model)
            raise last_error

        elapsed = (datetime.now() - attempt_start).total_seconds()

        # Log stderr if present (contains error messages from CLI)
        if result.stderr and result.stderr.strip() and logger:
            logger.log(f"[Claude] stderr:\n{result.stderr.strip()}")

        # --- Parse JSON output ---
        response = ""
        input_tokens = 0
        output_tokens = 0
        json_parse_error = None

        try:
            data = json.loads(result.stdout)
            response = data.get("result", "")

            for _, model_stats in data.get("modelUsage", {}).items():
                input_tokens += model_stats.get("inputTokens", 0)
                output_tokens += model_stats.get("outputTokens", 0)
        except (json.JSONDecodeError, ValueError) as exc:
            json_parse_error = str(exc)
            if logger:
                logger.log(f"[Claude] JSON parse error: {exc}")
                if result.stdout.strip():
                    logger.log(f"[Claude] Raw stdout (first 1000 chars): {result.stdout.strip()[:1000]}")
            response = result.stdout.strip()

        # Check for non-zero exit code (indicates CLI failure) — retryable
        if result.returncode != 0:
            if logger:
                logger.log(f"[Claude] Non-zero exit code: {result.returncode} "
                           f"(attempt {attempt}/{MAX_RETRIES})")
            last_error = ModelRunnerError(
                provider="claude",
                error_type="non_zero_exit",
                message=f"Claude CLI exited with code {result.returncode}",
                exit_code=result.returncode,
                stderr=result.stderr,
                stdout=result.stdout,
            )
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF[attempt - 1]
                if logger:
                    logger.log(f"[Claude] Retrying in {wait}s...")
                await asyncio.sleep(wait)
                continue
            if tracker:
                tracker.record(call_name or "claude", input_tokens, output_tokens,
                               (datetime.now() - start).total_seconds(),
                               provider="claude", model=model)
            raise last_error

        # Check for empty response (might indicate silent failure) — retryable
        if not response.strip():
            if logger:
                logger.log(f"[Claude] Empty response received "
                           f"(attempt {attempt}/{MAX_RETRIES})")
            last_error = ModelRunnerError(
                provider="claude",
                error_type="empty_response",
                message="Claude returned empty response" + (f" (JSON parse error: {json_parse_error})" if json_parse_error else ""),
                exit_code=result.returncode,
                stderr=result.stderr,
                stdout=result.stdout,
            )
            if attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF[attempt - 1]
                if logger:
                    logger.log(f"[Claude] Retrying in {wait}s...")
                await asyncio.sleep(wait)
                continue
            if tracker:
                tracker.record(call_name or "claude", input_tokens, output_tokens,
                               (datetime.now() - start).total_seconds(),
                               provider="claude", model=model)
            raise last_error

        # Success — break out of retry loop
        if attempt > 1 and logger:
            logger.log(f"[Claude] Succeeded on attempt {attempt}")
        break

    total_elapsed = (datetime.now() - start).total_seconds()
    if logger:
        logger.log(f"[Claude] Completed {call_name} in {total_elapsed:.0f}s "
                    f"({input_tokens} in / {output_tokens} out)")

    if tracker:
        tracker.record(call_name or "claude", input_tokens, output_tokens,
                       total_elapsed, provider="claude", model=model)

    return response


# ---------------------------------------------------------------------------
# ChatGPT browser bridge (Codex-supervised)
# ---------------------------------------------------------------------------

def _safe_name(name: str) -> str:
    """Return a filesystem-safe label for logs and handoff directories."""
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", name.strip())
    return cleaned.strip("._") or "agent_call"


def _write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _build_chatgpt_browser_supervisor_prompt(
    *,
    original_prompt: str,
    run_dir: str,
    call_name: str,
    cfg: dict,
) -> str:
    chatgpt_model = cfg.get("chatgpt_model", "the currently selected ChatGPT model in the browser")
    chrome_invocation = cfg.get("chrome_invocation", "@Chrome")
    project_context = str(cfg.get("project_context", "") or "").strip()
    manual_prompt_file = os.path.join(run_dir, "manual_prompt.md")
    manual_response_file = os.path.join(run_dir, "manual_response.md")
    final_response_file = os.path.join(run_dir, "final_response.md")
    scratch_file = os.path.join(run_dir, "chatgpt_step_transcript.md")
    project_instruction = ""
    if project_context:
        project_instruction = (
            "\nProject/context note for ChatGPT:\n\n"
            f"```text\n{project_context}\n```\n"
        )

    return f"""# Codex-supervised ChatGPT browser provider

You are the Codex supervisor for QED agent call `{call_name}`.

Your job is NOT to solve the mathematical step yourself unless needed for
format checking. Your job is to delegate the whole current QED agent step to
ChatGPT and supervise the result.

1. Read the original QED agent prompt below.
2. Use {chrome_invocation} with the user's logged-in ChatGPT page when available.
3. Ask ChatGPT to use `{chatgpt_model}` if the UI exposes that model.
4. If ChatGPT Projects are available and the configured project/context note
   identifies one, use the relevant project or include that note in the prompt.
5. Send ChatGPT the full QED agent prompt as one task. Do not break it into
   small atomic questions unless ChatGPT itself chooses that as internal
   reasoning.
6. Ask ChatGPT to return the final answer in exactly the format required by
   the QED prompt.
7. Check ChatGPT's answer for consistency, formatting, relevance, and whether
   it satisfies the original output contract.
8. Return the final answer required by the original QED prompt.

Important constraints:

- Preserve the original QED output contract. If the original prompt asks for a specific Markdown or YAML file, write that file.
- If the original prompt asks for YAML, the final content must be valid YAML with no extra prose around it.
- If the original prompt asks for Markdown, use the section structure requested by that prompt.
- Keep a concise transcript of the ChatGPT prompt and response in `{scratch_file}`.
- Write your final returned answer to `{final_response_file}` as well as any output file required by the original prompt.
- If Chrome or ChatGPT browser access is unavailable, write a manual handoff prompt to `{manual_prompt_file}` explaining exactly what the user should paste into ChatGPT, and state that the expected reply should be saved to `{manual_response_file}`.
- If you use the manual handoff path, do not invent the math answer yourself. Return a clear message beginning with `MANUAL_CHATGPT_REQUIRED`.

ChatGPT prompt guidance:

- Treat the QED prompt below as the complete task for this step.
- Use any project-level context available in ChatGPT if relevant.
- Return only the final answer expected by the QED prompt.
- Do not include wrapper commentary before or after the requested output.
{project_instruction}

Original QED agent prompt:

```text
{original_prompt}
```
"""


def _build_manual_handoff_prompt(
    *,
    original_prompt: str,
    call_name: str,
    cfg: dict,
) -> str:
    chatgpt_model = cfg.get("chatgpt_model", "the currently selected ChatGPT model in the browser")
    project_context = str(cfg.get("project_context", "") or "").strip()
    project_section = ""
    if project_context:
        project_section = f"""
Project/context note:

```text
{project_context}
```
"""
    return f"""# Manual ChatGPT handoff for QED

Call: `{call_name}`
Preferred ChatGPT model: `{chatgpt_model}`
{project_section}

Please paste the task below into ChatGPT as one complete QED step. If ChatGPT
Projects are available and the project/context note identifies one, use that
project or include the note in the prompt.

Ask ChatGPT to return the final answer in exactly the format required by the
QED task. Do not add wrapper commentary before or after the final answer.

Suggested instruction to ChatGPT:

```text
You are helping a QED proof pipeline. Treat the following QED prompt as one
complete agent step. Solve the requested step carefully, using any available
project-level context if relevant. Then produce the final output required by
the pipeline prompt exactly, preserving any requested YAML or Markdown format.
If YAML is requested, output only valid YAML. If Markdown is requested, use the
requested headings only.
```

QED task:

```text
{original_prompt}
```
"""


async def run_chatgpt_browser_agent(
    prompt: str,
    working_dir: str,
    full_config: dict,
    logger=None,
    tracker=None,
    call_name: str = "",
) -> str:
    """Run a Codex-supervised ChatGPT browser bridge.

    This provider keeps Codex responsible for QED orchestration and file I/O,
    while directing Codex to delegate the full current QED agent step to
    ChatGPT via Chrome. If automatic browser delegation fails, it writes a manual handoff
    prompt and optionally waits for ``manual_response.md``.
    """
    cfg = full_config.get("chatgpt_browser", {})
    codex_base = dict(full_config.get("codex", {}))
    supervisor_cfg = dict(cfg.get("supervisor", {}))
    if supervisor_cfg.get("provider", "codex") != "codex":
        raise ValueError("chatgpt_browser.supervisor.provider must be 'codex'.")

    codex_cfg = {**codex_base, **{k: v for k, v in supervisor_cfg.items() if k != "provider"}}
    max_retries = int(cfg.get("max_retries", 2))
    retry_delay = float(cfg.get("retry_delay_seconds", 10))
    manual_wait_seconds = float(cfg.get("manual_wait_seconds", 0))
    manual_poll_seconds = max(1.0, float(cfg.get("manual_poll_seconds", 5)))
    fallback = cfg.get("fallback", "manual")

    safe_call = _safe_name(call_name or "chatgpt_browser")
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
    run_dir = os.path.join(working_dir, "chatgpt_browser_runs", f"{safe_call}_{prompt_hash}")
    os.makedirs(run_dir, exist_ok=True)

    original_prompt_file = os.path.join(run_dir, "original_qed_prompt.md")
    supervisor_prompt_file = os.path.join(run_dir, "supervisor_prompt.md")
    manual_prompt_file = os.path.join(run_dir, "manual_prompt.md")
    manual_response_file = os.path.join(run_dir, "manual_response.md")
    status_file = os.path.join(run_dir, "STATUS.md")
    error_file = os.path.join(run_dir, "error.md")

    existing_manual_response = _read_text(manual_response_file).strip()
    if existing_manual_response:
        if logger:
            logger.log(f"[ChatGPT Browser] Using existing manual response for {call_name}: {manual_response_file}")
        if tracker:
            tracker.record(
                call_name or "chatgpt_browser_manual_resume",
                0,
                0,
                0,
                provider="chatgpt_browser",
                model=cfg.get("chatgpt_model", "ChatGPT browser selected model"),
            )
        return existing_manual_response

    _write_text(original_prompt_file, prompt)
    _write_text(
        manual_prompt_file,
        _build_manual_handoff_prompt(
            original_prompt=prompt,
            call_name=call_name or "chatgpt_browser",
            cfg=cfg,
        ),
    )

    supervisor_prompt = _build_chatgpt_browser_supervisor_prompt(
        original_prompt=prompt,
        run_dir=run_dir,
        call_name=call_name or "chatgpt_browser",
        cfg=cfg,
    )
    _write_text(supervisor_prompt_file, supervisor_prompt)
    _write_text(
        status_file,
        f"# ChatGPT Browser Run\n\nState: STARTING\nCall: {call_name}\n"
        f"Started: {datetime.now().isoformat()}\nPrompt hash: {prompt_hash}\n",
    )

    start = datetime.now()
    if logger:
        logger.log(f"[ChatGPT Browser] Starting {call_name}; run_dir={run_dir}")

    last_error = None
    response = ""
    for attempt in range(1, max_retries + 1):
        _write_text(
            status_file,
            f"# ChatGPT Browser Run\n\nState: AUTO_CHROME_ATTEMPT\n"
            f"Call: {call_name}\nAttempt: {attempt} / {max_retries}\n"
            f"Manual prompt: {manual_prompt_file}\nManual response: {manual_response_file}\n",
        )
        try:
            response = await run_codex_agent(
                supervisor_prompt,
                working_dir,
                codex_cfg,
                logger=logger,
                tracker=tracker,
                call_name=f"{call_name or 'chatgpt_browser'}_codex_supervisor",
            )
            if response.strip() and not response.lstrip().startswith("MANUAL_CHATGPT_REQUIRED"):
                elapsed = (datetime.now() - start).total_seconds()
                if logger:
                    logger.log(f"[ChatGPT Browser] Completed {call_name} in {elapsed:.0f}s")
                _write_text(
                    status_file,
                    f"# ChatGPT Browser Run\n\nState: COMPLETED\nCall: {call_name}\n",
                )
                return response
            last_error = ModelRunnerError(
                provider="chatgpt_browser",
                error_type="manual_required",
                message="Codex supervisor reported that manual ChatGPT handoff is required.",
                stdout=response,
            )
        except ModelRunnerError as exc:
            last_error = exc
            _write_text(error_file, exc.full_details())
            if logger:
                logger.log(f"[ChatGPT Browser] Attempt {attempt}/{max_retries} failed: {exc}")

        if attempt < max_retries:
            await asyncio.sleep(retry_delay)

    if fallback != "manual":
        raise ModelRunnerError(
            provider="chatgpt_browser",
            error_type="auto_chrome_failed",
            message=f"Automatic Chrome delegation failed; fallback={fallback!r}. See {run_dir}",
            stdout=response,
        )

    _write_text(
        status_file,
        f"# ChatGPT Browser Run\n\nState: WAITING_FOR_MANUAL_RESPONSE\n"
        f"Call: {call_name}\nManual prompt: {manual_prompt_file}\n"
        f"Manual response: {manual_response_file}\n"
        f"Wait seconds: {manual_wait_seconds}\n",
    )
    if logger:
        logger.log(
            f"[ChatGPT Browser] Automatic path failed. Manual prompt is at {manual_prompt_file}; "
            f"save ChatGPT output to {manual_response_file}."
        )

    if manual_wait_seconds > 0:
        deadline = time.time() + manual_wait_seconds
        while time.time() < deadline:
            manual_response = _read_text(manual_response_file).strip()
            if manual_response:
                elapsed = (datetime.now() - start).total_seconds()
                if tracker:
                    tracker.record(
                        call_name or "chatgpt_browser_manual",
                        0,
                        0,
                        elapsed,
                        provider="chatgpt_browser",
                        model=cfg.get("chatgpt_model", "ChatGPT browser selected model"),
                    )
                _write_text(
                    status_file,
                    f"# ChatGPT Browser Run\n\nState: COMPLETED_MANUAL\nCall: {call_name}\n",
                )
                return manual_response
            await asyncio.sleep(manual_poll_seconds)

    message = (
        "ChatGPT browser provider could not complete automatically. "
        f"Manual prompt: {manual_prompt_file}. "
        f"Save the ChatGPT answer to: {manual_response_file}. "
        "Then rerun/resume the pipeline."
    )
    if last_error:
        message += f"\nLast automatic error: {last_error}"
    raise ModelRunnerError(
        provider="chatgpt_browser",
        error_type="manual_response_required",
        message=message,
        stdout=response,
    )


# ---------------------------------------------------------------------------
# Codex wrapper
# ---------------------------------------------------------------------------

async def run_codex_agent(
    prompt: str,
    working_dir: str,
    codex_config: dict,
    logger=None,
    tracker=None,
    call_name: str = "",
) -> str:
    """Run the Codex CLI as a proof-search agent. Returns response text.

    Args:
        prompt: The full prompt string to send.
        working_dir: Directory the agent operates in (cwd for subprocess).
        codex_config: Dict with keys: cli_path, model, reasoning_effort.
        logger: Optional PipelineLogger for streaming output.
        tracker: Optional TokenTracker for recording token usage.
        call_name: Human-readable label for this call.
    """
    cli_path = codex_config.get("cli_path", "codex")
    model = codex_config.get("model", "gpt-5.5")
    reasoning = codex_config.get("reasoning_effort", "xhigh")

    cmd = [
        cli_path,
        "--search",
        "-m", model,
        "-c", f'model_reasoning_effort="{reasoning}"',
        "exec",
        "--json",
        "--dangerously-bypass-approvals-and-sandbox",
        "-C", working_dir,
        prompt,
    ]

    def _call():
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=working_dir,
        )

    start = datetime.now()
    if logger:
        logger.log(f"[Codex] Starting {call_name} (model={model})")

    try:
        result = await asyncio.get_event_loop().run_in_executor(None, _call)
    except Exception as exc:
        elapsed = (datetime.now() - start).total_seconds()
        if logger:
            logger.log(f"[Codex] EXCEPTION: {type(exc).__name__}: {exc}")
        if tracker:
            tracker.record(call_name or "codex", 0, 0, elapsed,
                           provider="codex", model=model)
        raise ModelRunnerError(
            provider="codex",
            error_type="subprocess_error",
            message=f"Failed to execute Codex CLI: {type(exc).__name__}: {exc}",
        )

    elapsed = (datetime.now() - start).total_seconds()

    # Log stderr if present (contains error messages from CLI)
    if result.stderr and result.stderr.strip() and logger:
        logger.log(f"[Codex] stderr:\n{result.stderr.strip()}")

    # --- Parse JSONL output (adapted from test_call.py:41-67) ---
    response = ""
    input_tokens = 0
    output_tokens = 0
    json_parse_error = None

    try:
        lines = result.stdout.strip().split("\n")
        events = [json.loads(line) for line in lines if line.strip()]

        for event in events:
            if event.get("type") == "item.completed":
                item = event.get("item", {})
                if item.get("type") == "agent_message":
                    response = item.get("text", "")
            elif event.get("type") == "turn.completed":
                usage = event.get("usage", {})
                input_tokens += usage.get("input_tokens", 0)
                output_tokens += usage.get("output_tokens", 0)
    except (json.JSONDecodeError, ValueError) as exc:
        json_parse_error = str(exc)
        if logger:
            logger.log(f"[Codex] JSON parse error: {exc}")
            if result.stdout.strip():
                logger.log(f"[Codex] Raw stdout (first 1000 chars): {result.stdout.strip()[:1000]}")
        # Fall back to raw stdout as response
        response = result.stdout.strip()

    # The Codex CLI sometimes exits non-zero (e.g. "Reading additional input
    # from stdin..." warning → exit code 1) even when it produced a valid
    # agent_message. Treat the response payload as authoritative: a non-zero
    # exit is only fatal if we could not parse any usable response.
    if result.returncode != 0:
        if logger:
            logger.log(f"[Codex] Non-zero exit code: {result.returncode} "
                       f"(treating as warning since response was parsed)" if response.strip()
                       else f"[Codex] Non-zero exit code: {result.returncode}")
        if not response.strip():
            if tracker:
                tracker.record(call_name or "codex", input_tokens, output_tokens,
                               elapsed, provider="codex", model=model)
            raise ModelRunnerError(
                provider="codex",
                error_type="non_zero_exit",
                message=f"Codex CLI exited with code {result.returncode}",
                exit_code=result.returncode,
                stderr=result.stderr,
                stdout=result.stdout,
            )

    # Check for empty response (might indicate silent failure)
    if not response.strip():
        if logger:
            logger.log(f"[Codex] Empty response received")
        if tracker:
            tracker.record(call_name or "codex", input_tokens, output_tokens,
                           elapsed, provider="codex", model=model)
        raise ModelRunnerError(
            provider="codex",
            error_type="empty_response",
            message="Codex returned empty response" + (f" (JSON parse error: {json_parse_error})" if json_parse_error else ""),
            exit_code=result.returncode,
            stderr=result.stderr,
            stdout=result.stdout,
        )

    if logger:
        logger.log(f"[Codex] Completed {call_name} in {elapsed:.0f}s "
                    f"({input_tokens} in / {output_tokens} out)")

    if tracker:
        tracker.record(call_name or "codex", input_tokens, output_tokens,
                       elapsed, provider="codex", model=model)

    return response


# ---------------------------------------------------------------------------
# Gemini wrapper
# ---------------------------------------------------------------------------

async def run_gemini_agent(
    prompt: str,
    working_dir: str,
    gemini_config: dict,
    logger=None,
    tracker=None,
    call_name: str = "",
) -> str:
    """Run the Gemini CLI as a proof-search agent. Returns response text.

    Args:
        prompt: The full prompt string to send.
        working_dir: Directory the agent operates in (cwd for subprocess).
        gemini_config: Dict with keys: cli_path, model, api_key,
            approval_mode, thinking_level, thinking_budget.
        logger: Optional PipelineLogger for streaming output.
        tracker: Optional TokenTracker for recording token usage.
        call_name: Human-readable label for this call.
    """
    cli_path = gemini_config.get("cli_path", "gemini")
    model = gemini_config.get("model", "gemini-3-flash-preview")
    api_key = gemini_config.get("api_key", "")
    approval_mode = gemini_config.get("approval_mode", "yolo")
    thinking_level = gemini_config.get("thinking_level", "")
    thinking_budget = gemini_config.get("thinking_budget")

    cmd = [
        cli_path,
        "-m", model,
        "--approval-mode", approval_mode,
        "-o", "json",   # JSON output for metadata extraction
        "-p", prompt,
    ]

    def _call():
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
                        "overrides": [
                            {
                                "match": {"model": model},
                                "modelConfig": {
                                    "generateContentConfig": {
                                        "thinkingConfig": thinking_config,
                                    }
                                },
                            }
                        ]
                    }
                }
                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings, f)
                env["GEMINI_CLI_HOME"] = gemini_home
                return subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=working_dir,
                    env=env,
                )

        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=working_dir,
            env=env,
        )

    start = datetime.now()
    if logger:
        logger.log(f"[Gemini] Starting {call_name} (model={model})")

    try:
        result = await asyncio.get_event_loop().run_in_executor(None, _call)
    except Exception as exc:
        elapsed = (datetime.now() - start).total_seconds()
        if logger:
            logger.log(f"[Gemini] EXCEPTION: {type(exc).__name__}: {exc}")
        if tracker:
            tracker.record(call_name or "gemini", 0, 0, elapsed,
                           provider="gemini", model=model)
        raise ModelRunnerError(
            provider="gemini",
            error_type="subprocess_error",
            message=f"Failed to execute Gemini CLI: {type(exc).__name__}: {exc}",
        )

    elapsed = (datetime.now() - start).total_seconds()

    # Log stderr if present (contains error messages from CLI)
    if result.stderr and result.stderr.strip() and logger:
        logger.log(f"[Gemini] stderr:\n{result.stderr.strip()}")

    # --- Parse JSON output (adapted from test_call.py:74-121) ---
    response = ""
    input_tokens = 0
    output_tokens = 0
    json_parse_error = None

    try:
        data = json.loads(result.stdout)
        response = data.get("response", "")

        for _, model_stats in data.get("stats", {}).get("models", {}).items():
            tokens = model_stats.get("tokens", {})
            input_tokens += tokens.get("input", 0)
            output_tokens += tokens.get("candidates", 0)
            output_tokens += tokens.get("thoughts", 0)  # include thinking tokens
    except (json.JSONDecodeError, ValueError) as exc:
        json_parse_error = str(exc)
        if logger:
            logger.log(f"[Gemini] JSON parse error: {exc}")
            if result.stdout.strip():
                logger.log(f"[Gemini] Raw stdout (first 1000 chars): {result.stdout.strip()[:1000]}")
        response = result.stdout.strip()

    # Check for non-zero exit code (indicates CLI failure)
    if result.returncode != 0:
        if logger:
            logger.log(f"[Gemini] Non-zero exit code: {result.returncode}")
        if tracker:
            tracker.record(call_name or "gemini", input_tokens, output_tokens,
                           elapsed, provider="gemini", model=model)
        raise ModelRunnerError(
            provider="gemini",
            error_type="non_zero_exit",
            message=f"Gemini CLI exited with code {result.returncode}",
            exit_code=result.returncode,
            stderr=result.stderr,
            stdout=result.stdout,
        )

    # Check for empty response (might indicate silent failure)
    if not response.strip():
        if logger:
            logger.log(f"[Gemini] Empty response received")
        if tracker:
            tracker.record(call_name or "gemini", input_tokens, output_tokens,
                           elapsed, provider="gemini", model=model)
        raise ModelRunnerError(
            provider="gemini",
            error_type="empty_response",
            message="Gemini returned empty response" + (f" (JSON parse error: {json_parse_error})" if json_parse_error else ""),
            exit_code=result.returncode,
            stderr=result.stderr,
            stdout=result.stdout,
        )

    if logger:
        logger.log(f"[Gemini] Completed {call_name} in {elapsed:.0f}s "
                    f"({input_tokens} in / {output_tokens} out)")

    if tracker:
        tracker.record(call_name or "gemini", input_tokens, output_tokens,
                       elapsed, provider="gemini", model=model)

    return response


# ---------------------------------------------------------------------------
# Per-agent override resolution
# ---------------------------------------------------------------------------

def resolve_agent_provider_config(
    full_config: dict,
    agent_role_cfg: dict,
) -> tuple[str, dict]:
    """Resolve a per-agent role config against the global provider section.

    Each agent role in config.yaml is a dict of the form::

        { provider: "codex", model: "gpt-5.5", reasoning_effort: "xhigh" }

    The provider name picks the global section (``codex:`` / ``gemini:`` /
    ``claude:``). Any other keys override the corresponding fields from the
    global section. Knobs not set on the agent fall back to global.

    For ``claude``, the global section contains nested
    ``subscription:`` / ``api_key:`` / ``bedrock:`` blocks; the per-agent
    ``model`` override (if any) overrides whichever block ``claude.provider``
    selects (the global ``claude.provider`` value still controls auth).

    Returns ``(provider, merged_provider_cfg)`` — ``merged_provider_cfg`` is
    a shallow copy of the global section with per-agent fields overlaid.
    """
    if not isinstance(agent_role_cfg, dict):
        raise ValueError(
            f"Agent role config must be a dict like "
            f"{{provider: 'codex', model: 'gpt-5.5'}}, got: {agent_role_cfg!r}"
        )
    provider = agent_role_cfg.get("provider")
    if not provider:
        raise ValueError(
            f"Agent role config is missing required 'provider' field: {agent_role_cfg!r}"
        )
    provider = provider.lower().strip()
    if provider not in ("claude", "codex", "gemini", "chatgpt_browser"):
        raise ValueError(
            f"Unknown provider {provider!r}; expected 'claude', 'codex', 'gemini', or 'chatgpt_browser'."
        )

    overrides = {k: v for k, v in agent_role_cfg.items() if k != "provider"}
    global_section = full_config.get(provider, {})

    if provider == "claude":
        merged = {k: v for k, v in global_section.items()}
        auth_mode = merged.get("provider", "subscription")
        # Apply the per-agent model override into the active auth block
        if "model" in overrides:
            sub = dict(merged.get(auth_mode, {}))
            sub["model"] = overrides["model"]
            merged[auth_mode] = sub
        # Other claude-level overrides (cli_path, permission_mode) overlay directly
        for k, v in overrides.items():
            if k == "model":
                continue
            merged[k] = v
        return provider, merged

    # codex / gemini / chatgpt_browser: flat dict merge
    merged = {**global_section, **overrides}
    return provider, merged


# ---------------------------------------------------------------------------
# Unified dispatcher
# ---------------------------------------------------------------------------

async def run_model(
    provider: str,
    prompt: str,
    working_dir: str,
    config: dict,
    *,
    claude_opts: dict | None = None,
    logger=None,
    tracker=None,
    call_name: str = "",
    instructions: str | None = None,
) -> str:
    """Dispatch a prompt to the specified model provider.

    Args:
        provider: One of "claude", "codex", "gemini", "chatgpt_browser".
        prompt: The full prompt string.
        working_dir: Agent's working directory.
        config: Full pipeline config dict (with claude/codex/gemini sections).
        claude_opts: Claude CLI options dict (required when provider="claude").
        logger: Optional PipelineLogger.
        tracker: Optional TokenTracker.
        call_name: Human-readable label.
        instructions: System instructions (used only for Claude).

    Returns:
        The agent's response text.
    """
    if provider == "claude":
        return await run_claude_agent(
            prompt, working_dir, claude_opts or {},
            logger=logger, tracker=tracker, call_name=call_name,
            instructions=instructions,
        )
    elif provider == "codex":
        codex_cfg = config.get("codex", {})
        if codex_cfg.get("execution_mode", "direct") == "browser":
            return await run_chatgpt_browser_agent(
                prompt, working_dir, config,
                logger=logger, tracker=tracker, call_name=call_name,
            )
        return await run_codex_agent(
            prompt, working_dir, codex_cfg,
            logger=logger, tracker=tracker, call_name=call_name,
        )
    elif provider == "gemini":
        return await run_gemini_agent(
            prompt, working_dir, config.get("gemini", {}),
            logger=logger, tracker=tracker, call_name=call_name,
        )
    elif provider == "chatgpt_browser":
        return await run_chatgpt_browser_agent(
            prompt, working_dir, config,
            logger=logger, tracker=tracker, call_name=call_name,
        )
    else:
        raise ValueError(f"Unknown model provider: {provider!r}. "
                         f"Expected 'claude', 'codex', 'gemini', or 'chatgpt_browser'.")


async def run_model_for_agent(
    agent_role_cfg: dict,
    prompt: str,
    working_dir: str,
    config: dict,
    *,
    claude_opts: dict | None = None,
    logger=None,
    tracker=None,
    call_name: str = "",
    instructions: str | None = None,
) -> str:
    """Dispatch using a per-agent role config (the dict-with-provider format).

    Resolves ``agent_role_cfg`` against the global provider section, then
    invokes :func:`run_model` with an effective config in which the chosen
    provider's section has been overlaid with the per-agent overrides.

    For ``claude``, also overlays the per-agent ``model`` into ``claude_opts``.
    """
    provider, merged_provider_cfg = resolve_agent_provider_config(
        config, agent_role_cfg
    )
    effective_config = dict(config)
    effective_config[provider] = merged_provider_cfg

    if provider == "claude":
        effective_claude_opts = dict(claude_opts or {})
        if "model" in agent_role_cfg:
            effective_claude_opts["model"] = agent_role_cfg["model"]
    else:
        effective_claude_opts = claude_opts

    return await run_model(
        provider,
        prompt,
        working_dir,
        effective_config,
        claude_opts=effective_claude_opts,
        logger=logger,
        tracker=tracker,
        call_name=call_name,
        instructions=instructions,
    )
