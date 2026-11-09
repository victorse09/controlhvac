from PySide6.QtWidgets import QCalendarWidget
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QPen

class HVACCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.events = {}  # Format: {'YYYY-MM-DD': [{'type': '...', 'color': '...', 'title': '...'}]}
        
        self.setStyleSheet("""
            QCalendarWidget QWidget {
                alternate-background-color: #1E293B;
            }
            QCalendarWidget QToolButton {
                color: #F8FAFC;
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #334155;
            }
            QCalendarWidget QMenu {
                background-color: #1E293B;
                color: #F8FAFC;
            }
            QCalendarWidget QSpinBox {
                background-color: #0F172A;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 4px;
            }
            QCalendarWidget QAbstractItemView:enabled {
                background-color: #0F172A;
                color: #F8FAFC;
                selection-background-color: #0EA5E9;
                selection-color: #F8FAFC;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #475569;
            }
        """)

    def set_events(self, events: dict):
        self.events = events
        self.updateCells()

    def paintCell(self, painter: QPainter, rect: QRect, date):
        super().paintCell(painter, rect, date)
        
        date_str = date.toString("yyyy-MM-dd")
        if date_str in self.events:
            events_today = self.events[date_str]
            if not events_today:
                return
                
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw dots at bottom
            dot_size = 4
            spacing = 2
            total_width = len(events_today) * dot_size + (len(events_today) - 1) * spacing
            start_x = rect.x() + (rect.width() - total_width) // 2
            y = rect.bottom() - 6
            
            for i, event in enumerate(events_today[:3]): # max 3 dots
                color = QColor(event.get('color', '#0EA5E9'))
                painter.setBrush(color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(start_x + i * (dot_size + spacing), y, dot_size, dot_size)
                
            if len(events_today) > 3:
                # draw a plus or more indicator
                painter.setPen(QPen(QColor("#94A3B8"), 1))
                painter.drawText(QRect(start_x + 3 * (dot_size + spacing), y - 4, 10, 10), Qt.AlignmentFlag.AlignCenter, "+")
                
            painter.restore()


HVACCalendarWidget = HVACCalendar

