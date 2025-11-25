"""Configuration management for Workflow Builder."""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        """Initialize settings from environment variables."""
        # Groq Configuration
        self.groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")
        
        # LLM Configuration
        # Default to a current Groq model (llama-3.3-70b-versatile or llama-3.1-8b-instant)
        self.llm_model_name: str = os.getenv("LLM_MODEL_NAME", "qwen/qwen3-32b")
        self.llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        
        # Application Settings
        storage_path = os.getenv("WORKFLOW_STORAGE_PATH", "./workflows")
        self.workflow_storage_path: Path = Path(storage_path)
        self.workflow_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Logging Configuration
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        log_file = os.getenv("LOG_FILE", "./logs/workflow_builder.log")
        self.log_file: Path = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Optional: Other LLM Providers (for future use)
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
        self.google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
        
        # Routing Configuration
        self.routing_key_marker: str = "ROUTING_KEY:"
        self.default_routing_key: str = "__DEFAULT__"
        self.start_node_id: str = "__START__"
        self.end_node_id: str = "END"
        
        # Graph Configuration
        self.default_recursion_multiplier: int = 3
        self.default_recursion_base: int = 10

    @property
    def is_groq_configured(self) -> bool:
        """Check if Groq API key is configured."""
        return bool(self.groq_api_key)

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate that required settings are configured.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.is_groq_configured:
            return False, "GROQ_API_KEY is not set. Please configure it in your .env file."
        
        if self.llm_temperature < 0 or self.llm_temperature > 2:
            return False, "LLM_TEMPERATURE must be between 0 and 2."
        
        return True, None


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance (singleton pattern).
    
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

