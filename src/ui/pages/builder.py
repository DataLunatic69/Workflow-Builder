"""Workflow builder page."""

import streamlit as st
from src.models.workflow import Workflow
from src.core.graph_builder import GraphBuilder
from src.core.executor import WorkflowExecutor
from src.storage import get_storage
from src.ui.components.node_editor import render_node_editor
from src.ui.components.workflow_viewer import render_workflow_graph
from src.ui.components.execution_log import render_execution_log
from src.utils.validators import validate_workflow_structure
from src.utils.logger import get_logger

logger = get_logger(__name__)

def _clear_compilation_state():
    """Helper to clear compiled graph state."""
    keys_to_clear = ["compiled_graph", "compiled_workflow_id", "recursion_limit", "final_state"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def render_builder_page():
    """Render the main workflow builder page."""
    st.header("🔧 Workflow Builder")
    
    # Initialize session state
    if "current_workflow" not in st.session_state:
        st.session_state.current_workflow = Workflow(name="Untitled Workflow", description="")
    
    if "execution_log" not in st.session_state:
        st.session_state.execution_log = []
    
    if "selected_node_id" not in st.session_state:
        st.session_state.selected_node_id = None
    
    workflow = st.session_state.current_workflow
    storage = get_storage()
    
    # Debug: Show current workflow info (can be removed later)
    if st.session_state.get("debug_mode", False):
        with st.expander("🔍 Debug Info"):
            st.write(f"Current Workflow ID: `{workflow.id}`")
            st.write(f"Current Workflow Name: **{workflow.name}**")
            st.write(f"Number of Nodes: {len(workflow.nodes)}")
            if workflow.nodes:
                st.write("Node Names:", [n.name for n in workflow.nodes])
            compiled_id = st.session_state.get("compiled_workflow_id")
            st.write(f"Compiled Workflow ID: `{compiled_id if compiled_id else 'None'}`")
            st.write(f"Match: {'✅' if compiled_id == workflow.id else '❌'}")
    
    # Top toolbar
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("➕ New Workflow"):
            st.session_state.current_workflow = Workflow(name="Untitled Workflow", description="")
            st.session_state.execution_log = []
            st.session_state.selected_node_id = None
            _clear_compilation_state()
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
            # CRITICAL: Initialize selectbox state to prevent auto-selection
            # Only show selectbox if user explicitly wants to load
            if "show_load_select" not in st.session_state:
                st.session_state.show_load_select = False
            
            if st.button("📂 Load Workflow", key="show_load_btn"):
                st.session_state.show_load_select = True
                st.rerun()
            
            if st.session_state.show_load_select:
                # Get current workflow ID to set as default selection
                current_workflow_id = workflow.id if workflow.id in workflow_ids else workflow_ids[0]
                try:
                    default_index = workflow_ids.index(current_workflow_id) if current_workflow_id in workflow_ids else 0
                except ValueError:
                    default_index = 0
                
                selected_id = st.selectbox(
                    "Select Workflow to Load", 
                    workflow_ids, 
                    key="load_select",
                    index=default_index,
                    label_visibility="visible"
                )
                
                col_load_confirm, col_cancel = st.columns(2)
                with col_load_confirm:
                    if st.button("✅ Confirm Load", key="load_confirm_btn"):
                        loaded = storage.load(selected_id)
                        if loaded:
                            logger.info(f"Loading workflow: {loaded.name} (ID: {loaded.id})")
                            
                            # IMPORTANT: Clear ALL workflow-related state before loading
                            _clear_compilation_state()
                            st.session_state.execution_log = []
                            st.session_state.selected_node_id = None
                            st.session_state.show_load_select = False
                            
                            # Set the new workflow AFTER clearing state
                            st.session_state.current_workflow = loaded
                            
                            st.success(f"✅ Loaded '{loaded.name}' (ID: {loaded.id[:8]}...)")
                            st.info("⚠️ Remember to compile before running.")
                            st.rerun()
                
                with col_cancel:
                    if st.button("❌ Cancel", key="load_cancel_btn"):
                        st.session_state.show_load_select = False
                        st.rerun()
    
    with col4:
        if st.button("🔨 Compile Workflow"):
            if not workflow.nodes:
                st.warning("Add at least one node to compile")
            else:
                # Log which workflow we're compiling for debugging
                logger.info(f"Compiling workflow: {workflow.name} (ID: {workflow.id})")
                
                _clear_compilation_state() # Clear before re-compiling
                
                is_valid, error_msg = validate_workflow_structure(workflow)
                if not is_valid:
                    st.error(f"Validation failed: {error_msg}")
                else:
                    # Store workflow ID and name BEFORE compilation to ensure we're compiling the right one
                    workflow_id_before_compile = workflow.id
                    workflow_name_before_compile = workflow.name
                    
                    logger.info(f"Compiling workflow: {workflow_name_before_compile} (ID: {workflow_id_before_compile})")
                    
                    graph_builder = GraphBuilder()
                    compiled_graph, recursion_limit, error_msg = graph_builder.compile(workflow)
                    
                    if compiled_graph:
                        # CRITICAL: Verify workflow hasn't changed during compilation
                        if workflow.id == workflow_id_before_compile and workflow.name == workflow_name_before_compile:
                            st.session_state.compiled_graph = compiled_graph
                            st.session_state.compiled_workflow_id = workflow.id
                            st.session_state.compiled_workflow_name = workflow.name  # Store name too
                            st.session_state.recursion_limit = recursion_limit
                            logger.info(f"Successfully compiled: {workflow.name} (ID: {workflow.id})")
                            st.success(f"✅ Workflow '{workflow.name}' compiled successfully!")
                        else:
                            logger.warning(
                                f"Workflow changed during compilation! "
                                f"Was: {workflow_name_before_compile} ({workflow_id_before_compile}), "
                                f"Now: {workflow.name} ({workflow.id})"
                            )
                            st.error(
                                f"❌ Workflow changed during compilation!\n"
                                f"Was compiling: **{workflow_name_before_compile}** ({workflow_id_before_compile[:8]}...)\n"
                                f"Current workflow: **{workflow.name}** ({workflow.id[:8]}...)\n"
                                f"Please compile again."
                            )
                    else:
                        logger.error(f"Compilation failed for {workflow.name}: {error_msg}")
                        st.error(f"Compilation failed: {error_msg}")
    
    with col5:
        # Check if workflow is compiled and matches current workflow
        compiled_workflow_id = st.session_state.get("compiled_workflow_id")
        compiled_workflow_name = st.session_state.get("compiled_workflow_name", "Unknown")
        is_compiled = "compiled_graph" in st.session_state
        is_correct_workflow = compiled_workflow_id == workflow.id if compiled_workflow_id else False
        
        if not is_compiled:
            st.info("⚠️ Compile workflow first")
        elif not is_correct_workflow:
            st.error(
                f"❌ **Workflow Mismatch!**\n\n"
                f"Current: **{workflow.name}** (`{workflow.id[:8]}...`)\n\n"
                f"Compiled: **{compiled_workflow_name}** (`{compiled_workflow_id[:8] if compiled_workflow_id else 'None'}...`)\n\n"
                f"Please compile the current workflow."
            )
            if st.button("🔄 Clear Compiled", key="clear_compiled"):
                _clear_compilation_state()
                st.rerun()
        else:
            input_text = st.text_input("Input", key="run_input", placeholder="Input text...", label_visibility="collapsed")
            if st.button("▶️ Run", key="run_btn"):
                if not input_text:
                    st.warning("Enter input text")
                else:
                    # CRITICAL: Double-check we're running the right workflow
                    if st.session_state.get("compiled_workflow_id") != workflow.id:
                        st.error(
                            f"❌ **Workflow Mismatch Detected!**\n\n"
                            f"Current: **{workflow.name}** (`{workflow.id[:8]}...`)\n\n"
                            f"Compiled: **{compiled_workflow_name}** (`{compiled_workflow_id[:8]}...`)\n\n"
                            f"**Cannot run** - workflows don't match. Please compile first."
                        )
                    else:
                        logger.info(f"Executing workflow: {workflow.name} (ID: {workflow.id})")
                        
                        executor = WorkflowExecutor()
                        st.session_state.execution_log = []
                        st.session_state.execution_log.append(f"🔧 Running workflow: **{workflow.name}** (ID: `{workflow.id[:8]}...`)")
                        st.session_state.execution_log.append(f"📊 Nodes: {len(workflow.nodes)}")
                        
                        final_state, execution_log = executor.execute(
                            st.session_state.compiled_graph,
                            input_text,
                            st.session_state.recursion_limit,
                            execution_log=st.session_state.execution_log
                        )
                        st.session_state.execution_log = execution_log
                        st.session_state.final_state = final_state
                        st.success(f"✅ Workflow '{workflow.name}' execution completed!")
                        st.rerun()
    
    st.divider()
    
    # Metadata editing
    col_name, col_desc = st.columns([1, 2])
    with col_name:
        new_name = st.text_input("Workflow Name", value=workflow.name)
        if new_name != workflow.name:
            workflow.name = new_name
    with col_desc:
        new_desc = st.text_input("Description", value=workflow.description or "")
        if new_desc != workflow.description:
            workflow.description = new_desc

    # Nodes and Graph
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("📝 Nodes")
        if st.button("➕ Add Node"):
            st.session_state.show_node_editor = True
            st.session_state.editing_node_id = None
        
        if workflow.nodes:
            for i, node in enumerate(workflow.nodes):
                with st.expander(f"{i+1}. {node.name}"):
                    st.caption(f"Prompt: {node.prompt[:60]}...")
                    c1, c2 = st.columns(2)
                    if c1.button("✏️ Edit", key=f"edit_{node.id}"):
                        st.session_state.show_node_editor = True
                        st.session_state.editing_node_id = node.id
                        st.rerun()
                    if c2.button("🗑️ Delete", key=f"del_{node.id}"):
                        workflow.remove_node(node.id)
                        _clear_compilation_state() # Invalidate graph on edit
                        st.rerun()

        # Node Editor Modal Logic
        if st.session_state.get("show_node_editor", False):
            editing_node = workflow.get_node(st.session_state.editing_node_id) if st.session_state.get("editing_node_id") else None
            edited_node = render_node_editor(editing_node, workflow.nodes)
            
            if edited_node:
                if editing_node:
                    editing_node.name = edited_node.name
                    editing_node.prompt = edited_node.prompt
                    editing_node.routing_rules = edited_node.routing_rules
                else:
                    workflow.add_node(edited_node)
                
                st.session_state.show_node_editor = False
                st.session_state.editing_node_id = None
                _clear_compilation_state() # Invalidate graph on edit
                st.rerun()
            
            if st.button("Cancel", key="cancel_edit"):
                st.session_state.show_node_editor = False
                st.session_state.editing_node_id = None
                st.rerun()

    with col_right:
        st.subheader("📊 Graph")
        render_workflow_graph(workflow, st.session_state.selected_node_id)
    
    st.divider()
    render_execution_log()