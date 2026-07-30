"""Module-local prompt accessor. Single source in prompts/response_planning_prompt.py."""
from __future__ import annotations
try:
    from prompts.response_planning_prompt import RESPONSE_PLANNING_SYSTEM_PROMPT, load_response_planning_prompt
except Exception:
    import os, importlib.util
    _p = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "response_planning_prompt.py")
    _s = importlib.util.spec_from_file_location("response_planning_prompt", _p)
    _m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
    RESPONSE_PLANNING_SYSTEM_PROMPT = _m.RESPONSE_PLANNING_SYSTEM_PROMPT
    load_response_planning_prompt = _m.load_response_planning_prompt
__all__ = ["RESPONSE_PLANNING_SYSTEM_PROMPT", "load_response_planning_prompt"]
