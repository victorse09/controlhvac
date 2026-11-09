"""
Technicians View for ControlHVAC CMMS.
Displays the list of technicians, filters, metrics, and detailed view.
"""
import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableView,
    QPushButton, QLabel, QFrame, QMessageBox, QHeaderView, QComboBox,
    QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor

from src.core.models.enums import (
    TechnicianStatus, TECHNICIAN_STATUS_LABELS,
    TechnicianSpecialty, TECHNICIAN_SPECIALTY_LABELS
)
from src.core.models.technician import Technician
from src.ui.dialogs.technician_dialog import TechnicianDialog
from src.ui.icon_manager import IconManager
from src.ui.models.table_models import TechnicianTableModel
from src.ui.widgets.search_bar import SearchBar
from src.ui.widgets.stat_card import StatCard
from src.ui.widgets.detail_card import (
    clear_layout_widgets, build_section_card, build_kv_widget,
    build_rich_label, build_status_banner, build_empty_detail_card
)
from src.ui.widgets.table_state_helper import setup_modern_table


class TechniciansView(QWidget):
    def __init__(self, technician_service, parent=None):
        super().__init__(parent)
        self.technician_service = technician_service
        self.technicians = []
        self._selected_technician = None
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Stats Cards Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.card_total = StatCard("Total Personal", "0", IconManager.get_icon("technicians", "#38BDF8"), accent_color="#38BDF8")
        self.card_active = StatCard("Activos / Disponibles", "0", IconManager.get_icon("check.svg", "#10B981"), accent_color="#10B981")
        self.card_leave = StatCard("Licencia / Vacaciones", "0", IconManager.get_icon("calendar.svg", "#F59E0B"), accent_color="#F59E0B")
        self.card_inactive = StatCard("Inactivos", "0", IconManager.get_icon("warning.svg", "#EF4444"), accent_color="#EF4444")

        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_active)
        stats_layout.addWidget(self.card_leave)
        stats_layout.addWidget(self.card_inactive)
        main_layout.addLayout(stats_layout)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.search_bar = SearchBar()
        self.search_bar.setPlaceholderText("Buscar técnicos por nombre, RUT, teléfono, especialidad...")
        self.search_bar.textChanged.connect(self._apply_filters)

        self.specialty_filter = QComboBox()
        self.specialty_filter.addItem("Todas las Especialidades", "")
        for spec, label in TECHNICIAN_SPECIALTY_LABELS.items():
            self.specialty_filter.addItem(label, spec.value if hasattr(spec, 'value') else spec)
        self.specialty_filter.currentIndexChanged.connect(self._apply_filters)

        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos los Estados", "")
        for st, label in TECHNICIAN_STATUS_LABELS.items():
            self.status_filter.addItem(label, st.value if hasattr(st, 'value') else st)
        self.status_filter.currentIndexChanged.connect(self._apply_filters)

        self.btn_new = QPushButton(" Nuevo Técnico")
        self.btn_new.setObjectName("primaryButton")
        self.btn_new.setIcon(IconManager.get_icon("add.svg", "#000000", 18))
        self.btn_new.setIconSize(QSize(18, 18))
        self.btn_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new.clicked.connect(self.on_new)

        toolbar.addWidget(self.search_bar, 2)
        toolbar.addWidget(self.specialty_filter, 1)
        toolbar.addWidget(self.status_filter, 1)
        toolbar.addWidget(self.btn_new)
        main_layout.addLayout(toolbar)

        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter, 1)

        # Table
        self.table = QTableView()
        self.model = TechnicianTableModel([])
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.on_double_click)
        self.splitter.addWidget(self.table)

        # Detail Frame
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("cardFrame")
        self.detail_frame.setMinimumWidth(340)
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(12)

        # Header with actions
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        self.lbl_title = QLabel("Seleccione un técnico")
        self.lbl_title.setObjectName("detailTitleLabel")
        self.lbl_title.setWordWrap(True)
        header_layout.addWidget(self.lbl_title, 1)

        self.btn_edit = QPushButton()
        self.btn_edit.setIcon(IconManager.get_icon("edit.svg", "#F8FAFC", 18))
        self.btn_edit.setIconSize(QSize(18, 18))
        self.btn_edit.setFixedSize(36, 36)
        self.btn_edit.setToolTip("Editar Técnico")
        self.btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self.on_edit_clicked)
        header_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton()
        self.btn_delete.setObjectName("dangerButton")
        self.btn_delete.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 18))
        self.btn_delete.setIconSize(QSize(18, 18))
        self.btn_delete.setFixedSize(36, 36)
        self.btn_delete.setToolTip("Eliminar Técnico")
        self.btn_delete.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        header_layout.addWidget(self.btn_delete)

        detail_layout.addLayout(header_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        detail_content = QWidget()
        self.detail_content_layout = QVBoxLayout(detail_content)
        self.detail_content_layout.setContentsMargins(0, 0, 4, 0)
        self.detail_content_layout.setSpacing(10)
        scroll.setWidget(detail_content)
        detail_layout.addWidget(scroll, 1)

        self.splitter.addWidget(self.detail_frame)
        storage = getattr(self.technician_service, "storage", None)
        setup_modern_table(
            self.table,
            storage=storage,
            settings_key="technicians_table",
            default_widths=[110, 175, 130, 115, 110, 145, 120],
            splitter=self.splitter,
            default_splitter_sizes=[660, 360],
        )
        self._display_technician_detail(None)

    def refresh_data(self):
        """Reload technicians from service and update views."""
        self._apply_filters()
        self._update_stats()

    def _update_stats(self):
        stats = self.technician_service.get_stats()
        self.card_total.set_value(str(stats.get("total", 0)))
        self.card_active.set_value(str(stats.get("active", 0)))
        self.card_leave.set_value(str(stats.get("on_leave", 0)))
        self.card_inactive.set_value(str(stats.get("inactive", 0)))

    def _apply_filters(self):
        query = self.search_bar.text()
        specialty = self.specialty_filter.currentData() or None
        status = self.status_filter.currentData() or None

        self.technicians = self.technician_service.search_technicians(
            query=query, specialty=specialty, status=status
        )
        self.model.set_data(self.technicians)

        if self._selected_technician and self._selected_technician not in self.technicians:
            self._display_technician_detail(None)

    def on_selection_changed(self, selected, deselected):
        indexes = self.table.selectionModel().selectedRows()
        if indexes:
            row = indexes[0].row()
            tech = self.model.get_item(row)
            self._display_technician_detail(tech)
        else:
            self._display_technician_detail(None)

    def _display_technician_detail(self, tech: Technician):
        self._selected_technician = tech
        clear_layout_widgets(self.detail_content_layout)
        if not tech:
            self.lbl_title.setText("Seleccione un técnico")
            self.btn_edit.setEnabled(False)
            self.btn_delete.setEnabled(False)
            self.detail_content_layout.addWidget(
                build_empty_detail_card("Haga clic en un técnico de la lista para ver su perfil profesional, contacto y certificaciones.")
            )
            self.detail_content_layout.addStretch()
            return

        self.lbl_title.setText(f"{tech.full_name}")
        self.btn_edit.setEnabled(True)
        self.btn_delete.setEnabled(True)

        spec_label = TECHNICIAN_SPECIALTY_LABELS.get(tech.specialty, tech.specialty)
        st_label = TECHNICIAN_STATUS_LABELS.get(tech.status, tech.status)
        st_upper = (tech.status or "").upper()
        if "ACTIVO" in st_upper and "INACTIVO" not in st_upper:
            st_fg, st_bg = "#10B981", "#064E3B"
        elif "LICENCIA" in st_upper or "VACACIONES" in st_upper:
            st_fg, st_bg = "#F59E0B", "#451A03"
        else:
            st_fg, st_bg = "#EF4444", "#450A0A"

        self.detail_content_layout.addWidget(
            build_status_banner([
                ("ESTADO LABORAL", st_label, st_fg, st_bg),
                ("ESPECIALIDAD", spec_label, "#38BDF8", "#0C4A6E"),
            ])
        )

        rows = [
            ("RUT / Código", f"<b style='color: #38BDF8;'>{html.escape(tech.code or 'N/A')}</b>"),
            ("Nombre Completo", f"<b>{html.escape(tech.full_name or '')}</b>"),
            ("Especialidad", html.escape(spec_label)),
            ("Teléfono", html.escape(tech.phone or "No especificado")),
            ("Email", html.escape(tech.email or "No especificado")),
            ("Certificación / SEC", f"<b style='color: #10B981;'>{html.escape(tech.license_number)}</b>" if tech.license_number else "<i style='color: #64748B;'>Sin certificación registrada</i>"),
        ]
        self.detail_content_layout.addWidget(
            build_section_card("Ficha del Técnico", "#38BDF8", build_kv_widget(rows))
        )

        notes_txt = html.escape(tech.notes).replace("\n", "<br>") if tech.notes else "<i style='color: #64748B;'>Sin observaciones adicionales.</i>"
        self.detail_content_layout.addWidget(
            build_section_card("Notas y Observaciones", "#A855F7", build_rich_label(notes_txt))
        )
        self.detail_content_layout.addStretch()

    def on_new(self):
        dialog = TechnicianDialog(self)
        if dialog.exec():
            new_tech = dialog.get_technician_data()
            self.technician_service.save_technician(new_tech)
            self.refresh_data()

    def on_double_click(self, index):
        tech = self.model.get_item(index.row())
        if tech:
            dialog = TechnicianDialog(self, technician=tech, read_only=True)
            if dialog.exec():
                updated_tech = dialog.get_technician_data()
                self.technician_service.save_technician(updated_tech)
                self.refresh_data()
                self._display_technician_detail(updated_tech)

    def on_edit_clicked(self):
        if self._selected_technician:
            dialog = TechnicianDialog(self, technician=self._selected_technician, read_only=False)
            if dialog.exec():
                updated_tech = dialog.get_technician_data()
                self.technician_service.save_technician(updated_tech)
                self.refresh_data()
                self._display_technician_detail(updated_tech)

    def on_delete_clicked(self):
        if not self._selected_technician:
            return

        confirm = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de enviar al técnico '{self._selected_technician.full_name}' a la papelera de reciclaje?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.technician_service.delete_technician(self._selected_technician.id)
            self._selected_technician = None
            self.refresh_data()
