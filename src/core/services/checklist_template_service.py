import os
from typing import Dict, List, Any
from src.data.json_storage import JsonStorageEngine
from src.core.models.work_order import DEFAULT_CHECKLISTS

class ChecklistTemplateService:
    def __init__(self, storage: JsonStorageEngine):
        self.storage = storage
        self.file_path = "config/checklist_templates.json"
        self._ensure_default_templates()

    def _ensure_default_templates(self):
        # Create if not exists, or merge missing default system types
        templates = self.storage.load(self.file_path)
        if not templates or not isinstance(templates, dict):
            self.storage.save(self.file_path, DEFAULT_CHECKLISTS)
        else:
            changed = False
            for k, v in DEFAULT_CHECKLISTS.items():
                if k not in templates:
                    templates[k] = v
                    changed = True
            if changed:
                self.storage.save(self.file_path, templates)

    def get_all_templates(self) -> Dict[str, List[Dict]]:
        templates = self.storage.load(self.file_path)
        return templates or {}

    def get_template(self, name: str) -> List[Dict]:
        templates = self.get_all_templates()
        return templates.get(name, [])

    def save_template(self, name: str, tasks: List[Dict]) -> bool:
        templates = self.get_all_templates()
        templates[name] = tasks
        return self.storage.save(self.file_path, templates)

    def delete_template(self, name: str) -> bool:
        templates = self.get_all_templates()
        if name in templates:
            del templates[name]
            return self.storage.save(self.file_path, templates)
        return False
