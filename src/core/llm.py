"""LLM management for Workflow Builder."""

from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class LLMManager:
    """Manages LLM initialization and tool binding."""
    
    def __init__(self):
        """Initialize LLM manager."""
        self._llm: Optional[ChatOpenAI] = None
        self._llm_with_tools: Optional[Any] = None
        self._tools: List[Dict[str, Any]] = []
        self._initialized = False
        
    def initialize(self) -> bool:
        """
        Initialize the LLM with tools.
        
        Returns:
            True if initialization successful, False otherwise
        """
        settings = get_settings()
        
        if not settings.is_openai_configured:
            logger.error("OpenAI API key not configured")
            return False
        
        try:
            # Define tools (web search for now)
            self._tools = [{"type": "web_search_preview"}]
            
            # Initialize base LLM
            self._llm = ChatOpenAI(
                model_name=settings.llm_model_name,
                openai_api_key=settings.openai_api_key,
                temperature=settings.llm_temperature
            )
            
            # Bind tools
            self._llm_with_tools = self._llm.bind_tools(self._tools)
            
            self._initialized = True
            logger.info(
                f"LLM initialized successfully (model: {settings.llm_model_name}, "
                f"temperature: {settings.llm_temperature})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}", exc_info=True)
            self._llm = None
            self._llm_with_tools = None
            self._initialized = False
            return False
    
    def reinitialize_if_needed(self) -> bool:
        """
        Reinitialize LLM if settings have changed.
        
        Returns:
            True if reinitialization was successful or not needed
        """
        settings = get_settings()
        
        # Check if API key changed
        current_key = getattr(self._llm, 'openai_api_key', None) if self._llm else None
        if current_key != settings.openai_api_key:
            logger.info("API key changed, reinitializing LLM")
            return self.initialize()
        
        # Check if not initialized but should be
        if not self._initialized and settings.is_openai_configured:
            return self.initialize()
        
        # Check if initialized but shouldn't be
        if self._initialized and not settings.is_openai_configured:
            logger.info("API key removed, clearing LLM")
            self._llm = None
            self._llm_with_tools = None
            self._initialized = False
            return False
        
        return self._initialized
    
    @property
    def llm(self) -> Optional[ChatOpenAI]:
        """Get the base LLM instance."""
        if not self._initialized:
            self.reinitialize_if_needed()
        return self._llm
    
    @property
    def llm_with_tools(self) -> Optional[Any]:
        """Get the LLM instance with tools bound."""
        if not self._initialized:
            self.reinitialize_if_needed()
        return self._llm_with_tools
    
    @property
    def is_initialized(self) -> bool:
        """Check if LLM is initialized."""
        return self._initialized and self._llm is not None
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the list of tools bound to the LLM."""
        return self._tools.copy()
    
    def clear(self) -> None:
        """Clear the LLM instances."""
        self._llm = None
        self._llm_with_tools = None
        self._initialized = False
        logger.info("LLM instances cleared")


# Singleton instance
_llm_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """
    Get the global LLM manager instance (singleton pattern).
    
    Returns:
        LLMManager instance
    """
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager

