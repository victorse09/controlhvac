from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

class StatusBadge(QLabel):
    def __init__(self, text: str, status_type: str = "default", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status(status_type, text)

    def set_status(self, status_type: str, text: str = None):
        if text:
            self.setText(text)
            
        status_type = status_type.upper()
        
        # Determine colors based on status type
        bg_color = "#334155" # Default gray
        text_color = "#F8FAFC"
        
        if status_type in ["OPERATIONAL", "COMPLETED", "AVAILABLE"]:
            bg_color = "rgba(16, 185, 129, 0.2)" # Emerald
            text_color = "#10B981"
        elif status_type in ["WARNING", "SCHEDULED", "IN_USE", "NORMAL", "PREVENTIVE"]:
            bg_color = "rgba(245, 158, 11, 0.2)" # Amber
            text_color = "#F59E0B"
        elif status_type in ["FAULT", "OVERDUE", "OUT_OF_SERVICE", "HIGH", "URGENT", "CORRECTIVE"]:
            bg_color = "rgba(239, 68, 68, 0.2)" # Red
            text_color = "#EF4444"
        elif status_type in ["IN_MAINTENANCE", "IN_PROGRESS", "IN_CALIBRATION", "ONE_TIME"]:
            bg_color = "rgba(59, 130, 246, 0.2)" # Blue
            text_color = "#3B82F6"
        elif status_type in ["LOW"]:
            bg_color = "rgba(148, 163, 184, 0.2)" # Slate
            text_color = "#94A3B8"

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)
