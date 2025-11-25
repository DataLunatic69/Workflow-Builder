"""Execution log viewer component."""

import streamlit as st
from typing import List


def render_execution_log(execution_log: List[str] = None):
    """
    Render execution log viewer.
    
    Args:
        execution_log: List of log entries
    """
    if execution_log is None:
        execution_log = st.session_state.get("execution_log", [])
    
    st.subheader("📋 Execution Log")
    
    if not execution_log:
        st.info("No execution log yet. Run a workflow to see logs here.")
        return
    
    # Display log entries
    log_container = st.container()
    with log_container:
        for entry in execution_log:
            # Format based on entry type
            if "❌" in entry or "ERROR" in entry.upper():
                st.error(entry)
            elif "⚠️" in entry or "WARNING" in entry.upper():
                st.warning(entry)
            elif "✅" in entry or "SUCCESS" in entry.upper():
                st.success(entry)
            elif "🚦" in entry or "ROUTING" in entry.upper():
                st.info(entry)
            else:
                st.text(entry)
    
    # Clear log button
    if st.button("🗑️ Clear Log"):
        st.session_state.execution_log = []
        st.rerun()

