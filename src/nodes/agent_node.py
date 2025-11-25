"""AI Agent node implementation."""

import re
from typing import List
from src.models.state import WorkflowState
from src.models.node import Node
from src.nodes.base import BaseNode
from src.core.llm import get_llm_manager
from src.core.router import Router
from config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AgentNode(BaseNode):
    """AI-powered agent node that uses LLM for processing."""
    
    def __init__(self, node: Node, possible_keys: List[str]):
        """
        Initialize agent node.
        
        Args:
            node: The node model
            possible_keys: List of possible routing keys for this node
        """
        super().__init__(node)
        self.possible_keys = possible_keys
        self.settings = get_settings()
        self.router = Router()
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the agent node using LLM.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        logger.info(f"Executing node: {self.node.name} ({self.node.id})")
        
        # Check LLM initialization
        llm_manager = get_llm_manager()
        if not llm_manager.is_initialized:
            error_msg = "LLM not initialized"
            logger.error(error_msg)
            return self._create_error_state(state, error_msg)
        
        llm_with_tools = llm_manager.llm_with_tools
        if not llm_with_tools:
            error_msg = "LLM with tools not available"
            logger.error(error_msg)
            return self._create_error_state(state, error_msg)
        
        try:
            # Prepare context
            context_input = self.prepare_context(state)
            
            # Prepare prompt
            prompt_with_context = self._prepare_prompt(context_input)
            
            # Add routing instructions
            full_prompt = self._add_routing_instructions(prompt_with_context)
            
            logger.debug(f"Sending prompt to LLM (length: {len(full_prompt)})")
            
            # Invoke LLM
            result = llm_with_tools.invoke(full_prompt)
            
            # Extract content
            response_content = self._extract_content(result)
            
            # Ensure routing key is present
            response_content = self._ensure_routing_key(response_content)
            
            logger.debug(f"Node response length: {len(response_content)}")
            
            # Update state
            return self.update_state(state, response_content)
            
        except Exception as e:
            error_msg = f"Error in node {self.node.name}: {e}"
            logger.error(error_msg, exc_info=True)
            return self._create_error_state(state, error_msg)
    
    def _prepare_prompt(self, context_input: str) -> str:
        """
        Prepare the prompt with context.
        
        Args:
            context_input: Input context
            
        Returns:
            Prepared prompt
        """
        prompt = self.node.prompt
        
        # Replace {input_text} placeholder if present
        if "{input_text}" in prompt:
            return prompt.replace("{input_text}", context_input)
        
        # Otherwise append context
        if context_input:
            return f"{prompt}\n\nInput Context:\n{context_input}"
        
        return prompt
    
    def _add_routing_instructions(self, prompt: str) -> str:
        """
        Add routing instructions to the prompt.
        
        Args:
            prompt: Base prompt
            
        Returns:
            Prompt with routing instructions
        """
        current_task = f"Current Task ({self.node.name}):\n{prompt}\n(Search web if needed)."
        
        # Format possible keys
        key_options = [
            f"'{k}'" for k in self.possible_keys
            if k and k != self.settings.default_routing_key
        ]
        key_options_text = ", ".join(key_options) if key_options else "none"
        
        routing_instruction = (
            f"\n\n--- ROUTING ---\n"
            f"After your response, you MUST end with "
            f"'{self.settings.routing_key_marker} <key>' "
            f"(e.g., from [{key_options_text}]).\n"
            f"--- END ROUTING ---"
        )
        
        return current_task + routing_instruction
    
    def _extract_content(self, result: Any) -> str:
        """
        Extract text content from LLM result.
        
        Args:
            result: LLM result object
            
        Returns:
            Extracted content string
        """
        if not hasattr(result, 'content'):
            logger.warning("Result has no 'content' attribute")
            return ""
        
        raw_content = result.content
        
        # Handle string content
        if isinstance(raw_content, str):
            return raw_content
        
        # Handle list content (e.g., from gpt-4o)
        if isinstance(raw_content, list) and len(raw_content) > 0:
            first_item = raw_content[0]
            if isinstance(first_item, dict) and 'text' in first_item:
                return first_item.get('text', '')
        
        # Fallback: convert to string
        logger.warning(f"Unexpected content format: {type(raw_content)}")
        return str(raw_content)
    
    def _ensure_routing_key(self, content: str) -> str:
        """
        Ensure routing key is present in content.
        
        Args:
            content: Response content
            
        Returns:
            Content with routing key
        """
        if not isinstance(content, str):
            content = str(content)
        
        # Check if routing key already present
        pattern = rf"{re.escape(self.settings.routing_key_marker)}\s*\w+\s*$"
        if re.search(pattern, content):
            return content
        
        # Add default routing key
        logger.debug("No routing key found, appending default")
        return f"{content} {self.settings.routing_key_marker} {self.settings.default_routing_key}"
    
    def _create_error_state(
        self,
        state: WorkflowState,
        error_msg: str
    ) -> WorkflowState:
        """
        Create an error state.
        
        Args:
            state: Current state
            error_msg: Error message
            
        Returns:
            Error state
        """
        error_content = f"ERROR: {error_msg} {self.settings.routing_key_marker} error"
        return self.update_state(state, error_content)

