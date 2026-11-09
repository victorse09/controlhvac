from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

class StatCard(QFrame):
    def __init__(self, title: str, value: str, icon: QIcon = None, subtitle: str = None, trend: str = None, accent_color: str = "#38BDF8", parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        self.setObjectName("statCardFrame")
        self.setMinimumWidth(180)
        self.setMinimumHeight(96)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            f"QFrame#statCardFrame {{"
            f"  border-left: 4px solid {self.accent_color};"
            f"}}"
            f"QFrame#statCardFrame:hover {{"
            f"  border-left: 4px solid {self.accent_color};"
            f"}}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        # Header with Title and optional Icon
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel(title.upper())
        title_label.setObjectName("kvKeyLabel")
        title_label.setStyleSheet(
            "font-size: 11px; font-weight: 700; "
            "letter-spacing: 0.5px; background: transparent; border: none;"
        )
        header_layout.addWidget(title_label)
        
        if icon and not icon.isNull():
            icon_badge = QFrame()
            icon_badge.setObjectName("statIconBadge")
            icon_badge.setFixedSize(30, 30)
            ib_layout = QHBoxLayout(icon_badge)
            ib_layout.setContentsMargins(0, 0, 0, 0)
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setPixmap(icon.pixmap(18, 18))
            icon_label.setStyleSheet("background: transparent; border: none;")
            ib_layout.addWidget(icon_label)
            header_layout.addWidget(icon_badge, 0, Qt.AlignmentFlag.AlignRight)
            
        layout.addLayout(header_layout)

        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"color: {self.accent_color}; font-size: 24px; font-weight: 800; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self.value_label)

        # Footer with subtitle and trend
        if subtitle or trend:
            footer_layout = QHBoxLayout()
            footer_layout.setContentsMargins(0, 0, 0, 0)
            if trend:
                trend_label = QLabel(trend)
                if "+" in trend or "↑" in trend:
                    trend_label.setStyleSheet("color: #10B981; font-size: 11px; font-weight: bold; background: transparent;")
                elif "-" in trend or "↓" in trend:
                    trend_label.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: bold; background: transparent;")
                else:
                    trend_label.setObjectName("richBodyLabel")
                footer_layout.addWidget(trend_label)

            if subtitle:
                sub_label = QLabel(subtitle)
                sub_label.setObjectName("muted")
                footer_layout.addWidget(sub_label)
                
            footer_layout.addStretch()
            layout.addLayout(footer_layout)

        layout.addStretch()

    def set_value(self, value: str):
        self.value_label.setText(value)
