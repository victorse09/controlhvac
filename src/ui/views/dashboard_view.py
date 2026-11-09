import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QScrollArea, QFrame, QTableView, QMessageBox, QHeaderView,
    QSplitter, QSizePolicy
)
from PySide6.QtCore import Qt, QDate
from src.core.models.enums import WorkOrderStatus, SYSTEM_TYPE_LABELS
from src.ui.widgets.stat_card import StatCard
from src.ui.widgets.table_state_helper import setup_modern_table
from src.ui.models.table_models import WorkOrderTableModel, EquipmentTableModel
from src.ui.dialogs.work_order_dialog import WorkOrderDialog
from src.ui.dialogs.equipment_dialog import EquipmentDialog
from src.ui.icon_manager import IconManager


class DashboardView(QWidget):
    def __init__(self, equipment_service, work_order_service, maintenance_service, client_service=None, inventory_service=None, incident_service=None, parent=None):
        super().__init__(parent)
        self.equipment_service = equipment_service
        self.work_order_service = work_order_service
        self.maintenance_service = maintenance_service
        self.client_service = client_service
        self.inventory_service = inventory_service
        self.incident_service = incident_service
        self.setup_ui()
        self.refresh_data()

    def _build_dashboard_card(self, title: str, accent_color: str, icon_name: str = None) -> tuple[QFrame, QVBoxLayout, QLabel]:
        card = QFrame()
        card.setObjectName("dashSectionCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("dashCardHeader")
        header.setStyleSheet(
            f"QFrame#dashCardHeader {{"
            f"  border-bottom: 2px solid {accent_color};"
            f"}}"
        )
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 6, 12, 6)
        h_layout.setSpacing(8)

        if icon_name:
            ic_lbl = QLabel()
            ic_lbl.setPixmap(IconManager.get_icon(icon_name, accent_color).pixmap(15, 15))
            ic_lbl.setStyleSheet("background: transparent; border: none;")
            h_layout.addWidget(ic_lbl)

        lbl_h = QLabel(title.upper())
        lbl_h.setStyleSheet(
            f"color: {accent_color}; font-size: 11px; font-weight: bold; "
            f"letter-spacing: 0.6px; background: transparent; border: none;"
        )
        h_layout.addWidget(lbl_h)
        h_layout.addStretch()

        hint_lbl = QLabel("↕ Arrastre los bordes para ajustar altura")
        hint_lbl.setObjectName("muted")
        hint_lbl.setStyleSheet("font-size: 10px; background: transparent; border: none;")
        h_layout.addWidget(hint_lbl)

        card_layout.addWidget(header)

        body = QWidget()
        body.setStyleSheet("background: transparent; border: none;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(10, 8, 10, 8)
        body_layout.setSpacing(6)
        card_layout.addWidget(body, 1)
        return card, body_layout, lbl_h

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        main_layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # Top row: Stats Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        self.stat_total_equip = StatCard("Total Equipos", "0", IconManager.get_icon("equipment", "#38BDF8"), accent_color="#38BDF8")
        self.stat_fault_equip = StatCard("Equipos en Falla", "0", IconManager.get_icon("fault.svg", "#EF4444"), accent_color="#EF4444")
        self.stat_pending_wo = StatCard("OTs Pendientes", "0", IconManager.get_icon("work_orders", "#F59E0B"), accent_color="#F59E0B")
        self.stat_overdue_wo = StatCard("OTs Vencidas", "0", IconManager.get_icon("warning", "#EF4444"), accent_color="#EF4444")
        
        stats_layout.addWidget(self.stat_total_equip)
        stats_layout.addWidget(self.stat_fault_equip)
        stats_layout.addWidget(self.stat_pending_wo)
        stats_layout.addWidget(self.stat_overdue_wo)
        layout.addLayout(stats_layout)

        # Vertical Resizable Splitter for Dashboard Sections
        self.v_splitter = QSplitter(Qt.Orientation.Vertical)
        self.v_splitter.setChildrenCollapsible(False)
        self.v_splitter.setHandleWidth(6)
        self.v_splitter.setStyleSheet(
            "QSplitter::handle:vertical {"
            "  background-color: #1E293B;"
            "  height: 6px;"
            "  border-radius: 3px;"
            "  margin: 2px 40px;"
            "}"
            "QSplitter::handle:vertical:hover {"
            "  background-color: #38BDF8;"
            "}"
        )

        # 1. Faulty Equipments Section
        self.fault_frame, fault_layout, self.lbl_fault_title = self._build_dashboard_card(
            "Equipos en Falla o en Observación", "#EF4444", "fault.svg"
        )
        self.fault_frame.setMinimumHeight(210)
        
        self.fault_empty_lbl = QLabel("● Todos los equipos operan con normalidad.")
        self.fault_empty_lbl.setStyleSheet(
            "color: #10B981; background-color: #064E3B; border: 1px solid #10B981; "
            "border-radius: 6px; font-weight: 600; font-size: 12px; padding: 8px 12px;"
        )
        self.fault_empty_lbl.setVisible(False)
        fault_layout.addWidget(self.fault_empty_lbl)

        self.fault_table = QTableView()
        self.fault_table.setMinimumHeight(155)
        self.fault_model = EquipmentTableModel([])
        self.fault_table.setModel(self.fault_model)
        self.fault_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.fault_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.fault_table.doubleClicked.connect(self._on_table_double_clicked_fault)
        storage = getattr(self.equipment_service, "storage", None)
        setup_modern_table(
            self.fault_table,
            storage=storage,
            settings_key="dashboard_fault_table",
            default_widths=[140, 175, 130, 100, 120, 150, 170],
        )
        fault_layout.addWidget(self.fault_table, 1)
        self.v_splitter.addWidget(self.fault_frame)

        # 2. Overdue WOs
        self.overdue_frame, overdue_layout, self.lbl_overdue_title = self._build_dashboard_card(
            "Órdenes de Trabajo Vencidas", "#F59E0B", "warning.svg"
        )
        self.overdue_frame.setMinimumHeight(140)

        self.overdue_empty_lbl = QLabel("● Sin órdenes de trabajo vencidas.")
        self.overdue_empty_lbl.setStyleSheet(
            "color: #10B981; background-color: #064E3B; border: 1px solid #10B981; "
            "border-radius: 6px; font-weight: 600; font-size: 12px; padding: 6px 12px;"
        )
        self.overdue_empty_lbl.setVisible(False)
        overdue_layout.addWidget(self.overdue_empty_lbl)
        
        self.overdue_table = QTableView()
        self.overdue_table.setMinimumHeight(110)
        self.overdue_model = WorkOrderTableModel([])
        self.overdue_table.setModel(self.overdue_model)
        self.overdue_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.overdue_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.overdue_table.doubleClicked.connect(self._on_table_double_clicked_overdue)
        setup_modern_table(
            self.overdue_table,
            storage=storage,
            settings_key="dashboard_overdue_table",
            default_widths=[125, 140, 185, 105, 125, 125, 145],
        )
        overdue_layout.addWidget(self.overdue_table, 1)
        self.v_splitter.addWidget(self.overdue_frame)

        # 3. Upcoming Maint
        self.upcoming_frame, upcoming_layout, self.lbl_upcoming_title = self._build_dashboard_card(
            "Próximos Mantenimientos (Siguientes 7 Días)", "#38BDF8", "calendar.svg"
        )
        self.upcoming_frame.setMinimumHeight(140)

        self.upcoming_empty_lbl = QLabel("● No hay mantenimientos programados para los próximos 7 días.")
        self.upcoming_empty_lbl.setObjectName("muted")
        self.upcoming_empty_lbl.setStyleSheet(
            "border-radius: 6px; font-weight: 500; font-size: 12px; padding: 6px 12px;"
        )
        self.upcoming_empty_lbl.setVisible(False)
        upcoming_layout.addWidget(self.upcoming_empty_lbl)
        
        self.upcoming_table = QTableView()
        self.upcoming_table.setMinimumHeight(110)
        self.upcoming_model = WorkOrderTableModel([])
        self.upcoming_table.setModel(self.upcoming_model)
        self.upcoming_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.upcoming_table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.upcoming_table.doubleClicked.connect(self._on_table_double_clicked_upcoming)
        setup_modern_table(
            self.upcoming_table,
            storage=storage,
            settings_key="dashboard_upcoming_table",
            default_widths=[125, 140, 185, 105, 125, 125, 145],
        )
        upcoming_layout.addWidget(self.upcoming_table, 1)
        self.v_splitter.addWidget(self.upcoming_frame)

        # 4. Equipment Distribution (Compact 5-column layout)
        self.dist_frame, dist_layout, self.lbl_dist_title = self._build_dashboard_card(
            "Distribución de Equipos por Tipo de Sistema", "#10B981", "equipment"
        )
        self.dist_frame.setMinimumHeight(115)
        self.dist_content_layout = QGridLayout()
        self.dist_content_layout.setContentsMargins(0, 0, 0, 0)
        self.dist_content_layout.setHorizontalSpacing(8)
        self.dist_content_layout.setVerticalSpacing(6)
        dist_layout.addLayout(self.dist_content_layout)
        dist_layout.addStretch()
        self.v_splitter.addWidget(self.dist_frame)

        # Give generous initial height to Faulty Equipment table and balanced heights to others
        self.v_splitter.setStretchFactor(0, 4)
        self.v_splitter.setStretchFactor(1, 2)
        self.v_splitter.setStretchFactor(2, 2)
        self.v_splitter.setStretchFactor(3, 1)
        self.v_splitter.setSizes([320, 170, 170, 130])

        layout.addWidget(self.v_splitter, 1)

    def refresh_data(self):
        try:
            equipments = self.equipment_service.get_all_equipment()
            self.stat_total_equip.set_value(str(len(equipments)))

            # Faulty equipment
            faulty = [
                e for e in equipments 
                if (e.status.value if hasattr(e.status, 'value') else str(e.status)) in ["FAULT", "WARNING", "DECOMMISSIONED"]
            ]
            self.stat_fault_equip.set_value(str(len(faulty)))
            self.lbl_fault_title.setText(f"EQUIPOS EN FALLA O EN OBSERVACIÓN ({len(faulty)})")
            self.fault_model.set_data(faulty)
            
            if len(faulty) == 0:
                self.fault_table.setVisible(False)
                self.fault_empty_lbl.setVisible(True)
                self.fault_frame.setMinimumHeight(80)
            else:
                self.fault_table.setVisible(True)
                self.fault_empty_lbl.setVisible(False)
                self.fault_frame.setMinimumHeight(230)

            # Work orders
            wos = self.work_order_service.get_all_work_orders()
            pending = [
                wo for wo in wos 
                if (wo.status.value if hasattr(wo.status, 'value') else str(wo.status)) in ["SCHEDULED", "IN_PROGRESS"]
            ]
            self.stat_pending_wo.set_value(str(len(pending)))

            today = QDate.currentDate().toString(Qt.DateFormat.ISODate)
            next_week = QDate.currentDate().addDays(7).toString(Qt.DateFormat.ISODate)

            overdue = [wo for wo in pending if wo.scheduled_date and wo.scheduled_date < today]
            self.stat_overdue_wo.set_value(str(len(overdue)))
            self.lbl_overdue_title.setText(f"ÓRDENES DE TRABAJO VENCIDAS ({len(overdue)})")
            self.overdue_model.set_data(overdue)
            if len(overdue) == 0:
                self.overdue_empty_lbl.setVisible(True)
                self.overdue_frame.setMinimumHeight(105)
            else:
                self.overdue_empty_lbl.setVisible(False)
                self.overdue_frame.setMinimumHeight(180)

            upcoming = [wo for wo in wos if wo.scheduled_date and today <= wo.scheduled_date <= next_week]
            self.lbl_upcoming_title.setText(f"PRÓXIMOS MANTENIMIENTOS - SIGUIENTES 7 DÍAS ({len(upcoming)})")
            self.upcoming_model.set_data(upcoming)
            if len(upcoming) == 0:
                self.upcoming_empty_lbl.setVisible(True)
                self.upcoming_frame.setMinimumHeight(105)
            else:
                self.upcoming_empty_lbl.setVisible(False)
                self.upcoming_frame.setMinimumHeight(180)

            # Adjust splitter sizes dynamically so non-empty tables get plenty of room
            f_size = 340 if len(faulty) > 0 else 95
            o_size = 200 if len(overdue) > 0 else 115
            u_size = 200 if len(upcoming) > 0 else 115
            self.v_splitter.setSizes([f_size, o_size, u_size, 125])

            # Distribution (5 columns compact badges)
            while self.dist_content_layout.count():
                item = self.dist_content_layout.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.hide()
                    w.setParent(None)
                    w.deleteLater()
            
            dist_map = {}
            for e in equipments:
                raw_st = e.system_type.value if hasattr(e.system_type, 'value') else str(e.system_type)
                label_st = SYSTEM_TYPE_LABELS.get(e.system_type, SYSTEM_TYPE_LABELS.get(raw_st, raw_st))
                dist_map[label_st] = dist_map.get(label_st, 0) + 1
            
            max_cols = 5
            row, col = 0, 0
            for stype_lbl, count in sorted(dist_map.items(), key=lambda x: -x[1]):
                badge = QFrame()
                badge.setObjectName("distBadgeFrame")
                b_lay = QHBoxLayout(badge)
                b_lay.setContentsMargins(8, 5, 8, 5)
                b_lay.setSpacing(6)
                lbl_name = QLabel(stype_lbl)
                lbl_name.setObjectName("richBodyLabel")
                lbl_name.setStyleSheet("font-size: 11px; font-weight: 600; background: transparent; border: none;")
                lbl_cnt = QLabel(str(count))
                lbl_cnt.setObjectName("distCountBadge")
                b_lay.addWidget(lbl_name, 1)
                b_lay.addWidget(lbl_cnt, 0, Qt.AlignmentFlag.AlignRight)
                self.dist_content_layout.addWidget(badge, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            for c_idx in range(max_cols):
                self.dist_content_layout.setColumnStretch(c_idx, 1)

        except Exception as e:
            print(f"Error refreshing dashboard: {e}")

    def _on_table_double_clicked_fault(self, index):
        eq = self.fault_model.get_item(index.row())
        if eq:
            dialog = EquipmentDialog(
                parent=self, 
                client_service=self.client_service, 
                inventory_service=self.inventory_service, 
                equipment=eq
            )
            if dialog.exec():
                updated = dialog.get_equipment()
                self.equipment_service.save_equipment(updated)
                if self.incident_service:
                    self.incident_service.sync_incident_from_equipment_change(updated)
                self.refresh_data()

    def _on_table_double_clicked_overdue(self, index):
        wo = self.overdue_model.get_item(index.row())
        if wo:
            equipments = self.equipment_service.get_all_equipment()
            dialog = WorkOrderDialog(parent=self, equipment_list=equipments, work_order=wo)
            if dialog.exec():
                updated = dialog.get_work_order()
                self.work_order_service.save_work_order(updated)
                self.refresh_data()

    def _on_table_double_clicked_upcoming(self, index):
        wo = self.upcoming_model.get_item(index.row())
        if wo:
            equipments = self.equipment_service.get_all_equipment()
            dialog = WorkOrderDialog(parent=self, equipment_list=equipments, work_order=wo)
            if dialog.exec():
                updated = dialog.get_work_order()
                self.work_order_service.save_work_order(updated)
                self.refresh_data()
