import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from src.app.config import APP_NAME, APP_VERSION
from src.ui.icon_manager import IconManager


class SplashScreen(QWidget):
    """Modern frameless splash screen with progress feedback during application boot."""

    def __init__(self, logo_path: str = ""):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(480, 260)

        self._setup_ui(logo_path)
        self._center_on_screen()

    def _center_on_screen(self):
        screen = self.screen()
        if screen:
            screen_geom = screen.geometry()
            x = (screen_geom.width() - self.width()) // 2
            y = (screen_geom.height() - self.height()) // 2
            self.move(x, y)

    def _setup_ui(self, logo_path: str = ""):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Container card with dark aesthetic matching ControlHVAC Midnight Pro
        card = QWidget(self)
        card.setObjectName("splashCard")
        card.setStyleSheet("""
            QWidget#splashCard {
                background-color: #0F172A;
                border: 1px solid #1E293B;
                border-radius: 12px;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 24)
        card_layout.setSpacing(12)

        # Top section: App Icon & Brand
        top_layout = QHBoxLayout()
        top_layout.setSpacing(16)

        icon_lbl = QLabel()
        app_pixmap = None

        if logo_path and os.path.exists(logo_path):
            p = QPixmap(logo_path)
            if not p.isNull():
                app_pixmap = p.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        if not app_pixmap or app_pixmap.isNull():
            app_pixmap = IconManager.get_pixmap("app_icon", "#38BDF8", 48)

        icon_lbl.setPixmap(app_pixmap)
        icon_lbl.setFixedSize(48, 48)
        top_layout.addWidget(icon_lbl)

        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(2)

        title_lbl = QLabel(APP_NAME)
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 700; color: #F8FAFC; letter-spacing: 0.5px;")

        subtitle_lbl = QLabel(f"CMMS Climatización & Gestión Técnica • v{APP_VERSION}")
        subtitle_lbl.setStyleSheet("font-size: 11px; color: #94A3B8; font-weight: 500;")

        brand_layout.addWidget(title_lbl)
        brand_layout.addWidget(subtitle_lbl)
        top_layout.addLayout(brand_layout)
        top_layout.addStretch()

        card_layout.addLayout(top_layout)
        card_layout.addStretch()

        # Status Label
        self.status_lbl = QLabel("Iniciando aplicación...")
        self.status_lbl.setStyleSheet("font-size: 11px; color: #38BDF8; font-weight: 500;")
        card_layout.addWidget(self.status_lbl)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1E293B;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:1 #38BDF8);
                border-radius: 3px;
            }
        """)
        card_layout.addWidget(self.progress_bar)

        layout.addWidget(card)

    def set_progress(self, percent: int, message: str = ""):
        """Updates progress percentage (0-100) and status message."""
        self.progress_bar.setValue(percent)
        if message:
            self.status_lbl.setText(message)
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
