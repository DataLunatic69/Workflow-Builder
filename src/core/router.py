"""Routing logic for workflow execution."""

import re
from typing import Dict
from config.settings import get_settings
from src.models.state import WorkflowState
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Router:
    """Handles routing decisions based on workflow state."""
    
    def __init__(self):
        """Initialize router."""
        self.settings = get_settings()
    
    def extract_routing_key(self, content: str) -> str:
        """
        Extract routing key from LLM response content.
        
        Args:
            content: The response content from LLM
            
        Returns:
            Extracted routing key, or default key if not found
        """
        if not isinstance(content, str):
            logger.warning(f"Content is not a string: {type(content)}")
            return self.settings.default_routing_key
        
        # Search for routing key marker at the end
        pattern = rf"{re.escape(self.settings.routing_key_marker)}\s*(\w+)\s*$"
        match = re.search(pattern, content)
        
        if match:
            key = match.group(1).strip()
            logger.debug(f"Extracted routing key: '{key}'")
            return key
        
        logger.debug("No routing key found, using default")
        return self.settings.default_routing_key
    
    def route(self, state: WorkflowState, path_map: Dict[str, str]) -> str:
        """
        Determine the next node based on workflow state.
        
        Args:
            state: Current workflow state
            path_map: Mapping of routing keys to target node IDs
            
        Returns:
            Target node ID
        """
        last_content = state.get("last_response_content", "")
        
        if not last_content:
            logger.debug("No previous response content, using default routing")
            return path_map.get(
                self.settings.default_routing_key,
                self.settings.end_node_id
            )
        
        # Extract routing key
        routing_key = self.extract_routing_key(last_content)
        
        # Get target from path map
        target = path_map.get(routing_key)
        
        if target is None:
            logger.warning(
                f"Routing key '{routing_key}' not found in path_map, "
                f"using default"
            )
            target = path_map.get(
                self.settings.default_routing_key,
                self.settings.end_node_id
            )
        
        logger.info(f"Routing decision: '{routing_key}' -> '{target}'")
        return target
    
    def clean_content(self, content: str) -> str:
        """
        Remove routing key marker from content.
        
        Args:
            content: Content with routing key marker
            
        Returns:
            Cleaned content without routing marker
        """
        if not isinstance(content, str):
            return str(content)
        
        pattern = rf"\s*{re.escape(self.settings.routing_key_marker)}\s*\w+\s*$"
        cleaned = re.sub(pattern, "", content).strip()
        return cleaned

