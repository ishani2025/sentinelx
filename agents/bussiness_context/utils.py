"""Shared utilities: LLM helpers (single instance), ARN parsing, JSON parsing, timing."""
from __future__ import annotations
import json, os, re, time
from functools import lru_cache
from typing import Any, Optional

_LLM_MODEL = os.getenv("SENTINELX_LLM_MODEL", "llama3.2")
_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


@lru_cache(maxsize=1)
def get_chat_llm(model: str = _LLM_MODEL, temperature: float = 0.0):
    """Singleton tool-calling ChatOllama (used by the node for bind_tools)."""
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, base_url=_OLLAMA_URL, temperature=temperature)


@lru_cache(maxsize=1)
def _get_json_llm(model: str = _LLM_MODEL, temperature: float = 0.0):
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, base_url=_OLLAMA_URL, temperature=temperature, format="json")


def default_summary_call(system_prompt: str, user_content: str) -> str:
    """Default LLM call used by the Business Summary tool (JSON mode)."""
    from langchain_core.messages import SystemMessage, HumanMessage
    resp = _get_json_llm().invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_content)])
    return resp.content if hasattr(resp, "content") else str(resp)


_ARN_RE = re.compile(r"[:/]([^:/\s]+)$")


def extract_aws_resource_ids(incident: dict) -> list[str]:
    """Collect candidate AWS resource identifiers from the incident (never mutates incident)."""
    candidates: list[str] = []
    for key in ("resource_arn", "arn", "ec2", "ec2_instance", "instance_id",
                "iam", "iam_user", "s3", "s3_bucket", "bucket", "resource_id"):
        val = incident.get(key)
        if isinstance(val, str) and val:
            candidates.append(val)
            m = _ARN_RE.search(val)          # last ARN segment (e.g. i-0abc / bucket / user)
            if m:
                candidates.append(m.group(1))
    # de-duplicate, keep order
    seen: set[str] = set()
    return [c for c in candidates if not (c in seen or seen.add(c))]


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
