# shared/schemas.py
"""
Data schemas and validation for character recommender.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json


@dataclass
class Character:
    """Schema for a character."""
    id: str
    name: str
    media_id: str
    media_title: str
    media_type: str  # "TV", "Movie", etc.
    media_year: int
    genres: List[str] = field(default_factory=list)
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    trait_vector: List[float] = field(default_factory=list)  # 638 dims
    trait_scores: Dict[str, float] = field(default_factory=dict)
    tropes: List[str] = field(default_factory=list)
    description: str = ""
    sources: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "media_id": self.media_id,
            "media_title": self.media_title,
            "media_type": self.media_type,
            "media_year": self.media_year,
            "genres": self.genres,
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "trait_vector": self.trait_vector,
            "trait_scores": self.trait_scores,
            "tropes": self.tropes,
            "description": self.description,
            "sources": self.sources
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        return cls(**data)


@dataclass
class Actor:
    """Schema for an actor."""
    id: str
    name: str
    characters: List[str] = field(default_factory=list)  # character IDs
    vector: List[float] = field(default_factory=list)
    typecasting_score: float = 0.0
    top_traits: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "characters": self.characters,
            "vector": self.vector,
            "typecasting_score": self.typecasting_score,
            "top_traits": self.top_traits
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Actor":
        return cls(**data)


@dataclass
class Media:
    """Schema for a TV show or movie."""
    id: str
    title: str
    media_type: str  # "TV", "Movie"
    year_start: int
    year_end: Optional[int] = None
    genres: List[str] = field(default_factory=list)
    characters: List[str] = field(default_factory=list)  # character IDs
    vector: List[float] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "media_type": self.media_type,
            "year_start": self.year_start,
            "year_end": self.year_end,
            "genres": self.genres,
            "characters": self.characters,
            "vector": self.vector
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Media":
        return cls(**data)


def generate_character_id(media_title: str, character_name: str) -> str:
    """Generate a unique character ID."""
    media_slug = media_title.lower().replace(" ", "_").replace(":", "").replace("'", "")
    char_slug = character_name.lower().replace(" ", "_").replace(".", "").replace("'", "")
    return f"{media_slug}_{char_slug}"


def generate_actor_id(actor_name: str) -> str:
    """Generate a unique actor ID."""
    return actor_name.lower().replace(" ", "_").replace(".", "").replace("'", "")


def generate_media_id(media_title: str) -> str:
    """Generate a unique media ID."""
    return media_title.lower().replace(" ", "_").replace(":", "").replace("'", "")