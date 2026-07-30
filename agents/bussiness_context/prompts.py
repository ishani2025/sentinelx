"""Module-local prompt accessor. Single source in prompts/business_context_prompt.py."""
from __future__ import annotations
try:
    from prompts.business_context_prompt import (
        BUSINESS_CONTEXT_SYSTEM_PROMPT, BUSINESS_SUMMARY_SYSTEM_PROMPT,
        load_business_context_prompt, load_business_summary_prompt)
except Exception:
    import os, importlib.util
    _p = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "business_context_prompt.py")
    _spec = importlib.util.spec_from_file_location("business_context_prompt", _p)
    _m = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m)
    BUSINESS_CONTEXT_SYSTEM_PROMPT = _m.BUSINESS_CONTEXT_SYSTEM_PROMPT
    BUSINESS_SUMMARY_SYSTEM_PROMPT = _m.BUSINESS_SUMMARY_SYSTEM_PROMPT
    load_business_context_prompt = _m.load_business_context_prompt
    load_business_summary_prompt = _m.load_business_summary_prompt

__all__ = ["BUSINESS_CONTEXT_SYSTEM_PROMPT", "BUSINESS_SUMMARY_SYSTEM_PROMPT",
           "load_business_context_prompt", "load_business_summary_prompt"]
