#!/usr/bin/env python3
"""
Smoke test: validates prompt loading and agent connectivity
without running the full proof loop (which is expensive).
"""

import argparse
import asyncio
import json
import os
import sys
import tempfile

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import load_prompt, make_claude_options
from decomposition_prover import load_prompt as decomp_load_prompt


async def run_smoke_test(config: dict, config_path: str | None = None) -> bool:
    """Run all smoke tests. Returns True if all passed, False if any failed.

    Can be called from pipeline.py at startup, or standalone via main().

    Args:
        config: Parsed config dict (from yaml.safe_load).
        config_path: Path to config.yaml (used to resolve project paths).
            If None, resolves from this file's location.
    """
    # Resolve project root: config.yaml lives at project_base/config.yaml
    if config_path:
        project_base = os.path.dirname(os.path.abspath(config_path))
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_base = os.path.dirname(script_dir)

    prompts_dir = os.path.join(project_base, "prompts")
    skill_dir = os.path.join(project_base, "skill")

    claude_cfg = config.get("claude", {})

    passed = 0
    failed = 0

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal passed, failed
        if condition:
            print(f"  PASS: {name}")
            passed += 1
        else:
            print(f"  FAIL: {name} -- {detail}")
            failed += 1

    # -------------------------------------------------------
    # Test 1: Prompt files exist
    # -------------------------------------------------------
    print("\n=== Test 1: Prompt files ===")
    prompt_files = [
        "literature_survey.md",
        "proof_effort_summary.md",
    ]
    for pf in prompt_files:
        exists = os.path.exists(os.path.join(prompts_dir, pf))
        check(f"Prompt {pf} exists", exists)

    # Decomposition mode prompts
    decomposition_prompt_files = [
        "decomposition-prover/decomposition.md",
        "decomposition-prover/single_prover.md",
        "decomposition-prover/regulator.md",
        "decomposition-prover/proof_verify_structural.md",
        "decomposition-prover/proof_verify_detailed.md",
        "decomposition-prover/verdict_proof.md",
    ]
    for pf in decomposition_prompt_files:
        exists = os.path.exists(os.path.join(prompts_dir, pf))
        check(f"Prompt {pf} exists", exists)

    # -------------------------------------------------------
    # Test 2: Skill files exist
    # -------------------------------------------------------
    print("\n=== Test 2: Skill files ===")
    skill_files = ["super_math_skill.md"]
    for sf in skill_files:
        exists = os.path.exists(os.path.join(skill_dir, sf))
        check(f"Skill {sf} exists", exists)

    # -------------------------------------------------------
    # Test 3: Prompt loading with variable substitution
    # -------------------------------------------------------
    print("\n=== Test 3: Prompt loading ===")
    try:
        prompt = load_prompt(
            prompts_dir, "literature_survey.md",
            problem_file="/tmp/test_problem.tex",
            related_info_dir="/tmp/test_output/related_info",
            output_dir="/tmp/test_output",
            proof_file="/tmp/test_output/proof.md",
            error_file="/tmp/test_output/error_literature_survey.md",
        )
        check("literature_survey.md renders OK", "test_problem.tex" in prompt)
    except Exception as e:
        check("literature_survey.md renders OK", False, str(e))

    try:
        prompt = load_prompt(
            prompts_dir, "proof_effort_summary.md",
            output_dir="/tmp/test_output",
            outcome="PASS",
            total_attempts=2,
            total_proofs=3,
            max_attempts=2,
            summary_file="/tmp/test_output/proof_effort_summary.md",
            error_file="/tmp/test_output/error_proof_effort_summary.md",
        )
        check("proof_effort_summary.md renders OK", "test_output" in prompt)
    except Exception as e:
        check("proof_effort_summary.md renders OK", False, str(e))

    # -------------------------------------------------------
    # Test 3b: Decomposition mode prompt loading
    # -------------------------------------------------------
    print("\n=== Test 3b: Decomposition prompt loading ===")

    try:
        prompt = load_prompt(
            prompts_dir, "decomposition-prover/decomposition.md",
            mode="CREATE",
            problem_file="/tmp/test_problem.tex",
            related_work_file="/tmp/test_related_work.md",
            problem_id="test_problem",
            attempt_number=1,
            revision_number=1,
            timestamp="2024-01-01T00:00:00",
            output_file="/tmp/test_decomposition.yaml",
            current_decomposition_file="",
            verification_feedback="",
            regulator_guidance="",
            previous_proof_file="",
            human_help_file="/tmp/test_human_help.md",
            plan_history_file="/tmp/test_plan_history.md",
        )
        check("decomposition.md renders OK", "test_problem.tex" in prompt)
        check("decomposition.md has mode", "CREATE" in prompt)
        check("decomposition.md references plan history",
              "plan_history" in prompt or "Plan History" in prompt)
        check("decomposition.md no longer references difficulty",
              "difficulty_file" not in prompt and "Difficulty Evaluation" not in prompt)
        check("decomposition.md no longer references revision_context",
              "{revision_context}" not in prompt)
    except Exception as e:
        check("decomposition.md renders OK", False, str(e))

    try:
        prompt = load_prompt(
            prompts_dir, "decomposition-prover/single_prover.md",
            problem_file="/tmp/test_problem.tex",
            related_work_file="/tmp/test_related_work.md",
            decomposition_file="/tmp/test_decomposition.yaml",
            human_help_file="/tmp/test_human_help.md",
            previous_proof_file="",
            previous_verification_file="",
            output_file="/tmp/test_proof.md",
            output_dir="/tmp/test_output",
            scratchpad_file="/tmp/test_output/scratchpad.md",
        )
        check("single_prover.md renders OK", "test_problem.tex" in prompt)
        check("single_prover.md has decomposition file", "test_decomposition.yaml" in prompt)
    except Exception as e:
        check("single_prover.md renders OK", False, str(e))

    try:
        prompt = load_prompt(
            prompts_dir, "decomposition-prover/regulator.md",
            mode="DECIDE",
            state_file="attempt: 1\nrevision: 1\nproof: 1",
            decomposition_file="/tmp/test_decomposition.yaml",
            proof_file="/tmp/test_proof.md",
            verification_report="Test verification report",
            attempt_history="First attempt",
            max_proof_attempts=3,
            max_revisions=2,
            max_decompositions=2,
            output_file="/tmp/test_regulator_decision.md",
            plan_history_file="/tmp/test_plan_history.md",
            verification_phase="structural",
        )
        check("regulator.md renders OK", "DECIDE" in prompt)
        check("regulator.md references plan history append",
              "Plan History Append" in prompt)
        check("regulator.md surfaces verification_phase",
              "structural" in prompt and "Verification Phase" in prompt)
    except Exception as e:
        check("regulator.md renders OK", False, str(e))

    try:
        prompt = load_prompt(
            prompts_dir, "decomposition-prover/verdict_proof.md",
            mode="STRUCTURAL",
            structural_verification_file="/tmp/test_structural.md",
            detailed_verification_file="",
        )
        check("verdict_proof.md (decomp) renders OK", "STRUCTURAL" in prompt)
    except Exception as e:
        check("verdict_proof.md (decomp) renders OK", False, str(e))

    # decomposition_prover.load_prompt MUST render the same output as
    # pipeline.load_prompt for the templates that the prover uses (these
    # templates rely on {{...}} escapes intended for str.format).
    try:
        a = load_prompt(
            prompts_dir, "decomposition-prover/regulator.md",
            mode="DECIDE", state_file="x", decomposition_file="x",
            proof_file="x", verification_report="", attempt_history="",
            max_decompositions=4, max_revisions=4, max_proof_attempts=4,
            output_file="x", plan_history_file="x",
            verification_phase="structural",
        )
        b = decomp_load_prompt(
            prompts_dir, "decomposition-prover/regulator.md",
            mode="DECIDE", state_file="x", decomposition_file="x",
            proof_file="x", verification_report="", attempt_history="",
            max_decompositions=4, max_revisions=4, max_proof_attempts=4,
            output_file="x", plan_history_file="x",
            verification_phase="structural",
        )
        check("decomposition_prover.load_prompt matches pipeline.load_prompt",
              a == b, "Renderer divergence — escapes will not resolve at runtime")
        check("regulator.md {{N}} escape resolves to {N}",
              "{N}" in b and "{{N}}" not in b,
              "Literal '{{N}}' would be sent to the model")
    except Exception as e:
        check("decomposition_prover.load_prompt matches pipeline.load_prompt",
              False, str(e))

    # -------------------------------------------------------
    # Test 4: Skill loading
    # -------------------------------------------------------
    print("\n=== Test 4: Skill loading ===")
    math_skill_path = os.path.join(skill_dir, "super_math_skill.md")
    try:
        with open(math_skill_path) as f:
            math_skill = f.read()
        check("Math skill loads", len(math_skill) > 100)
    except Exception as e:
        check("Skill loading", False, str(e))

    # -------------------------------------------------------
    # Determine which providers are actually used by the configured pipeline.
    # Skip connectivity tests for providers that no role references.
    # -------------------------------------------------------
    import shutil
    import subprocess

    pipeline_cfg_for_use = config.get("pipeline", {})
    providers_in_use: set[str] = set()

    def _role_provider(role_cfg) -> str | None:
        if isinstance(role_cfg, dict):
            p = role_cfg.get("provider")
            return p.lower() if isinstance(p, str) else None
        return None

    for agent_key in ("literature_survey", "proof_summary"):
        prov = _role_provider(pipeline_cfg_for_use.get(agent_key))
        if prov:
            providers_in_use.add(prov)

    decomp_models = config.get("decomposition", {}).get("models", {})
    for v in decomp_models.values():
        prov = _role_provider(v)
        if prov:
            providers_in_use.add(prov)

    providers_in_use = {p for p in providers_in_use if p in {"claude", "codex", "gemini", "chatgpt_browser"}}
    browser_mode_in_use = any(
        isinstance(v, dict)
        and v.get("provider", "").lower() == "codex"
        and v.get("execution_mode") == "browser"
        for v in list(decomp_models.values()) + [
            pipeline_cfg_for_use.get("literature_survey"),
            pipeline_cfg_for_use.get("proof_summary"),
        ]
    )

    # -------------------------------------------------------
    # Test 5: Claude CLI connectivity (provider-aware)
    # -------------------------------------------------------
    provider = claude_cfg.get("provider", "subscription")
    run_claude_test = "claude" in providers_in_use
    if not run_claude_test:
        print("\n=== Test 5: Claude CLI connectivity [SKIPPED — Claude not used by any role] ===")
    else:
        print(f"\n=== Test 5: Claude CLI connectivity (provider: {provider}) ===")

    # Detect if ~/.claude/settings.json injects provider vars that would
    # override the config.yaml provider selection.
    _PROVIDER_VARS = ("CLAUDE_CODE_USE_BEDROCK", "ANTHROPIC_API_KEY",
                      "AWS_PROFILE", "ANTHROPIC_MODEL")
    cli_settings_path = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
    cli_settings_conflict = False
    if run_claude_test and os.path.exists(cli_settings_path):
        import json as _json_settings
        try:
            with open(cli_settings_path) as _sf:
                cli_settings = _json_settings.load(_sf)
            settings_env = cli_settings.get("env", {})
            if provider == "subscription" and settings_env.get("CLAUDE_CODE_USE_BEDROCK"):
                check("No settings.json provider conflict", False,
                      "~/.claude/settings.json has CLAUDE_CODE_USE_BEDROCK set — "
                      "the CLI will use Bedrock regardless of config.yaml provider='subscription'. "
                      "Either set provider to 'bedrock' in config.yaml, or remove "
                      "CLAUDE_CODE_USE_BEDROCK from ~/.claude/settings.json")
                cli_settings_conflict = True
            elif provider == "subscription" and settings_env.get("ANTHROPIC_API_KEY"):
                check("No settings.json provider conflict", False,
                      "~/.claude/settings.json has ANTHROPIC_API_KEY set — "
                      "the CLI will use API key auth regardless of config.yaml provider='subscription'. "
                      "Either set provider to 'api_key' in config.yaml, or remove "
                      "ANTHROPIC_API_KEY from ~/.claude/settings.json")
                cli_settings_conflict = True
            elif provider == "api_key" and settings_env.get("CLAUDE_CODE_USE_BEDROCK"):
                check("No settings.json provider conflict", False,
                      "~/.claude/settings.json has CLAUDE_CODE_USE_BEDROCK set — "
                      "the CLI may use Bedrock instead of your API key. "
                      "Remove CLAUDE_CODE_USE_BEDROCK from ~/.claude/settings.json")
                cli_settings_conflict = True
            else:
                check("No settings.json provider conflict", True)
        except Exception:
            pass  # Can't read settings — not a conflict we can detect

    cli_path = claude_cfg.get("cli_path", "claude")
    if not run_claude_test:
        pass
    elif shutil.which(cli_path) is not None:
        check(f"Claude CLI '{cli_path}' found", True)

        # Build options via make_claude_options so we get the right model
        # and env vars for the configured provider.
        try:
            opts = make_claude_options(claude_cfg, tempfile.mkdtemp())
        except ValueError as e:
            check(f"Claude config valid ({provider})", False, str(e))
            opts = None

        if opts is not None:
            check(f"Claude config valid ({provider})", True)

            # Strip vars that cause provider cross-contamination, then
            # add back only the ones for the configured provider.
            clean_env = {k: v for k, v in os.environ.items()
                         if k not in _PROVIDER_VARS}
            clean_env.update(opts["env"])

            model = opts["model"]
            try:
                result = subprocess.run(
                    [cli_path, "-p", "--output-format", "json",
                     "--model", model,
                     "Reply with exactly: SMOKE_TEST_OK"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    env=clean_env, text=True, timeout=60,
                )
                import json as _json
                try:
                    data = _json.loads(result.stdout)
                    text = data.get("result", "")
                except (ValueError, KeyError):
                    text = result.stdout
                check(f"Claude CLI responds ({provider}, model={model})",
                      len(text) > 0,
                      f"Empty response, stderr: {result.stderr[:200]}")
                check("Claude CLI response valid",
                      "SMOKE_TEST_OK" in text.upper() or "smoke" in text.lower(),
                      f"Got: {text[:100]}")
            except subprocess.TimeoutExpired:
                check(f"Claude CLI responds ({provider})", False, "Timed out after 60s")
            except Exception as e:
                check(f"Claude CLI connectivity ({provider})", False, str(e))
    else:
        check(f"Claude CLI '{cli_path}' found", False,
              "Install claude CLI: npm install -g @anthropic-ai/claude-code")

    # -------------------------------------------------------
    # Test 6: Config validation
    # -------------------------------------------------------
    print("\n=== Test 6: Config validation ===")
    pipeline_cfg = config.get("pipeline", {})
    check("claude config present", "claude" in config, "Missing claude config")

    prover_cfg = config.get("prover", {})
    prover_mode = prover_cfg.get("mode", "decomposition")
    check("prover.mode is 'decomposition'", prover_mode == "decomposition",
          f"Only 'decomposition' is supported; got: {prover_mode}")

    print("\n=== Test 6b: Decomposition config validation ===")
    decomp_cfg = config.get("decomposition", {})
    check("decomposition config present", bool(decomp_cfg),
          "Missing decomposition config")

    valid_providers = {"claude", "codex", "gemini", "chatgpt_browser"}

    def _validate_role(label: str, role_cfg) -> None:
        if not isinstance(role_cfg, dict):
            check(f"{label} is a dict", False,
                  f"Expected dict like {{provider: 'codex', model: 'gpt-5.5'}}, got: {role_cfg!r}")
            return
        check(f"{label} is a dict", True)
        provider = role_cfg.get("provider")
        ok = isinstance(provider, str) and provider.lower() in valid_providers
        check(f"{label}.provider valid ({provider})",
              ok, f"Invalid or missing provider for {label}")
        if isinstance(provider, str) and provider.lower() == "codex":
            mode = role_cfg.get("execution_mode", "direct")
            check(f"{label}.execution_mode valid ({mode})",
                  mode in ("direct", "browser"),
                  "Codex execution_mode must be 'direct' or 'browser'")

    # Validate decomposition model assignments
    decomp_models = decomp_cfg.get("models", {})
    required_agents = ["decomposer", "single_prover", "regulator",
                      "structural_verifier", "detailed_verifier", "verdict"]
    for agent in required_agents:
        _validate_role(f"decomposition.models.{agent}", decomp_models.get(agent))

    if "chatgpt_browser" in providers_in_use or browser_mode_in_use:
        cgb_cfg = config.get("chatgpt_browser", {})
        check("chatgpt_browser config present", bool(cgb_cfg),
              "Missing chatgpt_browser config")
        supervisor = cgb_cfg.get("supervisor", {})
        check("chatgpt_browser.supervisor is codex",
              isinstance(supervisor, dict) and supervisor.get("provider", "codex") == "codex",
              "chatgpt_browser currently requires supervisor.provider: codex")

    # Validate limits
    max_proof = decomp_cfg.get("max_proof_attempts", 3)
    max_rev = decomp_cfg.get("max_revisions", 2)
    max_decomp = decomp_cfg.get("max_decompositions", 2)
    check("max_proof_attempts > 0", max_proof > 0, f"Invalid: {max_proof}")
    check("max_revisions > 0", max_rev > 0, f"Invalid: {max_rev}")
    check("max_decompositions > 0", max_decomp > 0, f"Invalid: {max_decomp}")

    # -------------------------------------------------------
    # Test 7: Auxiliary agent providers config validation
    # -------------------------------------------------------
    print("\n=== Test 7: Auxiliary agent providers ===")
    for agent_key in ("literature_survey", "proof_summary"):
        _validate_role(f"pipeline.{agent_key}", pipeline_cfg.get(agent_key))

    # -------------------------------------------------------
    # Test 7b: Standalone verifier agents (if present)
    # -------------------------------------------------------
    sv_cfg = config.get("standalone_verifier", {})
    if sv_cfg:
        print("\n=== Test 7b: Standalone verifier agents ===")
        for agent_key in ("judge", "structural_verifier", "detailed_verifier", "problem_reviewer"):
            _validate_role(f"standalone_verifier.{agent_key}", sv_cfg.get(agent_key))

    # -------------------------------------------------------
    # Test 8: Non-Claude provider connectivity (when needed)
    # -------------------------------------------------------
    providers_to_test = {p for p in providers_in_use if p != "claude"}
    if "chatgpt_browser" in providers_to_test or browser_mode_in_use:
        # The browser bridge is Codex-supervised. Smoke-test Codex CLI only;
        # live Chrome/ChatGPT delegation is intentionally skipped because it
        # depends on logged-in browser state and can be expensive.
        providers_to_test.add("codex")

    if providers_to_test:
        print(f"\n=== Test 8: Non-Claude provider connectivity (testing: {', '.join(sorted(providers_to_test))}) ===")
        import json as _json_test

        # --- Codex ---
        if "codex" in providers_to_test:
            codex_cfg = config.get("codex", {})
            codex_cli = codex_cfg.get("cli_path", "codex")
            if shutil.which(codex_cli) is not None:
                try:
                    codex_model = codex_cfg.get("model", "gpt-5.5")
                    codex_reasoning = codex_cfg.get("reasoning_effort", "xhigh")
                    codex_cwd = tempfile.mkdtemp()
                    # Mirror model_runner.run_codex_agent so the exit-code
                    # check reflects how Codex behaves at runtime.
                    codex_result = subprocess.run(
                        [codex_cli, "--search", "-m", codex_model,
                         "-c", f'model_reasoning_effort="{codex_reasoning}"',
                         "exec", "--json",
                         "--dangerously-bypass-approvals-and-sandbox",
                         "-C", codex_cwd,
                         "Reply with exactly: SMOKE_TEST_OK"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        text=True, timeout=120, cwd=codex_cwd,
                    )
                    codex_resp = codex_result.stdout.strip()
                    # Non-zero exit is treated as a warning if a response was
                    # produced (matches run_codex_agent's tolerance).
                    exit_ok = codex_result.returncode == 0 or bool(codex_resp)
                    check("Codex CLI exits cleanly (or returned a response)",
                          exit_ok,
                          f"Exit code {codex_result.returncode}, stderr: {codex_result.stderr[:200]}")
                    check("Codex responds", len(codex_resp) > 0, "Empty response")
                    check("Codex response valid",
                          "smoke" in codex_resp.lower() or "ok" in codex_resp.lower() or len(codex_resp) > 5,
                          f"Got: {codex_resp[:100]}")
                except subprocess.TimeoutExpired:
                    check("Codex connectivity", False, "Timed out after 120s")
                except Exception as e:
                    check("Codex connectivity", False, str(e))
            else:
                check(f"Codex CLI '{codex_cli}' found", False,
                      "Install codex or switch decomposition.models.* away from codex")

        if "chatgpt_browser" in providers_to_test or browser_mode_in_use:
            print("  SKIP: ChatGPT browser live check -- requires logged-in Chrome/ChatGPT session")

        # --- Gemini ---
        if "gemini" in providers_to_test:
            gemini_cfg = config.get("gemini", {})
            gemini_cli = gemini_cfg.get("cli_path", "gemini")
            gemini_api_key = gemini_cfg.get("api_key", "")
            if shutil.which(gemini_cli) is not None:
                try:
                    gemini_model = gemini_cfg.get("model", "gemini-3-flash-preview")
                    gemini_approval_mode = gemini_cfg.get("approval_mode", "yolo")
                    gemini_thinking_level = gemini_cfg.get("thinking_level", "")
                    gemini_thinking_budget = gemini_cfg.get("thinking_budget")
                    gemini_env = os.environ.copy()
                    if gemini_api_key:
                        gemini_env["GEMINI_API_KEY"] = gemini_api_key

                    thinking_config = {}
                    if gemini_thinking_level:
                        thinking_config["thinkingLevel"] = gemini_thinking_level
                    if gemini_thinking_budget is not None:
                        thinking_config["thinkingBudget"] = gemini_thinking_budget

                    if thinking_config:
                        with tempfile.TemporaryDirectory(prefix="qed-gemini-home-") as gemini_home:
                            settings_dir = os.path.join(gemini_home, ".gemini")
                            os.makedirs(settings_dir, exist_ok=True)
                            settings_path = os.path.join(settings_dir, "settings.json")
                            settings = {
                                "modelConfigs": {
                                    "overrides": [
                                        {
                                            "match": {"model": gemini_model},
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
                            gemini_env["GEMINI_CLI_HOME"] = gemini_home
                            gemini_result = subprocess.run(
                                [gemini_cli, "-m", gemini_model, "--approval-mode", gemini_approval_mode, "-o", "json",
                                 "-p", "Reply with exactly: SMOKE_TEST_OK"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, timeout=120, env=gemini_env,
                            )
                    else:
                        gemini_result = subprocess.run(
                            [gemini_cli, "-m", gemini_model, "--approval-mode", gemini_approval_mode, "-o", "json",
                             "-p", "Reply with exactly: SMOKE_TEST_OK"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=120, env=gemini_env,
                        )
                    check("Gemini CLI exits cleanly", gemini_result.returncode == 0,
                          f"Exit code {gemini_result.returncode}, stderr: {gemini_result.stderr[:300]}")
                    # Parse JSON response
                    gemini_resp = ""
                    try:
                        gemini_data = _json_test.loads(gemini_result.stdout)
                        gemini_resp = gemini_data.get("response", "")
                    except (ValueError, KeyError):
                        gemini_resp = gemini_result.stdout.strip()
                    check("Gemini responds", len(gemini_resp) > 0,
                          f"Empty response, stdout: {gemini_result.stdout[:200]}")
                    check("Gemini response valid",
                          "smoke" in gemini_resp.lower() or "ok" in gemini_resp.lower() or len(gemini_resp) > 5,
                          f"Got: {gemini_resp[:100]}")
                except subprocess.TimeoutExpired:
                    check("Gemini connectivity", False, "Timed out after 120s")
                except Exception as e:
                    check("Gemini connectivity", False, str(e))
            else:
                check(f"Gemini CLI '{gemini_cli}' found", False,
                      "Install gemini or switch decomposition.models.* away from gemini")
    else:
        print("\n=== Test 8: Non-Claude provider connectivity [SKIPPED — no non-Claude providers enabled] ===")

    # -------------------------------------------------------
    # Summary
    # -------------------------------------------------------
    print(f"\n{'=' * 60}")
    print(f"SMOKE TEST RESULTS: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")

    return failed == 0


async def main():
    parser = argparse.ArgumentParser(description="Smoke test for the proof agent pipeline")
    parser.add_argument("--config", help="Path to config.yaml", default=None)
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_base = os.path.dirname(script_dir)
    config_path = args.config or os.path.join(project_base, "config.yaml")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    ok = await run_smoke_test(config, config_path)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
