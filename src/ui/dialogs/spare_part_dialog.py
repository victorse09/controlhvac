from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QTextEdit, QPushButton, QMessageBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QListWidget, QListWidgetItem,
    QScrollArea, QWidget, QFrame, QLabel
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor
from ...core.models.inventory import SparePart
from ...core.models.enums import SYSTEM_TYPE_LABELS
from src.ui.icon_manager import IconManager
from src.ui.dialogs.equipment_dialog import _create_dialog_card

class SparePartDialog(QDialog):
    def __init__(self, parent=None, spare_part=None, read_only=None):
        super().__init__(parent)
        self.spare_part = spare_part
        
        # Start in read-only / view mode if opening existing spare part
        self.is_read_only = (spare_part is not None) if read_only is None else read_only
        self.resize(620, 720)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

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
        lbl_icon.setPixmap(IconManager.get_icon("inventory.svg", "#14B8A6", 20).pixmap(20, 20))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        hb_layout.addWidget(icon_badge)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        pname = getattr(self.spare_part, 'name', '') if self.spare_part else "Nuevo Repuesto"
        lbl_t = QLabel(f"Ficha de Repuesto  —  {pname}")
        lbl_t.setObjectName("detailTitleLabel")
        lbl_t.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")
        lbl_s = QLabel("Control de stock, compatibilidad con equipos HVAC y ubicación en bodega")
        lbl_s.setObjectName("kvKeyLabel")
        title_col.addWidget(lbl_t)
        title_col.addWidget(lbl_s)
        hb_layout.addLayout(title_col, 1)
        main_layout.addWidget(header_banner)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_widget.setObjectName("scrollContent")
        scroll_layout = QVBoxLayout(content_widget)
        scroll_layout.setContentsMargins(10, 10, 10, 10)

        card, card_body = _create_dialog_card("Datos del Repuesto e Inventario", "#14B8A6")
        form_layout = QFormLayout(card_body)
        form_layout.setContentsMargins(16, 14, 16, 16)
        form_layout.setSpacing(10)
        
        self.nombre_edit = QLineEdit()
        self.codigo_edit = QLineEdit()
        
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["Filtros", "Correas", "Rodamientos", "Refrigerante", "Lubricante", "Eléctrico", "Válvulas", "Sensores", "Otro"])
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(60)
        
        self.cant = QSpinBox()
        self.cant.setRange(0, 100000)
        
        self.cant_min = QSpinBox()
        self.cant_min.setRange(0, 100000)
        
        self.unidad_combo = QComboBox()
        self.unidad_combo.addItems(["unidad", "litro", "kg", "metro", "galón", "otro"])
        
        self.ubicacion_edit = QLineEdit()
        self.proveedor_edit = QLineEdit()
        
        self.costo = QDoubleSpinBox()
        self.costo.setRange(0, 100000000)
        self.costo.setDecimals(2)
        
        self.moneda = QLineEdit("CLP")
        
        self.equipos_list = QListWidget()
        self.equipos_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.equipos_list.setMaximumHeight(100)
        for sys_type, label in SYSTEM_TYPE_LABELS.items():
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, sys_type.value)
            self.equipos_list.addItem(item)
            
        self.notas_edit = QTextEdit()
        self.notas_edit.setMaximumHeight(60)

        form_layout.addRow("Nombre *:", self.nombre_edit)
        form_layout.addRow("Código/Ref:", self.codigo_edit)
        form_layout.addRow("Categoría:", self.cat_combo)
        form_layout.addRow("Descripción:", self.desc_edit)
        form_layout.addRow("Cantidad:", self.cant)
        form_layout.addRow("Cant. Mínima:", self.cant_min)
        form_layout.addRow("Unidad:", self.unidad_combo)
        form_layout.addRow("Ubicación:", self.ubicacion_edit)
        form_layout.addRow("Proveedor:", self.proveedor_edit)
        form_layout.addRow("Costo Unitario:", self.costo)
        form_layout.addRow("Moneda:", self.moneda)
        form_layout.addRow("Equipos Comp.:", self.equipos_list)
        form_layout.addRow("Notas:", self.notas_edit)

        scroll_layout.addWidget(card)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)

        # Buttons
        footer_bar = QFrame()
        footer_bar.setObjectName("dialogFooterBar")
        btn_layout = QHBoxLayout(footer_bar)
        btn_layout.setContentsMargins(12, 10, 12, 10)
        btn_layout.setSpacing(10)
        btn_layout.addStretch()
        
        # View Mode Buttons
        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.clicked.connect(self.reject)
        
        self.btn_edit_mode = QPushButton("Editar")
        self.btn_edit_mode.setObjectName("primaryButton")
        self.btn_edit_mode.setIcon(IconManager.get_icon("edit.svg", "#000000", 16))
        self.btn_edit_mode.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit_mode.clicked.connect(lambda: self.set_read_only(False))
        
        # Edit / New Mode Buttons
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        
        self.btn_save = QPushButton("Guardar")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setIcon(IconManager.get_icon("check.svg", "#000000", 16))
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self.validate_and_accept)
        
        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_edit_mode)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        main_layout.addWidget(footer_bar)

        if self.spare_part:
            self._load_data()

        self.set_read_only(self.is_read_only)

    def set_read_only(self, read_only: bool):
        self.is_read_only = read_only
        
        # Update Window Title
        if self.spare_part:
            pname = getattr(self.spare_part, 'name', '')
            if read_only:
                self.setWindowTitle(f"Detalle de Repuesto - {pname}")
            else:
                self.setWindowTitle(f"Editar Repuesto - {pname}")
        else:
            self.setWindowTitle("Nuevo Repuesto")

        # Toggle Button Visibility
        self.btn_close.setVisible(read_only)
        self.btn_edit_mode.setVisible(read_only)
        self.btn_cancel.setVisible(not read_only)
        self.btn_save.setVisible(not read_only)

        # Toggle Form Fields
        enabled = not read_only
        self.nombre_edit.setReadOnly(read_only)
        self.codigo_edit.setReadOnly(read_only)
        self.cat_combo.setEnabled(enabled)
        self.desc_edit.setReadOnly(read_only)
        self.cant.setEnabled(enabled)
        self.cant_min.setEnabled(enabled)
        self.unidad_combo.setEnabled(enabled)
        self.ubicacion_edit.setReadOnly(read_only)
        self.proveedor_edit.setReadOnly(read_only)
        self.costo.setEnabled(enabled)
        self.moneda.setReadOnly(read_only)
        self.equipos_list.setEnabled(enabled)
        self.notas_edit.setReadOnly(read_only)

    def _on_cancel_clicked(self):
        if self.spare_part:
            self._load_data()
            self.set_read_only(True)
        else:
            self.reject()

    def _load_data(self):
        self.nombre_edit.setText(self.spare_part.name)
        self.codigo_edit.setText(self.spare_part.part_number)
        self.cat_combo.setCurrentText(self.spare_part.category)
        self.desc_edit.setPlainText(self.spare_part.description)
        self.cant.setValue(self.spare_part.quantity)
        self.cant_min.setValue(self.spare_part.minimum_quantity)
        self.unidad_combo.setCurrentText(self.spare_part.unit)
        self.ubicacion_edit.setText(self.spare_part.location)
        self.proveedor_edit.setText(self.spare_part.supplier)
        self.costo.setValue(self.spare_part.unit_cost)
        self.moneda.setText(self.spare_part.currency)
        
        for i in range(self.equipos_list.count()):
            item = self.equipos_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) in self.spare_part.compatible_equipment:
                item.setSelected(True)
                
        self.notas_edit.setPlainText(self.spare_part.notes)

    def validate_and_accept(self):
        if not self.nombre_edit.text().strip():
            QMessageBox.warning(self, "Error", "El campo Nombre es obligatorio.")
            return
        self.accept()

    def get_spare_part(self) -> SparePart:
        comp_eq = [item.data(Qt.ItemDataRole.UserRole) for item in self.equipos_list.selectedItems()]
        part_id = self.spare_part.id if self.spare_part else ""
        return SparePart(
            id=part_id,
            name=self.nombre_edit.text().strip(),
            part_number=self.codigo_edit.text().strip(),
            category=self.cat_combo.currentText(),
            description=self.desc_edit.toPlainText().strip(),
            quantity=self.cant.value(),
            minimum_quantity=self.cant_min.value(),
            unit=self.unidad_combo.currentText(),
            location=self.ubicacion_edit.text().strip(),
            supplier=self.proveedor_edit.text().strip(),
            unit_cost=self.costo.value(),
            currency=self.moneda.text().strip(),
            compatible_equipment=comp_eq,
            notes=self.notas_edit.toPlainText().strip()
        )
