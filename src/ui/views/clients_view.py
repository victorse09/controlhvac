import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableView, 
    QPushButton, QLabel, QFrame, QMessageBox, QHeaderView, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor
from src.ui.widgets.search_bar import SearchBar
from src.ui.widgets.detail_card import (
    clear_layout_widgets, build_section_card, build_kv_widget,
    build_rich_label, build_status_banner, build_empty_detail_card
)
from src.ui.widgets.table_state_helper import setup_modern_table
from src.ui.models.table_models import ClientTableModel, SiteTableModel
from src.ui.dialogs.client_dialog import ClientDialog
from src.ui.dialogs.site_dialog import SiteDialog
from src.ui.icon_manager import IconManager


class ClientsView(QWidget):
    def __init__(self, client_service, parent=None):
        super().__init__(parent)
        self.client_service = client_service
        self.clients = []
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search_bar = SearchBar()
        self.search_bar.setPlaceholderText("Buscar clientes por nombre, RUT, contacto...")
        self.search_bar.textChanged.connect(self.on_search)
        
        self.btn_new_client = QPushButton()
        self.btn_new_client.setObjectName("primaryButton")
        self.btn_new_client.setIcon(IconManager.get_icon("add.svg", "#FFFFFF", 18))
        self.btn_new_client.setIconSize(QSize(18, 18))
        self.btn_new_client.setFixedSize(36, 36)
        self.btn_new_client.setToolTip("Nuevo Cliente")
        self.btn_new_client.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new_client.clicked.connect(self.on_new_client)

        toolbar.addWidget(self.search_bar, 1)
        toolbar.addWidget(self.btn_new_client)
        main_layout.addLayout(toolbar)

        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter, 1)

        # Left: Clients Table
        self.client_table = QTableView()
        self.client_model = ClientTableModel([])
        self.client_table.setModel(self.client_model)
        self.client_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.client_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.client_table.selectionModel().selectionChanged.connect(self.on_client_selected)
        self.client_table.doubleClicked.connect(self.on_edit_client)
        self.splitter.addWidget(self.client_table)

        # Right: Detail View
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("cardFrame")
        detail_layout = QVBoxLayout(self.detail_frame)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(12)
        
        # Client header & actions
        client_header_layout = QHBoxLayout()
        self.lbl_client_name = QLabel("Seleccione un cliente")
        self.lbl_client_name.setObjectName("detailTitleLabel")
        client_header_layout.addWidget(self.lbl_client_name)
        client_header_layout.addStretch()

        self.btn_edit_client = QPushButton()
        self.btn_edit_client.setIcon(IconManager.get_icon("edit.svg", "#F8FAFC", 18))
        self.btn_edit_client.setIconSize(QSize(18, 18))
        self.btn_edit_client.setFixedSize(36, 36)
        self.btn_edit_client.setToolTip("Editar Cliente")
        self.btn_edit_client.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit_client.setEnabled(False)
        self.btn_edit_client.clicked.connect(self.on_edit_client_clicked)
        client_header_layout.addWidget(self.btn_edit_client)

        self.btn_delete_client = QPushButton()
        self.btn_delete_client.setObjectName("dangerButton")
        self.btn_delete_client.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 18))
        self.btn_delete_client.setIconSize(QSize(18, 18))
        self.btn_delete_client.setFixedSize(36, 36)
        self.btn_delete_client.setToolTip("Eliminar Cliente")
        self.btn_delete_client.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_delete_client.setEnabled(False)
        self.btn_delete_client.clicked.connect(self.on_delete_client)
        client_header_layout.addWidget(self.btn_delete_client)

        detail_layout.addLayout(client_header_layout)
        
        # Scrollable cards area for client info
        self.info_scroll = QScrollArea()
        self.info_scroll.setWidgetResizable(True)
        self.info_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.info_scroll.setMaximumHeight(260)
        info_container = QWidget()
        self.client_info_layout = QVBoxLayout(info_container)
        self.client_info_layout.setContentsMargins(0, 0, 4, 0)
        self.client_info_layout.setSpacing(8)
        self.info_scroll.setWidget(info_container)
        detail_layout.addWidget(self.info_scroll)
        
        # Sites section card
        sites_card = QFrame()
        sites_card.setObjectName("eqSectionCard")
        sc_layout = QVBoxLayout(sites_card)
        sc_layout.setContentsMargins(0, 0, 0, 0)
        sc_layout.setSpacing(0)

        sites_header = QFrame()
        sites_header.setObjectName("eqCardHeader")
        sites_header.setStyleSheet(
            "QFrame#eqCardHeader {"
            "  border-bottom: 2px solid #F59E0B;"
            "}"
        )
        sites_header_layout = QHBoxLayout(sites_header)
        sites_header_layout.setContentsMargins(12, 6, 12, 6)
        self.lbl_sites = QLabel("INSTALACIONES / SEDES ASOCIADAS")
        self.lbl_sites.setStyleSheet("color: #F59E0B; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; background: transparent; border: none;")
        sites_header_layout.addWidget(self.lbl_sites)
        sites_header_layout.addStretch()

        self.btn_new_site = QPushButton()
        self.btn_new_site.setObjectName("primaryButton")
        self.btn_new_site.setIcon(IconManager.get_icon("add.svg", "#FFFFFF", 14))
        self.btn_new_site.setIconSize(QSize(14, 14))
        self.btn_new_site.setFixedSize(28, 28)
        self.btn_new_site.setToolTip("Nueva Instalación")
        self.btn_new_site.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new_site.setEnabled(False)
        self.btn_new_site.clicked.connect(self.on_new_site)
        sites_header_layout.addWidget(self.btn_new_site)

        self.btn_edit_site = QPushButton()
        self.btn_edit_site.setIcon(IconManager.get_icon("edit.svg", "#F8FAFC", 14))
        self.btn_edit_site.setIconSize(QSize(14, 14))
        self.btn_edit_site.setFixedSize(28, 28)
        self.btn_edit_site.setToolTip("Editar Instalación")
        self.btn_edit_site.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_edit_site.setEnabled(False)
        self.btn_edit_site.clicked.connect(self.on_edit_site_clicked)
        sites_header_layout.addWidget(self.btn_edit_site)

        self.btn_delete_site = QPushButton()
        self.btn_delete_site.setObjectName("dangerButton")
        self.btn_delete_site.setIcon(IconManager.get_icon("delete.svg", "#FFFFFF", 14))
        self.btn_delete_site.setIconSize(QSize(14, 14))
        self.btn_delete_site.setFixedSize(28, 28)
        self.btn_delete_site.setToolTip("Eliminar Instalación")
        self.btn_delete_site.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_delete_site.setEnabled(False)
        self.btn_delete_site.clicked.connect(self.on_delete_site)
        sites_header_layout.addWidget(self.btn_delete_site)

        sc_layout.addWidget(sites_header)

        sites_body = QWidget()
        sites_body.setStyleSheet("background: transparent; border: none;")
        sb_layout = QVBoxLayout(sites_body)
        sb_layout.setContentsMargins(10, 10, 10, 10)

        self.sites_table = QTableView()
        self.sites_model = SiteTableModel([])
        self.sites_table.setModel(self.sites_model)
        self.sites_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.sites_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.sites_table.selectionModel().selectionChanged.connect(self.on_site_selected)
        self.sites_table.doubleClicked.connect(self.on_site_double_clicked)
        sb_layout.addWidget(self.sites_table)
        sc_layout.addWidget(sites_body, 1)

        detail_layout.addWidget(sites_card, 1)
        
        self.splitter.addWidget(self.detail_frame)
        storage = getattr(self.client_service, "storage", None)
        setup_modern_table(
            self.client_table,
            storage=storage,
            settings_key="clients_table",
            default_widths=[180, 105, 140, 110, 150, 100],
            splitter=self.splitter,
            default_splitter_sizes=[460, 540],
        )
        setup_modern_table(
            self.sites_table,
            storage=storage,
            settings_key="client_sites_table",
            default_widths=[150, 160, 130, 105, 140],
        )

    def get_selected_client(self):
        indexes = self.client_table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.client_model.get_item(indexes[0].row())

    def get_selected_site(self):
        indexes = self.sites_table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.sites_model.get_item(indexes[0].row())

    def refresh_data(self):
        try:
            selected_client_id = None
            client = self.get_selected_client()
            if client:
                selected_client_id = client.id

            self.clients = self.client_service.get_all_clients()
            self.client_model.update_data(self.clients)

            if selected_client_id:
                for row, c in enumerate(self.clients):
                    if c.id == selected_client_id:
                        self.client_table.selectRow(row)
                        break
                else:
                    self.on_client_selected()
            else:
                self.on_client_selected()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def load_sites_for_client(self, client_id):
        try:
            sites = self.client_service.get_sites_for_client(client_id)
            self.sites_model.set_data(sites)
            self.lbl_sites.setText(f"INSTALACIONES / SEDES ASOCIADAS ({len(sites)})")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar instalaciones: {e}")
        self.btn_edit_site.setEnabled(False)
        self.btn_delete_site.setEnabled(False)

    def on_search(self, text):
        filtered = [
            c for c in self.clients 
            if text.lower() in (c.name or '').lower() or text.lower() in (c.email or '').lower() or text.lower() in (c.tax_id or '').lower()
        ]
        self.client_model.set_data(filtered)

    def on_client_selected(self, selected=None, deselected=None):
        client = self.get_selected_client()
        clear_layout_widgets(self.client_info_layout)
        if not client:
            self.btn_edit_client.setEnabled(False)
            self.btn_delete_client.setEnabled(False)
            self.btn_new_site.setEnabled(False)
            self.btn_edit_site.setEnabled(False)
            self.btn_delete_site.setEnabled(False)
            self.lbl_client_name.setText("Seleccione un cliente")
            self.lbl_sites.setText("INSTALACIONES / SEDES ASOCIADAS")
            self.client_info_layout.addWidget(
                build_empty_detail_card("Haga clic en un cliente de la tabla izquierda para visualizar sus datos comerciales, contacto y sedes asociadas.")
            )
            self.client_info_layout.addStretch()
            self.sites_model.set_data([])
            return
            
        self.btn_edit_client.setEnabled(True)
        self.btn_delete_client.setEnabled(True)
        self.btn_new_site.setEnabled(True)
        self.lbl_client_name.setText(client.name)

        rows = [
            ("RUT / ID Tributario", f"<b style='color: #38BDF8;'>{html.escape(client.tax_id or 'N/A')}</b>"),
            ("Contacto Principal", html.escape(client.contact_name or "No especificado")),
            ("Teléfono Contacto", html.escape(client.phone or "No especificado")),
            ("Email Contacto", html.escape(client.email or "No especificado")),
            ("Dirección Comercial", html.escape(client.address or "No especificada")),
        ]
        if client.contract_number:
            rows.append(("N° Contrato", f"<b style='color: #10B981;'>{html.escape(client.contract_number)}</b>"))
        if getattr(client, 'contract_start', '') or getattr(client, 'contract_end', ''):
            vig = f"{getattr(client, 'contract_start', '-') or '-'} al {getattr(client, 'contract_end', '-') or '-'}"
            rows.append(("Vigencia Contrato", html.escape(vig)))

        self.client_info_layout.addWidget(
            build_section_card("Información Comercial y Contacto", "#38BDF8", build_kv_widget(rows))
        )
        if getattr(client, 'notes', ''):
            self.client_info_layout.addWidget(
                build_section_card("Notas del Cliente", "#A855F7", build_rich_label(html.escape(client.notes)))
            )
        self.client_info_layout.addStretch()
        self.load_sites_for_client(client.id)

    def on_site_selected(self, selected=None, deselected=None):
        site = self.get_selected_site()
        has_site = site is not None
        self.btn_edit_site.setEnabled(has_site)
        self.btn_delete_site.setEnabled(has_site)

    def on_new_client(self):
        dialog = ClientDialog(parent=self)
        if dialog.exec():
            client = dialog.get_client()
            self.client_service.save_client(client)
            self.refresh_data()

    def on_edit_client_clicked(self):
        client = self.get_selected_client()
        if client:
            dialog = ClientDialog(parent=self, client=client)
            if dialog.exec():
                updated = dialog.get_client()
                self.client_service.save_client(updated)
                self.refresh_data()

    def on_edit_client(self, index):
        client = self.client_model.get_item(index.row())
        if client:
            dialog = ClientDialog(parent=self, client=client)
            if dialog.exec():
                updated = dialog.get_client()
                self.client_service.save_client(updated)
                self.refresh_data()

    def on_delete_client(self):
        client = self.get_selected_client()
        if not client:
            return
        reply = QMessageBox.question(
            self,
            "Eliminar Cliente",
            f"¿Está seguro de que desea eliminar al cliente '{client.name}' y todas sus instalaciones asociadas?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.client_service.delete_client(client.id):
                self.refresh_data()
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el cliente.")

    def on_new_site(self):
        client = self.get_selected_client()
        if not client:
            return
        dialog = SiteDialog(parent=self, client_id=client.id)
        if dialog.exec():
            site = dialog.get_site()
            self.client_service.save_site(site)
            self.load_sites_for_client(client.id)

    def on_edit_site_clicked(self):
        client = self.get_selected_client()
        site = self.get_selected_site()
        if client and site:
            self._edit_site(client, site)

    def on_site_double_clicked(self, index):
        client = self.get_selected_client()
        site = self.sites_model.get_item(index.row())
        if client and site:
            self._edit_site(client, site)

    def _edit_site(self, client, site):
        dialog = SiteDialog(parent=self, client_id=client.id, site=site)
        if dialog.exec():
            updated = dialog.get_site()
            self.client_service.save_site(updated)
            self.load_sites_for_client(client.id)

    def on_delete_site(self):
        client = self.get_selected_client()
        site = self.get_selected_site()
        if not client or not site:
            return
        reply = QMessageBox.question(
            self,
            "Eliminar Instalación",
            f"¿Está seguro de que desea eliminar la instalación '{site.name}'?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.client_service.delete_site(site.id, client.id):
                self.load_sites_for_client(client.id)
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar la instalación.")
