from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QHeaderView, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from src.core.services.recycle_bin_service import ITEM_TYPE_LABELS
from src.ui.icon_manager import IconManager

class RecycleBinDialog(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent or main_window)
        self.main_window = main_window
        self.recycle_bin_service = main_window.recycle_bin_service
        self.services_map = {
            "client_service": main_window.client_service,
            "equipment_service": main_window.equipment_service,
            "work_order_service": main_window.work_order_service,
            "inventory_service": main_window.inventory_service
        }
        self.items = []
        
        self.setWindowTitle("Papelera de Reciclaje")
        self.resize(720, 540)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Modern Top Header Banner
        header_banner = QFrame()
        header_banner.setObjectName("dialogHeaderBanner")
        hb_layout = QHBoxLayout(header_banner)
        hb_layout.setContentsMargins(14, 10, 14, 10)
        hb_layout.setSpacing(12)

        icon_badge = QFrame()
        icon_badge.setObjectName("statIconBadge")
        icon_badge.setFixedSize(40, 40)
        ib_l = QVBoxLayout(icon_badge)
        ib_l.setContentsMargins(0, 0, 0, 0)
        ib_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon = QLabel()
        lbl_icon.setPixmap(IconManager.get_icon("delete.svg", "#EF4444", 20).pixmap(20, 20))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        hb_layout.addWidget(icon_badge)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        lbl_title = QLabel("Papelera de Reciclaje del Sistema")
        lbl_title.setObjectName("detailTitleLabel")
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")
        self.lbl_info = QLabel("Elementos eliminados recuperables:")
        self.lbl_info.setObjectName("kvKeyLabel")
        title_col.addWidget(lbl_title)
        title_col.addWidget(self.lbl_info)
        hb_layout.addLayout(title_col, 1)
        layout.addWidget(header_banner)

        # Table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Tipo", "Nombre / Elemento", "Fecha Eliminación"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table, 1)

        # Bottom buttons
        footer_bar = QFrame()
        footer_bar.setObjectName("dialogFooterBar")
        btn_layout = QHBoxLayout(footer_bar)
        btn_layout.setContentsMargins(12, 10, 12, 10)
        
        self.btn_empty = QPushButton("Vaciar Papelera")
        self.btn_empty.setObjectName("dangerButton")
        self.btn_empty.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF"))
        self.btn_empty.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_empty.clicked.connect(self._empty_bin)
        btn_layout.addWidget(self.btn_empty)
        
        btn_layout.addStretch()

        self.btn_restore = QPushButton("Restaurar Seleccionado")
        self.btn_restore.setObjectName("primaryButton")
        self.btn_restore.setIcon(IconManager.get_icon("refresh.svg", "#050B14"))
        self.btn_restore.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_restore.setEnabled(False)
        self.btn_restore.clicked.connect(self._restore_selected)
        btn_layout.addWidget(self.btn_restore)

        self.btn_purge = QPushButton("Eliminar Definitivamente")
        self.btn_purge.setObjectName("dangerButton")
        self.btn_purge.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF"))
        self.btn_purge.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_purge.setEnabled(False)
        self.btn_purge.clicked.connect(self._purge_selected)
        btn_layout.addWidget(self.btn_purge)

        close_btn = QPushButton("Cerrar")
        close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addWidget(footer_bar)

        self.refresh_data()

    def get_selected_item(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.items):
            return self.items[row]
        return None

    def refresh_data(self):
        try:
            self.items = self.recycle_bin_service.get_all_recycled_items()
            self.table.setRowCount(len(self.items))
            
            for row, item in enumerate(self.items):
                type_str = ITEM_TYPE_LABELS.get(item.item_type, item.item_type)
                
                try:
                    dt = datetime.fromisoformat(item.deleted_at)
                    date_str = dt.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    date_str = item.deleted_at[:16]

                self.table.setItem(row, 0, QTableWidgetItem(type_str))
                self.table.setItem(row, 1, QTableWidgetItem(item.display_name))
                self.table.setItem(row, 2, QTableWidgetItem(date_str))

            self.lbl_info.setText(f"Elementos eliminados en la papelera: ({len(self.items)})")
            self.btn_empty.setEnabled(len(self.items) > 0)
            self._on_selection_changed()

            # Refresh views on main window
            if hasattr(self.main_window, '_refresh_current_view'):
                self.main_window._refresh_current_view()
        except Exception as e:
            print(f"Error refreshing recycle bin dialog: {e}")

    def _on_selection_changed(self):
        item = self.get_selected_item()
        has_sel = item is not None
        self.btn_restore.setEnabled(has_sel)
        self.btn_purge.setEnabled(has_sel)

    def _restore_selected(self):
        item = self.get_selected_item()
        if not item:
            return
            
        type_str = ITEM_TYPE_LABELS.get(item.item_type, item.item_type)
        if self.recycle_bin_service.restore_item(item.id, self.services_map):
            QMessageBox.information(
                self, 
                "Restauración Exitosa", 
                f"El elemento '{item.display_name}' ({type_str}) ha sido restaurado correctamente."
            )
            self.refresh_data()
        else:
            QMessageBox.critical(self, "Error", "No se pudo restaurar el elemento.")

    def _purge_selected(self):
        item = self.get_selected_item()
        if not item:
            return
            
        reply = QMessageBox.question(
            self,
            "Eliminar Definitivamente",
            f"¿Está seguro de que desea eliminar definitivamente '{item.display_name}'?\nEsta acción BORRARÁ el elemento para siempre.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.recycle_bin_service.purge_item(item.id):
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el elemento.")

    def _empty_bin(self):
        if not self.items:
            return
            
        reply = QMessageBox.question(
            self,
            "Vaciar Papelera de Reciclaje",
            "¿Está seguro de vaciar toda la Papelera de Reciclaje?\nTodos los elementos eliminados se perderán de forma permanente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.recycle_bin_service.empty_bin()
            self.refresh_data()
