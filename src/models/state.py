"""Workflow state model."""

from typing import Dict, TypedDict


class WorkflowState(TypedDict):
    """
    State dictionary for workflow execution.
    
    This matches the LangGraph state structure used throughout the application.
    """
    input: str
    node_outputs: Dict[str, str]
    last_response_content: str
    current_node_id: str

