"""Shared local LLM configuration (Llama 3.2 via Ollama) and a structured
JSON invocation helper.

Every node in the graph — supervisor, business, policy, knowledge, risk,
response — goes through `get_llm()` and `invoke_structured()` so the whole
platform runs on exactly one LLM configuration, in strict JSON mode, with
schema validation and one bounded self-correction retry. Nothing else in
the codebase should import `langchain_ollama` directly.
"""
from __future__ import annotations

from functools import lru_cache
from typing import TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel, ValidationError

from config.settings import get_settings
from utils.json_utils import JSONExtractionError, extract_json_object
from utils.logging import get_logger

logger = get_logger(__name__)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMOutputError(RuntimeError):
    """Raised when the LLM's output could not be parsed into the target schema
    even after the self-correction retry."""


@lru_cache(maxsize=4)
def get_llm(temperature: float | None = None) -> ChatOllama:
    """Returns a cached ChatOllama client for Llama 3.2, configured for
    strict JSON output. `temperature` overrides the configured default
    (nodes that need to be maximally deterministic, e.g. the Supervisor,
    should pass `temperature=0.0` explicitly).
    """
    settings = get_settings()
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=settings.ollama_temperature if temperature is None else temperature,
        format="json",
        client_kwargs={"timeout": settings.ollama_request_timeout},
    )


def invoke_structured(
    system_prompt: str,
    user_prompt: str,
    schema: type[SchemaT],
    *,
    temperature: float | None = None,
) -> SchemaT:
    """Invokes the shared LLM with a system/user prompt pair and validates
    the JSON response against `schema`, retrying once with the validation
    error fed back to the model if parsing/validation fails.
    """
    llm = get_llm(temperature=temperature)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

    last_error: Exception | None = None
    for attempt in range(2):
        response = llm.invoke(messages)
        raw_text = response.content if isinstance(response.content, str) else str(response.content)
        try:
            payload = extract_json_object(raw_text)
            return schema.model_validate(payload)
        except (JSONExtractionError, ValidationError) as error:
            last_error = error
            logger.warning(
                "llm_output_validation_failed",
                schema=schema.__name__,
                attempt=attempt + 1,
                error=str(error),
            )
            messages.append(HumanMessage(
                content=(
                    "Your previous response was not valid JSON matching the required "
                    f"schema. Error: {error}\n\nRespond again with ONLY a single valid "
                    "JSON object matching the schema, no prose, no markdown fences."
                )
            ))

    raise LLMOutputError(
        f"Failed to obtain valid {schema.__name__} output after retries: {last_error}"
    )
