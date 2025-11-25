"""File-based storage implementation for workflows."""

import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from config.settings import get_settings
from src.models.workflow import Workflow
from src.storage.storage_interface import StorageInterface
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FileStorage(StorageInterface):
    """JSON file-based storage for workflows."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize file storage.
        
        Args:
            storage_path: Optional custom storage path (defaults to settings)
        """
        settings = get_settings()
        self.storage_path = storage_path or settings.workflow_storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileStorage initialized at: {self.storage_path}")
    
    def _get_workflow_path(self, workflow_id: str) -> Path:
        """
        Get the file path for a workflow.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            Path to workflow file
        """
        return self.storage_path / f"{workflow_id}.json"
    
    def _get_metadata_path(self) -> Path:
        """
        Get the path to metadata index file.
        
        Returns:
            Path to metadata file
        """
        return self.storage_path / ".metadata.json"
    
    def _load_metadata(self) -> dict:
        """
        Load metadata index.
        
        Returns:
            Metadata dictionary
        """
        metadata_path = self._get_metadata_path()
        if not metadata_path.exists():
            return {}
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
            return {}
    
    def _save_metadata(self, metadata: dict) -> None:
        """
        Save metadata index.
        
        Args:
            metadata: Metadata dictionary
        """
        metadata_path = self._get_metadata_path()
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def save(self, workflow: Workflow) -> bool:
        """
        Save a workflow to disk.
        
        Args:
            workflow: The workflow to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Update timestamp
            workflow.updated_at = datetime.now()
            
            # Save workflow file
            workflow_path = self._get_workflow_path(workflow.id)
            workflow_dict = workflow.to_dict()
            
            with open(workflow_path, 'w', encoding='utf-8') as f:
                json.dump(workflow_dict, f, indent=2, default=str)
            
            # Update metadata
            metadata = self._load_metadata()
            metadata[workflow.id] = {
                "name": workflow.name,
                "description": workflow.description,
                "created_at": workflow.created_at.isoformat(),
                "updated_at": workflow.updated_at.isoformat(),
                "node_count": len(workflow.nodes)
            }
            self._save_metadata(metadata)
            
            logger.info(f"Workflow saved: {workflow.name} ({workflow.id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save workflow {workflow.id}: {e}", exc_info=True)
            return False
    
    def load(self, workflow_id: str) -> Optional[Workflow]:
        """
        Load a workflow from disk.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            Workflow instance or None if not found
        """
        workflow_path = self._get_workflow_path(workflow_id)
        
        if not workflow_path.exists():
            logger.warning(f"Workflow not found: {workflow_id}")
            return None
        
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow_dict = json.load(f)
            
            workflow = Workflow.from_dict(workflow_dict)
            logger.info(f"Workflow loaded: {workflow.name} ({workflow_id})")
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to load workflow {workflow_id}: {e}", exc_info=True)
            return None
    
    def list_all(self) -> List[str]:
        """
        List all workflow IDs.
        
        Returns:
            List of workflow IDs
        """
        metadata = self._load_metadata()
        return list(metadata.keys())
    
    def delete(self, workflow_id: str) -> bool:
        """
        Delete a workflow.
        
        Args:
            workflow_id: The workflow ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        workflow_path = self._get_workflow_path(workflow_id)
        
        if not workflow_path.exists():
            logger.warning(f"Workflow not found for deletion: {workflow_id}")
            return False
        
        try:
            # Delete workflow file
            workflow_path.unlink()
            
            # Update metadata
            metadata = self._load_metadata()
            if workflow_id in metadata:
                del metadata[workflow_id]
                self._save_metadata(metadata)
            
            logger.info(f"Workflow deleted: {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {e}", exc_info=True)
            return False
    
    def exists(self, workflow_id: str) -> bool:
        """
        Check if a workflow exists.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            True if exists, False otherwise
        """
        return self._get_workflow_path(workflow_id).exists()
    
    def get_metadata(self, workflow_id: str) -> Optional[dict]:
        """
        Get metadata for a workflow without loading the full workflow.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            Metadata dictionary or None if not found
        """
        metadata = self._load_metadata()
        return metadata.get(workflow_id)
    
    def list_with_metadata(self) -> List[dict]:
        """
        List all workflows with their metadata.
        
        Returns:
            List of metadata dictionaries
        """
        metadata = self._load_metadata()
        return [
            {"id": workflow_id, **meta}
            for workflow_id, meta in metadata.items()
        ]


# Singleton instance
_storage: Optional[FileStorage] = None


def get_storage() -> FileStorage:
    """
    Get the global storage instance (singleton pattern).
    
    Returns:
        FileStorage instance
    """
    global _storage
    if _storage is None:
        _storage = FileStorage()
    return _storage

