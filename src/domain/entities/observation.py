"""
Observation Entity

Represents a structured observation with tags for analytics and service optimization.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from ..value_objects.observation_tag import ObservationTag


@dataclass
class Observation:
    """
    Observation entity for structured logging

    Business Rules from PRD (Section 7.1: Structured Logging):
        - Observations use normalized tags for analytics
        - Tags enable proper service categorization
        - All special needs must be captured as observations
        - Observations support business intelligence

    Attributes:
        observation_id: Unique observation identifier
        session_id: ID of the conversation session
        tags: List of observation tags (ObservationTag enums)
        notes: Free-text notes providing context
        patient_id: Optional patient ID if available
        service_id: Optional service ID if available
        metadata: Additional structured data (JSON-like)
        created_at: Observation creation timestamp
    """
    observation_id: str
    session_id: str
    tags: List[ObservationTag]
    notes: str
    patient_id: Optional[str] = None
    service_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate observation upon creation"""
        self._validate()

    def _validate(self):
        """
        Validate observation entity

        Business Rules:
            - Must have at least one tag
            - Notes must not be empty
            - Tags must be valid ObservationTag enums
        """
        if not self.tags or len(self.tags) == 0:
            raise ValueError("Observation must have at least one tag")

        if not self.notes or not self.notes.strip():
            raise ValueError("Observation notes cannot be empty")

        # Ensure all tags are valid ObservationTag instances
        for tag in self.tags:
            if not isinstance(tag, ObservationTag):
                raise ValueError(
                    f"Invalid tag type: {type(tag)}. Must be ObservationTag enum."
                )

    def has_tag(self, tag: ObservationTag) -> bool:
        """
        Check if observation has a specific tag

        Args:
            tag: Tag to check for

        Returns:
            bool: True if tag exists
        """
        return tag in self.tags

    def has_any_tag(self, tags: List[ObservationTag]) -> bool:
        """
        Check if observation has any of the specified tags

        Args:
            tags: List of tags to check

        Returns:
            bool: True if any tag exists
        """
        return any(tag in self.tags for tag in tags)

    def add_tag(self, tag: ObservationTag) -> None:
        """
        Add a tag to observation

        Args:
            tag: Tag to add

        Business Rule:
            - Prevents duplicate tags
        """
        if not isinstance(tag, ObservationTag):
            raise ValueError("Tag must be ObservationTag enum")

        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: ObservationTag) -> None:
        """
        Remove a tag from observation

        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)

    def get_tag_categories(self) -> List[str]:
        """
        Get unique categories of all tags

        Returns:
            List[str]: List of tag categories
        """
        return list(set(tag.category for tag in self.tags))

    def requires_action(self) -> bool:
        """
        Check if observation requires immediate action

        Business Rule:
            - Some tags indicate action required (ALTA_PRIORIDAD, etc.)
        """
        return any(tag.requires_action for tag in self.tags)

    def is_service_requirement(self) -> bool:
        """
        Check if observation represents a service requirement

        Returns:
            bool: True if any tag is a service requirement
        """
        return "SERVICE_REQUIREMENT" in self.get_tag_categories()

    def is_complaint(self) -> bool:
        """
        Check if observation represents a complaint

        Returns:
            bool: True if any tag is a complaint
        """
        return "COMPLAINT" in self.get_tag_categories()

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to observation

        Args:
            key: Metadata key
            value: Metadata value (must be JSON-serializable)

        Business Rule:
            - Metadata supports additional context
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    def to_dict(self) -> dict:
        """Convert entity to dictionary"""
        return {
            "observation_id": self.observation_id,
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "service_id": self.service_id,
            "tags": [str(tag) for tag in self.tags],
            "notes": self.notes,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def __str__(self) -> str:
        tag_list = ', '.join(str(tag) for tag in self.tags)
        return f"Observation({self.observation_id}, [{tag_list}])"

    def __repr__(self) -> str:
        return (
            f"Observation(observation_id='{self.observation_id}', "
            f"tags={self.tags}, "
            f"session_id='{self.session_id}')"
        )
