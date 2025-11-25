"""Workflow execution engine."""

from typing import Dict, List, Optional, Any
from langgraph.graph import StateGraph
from config.settings import get_settings
from src.models.state import WorkflowState
from src.models.workflow import Workflow
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowExecutor:
    """Executes compiled workflows."""
    
    def __init__(self):
        """Initialize executor."""
        self.settings = get_settings()
    
    def execute(
        self,
        compiled_graph: StateGraph,
        initial_input: str,
        recursion_limit: int,
        execution_log: Optional[List[str]] = None
    ) -> tuple[WorkflowState, List[str]]:
        """
        Execute a compiled workflow graph.
        
        Args:
            compiled_graph: The compiled LangGraph graph
            initial_input: Initial input string for the workflow
            recursion_limit: Maximum recursion depth
            execution_log: Optional list to append execution logs to
            
        Returns:
            Tuple of (final_state, execution_log)
        """
        if execution_log is None:
            execution_log = []
        
        # Initialize state
        initial_state: WorkflowState = {
            "input": initial_input,
            "node_outputs": {},
            "last_response_content": "",
            "current_node_id": ""
        }
        
        logger.info(f"Starting workflow execution with input: '{initial_input[:100]}...'")
        execution_log.append(f"🚀 Starting workflow execution")
        execution_log.append(f"📥 Input: {initial_input[:200]}...")
        
        try:
            # Execute graph
            final_state = compiled_graph.invoke(
                initial_state,
                config={"recursion_limit": recursion_limit}
            )
            
            logger.info("Workflow execution completed successfully")
            execution_log.append(f"✅ Workflow execution completed")
            
            return final_state, execution_log
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {e}"
            logger.error(error_msg, exc_info=True)
            execution_log.append(f"❌ {error_msg}")
            
            # Return partial state
            error_state: WorkflowState = {
                "input": initial_input,
                "node_outputs": initial_state.get("node_outputs", {}),
                "last_response_content": f"ERROR: {error_msg}",
                "current_node_id": initial_state.get("current_node_id", "")
            }
            
            return error_state, execution_log
    
    def get_execution_summary(self, final_state: WorkflowState) -> Dict[str, Any]:
        """
        Get a summary of workflow execution.
        
        Args:
            final_state: The final workflow state
            
        Returns:
            Dictionary with execution summary
        """
        node_outputs = final_state.get("node_outputs", {})
        
        return {
            "nodes_executed": len(node_outputs),
            "node_outputs": node_outputs,
            "final_output": final_state.get("last_response_content", ""),
            "current_node": final_state.get("current_node_id", ""),
            "has_error": "ERROR" in final_state.get("last_response_content", "")
        }

