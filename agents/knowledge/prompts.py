"""Module-local prompt accessor. Single source in prompts/knowledge_prompt.py."""
from __future__ import annotations
try:
    from prompts.knowledge_prompt import (KNOWLEDGE_SYSTEM_PROMPT, KNOWLEDGE_SYNTHESIS_PROMPT,
                                           load_knowledge_prompt, load_synthesis_prompt)
except Exception:
    import os, importlib.util
    _p = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "knowledge_prompt.py")
    _s = importlib.util.spec_from_file_location("knowledge_prompt", _p)
    _m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
    KNOWLEDGE_SYSTEM_PROMPT = _m.KNOWLEDGE_SYSTEM_PROMPT; KNOWLEDGE_SYNTHESIS_PROMPT = _m.KNOWLEDGE_SYNTHESIS_PROMPT
    load_knowledge_prompt = _m.load_knowledge_prompt; load_synthesis_prompt = _m.load_synthesis_prompt
__all__ = ["KNOWLEDGE_SYSTEM_PROMPT", "KNOWLEDGE_SYNTHESIS_PROMPT", "load_knowledge_prompt", "load_synthesis_prompt"]
