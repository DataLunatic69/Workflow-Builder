"""Workflow visualization component."""

import streamlit as st
from typing import List, Optional
from streamlit_agraph import agraph, Node, Edge, Config
from src.models.workflow import Workflow
from src.models.node import Node as WorkflowNode
from config.settings import get_settings
from src.utils.helpers import get_node_display_name


def render_workflow_graph(workflow: Workflow, selected_node_id: Optional[str] = None):
    """
    Render workflow graph visualization.
    
    Args:
        workflow: The workflow to visualize
        selected_node_id: Optional selected node ID to highlight
    """
    if not workflow or not workflow.nodes:
        st.info("No workflow to display. Add nodes to see the graph.")
        return
    
    settings = get_settings()
    
    # Create nodes for visualization
    agraph_nodes: List[Node] = []
    agraph_edges: List[Edge] = []
    
    # Add START node
    agraph_nodes.append(
        Node(
            id=settings.start_node_id,
            label="START",
            shape="ellipse",
            color="#4CAF50",
            title="Workflow Entry Point"
        )
    )
    
    # Add workflow nodes
    node_ids = {node.id for node in workflow.nodes}
    
    for i, node in enumerate(workflow.nodes):
        is_selected = selected_node_id == node.id
        border_width = 3 if is_selected else 1
        node_color = "#FFC107" if is_selected else "#90CAF9"
        
        prompt_snippet = node.prompt[:100] + "..." if len(node.prompt) > 100 else node.prompt
        
        agraph_nodes.append(
            Node(
                id=node.id,
                label=f"{i+1}. {node.name}",
                shape="box",
                color=node_color,
                borderWidth=border_width,
                title=f"ID: {node.id}\nPrompt: {prompt_snippet}"
            )
        )
        
        # Add START -> first node edge
        if i == 0:
            agraph_edges.append(
                Edge(
                    source=settings.start_node_id,
                    target=node.id,
                    label="Start Flow",
                    color="#4CAF50",
                    width=2
                )
            )
        
        # Add routing edges
        default_target = node.routing_rules.default_target
        
        # Default routing edge
        if default_target == settings.end_node_id or default_target in node_ids:
            is_overridden = any(
                rule.output_key == settings.default_routing_key
                for rule in node.routing_rules.conditional_targets
            )
            
            if not is_overridden:
                edge_label = "default"
                if default_target == settings.end_node_id:
                    edge_label = "→ END"
                
                agraph_edges.append(
                    Edge(
                        source=node.id,
                        target=default_target,
                        label=edge_label,
                        color="#2196F3",
                        width=2
                    )
                )
        
        # Conditional routing edges
        for rule in node.routing_rules.conditional_targets:
            target_id = rule.target_node_id
            if target_id == settings.end_node_id or target_id in node_ids:
                agraph_edges.append(
                    Edge(
                        source=node.id,
                        target=target_id,
                        label=rule.output_key,
                        color="#FF9800",
                        width=2,
                        dashes=True
                    )
                )
    
    # Add END node if referenced
    has_end = any(
        edge.target == settings.end_node_id
        for edge in agraph_edges
    )
    
    if has_end:
        agraph_nodes.append(
            Node(
                id=settings.end_node_id,
                label="END",
                shape="ellipse",
                color="#F44336",
                title="Workflow End Point"
            )
        )
    
    # Configure graph
    config = Config(
        width=800,
        height=600,
        directed=True,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        collapsible=False,
        node={"labelProperty": "label"},
        link={"labelProperty": "label", "renderLabel": True},
        maxZoom=2,
        minZoom=0.1,
        staticGraphWithDragAndDrop=False,
        staticGraph=False,
    )
    
    # Render graph
    try:
        return_value = agraph(
            nodes=agraph_nodes,
            edges=agraph_edges,
            config=config
        )
        
        # Handle node selection
        if return_value:
            selected_id = return_value
            if selected_id and selected_id != st.session_state.get("selected_node_id"):
                st.session_state.selected_node_id = selected_id
                st.rerun()
                
    except Exception as e:
        st.error(f"Error rendering graph: {e}")
        st.info("Make sure streamlit-agraph is installed: `pip install streamlit-agraph`")

