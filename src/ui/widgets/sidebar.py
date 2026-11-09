from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy, QHBoxLayout
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QCursor, QPixmap
import os
from ..icon_manager import IconManager

class Sidebar(QWidget):
    navigation_changed = Signal(str)
    settings_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.active_button = None
        self.active_section = "dashboard"
        self.nav_buttons = {}

        self._setup_header()
        self._setup_navigation()
        self._setup_footer()

    def _setup_header(self):
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(18, 22, 18, 18)
        header_layout.setSpacing(4)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.hide()
        header_layout.addWidget(self.logo_label)

        title = QLabel("ControlHVAC")
        title.setObjectName("h1")
        
        subtitle = QLabel("CMMS Climatización")
        subtitle.setObjectName("muted")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        
        self.layout.addWidget(header_widget)

    def update_logo(self, logo_path: str = ""):
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(200, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(scaled_pixmap)
                self.logo_label.show()
                return
        self.logo_label.hide()
        self.logo_label.setPixmap(QPixmap())

    def _setup_navigation(self):
        nav_widget = QWidget()
        self.nav_layout = QVBoxLayout(nav_widget)
        self.nav_layout.setContentsMargins(10, 0, 10, 0)
        self.nav_layout.setSpacing(4)

        sections = [
            ("dashboard", "Panel de Control", "dashboard"),
            ("clients", "Clientes", "clients"),
            ("equipment", "Equipos", "equipment"),
            ("incidents", "Averías y Obs.", "incidents"),
            ("work_orders", "Órdenes de Trabajo", "work_orders"),
            ("calendar", "Tablero de Tareas", "calendar"),
            ("technicians", "Técnicos", "technicians"),
            ("panol", "Pañol (Insumos / EPP)", "tools"),
            ("spare_parts", "Repuestos", "spare_parts"),
            ("library", "Librería", "library"),
        ]

        self.nav_buttons = {}
        for section_id, text, icon_name in sections:
            btn = QPushButton(text)
            btn.setObjectName("sidebarNavBtn")
            icon = IconManager.get_nav_icon(icon_name)
            btn.setIcon(icon)
            btn.setIconSize(QSize(18, 18))
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setProperty("active", False)
            
            btn.clicked.connect(lambda checked=False, sid=section_id: self._on_nav_clicked(sid))
            self.nav_layout.addWidget(btn)
            self.nav_buttons[section_id] = btn

        self.layout.addWidget(nav_widget)
        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def _setup_footer(self):
        footer_widget = QWidget()
        footer_layout = QVBoxLayout(footer_widget)
        footer_layout.setContentsMargins(16, 16, 16, 16)
        footer_layout.setSpacing(6)

        settings_btn = QPushButton("Configuración")
        settings_btn.setObjectName("sidebarSettingsBtn")
        settings_btn.setIcon(IconManager.get_nav_icon("settings"))
        settings_btn.setIconSize(QSize(18, 18))
        settings_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        settings_btn.clicked.connect(self.settings_requested.emit)
        
        version_label = QLabel("v1.0.0")
        version_label.setObjectName("muted")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        footer_layout.addWidget(settings_btn)
        footer_layout.addWidget(version_label)
        
        self.layout.addWidget(footer_widget)

    def _on_nav_clicked(self, section_id: str):
        self.set_active(section_id)
        self.navigation_changed.emit(section_id)

    def set_active(self, section_id: str):
        self.active_section = section_id
        if self.active_button:
            self.active_button.setProperty("active", False)
            self.active_button.style().unpolish(self.active_button)
            self.active_button.style().polish(self.active_button)
        
        btn = self.nav_buttons.get(section_id)
        if btn:
            btn.setProperty("active", True)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            self.active_button = btn
