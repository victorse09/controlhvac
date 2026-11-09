import os
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QLabel, QPushButton, QFileDialog,
    QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QCursor

from src.app.config import AppConfig
from src.app.state_manager import StateManager
from src.ui.widgets.sidebar import Sidebar
from src.ui.icon_manager import IconManager
from src.data.json_storage import JsonStorageEngine

from src.core.services.client_service import ClientService
from src.core.services.equipment_service import EquipmentService
from src.core.services.work_order_service import WorkOrderService
from src.core.services.maintenance_service import MaintenanceService
from src.core.services.inventory_service import InventoryService
from src.core.services.export_service import ExportService
from src.core.services.recycle_bin_service import RecycleBinService
from src.core.services.custom_lists_service import CustomListsService
from src.core.services.incident_service import IncidentService
from src.core.services.technician_service import TechnicianService
from src.core.services.library_service import LibraryService
from src.ui.dialogs.settings_dialog import SettingsDialog

from src.ui.views.dashboard_view import DashboardView


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig, state_manager: StateManager):
        super().__init__()
        self.config = config
        self.state_manager = state_manager
        
        self.setWindowTitle("ControlHVAC - CMMS de Climatización")
        self.setWindowIcon(QIcon("assets/icons/app_icon.svg"))
        self.setMinimumSize(1200, 800)

        # Pre-initialize service references
        self.storage = None
        self.recycle_bin_service = None
        self.custom_lists_service = None
        self.technician_service = None
        self.library_service = None
        self.client_service = None
        self.equipment_service = None
        self.incident_service = None
        self.work_order_service = None
        self.maintenance_service = None
        self.inventory_service = None
        self.export_service = None
        
        # UI Setup
        self._setup_ui()
        
        # Load sidebar logo if configured
        self.sidebar.update_logo(self.state_manager.get_logo_path())
        
        # Check data directory
        if not self.config.is_data_dir_set:
            self._prompt_for_data_directory()
        else:
            self._initialize_services()
            self._create_views()
            self._switch_view("dashboard")
        
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.navigation_changed.connect(self._switch_view)
        self.sidebar.settings_requested.connect(self._open_settings_dialog)
        main_layout.addWidget(self.sidebar)
        
        # Right side layout
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Stacked widget for views
        self.stacked_widget = QStackedWidget()
        right_layout.addWidget(self.stacked_widget, 1)
        
        # Bottom Status / Footer Bar (Read-only folder path)
        footer_widget = QWidget()
        footer_widget.setObjectName("statusBar")
        footer_layout = QHBoxLayout(footer_widget)
        footer_layout.setContentsMargins(16, 6, 16, 6)
        footer_layout.setSpacing(8)

        folder_icon_lbl = QLabel()
        folder_icon_lbl.setPixmap(IconManager.get_pixmap("actions/folder.svg", "#64748B", 14))

        self.data_folder_label = QLabel(f"Carpeta de trabajo: {self.config.data_dir}" if self.config.data_dir else "Carpeta de trabajo: No seleccionada")
        self.data_folder_label.setObjectName("muted")
        self.data_folder_label.setStyleSheet("color: #64748B; font-size: 11px;")

        footer_layout.addWidget(folder_icon_lbl)
        footer_layout.addWidget(self.data_folder_label)
        footer_layout.addStretch()

        right_layout.addWidget(footer_widget)
        
        main_layout.addWidget(right_widget)
        
    def _prompt_for_data_directory(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Configuración Inicial")
        msg.setText("Bienvenido a ControlHVAC CMMS.\n\nPor favor, seleccione una carpeta donde se guardarán todos los datos del sistema.")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        
        if msg.exec() == QMessageBox.StandardButton.Ok:
            self._select_data_folder()
        else:
            # User cancelled, check if we have a default or exit
            if not self.config.data_dir:
                res = QMessageBox.warning(
                    self,
                    "Carpeta Requerida",
                    "La aplicación necesita una carpeta de datos para funcionar. ¿Desea salir?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if res == QMessageBox.StandardButton.Yes:
                    import sys
                    sys.exit(0)
    
    def _select_data_folder(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de datos",
            self.config.data_dir or os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        if dir_path:
            self.config.data_dir = dir_path
            self.state_manager.set_last_data_dir(dir_path)
            self.state_manager.add_recent_data_dir(dir_path)
            self.data_folder_label.setText(f"Carpeta de trabajo: {dir_path}")
            
            # Reinitialize on data folder change
            self._initialize_services()
            self._create_views()
            
            active_sec = getattr(self.sidebar, "active_section", None) or "dashboard"
            self.sidebar.set_active(active_sec)
            self._switch_view(active_sec)
                
    def _initialize_services(self):
        if not self.config.data_dir:
            return
            
        self.storage = JsonStorageEngine(self.config.data_dir)
        self.storage.initialize_structure()
        
        self.recycle_bin_service = RecycleBinService(self.storage)
        self.custom_lists_service = CustomListsService(self.storage)
        self.technician_service = TechnicianService(self.storage, self.recycle_bin_service)
        self.library_service = LibraryService(self.storage, self.recycle_bin_service)
        self.client_service = ClientService(self.storage, self.recycle_bin_service)
        self.equipment_service = EquipmentService(self.storage, self.recycle_bin_service)
        self.incident_service = IncidentService(self.storage, self.recycle_bin_service)
        self.work_order_service = WorkOrderService(self.storage, self.recycle_bin_service, equipment_service=self.equipment_service, incident_service=self.incident_service)
        self.maintenance_service = MaintenanceService(self.storage)
        self.inventory_service = InventoryService(self.storage, self.recycle_bin_service, equipment_service=self.equipment_service)
        self.export_service = ExportService(self.storage)

        # Refresh company logo from workspace directory (e.g., after folder change or full backup restoration)
        if hasattr(self, 'sidebar'):
            self.sidebar.update_logo(self.state_manager.get_logo_path())
        
        # Defer auto-sync to background after UI is loaded and interactive
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, self._background_sync_histories)
        
    def _background_sync_histories(self):
        """Runs initial data integrity sync in the background so it doesn't block startup."""
        try:
            if self.equipment_service and self.inventory_service:
                self.equipment_service.sync_all_parts_history_from_inventory(self.inventory_service)
            if self.equipment_service and self.work_order_service:
                self.equipment_service.sync_all_service_history_from_work_orders(self.work_order_service)
        except Exception as e:
            print(f"Background sync notice: {e}")

    def _create_views(self):
        """Registers view creator factories for lazy loading on demand."""
        # Clear existing views
        while self.stacked_widget.count() > 0:
            widget = self.stacked_widget.widget(0)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
            
        self.views = {}
        
        # Register view constructors (lazy loading on demand)
        def _create_clients():
            from src.ui.views.clients_view import ClientsView
            return ClientsView(self.client_service)

        def _create_equipment():
            from src.ui.views.equipment_view import EquipmentView
            return EquipmentView(self.equipment_service, self.client_service, self.inventory_service, self.custom_lists_service, self.incident_service, self.export_service, self.library_service)

        def _create_incidents():
            from src.ui.views.incidents_view import IncidentsView
            return IncidentsView(self.incident_service, self.equipment_service, self.client_service, self.inventory_service, self.export_service, self.work_order_service, self.technician_service, self.library_service)

        def _create_work_orders():
            from src.ui.views.work_orders_view import WorkOrdersView
            return WorkOrdersView(self.work_order_service, self.equipment_service, self.client_service, self.inventory_service, self.export_service, self.technician_service)

        def _create_calendar():
            from src.ui.views.task_board_view import TaskBoardView
            return TaskBoardView(self.maintenance_service, self.work_order_service, self.equipment_service, self.client_service)

        def _create_technicians():
            from src.ui.views.technicians_view import TechniciansView
            return TechniciansView(self.technician_service)

        def _create_tools():
            from src.ui.views.panol_view import PanolView
            return PanolView(self.inventory_service, self.technician_service, self.client_service, self.equipment_service)

        def _create_spare_parts():
            from src.ui.views.spare_parts_view import SparePartsView
            return SparePartsView(self.inventory_service, self.equipment_service, self.client_service)

        def _create_library():
            from src.ui.views.library_view import LibraryView
            return LibraryView(self.library_service, self.equipment_service, self.client_service)

        self.view_creators = {
            "dashboard": lambda: DashboardView(self.equipment_service, self.work_order_service, self.maintenance_service, self.client_service, self.inventory_service, self.incident_service),
            "clients": _create_clients,
            "equipment": _create_equipment,
            "incidents": _create_incidents,
            "work_orders": _create_work_orders,
            "calendar": _create_calendar,
            "technicians": _create_technicians,
            "panol": _create_tools,
            "tools": _create_tools,
            "spare_parts": _create_spare_parts,
            "library": _create_library,
        }

    def _get_or_create_view(self, section_id: str) -> Optional[QWidget]:
        """Returns the view if already created, or instantiates and adds it to stacked_widget."""
        if section_id in self.views:
            return self.views[section_id]
            
        if hasattr(self, 'view_creators') and section_id in self.view_creators:
            try:
                creator_fn = self.view_creators[section_id]
                view_instance = creator_fn()
                self.views[section_id] = view_instance
                self.stacked_widget.addWidget(view_instance)
                return view_instance
            except Exception as e:
                placeholder = QWidget()
                layout = QVBoxLayout(placeholder)
                label = QLabel(f"Vista no disponible: {section_id}\n({str(e)})")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet("color: #94A3B8; font-size: 16px;")
                layout.addWidget(label)
                self.views[section_id] = placeholder
                self.stacked_widget.addWidget(placeholder)
                print(f"Failed to load {section_id}: {e}")
                return placeholder
        return None

    def _switch_view(self, section_id: str):
        view = self._get_or_create_view(section_id)
        if view:
            self.stacked_widget.setCurrentWidget(view)
            self._refresh_current_view()
            
    def _refresh_current_view(self):
        current_view = self.stacked_widget.currentWidget()
        if hasattr(current_view, 'refresh_data') and callable(current_view.refresh_data):
            current_view.refresh_data()
            
    def _open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            pass
        self.sidebar.update_logo(self.state_manager.get_logo_path())

    def closeEvent(self, event):
        self.state_manager.save_window_state(self)
        super().closeEvent(event)

