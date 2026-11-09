from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableView, 
    QPushButton, QLabel, QFrame, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor
from src.ui.widgets.search_bar import SearchBar
from src.ui.models.table_models import ToolTableModel
from src.ui.dialogs.tool_dialog import ToolDialog
from src.ui.icon_manager import IconManager

class ToolsView(QWidget):
    def __init__(self, inventory_service, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.tools = []
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search_bar = SearchBar()
        self.search_bar.setPlaceholderText("Buscar herramientas por nombre, código, serie, ubicación...")
        self.search_bar.textChanged.connect(self.on_search)
        
        self.btn_new = QPushButton()
        self.btn_new.setObjectName("primaryButton")
        self.btn_new.setIcon(IconManager.get_icon("add.svg", "#FFFFFF", 18))
        self.btn_new.setIconSize(QSize(18, 18))
        self.btn_new.setFixedSize(36, 36)
        self.btn_new.setToolTip("Nueva Herramienta")
        self.btn_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new.clicked.connect(self.on_new)
        
        toolbar.addWidget(self.search_bar, 1)
        toolbar.addWidget(self.btn_new)
        main_layout.addLayout(toolbar)

        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        # Table
        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.model = ToolTableModel([])
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.on_edit_double_click)
        self.splitter.addWidget(self.table)

        # Detail frame
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("cardFrame")
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(12)
        
        # Detail header actions
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        self.lbl_title = QLabel("Seleccione una herramienta")
        self.lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #F8FAFC;")
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()

        self.btn_edit = QPushButton()
        self.btn_edit.setIcon(IconManager.get_icon("edit.svg", "#F8FAFC", 18))
        self.btn_edit.setIconSize(QSize(18, 18))
        self.btn_edit.setFixedSize(36, 36)
        self.btn_edit.setToolTip("Editar Herramienta seleccionada")
        self.btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self.on_edit_clicked)
        header_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton()
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 18))
        self.btn_delete.setIconSize(QSize(18, 18))
        self.btn_delete.setFixedSize(36, 36)
        self.btn_delete.setToolTip("Eliminar Herramienta seleccionada")
        self.btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.on_delete)
        header_layout.addWidget(self.btn_delete)

        detail_layout.addLayout(header_layout)

        self.lbl_detail = QLabel("Haga clic en una herramienta para ver su información detallada.")
        self.lbl_detail.setStyleSheet("color: #CBD5E1; line-height: 1.5; font-size: 13px;")
        self.lbl_detail.setWordWrap(True)
        detail_layout.addWidget(self.lbl_detail)
        
        detail_layout.addStretch()
        self.splitter.addWidget(self.detail_frame)
        self.splitter.setSizes([550, 450])

    def get_selected_tool(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.get_item(indexes[0].row())

    def refresh_data(self):
        try:
            self.tools = self.inventory_service.get_all_tools()
            self.model.set_data(self.tools)
            self.on_selection_changed()
        except Exception as e:
            print(f"Error refreshing tools: {e}")

    def on_search(self, text):
        query = text.strip().lower()
        if not query:
            self.model.set_data(self.tools)
            return
            
        filtered = [
            t for t in self.tools 
            if query in (t.name or '').lower() or 
               query in (t.brand or '').lower() or 
               query in (t.model or '').lower() or 
               query in (t.serial_number or '').lower()
        ]
        self.model.set_data(filtered)

    def on_selection_changed(self):
        tool = self.get_selected_tool()
        if not tool:
            self.lbl_title.setText("Seleccione una herramienta")
            self.lbl_detail.setText("Haga clic en una herramienta para ver su información detallada.")
            self.btn_edit.setEnabled(False)
            self.btn_delete.setEnabled(False)
            return

        self.lbl_title.setText(tool.name)
        self.btn_edit.setEnabled(True)
        self.btn_delete.setEnabled(True)

        status_val = tool.status.value if hasattr(tool.status, 'value') else str(tool.status)
        calib_req = "Sí" if getattr(tool, 'requires_calibration', False) else "No"
        next_cal = getattr(tool, 'next_calibration_date', None) or getattr(tool, 'next_calibration', None) or 'N/A'

        lines = [
            f"<b>Nombre:</b> {tool.name}",
            f"<b>Marca:</b> {tool.brand or 'N/A'}",
            f"<b>Modelo:</b> {tool.model or 'N/A'}",
            f"<b>Serial:</b> {tool.serial_number or 'N/A'}",
            f"<b>Estado:</b> {status_val}",
            f"<b>Asignado a:</b> {tool.assigned_to or 'Disponible'}",
            f"<b>Requiere Calibración:</b> {calib_req}",
            f"<b>Próxima Calibración:</b> {next_cal}",
        ]
        if hasattr(tool, 'notes') and tool.notes:
            lines.append(f"<br><b>Notas:</b> {tool.notes}")

        self.lbl_detail.setText("<br>".join(lines))

    def on_new(self):
        dialog = ToolDialog(parent=self)
        if dialog.exec():
            t = dialog.get_tool()
            self.inventory_service.save_tool(t)
            self.refresh_data()

    def on_edit_clicked(self):
        tool = self.get_selected_tool()
        if tool:
            dialog = ToolDialog(parent=self, tool=tool)
            if dialog.exec():
                updated = dialog.get_tool()
                self.inventory_service.save_tool(updated)
                self.refresh_data()

    def on_edit_double_click(self, index):
        tool = self.model.get_item(index.row())
        if tool:
            dialog = ToolDialog(parent=self, tool=tool)
            if dialog.exec():
                updated = dialog.get_tool()
                self.inventory_service.save_tool(updated)
                self.refresh_data()

    def on_delete(self):
        tool = self.get_selected_tool()
        if not tool:
            return
        reply = QMessageBox.question(
            self,
            "Eliminar Herramienta",
            f"¿Está seguro de que desea eliminar la herramienta '{tool.name}'?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.inventory_service.delete_tool(tool.id):
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar la herramienta.")
