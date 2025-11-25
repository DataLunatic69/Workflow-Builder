"""Storage interface abstraction for Workflow Builder."""

from abc import ABC, abstractmethod
from typing import List, Optional
from src.models.workflow import Workflow


class StorageInterface(ABC):
    """Abstract base class for workflow storage implementations."""
    
    @abstractmethod
    def save(self, workflow: Workflow) -> bool:
        """
        Save a workflow.
        
        Args:
            workflow: The workflow to save
            
        Returns:
            True if save successful, False otherwise
        """
        pass
    
    @abstractmethod
    def load(self, workflow_id: str) -> Optional[Workflow]:
        """
        Load a workflow by ID.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            Workflow instance or None if not found
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[str]:
        """
        List all workflow IDs.
        
        Returns:
            List of workflow IDs
        """
        pass
    
    @abstractmethod
    def delete(self, workflow_id: str) -> bool:
        """
        Delete a workflow.
        
        Args:
            workflow_id: The workflow ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def exists(self, workflow_id: str) -> bool:
        """
        Check if a workflow exists.
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            True if exists, False otherwise
        """
        pass

