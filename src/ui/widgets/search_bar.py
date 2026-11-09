from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit
from PySide6.QtCore import Signal, QTimer, Qt

class SearchBar(QWidget):
    search_triggered = Signal(str)
    textChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("searchBarWidget")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar...")
        
        # Debounce timer
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(300)
        self.debounce_timer.timeout.connect(self._on_timeout)

        self.search_input.textChanged.connect(self._on_text_changed)

        layout.addWidget(self.search_input)

    def _on_text_changed(self, text):
        self.textChanged.emit(text)
        self.debounce_timer.stop()
        self.debounce_timer.start()

    def _on_timeout(self):
        self.search_triggered.emit(self.search_input.text())
        
    def clear(self):
        self.search_input.clear()
        
    def text(self):
        return self.search_input.text()

    def setPlaceholderText(self, text: str):
        self.search_input.setPlaceholderText(text)
