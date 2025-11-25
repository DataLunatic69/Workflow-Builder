"""Base node class."""

from abc import ABC, abstractmethod
from typing import List
from src.models.state import WorkflowState
from src.models.node import Node


class BaseNode(ABC):
    """Base class for all workflow nodes."""
    
    def __init__(self, node: Node):
        """
        Initialize base node.
        
        Args:
            node: The node model
        """
        self.node = node
    
    @abstractmethod
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the node logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        pass
    
    def prepare_context(self, state: WorkflowState) -> str:
        """
        Prepare input context for the node.
        
        Args:
            state: Current workflow state
            
        Returns:
            Context string
        """
        from src.core.router import Router
        
        router = Router()
        
        # First node uses initial input
        if not state.get("last_response_content"):
            return state.get("input", "")
        
        # Subsequent nodes use previous response (cleaned)
        prev_content = state.get("last_response_content", "")
        return router.clean_content(prev_content)
    
    def update_state(
        self,
        state: WorkflowState,
        response_content: str
    ) -> WorkflowState:
        """
        Update workflow state with node output.
        
        Args:
            state: Current workflow state
            response_content: Node output content
            
        Returns:
            Updated workflow state
        """
        updated_state = state.copy()
        
        # Ensure node_outputs dict exists
        if "node_outputs" not in updated_state:
            updated_state["node_outputs"] = {}
        
        # Store node output
        updated_state["node_outputs"][self.node.id] = str(response_content)
        updated_state["last_response_content"] = str(response_content)
        updated_state["current_node_id"] = self.node.id
        
        return updated_state

