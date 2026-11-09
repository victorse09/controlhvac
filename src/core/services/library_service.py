"""
Technical Library Service for ControlHVAC CMMS.
Manages documentation, manuals, datasheets, MSDS, diagrams and their association with equipment.
"""
from __future__ import annotations

import mimetypes
import os
import shutil
import subprocess
import sys
from typing import Dict, List, Optional

from src.core.models.enums import LibraryCategory
from src.core.models.library import LibraryDocument
from src.data.json_storage import JsonStorageEngine


class LibraryService:
    """Service for managing digital library documentation and equipment links."""

    def __init__(self, storage: JsonStorageEngine, recycle_bin_service=None):
        self.storage = storage
        self.recycle_bin_service = recycle_bin_service

    @property
    def files_dir(self) -> str:
        """Full path to library files storage directory."""
        path = os.path.join(self.storage.base_path, "library", "files")
        os.makedirs(path, exist_ok=True)
        return path

    def save_document(
        self,
        doc: LibraryDocument,
        source_file_path: Optional[str] = None
    ) -> LibraryDocument:
        """Save or update a library document, copying physical file if source_file_path is provided."""
        if source_file_path and os.path.isfile(source_file_path):
            abs_src = os.path.abspath(source_file_path)
            base_name = os.path.basename(abs_src)
            # Create a clean safe unique filename
            clean_name = f"{doc.id}_{base_name}"
            target_file_path = os.path.abspath(os.path.join(self.files_dir, clean_name))
            if abs_src != target_file_path:
                shutil.copy2(abs_src, target_file_path)

            doc.file_name = base_name
            doc.file_path = os.path.join("library", "files", clean_name)
            doc.original_path = abs_src
            doc.file_size = os.path.getsize(target_file_path)

            mime_type, _ = mimetypes.guess_type(base_name)
            doc.mime_type = mime_type or "application/octet-stream"
        elif not doc.file_path and doc.file_name:
            # Ensure file_path is preserved if file already exists in library/files
            clean_name = f"{doc.id}_{doc.file_name}"
            candidate = os.path.join(self.files_dir, clean_name)
            if os.path.isfile(candidate):
                doc.file_path = os.path.join("library", "files", clean_name)

        return self.save_document_metadata(doc)

    def save_document_metadata(self, doc: LibraryDocument) -> LibraryDocument:
        """Save document metadata without copying files."""
        self.storage.save_document("library", doc.id, "document.json", doc.to_dict())
        self.storage.update_index("library", doc.id, {
            "title": doc.title,
            "category": doc.category,
            "file_name": doc.file_name,
            "file_path": doc.file_path,
            "original_path": getattr(doc, "original_path", "") or "",
            "file_size": doc.file_size,
            "client_id": doc.client_id,
            "site_id": doc.site_id,
            "floor_area": doc.floor_area,
            "equipment_ids": doc.equipment_ids,
            "updated_at": doc.updated_at,
        })
        return doc

    def get_document(self, doc_id: str) -> Optional[LibraryDocument]:
        """Get document by ID."""
        data = self.storage.load_document("library", doc_id, "document.json")
        if not data:
            return None
        doc = LibraryDocument.from_dict(data)
        if not doc.file_path and doc.file_name:
            clean_name = f"{doc.id}_{doc.file_name}"
            if os.path.isfile(os.path.join(self.files_dir, clean_name)):
                doc.file_path = os.path.join("library", "files", clean_name)
        return doc

    def get_all_documents(self) -> List[LibraryDocument]:
        """Get all library documents sorted by newest updated first."""
        docs = []
        index = self.storage.get_index("library")
        for doc_id in index:
            doc = self.get_document(doc_id)
            if doc:
                docs.append(doc)
        docs.sort(key=lambda d: d.created_at, reverse=True)
        return docs

    def get_documents_by_category(self, category: str) -> List[LibraryDocument]:
        """Get documents filtered by category."""
        return [d for d in self.get_all_documents() if d.category == category]

    def get_documents_for_equipment(self, equipment_id: str) -> List[LibraryDocument]:
        """Get all documents linked to a specific equipment ID."""
        return [
            d for d in self.get_all_documents()
            if equipment_id in d.equipment_ids
        ]

    def link_document_to_equipment(self, doc_id: str, equipment_id: str) -> bool:
        """Associate a document with an equipment."""
        doc = self.get_document(doc_id)
        if not doc:
            return False
        if equipment_id not in doc.equipment_ids:
            doc.equipment_ids.append(equipment_id)
            self.save_document_metadata(doc)
        return True

    def unlink_document_from_equipment(self, doc_id: str, equipment_id: str) -> bool:
        """Remove association between a document and an equipment."""
        doc = self.get_document(doc_id)
        if not doc:
            return False
        if equipment_id in doc.equipment_ids:
            doc.equipment_ids.remove(equipment_id)
            self.save_document_metadata(doc)
        return True

    def delete_document(self, doc_id: str) -> bool:
        """Delete document, recycle metadata and remove file."""
        doc = self.get_document(doc_id)
        if not doc:
            return False

        if self.recycle_bin_service:
            self.recycle_bin_service.recycle_item(
                doc.id, "LIBRARY_DOCUMENT", doc.title, doc.to_dict()
            )

        # Delete document directory (keep physical file in library/files if recycled so restore works)
        doc_dir = os.path.join(self.storage.base_path, "library", doc_id)
        try:
            if os.path.exists(doc_dir):
                shutil.rmtree(doc_dir)
        except Exception:
            pass

        # Only remove physical file if recycle_bin_service is not active
        if not self.recycle_bin_service and doc.file_path:
            full_file_path = self.get_absolute_file_path(doc)
            if full_file_path and os.path.exists(full_file_path):
                try:
                    os.remove(full_file_path)
                except Exception:
                    pass

        self.storage.remove_from_index("library", doc_id)
        return True

    def get_absolute_file_path(self, doc: LibraryDocument) -> str:
        """Get full absolute path on disk for document file."""
        candidates = []
        if doc.file_path:
            if os.path.isabs(doc.file_path):
                candidates.append(doc.file_path)
            else:
                candidates.append(os.path.abspath(os.path.join(self.storage.base_path, doc.file_path)))
        if doc.file_name:
            candidates.append(os.path.abspath(os.path.join(self.files_dir, f"{doc.id}_{doc.file_name}")))
            candidates.append(os.path.abspath(os.path.join(self.files_dir, doc.file_name)))
        if getattr(doc, "original_path", ""):
            candidates.append(doc.original_path)

        for cand in candidates:
            if cand and os.path.isfile(cand):
                return cand

        # If file doesn't exist yet on disk, return primary expected library path
        if candidates:
            return candidates[0]
        return ""

    def open_document(self, doc_id: str) -> bool:
        """Open the document using the system default application (PDF reader, image viewer, etc.)."""
        doc = self.get_document(doc_id)
        if not doc:
            return False

        file_path = self.get_absolute_file_path(doc)
        if not file_path or not os.path.exists(file_path):
            return False

        try:
            if sys.platform.startswith('win'):
                os.startfile(file_path)
            elif sys.platform.startswith('darwin'):
                subprocess.Popen(['open', file_path])
            else:
                subprocess.Popen(['xdg-open', file_path])
            return True
        except Exception as e:
            print(f"Error opening document {file_path}: {e}")
            return False

    def search_documents(
        self,
        query: str = "",
        category: Optional[str] = None,
        equipment_id: Optional[str] = None
    ) -> List[LibraryDocument]:
        """Search and filter library documents."""
        docs = self.get_all_documents()
        query = query.strip().lower()

        if query:
            docs = [
                d for d in docs
                if (
                    query in d.title.lower() or
                    query in d.file_name.lower() or
                    query in (d.description or "").lower() or
                    any(query in tag.lower() for tag in d.tags)
                )
            ]

        if category:
            docs = [d for d in docs if d.category == category]

        if equipment_id:
            docs = [d for d in docs if equipment_id in d.equipment_ids]

        return docs

    def get_floor_plans(self, site_id: str = "", floor_area: str = "") -> List[LibraryDocument]:
        """Get floor plan documents, optionally filtered by site and floor name."""
        all_docs = self.get_all_documents()
        plans = [d for d in all_docs if d.category == LibraryCategory.FLOOR_PLAN.value]

        if site_id:
            plans = [d for d in plans if not d.site_id or d.site_id == site_id]

        if floor_area:
            clean_fl = floor_area.strip().lower()
            plans = [d for d in plans if d.floor_area and (d.floor_area.strip().lower() == clean_fl or clean_fl in d.floor_area.strip().lower() or d.floor_area.strip().lower() in clean_fl)]

        return plans

    def get_floor_plan_image_path(self, floor_area: str, site_id: str = "") -> Optional[str]:
        """Find the image file path for a floor plan associated with the given floor/area."""
        if not floor_area or floor_area.startswith("Sin Piso"):
            return None

        plans = self.get_floor_plans(site_id=site_id, floor_area=floor_area)
        for p in plans:
            if p.is_image:
                abs_path = self.get_absolute_file_path(p)
                if abs_path and os.path.exists(abs_path):
                    return abs_path

        # If no strict match by category, also check DIAGRAM/IMAGE with floor_area matching
        all_docs = self.get_all_documents()
        clean_fl = floor_area.strip().lower()
        for d in all_docs:
            if d.is_image and d.floor_area and (d.floor_area.strip().lower() == clean_fl or clean_fl in d.floor_area.strip().lower()):
                if not site_id or not d.site_id or d.site_id == site_id:
                    abs_path = self.get_absolute_file_path(d)
                    if abs_path and os.path.exists(abs_path):
                        return abs_path

        return None

    def get_stats(self) -> Dict[str, int]:
        """Get category counts and total document metrics."""
        docs = self.get_all_documents()
        stats = {
            "total": len(docs),
            "floor_plans": sum(1 for d in docs if d.category == LibraryCategory.FLOOR_PLAN.value),
            "manuals": sum(1 for d in docs if d.category == LibraryCategory.MANUAL.value),
            "datasheets": sum(1 for d in docs if d.category == LibraryCategory.DATASHEET.value),
            "safety_sheets": sum(1 for d in docs if d.category == LibraryCategory.SAFETY_SHEET.value),
            "diagrams": sum(1 for d in docs if d.category == LibraryCategory.DIAGRAM.value),
            "images": sum(1 for d in docs if d.category == LibraryCategory.IMAGE.value),
            "others": sum(1 for d in docs if d.category not in [
                LibraryCategory.FLOOR_PLAN.value,
                LibraryCategory.MANUAL.value,
                LibraryCategory.DATASHEET.value,
                LibraryCategory.SAFETY_SHEET.value,
                LibraryCategory.DIAGRAM.value,
                LibraryCategory.IMAGE.value
            ]),
        }
        return stats
