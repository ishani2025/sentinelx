"""Strongly typed Pydantic models for every InvestigationState section.

Each node in the graph reads a subset of these models from state and writes
back exactly one of them. See `graph.state.InvestigationState` for how these
compose into the shared workflow state.
"""
