"""Module-local prompt accessor. Single source in prompts/risk_assessment_prompt.py."""
from __future__ import annotations
try:
    from prompts.risk_assessment_prompt import RISK_ASSESSMENT_SYSTEM_PROMPT, load_risk_assessment_prompt
except Exception:
    import os, importlib.util
    _p = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "risk_assessment_prompt.py")
    _s = importlib.util.spec_from_file_location("risk_assessment_prompt", _p)
    _m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
    RISK_ASSESSMENT_SYSTEM_PROMPT = _m.RISK_ASSESSMENT_SYSTEM_PROMPT
    load_risk_assessment_prompt = _m.load_risk_assessment_prompt
__all__ = ["RISK_ASSESSMENT_SYSTEM_PROMPT", "load_risk_assessment_prompt"]
