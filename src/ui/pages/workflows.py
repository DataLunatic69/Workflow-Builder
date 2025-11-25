"""Workflows page for managing saved workflows."""

import streamlit as st
from src.storage import get_storage
from datetime import datetime


def render_workflows_page():
    """Render the workflows management page."""
    st.header("💾 Saved Workflows")
    
    storage = get_storage()
    
    # Load workflows
    try:
        workflows_metadata = storage.list_with_metadata()
    except Exception as e:
        st.error(f"Failed to load workflows: {e}")
        workflows_metadata = []
    
    if not workflows_metadata:
        st.info("No saved workflows. Create and save a workflow in the Builder page.")
        return
    
    st.markdown(f"Found **{len(workflows_metadata)}** saved workflow(s)")
    st.divider()
    
    # Display workflows
    for workflow_meta in workflows_metadata:
        workflow_id = workflow_meta["id"]
        
        with st.expander(f"📋 {workflow_meta.get('name', 'Unnamed')}"):
            col_info, col_actions = st.columns([2, 1])
            
            with col_info:
                st.markdown(f"**ID:** `{workflow_id}`")
                if workflow_meta.get('description'):
                    st.caption(workflow_meta['description'])
                
                st.caption(f"**Nodes:** {workflow_meta.get('node_count', 0)}")
                
                if workflow_meta.get('created_at'):
                    try:
                        created = datetime.fromisoformat(workflow_meta['created_at'])
                        st.caption(f"**Created:** {created.strftime('%Y-%m-%d %H:%M')}")
                    except:
                        pass
                
                if workflow_meta.get('updated_at'):
                    try:
                        updated = datetime.fromisoformat(workflow_meta['updated_at'])
                        st.caption(f"**Updated:** {updated.strftime('%Y-%m-%d %H:%M')}")
                    except:
                        pass
            
            with col_actions:
                if st.button("📂 Load", key=f"load_{workflow_id}"):
                    loaded = storage.load(workflow_id)
                    if loaded:
                        # Clear any compiled graph from previous workflow
                        if "compiled_graph" in st.session_state:
                            del st.session_state.compiled_graph
                        if "compiled_workflow_id" in st.session_state:
                            del st.session_state.compiled_workflow_id
                        if "recursion_limit" in st.session_state:
                            del st.session_state.recursion_limit
                        
                        # Clear execution log
                        st.session_state.execution_log = []
                        
                        # Set the new workflow
                        st.session_state.current_workflow = loaded
                        st.session_state.current_page = "builder"
                        st.success(f"✅ Workflow '{loaded.name}' loaded! (ID: {loaded.id})")
                        st.info("⚠️ Remember to compile the workflow before running it.")
                        st.rerun()
                
                if st.button("🗑️ Delete", key=f"delete_{workflow_id}"):
                    if storage.delete(workflow_id):
                        st.success("Workflow deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete workflow")

