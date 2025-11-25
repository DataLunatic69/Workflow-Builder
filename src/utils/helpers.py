"""Helper utility functions."""

import uuid
from typing import List, Optional
from src.models.node import Node
from src.models.workflow import Workflow


def generate_node_id() -> str:
    """
    Generate a unique node ID.
    
    Returns:
        Unique node ID string
    """
    return str(uuid.uuid4())


def get_node_display_name(
    node_id: str,
    nodes: Optional[List[Node]] = None,
    workflow: Optional[Workflow] = None
) -> str:
    """
    Get a display name for a node.
    
    Args:
        node_id: The node ID
        nodes: Optional list of nodes to search
        workflow: Optional workflow to search for nodes
        
    Returns:
        Display name for the node
    """
    from config.settings import get_settings
    
    settings = get_settings()
    
    # Special node IDs
    if node_id == settings.start_node_id:
        return "⏹️ START"
    if node_id == settings.end_node_id:
        return "🏁 END"
    
    # Search in provided nodes list
    if nodes:
        for i, node in enumerate(nodes):
            if node.id == node_id:
                return f"{i+1}. {node.name}"
    
    # Search in workflow
    if workflow:
        node = workflow.get_node(node_id)
        if node:
            index = workflow.nodes.index(node)
            return f"{index+1}. {node.name}"
    
    return f"Unknown ({node_id})"


def format_execution_log_entry(message: str, level: str = "info") -> str:
    """
    Format a message for execution log display.
    
    Args:
        message: The log message
        level: Log level (info, warning, error, success)
        
    Returns:
        Formatted log entry
    """
    icons = {
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅",
        "executing": "⚙️",
        "routing": "🚦",
    }
    
    icon = icons.get(level.lower(), "•")
    return f"{icon} {message}"

