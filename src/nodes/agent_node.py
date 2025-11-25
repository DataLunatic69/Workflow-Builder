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
            logger.debug(f"Prompt preview: {full_prompt[:200]}...")
            
            # Invoke LLM
            try:
                logger.info(f"⚙️ Invoking LLM for node '{self.node.name}'...")
                result = llm_with_tools.invoke(full_prompt)
                logger.info(f"✅ LLM invocation successful, result type: {type(result)}")
                logger.debug(f"Result attributes: {dir(result)}")
            except Exception as invoke_error:
                error_str = str(invoke_error)
                logger.error(f"❌ LLM invocation failed: {error_str}", exc_info=True)
                logger.info(f"❌ LLM ERROR DETAILS: {type(invoke_error).__name__}: {error_str}")
                raise  # Re-raise to be caught by outer exception handler
            
            # Extract content
            logger.info(f"📝 Extracting content from LLM response...")
            response_content = self._extract_content(result)
            logger.info(f"📝 Extracted content length: {len(response_content) if response_content else 0}")
            
            if not response_content or len(response_content.strip()) == 0:
                logger.error("❌ LLM returned empty content")
                logger.info("❌ EMPTY RESPONSE ERROR: LLM returned empty response")
                raise ValueError("LLM returned empty response")
            
            # Ensure routing key is present
            response_content = self._ensure_routing_key(response_content)
            
            logger.debug(f"Node response length: {len(response_content)}")
            
            # Update state
            return self.update_state(state, response_content)
            
        except Exception as e:
            error_msg = f"Error in node {self.node.name}: {str(e)}"
            error_details = f"{type(e).__name__}: {str(e)}"
            # Log with full traceback for debugging
            logger.error(f"{error_msg} - {error_details}", exc_info=True)
            # Also log at INFO level so it shows in console
            logger.info(f"❌ NODE ERROR: {self.node.name} - {error_details}")
            # Include more details in the error state for debugging
            detailed_error = f"{error_msg}\nDetails: {error_details}"
            return self._create_error_state(state, detailed_error)
    
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
        
        # Build routing instruction with clear examples
        if key_options_text == "none":
            # Only default routing available
            routing_instruction = (
                f"\n\n--- ROUTING INSTRUCTIONS ---\n"
                f"After your response, you MUST end with exactly: "
                f"'{self.settings.routing_key_marker} {self.settings.default_routing_key}'\n"
                f"This is the only valid routing key for this node.\n"
                f"--- END ROUTING ---"
            )
        else:
            # Multiple routing options available
            routing_instruction = (
                f"\n\n--- ROUTING INSTRUCTIONS ---\n"
                f"After your response, you MUST end with '{self.settings.routing_key_marker} <key>' "
                f"where <key> is ONE of these exact values: [{key_options_text}].\n"
                f"If none of these keys apply, use: '{self.settings.routing_key_marker} {self.settings.default_routing_key}'\n"
                f"IMPORTANT: Use ONLY the keys listed above. Do not create new keys.\n"
                f"Example: '...your response here... {self.settings.routing_key_marker} {key_options[0] if key_options else self.settings.default_routing_key}'\n"
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
        try:
            if not hasattr(result, 'content'):
                logger.error(f"❌ Result has no 'content' attribute. Result type: {type(result)}, dir: {[x for x in dir(result) if not x.startswith('_')]}")
                return ""
            
            raw_content = result.content
            logger.debug(f"Raw content type: {type(raw_content)}")
            
            # Handle string content
            if isinstance(raw_content, str):
                logger.debug(f"Content is string, length: {len(raw_content)}")
                return raw_content
            
            # Handle list content (e.g., from some LLM formats)
            if isinstance(raw_content, list):
                logger.debug(f"Content is list, length: {len(raw_content)}")
                if len(raw_content) > 0:
                    first_item = raw_content[0]
                    logger.debug(f"First item type: {type(first_item)}")
                    if isinstance(first_item, dict):
                        if 'text' in first_item:
                            text = first_item.get('text', '')
                            logger.debug(f"Extracted text from dict, length: {len(text)}")
                            return text
                        else:
                            logger.warning(f"Dict has no 'text' key. Keys: {first_item.keys()}")
                    elif isinstance(first_item, str):
                        logger.debug(f"First item is string, length: {len(first_item)}")
                        return first_item
                logger.warning("List is empty")
                return ""
            
            # Fallback: convert to string
            logger.warning(f"⚠️ Unexpected content format: {type(raw_content)}. Converting to string.")
            content_str = str(raw_content)
            logger.debug(f"Converted content length: {len(content_str)}")
            return content_str
            
        except Exception as extract_error:
            logger.error(f"❌ Error extracting content: {extract_error}", exc_info=True)
            logger.info(f"❌ EXTRACTION ERROR: {type(extract_error).__name__}: {str(extract_error)}")
            raise
    
    def _ensure_routing_key(self, content: str) -> str:
        """
        Ensure routing key is present in content and validate it.
        
        Args:
            content: Response content
            
        Returns:
            Content with valid routing key
        """
        if not isinstance(content, str):
            content = str(content)
        
        # Check if routing key already present
        pattern = rf"{re.escape(self.settings.routing_key_marker)}\s*(\w+)\s*$"
        match = re.search(pattern, content)
        
        if match:
            extracted_key = match.group(1).strip()
            # Validate that the extracted key is in the possible keys
            if extracted_key in self.possible_keys:
                logger.debug(f"Valid routing key found: '{extracted_key}'")
                return content
            else:
                # Invalid routing key - replace with default
                logger.warning(
                    f"Invalid routing key '{extracted_key}' not in possible keys "
                    f"{self.possible_keys}. Using default."
                )
                # Remove the invalid key and add default
                content_without_key = re.sub(pattern, "", content).strip()
                return f"{content_without_key} {self.settings.routing_key_marker} {self.settings.default_routing_key}"
        
        # Add default routing key if none found
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

