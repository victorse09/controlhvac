import os
import json
from pathlib import Path

APP_NAME = "ControlHVAC"
APP_VERSION = "1.0.0"
APP_ORGANIZATION = "HVAC Systems"

class AppConfig:
    """Manages application configuration and data paths."""
    
    def __init__(self):
        # Setup OS-specific config directory
        if os.name == 'nt':
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            self._config_dir = os.path.join(app_data, APP_NAME)
        else:
            self._config_dir = os.path.join(os.path.expanduser('~'), f'.{APP_NAME.lower()}')
            
        os.makedirs(self._config_dir, exist_ok=True)
        self._config_file = os.path.join(self._config_dir, "app_config.json")
        
        self._data_dir = ""
        self._load_config()
    
    @property
    def data_dir(self) -> str:
        return self._data_dir
    
    @data_dir.setter
    def data_dir(self, path: str):
        self._data_dir = path
        self._save_config()
        if path:
            self._ensure_dirs()
    
    @property
    def is_data_dir_set(self) -> bool:
        return bool(self._data_dir and os.path.isdir(self._data_dir))
    
    def get_data_path(self, *parts) -> str:
        if not self._data_dir:
            raise ValueError("Data directory not set.")
        path = os.path.join(self._data_dir, *parts)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path
        
    def _ensure_dirs(self):
        """Creates the default subdirectories inside the data directory."""
        dirs = [
            self.clients_dir,
            self.equipment_dir,
            self.work_orders_dir,
            self.maintenance_dir,
            self.inventory_dir,
            self.photos_dir,
            self.attachments_dir,
            self.backups_dir,
            self.workspace_config_dir
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
    
    def _load_config(self):
        if os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._data_dir = data.get('data_dir', "")
            except (json.JSONDecodeError, IOError):
                pass
    
    def _save_config(self):
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump({'data_dir': self._data_dir}, f, indent=4)
        except IOError:
            pass
    
    # Convenience paths:
    @property
    def clients_dir(self) -> str:
        return self.get_data_path('clients')
        
    @property  
    def equipment_dir(self) -> str:
        return self.get_data_path('equipment')
        
    @property
    def work_orders_dir(self) -> str:
        return self.get_data_path('work_orders')
        
    @property
    def maintenance_dir(self) -> str:
        return self.get_data_path('maintenance')
        
    @property
    def inventory_dir(self) -> str:
        return self.get_data_path('inventory')
        
    @property
    def photos_dir(self) -> str:
        return self.get_data_path('photos')
        
    @property
    def attachments_dir(self) -> str:
        return self.get_data_path('attachments')
        
    @property
    def backups_dir(self) -> str:
        return self.get_data_path('backups')

    @property
    def workspace_config_dir(self) -> str:
        return self.get_data_path('config')

    def find_workspace_logo(self) -> str:
        """Look for company_logo.* inside the workspace data directory (config/ or root)."""
        if not self.is_data_dir_set:
            return ""
        valid_exts = ('.png', '.jpg', '.jpeg', '.bmp', '.svg')
        search_dirs = [
            os.path.join(self._data_dir, 'config'),
            self._data_dir,
        ]
        for s_dir in search_dirs:
            if not os.path.isdir(s_dir):
                continue
            try:
                for fname in sorted(os.listdir(s_dir)):
                    lower = fname.lower()
                    if lower.startswith("company_logo") and lower.endswith(valid_exts):
                        full_p = os.path.join(s_dir, fname)
                        if os.path.isfile(full_p):
                            return full_p
            except OSError:
                pass
        return ""
