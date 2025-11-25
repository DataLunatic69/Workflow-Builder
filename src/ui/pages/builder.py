"""Workflow builder page."""

import streamlit as st
from src.models.workflow import Workflow
from src.models.node import Node
from src.core.graph_builder import GraphBuilder
from src.core.executor import WorkflowExecutor
from src.storage import get_storage
from src.ui.components.node_editor import render_node_editor
from src.ui.components.workflow_viewer import render_workflow_graph
from src.ui.components.execution_log import render_execution_log
from src.utils.validators import validate_workflow_structure
from src.utils.helpers import generate_node_id


def render_builder_page():
    """Render the main workflow builder page."""
    st.header("🔧 Workflow Builder")
    
    # Initialize session state
    if "current_workflow" not in st.session_state:
        st.session_state.current_workflow = Workflow(
            name="Untitled Workflow",
            description=""
        )
    
    if "execution_log" not in st.session_state:
        st.session_state.execution_log = []
    
    if "selected_node_id" not in st.session_state:
        st.session_state.selected_node_id = None
    
    workflow = st.session_state.current_workflow
    storage = get_storage()
    
    # Top toolbar
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("➕ New Workflow"):
            st.session_state.current_workflow = Workflow(
                name="Untitled Workflow",
                description=""
            )
            st.session_state.execution_log = []
            st.session_state.selected_node_id = None
            st.rerun()
    
    with col2:
        if st.button("💾 Save Workflow"):
            if workflow.name == "Untitled Workflow":
                workflow.name = st.text_input("Workflow Name", value="My Workflow")
            
            if storage.save(workflow):
                st.success(f"Workflow '{workflow.name}' saved!")
            else:
                st.error("Failed to save workflow")
    
    with col3:
        workflow_ids = storage.list_all()
        if workflow_ids:
            selected_id = st.selectbox("Select Workflow", workflow_ids, key="load_select")
            if st.button("📂 Load", key="load_btn"):
                loaded = storage.load(selected_id)
                if loaded:
                    st.session_state.current_workflow = loaded
                    st.session_state.execution_log = []
                    st.session_state.selected_node_id = None
                    st.success("Workflow loaded!")
                    st.rerun()
        else:
            st.info("No saved workflows")
    
    with col4:
        if st.button("🔨 Compile Workflow"):
            if not workflow.nodes:
                st.warning("Add at least one node to compile")
            else:
                # Validate workflow
                is_valid, error_msg = validate_workflow_structure(workflow)
                if not is_valid:
                    st.error(f"Validation failed: {error_msg}")
                else:
                    graph_builder = GraphBuilder()
                    compiled_graph, recursion_limit, error_msg = graph_builder.compile(workflow)
                    
                    if compiled_graph:
                        st.session_state.compiled_graph = compiled_graph
                        st.session_state.recursion_limit = recursion_limit
                        st.success("✅ Workflow compiled successfully!")
                    else:
                        st.error(f"Compilation failed: {error_msg}")
    
    with col5:
        if "compiled_graph" not in st.session_state:
            st.info("Compile first")
        else:
            input_text = st.text_input("Input", key="run_input", placeholder="Enter input for workflow")
            if st.button("▶️ Run Workflow", key="run_btn"):
                if not input_text:
                    st.warning("Please enter input text")
                else:
                    executor = WorkflowExecutor()
                    st.session_state.execution_log = []
                    final_state, execution_log = executor.execute(
                        st.session_state.compiled_graph,
                        input_text,
                        st.session_state.recursion_limit,
                        execution_log=st.session_state.execution_log
                    )
                    st.session_state.execution_log = execution_log
                    st.session_state.final_state = final_state
                    st.success("Workflow execution completed!")
                    st.rerun()
    
    st.divider()
    
    # Workflow name and description
    col_name, col_desc = st.columns([1, 2])
    with col_name:
        workflow_name = st.text_input(
            "Workflow Name",
            value=workflow.name,
            key="workflow_name_input"
        )
        if workflow_name != workflow.name:
            workflow.name = workflow_name
    
    with col_desc:
        workflow_desc = st.text_input(
            "Description",
            value=workflow.description or "",
            key="workflow_desc_input"
        )
        if workflow_desc != workflow.description:
            workflow.description = workflow_desc
    
    st.divider()
    
    # Main content area
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("📝 Nodes")
        
        # Add node button
        if st.button("➕ Add Node"):
            st.session_state.show_node_editor = True
            st.session_state.editing_node_id = None
        
        # Node list
        if workflow.nodes:
            for i, node in enumerate(workflow.nodes):
                with st.expander(f"{i+1}. {node.name}", expanded=False):
                    st.text(f"ID: {node.id}")
                    st.text(f"Prompt: {node.prompt[:100]}...")
                    
                    col_edit, col_delete = st.columns(2)
                    with col_edit:
                        if st.button("✏️ Edit", key=f"edit_{node.id}"):
                            st.session_state.show_node_editor = True
                            st.session_state.editing_node_id = node.id
                            st.rerun()
                    
                    with col_delete:
                        if st.button("🗑️ Delete", key=f"delete_{node.id}"):
                            workflow.remove_node(node.id)
                            st.rerun()
        
        # Node editor
        if st.session_state.get("show_node_editor", False):
            editing_node = None
            if st.session_state.get("editing_node_id"):
                editing_node = workflow.get_node(st.session_state.editing_node_id)
            
            edited_node = render_node_editor(editing_node, workflow.nodes)
            
            if edited_node:
                if editing_node:
                    # Update existing node
                    editing_node.name = edited_node.name
                    editing_node.prompt = edited_node.prompt
                    editing_node.routing_rules = edited_node.routing_rules
                else:
                    # Add new node
                    workflow.add_node(edited_node)
                
                st.session_state.show_node_editor = False
                st.session_state.editing_node_id = None
                st.rerun()
            
            if st.button("Cancel", key="cancel_edit"):
                st.session_state.show_node_editor = False
                st.session_state.editing_node_id = None
                st.rerun()
    
    with col_right:
        st.subheader("📊 Workflow Graph")
        render_workflow_graph(workflow, st.session_state.selected_node_id)
    
    st.divider()
    
    # Execution log
    render_execution_log()

