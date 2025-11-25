"""Node editor component for editing node properties."""

import streamlit as st
from src.models.node import Node, RoutingRule, RoutingRules
from src.utils.helpers import generate_node_id


def render_node_editor(node: Node = None, workflow_nodes: list = None) -> Node:
    """
    Render node editor form.
    
    Args:
        node: Optional existing node to edit
        workflow_nodes: List of nodes in workflow for routing targets
        
    Returns:
        Node instance (or None if cancelled)
    """
    is_editing = node is not None
    form_key = f"node_editor_{node.id if node else 'new'}"
    rule_count_key = f"{form_key}_rule_count"
    
    # Initialize rule count
    if rule_count_key not in st.session_state:
        if node and node.routing_rules.conditional_targets:
            st.session_state[rule_count_key] = len(node.routing_rules.conditional_targets)
        else:
            st.session_state[rule_count_key] = 1
    
    # Add/remove rule buttons (outside form)
    col_add, col_remove = st.columns(2)
    with col_add:
        if st.button("➕ Add Rule", key=f"{form_key}_add_rule"):
            st.session_state[rule_count_key] += 1
            st.rerun()
    with col_remove:
        if st.button("➖ Remove Rule", key=f"{form_key}_remove_rule"):
            if st.session_state[rule_count_key] > 0:
                st.session_state[rule_count_key] -= 1
            st.rerun()
    
    with st.form(form_key):
        st.subheader("✏️ Edit Node" if is_editing else "➕ Add Node")
        
        # Node name
        node_name = st.text_input(
            "Node Name",
            value=node.name if node else "",
            placeholder="Enter node name",
            help="A descriptive name for this node"
        )
        
        # Node prompt
        node_prompt = st.text_area(
            "Node Prompt",
            value=node.prompt if node else "",
            placeholder="Enter the prompt/instruction for this node. Use {input_text} as a placeholder for input.",
            height=150,
            help="The instruction that will be sent to the LLM. Use {input_text} to include previous node output."
        )
        
        st.divider()
        st.subheader("🔀 Routing Rules")
        
        # Default target
        if workflow_nodes:
            node_options = ["END"] + [n.name for n in workflow_nodes if n.id != (node.id if node else None)]
            node_ids = ["END"] + [n.id for n in workflow_nodes if n.id != (node.id if node else None)]
            
            default_target_idx = 0
            if node and node.routing_rules.default_target:
                try:
                    default_target_idx = node_ids.index(node.routing_rules.default_target)
                except ValueError:
                    default_target_idx = 0
            
            default_target_name = st.selectbox(
                "Default Target",
                options=node_options,
                index=default_target_idx,
                help="Where to route when no conditional rule matches"
            )
            default_target_id = node_ids[node_options.index(default_target_name)]
        else:
            default_target_id = "END"
            st.info("Add more nodes to enable routing")
        
        # Conditional routing rules
        st.markdown("**Conditional Routing**")
        st.caption("Route to different nodes based on LLM output keys")
        
        conditional_rules = []
        if node and node.routing_rules.conditional_targets:
            conditional_rules = [
                {"output_key": rule.output_key, "target_node_id": rule.target_node_id}
                for rule in node.routing_rules.conditional_targets
            ]
        
        # Store rules in form state
        rule_inputs = []
        for i in range(st.session_state[rule_count_key]):
            col1, col2 = st.columns([2, 1])
            with col1:
                output_key = st.text_input(
                    f"Output Key {i+1}",
                    value=conditional_rules[i]["output_key"] if i < len(conditional_rules) else "",
                    placeholder="e.g., positive, negative, error",
                    key=f"{form_key}_output_key_{i}",
                    help="The routing key that the LLM should output"
                )
            with col2:
                if workflow_nodes:
                    target_options = ["END"] + [n.name for n in workflow_nodes if n.id != (node.id if node else None)]
                    target_ids = ["END"] + [n.id for n in workflow_nodes if n.id != (node.id if node else None)]
                    
                    target_idx = 0
                    if i < len(conditional_rules):
                        try:
                            target_idx = target_ids.index(conditional_rules[i]["target_node_id"])
                        except ValueError:
                            target_idx = 0
                    
                    target_name = st.selectbox(
                        "Target",
                        options=target_options,
                        index=target_idx,
                        key=f"{form_key}_target_{i}",
                        label_visibility="collapsed"
                    )
                    target_id = target_ids[target_options.index(target_name)]
                else:
                    target_id = "END"
                    st.selectbox("Target", ["END"], key=f"{form_key}_target_{i}", label_visibility="collapsed")
            
            rule_inputs.append({"output_key": output_key, "target_id": target_id})
        
        # Form buttons
        col_save, col_cancel = st.columns(2)
        with col_save:
            save_clicked = st.form_submit_button("💾 Save Node", type="primary")
        with col_cancel:
            cancel_clicked = st.form_submit_button("❌ Cancel")
        
        if save_clicked:
            if not node_name or not node_prompt:
                st.error("Node name and prompt are required!")
                return None
            
            # Collect conditional rules from form inputs
            conditional_targets = []
            for rule_input in rule_inputs:
                output_key = rule_input["output_key"]
                target_id = rule_input["target_id"]
                
                if output_key and output_key.strip():
                    conditional_targets.append(
                        RoutingRule(
                            output_key=output_key.strip(),
                            target_node_id=target_id
                        )
                    )
            
            # Create routing rules
            routing_rules = RoutingRules(
                default_target=default_target_id,
                conditional_targets=conditional_targets
            )
            
            # Create or update node
            if is_editing:
                node.name = node_name
                node.prompt = node_prompt
                node.routing_rules = routing_rules
                return node
            else:
                new_node = Node(
                    id=generate_node_id(),
                    name=node_name,
                    prompt=node_prompt,
                    routing_rules=routing_rules
                )
                return new_node
        
        if cancel_clicked:
            return None
    
    return None

