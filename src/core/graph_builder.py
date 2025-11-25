"""Graph compilation and building logic."""

from typing import Dict, List, Optional, Any
from langgraph.graph import StateGraph, START, END
from config.settings import get_settings
from src.models.workflow import Workflow
from src.models.state import WorkflowState
from src.core.llm import get_llm_manager
from src.core.router import Router
from src.nodes.node_factory import NodeFactory
from src.utils.logger import get_logger
# Checkpointer for state persistence (optional)
# Set to None if checkpointing is not needed
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()  # Use MemorySaver for checkpointing
# Set to None if you don't need checkpointing: checkpointer = None

logger = get_logger(__name__)


class GraphBuilder:
    """Builds and compiles LangGraph workflows from Workflow models."""
    
    def __init__(self):
        """Initialize graph builder."""
        self.settings = get_settings()
        self.router = Router()
        self.node_factory = NodeFactory()
    
    def compile(self, workflow: Workflow) -> tuple[Optional[Any], Optional[int], Optional[str]]:
        """
        Compile a workflow into a LangGraph executable graph.
        
        Args:
            workflow: The workflow to compile
            
        Returns:
            Tuple of (compiled_graph, recursion_limit, error_message)
        """
        # Validate workflow
        from src.utils.validators import validate_workflow_structure
        is_valid, error_msg = validate_workflow_structure(workflow)
        if not is_valid:
            logger.error(f"Workflow validation failed: {error_msg}")
            return None, None, error_msg
        
        # Check LLM initialization
        llm_manager = get_llm_manager()
        if not llm_manager.is_initialized:
            error_msg = "LLM not initialized. Please configure GROQ_API_KEY."
            logger.error(error_msg)
            return None, None, error_msg
        
        if not workflow.nodes:
            error_msg = "Workflow has no nodes"
            logger.error(error_msg)
            return None, None, error_msg
        
        try:
            logger.info(f"Compiling workflow '{workflow.name}' with {len(workflow.nodes)} nodes")
            
            # Create graph builder
            graph_builder = StateGraph(WorkflowState)
            
            # Get all node IDs for validation
            node_ids = set(workflow.get_node_ids())
            all_valid_targets = node_ids.copy()
            all_valid_targets.add(self.settings.end_node_id)
            
            # Add nodes to graph
            logger.debug("Adding nodes to graph")
            possible_keys_per_node: Dict[str, List[str]] = {}
            
            for node in workflow.nodes:
                # Collect possible routing keys for this node
                # Only include actual routing keys, not 'error' (error is handled automatically)
                cond_keys = {
                    rule.output_key
                    for rule in node.routing_rules.conditional_targets
                    if rule.output_key and rule.output_key != "error"
                }
                # Add default routing key (but not 'error' - that's implicit)
                all_keys = cond_keys.union({
                    self.settings.default_routing_key
                })
                # Note: 'error' is handled automatically by the router, don't show it to LLM
                possible_keys_per_node[node.id] = list(all_keys)
                
                # Create node function
                node_func = self.node_factory.create_node_function(
                    node=node,
                    possible_keys=possible_keys_per_node[node.id]
                )
                
                # Add to graph
                graph_builder.add_node(node.id, node_func)
                logger.debug(f"Added node: {node.name} ({node.id})")
            
            # Add START -> first node edge
            start_node_id = workflow.nodes[0].id
            graph_builder.add_edge(START, start_node_id)
            logger.debug(f"Added START -> {workflow.nodes[0].name}")
            
            # Add conditional edges for each node
            all_targets_valid = True
            
            for node in workflow.nodes:
                routing_map = {}
                seen_keys = set()
                
                # Helper function to convert END string to END constant
                def convert_target(target: str):
                    """Convert 'END' string to END constant for LangGraph."""
                    if target == self.settings.end_node_id:
                        return END
                    return target
                
                # Add conditional routing rules
                for rule in node.routing_rules.conditional_targets:
                    key = rule.output_key.strip()
                    target_id = rule.target_node_id.strip()
                    
                    if not key or not target_id:
                        logger.warning(
                            f"Incomplete routing rule in node '{node.name}', skipping"
                        )
                        continue
                    
                    # Validate target
                    if target_id != self.settings.end_node_id and target_id not in node_ids:
                        error_msg = (
                            f"Invalid target '{target_id}' for node '{node.name}' "
                            f"routing key '{key}'"
                        )
                        logger.error(error_msg)
                        all_targets_valid = False
                        continue
                    
                    # Check for duplicate keys
                    if key in seen_keys:
                        logger.warning(
                            f"Duplicate routing key '{key}' in node '{node.name}'"
                        )
                    
                    # Convert END string to END constant
                    routing_map[key] = convert_target(target_id)
                    seen_keys.add(key)
                    logger.debug(
                        f"  Routing rule: '{key}' -> {target_id}"
                    )
                
                # Add default routing
                default_target = node.routing_rules.default_target
                if self.settings.default_routing_key not in routing_map:
                    if default_target != self.settings.end_node_id and default_target not in node_ids:
                        error_msg = (
                            f"Invalid default target '{default_target}' "
                            f"for node '{node.name}'"
                        )
                        logger.error(error_msg)
                        all_targets_valid = False
                    else:
                        # Convert END string to END constant
                        routing_map[self.settings.default_routing_key] = convert_target(default_target)
                        logger.debug(
                            f"  Default routing -> {default_target}"
                        )
                
                # Add error routing (implicit)
                if "error" not in routing_map:
                    routing_map["error"] = END  # Always use END constant for error routing
                
                # Add conditional edges if valid
                if all_targets_valid:
                    graph_builder.add_conditional_edges(
                        node.id,
                        lambda state: self.router.route(state, routing_map),
                        routing_map
                    )
            
            if not all_targets_valid:
                error_msg = "Graph compilation failed due to invalid routing targets"
                logger.error(error_msg)
                return None, None, error_msg
            
            # Compile graph
            compiled_graph = graph_builder.compile(checkpointer=checkpointer)
            
            # Calculate recursion limit
            recursion_limit = (
                len(workflow.nodes) * self.settings.default_recursion_multiplier +
                self.settings.default_recursion_base
            )
            
            logger.info(
                f"Graph compiled successfully (recursion limit: {recursion_limit})"
            )
            
            return compiled_graph, recursion_limit, None
            
        except Exception as e:
            error_msg = f"Graph compilation error: {e}"
            logger.error(error_msg, exc_info=True)
            return None, None, error_msg

