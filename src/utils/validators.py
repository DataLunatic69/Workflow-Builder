"""Validation utilities for workflows and nodes."""

from typing import List, Tuple, Optional
from src.models.node import Node
from src.models.workflow import Workflow


def validate_node(node: Node, all_node_ids: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate a single node.
    
    Args:
        node: The node to validate
        all_node_ids: List of all valid node IDs (including "END")
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check default target
    default_target = node.routing_rules.default_target
    if default_target != "END" and default_target not in all_node_ids:
        return False, f"Node '{node.name}' has invalid default target: {default_target}"
    
    # Check conditional targets
    for rule in node.routing_rules.conditional_targets:
        if rule.target_node_id != "END" and rule.target_node_id not in all_node_ids:
            return False, (
                f"Node '{node.name}' has invalid conditional target "
                f"'{rule.output_key}' -> '{rule.target_node_id}'"
            )
    
    # Check for duplicate routing keys
    routing_keys = [rule.output_key for rule in node.routing_rules.conditional_targets]
    if len(routing_keys) != len(set(routing_keys)):
        return False, f"Node '{node.name}' has duplicate routing keys"
    
    return True, None


def validate_workflow_structure(workflow: Workflow) -> Tuple[bool, Optional[str]]:
    """
    Validate workflow structure.
    
    Args:
        workflow: The workflow to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not workflow.nodes:
        return False, "Workflow must contain at least one node"
    
    # Check for duplicate node IDs
    node_ids = workflow.get_node_ids()
    if len(node_ids) != len(set(node_ids)):
        return False, "Workflow contains duplicate node IDs"
    
    # Validate all nodes
    all_node_ids = set(node_ids)
    all_node_ids.add("END")  # END is a valid target
    
    for node in workflow.nodes:
        is_valid, error_msg = validate_node(node, list(all_node_ids))
        if not is_valid:
            return False, error_msg
    
    return True, None


def validate_graph_connectivity(workflow: Workflow) -> Tuple[bool, Optional[str]]:
    """
    Validate that the workflow graph is properly connected.
    
    This checks that:
    - All nodes are reachable from the start
    - No orphaned nodes exist
    
    Args:
        workflow: The workflow to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not workflow.nodes:
        return True, None
    
    # Build adjacency list
    node_ids = set(workflow.get_node_ids())
    reachable = set()
    
    # Start from first node
    if workflow.nodes:
        queue = [workflow.nodes[0].id]
        reachable.add(workflow.nodes[0].id)
        
        while queue:
            current_id = queue.pop(0)
            node = workflow.get_node(current_id)
            if not node:
                continue
            
            # Get all targets from this node
            targets = node.routing_rules.get_all_targets()
            for target in targets:
                if target != "END" and target in node_ids:
                    if target not in reachable:
                        reachable.add(target)
                        queue.append(target)
    
    # Check if all nodes are reachable
    unreachable = node_ids - reachable
    if unreachable:
        unreachable_names = [
            workflow.get_node(nid).name if workflow.get_node(nid) else nid
            for nid in unreachable
        ]
        return False, f"Unreachable nodes found: {', '.join(unreachable_names)}"
    
    return True, None

