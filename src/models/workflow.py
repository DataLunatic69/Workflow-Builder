"""Workflow data model."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import uuid

from .node import Node


class Workflow(BaseModel):
    """A workflow containing multiple nodes."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique workflow ID")
    name: str = Field(..., min_length=1, description="Workflow name")
    description: Optional[str] = Field(default=None, description="Workflow description")
    nodes: List[Node] = Field(default_factory=list, description="List of nodes in the workflow")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the workflow"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean workflow name."""
        if not v or not v.strip():
            raise ValueError("Workflow name cannot be empty")
        return v.strip()
    
    def add_node(self, node: Node) -> None:
        """Add a node to the workflow."""
        self.nodes.append(node)
        self.updated_at = datetime.now()
    
    def remove_node(self, node_id: str) -> bool:
        """
        Remove a node from the workflow.
        
        Args:
            node_id: ID of the node to remove
            
        Returns:
            True if node was removed, False if not found
        """
        initial_count = len(self.nodes)
        self.nodes = [node for node in self.nodes if node.id != node_id]
        if len(self.nodes) < initial_count:
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_node_ids(self) -> List[str]:
        """Get all node IDs in the workflow."""
        return [node.id for node in self.nodes]
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the workflow structure.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.nodes:
            return False, "Workflow must contain at least one node"
        
        # Check for duplicate node IDs
        node_ids = self.get_node_ids()
        if len(node_ids) != len(set(node_ids)):
            return False, "Workflow contains duplicate node IDs"
        
        # Validate routing targets
        all_node_ids = set(node_ids)
        all_node_ids.add("END")  # END is a valid target
        
        for node in self.nodes:
            # Check default target
            default_target = node.routing_rules.default_target
            if default_target != "END" and default_target not in all_node_ids:
                return False, f"Node '{node.name}' has invalid default target: {default_target}"
            
            # Check conditional targets
            for rule in node.routing_rules.conditional_targets:
                if rule.target_node_id != "END" and rule.target_node_id not in all_node_ids:
                    return False, (
                        f"Node '{node.name}' has invalid conditional target "
                        f"'{rule.output_key}' -> '{rule.target_node_id}'"
                    )
        
        return True, None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary format."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": [node.to_dict() for node in self.nodes],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Create a Workflow from dictionary format."""
        created_at = datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now())
        updated_at = datetime.fromisoformat(data["updated_at"]) if isinstance(data.get("updated_at"), str) else data.get("updated_at", datetime.now())
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            description=data.get("description"),
            nodes=[Node.from_dict(node_data) for node_data in data.get("nodes", [])],
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {})
        )

