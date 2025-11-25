"""Main Streamlit application entry point."""

import streamlit as st
from config.settings import get_settings
from src.core.llm import get_llm_manager
from src.utils.logger import setup_logger

# Set up logging
logger = setup_logger()

# Page configuration
st.set_page_config(
    page_title="Workflow Builder",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize settings
settings = get_settings()

# Initialize LLM manager
llm_manager = get_llm_manager()

# Main title
st.title("🔧 Workflow Builder")
st.markdown("AI-powered workflow automation tool")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key status
    if settings.is_openai_configured:
        st.success("✅ OpenAI API Key configured")
    else:
        st.error("❌ OpenAI API Key not configured")
        st.info("Please set OPENAI_API_KEY in your .env file")
    
    # LLM Status
    if llm_manager.is_initialized:
        st.success("✅ LLM initialized")
    else:
        st.warning("⚠️ LLM not initialized")
        if st.button("Initialize LLM"):
            if llm_manager.initialize():
                st.success("LLM initialized successfully!")
                st.rerun()
            else:
                st.error("Failed to initialize LLM")
    
    st.divider()
    st.markdown("### Navigation")
    st.info("🚧 UI components coming in Phase 4")

# Main content
st.markdown("""
## Welcome to Workflow Builder!

This is a refactored version of the workflow builder with improved architecture.

### Current Status

✅ **Phase 1 Complete**: Foundation & Refactoring
- Project structure
- Configuration management
- Data models
- Logging system
- Helper utilities

✅ **Phase 2 Complete**: Core Engine Refactoring
- LLM management
- Graph builder
- Router
- Executor
- Node system

🚧 **Phase 3**: Storage & Persistence (Next)
🚧 **Phase 4**: UI Enhancement (Next)
🚧 **Phase 5**: Testing & QA (Next)
🚧 **Phase 6**: Documentation & Polish (Next)

### Getting Started

1. Make sure your `.env` file is configured with `OPENAI_API_KEY`
2. Initialize the LLM using the sidebar button
3. UI components will be available in Phase 4

### Architecture

The application is now structured with:
- **Models**: Data structures (Workflow, Node, State)
- **Core**: Engine components (LLM, Graph Builder, Router, Executor)
- **Nodes**: Node implementations (Agent Node, Base Node)
- **Utils**: Helper functions and validators
- **Config**: Configuration management

See `plan.md` for detailed implementation plan.
""")

# Footer
st.divider()
st.markdown(
    "<small>Workflow Builder v0.1.0 | Built with Streamlit, LangGraph, and OpenAI</small>",
    unsafe_allow_html=True
)

