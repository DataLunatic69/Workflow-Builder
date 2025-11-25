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
            # Generate a unique thread_id for this execution
            import uuid
            thread_id = str(uuid.uuid4())
            
            # Configure execution with thread_id (required if using checkpointer)
            # and recursion_limit
            config = {
                "recursion_limit": recursion_limit,
                "configurable": {
                    "thread_id": thread_id
                }
            }
            
            final_state = compiled_graph.invoke(
                initial_state,
                config=config
            )
            
            # Check if execution ended in error state
            last_response = final_state.get("last_response_content", "")
            node_outputs = final_state.get("node_outputs", {})
            
            # Check for errors in node outputs or final response
            has_error = False
            error_details = []
            
            if "ERROR" in last_response.upper():
                has_error = True
                error_details.append(f"Final state error: {last_response}")
            
            for node_id, output in node_outputs.items():
                if "ERROR" in str(output).upper():
                    has_error = True
                    error_details.append(f"Node {node_id} error: {output[:200]}")
            
            if has_error:
                logger.error(f"Workflow execution completed with errors: {error_details}")
                execution_log.append(f"❌ Workflow execution completed with errors")
                for detail in error_details:
                    execution_log.append(f"  ⚠️ {detail[:300]}")
            else:
                logger.info("Workflow execution completed successfully")
                execution_log.append(f"✅ Workflow execution completed")
                # Show final output
                if last_response and "ERROR" not in last_response.upper():
                    execution_log.append(f"📤 Final output: {last_response[:500]}...")
            
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

