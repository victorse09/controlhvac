import os
from PySide6.QtGui import QIcon, QPixmap, QImage, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt

class IconManager:
    """SVG icon manager with caching and dynamic tinting."""
    _cache: dict = {}
    _base_path: str = ""
    
    @classmethod
    def init(cls, base_path: str):
        cls._base_path = base_path
    
    @classmethod
    def get_icon(cls, relative_path: str, color: str = '#94A3B8', size: int = 24) -> QIcon:
        cache_key = f"{relative_path}_{color}_{size}"
        if cache_key in cls._cache:
            return QIcon(cls._cache[cache_key])
            
        pixmap = cls.get_pixmap(relative_path, color, size)
        icon = QIcon(pixmap)
        cls._cache[cache_key] = pixmap
        return icon
    
    @classmethod
    def _resolve_path(cls, relative_path: str) -> str:
        """Resolve a relative icon path with fallbacks across subdirectories."""
        candidates = [
            os.path.join(cls._base_path, relative_path),
            os.path.join(cls._base_path, f"{relative_path}.svg"),
            os.path.join(cls._base_path, "nav", relative_path),
            os.path.join(cls._base_path, "nav", f"{relative_path}.svg"),
            os.path.join(cls._base_path, "nav", f"{relative_path}s.svg"),
            os.path.join(cls._base_path, "actions", relative_path),
            os.path.join(cls._base_path, "actions", f"{relative_path}.svg"),
            os.path.join(cls._base_path, "actions", f"{relative_path}s.svg"),
            os.path.join(cls._base_path, "equipment", relative_path),
            os.path.join(cls._base_path, "equipment", f"{relative_path}.svg"),
            os.path.join(cls._base_path, "status", relative_path),
            os.path.join(cls._base_path, "status", f"{relative_path}.svg"),
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate
        return ""

    @classmethod
    def get_pixmap(cls, relative_path: str, color: str = '#94A3B8', size: int = 24) -> QPixmap:
        cache_key = f"pix_{relative_path}_{color}_{size}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]
            
        path = cls._resolve_path(relative_path)
        if not path or not os.path.isfile(path):
            # Return empty pixmap if file not found
            pix = QPixmap(size, size)
            pix.fill(Qt.GlobalColor.transparent)
            return pix
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                svg_data = f.read()
        except Exception:
            pix = QPixmap(size, size)
            pix.fill(Qt.GlobalColor.transparent)
            return pix
            
        # Replace currentColor with our desired color
        svg_data = svg_data.replace('currentColor', color)
        
        # Render SVG to pixmap
        renderer = QSvgRenderer(svg_data.encode('utf-8'))
        
        # Support high-DPI (2x for standard rendering logic if needed, though QPixmap is fine)
        # Using a QImage first to ensure transparency
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        
        pixmap = QPixmap.fromImage(image)
        cls._cache[cache_key] = pixmap
        return pixmap
    
    @classmethod
    def clear_cache(cls):
        cls._cache.clear()

    @classmethod
    def get_nav_icon(cls, name: str, color: str = '#94A3B8') -> QIcon:
        return cls.get_icon(f'nav/{name}.svg', color)
    
    @classmethod
    def get_equipment_icon(cls, system_type: str, color: str = '#94A3B8') -> QIcon:
        filename = system_type.lower()
        return cls.get_icon(f'equipment/{filename}.svg', color)
    
    @classmethod
    def get_status_icon(cls, status: str, size: int = 16) -> QIcon:
        status_map = {
            'OPERATIONAL': ('operational.svg', '#10B981'),  # Emerald 500
            'WARNING': ('warning.svg', '#F59E0B'),          # Amber 500
            'FAULT': ('fault.svg', '#EF4444'),              # Red 500
            'IN_MAINTENANCE': ('maintenance.svg', '#3B82F6') # Blue 500
        }
        
        icon_file, color = status_map.get(status.upper(), ('unknown.svg', '#94A3B8'))
        return cls.get_icon(f'status/{icon_file}', color, size)
    
    @classmethod
    def get_action_icon(cls, name: str, color: str = '#94A3B8') -> QIcon:
        return cls.get_icon(f'actions/{name}.svg', color)
