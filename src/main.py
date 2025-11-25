"""Main Streamlit application entry point."""

import sys
import os
from pathlib import Path

# Add project root to Python path
# Get the directory containing this file (src/)
current_dir = Path(__file__).resolve().parent
# Get the project root (parent of src/)
project_root = current_dir.parent
# Add to Python path if not already there
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

import streamlit as st
from src.ui.components.sidebar import render_sidebar
from src.ui.pages.builder import render_builder_page
from src.ui.pages.templates import render_templates_page
from src.ui.pages.workflows import render_workflows_page
from src.ui.pages.settings import render_settings_page
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

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "builder"

# Render sidebar
render_sidebar()

# Main content area - route to appropriate page
current_page = st.session_state.current_page

if current_page == "builder":
    render_builder_page()
elif current_page == "templates":
    render_templates_page()
elif current_page == "workflows":
    render_workflows_page()
elif current_page == "settings":
    render_settings_page()
else:
    render_builder_page()

# Footer
st.divider()
st.markdown(
    "<small>Workflow Builder v0.1.0 | Built with Streamlit, LangGraph, and Groq</small>",
    unsafe_allow_html=True
)

