"""Node data models."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid


class RoutingRule(BaseModel):
    """A routing rule that maps an output key to a target node."""
    
    output_key: str = Field(..., description="The routing key that triggers this rule")
    target_node_id: str = Field(..., description="ID of the target node")
    
    @field_validator("output_key")
    @classmethod
    def validate_output_key(cls, v: str) -> str:
        """Validate that output_key is not empty."""
        if not v or not v.strip():
            raise ValueError("output_key cannot be empty")
        return v.strip()
    
    @field_validator("target_node_id")
    @classmethod
    def validate_target_node_id(cls, v: str) -> str:
        """Validate that target_node_id is not empty."""
        if not v or not v.strip():
            raise ValueError("target_node_id cannot be empty")
        return v.strip()


class RoutingRules(BaseModel):
    """Routing rules for a node."""
    
    default_target: str = Field(
        default="END",
        description="Default target node ID when no conditional rule matches"
    )
    conditional_targets: List[RoutingRule] = Field(
        default_factory=list,
        description="List of conditional routing rules"
    )
    
    def get_all_targets(self) -> List[str]:
        """Get all unique target node IDs."""
        targets = {self.default_target}
        targets.update(rule.target_node_id for rule in self.conditional_targets)
        return list(targets)
    
    def get_routing_map(self) -> Dict[str, str]:
        """
        Get a mapping of output keys to target node IDs.
        
        Returns:
            Dictionary mapping output_key -> target_node_id
        """
        routing_map: Dict[str, str] = {}
        for rule in self.conditional_targets:
            routing_map[rule.output_key] = rule.target_node_id
        return routing_map


class Node(BaseModel):
    """A workflow node."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique node ID")
    name: str = Field(..., min_length=1, description="Node name")
    prompt: str = Field(..., min_length=1, description="Prompt/instruction for this node")
    routing_rules: RoutingRules = Field(
        default_factory=RoutingRules,
        description="Routing rules for this node"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the node"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean node name."""
        if not v or not v.strip():
            raise ValueError("Node name cannot be empty")
        return v.strip()
    
    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate that prompt is not empty."""
        if not v or not v.strip():
            raise ValueError("Node prompt cannot be empty")
        return v.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary format (for compatibility with existing code)."""
        return {
            "id": self.id,
            "name": self.name,
            "prompt": self.prompt,
            "routing_rules": {
                "default_target": self.routing_rules.default_target,
                "conditional_targets": [
                    {
                        "output_key": rule.output_key,
                        "target_node_id": rule.target_node_id
                    }
                    for rule in self.routing_rules.conditional_targets
                ]
            },
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        """Create a Node from dictionary format."""
        routing_rules_data = data.get("routing_rules", {})
        routing_rules = RoutingRules(
            default_target=routing_rules_data.get("default_target", "END"),
            conditional_targets=[
                RoutingRule(**rule)
                for rule in routing_rules_data.get("conditional_targets", [])
            ]
        )
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            prompt=data["prompt"],
            routing_rules=routing_rules,
            metadata=data.get("metadata", {})
        )

