"""Templates page for browsing and loading workflow templates."""

import streamlit as st
from src.storage import get_template_loader
from src.storage import get_storage


def render_templates_page():
    """Render the templates page."""
    st.header("📝 Workflow Templates")
    
    template_loader = get_template_loader()
    storage = get_storage()
    
    # Load templates
    templates = template_loader.list_templates()
    
    if not templates:
        st.info("No templates found. Check the templates/example_workflows directory.")
        return
    
    st.markdown("Browse and load pre-built workflow templates.")
    st.divider()
    
    # Display templates
    for template in templates:
        with st.expander(f"📋 {template['name']}"):
            st.markdown(f"**Description:** {template.get('description', 'No description')}")
            
            metadata = template.get('metadata', {})
            if metadata:
                st.caption(f"Category: {metadata.get('category', 'general')}")
            
            col_load, col_preview = st.columns(2)
            
            with col_load:
                if st.button(f"📥 Load Template", key=f"load_{template['id']}"):
                    loaded_workflow = template_loader.load_template(template['id'])
                    if loaded_workflow:
                        # Generate new ID for the loaded workflow
                        from src.utils.helpers import generate_node_id
                        loaded_workflow.id = generate_node_id()
                        loaded_workflow.name = f"{loaded_workflow.name} (Copy)"
                        
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
                        st.session_state.current_workflow = loaded_workflow
                        st.session_state.current_page = "builder"
                        st.success(f"✅ Template '{template['name']}' loaded! (ID: {loaded_workflow.id})")
                        st.info("⚠️ Remember to compile the workflow before running it.")
                        st.rerun()
                    else:
                        st.error("Failed to load template")
            
            with col_preview:
                if st.button(f"👁️ Preview", key=f"preview_{template['id']}"):
                    st.session_state.preview_template_id = template['id']
                    st.rerun()
    
    # Template preview
    if st.session_state.get("preview_template_id"):
        st.divider()
        st.subheader("🔍 Template Preview")
        
        preview_id = st.session_state.preview_template_id
        preview_workflow = template_loader.load_template(preview_id)
        
        if preview_workflow:
            st.markdown(f"**Name:** {preview_workflow.name}")
            st.markdown(f"**Description:** {preview_workflow.description or 'No description'}")
            st.markdown(f"**Nodes:** {len(preview_workflow.nodes)}")
            
            st.markdown("**Node Structure:**")
            for i, node in enumerate(preview_workflow.nodes):
                st.markdown(f"{i+1}. **{node.name}**")
                st.caption(f"   Prompt: {node.prompt[:100]}...")
                st.caption(f"   Default target: {node.routing_rules.default_target}")
                if node.routing_rules.conditional_targets:
                    st.caption(f"   Conditional routes: {len(node.routing_rules.conditional_targets)}")
            
            if st.button("Close Preview"):
                st.session_state.preview_template_id = None
                st.rerun()

