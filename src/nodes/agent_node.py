"""AI Agent node implementation."""

import re
from typing import List, Any
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
        super().__init__(node)
        self.possible_keys = possible_keys
        self.settings = get_settings()
        self.router = Router()
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute the agent node using LLM."""
        logger.info(f"Executing node: {self.node.name} ({self.node.id})")
        
        llm_manager = get_llm_manager()
        if not llm_manager.is_initialized:
            error_msg = "LLM not initialized"
            return self._create_error_state(state, error_msg)
        
        llm_with_tools = llm_manager.llm_with_tools
        
        try:
            # Prepare context and prompt
            context_input = self.prepare_context(state)
            prompt_with_context = self._prepare_prompt(context_input)
            full_prompt = self._add_routing_instructions(prompt_with_context)
            
            logger.debug(f"Sending prompt to LLM (length: {len(full_prompt)})")
            
            # Invoke LLM
            logger.info(f"⚙️ Invoking LLM for node '{self.node.name}'...")
            result = llm_with_tools.invoke(full_prompt)
            logger.info(f"✅ LLM invocation successful")
            
            # Extract content
            response_content = self._extract_content(result)
            
            if not response_content or len(response_content.strip()) == 0:
                raise ValueError("LLM returned empty response")
            
            # Ensure routing key is present
            response_content = self._ensure_routing_key(response_content)
            
            return self.update_state(state, response_content)
            
        except Exception as e:
            error_msg = f"Error in node {self.node.name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return self._create_error_state(state, str(e))
    
    def _prepare_prompt(self, context_input: str) -> str:
        prompt = self.node.prompt
        if "{input_text}" in prompt:
            return prompt.replace("{input_text}", context_input)
        if context_input:
            return f"{prompt}\n\nInput Context:\n{context_input}"
        return prompt
    
    def _add_routing_instructions(self, prompt: str) -> str:
        current_task = f"Current Task ({self.node.name}):\n{prompt}\n"
        
        # Filter out default key and empty keys
        key_options = [
            f"'{k}'" for k in self.possible_keys
            if k and k != self.settings.default_routing_key
        ]
        key_options_text = ", ".join(key_options) if key_options else "none"
        
        routing_instruction = (
            f"\n\n--- ROUTING INSTRUCTIONS ---\n"
            f"1. Perform the task above.\n"
            f"2. At the VERY END of your response, append exactly: '{self.settings.routing_key_marker} <key>'\n"
        )
        
        if key_options_text != "none":
            routing_instruction += (
                f"3. <key> must be ONE of: [{key_options_text}].\n"
                f"4. If none apply, use: '{self.settings.routing_key_marker} {self.settings.default_routing_key}'\n"
            )
        else:
            routing_instruction += (
                f"3. Use the key: '{self.settings.default_routing_key}'\n"
            )
            
        routing_instruction += "--- END ROUTING ---"
        return current_task + routing_instruction
    
    def _extract_content(self, result: Any) -> str:
        """Extract text content and clean <think> tags."""
        content = ""
        
        try:
            if hasattr(result, 'content'):
                raw_content = result.content
                if isinstance(raw_content, str):
                    content = raw_content
                elif isinstance(raw_content, list):
                    if len(raw_content) > 0:
                        first = raw_content[0]
                        if isinstance(first, dict):
                            content = first.get('text', '')
                        elif isinstance(first, str):
                            content = first
                else:
                    content = str(raw_content)
            
            # FIX: Strip <think> tags from Qwen/DeepSeek reasoning models
            # This uses regex to remove <think>... content ...</think> including newlines
            if content:
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                
            return content
            
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return ""
    
    def _ensure_routing_key(self, content: str) -> str:
        if not isinstance(content, str):
            content = str(content)
        
        pattern = rf"{re.escape(self.settings.routing_key_marker)}\s*(\w+)\s*$"
        match = re.search(pattern, content)
        
        if match:
            extracted_key = match.group(1).strip()
            if extracted_key in self.possible_keys:
                return content
            else:
                # Invalid key found, replace it
                content = re.sub(pattern, "", content).strip()
        
        return f"{content}\n\n{self.settings.routing_key_marker} {self.settings.default_routing_key}"
    
    def _create_error_state(self, state: WorkflowState, error_msg: str) -> WorkflowState:
        # Standardize error format for the Executor to catch
        error_content = f"ERROR: {error_msg}\n\n{self.settings.routing_key_marker} error"
        return self.update_state(state, error_content)