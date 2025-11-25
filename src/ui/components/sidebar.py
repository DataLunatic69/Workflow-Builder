"""Sidebar component for navigation and configuration."""

import streamlit as st
from config.settings import get_settings
from src.core.llm import get_llm_manager
from src.storage import get_storage


def render_sidebar():
    """Render the sidebar with navigation and configuration."""
    settings = get_settings()
    llm_manager = get_llm_manager()
    storage = get_storage()
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key status
        if settings.is_groq_configured:
            st.success("✅ Groq API Key configured")
        else:
            st.error("❌ Groq API Key not configured")
            st.info("Please set GROQ_API_KEY in your .env file")
        
        # LLM Status
        if llm_manager.is_initialized:
            st.success("✅ LLM initialized")
            if st.button("🔄 Reinitialize LLM"):
                llm_manager.clear()
                if llm_manager.initialize():
                    st.success("LLM reinitialized!")
                    st.rerun()
        else:
            st.warning("⚠️ LLM not initialized")
            if st.button("Initialize LLM"):
                if llm_manager.initialize():
                    st.success("LLM initialized successfully!")
                    st.rerun()
                else:
                    st.error("Failed to initialize LLM")
        
        st.divider()
        
        # Navigation
        st.header("🧭 Navigation")
        
        # Initialize session state for page
        if "current_page" not in st.session_state:
            st.session_state.current_page = "builder"
        
        page = st.radio(
            "Select Page",
            ["Builder", "Templates", "Workflows", "Settings"],
            index=["builder", "templates", "workflows", "settings"].index(
                st.session_state.current_page
            ) if st.session_state.current_page in ["builder", "templates", "workflows", "settings"] else 0,
            label_visibility="collapsed"
        )
        
        # Update page based on selection
        page_map = {
            "Builder": "builder",
            "Templates": "templates",
            "Workflows": "workflows",
            "Settings": "settings"
        }
        st.session_state.current_page = page_map[page]
        
        st.divider()
        
        # Workflow stats
        st.header("📊 Stats")
        try:
            workflow_count = len(storage.list_all())
            st.metric("Saved Workflows", workflow_count)
        except Exception as e:
            st.warning(f"Could not load stats: {e}")
        
        # Current workflow info
        if "current_workflow" in st.session_state and st.session_state.current_workflow:
            workflow = st.session_state.current_workflow
            st.divider()
            st.header("📝 Current Workflow")
            st.text(f"Name: {workflow.name}")
            st.text(f"Nodes: {len(workflow.nodes)}")
            if workflow.description:
                st.caption(workflow.description[:100])

