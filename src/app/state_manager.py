from PySide6.QtCore import QSettings
import os
import shutil

from src.app.config import APP_ORGANIZATION, APP_NAME, AppConfig

class StateManager:
    """Application state manager using QSettings."""
    
    def __init__(self):
        self.settings = QSettings(APP_ORGANIZATION, APP_NAME)
    
    def save_window_state(self, window):
        """Save geometry and window state."""
        self.settings.setValue(f"{window.objectName()}_geometry", window.saveGeometry())
        self.settings.setValue(f"{window.objectName()}_state", window.saveState())
    
    def restore_window_state(self, window):
        """Restore geometry and window state."""
        geometry = self.settings.value(f"{window.objectName()}_geometry")
        if geometry:
            window.restoreGeometry(geometry)
            
        state = self.settings.value(f"{window.objectName()}_state")
        if state:
            window.restoreState(state)
    
    def get_last_data_dir(self) -> str:
        """Get the last used data directory."""
        return str(self.settings.value("last_data_dir", ""))
    
    def set_last_data_dir(self, path: str):
        """Save the last used data directory."""
        self.settings.setValue("last_data_dir", path)
    
    def get_recent_data_dirs(self) -> list:
        """Get list of recently used data directories."""
        recent = self.settings.value("recent_data_dirs", [])
        if isinstance(recent, str):
            # Sometimes QSettings returns a comma-separated string depending on format
            recent = [recent]
        return recent if isinstance(recent, list) else []
    
    def add_recent_data_dir(self, path: str):
        """Add to recent list (max 5)."""
        recent = self.get_recent_data_dirs()
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        recent = recent[:5]
        self.settings.setValue("recent_data_dirs", recent)

    def get_theme(self) -> str:
        """Get the saved application theme name."""
        return str(self.settings.value("app_theme", "slate"))

    def set_theme(self, theme_name: str):
        """Save the application theme name."""
        self.settings.setValue("app_theme", theme_name)

    def get_logo_path(self) -> str:
        """Get the custom company logo image path, preferring the workspace copy."""
        saved_path = str(self.settings.value("company_logo_path", ""))
        cfg = AppConfig()
        ws_logo = cfg.find_workspace_logo()
        if ws_logo and os.path.exists(ws_logo):
            if saved_path != ws_logo:
                self.settings.setValue("company_logo_path", ws_logo)
            return ws_logo

        if saved_path and os.path.exists(saved_path):
            # Migrate external logo into the workspace folder automatically if workspace is set
            if cfg.is_data_dir_set:
                try:
                    logo_dir = cfg.workspace_config_dir
                    os.makedirs(logo_dir, exist_ok=True)
                    ext = os.path.splitext(saved_path)[1].lower() or ".png"
                    target_path = os.path.join(logo_dir, f"company_logo{ext}")
                    if os.path.abspath(saved_path) != os.path.abspath(target_path):
                        shutil.copy2(saved_path, target_path)
                    self.settings.setValue("company_logo_path", target_path)
                    return target_path
                except Exception:
                    pass
            return saved_path

        return ""

    def set_logo_path(self, path: str):
        """Save the custom company logo image path."""
        self.settings.setValue("company_logo_path", path)

    def get_last_library_dir(self) -> str:
        """Get the last browsed directory when selecting or exporting files in Library."""
        saved_dir = str(self.settings.value("last_library_dir", ""))
        if saved_dir and os.path.isdir(saved_dir):
            return saved_dir
        return os.path.expanduser("~")

    def set_last_library_dir(self, path: str):
        """Save the last browsed directory for Library file dialogs."""
        if not path:
            return
        folder = path if os.path.isdir(path) else os.path.dirname(os.path.abspath(path))
        if folder and os.path.isdir(folder):
            self.settings.setValue("last_library_dir", folder)


