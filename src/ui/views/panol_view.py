"""
PanolView (Pañol) for ControlHVAC CMMS.
Unifies control of:
1. Insumos de Pañol (Detergente, Paños de limpieza, terminales de manguera, etc.) y entregas a Técnicos, Personal Externo o Recintos.
2. Control de Gases y Cilindros:
   - Gases combustibles y técnicos de soldadura/presurización (Oxígeno, Nitrógeno, Gas Propano, Gas Butano, Argón, etc.) en cilindros (tubos) en m³ o Kg.
   - Gases refrigerantes en cilindros (bombonas): contenido neto inicial, usado en qué equipos y cuántos Kg quedan en Pañol/cilindros.
   - Almacenamiento de gas refrigerante recuperado en Kg.
   - Cantidad de cilindros de Nitrógeno y agente de limpieza (R-141b).
3. Control de EPP (Elementos de Protección Personal):
   - EPP de Entrega / Stock (Guantes, lentes, ropa, calzado de seguridad, casco, bloqueador solar, etc.)
   - EPP por Asignación / Cargo (Arnés de seguridad, líneas de vida, carro y estrobos, polainas y coletos, etc.)
4. Herramientas (Sistema integrado de herramientas de Pañol con asignación/devolución y calibración).
5. Historial General de Movimientos de Pañol.
"""
import html
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableView,
    QPushButton, QLabel, QFrame, QMessageBox, QHeaderView,
    QTabWidget, QComboBox, QListWidget, QListWidgetItem, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor

from src.ui.widgets.search_bar import SearchBar
from src.ui.widgets.stat_card import StatCard
from src.ui.widgets.detail_card import (
    clear_layout_widgets, build_section_card, build_kv_widget,
    build_rich_label, build_status_banner, build_empty_detail_card
)
from src.ui.widgets.table_state_helper import setup_modern_table
from src.ui.icon_manager import IconManager
from src.ui.models.table_models import (
    PanolSupplyTableModel,
    EppDeliveryTableModel,
    EppAssignmentTableModel,
    ToolTableModel,
    PanolMovementTableModel,
    GasCylinderTableModel
)
from src.ui.dialogs.panol_dialogs import (
    PanolSupplyDialog,
    EppItemDialog,
    PanolMovementDialog,
    GasCylinderDialog,
    GasMovementDialog
)
from src.ui.dialogs.tool_dialog import ToolDialog


class PanolView(QWidget):
    def __init__(self, inventory_service, technician_service=None, client_service=None, equipment_service=None, parent=None):
        super().__init__(parent)
        self.inventory_service = inventory_service
        self.technician_service = technician_service
        self.client_service = client_service
        self.equipment_service = equipment_service or getattr(inventory_service, 'equipment_service', None)

        self.supplies = []
        self.gas_cylinders = []
        self.epp_deliveries = []
        self.epp_assignments = []
        self.tools = []
        self.movements = []

        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header + KPI Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_supplies = StatCard("Insumos en Pañol", "0", IconManager.get_icon("tools.svg", "#38BDF8"), accent_color="#38BDF8")
        self.card_gases = StatCard("Cilindros / Gases", "0", IconManager.get_icon("equipment", "#06B6D4"), accent_color="#06B6D4")
        self.card_epp_del = StatCard("EPP de Entrega (Stock)", "0", IconManager.get_icon("check.svg", "#10B981"), accent_color="#10B981")
        self.card_epp_asg = StatCard("EPP Asignados / Cargo", "0 / 0", IconManager.get_icon("technicians", "#F59E0B"), accent_color="#F59E0B")
        self.card_tools = StatCard("Herramientas en Uso", "0 / 0", IconManager.get_icon("tools", "#818CF8"), accent_color="#818CF8")

        stats_layout.addWidget(self.card_supplies)
        stats_layout.addWidget(self.card_gases)
        stats_layout.addWidget(self.card_epp_del)
        stats_layout.addWidget(self.card_epp_asg)
        stats_layout.addWidget(self.card_tools)
        main_layout.addLayout(stats_layout)

        # Main Tabs for Pañol Sections
        self.main_tabs = QTabWidget()
        self.main_tabs.addTab(self._build_supplies_tab(), "🧴 Insumos de Pañol")
        self.main_tabs.addTab(self._build_gases_tab(), "🔥❄️ Control de Gases y Cilindros")
        self.main_tabs.addTab(self._build_epp_delivery_tab(), "🦺 EPP de Entrega (Stock)")
        self.main_tabs.addTab(self._build_epp_assignment_tab(), "🪢 EPP por Asignación (Cargo)")
        self.main_tabs.addTab(self._build_tools_tab(), "🧰 Herramientas")
        self.main_tabs.addTab(self._build_movements_tab(), "📋 Historial de Entregas y Movimientos")

        main_layout.addWidget(self.main_tabs, 1)

    # =========================================================================
    # TAB 1: INSUMOS DE PAÑOL
    # =========================================================================
    def _build_supplies_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search_supply = SearchBar()
        self.search_supply.setPlaceholderText("Buscar insumos (Detergente, paños de limpieza, terminales de manguera, categoría, código)...")
        self.search_supply.textChanged.connect(self._filter_supplies)

        self.btn_sup_in = QPushButton(" Ingreso (+)")
        self.btn_sup_in.setIcon(IconManager.get_icon("arrow_down.svg", "#10B981", 16))
        self.btn_sup_in.setToolTip("Registrar ingreso de insumos al Pañol")
        self.btn_sup_in.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sup_in.clicked.connect(self.on_supply_in)

        self.btn_sup_out = QPushButton(" Entregar Insumo (-)")
        self.btn_sup_out.setIcon(IconManager.get_icon("arrow_up.svg", "#F59E0B", 16))
        self.btn_sup_out.setToolTip("Entregar insumo a un Técnico, Personal Externo o Recinto")
        self.btn_sup_out.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sup_out.clicked.connect(self.on_supply_out)

        self.btn_sup_new = QPushButton(" Nuevo Insumo")
        self.btn_sup_new.setObjectName("primaryButton")
        self.btn_sup_new.setIcon(IconManager.get_icon("add.svg", "#000000", 16))
        self.btn_sup_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_sup_new.clicked.connect(self.on_supply_new)

        toolbar.addWidget(self.search_supply, 1)
        toolbar.addWidget(self.btn_sup_in)
        toolbar.addWidget(self.btn_sup_out)
        toolbar.addWidget(self.btn_sup_new)
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.table_supplies = QTableView()
        self.model_supplies = PanolSupplyTableModel([])
        self.table_supplies.setModel(self.model_supplies)
        self.table_supplies.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_supplies.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_supplies.selectionModel().selectionChanged.connect(self.on_supply_selected)
        self.table_supplies.doubleClicked.connect(lambda idx: self.on_supply_edit())
        splitter.addWidget(self.table_supplies)

        detail = QFrame()
        detail.setObjectName("cardFrame")
        d_layout = QVBoxLayout(detail)
        d_layout.setContentsMargins(14, 14, 14, 14)

        h_row = QHBoxLayout()
        self.lbl_sup_title = QLabel("Seleccione un insumo")
        self.lbl_sup_title.setObjectName("detailTitleLabel")
        h_row.addWidget(self.lbl_sup_title, 1)

        self.btn_sup_edit = QPushButton()
        self.btn_sup_edit.setIcon(IconManager.get_icon("edit.svg", "#F8FAFC", 16))
        self.btn_sup_edit.setFixedSize(34, 34)
        self.btn_sup_edit.setToolTip("Editar Insumo")
        self.btn_sup_edit.setEnabled(False)
        self.btn_sup_edit.clicked.connect(self.on_supply_edit)
        h_row.addWidget(self.btn_sup_edit)

        self.btn_sup_del = QPushButton()
        self.btn_sup_del.setObjectName("dangerButton")
        self.btn_sup_del.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 16))
        self.btn_sup_del.setFixedSize(34, 34)
        self.btn_sup_del.setToolTip("Eliminar Insumo")
        self.btn_sup_del.setEnabled(False)
        self.btn_sup_del.clicked.connect(self.on_supply_delete)
        h_row.addWidget(self.btn_sup_del)
        d_layout.addLayout(h_row)

        self.sup_cards_container = QWidget()
        self.sup_cards_layout = QVBoxLayout(self.sup_cards_container)
        self.sup_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.sup_cards_layout.setSpacing(8)
        d_layout.addWidget(self.sup_cards_container)

        lbl_hist = QLabel("BITÁCORA DE INGRESOS Y ENTREGAS")
        lbl_hist.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; margin-top: 4px;")
        d_layout.addWidget(lbl_hist)

        self.list_sup_movs = QListWidget()
        d_layout.addWidget(self.list_sup_movs, 1)

        splitter.addWidget(detail)
        setup_modern_table(
            self.table_supplies,
            storage=getattr(self.inventory_service, "storage", None),
            settings_key="panol_supplies_table",
            default_widths=[165, 90, 110, 95, 80, 70, 95, 120],
            splitter=splitter,
            default_splitter_sizes=[620, 380],
        )
        layout.addWidget(splitter, 1)
        return w

    # =========================================================================
    # TAB 2: CONTROL DE GASES Y CILINDROS (SOLDADURA, REFRIGERANTES, RECUPERADO, R-141b, NITRÓGENO)
    # =========================================================================
    def _build_gases_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Sub-KPIs for Gases
        gas_summary_frame = QFrame()
        gas_summary_frame.setObjectName("eqStatusBanner")
        gs_layout = QHBoxLayout(gas_summary_frame)
        gs_layout.setContentsMargins(14, 8, 14, 8)
        gs_layout.setSpacing(18)

        self.lbl_gas_ref_summary = QLabel("❄️ <b>Refrigerante Virgen:</b> 0 Kg (0 cilindros)")
        self.lbl_gas_rec_summary = QLabel("♻️ <b>Refrigerante Recuperado:</b> 0 Kg (0 cilindros)")
        self.lbl_gas_nit_summary = QLabel("💨 <b>Cilindros Nitrógeno:</b> 0 tubos")
        self.lbl_gas_clean_summary = QLabel("🧪 <b>Agente Limpieza (R-141b):</b> 0 Kg (0 cilindros)")
        self.lbl_gas_weld_summary = QLabel("🔥 <b>Soldadura (O2/GLP/Argón):</b> 0 tubos")

        for lbl in (
            self.lbl_gas_ref_summary,
            self.lbl_gas_rec_summary,
            self.lbl_gas_nit_summary,
            self.lbl_gas_clean_summary,
            self.lbl_gas_weld_summary
        ):
            lbl.setObjectName("richBodyLabel")
            gs_layout.addWidget(lbl)
        gs_layout.addStretch()
        layout.addWidget(gas_summary_frame)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.search_gas = SearchBar()
        self.search_gas.setPlaceholderText("Buscar cilindro por N° tubo, tipo de gas (Oxígeno, Nitrógeno, Propano, Butano, Argón, R-410A, R-141b)...")
        self.search_gas.textChanged.connect(self._filter_gases)

        self.combo_gas_cat = QComboBox()
        self.combo_gas_cat.addItem("Todas las Categorías de Gases", "")
        self.combo_gas_cat.addItem("❄️ Gases Refrigerantes (Bombonas)", "REFRIGERANT")
        self.combo_gas_cat.addItem("🔥 Gases Soldadura / Presurización (O2, N2, Propano, Butano, Argón)", "WELDING")
        self.combo_gas_cat.addItem("♻️ Gas Refrigerante Recuperado", "RECOVERED")
        self.combo_gas_cat.addItem("🧪 Agente de Limpieza (R-141b)", "CLEANING")
        self.combo_gas_cat.currentIndexChanged.connect(self._filter_gases)

        self.btn_gas_use = QPushButton(" Registrar Uso / Carga en Equipo (-)")
        self.btn_gas_use.setIcon(IconManager.get_icon("arrow_up.svg", "#F59E0B", 16))
        self.btn_gas_use.setToolTip("Descontar Kg o m³ usados en un equipo o soldadura")
        self.btn_gas_use.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_gas_use.clicked.connect(self.on_gas_use)

        self.btn_gas_in = QPushButton(" Recargar / Ingresar Gas Recuperado (+)")
        self.btn_gas_in.setIcon(IconManager.get_icon("arrow_down.svg", "#10B981", 16))
        self.btn_gas_in.setToolTip("Ingresar gas recuperado desde un equipo o recargar cilindro")
        self.btn_gas_in.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_gas_in.clicked.connect(self.on_gas_in)

        self.btn_gas_new = QPushButton(" Nuevo Cilindro / Tubo")
        self.btn_gas_new.setObjectName("primaryButton")
        self.btn_gas_new.setIcon(IconManager.get_icon("add.svg", "#000000", 16))
        self.btn_gas_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_gas_new.clicked.connect(self.on_gas_new)

        toolbar.addWidget(self.search_gas, 2)
        toolbar.addWidget(self.combo_gas_cat, 1)
        toolbar.addWidget(self.btn_gas_use)
        toolbar.addWidget(self.btn_gas_in)
        toolbar.addWidget(self.btn_gas_new)
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.table_gases = QTableView()
        self.model_gases = GasCylinderTableModel([])
        self.table_gases.setModel(self.model_gases)
        self.table_gases.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_gases.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_gases.selectionModel().selectionChanged.connect(self.on_gas_selected)
        self.table_gases.doubleClicked.connect(lambda idx: self.on_gas_edit())
        splitter.addWidget(self.table_gases)

        detail = QFrame()
        detail.setObjectName("cardFrame")
        d_layout = QVBoxLayout(detail)
        d_layout.setContentsMargins(14, 14, 14, 14)

        h_row = QHBoxLayout()
        self.lbl_gas_title = QLabel("Seleccione un cilindro")
        self.lbl_gas_title.setObjectName("detailTitleLabel")
        h_row.addWidget(self.lbl_gas_title, 1)

        self.btn_gas_edit = QPushButton()
        self.btn_gas_edit.setIcon(IconManager.get_icon("edit.svg", "#F8FAFC", 16))
        self.btn_gas_edit.setFixedSize(34, 34)
        self.btn_gas_edit.setEnabled(False)
        self.btn_gas_edit.clicked.connect(self.on_gas_edit)
        h_row.addWidget(self.btn_gas_edit)

        self.btn_gas_del = QPushButton()
        self.btn_gas_del.setObjectName("dangerButton")
        self.btn_gas_del.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 16))
        self.btn_gas_del.setFixedSize(34, 34)
        self.btn_gas_del.setEnabled(False)
        self.btn_gas_del.clicked.connect(self.on_gas_delete)
        h_row.addWidget(self.btn_gas_del)
        d_layout.addLayout(h_row)

        self.gas_cards_container = QWidget()
        self.gas_cards_layout = QVBoxLayout(self.gas_cards_container)
        self.gas_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.gas_cards_layout.setSpacing(8)
        d_layout.addWidget(self.gas_cards_container)

        lbl_h = QLabel("EQUIPOS INTERVENIDOS Y BITÁCORA DEL CILINDRO")
        lbl_h.setStyleSheet("color: #06B6D4; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; margin-top: 4px;")
        d_layout.addWidget(lbl_h)

        self.list_gas_movs = QListWidget()
        d_layout.addWidget(self.list_gas_movs, 1)

        splitter.addWidget(detail)
        setup_modern_table(
            self.table_gases,
            storage=getattr(self.inventory_service, "storage", None),
            settings_key="panol_gases_table",
            default_widths=[125, 150, 125, 110, 115, 110, 145, 130],
            splitter=splitter,
            default_splitter_sizes=[640, 380],
        )
        layout.addWidget(splitter, 1)
        return w

    # =========================================================================
    # TAB 3: EPP DE ENTREGA (STOCK)
    # =========================================================================
    def _build_epp_delivery_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search_epp_del = SearchBar()
        self.search_epp_del.setPlaceholderText("Buscar EPP de entrega (Guantes, lentes, ropa, calzado de seguridad, casco, bloqueador solar)...")
        self.search_epp_del.textChanged.connect(self._filter_epp_delivery)

        self.btn_epp_in = QPushButton(" Ingreso EPP a Pañol (+)")
        self.btn_epp_in.setIcon(IconManager.get_icon("arrow_down.svg", "#10B981", 16))
        self.btn_epp_in.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_epp_in.clicked.connect(self.on_epp_delivery_in)

        self.btn_epp_out = QPushButton(" Entregar EPP (-)")
        self.btn_epp_out.setIcon(IconManager.get_icon("arrow_up.svg", "#F59E0B", 16))
        self.btn_epp_out.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_epp_out.clicked.connect(self.on_epp_delivery_out)

        self.btn_epp_del_new = QPushButton(" Nuevo EPP (Entrega)")
        self.btn_epp_del_new.setObjectName("primaryButton")
        self.btn_epp_del_new.setIcon(IconManager.get_icon("add.svg", "#000000", 16))
        self.btn_epp_del_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_epp_del_new.clicked.connect(lambda: self.on_epp_new("DELIVERY"))

        toolbar.addWidget(self.search_epp_del, 1)
        toolbar.addWidget(self.btn_epp_in)
        toolbar.addWidget(self.btn_epp_out)
        toolbar.addWidget(self.btn_epp_del_new)
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.table_epp_del = QTableView()
        self.model_epp_del = EppDeliveryTableModel([])
        self.table_epp_del.setModel(self.model_epp_del)
        self.table_epp_del.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_epp_del.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_epp_del.selectionModel().selectionChanged.connect(self.on_epp_del_selected)
        self.table_epp_del.doubleClicked.connect(lambda idx: self.on_epp_del_edit())
        splitter.addWidget(self.table_epp_del)

        detail = QFrame()
        detail.setObjectName("cardFrame")
        d_layout = QVBoxLayout(detail)
        d_layout.setContentsMargins(14, 14, 14, 14)

        h_row = QHBoxLayout()
        self.lbl_epp_del_title = QLabel("Seleccione un EPP")
        self.lbl_epp_del_title.setObjectName("detailTitleLabel")
        h_row.addWidget(self.lbl_epp_del_title, 1)

        self.btn_epp_del_edit = QPushButton()
        self.btn_epp_del_edit.setIcon(IconManager.get_icon("edit.svg", "#F8FAFC", 16))
        self.btn_epp_del_edit.setFixedSize(34, 34)
        self.btn_epp_del_edit.setEnabled(False)
        self.btn_epp_del_edit.clicked.connect(self.on_epp_del_edit)
        h_row.addWidget(self.btn_epp_del_edit)

        self.btn_epp_del_delete = QPushButton()
        self.btn_epp_del_delete.setObjectName("dangerButton")
        self.btn_epp_del_delete.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 16))
        self.btn_epp_del_delete.setFixedSize(34, 34)
        self.btn_epp_del_delete.setEnabled(False)
        self.btn_epp_del_delete.clicked.connect(self.on_epp_del_delete)
        h_row.addWidget(self.btn_epp_del_delete)
        d_layout.addLayout(h_row)

        self.epp_del_cards_container = QWidget()
        self.epp_del_cards_layout = QVBoxLayout(self.epp_del_cards_container)
        self.epp_del_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.epp_del_cards_layout.setSpacing(8)
        d_layout.addWidget(self.epp_del_cards_container)

        lbl_h = QLabel("HISTORIAL DE INGRESOS Y ENTREGAS DE EPP")
        lbl_h.setStyleSheet("color: #10B981; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; margin-top: 4px;")
        d_layout.addWidget(lbl_h)

        self.list_epp_del_movs = QListWidget()
        d_layout.addWidget(self.list_epp_del_movs, 1)

        splitter.addWidget(detail)
        setup_modern_table(
            self.table_epp_del,
            storage=getattr(self.inventory_service, "storage", None),
            settings_key="panol_epp_delivery_table",
            default_widths=[165, 90, 115, 110, 100, 110, 80, 100],
            splitter=splitter,
            default_splitter_sizes=[620, 380],
        )
        layout.addWidget(splitter, 1)
        return w

    # =========================================================================
    # TAB 4: EPP POR ASIGNACIÓN (CARGO RETORNABLE)
    # =========================================================================
    def _build_epp_assignment_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search_epp_asg = SearchBar()
        self.search_epp_asg.setPlaceholderText("Buscar EPP por asignación (Arnés de seguridad, líneas de vida, carro y estrobos, polainas y coletos)...")
        self.search_epp_asg.textChanged.connect(self._filter_epp_assignment)

        self.btn_epp_assign = QPushButton(" Asignar a Técnico / Externo / Recinto")
        self.btn_epp_assign.setIcon(IconManager.get_icon("arrow_up.svg", "#38BDF8", 16))
        self.btn_epp_assign.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_epp_assign.clicked.connect(self.on_epp_assign)

        self.btn_epp_return = QPushButton(" Recepcionar / Devolver a Pañol")
        self.btn_epp_return.setIcon(IconManager.get_icon("arrow_down.svg", "#10B981", 16))
        self.btn_epp_return.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_epp_return.clicked.connect(self.on_epp_return)

        self.btn_epp_asg_new = QPushButton(" Nuevo EPP de Cargo")
        self.btn_epp_asg_new.setObjectName("primaryButton")
        self.btn_epp_asg_new.setIcon(IconManager.get_icon("add.svg", "#000000", 16))
        self.btn_epp_asg_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_epp_asg_new.clicked.connect(lambda: self.on_epp_new("ASSIGNMENT"))

        toolbar.addWidget(self.search_epp_asg, 1)
        toolbar.addWidget(self.btn_epp_assign)
        toolbar.addWidget(self.btn_epp_return)
        toolbar.addWidget(self.btn_epp_asg_new)
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.table_epp_asg = QTableView()
        self.model_epp_asg = EppAssignmentTableModel([])
        self.table_epp_asg.setModel(self.model_epp_asg)
        self.table_epp_asg.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_epp_asg.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_epp_asg.selectionModel().selectionChanged.connect(self.on_epp_asg_selected)
        self.table_epp_asg.doubleClicked.connect(lambda idx: self.on_epp_asg_edit())
        splitter.addWidget(self.table_epp_asg)

        detail = QFrame()
        detail.setObjectName("cardFrame")
        d_layout = QVBoxLayout(detail)
        d_layout.setContentsMargins(14, 14, 14, 14)

        h_row = QHBoxLayout()
        self.lbl_epp_asg_title = QLabel("Seleccione un equipo EPP")
        self.lbl_epp_asg_title.setObjectName("detailTitleLabel")
        h_row.addWidget(self.lbl_epp_asg_title, 1)

        self.btn_epp_asg_edit = QPushButton()
        self.btn_epp_asg_edit.setIcon(IconManager.get_icon("edit.svg", "#F8FAFC", 16))
        self.btn_epp_asg_edit.setFixedSize(34, 34)
        self.btn_epp_asg_edit.setEnabled(False)
        self.btn_epp_asg_edit.clicked.connect(self.on_epp_asg_edit)
        h_row.addWidget(self.btn_epp_asg_edit)

        self.btn_epp_asg_delete = QPushButton()
        self.btn_epp_asg_delete.setObjectName("dangerButton")
        self.btn_epp_asg_delete.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 16))
        self.btn_epp_asg_delete.setFixedSize(34, 34)
        self.btn_epp_asg_delete.setEnabled(False)
        self.btn_epp_asg_delete.clicked.connect(self.on_epp_asg_delete)
        h_row.addWidget(self.btn_epp_asg_delete)
        d_layout.addLayout(h_row)

        self.epp_asg_cards_container = QWidget()
        self.epp_asg_cards_layout = QVBoxLayout(self.epp_asg_cards_container)
        self.epp_asg_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.epp_asg_cards_layout.setSpacing(8)
        d_layout.addWidget(self.epp_asg_cards_container)

        lbl_h = QLabel("HISTORIAL DE ASIGNACIONES Y DEVOLUCIONES")
        lbl_h.setStyleSheet("color: #F59E0B; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; margin-top: 4px;")
        d_layout.addWidget(lbl_h)

        self.list_epp_asg_movs = QListWidget()
        d_layout.addWidget(self.list_epp_asg_movs, 1)

        splitter.addWidget(detail)
        setup_modern_table(
            self.table_epp_asg,
            storage=getattr(self.inventory_service, "storage", None),
            settings_key="panol_epp_assignment_table",
            default_widths=[160, 100, 115, 115, 145, 130, 110, 110],
            splitter=splitter,
            default_splitter_sizes=[620, 380],
        )
        layout.addWidget(splitter, 1)
        return w

    # =========================================================================
    # TAB 5: HERRAMIENTAS DE PAÑOL (INTEGRADO)
    # =========================================================================
    def _build_tools_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search_tool = SearchBar()
        self.search_tool.setPlaceholderText("Buscar herramientas por nombre, marca, modelo, serie, técnico asignado...")
        self.search_tool.textChanged.connect(self._filter_tools)

        self.btn_tool_assign = QPushButton(" Entregar / Asignar Herramienta")
        self.btn_tool_assign.setIcon(IconManager.get_icon("arrow_up.svg", "#38BDF8", 16))
        self.btn_tool_assign.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tool_assign.clicked.connect(self.on_tool_assign)

        self.btn_tool_return = QPushButton(" Devolver a Pañol")
        self.btn_tool_return.setIcon(IconManager.get_icon("arrow_down.svg", "#10B981", 16))
        self.btn_tool_return.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tool_return.clicked.connect(self.on_tool_return)

        self.btn_tool_new = QPushButton(" Nueva Herramienta")
        self.btn_tool_new.setObjectName("primaryButton")
        self.btn_tool_new.setIcon(IconManager.get_icon("add.svg", "#000000", 16))
        self.btn_tool_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_tool_new.clicked.connect(self.on_tool_new)

        toolbar.addWidget(self.search_tool, 1)
        toolbar.addWidget(self.btn_tool_assign)
        toolbar.addWidget(self.btn_tool_return)
        toolbar.addWidget(self.btn_tool_new)
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.table_tools = QTableView()
        self.model_tools = ToolTableModel([])
        self.table_tools.setModel(self.model_tools)
        self.table_tools.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_tools.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table_tools.selectionModel().selectionChanged.connect(self.on_tool_selected)
        self.table_tools.doubleClicked.connect(lambda idx: self.on_tool_edit())
        splitter.addWidget(self.table_tools)

        detail = QFrame()
        detail.setObjectName("cardFrame")
        d_layout = QVBoxLayout(detail)
        d_layout.setContentsMargins(14, 14, 14, 14)

        h_row = QHBoxLayout()
        self.lbl_tool_title = QLabel("Seleccione una herramienta")
        self.lbl_tool_title.setObjectName("detailTitleLabel")
        h_row.addWidget(self.lbl_tool_title, 1)

        self.btn_tool_edit = QPushButton()
        self.btn_tool_edit.setIcon(IconManager.get_icon("edit.svg", "#F8FAFC", 16))
        self.btn_tool_edit.setFixedSize(34, 34)
        self.btn_tool_edit.setEnabled(False)
        self.btn_tool_edit.clicked.connect(self.on_tool_edit)
        h_row.addWidget(self.btn_tool_edit)

        self.btn_tool_delete = QPushButton()
        self.btn_tool_delete.setObjectName("dangerButton")
        self.btn_tool_delete.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 16))
        self.btn_tool_delete.setFixedSize(34, 34)
        self.btn_tool_delete.setEnabled(False)
        self.btn_tool_delete.clicked.connect(self.on_tool_delete)
        h_row.addWidget(self.btn_tool_delete)
        d_layout.addLayout(h_row)

        self.tool_cards_container = QWidget()
        self.tool_cards_layout = QVBoxLayout(self.tool_cards_container)
        self.tool_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.tool_cards_layout.setSpacing(8)
        d_layout.addWidget(self.tool_cards_container)

        lbl_h = QLabel("HISTORIAL DE PRÉSTAMOS Y DEVOLUCIONES")
        lbl_h.setStyleSheet("color: #818CF8; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; margin-top: 4px;")
        d_layout.addWidget(lbl_h)

        self.list_tool_movs = QListWidget()
        d_layout.addWidget(self.list_tool_movs, 1)

        splitter.addWidget(detail)
        setup_modern_table(
            self.table_tools,
            storage=getattr(self.inventory_service, "storage", None),
            settings_key="panol_tools_table",
            default_widths=[165, 110, 110, 105, 140, 130, 110],
            splitter=splitter,
            default_splitter_sizes=[620, 380],
        )
        layout.addWidget(splitter, 1)
        return w

    # =========================================================================
    # TAB 6: HISTORIAL UNIFICADO DE PAÑOL
    # =========================================================================
    def _build_movements_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search_movs = SearchBar()
        self.search_movs.setPlaceholderText("Filtrar historial por insumo, gas, EPP, herramienta, técnico, externo, equipo o recinto...")
        self.search_movs.textChanged.connect(self._filter_movements)

        self.combo_mov_cat = QComboBox()
        self.combo_mov_cat.addItem("Todas las Secciones", "")
        self.combo_mov_cat.addItem("🧴 Insumos", "SUPPLY")
        self.combo_mov_cat.addItem("🔥❄️ Gases / Cilindros", "GAS")
        self.combo_mov_cat.addItem("🦺 EPP de Entrega", "EPP_DELIVERY")
        self.combo_mov_cat.addItem("🪢 EPP por Asignación", "EPP_ASSIGNMENT")
        self.combo_mov_cat.addItem("🧰 Herramientas", "TOOL")
        self.combo_mov_cat.currentIndexChanged.connect(self._filter_movements)

        self.combo_mov_rec = QComboBox()
        self.combo_mov_rec.addItem("Todos los Destinatarios", "")
        self.combo_mov_rec.addItem("👷 Técnicos Internos", "TECHNICIAN")
        self.combo_mov_rec.addItem("🧑‍🔧 Personal Externo", "EXTERNAL")
        self.combo_mov_rec.addItem("🏢 Recintos / Sedes", "SITE")
        self.combo_mov_rec.currentIndexChanged.connect(self._filter_movements)

        toolbar.addWidget(self.search_movs, 2)
        toolbar.addWidget(self.combo_mov_cat, 1)
        toolbar.addWidget(self.combo_mov_rec, 1)
        layout.addLayout(toolbar)

        self.table_movs = QTableView()
        self.model_movs = PanolMovementTableModel([])
        self.table_movs.setModel(self.model_movs)
        self.table_movs.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_movs.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        setup_modern_table(
            self.table_movs,
            storage=getattr(self.inventory_service, "storage", None),
            settings_key="panol_movements_table",
            default_widths=[130, 115, 130, 185, 85, 145, 120, 185, 115],
        )
        layout.addWidget(self.table_movs, 1)
        return w

    # =========================================================================
    # REFRESH & FILTERS
    # =========================================================================
    def refresh_data(self):
        try:
            self.supplies = self.inventory_service.get_all_supplies()
            self.gas_cylinders = self.inventory_service.get_all_gas_cylinders()
            self.epp_deliveries = self.inventory_service.get_all_epp("DELIVERY")
            self.epp_assignments = self.inventory_service.get_all_epp("ASSIGNMENT")
            self.tools = self.inventory_service.get_all_tools()
            self.movements = self.inventory_service.get_panol_movements()

            self._filter_supplies()
            self._filter_gases()
            self._filter_epp_delivery()
            self._filter_epp_assignment()
            self._filter_tools()
            self._filter_movements()
            self._update_stats()

            self.on_supply_selected()
            self.on_gas_selected()
            self.on_epp_del_selected()
            self.on_epp_asg_selected()
            self.on_tool_selected()
        except Exception as e:
            print(f"Error refreshing PanolView: {e}")

    def _update_stats(self):
        low_sup = sum(1 for s in self.supplies if s.quantity <= s.minimum_quantity)
        self.card_supplies.set_value(f"{len(self.supplies)} ({low_sup} bajo mín.)" if low_sup else str(len(self.supplies)))

        active_cyl = sum(1 for c in self.gas_cylinders if c.status not in ("EMPTY", "RETURNED"))
        self.card_gases.set_value(f"{active_cyl} activos / {len(self.gas_cylinders)}")

        # Sub-KPIs for Gases tab
        ref_cyls = [c for c in self.gas_cylinders if c.gas_category == "REFRIGERANT" and c.status != "RETURNED"]
        ref_kg = sum(c.current_amount for c in ref_cyls)
        self.lbl_gas_ref_summary.setText(f"❄️ <b>Refrigerante en Pañol:</b> {ref_kg:g} Kg ({len(ref_cyls)} cilindros)")

        rec_cyls = [c for c in self.gas_cylinders if c.gas_category == "RECOVERED" and c.status != "RETURNED"]
        rec_kg = sum(c.current_amount for c in rec_cyls)
        self.lbl_gas_rec_summary.setText(f"♻️ <b>Refrigerante Recuperado:</b> {rec_kg:g} Kg ({len(rec_cyls)} cilindros)")

        nit_cyls = [c for c in self.gas_cylinders if "nitr" in (c.gas_type or "").lower() and c.status != "RETURNED"]
        self.lbl_gas_nit_summary.setText(f"💨 <b>Cilindros Nitrógeno:</b> {len(nit_cyls)} tubos")

        clean_cyls = [c for c in self.gas_cylinders if (c.gas_category == "CLEANING" or "141" in (c.gas_type or "").lower()) and c.status != "RETURNED"]
        clean_kg = sum(c.current_amount for c in clean_cyls)
        self.lbl_gas_clean_summary.setText(f"🧪 <b>Agente Limpieza (R-141b):</b> {clean_kg:g} Kg ({len(clean_cyls)} cilindros)")

        weld_cyls = [c for c in self.gas_cylinders if c.gas_category == "WELDING" and "nitr" not in (c.gas_type or "").lower() and c.status != "RETURNED"]
        self.lbl_gas_weld_summary.setText(f"🔥 <b>Soldadura (O2/GLP/Argón):</b> {len(weld_cyls)} tubos")

        low_epp = sum(1 for e in self.epp_deliveries if e.quantity <= e.minimum_quantity)
        self.card_epp_del.set_value(f"{len(self.epp_deliveries)} ({low_epp} bajo mín.)" if low_epp else str(len(self.epp_deliveries)))

        asg_count = sum(1 for e in self.epp_assignments if e.status == "ASSIGNED")
        self.card_epp_asg.set_value(f"{asg_count} / {len(self.epp_assignments)}")

        in_use = sum(1 for t in self.tools if (t.status.value if hasattr(t.status, 'value') else str(t.status)) == "IN_USE")
        self.card_tools.set_value(f"{in_use} / {len(self.tools)}")

    def _filter_supplies(self):
        q = self.search_supply.text().strip().lower()
        if not q:
            self.model_supplies.set_data(self.supplies)
            return
        filtered = [
            s for s in self.supplies
            if q in (s.name or "").lower() or
               q in (s.code or "").lower() or
               q in (s.category or "").lower() or
               q in (s.supplier or "").lower() or
               q in (s.location or "").lower()
        ]
        self.model_supplies.set_data(filtered)

    def _filter_gases(self):
        q = self.search_gas.text().strip().lower()
        cat = self.combo_gas_cat.currentData()
        res = self.gas_cylinders
        if cat:
            res = [c for c in res if c.gas_category == cat]
        if q:
            res = [
                c for c in res
                if q in (c.code or "").lower() or
                   q in (c.gas_type or "").lower() or
                   q in (c.assigned_to or "").lower() or
                   q in (c.location or "").lower()
            ]
        self.model_gases.set_data(res)

    def _filter_epp_delivery(self):
        q = self.search_epp_del.text().strip().lower()
        if not q:
            self.model_epp_del.set_data(self.epp_deliveries)
            return
        filtered = [
            e for e in self.epp_deliveries
            if q in (e.name or "").lower() or
               q in (e.code or "").lower() or
               q in (e.category or "").lower() or
               q in (e.brand or "").lower() or
               q in (e.size_or_model or "").lower()
        ]
        self.model_epp_del.set_data(filtered)

    def _filter_epp_assignment(self):
        q = self.search_epp_asg.text().strip().lower()
        if not q:
            self.model_epp_asg.set_data(self.epp_assignments)
            return
        filtered = [
            e for e in self.epp_assignments
            if q in (e.name or "").lower() or
               q in (e.code or "").lower() or
               q in (e.serial_number or "").lower() or
               q in (e.category or "").lower() or
               q in (e.assigned_to or "").lower() or
               q in (e.brand or "").lower()
        ]
        self.model_epp_asg.set_data(filtered)

    def _filter_tools(self):
        q = self.search_tool.text().strip().lower()
        if not q:
            self.model_tools.set_data(self.tools)
            return
        filtered = [
            t for t in self.tools
            if q in (t.name or "").lower() or
               q in (t.brand or "").lower() or
               q in (t.model or "").lower() or
               q in (t.serial_number or "").lower() or
               q in (getattr(t, 'assigned_to', '') or "").lower()
        ]
        self.model_tools.set_data(filtered)

    def _filter_movements(self):
        q = self.search_movs.text().strip().lower()
        cat = self.combo_mov_cat.currentData()
        rtype = self.combo_mov_rec.currentData()

        res = self.movements
        if cat:
            res = [m for m in res if m.item_category == cat]
        if rtype:
            res = [m for m in res if m.recipient_type == rtype]
        if q:
            res = [
                m for m in res
                if q in (m.item_name or "").lower() or
                   q in (m.item_code or "").lower() or
                   q in (m.recipient_name or "").lower() or
                   q in (m.reason or "").lower() or
                   q in (m.reference or "").lower()
            ]
        self.model_movs.set_data(res)

    def _populate_item_movements_list(self, list_widget: QListWidget, item_id: str):
        list_widget.clear()
        movs = self.inventory_service.get_panol_movements(item_id=item_id)
        if not movs:
            item = QListWidgetItem("Sin movimientos registrados.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            list_widget.addItem(item)
            return

        rt_map = {
            "TECHNICIAN": "Técnico",
            "EXTERNAL": "Externo",
            "SITE": "Recinto"
        }

        for m in movs[:30]:
            mtype = (m.movement_type or "IN").upper()
            if mtype == "IN":
                badge = "🟢 INGRESO"
                qty_str = f"+{m.quantity} {m.unit}"
            elif mtype == "RETURN":
                badge = "🟢 DEVOLUCIÓN"
                qty_str = f"+{m.quantity} {m.unit}"
            elif mtype == "ASSIGN":
                badge = "🔵 ASIGNADO"
                qty_str = f"{m.quantity} {m.unit}"
            else:
                badge = "🟠 ENTREGA"
                qty_str = f"-{m.quantity} {m.unit}"

            dt_str = (m.date or "")[:16].replace("T", " ")
            rt_lbl = rt_map.get(m.recipient_type, "")
            rec_str = f"{m.recipient_name} ({rt_lbl})" if (m.recipient_name and rt_lbl) else (m.recipient_name or "")
            ref_str = f" | Ref: {m.reference}" if m.reference else ""
            note_str = f" | Nota: {m.notes}" if m.notes else ""

            text = f"{badge} {qty_str} — {dt_str}\n    Destinatario: {rec_str or 'Pañol'} | {m.reason}{ref_str}{note_str}"
            list_widget.addItem(QListWidgetItem(text))

    # =========================================================================
    # HANDLERS: INSUMOS
    # =========================================================================
    def _get_selected_supply(self):
        idxs = self.table_supplies.selectionModel().selectedRows()
        return self.model_supplies.get_item(idxs[0].row()) if idxs else None

    def on_supply_selected(self):
        s = self._get_selected_supply()
        clear_layout_widgets(self.sup_cards_layout)
        if not s:
            self.lbl_sup_title.setText("Seleccione un insumo")
            self.sup_cards_layout.addWidget(
                build_empty_detail_card("Haga clic en un insumo de la tabla para ver su stock disponible, ubicación e historial de entregas.")
            )
            self.btn_sup_edit.setEnabled(False)
            self.btn_sup_del.setEnabled(False)
            self.list_sup_movs.clear()
            return

        self.lbl_sup_title.setText(s.name)
        self.btn_sup_edit.setEnabled(True)
        self.btn_sup_del.setEnabled(True)

        if s.quantity <= 0:
            st_lbl, st_fg, st_bg = f"Agotado (0 {s.unit})", "#EF4444", "#450A0A"
        elif s.quantity <= s.minimum_quantity:
            st_lbl, st_fg, st_bg = f"Stock Bajo ({s.quantity} {s.unit})", "#F59E0B", "#451A03"
        else:
            st_lbl, st_fg, st_bg = f"Disponible ({s.quantity} {s.unit})", "#10B981", "#064E3B"

        self.sup_cards_layout.addWidget(
            build_status_banner([
                ("STOCK EN PAÑOL", st_lbl, st_fg, st_bg),
                ("STOCK MÍNIMO", f"{s.minimum_quantity} {s.unit}", "#38BDF8", "#0C4A6E"),
            ])
        )

        rows = [
            ("Código", f"<b style='color: #38BDF8;'>{html.escape(s.code or 'N/A')}</b>"),
            ("Categoría", html.escape(s.category or "General")),
            ("Ubicación", html.escape(s.location or "Pañol")),
            ("Proveedor", html.escape(s.supplier or "N/A")),
        ]
        if s.notes:
            rows.append(("Notas", html.escape(s.notes)))

        self.sup_cards_layout.addWidget(
            build_section_card("Ficha del Insumo", "#38BDF8", build_kv_widget(rows))
        )
        self._populate_item_movements_list(self.list_sup_movs, s.id)

    def on_supply_new(self):
        dlg = PanolSupplyDialog(self)
        if dlg.exec():
            s = dlg.get_supply()
            self.inventory_service.save_supply(s)
            if s.quantity > 0:
                self.inventory_service.record_panol_movement(
                    self._build_initial_movement(s.id, s.name, s.code, "SUPPLY", s.quantity, s.unit)
                )
            self.refresh_data()

    def on_supply_edit(self):
        s = self._get_selected_supply()
        if not s:
            return
        dlg = PanolSupplyDialog(self, supply=s)
        if dlg.exec():
            self.inventory_service.save_supply(dlg.get_supply())
            self.refresh_data()

    def on_supply_delete(self):
        s = self._get_selected_supply()
        if not s:
            return
        if QMessageBox.question(self, "Eliminar Insumo", f"¿Enviar el insumo '{s.name}' a la papelera?") == QMessageBox.StandardButton.Yes:
            self.inventory_service.delete_supply(s.id)
            self.refresh_data()

    def on_supply_in(self):
        s = self._get_selected_supply()
        if not s:
            QMessageBox.information(self, "Ingreso de Insumo", "Seleccione un insumo de la tabla para ingresar stock.")
            return
        dlg = PanolMovementDialog(
            item_name=s.name,
            current_stock=s.quantity,
            unit=s.unit,
            operation="IN",
            item_category="SUPPLY",
            technician_service=self.technician_service,
            client_service=self.client_service,
            parent=self
        )
        if dlg.exec():
            d = dlg.get_data()
            self.inventory_service.register_supply_movement(
                supply_id=s.id,
                movement_type="IN",
                **d
            )
            self.refresh_data()

    def on_supply_out(self):
        s = self._get_selected_supply()
        if not s:
            QMessageBox.information(self, "Entrega de Insumo", "Seleccione un insumo de la tabla para registrar su entrega.")
            return
        if s.quantity <= 0:
            QMessageBox.warning(self, "Sin Stock", f"El insumo '{s.name}' no tiene stock disponible en Pañol.")
            return
        dlg = PanolMovementDialog(
            item_name=s.name,
            current_stock=s.quantity,
            unit=s.unit,
            operation="OUT",
            item_category="SUPPLY",
            technician_service=self.technician_service,
            client_service=self.client_service,
            parent=self
        )
        if dlg.exec():
            d = dlg.get_data()
            self.inventory_service.register_supply_movement(
                supply_id=s.id,
                movement_type="OUT",
                **d
            )
            self.refresh_data()

    # =========================================================================
    # HANDLERS: CONTROL DE GASES Y CILINDROS
    # =========================================================================
    def _get_selected_gas(self):
        idxs = self.table_gases.selectionModel().selectedRows()
        return self.model_gases.get_item(idxs[0].row()) if idxs else None

    def on_gas_selected(self):
        c = self._get_selected_gas()
        clear_layout_widgets(self.gas_cards_layout)
        if not c:
            self.lbl_gas_title.setText("Seleccione un cilindro")
            self.gas_cards_layout.addWidget(
                build_empty_detail_card("Seleccione un cilindro o bombona para ver su contenido neto, cuánto se ha usado en equipos y el saldo restante.")
            )
            self.btn_gas_edit.setEnabled(False)
            self.btn_gas_del.setEnabled(False)
            self.list_gas_movs.clear()
            return

        self.lbl_gas_title.setText(f"{c.gas_type} ({c.code})")
        self.btn_gas_edit.setEnabled(True)
        self.btn_gas_del.setEnabled(True)

        u = c.unit or "Kg"
        cat_labels = {
            "WELDING": "Gas de Soldadura / Presurización",
            "REFRIGERANT": "Gas Refrigerante en Bombona",
            "RECOVERED": "Refrigerante Recuperado",
            "CLEANING": "Agente Limpieza (R-141b)"
        }
        st_map = {
            "AVAILABLE": ("En Pañol", "#10B981", "#064E3B"),
            "IN_USE": ("En Terreno / Uso", "#F59E0B", "#451A03"),
            "EMPTY": ("Vacío", "#EF4444", "#450A0A"),
            "RETURNED": ("Devuelto", "#94A3B8", "#1E293B")
        }
        st_lbl, st_fg, st_bg = st_map.get((c.status or "AVAILABLE").upper(), ("En Pañol", "#10B981", "#064E3B"))
        rem_fg = "#EF4444" if (c.gas_category != "RECOVERED" and c.current_amount <= 0) else "#06B6D4"

        self.gas_cards_layout.addWidget(
            build_status_banner([
                ("ESTADO CILINDRO", st_lbl, st_fg, st_bg),
                ("QUEDA EN CILINDRO", f"{c.current_amount:g} {u}", rem_fg, "#083344"),
            ])
        )

        rows = [
            ("N° Cilindro / Tubo", f"<b style='color: #06B6D4;'>{html.escape(c.code or 'N/A')}</b>"),
            ("Categoría", html.escape(cat_labels.get(c.gas_category, c.gas_category))),
            ("Tipo de Gas", f"<b>{html.escape(c.gas_type or '')}</b>"),
            ("Contenido Neto Inicial", f"{c.initial_amount:g} {html.escape(u)}"),
            (
                "Total Usado / Consumido" if c.gas_category != "RECOVERED" else "Total Recuperado",
                f"<b style='color: #F59E0B;'>{c.used_amount:g} {html.escape(u)}</b>"
                if c.gas_category != "RECOVERED"
                else f"<b style='color: #10B981;'>{c.current_amount:g} {html.escape(u)}</b>"
            ),
            ("Ubicación / Asignado", html.escape(c.assigned_to or c.location or "Pañol")),
        ]
        if c.tare_weight_kg > 0:
            rows.append(("Peso Tara Vacío", f"{c.tare_weight_kg:g} Kg"))
        if c.notes:
            rows.append(("Notas", html.escape(c.notes)))

        self.gas_cards_layout.addWidget(
            build_section_card("Especificaciones del Cilindro", "#06B6D4", build_kv_widget(rows))
        )

        # Populate gas usage history with equipment tags
        self.list_gas_movs.clear()
        g_movs = self.inventory_service.get_gas_movements(cylinder_id=c.id)
        if not g_movs:
            item = QListWidgetItem("Sin consumos ni cargas registradas para este cilindro.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_gas_movs.addItem(item)
            return

        for gm in g_movs[:40]:
            is_in = (gm.movement_type == "IN")
            badge = "🟢 INGRESO / RECUPERACIÓN" if is_in else "🟠 USO / CARGA"
            sign = "+" if is_in else "-"
            dt_str = (gm.date or "")[:16].replace("T", " ")
            eq_txt = f"Equipo: {gm.equipment_tag}" if gm.equipment_tag else "Uso General / Taller"
            wo_txt = f" | OT/Ref: {gm.work_order_ref}" if gm.work_order_ref else ""
            tech_txt = f" | Técnico: {gm.recipient_name}" if gm.recipient_name else ""
            rem_txt = f" (Quedó: {gm.remaining_after:g} {gm.unit})"

            txt = f"{badge} {sign}{gm.amount:g} {gm.unit}{rem_txt} — {dt_str}\n    ⚙️ {eq_txt}{tech_txt}{wo_txt} | {gm.reason}"
            self.list_gas_movs.addItem(QListWidgetItem(txt))

    def on_gas_new(self):
        default_cat = self.combo_gas_cat.currentData() or "REFRIGERANT"
        dlg = GasCylinderDialog(self, default_category=default_cat)
        if dlg.exec():
            cyl = dlg.get_cylinder()
            self.inventory_service.save_gas_cylinder(cyl)
            self.refresh_data()

    def on_gas_edit(self):
        c = self._get_selected_gas()
        if not c:
            return
        dlg = GasCylinderDialog(self, cylinder=c)
        if dlg.exec():
            self.inventory_service.save_gas_cylinder(dlg.get_cylinder())
            self.refresh_data()

    def on_gas_delete(self):
        c = self._get_selected_gas()
        if not c:
            return
        if QMessageBox.question(self, "Eliminar Cilindro", f"¿Enviar el cilindro '{c.code} ({c.gas_type})' a la papelera?") == QMessageBox.StandardButton.Yes:
            self.inventory_service.delete_gas_cylinder(c.id)
            self.refresh_data()

    def on_gas_use(self):
        c = self._get_selected_gas()
        if not c:
            QMessageBox.information(self, "Uso / Carga de Gas", "Seleccione un cilindro o bombona de la tabla para descontar gas usado.")
            return
        if c.current_amount <= 0:
            QMessageBox.warning(self, "Cilindro Vacío", f"El cilindro '{c.code}' no tiene contenido disponible (0 {c.unit}).")
            return
        dlg = GasMovementDialog(
            cylinder=c,
            movement_type="OUT",
            equipment_service=self.equipment_service,
            technician_service=self.technician_service,
            parent=self
        )
        if dlg.exec():
            d = dlg.get_data()
            self.inventory_service.register_gas_movement(**d)
            self.refresh_data()

    def on_gas_in(self):
        c = self._get_selected_gas()
        if not c:
            QMessageBox.information(self, "Ingreso / Recuperación de Gas", "Seleccione un cilindro de la tabla para recargarlo o almacenar gas refrigerante recuperado.")
            return
        dlg = GasMovementDialog(
            cylinder=c,
            movement_type="IN",
            equipment_service=self.equipment_service,
            technician_service=self.technician_service,
            parent=self
        )
        if dlg.exec():
            d = dlg.get_data()
            self.inventory_service.register_gas_movement(**d)
            self.refresh_data()

    # =========================================================================
    # HANDLERS: EPP DE ENTREGA (STOCK)
    # =========================================================================
    def _get_selected_epp_del(self):
        idxs = self.table_epp_del.selectionModel().selectedRows()
        return self.model_epp_del.get_item(idxs[0].row()) if idxs else None

    def on_epp_del_selected(self):
        e = self._get_selected_epp_del()
        clear_layout_widgets(self.epp_del_cards_layout)
        if not e:
            self.lbl_epp_del_title.setText("Seleccione un EPP")
            self.epp_del_cards_layout.addWidget(
                build_empty_detail_card("Seleccione un elemento EPP para ver su ficha técnica, talla y entregas registradas.")
            )
            self.btn_epp_del_edit.setEnabled(False)
            self.btn_epp_del_delete.setEnabled(False)
            self.list_epp_del_movs.clear()
            return

        self.lbl_epp_del_title.setText(e.name)
        self.btn_epp_del_edit.setEnabled(True)
        self.btn_epp_del_delete.setEnabled(True)

        if e.quantity <= 0:
            st_lbl, st_fg, st_bg = f"Sin Stock (0 {e.unit})", "#EF4444", "#450A0A"
        elif e.quantity <= e.minimum_quantity:
            st_lbl, st_fg, st_bg = f"Stock Bajo ({e.quantity} {e.unit})", "#F59E0B", "#451A03"
        else:
            st_lbl, st_fg, st_bg = f"Disponible ({e.quantity} {e.unit})", "#10B981", "#064E3B"

        self.epp_del_cards_layout.addWidget(
            build_status_banner([
                ("STOCK EPP", st_lbl, st_fg, st_bg),
                ("TALLA / MODELO", e.size_or_model or "Estándar", "#38BDF8", "#0C4A6E"),
            ])
        )

        rows = [
            ("Código", f"<b style='color: #10B981;'>{html.escape(e.code or 'N/A')}</b>"),
            ("Categoría", html.escape(e.category or "EPP")),
            ("Marca", html.escape(e.brand or "-")),
            ("Ubicación", html.escape(e.location or "Pañol")),
        ]
        if e.expiration_date:
            rows.append(("Vencimiento / Cert.", html.escape(e.expiration_date)))
        if e.notes:
            rows.append(("Notas", html.escape(e.notes)))

        self.epp_del_cards_layout.addWidget(
            build_section_card("Ficha de EPP de Entrega", "#10B981", build_kv_widget(rows))
        )
        self._populate_item_movements_list(self.list_epp_del_movs, e.id)

    def on_epp_new(self, default_type: str = "DELIVERY"):
        dlg = EppItemDialog(self, default_epp_type=default_type)
        if dlg.exec():
            e = dlg.get_epp()
            self.inventory_service.save_epp(e)
            if e.epp_type == "DELIVERY" and e.quantity > 0:
                self.inventory_service.record_panol_movement(
                    self._build_initial_movement(e.id, e.name, e.code, "EPP_DELIVERY", e.quantity, e.unit)
                )
            self.refresh_data()

    def on_epp_del_edit(self):
        e = self._get_selected_epp_del()
        if not e:
            return
        dlg = EppItemDialog(self, epp=e)
        if dlg.exec():
            self.inventory_service.save_epp(dlg.get_epp())
            self.refresh_data()

    def on_epp_del_delete(self):
        e = self._get_selected_epp_del()
        if not e:
            return
        if QMessageBox.question(self, "Eliminar EPP", f"¿Enviar '{e.name}' a la papelera?") == QMessageBox.StandardButton.Yes:
            self.inventory_service.delete_epp(e.id)
            self.refresh_data()

    def on_epp_delivery_in(self):
        e = self._get_selected_epp_del()
        if not e:
            QMessageBox.information(self, "Ingreso de EPP", "Seleccione un EPP de la lista para ingresar stock a Pañol.")
            return
        dlg = PanolMovementDialog(
            item_name=f"{e.name} ({e.size_or_model})" if e.size_or_model else e.name,
            current_stock=e.quantity,
            unit=e.unit,
            operation="IN",
            item_category="EPP_DELIVERY",
            technician_service=self.technician_service,
            client_service=self.client_service,
            parent=self
        )
        if dlg.exec():
            d = dlg.get_data()
            self.inventory_service.register_epp_stock_movement(
                epp_id=e.id,
                movement_type="IN",
                **d
            )
            self.refresh_data()

    def on_epp_delivery_out(self):
        e = self._get_selected_epp_del()
        if not e:
            QMessageBox.information(self, "Entrega de EPP", "Seleccione un EPP de la lista para registrar su entrega.")
            return
        if e.quantity <= 0:
            QMessageBox.warning(self, "Sin Stock", f"El EPP '{e.name}' no tiene unidades disponibles en Pañol.")
            return
        dlg = PanolMovementDialog(
            item_name=f"{e.name} ({e.size_or_model})" if e.size_or_model else e.name,
            current_stock=e.quantity,
            unit=e.unit,
            operation="OUT",
            item_category="EPP_DELIVERY",
            technician_service=self.technician_service,
            client_service=self.client_service,
            parent=self
        )
        if dlg.exec():
            d = dlg.get_data()
            self.inventory_service.register_epp_stock_movement(
                epp_id=e.id,
                movement_type="OUT",
                **d
            )
            self.refresh_data()

    # =========================================================================
    # HANDLERS: EPP POR ASIGNACIÓN (CARGO)
    # =========================================================================
    def _get_selected_epp_asg(self):
        idxs = self.table_epp_asg.selectionModel().selectedRows()
        return self.model_epp_asg.get_item(idxs[0].row()) if idxs else None

    def on_epp_asg_selected(self):
        e = self._get_selected_epp_asg()
        clear_layout_widgets(self.epp_asg_cards_layout)
        if not e:
            self.lbl_epp_asg_title.setText("Seleccione un equipo EPP")
            self.epp_asg_cards_layout.addWidget(
                build_empty_detail_card("Seleccione un elemento por asignación para ver su estado, inspección y cargo actual.")
            )
            self.btn_epp_asg_edit.setEnabled(False)
            self.btn_epp_asg_delete.setEnabled(False)
            self.list_epp_asg_movs.clear()
            return

        self.lbl_epp_asg_title.setText(e.name)
        self.btn_epp_asg_edit.setEnabled(True)
        self.btn_epp_asg_delete.setEnabled(True)

        st_map = {
            "AVAILABLE": ("Disponible en Pañol", "#10B981", "#064E3B"),
            "ASSIGNED": ("Asignado (En Cargo)", "#38BDF8", "#0C4A6E"),
            "IN_INSPECTION": ("En Revisión", "#F59E0B", "#451A03"),
            "OUT_OF_SERVICE": ("Fuera de Servicio", "#EF4444", "#450A0A"),
        }
        st_lbl, st_fg, st_bg = st_map.get((e.status or "AVAILABLE").upper(), (e.status, "#38BDF8", "#0C4A6E"))

        self.epp_asg_cards_layout.addWidget(
            build_status_banner([
                ("ESTADO ACTUAL", st_lbl, st_fg, st_bg),
                ("A CARGO DE", e.assigned_to or "Disponible en Pañol", "#F59E0B", "#451A03"),
            ])
        )

        rows = [
            ("N° Serie / Código", f"<b style='color: #F59E0B;'>{html.escape(e.serial_number or e.code or 'N/A')}</b>"),
            ("Categoría", html.escape(e.category or "EPP Cargo")),
            ("Marca / Modelo", html.escape(f"{e.brand or '-'} {e.size_or_model or ''}".strip())),
            ("Fecha Asignación", html.escape(e.assigned_date or "-")),
            ("Vencimiento / Inspección", html.escape(e.expiration_date or "-")),
        ]
        if e.notes:
            rows.append(("Notas", html.escape(e.notes)))

        self.epp_asg_cards_layout.addWidget(
            build_section_card("Ficha de EPP por Asignación", "#F59E0B", build_kv_widget(rows))
        )
        self._populate_item_movements_list(self.list_epp_asg_movs, e.id)

    def on_epp_asg_edit(self):
        e = self._get_selected_epp_asg()
        if not e:
            return
        dlg = EppItemDialog(self, epp=e)
        if dlg.exec():
            self.inventory_service.save_epp(dlg.get_epp())
            self.refresh_data()

    def on_epp_asg_delete(self):
        e = self._get_selected_epp_asg()
        if not e:
            return
        if QMessageBox.question(self, "Eliminar EPP de Cargo", f"¿Enviar '{e.name}' a la papelera?") == QMessageBox.StandardButton.Yes:
            self.inventory_service.delete_epp(e.id)
            self.refresh_data()

    def on_epp_assign(self):
        e = self._get_selected_epp_asg()
        if not e:
            QMessageBox.information(self, "Asignar EPP", "Seleccione un equipo EPP (Arnés, línea de vida, carro, estrobo, polaina, etc.) para asignarlo.")
            return
        if e.status == "OUT_OF_SERVICE":
            QMessageBox.warning(self, "Fuera de Servicio", "Este equipo figura dado de baja / fuera de servicio.")
            return

        dlg = PanolMovementDialog(
            item_name=f"{e.name} [{e.serial_number or e.code or 'S/N'}]",
            current_stock=1,
            unit=e.unit,
            operation="ASSIGN",
            item_category="EPP_ASSIGNMENT",
            technician_service=self.technician_service,
            client_service=self.client_service,
            parent=self
        )
        if dlg.exec():
            d = dlg.get_data()
            self.inventory_service.assign_epp(
                epp_id=e.id,
                recipient_name=d["recipient_name"],
                recipient_type=d["recipient_type"],
                reason=d["reason"],
                reference=d["reference"],
                performed_by=d["performed_by"],
                notes=d["notes"]
            )
            self.refresh_data()

    def on_epp_return(self):
        e = self._get_selected_epp_asg()
        if not e:
            QMessageBox.information(self, "Devolución a Pañol", "Seleccione un equipo EPP asignado para registrar su devolución a Pañol.")
            return
        if not e.assigned_to and e.status == "AVAILABLE":
            QMessageBox.information(self, "Disponible", "Este elemento ya se encuentra disponible en Pañol.")
            return

        reply = QMessageBox.question(
            self,
            "Recepcionar EPP en Pañol",
            f"¿Confirmar devolución a Pañol de '{e.name}' (actualmente a cargo de: {e.assigned_to or 'N/A'})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.inventory_service.return_epp(e.id)
            self.refresh_data()

    # =========================================================================
    # HANDLERS: HERRAMIENTAS EN PAÑOL
    # =========================================================================
    def _get_selected_tool(self):
        idxs = self.table_tools.selectionModel().selectedRows()
        return self.model_tools.get_item(idxs[0].row()) if idxs else None

    def on_tool_selected(self):
        t = self._get_selected_tool()
        clear_layout_widgets(self.tool_cards_layout)
        if not t:
            self.lbl_tool_title.setText("Seleccione una herramienta")
            self.tool_cards_layout.addWidget(
                build_empty_detail_card("Seleccione una herramienta de la lista para ver su estado, calibración y préstamos.")
            )
            self.btn_tool_edit.setEnabled(False)
            self.btn_tool_delete.setEnabled(False)
            self.list_tool_movs.clear()
            return

        self.lbl_tool_title.setText(t.name)
        self.btn_tool_edit.setEnabled(True)
        self.btn_tool_delete.setEnabled(True)

        st_val = (t.status.value if hasattr(t.status, 'value') else str(t.status)).upper()
        st_map = {
            "AVAILABLE": ("Disponible en Pañol", "#10B981", "#064E3B"),
            "IN_USE": ("En Uso / Asignada", "#F59E0B", "#451A03"),
            "IN_CALIBRATION": ("En Calibración", "#38BDF8", "#0C4A6E"),
            "OUT_OF_SERVICE": ("Fuera de Servicio", "#EF4444", "#450A0A"),
        }
        st_lbl, st_fg, st_bg = st_map.get(st_val, (st_val, "#818CF8", "#1E1B4B"))

        self.tool_cards_layout.addWidget(
            build_status_banner([
                ("ESTADO HERRAMIENTA", st_lbl, st_fg, st_bg),
                ("ASIGNADO A", t.assigned_to or "Disponible en Pañol", "#818CF8", "#1E1B4B"),
            ])
        )

        rows = [
            ("Marca / Modelo", html.escape(f"{t.brand or '-'} {t.model or ''}".strip())),
            ("N° Serie", f"<b style='color: #818CF8;'>{html.escape(t.serial_number or 'N/A')}</b>"),
            ("Categoría", html.escape(t.category or "General")),
            ("Ubicación", html.escape(t.location or "Pañol")),
            ("Próxima Calibración", html.escape(t.next_calibration or "N/A")),
        ]
        if t.notes:
            rows.append(("Notas", html.escape(t.notes)))

        self.tool_cards_layout.addWidget(
            build_section_card("Ficha de la Herramienta", "#818CF8", build_kv_widget(rows))
        )
        self._populate_item_movements_list(self.list_tool_movs, t.id)

    def on_tool_new(self):
        dlg = ToolDialog(parent=self)
        if dlg.exec():
            self.inventory_service.save_tool(dlg.get_tool())
            self.refresh_data()

    def on_tool_edit(self):
        t = self._get_selected_tool()
        if not t:
            return
        dlg = ToolDialog(parent=self, tool=t)
        if dlg.exec():
            self.inventory_service.save_tool(dlg.get_tool())
            self.refresh_data()

    def on_tool_delete(self):
        t = self._get_selected_tool()
        if not t:
            return
        if QMessageBox.question(self, "Eliminar Herramienta", f"¿Enviar la herramienta '{t.name}' a la papelera?") == QMessageBox.StandardButton.Yes:
            self.inventory_service.delete_tool(t.id)
            self.refresh_data()

    def on_tool_assign(self):
        t = self._get_selected_tool()
        if not t:
            QMessageBox.information(self, "Asignar Herramienta", "Seleccione una herramienta de la lista para entregarla/asignarla.")
            return

        dlg = PanolMovementDialog(
            item_name=f"{t.name} ({t.brand} {t.model})".strip(),
            current_stock=1,
            unit="unid",
            operation="ASSIGN",
            item_category="TOOL",
            technician_service=self.technician_service,
            client_service=self.client_service,
            parent=self
        )
        if dlg.exec():
            d = dlg.get_data()
            self.inventory_service.assign_tool(
                tool_id=t.id,
                technician=d["recipient_name"],
                recipient_type=d["recipient_type"],
                performed_by=d["performed_by"],
                notes=d["notes"]
            )
            self.refresh_data()

    def on_tool_return(self):
        t = self._get_selected_tool()
        if not t:
            QMessageBox.information(self, "Devolver Herramienta", "Seleccione una herramienta para registrar su devolución a Pañol.")
            return
        if not t.assigned_to and (t.status == "AVAILABLE" or getattr(t.status, 'value', '') == "AVAILABLE"):
            QMessageBox.information(self, "Disponible", "La herramienta ya figura disponible en Pañol.")
            return

        reply = QMessageBox.question(
            self,
            "Devolución de Herramienta a Pañol",
            f"¿Confirmar recepción en Pañol de la herramienta '{t.name}' (asignada a: {t.assigned_to or 'N/A'})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.inventory_service.return_tool(t.id)
            self.refresh_data()

    def _build_initial_movement(self, item_id, name, code, cat, qty, unit):
        from src.core.models.inventory import PanolMovement
        return PanolMovement(
            item_id=item_id,
            item_name=name,
            item_code=code,
            item_category=cat,
            movement_type="IN",
            quantity=qty,
            unit=unit,
            recipient_name="Stock Inicial Pañol",
            reason="Inventario Inicial en Pañol",
            performed_by="Pañolero"
        )
