"""Shared utilities for the Policy Node: LLM helper (single instance), extraction, JSON parsing."""
from __future__ import annotations

import json
import os
import re
import time
from functools import lru_cache
from typing import Any, Callable, Optional

# ---- shared LLM helper (Llama 3.2 via Ollama) — instantiate ONCE ---------- #
_LLM_MODEL = os.getenv("SENTINELX_LLM_MODEL", "llama3.2")
_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


@lru_cache(maxsize=1)
def get_llm(model: str = _LLM_MODEL, temperature: float = 0.0):
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, base_url=_OLLAMA_URL, temperature=temperature, format="json")


def default_llm_call(system_prompt: str, user_content: str) -> str:
    """Default LLM invocation used unless a callable is injected (dependency injection)."""
    from langchain_core.messages import SystemMessage, HumanMessage
    resp = get_llm().invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_content)])
    return resp.content if hasattr(resp, "content") else str(resp)


# ---- asset-type normalization -------------------------------------------- #
_ASSET_ALIASES = {
    "iam": "iam_user", "iam_user": "iam_user", "user": "iam_user", "identity": "iam_user",
    "s3": "s3", "bucket": "s3", "ec2": "ec2", "instance": "ec2",
    "lambda": "lambda", "function": "lambda", "root": "root_account", "root_account": "root_account",
    "rds": "rds", "eks": "eks",
}


def normalize_asset_type(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    key = str(raw).strip().lower().replace(" ", "_")
    for token, canon in _ASSET_ALIASES.items():
        if token in key:
            return canon
    return key


def derive_action(asset_type: Optional[str], incident: dict) -> Optional[str]:
    """Use an explicit proposed action if present, else a sensible default per asset type."""
    explicit = incident.get("proposed_action") or incident.get("action")
    if explicit:
        return str(explicit)
    defaults = {"iam_user": "disable_access_key", "s3": "revoke_access",
                "ec2": "isolate_instance", "lambda": "rotate_secrets",
                "root_account": "enforce_root_lockdown"}
    return defaults.get(asset_type or "", None)


def severity_from_criticality(criticality: Optional[str], incident: dict) -> str:
    if incident.get("severity"):
        return str(incident["severity"])
    return {"critical": "Sev1", "high": "Sev2", "medium": "Sev3", "low": "Sev4"}.get(
        str(criticality or "").lower(), "Sev3")


# ---- JSON parsing --------------------------------------------------------- #
def parse_json(raw: str) -> Optional[dict[str, Any]]:
    if not raw:
        return None
    text = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


class Timer:
    def __enter__(self):
        self._t = time.perf_counter(); return self
    def __exit__(self, *a):
        self.ms = round((time.perf_counter() - self._t) * 1000, 1)
