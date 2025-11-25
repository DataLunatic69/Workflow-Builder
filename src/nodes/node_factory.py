"""Node factory for creating node execution functions."""

from typing import List, Callable
from src.models.node import Node
from src.models.state import WorkflowState
from src.nodes.agent_node import AgentNode
from src.utils.logger import get_logger

logger = get_logger(__name__)


class NodeFactory:
    """Factory for creating node execution functions."""
    
    def create_node_function(
        self,
        node: Node,
        possible_keys: List[str]
    ) -> Callable[[WorkflowState], WorkflowState]:
        """
        Create a node execution function for LangGraph.
        
        Args:
            node: The node model
            possible_keys: List of possible routing keys
            
        Returns:
            Node execution function
        """
        # For now, only agent nodes are supported
        agent_node = AgentNode(node, possible_keys)
        
        def node_function(state: WorkflowState) -> WorkflowState:
            """
            Node execution function wrapper.
            
            Args:
                state: Current workflow state
                
            Returns:
                Updated workflow state
            """
            return agent_node.execute(state)
        
        return node_function


# Singleton instance
_node_factory: NodeFactory = None


def get_node_factory() -> NodeFactory:
    """
    Get the global node factory instance.
    
    Returns:
        NodeFactory instance
    """
    global _node_factory
    if _node_factory is None:
        _node_factory = NodeFactory()
    return _node_factory

