from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QTextEdit, QPushButton, QDateEdit, QMessageBox,
    QComboBox, QGroupBox, QScrollArea, QWidget, QDoubleSpinBox, QSpinBox, QCheckBox,
    QListWidget, QListWidgetItem, QLabel, QFrame
)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QCursor
from ...core.models.equipment import HVACEquipment, TECHNICAL_SPEC_FIELDS
from ...core.models.enums import (
    SYSTEM_TYPE_LABELS, OPERATIONAL_STATUS_LABELS, MAINTENANCE_FREQUENCY_LABELS
)
from ...core.services.custom_lists_service import (
    EQUIPMENT_DROPDOWN_MAP, DEFAULT_CUSTOM_LISTS
)
from src.ui.icon_manager import IconManager


def _create_dialog_card(title: str, accent_color: str = "#38BDF8"):
    """Creates a modern styled section card matching the main views (eqSectionCard + eqCardHeader)."""
    card = QFrame()
    card.setObjectName("eqSectionCard")
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(0, 0, 0, 0)
    card_layout.setSpacing(0)

    header = QFrame()
    header.setObjectName("eqCardHeader")
    header.setStyleSheet(f"QFrame#eqCardHeader {{ border-bottom: 2px solid {accent_color}; }}")
    h_layout = QHBoxLayout(header)
    h_layout.setContentsMargins(14, 9, 14, 9)

    dot = QLabel("●")
    dot.setStyleSheet(f"color: {accent_color}; font-size: 10px; background: transparent; border: none;")
    h_layout.addWidget(dot)

    lbl = QLabel(title.upper())
    lbl.setStyleSheet(
        f"color: {accent_color}; font-weight: 700; font-size: 11px; "
        f"letter-spacing: 0.7px; background: transparent; border: none;"
    )
    h_layout.addWidget(lbl)
    h_layout.addStretch()

    card_layout.addWidget(header)

    body = QWidget()
    body.setObjectName("eqCardBody")
    card_layout.addWidget(body)
    return card, body

class EquipmentDialog(QDialog):
    def __init__(self, parent=None, client_service=None, inventory_service=None, custom_lists_service=None, equipment_service=None, client_id="", site_id="", floor_area="", equipment=None, read_only=None):
        super().__init__(parent)
        self.client_service = client_service
        self.inventory_service = inventory_service
        self.custom_lists_service = custom_lists_service
        self.equipment_service = equipment_service
        
        # Fallback to parent attributes if not provided directly
        if self.equipment_service is None and hasattr(parent, 'equipment_service'):
            self.equipment_service = parent.equipment_service
        if self.custom_lists_service is None and hasattr(parent, 'custom_lists_service'):
            self.custom_lists_service = parent.custom_lists_service
        if self.custom_lists_service is None and hasattr(parent, 'main_window') and hasattr(parent.main_window, 'custom_lists_service'):
            self.custom_lists_service = parent.main_window.custom_lists_service

        self.client_id = client_id
        self.site_id = site_id
        self.floor_area = floor_area
        self.equipment = equipment
        self.tech_fields = {}
        self.tech_container = None
        
        # If opening existing equipment, start in read-only / view mode by default to prevent accidental edits
        self.is_read_only = (equipment is not None) if read_only is None else read_only
        
        if equipment:
            self.client_id = equipment.client_id
            self.site_id = equipment.site_id
            self.floor_area = getattr(equipment, 'floor_area', '')
            
        self.resize(740, 860)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        self._setup_header_banner()
        main_layout.addWidget(self.header_banner)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_widget.setObjectName("scrollContent")
        self.layout = QVBoxLayout(content_widget)
        self.layout.setSpacing(14)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        self._setup_general_section()
        self._setup_tech_specs_section()
        self._setup_spare_parts_section()
        self._setup_service_history_section()
        self._setup_other_section()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)

        # Bottom Button Bar
        footer_bar = QFrame()
        footer_bar.setObjectName("dialogFooterBar")
        btn_layout = QHBoxLayout(footer_bar)
        btn_layout.setContentsMargins(12, 10, 12, 10)
        btn_layout.setSpacing(10)

        self.lbl_mode_badge = QLabel()
        self.lbl_mode_badge.setStyleSheet("font-size: 11.5px; font-weight: 600; background: transparent;")
        btn_layout.addWidget(self.lbl_mode_badge)
        btn_layout.addStretch()
        
        # View Mode Buttons
        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setMinimumWidth(100)
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.clicked.connect(self.reject)
        
        self.btn_edit_mode = QPushButton("  Editar Ficha")
        self.btn_edit_mode.setObjectName("primaryButton")
        self.btn_edit_mode.setMinimumWidth(130)
        self.btn_edit_mode.setIcon(IconManager.get_icon("edit.svg", "#000000", 16))
        self.btn_edit_mode.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit_mode.clicked.connect(lambda: self.set_read_only(False))
        
        # Edit / New Mode Buttons
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setMinimumWidth(100)
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        
        self.btn_save = QPushButton("  Guardar Equipo")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setMinimumWidth(145)
        self.btn_save.setIcon(IconManager.get_icon("check.svg", "#000000", 16))
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self.validate_and_accept)
        
        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_edit_mode)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        
        main_layout.addWidget(footer_bar)

        if self.equipment:
            self._load_data()
        else:
            self._on_type_changed(self.tipo_combo.currentData())

        # Connect live signals to refresh header banner
        self.tag_edit.textChanged.connect(lambda _: self._refresh_header_banner())
        self.bms_id_edit.textChanged.connect(lambda _: self._refresh_header_banner())
        self.piso_edit.textChanged.connect(lambda _: self._refresh_header_banner())
        self.estado_combo.currentIndexChanged.connect(lambda _: self._refresh_header_banner())
        self.estado_bms_combo.currentIndexChanged.connect(lambda _: self._refresh_header_banner())

        self.set_read_only(self.is_read_only)
        self._refresh_header_banner()

    def _setup_header_banner(self):
        self.header_banner = QFrame()
        self.header_banner.setObjectName("dialogHeaderBanner")
        banner_layout = QHBoxLayout(self.header_banner)
        banner_layout.setContentsMargins(14, 12, 14, 12)
        banner_layout.setSpacing(14)

        # Icon badge
        icon_badge = QFrame()
        icon_badge.setObjectName("statIconBadge")
        icon_badge.setFixedSize(44, 44)
        ib_l = QVBoxLayout(icon_badge)
        ib_l.setContentsMargins(0, 0, 0, 0)
        ib_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_banner_icon = QLabel()
        self.lbl_banner_icon.setPixmap(IconManager.get_icon("equipment.svg", "#38BDF8", 22).pixmap(22, 22))
        self.lbl_banner_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(self.lbl_banner_icon)
        banner_layout.addWidget(icon_badge)

        # Title & Subtitle column
        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 0, 0, 0)
        title_col.setSpacing(3)

        self.lbl_banner_title = QLabel()
        self.lbl_banner_title.setObjectName("detailTitleLabel")
        self.lbl_banner_title.setStyleSheet("font-size: 16px; font-weight: 700; background: transparent;")
        title_col.addWidget(self.lbl_banner_title)

        self.lbl_banner_subtitle = QLabel()
        self.lbl_banner_subtitle.setObjectName("kvKeyLabel")
        self.lbl_banner_subtitle.setStyleSheet("font-size: 11.5px; background: transparent;")
        title_col.addWidget(self.lbl_banner_subtitle)

        banner_layout.addLayout(title_col, 1)

        # Operational Status Pill
        op_box = QFrame()
        op_box.setObjectName("eqStatusBanner")
        op_l = QVBoxLayout(op_box)
        op_l.setContentsMargins(10, 5, 10, 5)
        op_l.setSpacing(1)
        lbl_op_cap = QLabel("ESTADO OPERATIVO")
        lbl_op_cap.setObjectName("kvKeyLabel")
        lbl_op_cap.setStyleSheet("font-size: 9px; letter-spacing: 0.5px; background: transparent;")
        self.lbl_banner_op_status = QLabel()
        self.lbl_banner_op_status.setStyleSheet("font-size: 12px; font-weight: 700; background: transparent;")
        op_l.addWidget(lbl_op_cap)
        op_l.addWidget(self.lbl_banner_op_status)
        banner_layout.addWidget(op_box)

        # BMS Status Pill
        bms_box = QFrame()
        bms_box.setObjectName("eqStatusBanner")
        bms_l = QVBoxLayout(bms_box)
        bms_l.setContentsMargins(10, 5, 10, 5)
        bms_l.setSpacing(1)
        lbl_bms_cap = QLabel("ESTADO BMS / CTRL")
        lbl_bms_cap.setObjectName("kvKeyLabel")
        lbl_bms_cap.setStyleSheet("font-size: 9px; letter-spacing: 0.5px; background: transparent;")
        self.lbl_banner_bms_status = QLabel()
        self.lbl_banner_bms_status.setStyleSheet("font-size: 12px; font-weight: 700; background: transparent;")
        bms_l.addWidget(lbl_bms_cap)
        bms_l.addWidget(self.lbl_banner_bms_status)
        banner_layout.addWidget(bms_box)

    def _refresh_header_banner(self):
        if not hasattr(self, 'lbl_banner_title'):
            return
        tag_txt = self.tag_edit.text().strip() if hasattr(self, 'tag_edit') else ""
        if not tag_txt:
            tag_txt = self.equipment.tag if self.equipment else "Nuevo Equipo HVAC"
        sys_txt = self.tipo_combo.currentText() if hasattr(self, 'tipo_combo') else "Sistema HVAC"
        bms_id_txt = self.bms_id_edit.text().strip() if hasattr(self, 'bms_id_edit') else ""
        piso_txt = self.piso_edit.text().strip() if hasattr(self, 'piso_edit') else ""

        self.lbl_banner_title.setText(f"{tag_txt}  —  {sys_txt}")

        # Dynamic Equipment System Type Icon
        sys_code = self.tipo_combo.currentData() if hasattr(self, 'tipo_combo') else (
            self.equipment.system_type.value if (self.equipment and hasattr(self.equipment.system_type, 'value'))
            else (str(self.equipment.system_type) if self.equipment else "AHU")
        )
        sys_icon_name = f"equipment/{str(sys_code or 'ahu').lower()}.svg"
        if hasattr(self, 'lbl_banner_icon'):
            pix = IconManager.get_pixmap(sys_icon_name, "#38BDF8", 24)
            if pix.isNull():
                pix = IconManager.get_pixmap("equipment.svg", "#38BDF8", 24)
            self.lbl_banner_icon.setPixmap(pix)
        self.setWindowIcon(IconManager.get_equipment_icon(str(sys_code or "AHU"), "#38BDF8"))

        sub_parts = []
        if hasattr(self, 'cliente_combo') and self.cliente_combo.currentText():
            sub_parts.append(f"Cliente: {self.cliente_combo.currentText()}")
        if hasattr(self, 'sitio_combo') and self.sitio_combo.currentText():
            sub_parts.append(f"Instalación: {self.sitio_combo.currentText()}")
        if piso_txt:
            sub_parts.append(f"Área: {piso_txt}")
        if bms_id_txt:
            sub_parts.append(f"ID BMS: #{bms_id_txt}")
        self.lbl_banner_subtitle.setText("   •   ".join(sub_parts) if sub_parts else "Ficha Técnica y Configuración del Equipo")

        # Operational status color
        op_code = self.estado_combo.currentData() if hasattr(self, 'estado_combo') else "OPERATIONAL"
        op_label = self.estado_combo.currentText() if hasattr(self, 'estado_combo') else "Operativo"
        op_colors = {
            "OPERATIONAL": "#10B981",
            "WARNING": "#F59E0B",
            "CRITICAL": "#EF4444",
            "MAINTENANCE": "#38BDF8",
            "OUT_OF_SERVICE": "#EF4444",
            "INACTIVE": "#94A3B8",
        }
        op_col = op_colors.get(str(op_code), "#10B981")
        self.lbl_banner_op_status.setText(f"●  {op_label}")
        self.lbl_banner_op_status.setStyleSheet(f"color: {op_col}; font-size: 12px; font-weight: 700; background: transparent;")

        # BMS status color
        bms_label = self.estado_bms_combo.currentText() if hasattr(self, 'estado_bms_combo') else "Operativo"
        bms_low = bms_label.lower()
        if "falla" in bms_low or "fuera" in bms_low or "alarma" in bms_low:
            bms_col = "#EF4444"
        elif "sin " in bms_low or "manual" in bms_low or "inexistente" in bms_low:
            bms_col = "#F59E0B"
        else:
            bms_col = "#10B981"
        self.lbl_banner_bms_status.setText(f"●  {bms_label}")
        self.lbl_banner_bms_status.setStyleSheet(f"color: {bms_col}; font-size: 12px; font-weight: 700; background: transparent;")

    def set_read_only(self, read_only: bool):
        self.is_read_only = read_only
        
        # Update Window Title
        if self.equipment:
            if read_only:
                self.setWindowTitle(f"Detalle del Equipo - {self.equipment.tag}")
                if hasattr(self, 'lbl_mode_badge'):
                    self.lbl_mode_badge.setText("●  MODO LECTURA / CONSULTA")
                    self.lbl_mode_badge.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; background: transparent;")
            else:
                self.setWindowTitle(f"Editar Equipo - {self.equipment.tag}")
                if hasattr(self, 'lbl_mode_badge'):
                    self.lbl_mode_badge.setText("●  MODO EDICIÓN ACTIVO")
                    self.lbl_mode_badge.setStyleSheet("color: #F59E0B; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; background: transparent;")
        else:
            self.setWindowTitle("Nuevo Equipo")
            if hasattr(self, 'lbl_mode_badge'):
                self.lbl_mode_badge.setText("●  REGISTRO DE NUEVO EQUIPO")
                self.lbl_mode_badge.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; background: transparent;")

        # Toggle Button Visibility
        self.btn_close.setVisible(read_only)
        self.btn_edit_mode.setVisible(read_only)
        self.btn_cancel.setVisible(not read_only)
        self.btn_save.setVisible(not read_only)

        # Toggle Form Fields
        enabled = not read_only
        if hasattr(self, 'cliente_combo'):
            self.cliente_combo.setEnabled(enabled)
        if hasattr(self, 'sitio_combo'):
            self.sitio_combo.setEnabled(enabled)
            
        self.tag_edit.setReadOnly(read_only)
        self.bms_id_edit.setReadOnly(read_only)
        self.piso_edit.setReadOnly(read_only)
        self.tipo_combo.setEnabled(enabled)
        self.fabricante_edit.setReadOnly(read_only)
        self.modelo_edit.setReadOnly(read_only)
        self.serie_edit.setReadOnly(read_only)
        self.fecha_inst.setEnabled(enabled)
        self.garantia.setEnabled(enabled)
        self.ubicacion_edit.setReadOnly(read_only)
        self.estado_combo.setEnabled(enabled)
        self.estado_bms_combo.setEnabled(enabled)
        self.frecuencia_combo.setEnabled(enabled)
        
        self.repuestos_edit.setReadOnly(read_only)
        if hasattr(self, 'repuestos_list'):
            self.repuestos_list.setEnabled(enabled)
            
        self.notas_edit.setReadOnly(read_only)

        # Dynamic Technical Specifications Fields
        for widget in self.tech_fields.values():
            if isinstance(widget, (QLineEdit, QTextEdit)):
                widget.setReadOnly(read_only)
            else:
                widget.setEnabled(enabled)

    def _on_cancel_clicked(self):
        if self.equipment:
            self._load_data()
            self.set_read_only(True)
        else:
            self.reject()

    def _setup_general_section(self):
        card, body = _create_dialog_card("Información General", "#38BDF8")
        fl = QFormLayout(body)
        fl.setSpacing(10)
        fl.setContentsMargins(16, 14, 16, 16)
        fl.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        if self.client_service:
            self.cliente_combo = QComboBox()
            self.sitio_combo = QComboBox()
            self._populate_clients()
            self.cliente_combo.currentIndexChanged.connect(self._on_client_combo_changed)
            fl.addRow("Cliente *:", self.cliente_combo)
            fl.addRow("Instalación *:", self.sitio_combo)

        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText("Ej: UMA-01, FCU-101, CH-01")
        
        self.bms_id_edit = QLineEdit()
        self.bms_id_edit.setPlaceholderText("Ej: 1, 2, BMS-01, AHU-P1-01 (Orden en BMS)")
        
        self.piso_edit = QLineEdit()
        self.piso_edit.setPlaceholderText("Ej: Piso 1, Nivel -1, Azotea, Sala Técnica")
        if self.floor_area:
            self.piso_edit.setText(self.floor_area)
        
        self.tipo_combo = QComboBox()
        for sys_type, label in SYSTEM_TYPE_LABELS.items():
            self.tipo_combo.addItem(label, sys_type.value)
        self.tipo_combo.currentIndexChanged.connect(
            lambda idx: self._on_type_changed(self.tipo_combo.itemData(idx))
        )
        
        self.fabricante_edit = QLineEdit()
        self.modelo_edit = QLineEdit()
        self.serie_edit = QLineEdit()
        
        self.fecha_inst = QDateEdit()
        self.fecha_inst.setCalendarPopup(True)
        self.fecha_inst.setDate(QDate.currentDate())
        
        self.garantia = QDateEdit()
        self.garantia.setCalendarPopup(True)
        self.garantia.setDate(QDate.currentDate().addYears(1))
        
        self.ubicacion_edit = QLineEdit()
        self.ubicacion_edit.setPlaceholderText("Detalle específico de ubicación (Ej: Pasillo norte, Sala 102)")
        
        self.estado_combo = QComboBox()
        for status, label in OPERATIONAL_STATUS_LABELS.items():
            self.estado_combo.addItem(label, status.value)
            
        self.estado_bms_combo = QComboBox()
        if self.custom_lists_service:
            bms_options = self.custom_lists_service.get_list("bms_status")
        else:
            bms_options = DEFAULT_CUSTOM_LISTS.get("bms_status", ["Operativo", "En Falla", "Sin Grafica", "Sin Control", "Fuera de Servicio", "Inexistente"])
        for opt in bms_options:
            self.estado_bms_combo.addItem(opt, opt)

        self.frecuencia_combo = QComboBox()
        for freq, label in MAINTENANCE_FREQUENCY_LABELS.items():
            self.frecuencia_combo.addItem(label, freq.value)
        default_freq_idx = self.frecuencia_combo.findData("MONTHLY")
        if default_freq_idx >= 0:
            self.frecuencia_combo.setCurrentIndex(default_freq_idx)

        fl.addRow("Tag *:", self.tag_edit)
        fl.addRow("ID / Orden BMS:", self.bms_id_edit)
        fl.addRow("Estado BMS/Ctrl:", self.estado_bms_combo)
        fl.addRow("Piso / Nivel / Área:", self.piso_edit)
        fl.addRow("Tipo de Sistema:", self.tipo_combo)
        fl.addRow("Fabricante:", self.fabricante_edit)
        fl.addRow("Modelo:", self.modelo_edit)
        fl.addRow("Nro. Serie:", self.serie_edit)
        fl.addRow("Fecha Instalación:", self.fecha_inst)
        fl.addRow("Garantía Hasta:", self.garantia)
        fl.addRow("Ubicación Específica:", self.ubicacion_edit)
        fl.addRow("Estado Operativo:", self.estado_combo)
        fl.addRow("Frecuencia Mant.:", self.frecuencia_combo)
        
        self.layout.addWidget(card)

    def _populate_clients(self):
        self.cliente_combo.clear()
        clients = self.client_service.get_all_clients()
        for c in clients:
            cname = getattr(c, 'company_name', '') or getattr(c, 'name', '')
            self.cliente_combo.addItem(cname, c.id)
        if self.client_id:
            idx = self.cliente_combo.findData(self.client_id)
            if idx >= 0:
                self.cliente_combo.setCurrentIndex(idx)
        self._on_client_combo_changed()

    def _on_client_combo_changed(self):
        self.sitio_combo.clear()
        cid = self.cliente_combo.currentData()
        if cid:
            sites = self.client_service.get_sites_for_client(cid)
            for s in sites:
                self.sitio_combo.addItem(s.name, s.id)
            if self.site_id:
                idx = self.sitio_combo.findData(self.site_id)
                if idx >= 0:
                    self.sitio_combo.setCurrentIndex(idx)
        if hasattr(self, '_refresh_header_banner'):
            self._refresh_header_banner()

    def _setup_tech_specs_section(self):
        card, self.tech_gb = _create_dialog_card("Especificaciones Técnicas", "#F59E0B")
        self.tech_gb_layout = QVBoxLayout(self.tech_gb)
        self.tech_gb_layout.setContentsMargins(16, 14, 16, 16)
        self.tech_gb_layout.setSpacing(0)
        
        self.tech_container = None
        self.layout.addWidget(card)

    def _setup_spare_parts_section(self):
        card, body = _create_dialog_card("Repuestos Asociados / Compatibles", "#14B8A6")
        fl = QFormLayout(body)
        fl.setSpacing(10)
        fl.setContentsMargins(16, 14, 16, 16)
        
        self.repuestos_edit = QLineEdit()
        self.repuestos_edit.setPlaceholderText("Ej: Correa A75, Filtro 24x24x2, Rodamiento SKF 6205")
        fl.addRow("Repuestos (separados por coma):", self.repuestos_edit)
        
        if self.inventory_service:
            lbl_inv = QLabel("O seleccione repuestos del Inventario:")
            lbl_inv.setObjectName("kvKeyLabel")
            fl.addRow(lbl_inv)
            
            self.repuestos_list = QListWidget()
            self.repuestos_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            self.repuestos_list.setMaximumHeight(110)
            
            try:
                parts = self.inventory_service.get_all_spare_parts()
                for p in parts:
                    unit_str = getattr(p, 'unit', 'unid')
                    item_text = f"{p.name} [{p.part_number or 'Sin cód.'}] (Stock: {p.quantity} {unit_str})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.ItemDataRole.UserRole, p.name)
                    self.repuestos_list.addItem(item)
            except Exception:
                pass
                
            fl.addRow(self.repuestos_list)

        # Installed Parts History (from parts_history.json)
        if self.equipment and self.equipment_service:
            history = self.equipment_service.get_parts_history(self.equipment.id)
            if history:
                lbl_hist = QLabel("Historial de Repuestos Instalados / Utilizados en este Equipo:")
                lbl_hist.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 11px; margin-top: 6px; background: transparent;")
                fl.addRow(lbl_hist)

                self.history_list = QListWidget()
                self.history_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
                self.history_list.setMaximumHeight(130)
                
                for ph in history:
                    dt_str = ph.get('date', '')[:10]
                    p_name = ph.get('part_name', 'Repuesto')
                    p_num = f" [{ph.get('part_number')}]" if ph.get('part_number') else ""
                    qty = ph.get('quantity', 1)
                    unit = ph.get('unit', 'unid')
                    reason = ph.get('reason', 'Asignación')
                    by_u = ph.get('performed_by', '')
                    ref = ph.get('reference', '')
                    notes = ph.get('notes', '')
                    
                    sub = []
                    if ref: sub.append(f"Ref: {ref}")
                    if by_u: sub.append(f"Por: {by_u}")
                    if notes: sub.append(f"Nota: {notes}")
                    
                    text = f"• [{dt_str}] {qty} {unit} - {p_name}{p_num} ({reason})\n    {' | '.join(sub) if sub else 'Sin notas'}"
                    self.history_list.addItem(QListWidgetItem(text))
                    
                fl.addRow(self.history_list)
            
        self.layout.addWidget(card)

    def _setup_service_history_section(self):
        if not self.equipment or not self.equipment_service:
            return

        service_history = self.equipment_service.get_service_history(self.equipment.id)
        if not service_history:
            return

        card, body = _create_dialog_card("Historial de Servicios Técnicos y Mantenimiento", "#8B5CF6")
        fl = QFormLayout(body)
        fl.setSpacing(8)
        fl.setContentsMargins(16, 14, 16, 16)

        lbl_info = QLabel(f"Guías y Órdenes asociadas a este equipo ({len(service_history)} registros):")
        lbl_info.setStyleSheet("color: #8B5CF6; font-weight: bold; font-size: 11px; background: transparent;")
        fl.addRow(lbl_info)

        self.service_history_list = QListWidget()
        self.service_history_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.service_history_list.setMaximumHeight(150)

        for s_entry in service_history:
            dt = s_entry.get('date') or s_entry.get('scheduled_date', '')
            dt_str = dt[:10] if dt else "Sin fecha"
            wo_id = s_entry.get('id') or s_entry.get('work_order_id', '')
            stype = s_entry.get('service_type') or "Servicio / Mantenimiento"
            title = s_entry.get('title', '')
            status = s_entry.get('status', '')
            tech = s_entry.get('technician', '')
            
            sub_parts = []
            if status: sub_parts.append(f"Estado: {status}")
            if tech: sub_parts.append(f"Técnico: {tech}")
            
            # Materials used summary
            mats = s_entry.get('materials_used', [])
            if mats:
                mat_str = ", ".join([
                    f"{m.get('quantity', 1)} {m.get('unit', 'unid')} {m.get('name') or m.get('part_name', 'Repuesto')}"
                    if isinstance(m, dict) else str(m)
                    for m in mats
                ])
                sub_parts.append(f"Materiales: {mat_str}")
                
            text = f"• [{dt_str}] {wo_id} - {title} ({stype})\n    {' | '.join(sub_parts) if sub_parts else ''}"
            self.service_history_list.addItem(QListWidgetItem(text))

        fl.addRow(self.service_history_list)
        self.layout.addWidget(card)

    def _setup_other_section(self):
        card, body = _create_dialog_card("Notas / Observaciones", "#10B981")
        fl = QFormLayout(body)
        fl.setSpacing(10)
        fl.setContentsMargins(16, 14, 16, 16)
        
        self.notas_edit = QTextEdit()
        self.notas_edit.setMaximumHeight(85)
        fl.addRow("Notas:", self.notas_edit)
        
        self.layout.addWidget(card)

    def _on_type_changed(self, system_type):
        if hasattr(system_type, 'value'):
            system_type = system_type.value
        system_type_str = str(system_type) if system_type else "AHU"

        # Explicitly hide, remove and delete previous container and all its child widgets
        if self.tech_container is not None:
            self.tech_gb_layout.removeWidget(self.tech_container)
            self.tech_container.hide()
            self.tech_container.setParent(None)
            self.tech_container.deleteLater()
            self.tech_container = None
            
        self.tech_fields.clear()

        # Create fresh container with clean QFormLayout
        self.tech_container = QWidget(self.tech_gb)
        tech_fl = QFormLayout(self.tech_container)
        tech_fl.setContentsMargins(0, 0, 0, 0)
        tech_fl.setSpacing(10)
        
        # Build map of fields that have custom dropdowns
        dropdown_map = {
            field_name: list_key 
            for list_key, _, field_name in EQUIPMENT_DROPDOWN_MAP.get(system_type_str, [])
        }

        specs = TECHNICAL_SPEC_FIELDS.get(system_type_str, [])
        spec_field_names = {f[0] for f in specs}

        inline_unit_pairs = {
            "refrigerant_charge": ("refrigerant_unit", "refrigerant_unit", ["Kg", "g"], "Cantidad de Gas Refrigerante:"),
            "cooling_capacity_tons": ("cooling_capacity_unit", "rooftop_capacity_unit", ["Ton", "BTU/h", "HP", "kW"], "Capacidad Frío:"),
            "cooling_capacity_kw": ("cooling_capacity_unit", "rooftop_capacity_unit", ["kW", "BTU/h", "Ton", "HP"], "Capacidad / Potencia Frío:"),
            "cooling_capacity_btu": ("cooling_capacity_unit", "rooftop_capacity_unit", ["BTU/h", "Ton", "kW", "HP"], "Capacidad Frío:"),
            "heating_capacity_kw": ("heating_capacity_unit", "rooftop_capacity_unit", ["kW", "BTU/h", "Ton", "HP"], "Capacidad Calor:"),
            "heating_power_kw": ("heating_power_unit", "fan_power_unit", ["kW", "W", "BTU/h", "kcal/h"], "Potencia Eléctrica:"),
            "airflow_cfm": ("airflow_unit", "fan_airflow_unit", ["CFM", "m3/h", "L/s", "m3/s"], "Caudal:"),
            "min_cfm": ("min_cfm_unit", "fan_airflow_unit", ["CFM", "m3/h", "L/s", "m3/s"], "Caudal Mínimo:"),
            "max_cfm": ("max_cfm_unit", "fan_airflow_unit", ["CFM", "m3/h", "L/s", "m3/s"], "Caudal Máximo:"),
            "static_pressure_pa": ("static_pressure_unit", "fan_pressure_unit", ["Pa", "PSI", "Bar", "mmca", "inWG"], "Presión Estática:"),
            "motor_power_kw": ("motor_power_unit", "fan_power_unit", ["kW", "W", "HP", "CV"], "Potencia Motor:"),
            "water_flow_gpm": ("water_flow_unit", "water_flow_unit", ["GPM", "m3/h", "L/s", "L/min"], "Caudal de Agua Condensador:"),
            "flow_rate_m3h": ("flow_rate_unit", "water_flow_unit", ["m3/h", "GPM", "L/s", "L/min"], "Caudal:"),
            "ewt_design": ("ewt_unit", "temperature_unit", ["°C", "°F", "K"], "EWT Diseño:"),
            "lwt_design": ("lwt_unit", "temperature_unit", ["°C", "°F", "K"], "LWT Diseño:"),
            "design_range_c": ("design_range_unit", "temperature_unit", ["°C", "°F", "K"], "Rango Diseño:"),
            "design_approach_c": ("design_approach_unit", "temperature_unit", ["°C", "°F", "K"], "Approach Diseño:"),
            "head_m": ("head_unit", "head_unit", ["m", "mca", "ft", "PSI", "Bar"], "Carga / Altura Manométrica:"),
            "impeller_diameter_mm": ("impeller_diameter_unit", "length_mm_unit", ["mm", "cm", "in"], "Diámetro Impulsor:"),
            "volume_liters": ("volume_unit", "volume_unit", ["L", "m3", "Gal"], "Volumen:"),
            "max_pressure_bar": ("max_pressure_unit", "fan_pressure_unit", ["Bar", "PSI", "Pa", "mmca"], "Presión Máxima:"),
            "pre_charge_pressure_bar": ("pre_charge_pressure_unit", "fan_pressure_unit", ["Bar", "PSI", "Pa", "mmca"], "Presión Precarga:"),
            "capacity_m3": ("capacity_unit", "volume_unit", ["m3", "L", "Gal"], "Capacidad:"),
            "total_capacity_kw": ("total_capacity_unit", "rooftop_capacity_unit", ["kW", "BTU/h", "Ton", "HP"], "Capacidad Total:"),
            "pipe_length_m": ("pipe_length_unit", "length_m_unit", ["m", "ft"], "Longitud Tubería:"),
            "max_capacity_kw": ("max_capacity_unit", "rooftop_capacity_unit", ["kW", "BTU/h", "Ton", "HP"], "Capacidad Máxima:"),
            "voltage": ("voltage_unit", "electric_voltage_unit", ["V", "VAC", "VDC", "kV"], "Voltaje:"),
            "amperage": ("amperage_unit", "electric_current_unit", ["A", "mA"], "Amperaje:"),
            "nominal_current_a": ("nominal_current_unit", "electric_current_unit", ["A", "mA"], "Corriente Nominal Salida:"),
        }
        handled_unit_fields = {
            u_field for v_field, (u_field, _, _, _) in inline_unit_pairs.items()
            if v_field in spec_field_names and u_field in spec_field_names
        }
        spec_defaults = {f[0]: f[4] for f in specs}

        for field_name, label, dtype, unit, default in specs:
            if field_name in handled_unit_fields:
                # Handled inline with its paired value field
                continue

            if field_name in inline_unit_pairs and inline_unit_pairs[field_name][0] in spec_field_names:
                unit_field_name, unit_list_key, fallback_units, default_row_label = inline_unit_pairs[field_name]
                row_label = f"{label}:" if label and field_name != "refrigerant_charge" else default_row_label
                row_w = QWidget()
                row_l = QHBoxLayout(row_w)
                row_l.setContentsMargins(0, 0, 0, 0)
                row_l.setSpacing(8)

                spin = QDoubleSpinBox()
                spin.setRange(0, 1000000)
                spin.setDecimals(2)
                spin.setValue(float(default) if default else 0.0)

                unit_cb = QComboBox()
                if self.custom_lists_service:
                    u_opts = self.custom_lists_service.get_list(unit_list_key) or fallback_units
                else:
                    u_opts = DEFAULT_CUSTOM_LISTS.get(unit_list_key, fallback_units)
                for u_opt in u_opts:
                    unit_cb.addItem(u_opt, u_opt)
                default_unit_val = spec_defaults.get(unit_field_name, "")
                if default_unit_val:
                    u_idx = unit_cb.findText(str(default_unit_val), Qt.MatchFlag.MatchFixedString)
                    if u_idx >= 0:
                        unit_cb.setCurrentIndex(u_idx)
                unit_cb.setFixedWidth(100)

                row_l.addWidget(spin, 1)
                row_l.addWidget(unit_cb)

                tech_fl.addRow(row_label, row_w)
                self.tech_fields[field_name] = spin
                self.tech_fields[unit_field_name] = unit_cb
                continue

            display_label = f"{label} ({unit}):" if (unit and f"({unit})" not in label) else f"{label}:"
            
            if field_name in dropdown_map:
                list_key = dropdown_map[field_name]
                w = QComboBox()
                w.addItem("(Seleccionar opción)", "")
                
                if self.custom_lists_service:
                    options = self.custom_lists_service.get_list(list_key)
                else:
                    options = DEFAULT_CUSTOM_LISTS.get(list_key, [])
                    
                for opt in options:
                    w.addItem(opt, opt)

                if default and isinstance(default, str):
                    idx = w.findText(default)
                    if idx >= 0:
                        w.setCurrentIndex(idx)

            elif dtype == "float":
                w = QDoubleSpinBox()
                w.setRange(0, 1000000)
                w.setDecimals(2)
                w.setValue(float(default) if default else 0.0)
            elif dtype == "int":
                w = QSpinBox()
                w.setRange(0, 1000000)
                w.setValue(int(default) if default else 0)
            elif dtype == "bool":
                w = QCheckBox()
                w.setChecked(bool(default) if default else False)
            else:
                w = QLineEdit()
                w.setText(str(default) if default else "")
                
            tech_fl.addRow(display_label, w)
            self.tech_fields[field_name] = w

        if hasattr(self, 'is_read_only'):
            for widget in self.tech_fields.values():
                if isinstance(widget, (QLineEdit, QTextEdit)):
                    widget.setReadOnly(self.is_read_only)
                else:
                    widget.setEnabled(not self.is_read_only)

        self.tech_gb_layout.addWidget(self.tech_container)
        if hasattr(self, '_refresh_header_banner'):
            self._refresh_header_banner()

    def _load_data(self):
        if hasattr(self, 'cliente_combo') and self.equipment.client_id:
            self.cliente_combo.blockSignals(True)
            idx = self.cliente_combo.findData(self.equipment.client_id)
            if idx >= 0:
                self.cliente_combo.setCurrentIndex(idx)
            self.cliente_combo.blockSignals(False)
            
            if hasattr(self, 'sitio_combo') and self.equipment.site_id:
                self.sitio_combo.blockSignals(True)
                self._on_client_combo_changed()
                s_idx = self.sitio_combo.findData(self.equipment.site_id)
                if s_idx >= 0:
                    self.sitio_combo.setCurrentIndex(s_idx)
                self.sitio_combo.blockSignals(False)

        self.tag_edit.setText(self.equipment.tag)
        self.bms_id_edit.setText(getattr(self.equipment, 'bms_id', '') or "")
        self.piso_edit.setText(getattr(self.equipment, 'floor_area', '') or "")
        
        # Block signals on tipo_combo so setting index doesn't trigger _on_type_changed multiple times
        self.tipo_combo.blockSignals(True)
        sys_type = self.equipment.system_type.value if hasattr(self.equipment.system_type, 'value') else str(self.equipment.system_type)
        idx = self.tipo_combo.findData(sys_type)
        if idx >= 0:
            self.tipo_combo.setCurrentIndex(idx)
        self.tipo_combo.blockSignals(False)

        # Build dynamic tech fields once for the loaded equipment
        self._on_type_changed(sys_type)
            
        self.fabricante_edit.setText(self.equipment.manufacturer)
        self.modelo_edit.setText(self.equipment.model_number)
        self.serie_edit.setText(self.equipment.serial_number)
        
        if self.equipment.installation_date:
            try: self.fecha_inst.setDate(QDate.fromString(self.equipment.installation_date[:10], Qt.DateFormat.ISODate))
            except: pass
        if self.equipment.warranty_expiry:
            try: self.garantia.setDate(QDate.fromString(self.equipment.warranty_expiry[:10], Qt.DateFormat.ISODate))
            except: pass
            
        self.ubicacion_edit.setText(self.equipment.location_description)
        
        idx = self.estado_combo.findData(self.equipment.status)
        if idx >= 0: self.estado_combo.setCurrentIndex(idx)
        
        bms_st = getattr(self.equipment, 'bms_status', 'Operativo') or 'Operativo'
        idx_bms = self.estado_bms_combo.findText(bms_st)
        if idx_bms >= 0:
            self.estado_bms_combo.setCurrentIndex(idx_bms)
        else:
            self.estado_bms_combo.addItem(bms_st, bms_st)
            self.estado_bms_combo.setCurrentIndex(self.estado_bms_combo.count() - 1)

        idx = self.frecuencia_combo.findData(self.equipment.maintenance_frequency)
        if idx >= 0: self.frecuencia_combo.setCurrentIndex(idx)
        
        self.notas_edit.setPlainText(self.equipment.notes)
        
        # Load tech specs values into the created widgets
        for field_name, widget in self.tech_fields.items():
            if field_name in self.equipment.technical_specs:
                val = self.equipment.technical_specs[field_name]
                if isinstance(widget, QComboBox):
                    str_val = str(val).strip()
                    if str_val:
                        idx = widget.findText(str_val)
                        if idx >= 0:
                            widget.setCurrentIndex(idx)
                        else:
                            widget.addItem(str_val, str_val)
                            widget.setCurrentIndex(widget.count() - 1)
                elif isinstance(widget, QDoubleSpinBox) or isinstance(widget, QSpinBox):
                    try:
                        widget.setValue(float(val) if isinstance(widget, QDoubleSpinBox) else int(val))
                    except (ValueError, TypeError):
                        pass
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(val))
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(val))

        # Load spare parts
        sp_list = getattr(self.equipment, 'spare_parts', []) or []
        sp_strs = []
        for sp in sp_list:
            if isinstance(sp, dict):
                sp_strs.append(sp.get('name', ''))
            else:
                sp_strs.append(str(sp))
        
        self.repuestos_edit.setText(", ".join([s for s in sp_strs if s]))
        
        if hasattr(self, 'repuestos_list'):
            for idx in range(self.repuestos_list.count()):
                item = self.repuestos_list.item(idx)
                pname = item.data(Qt.ItemDataRole.UserRole)
                if pname in sp_strs:
                    item.setSelected(True)

    def validate_and_accept(self):
        if not self.tag_edit.text().strip():
            QMessageBox.warning(self, "Error", "El campo Tag es obligatorio.")
            return
            
        if hasattr(self, 'sitio_combo') and self.sitio_combo.count() > 0:
            self.site_id = self.sitio_combo.currentData() or ""
            self.client_id = self.cliente_combo.currentData() or ""
            
        if not self.site_id:
            QMessageBox.warning(self, "Error", "Debe seleccionar un Cliente e Instalación para el equipo.")
            return
            
        self.accept()

    def get_equipment(self) -> HVACEquipment:
        tech_specs = {}
        for field_name, widget in self.tech_fields.items():
            if isinstance(widget, QComboBox):
                text_val = widget.currentText().strip()
                data_val = widget.currentData()
                if data_val == "" or text_val == "(Seleccionar opción)":
                    tech_specs[field_name] = ""
                else:
                    tech_specs[field_name] = text_val
            elif isinstance(widget, QDoubleSpinBox) or isinstance(widget, QSpinBox):
                tech_specs[field_name] = widget.value()
            elif isinstance(widget, QCheckBox):
                tech_specs[field_name] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                tech_specs[field_name] = widget.text().strip()

        selected_sp = []
        raw_text = self.repuestos_edit.text().strip()
        if raw_text:
            for s in raw_text.split(','):
                st = s.strip()
                if st and st not in selected_sp:
                    selected_sp.append(st)
                    
        if hasattr(self, 'repuestos_list'):
            for item in self.repuestos_list.selectedItems():
                pname = item.data(Qt.ItemDataRole.UserRole)
                if pname and pname not in selected_sp:
                    selected_sp.append(pname)

        eq_id = self.equipment.id if self.equipment else ""
        return HVACEquipment(
            id=eq_id,
            site_id=self.site_id,
            client_id=self.client_id,
            tag=self.tag_edit.text().strip(),
            bms_id=self.bms_id_edit.text().strip(),
            bms_status=self.estado_bms_combo.currentText().strip() or "Operativo",
            floor_area=self.piso_edit.text().strip(),
            system_type=self.tipo_combo.currentData(),
            manufacturer=self.fabricante_edit.text().strip(),
            model_number=self.modelo_edit.text().strip(),
            serial_number=self.serie_edit.text().strip(),
            installation_date=self.fecha_inst.date().toString(Qt.DateFormat.ISODate),
            warranty_expiry=self.garantia.date().toString(Qt.DateFormat.ISODate),
            location_description=self.ubicacion_edit.text().strip(),
            status=self.estado_combo.currentData(),
            maintenance_frequency=self.frecuencia_combo.currentData(),
            technical_specs=tech_specs,
            spare_parts=selected_sp,
            notes=self.notas_edit.toPlainText().strip()
        )
