"""
Diálogos de Pañol (PanolDialogs) para ControlHVAC CMMS:
1. PanolSupplyDialog: Crear / Editar insumo de Pañol (Detergente, paños de limpieza, terminales de manguera, etc.)
2. EppItemDialog: Crear / Editar EPP (Entrega o Por Asignación / Cargo)
3. PanolMovementDialog: Registrar Ingreso a Pañol (+) o Entrega / Asignación (-) a Técnico, Personal Externo o Recinto.
4. GasCylinderDialog: Crear / Editar cilindro/tubo de gas (Soldadura, Refrigerante, Recuperado, Agente de Limpieza).
5. GasMovementDialog: Registrar uso/carga de gas en equipo (-) o ingreso/recuperación de gas (+).
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QMessageBox,
    QComboBox, QSpinBox, QDoubleSpinBox, QLabel, QFrame,
    QScrollArea, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from src.core.models.inventory import PanolSupply, EppItem, GasCylinder
from src.ui.icon_manager import IconManager
from src.ui.dialogs.equipment_dialog import _create_dialog_card


class PanolSupplyDialog(QDialog):
    """Diálogo para registrar o editar un Insumo de Pañol (Detergente, paños, terminales, etc.)."""

    DEFAULT_CATEGORIES = [
        "Limpieza y Desengrase (Detergente, Desincrustante, Paños, Trapos)",
        "Conexiones y Mangueras (Terminales de manguera, abrazaderas, acoples)",
        "Sellantes y Cintas (Teflón, cinta aluminio, aislación Armaflex, silicona)",
        "Soldadura y Aporte (Varillas de plata, fundente, lija, gas MAPP)",
        "Eléctrico y Fijación (Terminales eléctricos, amarras plásticas, tornillería)",
        "Químicos y Lubricantes (Aceite vacío, limpia contactos, pintura anticorrosiva)",
        "Otro Insumo de Pañol"
    ]

    DEFAULT_UNITS = [
        "unidad", "litro", "bidón", "galón", "kg", "paquete",
        "rollo", "metro", "par", "caja", "bolsa", "kit"
    ]

    def __init__(self, parent=None, supply: PanolSupply = None, read_only: bool = None):
        super().__init__(parent)
        self.supply = supply
        self.is_read_only = (supply is not None) if read_only is None else read_only
        self.resize(650, 660)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # ── Top Header Banner ──
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
        lbl_icon.setPixmap(IconManager.get_icon("tools.svg", "#38BDF8", 22).pixmap(22, 22))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        hb_layout.addWidget(icon_badge)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        sname = self.supply.name if self.supply else "Nuevo Insumo de Pañol"
        self.lbl_header_title = QLabel(f"Insumo de Pañol  —  {sname}")
        self.lbl_header_title.setObjectName("detailTitleLabel")
        self.lbl_header_title.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")
        lbl_s = QLabel("Control de consumibles, materiales de limpieza, terminales y entregas de pañol")
        lbl_s.setObjectName("kvKeyLabel")
        title_col.addWidget(self.lbl_header_title)
        title_col.addWidget(lbl_s)
        hb_layout.addLayout(title_col, 1)

        self.lbl_stock_pill = QLabel("●  Disponible")
        hb_layout.addWidget(self.lbl_stock_pill)

        main_layout.addWidget(header_banner)

        # ── Scrollable Body ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_widget.setObjectName("scrollContent")
        scroll_layout = QVBoxLayout(content_widget)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(12)

        # Card 1: Identificación y Clasificación
        card_id, body_id = _create_dialog_card("1. Identificación y Clasificación del Insumo", "#38BDF8")
        form_id = QFormLayout(body_id)
        form_id.setContentsMargins(16, 14, 16, 14)
        form_id.setSpacing(10)
        form_id.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.nombre_edit = QLineEdit()
        self.nombre_edit.setPlaceholderText("Ej: Detergente alcalino serpentines, Paños de limpieza microfibra, Terminal manguera 1/2\"...")
        self.nombre_edit.textChanged.connect(self._update_header_pill)

        self.codigo_edit = QLineEdit()
        self.codigo_edit.setPlaceholderText("Ej: INS-001 (Opcional)")

        self.cat_combo = QComboBox()
        self.cat_combo.setEditable(True)
        self.cat_combo.addItems(self.DEFAULT_CATEGORIES)

        self.ubicacion_edit = QLineEdit("Pañol Central")
        self.proveedor_edit = QLineEdit()
        self.proveedor_edit.setPlaceholderText("Proveedor habitual o marca...")

        form_id.addRow("Nombre del Insumo *:", self.nombre_edit)
        form_id.addRow("Código / Referencia:", self.codigo_edit)
        form_id.addRow("Categoría:", self.cat_combo)
        form_id.addRow("Ubicación en Pañol:", self.ubicacion_edit)
        form_id.addRow("Proveedor / Marca:", self.proveedor_edit)
        scroll_layout.addWidget(card_id)

        # Card 2: Stock, Costo y Observaciones
        card_st, body_st = _create_dialog_card("2. Control de Existencias, Costo y Observaciones", "#10B981")
        form_st = QFormLayout(body_st)
        form_st.setContentsMargins(16, 14, 16, 14)
        form_st.setSpacing(10)
        form_st.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.unidad_combo = QComboBox()
        self.unidad_combo.setEditable(True)
        self.unidad_combo.addItems(self.DEFAULT_UNITS)
        self.unidad_combo.currentTextChanged.connect(self._update_header_pill)

        self.cant_spin = QSpinBox()
        self.cant_spin.setRange(0, 999999)
        self.cant_spin.setValue(1)
        self.cant_spin.valueChanged.connect(self._update_header_pill)

        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 999999)
        self.min_spin.setValue(2)
        self.min_spin.valueChanged.connect(self._update_header_pill)

        self.costo_spin = QDoubleSpinBox()
        self.costo_spin.setRange(0, 100000000)
        self.costo_spin.setDecimals(0)
        self.costo_spin.setPrefix("$ ")

        self.notas_edit = QTextEdit()
        self.notas_edit.setMaximumHeight(68)
        self.notas_edit.setPlaceholderText("Notas adicionales, especificaciones o instrucciones de entrega...")

        form_st.addRow("Unidad de Medida:", self.unidad_combo)
        form_st.addRow("Stock en Pañol:", self.cant_spin)
        form_st.addRow("Stock Mínimo (Alerta):", self.min_spin)
        form_st.addRow("Costo Unitario Ref.:", self.costo_spin)
        form_st.addRow("Notas / Observaciones:", self.notas_edit)
        scroll_layout.addWidget(card_st)
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

        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.clicked.connect(self.reject)

        self.btn_edit_mode = QPushButton("Editar")
        self.btn_edit_mode.setObjectName("primaryButton")
        self.btn_edit_mode.setIcon(IconManager.get_icon("edit.svg", "#000000", 16))
        self.btn_edit_mode.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit_mode.clicked.connect(lambda: self.set_read_only(False))

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.clicked.connect(self._on_cancel)

        self.btn_save = QPushButton("Guardar Insumo")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setIcon(IconManager.get_icon("check.svg", "#000000", 16))
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self._on_save)

        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_edit_mode)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        main_layout.addWidget(footer_bar)

        if self.supply:
            self._load_data()
        self._update_header_pill()
        self.set_read_only(self.is_read_only)

    def _update_header_pill(self):
        name = self.nombre_edit.text().strip() or (self.supply.name if self.supply else "Nuevo Insumo")
        self.lbl_header_title.setText(f"Insumo de Pañol  —  {name}")
        qty = self.cant_spin.value()
        min_q = self.min_spin.value()
        unit = self.unidad_combo.currentText().strip() or "unid."
        if qty <= 0:
            fg, bg, txt = "#EF4444", "#450A0A", f"●  Agotado (0 {unit})"
        elif qty <= min_q:
            fg, bg, txt = "#F59E0B", "#451A03", f"●  Stock Bajo ({qty} {unit})"
        else:
            fg, bg, txt = "#10B981", "#064E3B", f"●  Stock: {qty} {unit}"
        self.lbl_stock_pill.setText(txt)
        self.lbl_stock_pill.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border: 1px solid {fg}; "
            f"border-radius: 5px; padding: 4px 10px; font-weight: bold; font-size: 11px;"
        )

    def set_read_only(self, ro: bool):
        self.is_read_only = ro
        if self.supply:
            self.setWindowTitle(f"{'Ficha de Insumo' if ro else 'Editar Insumo'} - {self.supply.name}")
            self.lbl_mode.setText("● MODO LECTURA / CONSULTA" if ro else "● MODO EDICIÓN ACTIVO")
            self.lbl_mode.setStyleSheet(
                "color: #94A3B8; font-weight: bold; font-size: 11px;" if ro
                else "color: #F59E0B; font-weight: bold; font-size: 11px;"
            )
        else:
            self.setWindowTitle("Registrar Nuevo Insumo en Pañol")
            self.lbl_mode.setText("● NUEVO REGISTRO EN PAÑOL")
            self.lbl_mode.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px;")

        self.btn_close.setVisible(ro)
        self.btn_edit_mode.setVisible(ro)
        self.btn_cancel.setVisible(not ro)
        self.btn_save.setVisible(not ro)

        enabled = not ro
        self.nombre_edit.setReadOnly(ro)
        self.codigo_edit.setReadOnly(ro)
        self.cat_combo.setEnabled(enabled)
        self.unidad_combo.setEnabled(enabled)
        self.cant_spin.setEnabled(enabled)
        self.min_spin.setEnabled(enabled)
        self.ubicacion_edit.setReadOnly(ro)
        self.proveedor_edit.setReadOnly(ro)
        self.costo_spin.setEnabled(enabled)
        self.notas_edit.setReadOnly(ro)

    def _load_data(self):
        self.nombre_edit.setText(self.supply.name)
        self.codigo_edit.setText(self.supply.code)
        self.cat_combo.setCurrentText(self.supply.category)
        self.unidad_combo.setCurrentText(self.supply.unit)
        self.cant_spin.setValue(self.supply.quantity)
        self.min_spin.setValue(self.supply.minimum_quantity)
        self.ubicacion_edit.setText(self.supply.location)
        self.proveedor_edit.setText(self.supply.supplier)
        self.costo_spin.setValue(self.supply.unit_cost)
        self.notas_edit.setPlainText(self.supply.notes)

    def _on_cancel(self):
        if self.supply:
            self._load_data()
            self.set_read_only(True)
        else:
            self.reject()

    def _on_save(self):
        if not self.nombre_edit.text().strip():
            QMessageBox.warning(self, "Campo Requerido", "El nombre del insumo es obligatorio.")
            return
        self.accept()

    def get_supply(self) -> PanolSupply:
        s_id = self.supply.id if self.supply else ""
        return PanolSupply(
            id=s_id,
            name=self.nombre_edit.text().strip(),
            code=self.codigo_edit.text().strip(),
            category=self.cat_combo.currentText().strip() or "General",
            unit=self.unidad_combo.currentText().strip() or "unidad",
            quantity=self.cant_spin.value(),
            minimum_quantity=self.min_spin.value(),
            location=self.ubicacion_edit.text().strip() or "Pañol",
            supplier=self.proveedor_edit.text().strip(),
            unit_cost=self.costo_spin.value(),
            notes=self.notas_edit.toPlainText().strip()
        )


class EppItemDialog(QDialog):
    """Diálogo para registrar o editar un Elemento de Protección Personal (EPP):
    - epp_type == 'DELIVERY': EPP de entrega (Guantes, lentes, ropa, calzado de seguridad, casco, bloqueador solar, etc.)
    - epp_type == 'ASSIGNMENT': EPP por asignación/cargo (Arnés de seguridad, líneas de vida, carro y estrobos, polainas y coletos, etc.)
    """

    DELIVERY_CATEGORIES = [
        "Protección de Manos (Guantes cabritilla, nitrilo, anticorte, dieléctricos)",
        "Protección Visual (Lentes de seguridad claros / oscuros, antiparras)",
        "Vestuario y Ropa de Trabajo (Pantalón, camisa, geólogo, térmico, overol)",
        "Calzado de Seguridad (Zapatos / Bototos dieléctricos, botas de agua)",
        "Protección Craneal (Casco de seguridad, barbiquejo)",
        "Protección Solar y Piel (Bloqueador solar UV, legionario, bálsamo)",
        "Protección Auditiva (Tapones auditivos, fonos adosables)",
        "Protección Respiratoria (Mascarillas, filtros, respirador medio rostro)",
        "Otro EPP de Entrega"
    ]

    ASSIGNMENT_CATEGORIES = [
        "Trabajo en Altura - Arnés de Seguridad (Cuerpo completo, ignífugo/dieléctrico)",
        "Trabajo en Altura - Líneas de Vida / Cabos de Vida (Doble mosquetón, acero, textil)",
        "Trabajo en Altura - Carro de Ascenso, Estrobos y Amortiguador de Impacto",
        "Trabajo en Caliente / Soldadura - Polainas y Coletos de Cuero",
        "Trabajo en Caliente / Soldadura - Careta Facial / Máscara Soldar Fotosensible",
        "Riesgo Eléctrico - Pértiga, Guantes Clase 0/00, Alfombra Dieléctrica",
        "Espacios Confinados / Rescate - Trípode, Detector Multigás",
        "Otro EPP por Asignación (Cargo)"
    ]

    STATUS_OPTIONS = [
        ("AVAILABLE", "Disponible en Pañol"),
        ("ASSIGNED", "Asignado (En Cargo)"),
        ("IN_INSPECTION", "En Revisión / Inspección"),
        ("OUT_OF_SERVICE", "Dado de Baja / Fuera de Servicio"),
    ]

    def __init__(self, parent=None, epp: EppItem = None, default_epp_type: str = "DELIVERY", read_only: bool = None):
        super().__init__(parent)
        self.epp = epp
        self.epp_type = epp.epp_type if epp else default_epp_type
        self.is_read_only = (epp is not None) if read_only is None else read_only
        self.resize(660, 690)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # ── Top Header Banner ──
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
        lbl_icon.setPixmap(IconManager.get_icon("check.svg", "#10B981", 22).pixmap(22, 22))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        hb_layout.addWidget(icon_badge)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        ename = self.epp.name if self.epp else "Nuevo Elemento EPP"
        self.lbl_header_title = QLabel(f"Elemento EPP  —  {ename}")
        self.lbl_header_title.setObjectName("detailTitleLabel")
        self.lbl_header_title.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")
        lbl_s = QLabel("Gestión de Elementos de Protección Personal de entrega (stock) y por asignación (cargo)")
        lbl_s.setObjectName("kvKeyLabel")
        title_col.addWidget(self.lbl_header_title)
        title_col.addWidget(lbl_s)
        hb_layout.addLayout(title_col, 1)

        self.lbl_epp_pill = QLabel("●  EPP")
        hb_layout.addWidget(self.lbl_epp_pill)

        main_layout.addWidget(header_banner)

        # ── Scrollable Body ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_widget.setObjectName("scrollContent")
        scroll_layout = QVBoxLayout(content_widget)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(12)

        # Card 1: Identificación y Clasificación EPP
        card_id, body_id = _create_dialog_card("1. Modalidad e Identificación del Elemento EPP", "#10B981")
        form_id = QFormLayout(body_id)
        form_id.setContentsMargins(16, 14, 16, 14)
        form_id.setSpacing(10)
        form_id.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.type_combo = QComboBox()
        self.type_combo.addItem("EPP de Entrega / Stock (Guantes, lentes, ropa, calzado, casco, bloqueador...)", "DELIVERY")
        self.type_combo.addItem("EPP por Asignación / Cargo (Arnés, línea de vida, carro y estrobo, polainas/coletos...)", "ASSIGNMENT")
        idx_t = self.type_combo.findData(self.epp_type)
        if idx_t >= 0:
            self.type_combo.setCurrentIndex(idx_t)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)

        self.nombre_edit = QLineEdit()
        self.nombre_edit.textChanged.connect(self._update_epp_pill)
        self.codigo_edit = QLineEdit()

        self.cat_combo = QComboBox()
        self.cat_combo.setEditable(True)

        self.marca_edit = QLineEdit()
        self.marca_edit.setPlaceholderText("Ej: 3M, MSA, Steelpro, Bata Industrials, Honeywell...")

        self.talla_modelo_edit = QLineEdit()
        self.talla_modelo_edit.setPlaceholderText("Ej: Talla L, N° 42, Modelo V-Gard, 1 Litro FPS 50+...")

        self.serie_edit = QLineEdit()
        self.serie_edit.setPlaceholderText("N° de Serie o Lote de certificación (clave para Arnés, Líneas de vida, Carros)...")

        form_id.addRow("Modalidad EPP *:", self.type_combo)
        form_id.addRow("Nombre del Elemento *:", self.nombre_edit)
        form_id.addRow("Código Interno / SKU:", self.codigo_edit)
        form_id.addRow("Categoría EPP:", self.cat_combo)
        form_id.addRow("Marca / Fabricante:", self.marca_edit)
        form_id.addRow("Talla / Medida / Modelo:", self.talla_modelo_edit)
        self.lbl_serie = QLabel("N° Serie / Certificación:")
        form_id.addRow(self.lbl_serie, self.serie_edit)

        scroll_layout.addWidget(card_id)

        # Card 2: Stock / Estado Operativo y Vencimiento
        card_st, body_st = _create_dialog_card("2. Stock, Estado de Cargo, Inspección y Notas", "#F59E0B")
        form_st = QFormLayout(body_st)
        form_st.setContentsMargins(16, 14, 16, 14)
        form_st.setSpacing(10)
        form_st.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.cant_spin = QSpinBox()
        self.cant_spin.setRange(0, 999999)
        self.cant_spin.setValue(1)
        self.cant_spin.valueChanged.connect(self._update_epp_pill)

        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 999999)
        self.min_spin.setValue(3)

        self.unidad_combo = QComboBox()
        self.unidad_combo.setEditable(True)
        self.unidad_combo.addItems(["unidad", "par", "juego", "kit", "frasco", "envase", "caja"])

        self.status_combo = QComboBox()
        for val, lbl in self.STATUS_OPTIONS:
            self.status_combo.addItem(lbl, val)
        self.status_combo.currentIndexChanged.connect(self._update_epp_pill)

        self.vencimiento_edit = QLineEdit()
        self.vencimiento_edit.setPlaceholderText("Ej: 2027-06-30 o fecha próxima inspección...")

        self.ubicacion_edit = QLineEdit("Pañol - Sección EPP")
        self.notas_edit = QTextEdit()
        self.notas_edit.setMaximumHeight(65)
        self.notas_edit.setPlaceholderText("Certificación, estado físico, observaciones...")

        self.lbl_cant = QLabel("Stock Disponible:")
        form_st.addRow(self.lbl_cant, self.cant_spin)

        self.lbl_min = QLabel("Stock Mínimo (Alerta):")
        form_st.addRow(self.lbl_min, self.min_spin)

        self.lbl_unidad = QLabel("Unidad:")
        form_st.addRow(self.lbl_unidad, self.unidad_combo)

        self.lbl_status = QLabel("Estado del Equipo:")
        form_st.addRow(self.lbl_status, self.status_combo)

        self.lbl_venc = QLabel("Vencimiento / Próx. Revisión:")
        form_st.addRow(self.lbl_venc, self.vencimiento_edit)

        form_st.addRow("Ubicación en Pañol:", self.ubicacion_edit)
        form_st.addRow("Notas / Certificaciones:", self.notas_edit)

        scroll_layout.addWidget(card_st)
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

        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.clicked.connect(self.reject)

        self.btn_edit_mode = QPushButton("Editar")
        self.btn_edit_mode.setObjectName("primaryButton")
        self.btn_edit_mode.setIcon(IconManager.get_icon("edit.svg", "#000000", 16))
        self.btn_edit_mode.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit_mode.clicked.connect(lambda: self.set_read_only(False))

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.clicked.connect(self._on_cancel)

        self.btn_save = QPushButton("Guardar EPP")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setIcon(IconManager.get_icon("check.svg", "#000000", 16))
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self._on_save)

        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_edit_mode)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        main_layout.addWidget(footer_bar)

        self._on_type_changed()
        if self.epp:
            self._load_data()
        self._update_epp_pill()
        self.set_read_only(self.is_read_only)

    def _update_epp_pill(self):
        name = self.nombre_edit.text().strip() or (self.epp.name if self.epp else "Nuevo EPP")
        self.lbl_header_title.setText(f"Elemento EPP  —  {name}")
        cur_type = self.type_combo.currentData()
        if cur_type == "ASSIGNMENT":
            fg, bg, txt = "#F59E0B", "#451A03", f"●  Cargo: {self.status_combo.currentText()}"
        else:
            fg, bg, txt = "#10B981", "#064E3B", f"●  Entrega (Stock: {self.cant_spin.value()})"
        self.lbl_epp_pill.setText(txt)
        self.lbl_epp_pill.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border: 1px solid {fg}; "
            f"border-radius: 5px; padding: 4px 10px; font-weight: bold; font-size: 11px;"
        )

    def _on_type_changed(self):
        cur_type = self.type_combo.currentData()
        is_assign = (cur_type == "ASSIGNMENT")

        prev_cat = self.cat_combo.currentText()
        self.cat_combo.clear()
        if is_assign:
            self.cat_combo.addItems(self.ASSIGNMENT_CATEGORIES)
            self.nombre_edit.setPlaceholderText("Ej: Arnés de seguridad 4 argollas, Línea de vida doble, Carro ascenso, Polainas y coleto...")
        else:
            self.cat_combo.addItems(self.DELIVERY_CATEGORIES)
            self.nombre_edit.setPlaceholderText("Ej: Guantes cabritilla, Lentes seguridad claros, Calzado seguridad N°42, Casco, Bloqueador solar...")

        if prev_cat:
            self.cat_combo.setCurrentText(prev_cat)

        self.lbl_cant.setVisible(not is_assign)
        self.cant_spin.setVisible(not is_assign)
        self.lbl_min.setVisible(not is_assign)
        self.min_spin.setVisible(not is_assign)
        self.lbl_unidad.setVisible(not is_assign)
        self.unidad_combo.setVisible(not is_assign)

        self.lbl_status.setVisible(is_assign)
        self.status_combo.setVisible(is_assign)
        self._update_epp_pill()

    def set_read_only(self, ro: bool):
        self.is_read_only = ro
        if self.epp:
            self.setWindowTitle(f"{'Ficha de EPP' if ro else 'Editar EPP'} - {self.epp.name}")
            self.lbl_mode.setText("● MODO LECTURA / CONSULTA" if ro else "● MODO EDICIÓN ACTIVO")
            self.lbl_mode.setStyleSheet(
                "color: #94A3B8; font-weight: bold; font-size: 11px;" if ro
                else "color: #F59E0B; font-weight: bold; font-size: 11px;"
            )
        else:
            self.setWindowTitle("Registrar Nuevo EPP en Pañol")
            self.lbl_mode.setText("● NUEVO ELEMENTO EPP")
            self.lbl_mode.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px;")

        self.btn_close.setVisible(ro)
        self.btn_edit_mode.setVisible(ro)
        self.btn_cancel.setVisible(not ro)
        self.btn_save.setVisible(not ro)

        enabled = not ro
        self.type_combo.setEnabled(enabled and self.epp is None)
        self.nombre_edit.setReadOnly(ro)
        self.codigo_edit.setReadOnly(ro)
        self.cat_combo.setEnabled(enabled)
        self.marca_edit.setReadOnly(ro)
        self.talla_modelo_edit.setReadOnly(ro)
        self.serie_edit.setReadOnly(ro)
        self.cant_spin.setEnabled(enabled)
        self.min_spin.setEnabled(enabled)
        self.unidad_combo.setEnabled(enabled)
        self.status_combo.setEnabled(enabled)
        self.vencimiento_edit.setReadOnly(ro)
        self.ubicacion_edit.setReadOnly(ro)
        self.notas_edit.setReadOnly(ro)

    def _load_data(self):
        idx = self.type_combo.findData(self.epp.epp_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        self._on_type_changed()

        self.nombre_edit.setText(self.epp.name)
        self.codigo_edit.setText(self.epp.code)
        self.cat_combo.setCurrentText(self.epp.category)
        self.marca_edit.setText(self.epp.brand)
        self.talla_modelo_edit.setText(self.epp.size_or_model)
        self.serie_edit.setText(self.epp.serial_number)
        self.cant_spin.setValue(self.epp.quantity)
        self.min_spin.setValue(self.epp.minimum_quantity)
        self.unidad_combo.setCurrentText(self.epp.unit)

        idx_st = self.status_combo.findData(self.epp.status)
        if idx_st >= 0:
            self.status_combo.setCurrentIndex(idx_st)

        self.vencimiento_edit.setText(self.epp.expiration_date)
        self.ubicacion_edit.setText(self.epp.location)
        self.notas_edit.setPlainText(self.epp.notes)

    def _on_cancel(self):
        if self.epp:
            self._load_data()
            self.set_read_only(True)
        else:
            self.reject()

    def _on_save(self):
        if not self.nombre_edit.text().strip():
            QMessageBox.warning(self, "Campo Requerido", "El nombre del EPP es obligatorio.")
            return
        self.accept()

    def get_epp(self) -> EppItem:
        e_id = self.epp.id if self.epp else ""
        cur_type = self.type_combo.currentData()
        assigned_to = self.epp.assigned_to if self.epp else ""
        assigned_type = self.epp.assigned_type if self.epp else ""
        assigned_date = self.epp.assigned_date if self.epp else ""

        return EppItem(
            id=e_id,
            name=self.nombre_edit.text().strip(),
            code=self.codigo_edit.text().strip(),
            epp_type=cur_type,
            category=self.cat_combo.currentText().strip() or "General",
            brand=self.marca_edit.text().strip(),
            size_or_model=self.talla_modelo_edit.text().strip(),
            serial_number=self.serie_edit.text().strip(),
            quantity=1 if cur_type == "ASSIGNMENT" else self.cant_spin.value(),
            minimum_quantity=0 if cur_type == "ASSIGNMENT" else self.min_spin.value(),
            unit=self.unidad_combo.currentText().strip() or "unidad",
            status=self.status_combo.currentData() if cur_type == "ASSIGNMENT" else "AVAILABLE",
            assigned_to=assigned_to,
            assigned_type=assigned_type,
            assigned_date=assigned_date,
            expiration_date=self.vencimiento_edit.text().strip(),
            location=self.ubicacion_edit.text().strip() or "Pañol",
            notes=self.notas_edit.toPlainText().strip()
        )


class PanolMovementDialog(QDialog):
    """Diálogo unificado para registrar:
    - Ingreso a Pañol (+) de Insumos o EPP
    - Entrega (-) de Insumos o EPP a un Técnico, Personal Externo o Recinto
    - Asignación (Cargo) de EPP por asignación o Herramientas a un Técnico, Personal Externo o Recinto
    """

    def __init__(
        self,
        item_name: str,
        current_stock: int = 1,
        unit: str = "unidad",
        operation: str = "OUT",  # "IN", "OUT", "ASSIGN"
        item_category: str = "SUPPLY",  # "SUPPLY", "EPP_DELIVERY", "EPP_ASSIGNMENT", "TOOL"
        technician_service=None,
        client_service=None,
        parent=None
    ):
        super().__init__(parent)
        self.item_name = item_name
        self.current_stock = current_stock
        self.unit = unit or "unid."
        self.operation = operation.upper()
        self.item_category = item_category
        self.technician_service = technician_service
        self.client_service = client_service

        self.is_in = (self.operation == "IN")
        self.is_assign = (self.operation == "ASSIGN")

        if self.is_in:
            title = f"Ingreso a Pañol (+) — {item_name}"
        elif self.is_assign:
            title = f"Asignación / Entrega a Cargo — {item_name}"
        else:
            title = f"Entrega desde Pañol (-) — {item_name}"

        self.setWindowTitle(title)
        self.resize(580, 520)
        self.setModal(True)

        self._setup_ui()
        self._on_recipient_type_changed()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # ── Header Banner ──
        header = QFrame()
        header.setObjectName("dialogHeaderBanner")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 12, 16, 12)
        h_layout.setSpacing(14)

        icon_name = "arrow_down.svg" if self.is_in else "arrow_up.svg"
        accent = "#10B981" if self.is_in else ("#38BDF8" if self.is_assign else "#F59E0B")

        icon_badge = QFrame()
        icon_badge.setObjectName("statIconBadge")
        icon_badge.setFixedSize(44, 44)
        ib_l = QVBoxLayout(icon_badge)
        ib_l.setContentsMargins(0, 0, 0, 0)
        ib_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon = QLabel()
        lbl_icon.setPixmap(IconManager.get_icon(icon_name, accent, 22).pixmap(22, 22))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        h_layout.addWidget(icon_badge)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        lbl_name = QLabel(self.item_name)
        lbl_name.setObjectName("detailTitleLabel")
        lbl_name.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")
        info_layout.addWidget(lbl_name)

        if not self.is_assign:
            lbl_sub = QLabel(f"Stock disponible actual en Pañol: {self.current_stock} {self.unit}")
        else:
            lbl_sub = QLabel("Modalidad: Asignación / Cargo Retornable a Pañol")
        lbl_sub.setObjectName("kvKeyLabel")
        info_layout.addWidget(lbl_sub)

        h_layout.addLayout(info_layout, 1)

        op_lbl = "● INGRESO (+)" if self.is_in else ("● CARGO" if self.is_assign else "● ENTREGA (-)")
        op_bg = "#064E3B" if self.is_in else ("#0C4A6E" if self.is_assign else "#451A03")
        lbl_pill = QLabel(op_lbl)
        lbl_pill.setStyleSheet(
            f"background-color: {op_bg}; color: {accent}; border: 1px solid {accent}; "
            f"border-radius: 5px; padding: 4px 10px; font-weight: bold; font-size: 11px;"
        )
        h_layout.addWidget(lbl_pill)

        main_layout.addWidget(header)

        # ── Form Card ──
        card, card_body = _create_dialog_card("Datos del Movimiento y Destinatario", accent)
        form = QFormLayout(card_body)
        form.setContentsMargins(16, 14, 16, 16)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.spin_qty = QSpinBox()
        self.spin_qty.setMinimum(1)
        if self.is_in:
            self.spin_qty.setMaximum(999999)
        else:
            self.spin_qty.setMaximum(max(1, self.current_stock))
        self.spin_qty.setValue(1)

        if not self.is_assign:
            form.addRow(f"Cantidad ({self.unit}) *:", self.spin_qty)

        self.combo_recipient_type = QComboBox()
        self.combo_recipient_type.addItem("👷 Técnico Interno", "TECHNICIAN")
        self.combo_recipient_type.addItem("🧑‍🔧 Personal Externo / Contratista", "EXTERNAL")
        self.combo_recipient_type.addItem("🏢 Recinto / Instalación / Sede", "SITE")
        self.combo_recipient_type.currentIndexChanged.connect(self._on_recipient_type_changed)

        self.combo_technician = QComboBox()
        self.combo_technician.setEditable(True)
        self._populate_technicians()

        self.txt_external = QLineEdit()
        self.txt_external.setPlaceholderText("Nombre y empresa del personal externo (Ej: Juan Pérez - Contratista)...")

        self.combo_site = QComboBox()
        self.combo_site.setEditable(True)
        self._populate_sites()

        self.lbl_rec_type = QLabel("Entregar / Asignar a *:")
        self.lbl_tech = QLabel("Seleccionar Técnico *:")
        self.lbl_ext = QLabel("Personal Externo *:")
        self.lbl_site = QLabel("Recinto / Sede *:")

        if not self.is_in:
            form.addRow(self.lbl_rec_type, self.combo_recipient_type)
            form.addRow(self.lbl_tech, self.combo_technician)
            form.addRow(self.lbl_ext, self.txt_external)
            form.addRow(self.lbl_site, self.combo_site)

        self.combo_reason = QComboBox()
        self.combo_reason.setEditable(True)
        if self.is_in:
            self.combo_reason.addItems([
                "Compra / Recepción en Pañol",
                "Reposición de Stock",
                "Devolución de Sobrante a Pañol",
                "Ajuste de Inventario (+)"
            ])
        elif self.is_assign:
            self.combo_reason.addItems([
                "Asignación a Cargo Permanente",
                "Préstamo para Trabajo en Terreno / Altura / Caliente",
                "Asignación a Recinto / Instalación",
                "Reemplazo Temporal"
            ])
        else:
            self.combo_reason.addItems([
                "Entrega para Mantenimiento / Limpieza",
                "Dotación / Renovación de EPP",
                "Reposición por Desgaste o Deterioro",
                "Abastecimiento de Recinto / Sala Técnica",
                "Entrega para Orden de Trabajo (OT)"
            ])
        form.addRow("Motivo / Concepto *:", self.combo_reason)

        self.txt_reference = QLineEdit()
        self.txt_reference.setPlaceholderText(
            "Ej: Factura / Guía N°..." if self.is_in else "Ej: Vale de Pañol, N° OT, Cargo firmado..."
        )
        form.addRow("N° Guía / OT / Ref:", self.txt_reference)

        self.txt_performed_by = QLineEdit("Pañolero")
        form.addRow("Registrado por:", self.txt_performed_by)

        self.txt_notes = QLineEdit()
        self.txt_notes.setPlaceholderText("Observaciones adicionales...")
        form.addRow("Observaciones:", self.txt_notes)

        main_layout.addWidget(card, 1)

        # ── Footer Bar ──
        footer_bar = QFrame()
        footer_bar.setObjectName("dialogFooterBar")
        btn_layout = QHBoxLayout(footer_bar)
        btn_layout.setContentsMargins(14, 10, 14, 10)
        btn_layout.setSpacing(10)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()

        btn_label = "Confirmar Ingreso (+)" if self.is_in else ("Confirmar Asignación" if self.is_assign else "Confirmar Entrega (-)")
        self.btn_confirm = QPushButton(btn_label)
        self.btn_confirm.setObjectName("successButton" if self.is_in else "primaryButton")
        self.btn_confirm.setIcon(IconManager.get_icon(icon_name, "#FFFFFF" if self.is_in else "#000000", 16))
        self.btn_confirm.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_confirm.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.btn_confirm)

        main_layout.addWidget(footer_bar)

    def _populate_technicians(self):
        self.combo_technician.clear()
        if self.technician_service:
            try:
                names = self.technician_service.get_technician_names()
                for n in names:
                    self.combo_technician.addItem(n)
            except Exception:
                pass

    def _populate_sites(self):
        self.combo_site.clear()
        if self.client_service:
            try:
                for client in self.client_service.get_all_clients():
                    sites = self.client_service.get_sites_for_client(client.id)
                    if sites:
                        for s in sites:
                            self.combo_site.addItem(f"{client.company_name} - {s.name}")
                    else:
                        self.combo_site.addItem(client.company_name)
            except Exception:
                pass

    def _on_recipient_type_changed(self):
        if self.is_in:
            return
        rtype = self.combo_recipient_type.currentData()
        self.lbl_tech.setVisible(rtype == "TECHNICIAN")
        self.combo_technician.setVisible(rtype == "TECHNICIAN")

        self.lbl_ext.setVisible(rtype == "EXTERNAL")
        self.txt_external.setVisible(rtype == "EXTERNAL")

        self.lbl_site.setVisible(rtype == "SITE")
        self.combo_site.setVisible(rtype == "SITE")

    def _get_selected_recipient(self) -> tuple[str, str]:
        if self.is_in:
            return ("", "Ingreso a Pañol")
        rtype = self.combo_recipient_type.currentData()
        if rtype == "TECHNICIAN":
            return ("TECHNICIAN", self.combo_technician.currentText().strip())
        elif rtype == "EXTERNAL":
            return ("EXTERNAL", self.txt_external.text().strip())
        else:
            return ("SITE", self.combo_site.currentText().strip())

    def _on_confirm(self):
        if not self.is_assign and not self.is_in:
            if self.spin_qty.value() > self.current_stock:
                QMessageBox.warning(self, "Stock Insuficiente", f"Stock disponible: {self.current_stock} {self.unit}.")
                return

        if not self.is_in:
            rtype, rname = self._get_selected_recipient()
            if not rname:
                QMessageBox.warning(self, "Destinatario Requerido", "Por favor indique el Técnico, Personal Externo o Recinto que recibe el elemento.")
                return

        self.accept()

    def get_data(self) -> dict:
        rtype, rname = self._get_selected_recipient()
        return {
            "quantity": 1 if self.is_assign else self.spin_qty.value(),
            "recipient_type": rtype,
            "recipient_name": rname,
            "reason": self.combo_reason.currentText().strip(),
            "reference": self.txt_reference.text().strip(),
            "performed_by": self.txt_performed_by.text().strip() or "Pañolero",
            "notes": self.txt_notes.text().strip()
        }


class GasCylinderDialog(QDialog):
    """Diálogo para registrar o editar un Cilindro (Tubo / Bombona) en Pañol:
    - Gases Combustibles y Técnicos de Soldadura/Presurización (Oxígeno, Nitrógeno, Gas Propano, Gas Butano, Argón, Acetileno, MAPP) en m³ o Kg
    - Gases Refrigerantes en Cilindros/Bombonas (R-410A, R-32, R-134a, R-407C, R-22, R-404A, R-507, R-454B) en Kg
    - Almacenamiento de Gas Refrigerante Recuperado en Kg
    - Agente de Limpieza de Circuitos (R-141b, etc.) en Kg
    """

    CATEGORY_OPTIONS = [
        ("REFRIGERANT", "❄️ Gas Refrigerante Virgen (Bombona en Kg)"),
        ("WELDING", "🔥 Gas de Soldadura / Presurización (Oxígeno, Nitrógeno, Propano, Butano, Argón en m³ o Kg)"),
        ("RECOVERED", "♻️ Cilindro de Gas Refrigerante Recuperado (Almacenamiento en Kg)"),
        ("CLEANING", "🧪 Agente de Limpieza de Sistema (R-141b, etc. en Kg)"),
    ]

    GAS_TYPES_BY_CAT = {
        "WELDING": [
            "Oxígeno (O2)",
            "Nitrógeno (N2)",
            "Gas Propano",
            "Gas Butano",
            "Argón",
            "Acetileno",
            "Gas MAPP / Propileno",
            "Mezcla Argón / CO2"
        ],
        "REFRIGERANT": [
            "R-410A",
            "R-32",
            "R-134a",
            "R-407C",
            "R-22",
            "R-404A",
            "R-507",
            "R-454B",
            "R-1234ze",
            "R-290 (Propano Refrigerante)"
        ],
        "RECOVERED": [
            "R-410A Recuperado",
            "R-22 Recuperado",
            "R-134a Recuperado",
            "R-407C Recuperado",
            "R-32 Recuperado",
            "R-404A Recuperado",
            "Refrigerante Mixto Recuperado"
        ],
        "CLEANING": [
            "R-141b (Agente de Limpieza)",
            "Agente Limpieza Circuito Frigorífico (Flush)",
            "Nitrógeno para Barrido (N2)"
        ]
    }

    STATUS_OPTIONS = [
        ("AVAILABLE", "En Pañol (Disponible)"),
        ("IN_USE", "En Terreno / En Uso"),
        ("EMPTY", "Vacío"),
        ("RETURNED", "Devuelto a Proveedor"),
    ]

    def __init__(self, parent=None, cylinder: GasCylinder = None, default_category: str = "REFRIGERANT", read_only: bool = None):
        super().__init__(parent)
        self.cylinder = cylinder
        self.default_category = cylinder.gas_category if cylinder else default_category
        self.is_read_only = (cylinder is not None) if read_only is None else read_only
        self.resize(650, 680)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # ── Top Header Banner ──
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
        lbl_icon.setPixmap(IconManager.get_icon("equipment.svg", "#06B6D4", 22).pixmap(22, 22))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        hb_layout.addWidget(icon_badge)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        cname = f"{self.cylinder.code} ({self.cylinder.gas_type})" if self.cylinder else "Nuevo Cilindro / Bombona"
        self.lbl_header_title = QLabel(f"Cilindro de Gas  —  {cname}")
        self.lbl_header_title.setObjectName("detailTitleLabel")
        self.lbl_header_title.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")
        lbl_s = QLabel("Control de bombonas de refrigerante, tubos de soldadura, gas recuperado y agentes de limpieza")
        lbl_s.setObjectName("kvKeyLabel")
        title_col.addWidget(self.lbl_header_title)
        title_col.addWidget(lbl_s)
        hb_layout.addLayout(title_col, 1)

        self.lbl_cyl_pill = QLabel("●  En Pañol")
        hb_layout.addWidget(self.lbl_cyl_pill)

        main_layout.addWidget(header_banner)

        # ── Scrollable Body ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_widget.setObjectName("scrollContent")
        scroll_layout = QVBoxLayout(content_widget)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        scroll_layout.setSpacing(12)

        # Card 1: Identificación y Tipo de Gas
        card_id, body_id = _create_dialog_card("1. Clasificación e Identificación del Cilindro / Tubo", "#06B6D4")
        form_id = QFormLayout(body_id)
        form_id.setContentsMargins(16, 14, 16, 14)
        form_id.setSpacing(10)
        form_id.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.cat_combo = QComboBox()
        for val, lbl in self.CATEGORY_OPTIONS:
            self.cat_combo.addItem(lbl, val)
        idx_c = self.cat_combo.findData(self.default_category)
        if idx_c >= 0:
            self.cat_combo.setCurrentIndex(idx_c)
        self.cat_combo.currentIndexChanged.connect(self._on_category_changed)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Ej: CIL-R410-01, TUBO-OXI-01, NITRO-03, REC-01, R141-01...")
        self.code_edit.textChanged.connect(self._update_cyl_pill)

        self.gas_type_combo = QComboBox()
        self.gas_type_combo.setEditable(True)
        self.gas_type_combo.currentTextChanged.connect(self._update_cyl_pill)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Kg", "m³"])
        self.unit_combo.currentTextChanged.connect(self._update_cyl_pill)

        form_id.addRow("Categoría de Cilindro *:", self.cat_combo)
        form_id.addRow("Código / N° Cilindro (Tubo) *:", self.code_edit)
        form_id.addRow("Tipo de Gas / Agente *:", self.gas_type_combo)
        form_id.addRow("Unidad de Medida (Kg / m³) *:", self.unit_combo)
        scroll_layout.addWidget(card_id)

        # Card 2: Pesaje, Capacidad y Ubicación
        card_cap, body_cap = _create_dialog_card("2. Capacidad, Saldo Disponible y Ubicación", "#38BDF8")
        form_cap = QFormLayout(body_cap)
        form_cap.setContentsMargins(16, 14, 16, 14)
        form_cap.setSpacing(10)
        form_cap.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.initial_spin = QDoubleSpinBox()
        self.initial_spin.setRange(0.0, 100000.0)
        self.initial_spin.setDecimals(2)
        self.initial_spin.setValue(11.30)

        self.current_spin = QDoubleSpinBox()
        self.current_spin.setRange(0.0, 100000.0)
        self.current_spin.setDecimals(2)
        self.current_spin.setValue(11.30)
        self.current_spin.valueChanged.connect(self._update_cyl_pill)

        self.tare_spin = QDoubleSpinBox()
        self.tare_spin.setRange(0.0, 500.0)
        self.tare_spin.setDecimals(2)
        self.tare_spin.setSuffix(" Kg")

        self.status_combo = QComboBox()
        for val, lbl in self.STATUS_OPTIONS:
            self.status_combo.addItem(lbl, val)
        self.status_combo.currentIndexChanged.connect(self._update_cyl_pill)

        self.assigned_edit = QLineEdit()
        self.assigned_edit.setPlaceholderText("Dejar vacío si está en Pañol, o indicar técnico/recinto...")

        self.location_edit = QLineEdit("Pañol - Jaula de Gases")
        self.supplier_edit = QLineEdit()
        self.supplier_edit.setPlaceholderText("Ej: Indura, Linde, Gasco, Refrigeración Industrial...")

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(65)
        self.notes_edit.setPlaceholderText("Observaciones, prueba hidrostática, pureza, etc.")

        self.lbl_initial = QLabel("Contenido Neto Inicial / Cap.:")
        form_cap.addRow(self.lbl_initial, self.initial_spin)

        self.lbl_current = QLabel("Contenido Actual en Cilindro:")
        form_cap.addRow(self.lbl_current, self.current_spin)

        form_cap.addRow("Peso Tara Cilindro Vacío:", self.tare_spin)
        form_cap.addRow("Estado del Cilindro:", self.status_combo)
        form_cap.addRow("Asignado a (si está en terreno):", self.assigned_edit)
        form_cap.addRow("Ubicación en Pañol:", self.location_edit)
        form_cap.addRow("Proveedor:", self.supplier_edit)
        form_cap.addRow("Notas / Observaciones:", self.notes_edit)

        scroll_layout.addWidget(card_cap)
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

        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.clicked.connect(self.reject)

        self.btn_edit_mode = QPushButton("Editar")
        self.btn_edit_mode.setObjectName("primaryButton")
        self.btn_edit_mode.setIcon(IconManager.get_icon("edit.svg", "#000000", 16))
        self.btn_edit_mode.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit_mode.clicked.connect(lambda: self.set_read_only(False))

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.clicked.connect(self._on_cancel)

        self.btn_save = QPushButton("Guardar Cilindro")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setIcon(IconManager.get_icon("check.svg", "#000000", 16))
        self.btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_save.clicked.connect(self._on_save)

        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_edit_mode)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        main_layout.addWidget(footer_bar)

        self._on_category_changed()
        if self.cylinder:
            self._load_data()
        self._update_cyl_pill()
        self.set_read_only(self.is_read_only)

    def _update_cyl_pill(self):
        code = self.code_edit.text().strip() or (self.cylinder.code if self.cylinder else "Nuevo")
        gtype = self.gas_type_combo.currentText().strip()
        self.lbl_header_title.setText(f"Cilindro  —  {code} ({gtype})" if gtype else f"Cilindro  —  {code}")
        u = self.unit_combo.currentText().strip() or "Kg"
        cur = self.current_spin.value()
        st = self.status_combo.currentData()
        if st == "EMPTY" or (self.cat_combo.currentData() != "RECOVERED" and cur <= 0):
            fg, bg = "#EF4444", "#450A0A"
        elif st == "IN_USE":
            fg, bg = "#F59E0B", "#451A03"
        else:
            fg, bg = "#06B6D4", "#083344"
        self.lbl_cyl_pill.setText(f"●  {cur:g} {u}")
        self.lbl_cyl_pill.setStyleSheet(
            f"background-color: {bg}; color: {fg}; border: 1px solid {fg}; "
            f"border-radius: 5px; padding: 4px 10px; font-weight: bold; font-size: 11px;"
        )

    def _on_category_changed(self):
        cat = self.cat_combo.currentData()
        prev_gas = self.gas_type_combo.currentText()
        self.gas_type_combo.clear()
        self.gas_type_combo.addItems(self.GAS_TYPES_BY_CAT.get(cat, []))
        if prev_gas:
            self.gas_type_combo.setCurrentText(prev_gas)

        if cat == "WELDING":
            self.lbl_initial.setText("Capacidad / Carga Inicial (m³ o Kg):")
            self.lbl_current.setText("Contenido Restante Actual:")
        elif cat == "RECOVERED":
            self.unit_combo.setCurrentText("Kg")
            self.lbl_initial.setText("Capacidad Máx. Cilindro Recuperación (Kg):")
            self.lbl_current.setText("Gas Recuperado Almacenado Actual (Kg):")
            if not self.cylinder:
                self.initial_spin.setValue(20.0)
                self.current_spin.setValue(0.0)
        elif cat == "CLEANING":
            self.unit_combo.setCurrentText("Kg")
            self.lbl_initial.setText("Contenido Neto Inicial (Kg):")
            self.lbl_current.setText("Contenido Restante en Cilindro (Kg):")
            if not self.cylinder:
                self.initial_spin.setValue(13.6)
                self.current_spin.setValue(13.6)
        else:
            self.unit_combo.setCurrentText("Kg")
            self.lbl_initial.setText("Contenido Neto Inicial Bombona (Kg):")
            self.lbl_current.setText("Queda en Cilindro Actual (Kg):")
            if not self.cylinder:
                self.initial_spin.setValue(11.3)
                self.current_spin.setValue(11.3)
        self._update_cyl_pill()

    def set_read_only(self, ro: bool):
        self.is_read_only = ro
        if self.cylinder:
            self.setWindowTitle(f"{'Ficha de Cilindro' if ro else 'Editar Cilindro'} - {self.cylinder.code}")
            self.lbl_mode.setText("● MODO LECTURA / CONSULTA" if ro else "● MODO EDICIÓN ACTIVO")
            self.lbl_mode.setStyleSheet(
                "color: #94A3B8; font-weight: bold; font-size: 11px;" if ro
                else "color: #F59E0B; font-weight: bold; font-size: 11px;"
            )
        else:
            self.setWindowTitle("Registrar Nuevo Cilindro / Bombona en Pañol")
            self.lbl_mode.setText("● NUEVO CILINDRO / BOMBONA")
            self.lbl_mode.setStyleSheet("color: #10B981; font-weight: bold; font-size: 11px;")

        self.btn_close.setVisible(ro)
        self.btn_edit_mode.setVisible(ro)
        self.btn_cancel.setVisible(not ro)
        self.btn_save.setVisible(not ro)

        en = not ro
        self.cat_combo.setEnabled(en)
        self.code_edit.setReadOnly(ro)
        self.gas_type_combo.setEnabled(en)
        self.unit_combo.setEnabled(en)
        self.initial_spin.setEnabled(en)
        self.current_spin.setEnabled(en)
        self.tare_spin.setEnabled(en)
        self.status_combo.setEnabled(en)
        self.assigned_edit.setReadOnly(ro)
        self.location_edit.setReadOnly(ro)
        self.supplier_edit.setReadOnly(ro)
        self.notes_edit.setReadOnly(ro)

    def _load_data(self):
        idx_c = self.cat_combo.findData(self.cylinder.gas_category)
        if idx_c >= 0:
            self.cat_combo.setCurrentIndex(idx_c)
        self._on_category_changed()

        self.code_edit.setText(self.cylinder.code)
        self.gas_type_combo.setCurrentText(self.cylinder.gas_type)
        self.unit_combo.setCurrentText(self.cylinder.unit)
        self.initial_spin.setValue(self.cylinder.initial_amount)
        self.current_spin.setValue(self.cylinder.current_amount)
        self.tare_spin.setValue(self.cylinder.tare_weight_kg)

        idx_s = self.status_combo.findData(self.cylinder.status)
        if idx_s >= 0:
            self.status_combo.setCurrentIndex(idx_s)

        self.assigned_edit.setText(self.cylinder.assigned_to)
        self.location_edit.setText(self.cylinder.location)
        self.supplier_edit.setText(self.cylinder.supplier)
        self.notes_edit.setPlainText(self.cylinder.notes)

    def _on_cancel(self):
        if self.cylinder:
            self._load_data()
            self.set_read_only(True)
        else:
            self.reject()

    def _on_save(self):
        if not self.code_edit.text().strip():
            QMessageBox.warning(self, "Campo Requerido", "Ingrese el código o número identificatorio del cilindro/tubo.")
            return
        if not self.gas_type_combo.currentText().strip():
            QMessageBox.warning(self, "Campo Requerido", "Seleccione o escriba el tipo de gas.")
            return
        self.accept()

    def get_cylinder(self) -> GasCylinder:
        c_id = self.cylinder.id if self.cylinder else ""
        return GasCylinder(
            id=c_id,
            code=self.code_edit.text().strip(),
            gas_category=self.cat_combo.currentData(),
            gas_type=self.gas_type_combo.currentText().strip(),
            unit=self.unit_combo.currentText().strip() or "Kg",
            initial_amount=round(self.initial_spin.value(), 3),
            current_amount=round(self.current_spin.value(), 3),
            tare_weight_kg=round(self.tare_spin.value(), 2),
            status=self.status_combo.currentData(),
            assigned_to=self.assigned_edit.text().strip(),
            location=self.location_edit.text().strip() or "Pañol",
            supplier=self.supplier_edit.text().strip(),
            notes=self.notes_edit.toPlainText().strip()
        )


class GasMovementDialog(QDialog):
    """Diálogo para registrar:
    - Uso / Carga de Gas en un Equipo (o en trabajos de soldadura/barrido), descontando Kg o m³ del cilindro
    - Ingreso / Recarga de Cilindro o Recuperación de Gas Refrigerante desde un equipo hacia cilindro de recuperación
    """

    def __init__(
        self,
        cylinder: GasCylinder,
        movement_type: str = "OUT",  # "OUT" (Uso/Carga en equipo) o "IN" (Recarga / Almacenar gas recuperado)
        equipment_service=None,
        technician_service=None,
        parent=None
    ):
        super().__init__(parent)
        self.cylinder = cylinder
        self.movement_type = movement_type.upper()
        self.equipment_service = equipment_service
        self.technician_service = technician_service
        self.is_in = (self.movement_type == "IN")

        if self.is_in:
            if cylinder.gas_category == "RECOVERED":
                title = f"Ingresar Gas Refrigerante Recuperado (+) — {cylinder.code}"
            else:
                title = f"Recarga / Ingreso a Cilindro (+) — {cylinder.code}"
        else:
            title = f"Registrar Uso / Carga de Gas (-) — {cylinder.code} ({cylinder.gas_type})"

        self.setWindowTitle(title)
        self.resize(600, 520)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # ── Header Banner ──
        header = QFrame()
        header.setObjectName("dialogHeaderBanner")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 12, 16, 12)
        h_layout.setSpacing(14)

        icon_name = "arrow_down.svg" if self.is_in else "arrow_up.svg"
        accent = "#10B981" if self.is_in else "#F59E0B"

        icon_badge = QFrame()
        icon_badge.setObjectName("statIconBadge")
        icon_badge.setFixedSize(44, 44)
        ib_l = QVBoxLayout(icon_badge)
        ib_l.setContentsMargins(0, 0, 0, 0)
        ib_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon = QLabel()
        lbl_icon.setPixmap(IconManager.get_icon(icon_name, accent, 22).pixmap(22, 22))
        lbl_icon.setStyleSheet("background: transparent; border: none;")
        ib_l.addWidget(lbl_icon)
        h_layout.addWidget(icon_badge)

        info_l = QVBoxLayout()
        info_l.setSpacing(2)
        lbl_t = QLabel(f"Cilindro {self.cylinder.code}  —  {self.cylinder.gas_type}")
        lbl_t.setObjectName("detailTitleLabel")
        lbl_t.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")
        info_l.addWidget(lbl_t)

        u = self.cylinder.unit
        lbl_s = QLabel(
            f"Contenido Inicial: {self.cylinder.initial_amount:g} {u}  |  "
            f"Disponible Actual: {self.cylinder.current_amount:g} {u}"
        )
        lbl_s.setObjectName("kvKeyLabel")
        info_l.addWidget(lbl_s)
        h_layout.addLayout(info_l, 1)

        pill_lbl = f"●  {self.cylinder.current_amount:g} {u}"
        pill_bg = "#064E3B" if self.is_in else "#451A03"
        lbl_pill = QLabel(pill_lbl)
        lbl_pill.setStyleSheet(
            f"background-color: {pill_bg}; color: {accent}; border: 1px solid {accent}; "
            f"border-radius: 5px; padding: 4px 10px; font-weight: bold; font-size: 11px;"
        )
        h_layout.addWidget(lbl_pill)

        main_layout.addWidget(header)

        # ── Form Card ──
        card, card_body = _create_dialog_card("Detalle de Consumo, Carga o Recuperación de Gas", accent)
        form = QFormLayout(card_body)
        form.setContentsMargins(16, 14, 16, 16)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.spin_amount = QDoubleSpinBox()
        self.spin_amount.setDecimals(3)
        self.spin_amount.setMinimum(0.01)
        if self.is_in:
            self.spin_amount.setMaximum(100000.0)
            self.spin_amount.setValue(1.0)
        else:
            self.spin_amount.setMaximum(max(0.01, self.cylinder.current_amount))
            self.spin_amount.setValue(min(1.0, max(0.01, self.cylinder.current_amount)))
        self.spin_amount.setSuffix(f" {self.cylinder.unit}")

        lbl_amt = "Cantidad Ingresada / Recuperada *:" if self.is_in else f"Cantidad Utilizada ({self.cylinder.unit}) *:"
        form.addRow(lbl_amt, self.spin_amount)

        self.combo_equipment = QComboBox()
        self.combo_equipment.addItem("(Sin equipo específico / Uso general de taller o soldadura)", ("", ""))
        if self.equipment_service:
            try:
                for eq in self.equipment_service.get_all_equipment():
                    loc = eq.floor_area or eq.location_description or ""
                    ref_spec = eq.technical_specs.get("refrigerant", "") if getattr(eq, "technical_specs", None) else ""
                    ref_txt = f" [{ref_spec}]" if ref_spec else ""
                    lbl = f"{eq.tag}{ref_txt} - {eq.manufacturer} {eq.model_number} ({loc})".strip()
                    self.combo_equipment.addItem(lbl, (eq.id, eq.tag))
            except Exception:
                pass

        eq_label = "Equipo Origen (Recuperación):" if (self.is_in and self.cylinder.gas_category == "RECOVERED") else "Equipo Intervenido (donde se usó):"
        form.addRow(eq_label, self.combo_equipment)

        self.combo_tech = QComboBox()
        self.combo_tech.setEditable(True)
        if self.technician_service:
            try:
                for name in self.technician_service.get_technician_names():
                    self.combo_tech.addItem(name)
            except Exception:
                pass
        form.addRow("Técnico Responsable *:", self.combo_tech)

        self.combo_reason = QComboBox()
        self.combo_reason.setEditable(True)
        if self.is_in:
            if self.cylinder.gas_category == "RECOVERED":
                self.combo_reason.addItems([
                    "Recuperación de Gas Refrigerante desde Equipo",
                    "Vaciado de Circuito para Reparación de Fuga",
                    "Recuperación por Baja Definitiva de Equipo"
                ])
            else:
                self.combo_reason.addItems([
                    "Recarga de Cilindro / Tubo por Proveedor",
                    "Recepción de Cilindro Nuevo en Pañol",
                    "Ajuste de Pesaje / Manómetro (+)"
                ])
        else:
            if self.cylinder.gas_category == "WELDING":
                self.combo_reason.addItems([
                    "Soldadura Fuerte / Oxiacetileno / Map-Pro en Tubería",
                    "Presurización y Prueba de Hermeticidad con Nitrógeno",
                    "Barrido / Soplado de Circuito con Nitrógeno",
                    "Soldadura TIG / Argón"
                ])
            elif self.cylinder.gas_category == "CLEANING":
                self.combo_reason.addItems([
                    "Limpieza / Flushing de Circuito Frigorífico con R-141b",
                    "Descontaminación por Quemadura de Compresor"
                ])
            else:
                self.combo_reason.addItems([
                    "Carga Completa de Gas Refrigerante tras Vacío",
                    "Ajuste de Carga / Recarga Parcial en Equipo",
                    "Recarga post Reparación de Fuga",
                    "Traspaso a Cilindro de Servicio"
                ])
        form.addRow("Trabajo / Motivo *:", self.combo_reason)

        self.txt_wo = QLineEdit()
        self.txt_wo.setPlaceholderText("Ej: OTS-0015, Guía de servicio, Factura...")
        form.addRow("N° OT / Guía / Ref:", self.txt_wo)

        self.txt_notes = QLineEdit()
        self.txt_notes.setPlaceholderText("Presiones registradas, peso en balanza, observaciones...")
        form.addRow("Observaciones:", self.txt_notes)

        main_layout.addWidget(card, 1)

        # ── Footer Bar ──
        footer_bar = QFrame()
        footer_bar.setObjectName("dialogFooterBar")
        btn_layout = QHBoxLayout(footer_bar)
        btn_layout.setContentsMargins(14, 10, 14, 10)
        btn_layout.setSpacing(10)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()

        btn_lbl = "Confirmar Ingreso / Recuperación (+)" if self.is_in else "Registrar Consumo / Carga (-)"
        self.btn_ok = QPushButton(btn_lbl)
        self.btn_ok.setObjectName("successButton" if self.is_in else "primaryButton")
        self.btn_ok.setIcon(IconManager.get_icon(icon_name, "#FFFFFF" if self.is_in else "#000000", 16))
        self.btn_ok.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ok.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.btn_ok)

        main_layout.addWidget(footer_bar)

    def _on_confirm(self):
        amt = self.spin_amount.value()
        if amt <= 0:
            QMessageBox.warning(self, "Cantidad Inválida", "La cantidad debe ser mayor a 0.")
            return
        if not self.is_in and amt > self.cylinder.current_amount:
            QMessageBox.warning(
                self,
                "Contenido Insuficiente",
                f"El cilindro solo dispone de {self.cylinder.current_amount:g} {self.cylinder.unit}."
            )
            return
        self.accept()

    def get_data(self) -> dict:
        eq_data = self.combo_equipment.currentData()
        eq_id, eq_tag = eq_data if isinstance(eq_data, tuple) else ("", "")
        return {
            "cylinder_id": self.cylinder.id,
            "movement_type": self.movement_type,
            "amount": round(self.spin_amount.value(), 3),
            "equipment_id": eq_id,
            "equipment_tag": eq_tag,
            "recipient_type": "TECHNICIAN",
            "recipient_name": self.combo_tech.currentText().strip() or "Técnico",
            "work_order_ref": self.txt_wo.text().strip(),
            "reason": self.combo_reason.currentText().strip(),
            "notes": self.txt_notes.text().strip()
        }
