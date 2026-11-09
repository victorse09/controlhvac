from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QListWidget, QListWidgetItem, QAbstractItemView,
    QPushButton, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from src.ui.dialogs.work_order_dialog import WorkOrderDialog
from src.ui.icon_manager import IconManager
from src.core.models.enums import WorkOrderStatus, SERVICE_TYPE_LABELS, WORK_ORDER_STATUS_LABELS

class KanbanList(QListWidget):
    itemMoved = Signal(object, str) # wo, new_status

    def __init__(self, status_val, parent=None):
        super().__init__(parent)
        self.status_val = status_val
        self.setObjectName("kanbanList")
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    def dropEvent(self, event):
        super().dropEvent(event)
        # Identificar items recién movidos a esta lista
        for i in range(self.count()):
            item = self.item(i)
            wo = item.data(Qt.ItemDataRole.UserRole)
            if wo:
                current_status = wo.status.value if hasattr(wo.status, 'value') else str(wo.status)
                # Col_todo maneja tanto SCHEDULED como OVERDUE
                if self.status_val == "SCHEDULED" and current_status in ["SCHEDULED", "OVERDUE"]:
                    continue
                if current_status != self.status_val:
                    # Actualizar estado y emitir
                    wo.status = self.status_val
                    item.setData(Qt.ItemDataRole.UserRole, wo)
                    self.itemMoved.emit(wo, self.status_val)

class TaskBoardView(QWidget):
    def __init__(self, maintenance_service, work_order_service, equipment_service, client_service, parent=None):
        super().__init__(parent)
        self.maintenance_service = maintenance_service
        self.work_order_service = work_order_service
        self.equipment_service = equipment_service
        self.client_service = client_service
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Header controls
        header_layout = QHBoxLayout()
        title = QLabel("Tablero Kanban de Tareas")
        title.setObjectName("h1")
        header_layout.addWidget(title)
        
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItem("Todas las Tareas", "ALL")
        for st_val, st_lbl in SERVICE_TYPE_LABELS.items():
            self.filter_type_combo.addItem(st_lbl, st_val)
        self.filter_type_combo.currentIndexChanged.connect(self.refresh_data)
        
        lbl_filter = QLabel("Filtrar por Tipo:")
        lbl_filter.setObjectName("muted")
        lbl_filter.setStyleSheet("margin-left: 20px;")
        header_layout.addWidget(lbl_filter)
        header_layout.addWidget(self.filter_type_combo)
        
        header_layout.addStretch()
        
        self.btn_new = QPushButton("Nueva Tarea")
        self.btn_new.setObjectName("primaryButton")
        self.btn_new.setIcon(IconManager.get_icon("add.svg", "#FFFFFF"))
        self.btn_new.clicked.connect(self.on_new_task)
        header_layout.addWidget(self.btn_new)
        
        main_layout.addLayout(header_layout)
        
        # Kanban board layout
        board_layout = QHBoxLayout()
        board_layout.setSpacing(16)
        
        # Columns
        self.col_todo = KanbanList("SCHEDULED")
        self.col_in_progress = KanbanList("IN_PROGRESS")
        self.col_done = KanbanList("COMPLETED")
        
        self.col_todo.itemMoved.connect(self.on_item_moved)
        self.col_in_progress.itemMoved.connect(self.on_item_moved)
        self.col_done.itemMoved.connect(self.on_item_moved)
        
        self.col_todo.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.col_in_progress.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.col_done.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        board_layout.addWidget(self._create_kanban_column("Pendientes", self.col_todo, "#F59E0B"))
        board_layout.addWidget(self._create_kanban_column("En Progreso", self.col_in_progress, "#3B82F6"))
        board_layout.addWidget(self._create_kanban_column("Completadas", self.col_done, "#10B981"))
        
        main_layout.addLayout(board_layout)
        
    def _create_kanban_column(self, title, list_widget, color):
        frame = QFrame()
        frame.setObjectName("cardFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color}; margin-bottom: 5px;")
        layout.addWidget(lbl_title)
        layout.addWidget(list_widget)
        
        return frame

    def refresh_data(self):
        self.col_todo.clear()
        self.col_in_progress.clear()
        self.col_done.clear()
        
        filter_val = self.filter_type_combo.currentData()
        
        wos = self.work_order_service.get_all_work_orders()
        for wo in wos:
            st = wo.service_type if hasattr(wo, 'service_type') else ""
            if filter_val != "ALL" and st != filter_val:
                continue
                
            status_val = wo.status.value if hasattr(wo.status, 'value') else str(wo.status)
            
            eq_tag = wo.equipment_tag or wo.manual_equipment_tag or "Sin Equipo"
            st_lbl = SERVICE_TYPE_LABELS.get(st, st) if st else "Desconocido"
            tech = wo.assigned_technician or "Sin asignar"
            
            card_text = f"#{wo.id[:8]} - {wo.title}\nEquipo: {eq_tag}\nTipo: {st_lbl}\nTécnico: {tech}"
            
            item = QListWidgetItem(card_text)
            item.setData(Qt.ItemDataRole.UserRole, wo)
            item.setToolTip(wo.description or "Doble clic para ver detalles")
            
            if status_val in ["SCHEDULED", "OVERDUE"]:
                self.col_todo.addItem(item)
            elif status_val == "IN_PROGRESS":
                self.col_in_progress.addItem(item)
            elif status_val == "COMPLETED":
                self.col_done.addItem(item)

    def on_item_moved(self, wo, new_status):
        self.work_order_service.save_work_order(wo)

    def on_item_double_clicked(self, item):
        wo = item.data(Qt.ItemDataRole.UserRole)
        if wo:
            equipments = self.equipment_service.get_all_equipment()
            dialog = WorkOrderDialog(parent=self, equipment_list=equipments, work_order=wo)
            if dialog.exec():
                updated = dialog.get_work_order()
                self.work_order_service.save_work_order(updated)
                self.refresh_data()

    def on_new_task(self):
        equipments = self.equipment_service.get_all_equipment()
        dialog = WorkOrderDialog(parent=self, equipment_list=equipments)
        if dialog.exec():
            wo = dialog.get_work_order()
            self.work_order_service.save_work_order(wo)
            self.refresh_data()
