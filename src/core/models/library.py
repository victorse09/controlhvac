"""
Library Document Model for ControlHVAC CMMS.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .enums import LibraryCategory


@dataclass
class LibraryDocument:
    id: str
    title: str
    category: str = LibraryCategory.MANUAL.value
    file_name: str = ""
    file_path: str = ""  # Relative path within data directory, e.g., library/files/...
    original_path: str = ""  # Original source file path on disk when selected/uploaded
    file_size: int = 0   # in bytes
    mime_type: str = ""
    description: str = ""
    client_id: str = ""
    site_id: str = ""
    floor_area: str = ""  # e.g. "Piso 1", "Piso 2", "Subterráneo", "Sala de Máquinas"
    equipment_ids: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def formatted_size(self) -> str:
        """Return human-readable file size."""
        if not self.file_size or self.file_size <= 0:
            return "0 KB"
        size_kb = self.file_size / 1024
        if size_kb < 1024:
            return f"{size_kb:.1f} KB"
        size_mb = size_kb / 1024
        return f"{size_mb:.2f} MB"

    @property
    def file_extension(self) -> str:
        if self.file_name:
            _, ext = os.path.splitext(self.file_name)
            return ext.lower().replace(".", "")
        return ""

    @property
    def is_image(self) -> bool:
        ext = self.file_extension
        return ext in ("png", "jpg", "jpeg", "webp", "bmp", "gif")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "original_path": self.original_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "description": self.description,
            "client_id": self.client_id,
            "site_id": self.site_id,
            "floor_area": self.floor_area,
            "equipment_ids": self.equipment_ids,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> LibraryDocument:
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            category=data.get("category", LibraryCategory.MANUAL.value),
            file_name=data.get("file_name", ""),
            file_path=data.get("file_path", ""),
            original_path=data.get("original_path", "") or "",
            file_size=data.get("file_size", 0),
            mime_type=data.get("mime_type", ""),
            description=data.get("description", ""),
            client_id=data.get("client_id", "") or "",
            site_id=data.get("site_id", "") or "",
            floor_area=data.get("floor_area", "") or "",
            equipment_ids=data.get("equipment_ids", []) or [],
            tags=data.get("tags", []) or [],
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )

