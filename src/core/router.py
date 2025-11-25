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
    
    def route(self, state: WorkflowState, path_map: Dict[str, any]) -> str:
        """
        Determine the routing key to use for conditional edges.
        
        Note: LangGraph's add_conditional_edges expects the routing function
        to return a KEY from the path_map, not the target value. LangGraph
        will then look up the target from the path_map.
        
        Args:
            state: Current workflow state
            path_map: Mapping of routing keys to target node IDs (may contain END constant)
            
        Returns:
            Routing key (string) that exists in path_map
        """
        last_content = state.get("last_response_content", "")
        
        if not last_content:
            logger.debug("No previous response content, using default routing")
            # Return the default routing key if it exists in path_map
            if self.settings.default_routing_key in path_map:
                logger.info(f"Routing decision: 'default' -> {self.settings.default_routing_key}")
                return self.settings.default_routing_key
            # Fallback to error if default not in map
            if "error" in path_map:
                logger.info("Routing decision: 'default' -> 'error' (fallback)")
                return "error"
            # Last resort: return default key (shouldn't happen if graph is valid)
            logger.warning("No valid routing key found, using default")
            return self.settings.default_routing_key
        
        # Extract routing key from content
        routing_key = self.extract_routing_key(last_content)
        
        # Check if routing key exists in path_map
        if routing_key in path_map:
            target = path_map[routing_key]
            target_str = str(target) if hasattr(target, '__name__') and target.__name__ == 'END' else str(target)
            logger.info(f"Routing decision: '{routing_key}' -> {target_str}")
            return routing_key
        
        # Routing key not found, use default
        logger.warning(
            f"Routing key '{routing_key}' not found in path_map, "
            f"using default"
        )
        if self.settings.default_routing_key in path_map:
            logger.info(f"Routing decision: '{routing_key}' -> '{self.settings.default_routing_key}' (fallback)")
            return self.settings.default_routing_key
        
        # Fallback to error
        if "error" in path_map:
            logger.info(f"Routing decision: '{routing_key}' -> 'error' (fallback)")
            return "error"
        
        # Last resort
        logger.error("No valid routing key found in path_map!")
        return self.settings.default_routing_key
    
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

