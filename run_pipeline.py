"""
SentinelX Pipeline Runner
==========================
Compiles and runs the real 5-node LangGraph investigation pipeline
(Supervisor -> Business/Policy/Knowledge/Risk -> Response) end-to-end against
a live Postgres database and a live Ollama server. No mocking, no stubs, no
simulated fallbacks — every node uses its real dependencies exactly as it
would in production. (Each node still has its own internal grounded fallback
for when the LLM call itself fails at runtime — that's the nodes' built-in
resilience, not something this runner adds.)

Usage:
    python run_pipeline.py path/to/report.json
    python run_pipeline.py path/to/report.json --full-state
    python run_pipeline.py path/to/report.json --output result.json

Environment (defaults below are applied only if not already set in your shell):
    SENTINELX_LLM_MODEL     Ollama model every node reasons with (default: llama3.1)
    OLLAMA_BASE_URL         Ollama server URL (default: http://localhost:11434)
    DATABASE_URL            Postgres URL used by the Policy Node
    BUSINESS_DATABASE_URL   Postgres URL used by the Business Context Node
                            (falls back to DATABASE_URL if unset)

Prerequisites:
    - Postgres reachable at DATABASE_URL (tables + seed data are created automatically
      on first run — see agents/bussiness_context/database.py and agents/policy/database.py)
    - Ollama running (`ollama serve`) with the model pulled: `ollama pull llama3.1`
"""
from __future__ import annotations

import argparse
import json
import os
from functools import lru_cache
from typing import Any

# Must happen BEFORE importing any agent module below — every node module reads
# SENTINELX_LLM_MODEL exactly once, at import time, into a module-level constant
# used as the default model for its ChatOllama client (see e.g.
# agents/risk/utils.py:9, agents/response/utils.py:9, agents/knowledge/utils.py:8,
# agents/bussiness_context/utils.py:7, agents/policy/utils.py:7).
# NOTE: the tag must match exactly what `ollama list` shows — "llama3.1" alone
# only resolves if a "llama3.1:latest" tag was pulled; if only "llama3.1:8b"
# is present (as it is on this machine), the bare tag 404s at call time.
os.environ.setdefault("SENTINELX_LLM_MODEL", "llama3.1:8b")

from agents.supervisor_agent import build_graph, adapt_aws_report, InvestigationState
from agents.bussiness_context.node import business_context_node
from agents.policy.node import policy_node
from agents.knowledge.node import knowledge_node
from agents.risk.node import risk_assessment_node
from agents.response.node import response_planning_node


@lru_cache(maxsize=1)
def _compiled_graph():
    """Compile the real graph once (cached). Business Context / Policy hit
    Postgres, Knowledge hits FAISS, and every node's LLM reasoning calls the
    live Ollama server configured above — nothing here is mocked."""
    return build_graph({
        "Business": business_context_node,
        "Policy": policy_node,
        "Knowledge": knowledge_node,
        "Risk": risk_assessment_node,
        "Response": response_planning_node,
    })


def run_sentinelx_pipeline(injection: dict[str, Any], *, return_full_state: bool = False):
    """Run one AWS investigation report (or an already-flat incident dict) through
    the full SentinelX graph. `injection` is whatever's given as input:
    adapt_aws_report() normalizes either a nested AWS report (report_metadata /
    finding_summary / attack_analysis / ...) or an already-flat incident dict into
    the shape every node expects, and is a no-op if the input is already flat.

    Returns response_plan by default. Pass return_full_state=True to get the
    complete InvestigationState instead (business_context, policy_context,
    knowledge_context, risk_assessment, response_plan, completed_nodes,
    reasoning_log, ...).
    """
    graph = _compiled_graph()
    initial_state: InvestigationState = {"incident": adapt_aws_report(injection)}
    final_state = graph.invoke(initial_state)
    return final_state if return_full_state else final_state.get("response_plan")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the SentinelX investigation graph on an AWS investigation report.")
    parser.add_argument("report", help="Path to the AWS investigation report JSON (the 'injection').")
    parser.add_argument("--full-state", action="store_true",
                        help="Print the complete InvestigationState instead of just response_plan.")
    parser.add_argument("--output", help="Optional path to also write the result to a JSON file.")
    args = parser.parse_args()

    with open(args.report, encoding="utf-8") as f:
        injection = json.load(f)

    result = run_sentinelx_pipeline(injection, return_full_state=args.full_state)

    output_text = json.dumps(result, indent=2, default=str)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_text)
    print(output_text)


if __name__ == "__main__":
    main()
