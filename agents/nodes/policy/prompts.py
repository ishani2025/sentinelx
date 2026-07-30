"""Module-local prompt accessor. Single source of truth lives in prompts/policy_prompt.py."""
from __future__ import annotations
try:
    from prompts.policy_prompt import POLICY_SYSTEM_PROMPT, load_policy_prompt
except Exception:  # allow standalone import if package root differs
    import os, importlib.util
    _p = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "policy_prompt.py")
    _spec = importlib.util.spec_from_file_location("policy_prompt", _p)
    _mod = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_mod)  # type: ignore
    POLICY_SYSTEM_PROMPT = _mod.POLICY_SYSTEM_PROMPT
    load_policy_prompt = _mod.load_policy_prompt

__all__ = ["POLICY_SYSTEM_PROMPT", "load_policy_prompt"]
