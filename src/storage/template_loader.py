"""Template loading utilities for workflows."""

import json
from pathlib import Path
from typing import List, Dict, Optional
from src.models.workflow import Workflow
from src.utils.logger import get_logger
from typing import Any

logger = get_logger(__name__)


class TemplateLoader:
    """Loads workflow templates from the templates directory."""
    
    def __init__(self, templates_path: Optional[Path] = None):
        """
        Initialize template loader.
        
        Args:
            templates_path: Optional custom templates path
        """
        if templates_path is None:
            # Default to templates/example_workflows relative to project root
            project_root = Path(__file__).parent.parent.parent
            templates_path = project_root / "templates" / "example_workflows"
        
        self.templates_path = Path(templates_path)
        logger.info(f"TemplateLoader initialized at: {self.templates_path}")
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all available templates.
        
        Returns:
            List of template metadata dictionaries
        """
        templates = []
        
        if not self.templates_path.exists():
            logger.warning(f"Templates directory does not exist: {self.templates_path}")
            return templates
        
        for template_file in self.templates_path.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                templates.append({
                    "id": template_data.get("id", template_file.stem),
                    "name": template_data.get("name", template_file.stem),
                    "description": template_data.get("description", ""),
                    "file": str(template_file),
                    "metadata": template_data.get("metadata", {})
                })
            except Exception as e:
                logger.warning(f"Failed to load template {template_file}: {e}")
        
        return templates
    
    def load_template(self, template_id: str) -> Optional[Workflow]:
        """
        Load a template workflow by ID.
        
        Args:
            template_id: The template ID
            
        Returns:
            Workflow instance or None if not found
        """
        template_file = self.templates_path / f"{template_id}.json"
        
        if not template_file.exists():
            # Try to find by ID in template data
            templates = self.list_templates()
            for template in templates:
                if template["id"] == template_id:
                    template_file = Path(template["file"])
                    break
            else:
                logger.warning(f"Template not found: {template_id}")
                return None
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            workflow = Workflow.from_dict(template_data)
            logger.info(f"Template loaded: {workflow.name} ({template_id})")
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to load template {template_id}: {e}", exc_info=True)
            return None
    
    def load_template_by_name(self, template_name: str) -> Optional[Workflow]:
        """
        Load a template workflow by name.
        
        Args:
            template_name: The template name
            
        Returns:
            Workflow instance or None if not found
        """
        templates = self.list_templates()
        for template in templates:
            if template["name"].lower() == template_name.lower():
                return self.load_template(template["id"])
        
        logger.warning(f"Template not found by name: {template_name}")
        return None


# Singleton instance
_template_loader: Optional[TemplateLoader] = None


def get_template_loader() -> TemplateLoader:
    """
    Get the global template loader instance.
    
    Returns:
        TemplateLoader instance
    """
    global _template_loader
    if _template_loader is None:
        _template_loader = TemplateLoader()
    return _template_loader

