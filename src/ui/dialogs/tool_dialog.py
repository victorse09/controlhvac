from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QTextEdit, QPushButton, QDateEdit, QMessageBox,
    QComboBox, QSpinBox, QScrollArea, QWidget, QFrame, QLabel
)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QCursor
from ...core.models.inventory import Tool
from ...core.models.enums import TOOL_STATUS_LABELS
from src.ui.icon_manager import IconManager
from src.ui.dialogs.equipment_dialog import _create_dialog_card


class ToolDialog(QDialog):
    def __init__(self, parent=None, tool=None, read_only=None):
        super().__init__(parent)
        self.tool = tool
        
        # Start in read-only / view mode if opening existing tool
        self.is_read_only = (tool is not None) if read_only is None else read_only
        self.resize(620, 680)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # ── Header Banner ──
        header_banner = QFrame()
        header_banner.setObjectName("dialogHeaderBanner")
        hb_layout = QHBoxLayout(header_banner)
        hb_layout.setContentsMargins(16, 12, 16, 12)
        hb_layout.setSpacing(14)

        icon_badge = QFrame()
        icon_badge.setObjectName("statIconBadge")
        icon_badge.setFixedSize(44, 44)
        ib_l = QVBoxLayout(icon_badge)
        ib_l.setContentsMargins(0, 0, 0, 0)
        ib_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon = QLabel()
        lbl_icon.setPixmap(IconManager.get_icon("tools.svg", "#818CF8", 22).pixmap(22, 22))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        hb_layout.addWidget(icon_badge)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        tname = getattr(self.tool, 'name', '') if self.tool else "Nueva Herramienta"
        self.lbl_header_title = QLabel(f"Herramienta de Pañol  —  {tname}")
        self.lbl_header_title.setObjectName("detailTitleLabel")
        self.lbl_header_title.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")
        lbl_s = QLabel("Control de instrumentos de medición, herramientas técnicas, calibración y préstamos")
        lbl_s.setObjectName("kvKeyLabel")
        title_col.addWidget(self.lbl_header_title)
        title_col.addWidget(lbl_s)
        hb_layout.addLayout(title_col, 1)

        self.lbl_status_pill = QLabel("●  Disponible")
        hb_layout.addWidget(self.lbl_status_pill)

        main_layout.addWidget(header_banner)

        # ── Scrollable Body ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_widget.setObjectName("scrollContent")
        scroll_layout = QVBoxLayout(content_widget)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(12)

        # Card 1: Identificación y Estado
        card_id, body_id = _create_dialog_card("1. Identificación y Estado de la Herramienta", "#818CF8")
        form_id = QFormLayout(body_id)
        form_id.setContentsMargins(16, 14, 16, 14)
        form_id.setSpacing(10)
        form_id.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.nombre_edit = QLineEdit()
        self.nombre_edit.textChanged.connect(self._update_pill)
        self.marca_edit = QLineEdit()
        self.modelo_edit = QLineEdit()
        self.serie_edit = QLineEdit()
        
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["Medición", "Manual", "Eléctrica", "Refrigeración", "Diagnóstico", "Otro"])
        
        self.estado_combo = QComboBox()
        for s, label in TOOL_STATUS_LABELS.items():
            self.estado_combo.addItem(label, s.value)
        self.estado_combo.currentIndexChanged.connect(self._update_pill)
            
        self.ubicacion_edit = QLineEdit()

        form_id.addRow("Nombre *:", self.nombre_edit)
        form_id.addRow("Marca:", self.marca_edit)
        form_id.addRow("Modelo:", self.modelo_edit)
        form_id.addRow("Nro. Serie:", self.serie_edit)
        form_id.addRow("Categoría:", self.cat_combo)
        form_id.addRow("Estado Operativo:", self.estado_combo)
        form_id.addRow("Ubicación en Pañol:", self.ubicacion_edit)
        scroll_layout.addWidget(card_id)

        # Card 2: Calibración y Notas
        card_cal, body_cal = _create_dialog_card("2. Control de Calibración, Compra y Observaciones", "#38BDF8")
        form_cal = QFormLayout(body_cal)
        form_cal.setContentsMargins(16, 14, 16, 14)
        form_cal.setSpacing(10)
        form_cal.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.compra = QDateEdit()
        self.compra.setCalendarPopup(True)
        self.compra.setDate(QDate.currentDate())
        
        self.calibracion = QDateEdit()
        self.calibracion.setCalendarPopup(True)
        self.calibracion.setDate(QDate.currentDate())
        
        self.prox_calibracion = QDateEdit()
        self.prox_calibracion.setCalendarPopup(True)
        self.prox_calibracion.setDate(QDate.currentDate().addYears(1))
        
        self.intervalo = QSpinBox()
        self.intervalo.setRange(0, 3650)
        self.intervalo.setValue(365)
        
        self.notas_edit = QTextEdit()
        self.notas_edit.setMaximumHeight(65)

        form_cal.addRow("Fecha Compra:", self.compra)
        form_cal.addRow("Última Calibración:", self.calibracion)
        form_cal.addRow("Próx. Calibración:", self.prox_calibracion)
        form_cal.addRow("Intervalo (días):", self.intervalo)
        form_cal.addRow("Notas / Certificados:", self.notas_edit)
        scroll_layout.addWidget(card_cal)
        scroll_layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)

        # ── Footer Bar ──
        footer_bar = QFrame()
        footer_bar.setObjectName("dialogFooterBar")
        btn_layout = QHBoxLayout(footer_bar)
        btn_layout.setContentsMargins(14, 10, 14, 10)
        btn_layout.setSpacing(10)

        self.lbl_mode = QLabel("● MODO EDICIÓN")
        self.lbl_mode.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 11px;")
        btn_layout.addWidget(self.lbl_mode)
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
        
        self.btn_save = QPushButton("Guardar Herramienta")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setIcon(IconManager.get_icon("check.svg", "#000000", 16))
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self.validate_and_accept)
        
        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_edit_mode)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        main_layout.addWidget(footer_bar)

        if self.tool:
            self._load_data()
        self._update_pill()
        self.set_read_only(self.is_read_only)

    def _update_pill(self):
        tname = self.nombre_edit.text().strip() or (self.tool.name if self.tool else "Nueva Herramienta")
        self.lbl_header_title.setText(f"Herramienta de Pañol  —  {tname}")
        st_code = (self.estado_combo.currentData() or "AVAILABLE").upper()
        st_txt = self.estado_combo.currentText()
        if st_code == "AVAILABLE":
            fg, bg = "#10B981", "#064E3B"
        elif st_code == "IN_USE":
            fg, bg = "#F59E0B", "#451A03"
        elif st_code == "OUT_OF_SERVICE":
            fg, bg = "#EF4444", "#450A0A"
        else:
            fg, bg = "#38BDF8", "#0C4A6E"
        self.lbl_status_pill.setText(f"●  {st_txt}")
        self.lbl_status_pill.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border: 1px solid {fg}; "
            f"border-radius: 5px; padding: 4px 10px; font-weight: bold; font-size: 11px;"
        )

    def set_read_only(self, read_only: bool):
        self.is_read_only = read_only
        
        if self.tool:
            tname = getattr(self.tool, 'name', '')
            if read_only:
                self.setWindowTitle(f"Detalle de Herramienta - {tname}")
                self.lbl_mode.setText("● MODO LECTURA / CONSULTA")
                self.lbl_mode.setStyleSheet("color: #94A3B8; font-weight: bold; font-size: 11px;")
            else:
                self.setWindowTitle(f"Editar Herramienta - {tname}")
                self.lbl_mode.setText("● MODO EDICIÓN ACTIVO")
                self.lbl_mode.setStyleSheet("color: #F59E0B; font-weight: bold; font-size: 11px;")
        else:
            self.setWindowTitle("Nueva Herramienta")
            self.lbl_mode.setText("● NUEVA HERRAMIENTA")
            self.lbl_mode.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px;")

        self.btn_close.setVisible(read_only)
        self.btn_edit_mode.setVisible(read_only)
        self.btn_cancel.setVisible(not read_only)
        self.btn_save.setVisible(not read_only)

        enabled = not read_only
        self.nombre_edit.setReadOnly(read_only)
        self.marca_edit.setReadOnly(read_only)
        self.modelo_edit.setReadOnly(read_only)
        self.serie_edit.setReadOnly(read_only)
        self.cat_combo.setEnabled(enabled)
        self.estado_combo.setEnabled(enabled)
        self.ubicacion_edit.setReadOnly(read_only)
        self.compra.setEnabled(enabled)
        self.calibracion.setEnabled(enabled)
        self.prox_calibracion.setEnabled(enabled)
        self.intervalo.setEnabled(enabled)
        self.notas_edit.setReadOnly(read_only)

    def _on_cancel_clicked(self):
        if self.tool:
            self._load_data()
            self.set_read_only(True)
        else:
            self.reject()

    def _load_data(self):
        self.nombre_edit.setText(self.tool.name)
        self.marca_edit.setText(self.tool.brand)
        self.modelo_edit.setText(self.tool.model)
        self.serie_edit.setText(self.tool.serial_number)
        self.cat_combo.setCurrentText(self.tool.category)
        
        idx = self.estado_combo.findData(self.tool.status)
        if idx >= 0:
            self.estado_combo.setCurrentIndex(idx)
        
        self.ubicacion_edit.setText(self.tool.location)
        
        if self.tool.purchase_date:
            try:
                self.compra.setDate(QDate.fromString(self.tool.purchase_date[:10], Qt.DateFormat.ISODate))
            except Exception:
                pass
        if self.tool.calibration_date:
            try:
                self.calibracion.setDate(QDate.fromString(self.tool.calibration_date[:10], Qt.DateFormat.ISODate))
            except Exception:
                pass
        if self.tool.next_calibration:
            try:
                self.prox_calibracion.setDate(QDate.fromString(self.tool.next_calibration[:10], Qt.DateFormat.ISODate))
            except Exception:
                pass
            
        self.intervalo.setValue(self.tool.calibration_interval_days)
        self.notas_edit.setPlainText(self.tool.notes)

    def validate_and_accept(self):
        if not self.nombre_edit.text().strip():
            QMessageBox.warning(self, "Error", "El campo Nombre es obligatorio.")
            return
        self.accept()

    def get_tool(self) -> Tool:
        tool_id = self.tool.id if self.tool else ""
        assigned_to = getattr(self.tool, 'assigned_to', '') if self.tool else ""
        if self.estado_combo.currentData() == "AVAILABLE":
            assigned_to = ""
        return Tool(
            id=tool_id,
            name=self.nombre_edit.text().strip(),
            brand=self.marca_edit.text().strip(),
            model=self.modelo_edit.text().strip(),
            serial_number=self.serie_edit.text().strip(),
            category=self.cat_combo.currentText(),
            status=self.estado_combo.currentData(),
            location=self.ubicacion_edit.text().strip(),
            assigned_to=assigned_to,
            purchase_date=self.compra.date().toString(Qt.DateFormat.ISODate),
            calibration_date=self.calibracion.date().toString(Qt.DateFormat.ISODate),
            next_calibration=self.prox_calibracion.date().toString(Qt.DateFormat.ISODate),
            calibration_interval_days=self.intervalo.value(),
            notes=self.notas_edit.toPlainText().strip()
        )
