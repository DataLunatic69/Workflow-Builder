"""Settings page for application configuration."""

import streamlit as st
from config.settings import get_settings
from src.core.llm import get_llm_manager


def render_settings_page():
    """Render the settings page."""
    st.header("⚙️ Settings")
    
    settings = get_settings()
    llm_manager = get_llm_manager()
    
    st.markdown("Configure application settings and preferences.")
    st.divider()
    
    # API Configuration
    st.subheader("🔑 API Configuration")
    
    st.info(
        "API keys are configured via environment variables. "
        "Set `GROQ_API_KEY` in your `.env` file."
    )
    
    if settings.is_groq_configured:
        st.success("✅ Groq API Key is configured")
        st.caption(f"Key starts with: {settings.groq_api_key[:10]}...")
    else:
        st.error("❌ Groq API Key is not configured")
        st.markdown("""
        To configure:
        1. Create a `.env` file in the project root
        2. Add: `GROQ_API_KEY=your_api_key_here`
        3. Restart the application
        """)
    
    st.divider()
    
    # LLM Configuration
    st.subheader("🤖 LLM Configuration")
    
    col_model, col_temp = st.columns(2)
    
    with col_model:
        st.text_input(
            "Model Name",
            value=settings.llm_model_name,
            disabled=True,
            help="Configure via LLM_MODEL_NAME environment variable"
        )
    
    with col_temp:
        st.number_input(
            "Temperature",
            value=settings.llm_temperature,
            min_value=0.0,
            max_value=2.0,
            step=0.1,
            disabled=True,
            help="Configure via LLM_TEMPERATURE environment variable"
        )
    
    st.info("LLM settings are configured via environment variables. Restart the app after changing them.")
    
    st.divider()
    
    # LLM Status
    st.subheader("📊 LLM Status")
    
    if llm_manager.is_initialized:
        st.success("✅ LLM is initialized and ready")
        
        if st.button("🔄 Reinitialize LLM"):
            llm_manager.clear()
            if llm_manager.initialize():
                st.success("LLM reinitialized successfully!")
                st.rerun()
            else:
                st.error("Failed to reinitialize LLM")
    else:
        st.warning("⚠️ LLM is not initialized")
        
        if st.button("▶️ Initialize LLM"):
            if llm_manager.initialize():
                st.success("LLM initialized successfully!")
                st.rerun()
            else:
                st.error("Failed to initialize LLM. Check your API key configuration.")
    
    st.divider()
    
    # Storage Configuration
    st.subheader("💾 Storage Configuration")
    
    st.text_input(
        "Storage Path",
        value=str(settings.workflow_storage_path),
        disabled=True,
        help="Configure via WORKFLOW_STORAGE_PATH environment variable"
    )
    
    st.info("Workflows are stored as JSON files in the storage directory.")
    
    st.divider()
    
    # Application Info
    st.subheader("ℹ️ Application Information")
    
    st.markdown(f"""
    - **Version:** 0.1.0
    - **Storage Path:** `{settings.workflow_storage_path}`
    - **Log Level:** `{settings.log_level}`
    - **Log File:** `{settings.log_file}`
    """)

