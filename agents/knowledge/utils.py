"""Knowledge Node utilities: Pydantic models, LLM helpers (single instance), JSON parsing."""
from __future__ import annotations
import json, os, re
from functools import lru_cache
from typing import Any, Optional
from pydantic import BaseModel, Field

_LLM_MODEL = os.getenv("SENTINELX_LLM_MODEL", "llama3.2")
_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

@lru_cache(maxsize=1)
def get_chat_llm(model: str = _LLM_MODEL, temperature: float = 0.0):
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, base_url=_OLLAMA_URL, temperature=temperature)

@lru_cache(maxsize=1)
def _get_json_llm(model: str = _LLM_MODEL, temperature: float = 0.0):
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, base_url=_OLLAMA_URL, temperature=temperature, format="json")

def default_synthesis_call(system_prompt: str, user_content: str) -> str:
    from langchain_core.messages import SystemMessage, HumanMessage
    resp = _get_json_llm().invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_content)])
    return resp.content if hasattr(resp, "content") else str(resp)

def parse_json(raw: str) -> Optional[dict[str, Any]]:
    if not raw: return None
    text = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try: return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try: return json.loads(m.group(0))
            except json.JSONDecodeError: return None
    return None

# ---- output models ----
class SupportingEvidence(BaseModel):
    source_type: str
    reference: str
    excerpt: str = ""

class KnowledgeContext(BaseModel):
    similar_cases: list[dict] = Field(default_factory=list)
    retrieved_playbooks: list[dict] = Field(default_factory=list)
    enterprise_recommendations: list[str] = Field(default_factory=list)
    missing_aws_recommendations: list[str] = Field(default_factory=list)
    supporting_evidence: list[SupportingEvidence] = Field(default_factory=list)
    reasoning: str = ""

class KnowledgeNodeError(BaseModel):
    error: str
    detail: str
