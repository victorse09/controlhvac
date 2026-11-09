import html
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QPushButton, QLabel, QFrame, QCheckBox, QMessageBox, QListWidget, QListWidgetItem,
    QScrollArea
)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QCursor
from src.ui.widgets.hvac_calendar import HVACCalendarWidget
from src.ui.widgets.detail_card import (
    clear_layout_widgets, build_section_card, build_kv_widget,
    build_rich_label, build_status_banner, build_empty_detail_card
)
from src.core.models.enums import WORK_ORDER_STATUS_LABELS, PRIORITY_LABELS
from src.ui.dialogs.work_order_dialog import WorkOrderDialog
from src.ui.icon_manager import IconManager


class CalendarView(QWidget):
    def __init__(self, maintenance_service, work_order_service, equipment_service, client_service, parent=None):
        super().__init__(parent)
        self.maintenance_service = maintenance_service
        self.work_order_service = work_order_service
        self.equipment_service = equipment_service
        self.client_service = client_service
        self.day_wos_map = {}
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter, 1)

        # Left side: Calendar Card + Controls
        left_card = QFrame()
        left_card.setObjectName("cardFrame")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        cal_header = QFrame()
        cal_header.setObjectName("eqCardHeader")
        cal_header.setStyleSheet(
            "QFrame#eqCardHeader {"
            "  background-color: #1E293B;"
            "  border-radius: 6px;"
            "  border-bottom: 2px solid #38BDF8;"
            "}"
        )
        ch_layout = QHBoxLayout(cal_header)
        ch_layout.setContentsMargins(12, 8, 12, 8)
        lbl_ch = QLabel("CALENDARIO DE MANTENIMIENTOS Y SERVICIOS")
        lbl_ch.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; background: transparent; border: none;")
        ch_layout.addWidget(lbl_ch)
        ch_layout.addStretch()

        self.btn_new = QPushButton(" + Nueva Programación / OT")
        self.btn_new.setObjectName("primaryButton")
        self.btn_new.setIcon(IconManager.get_icon("add.svg", "#000000", 16))
        self.btn_new.setIconSize(QSize(16, 16))
        self.btn_new.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_new.clicked.connect(self.on_new_programming)
        ch_layout.addWidget(self.btn_new)
        left_layout.addWidget(cal_header)
        
        self.calendar = HVACCalendarWidget()
        self.calendar.clicked.connect(self.on_date_selected)
        left_layout.addWidget(self.calendar, 1)
        
        filter_card = QFrame()
        filter_card.setStyleSheet("background-color: #0F172A; border: 1px solid #1E293B; border-radius: 6px;")
        filters_layout = QHBoxLayout(filter_card)
        filters_layout.setContentsMargins(12, 8, 12, 8)
        lbl_f = QLabel("FILTRAR POR TIPO:")
        lbl_f.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold; background: transparent; border: none;")
        filters_layout.addWidget(lbl_f)

        self.chk_prev = QCheckBox("Preventivo (OTM)")
        self.chk_corr = QCheckBox("Correctivo (OTS)")
        self.chk_one = QCheckBox("Otros / Puntuales")
        self.chk_prev.setChecked(True)
        self.chk_corr.setChecked(True)
        self.chk_one.setChecked(True)
        
        self.chk_prev.stateChanged.connect(self.refresh_data)
        self.chk_corr.stateChanged.connect(self.refresh_data)
        self.chk_one.stateChanged.connect(self.refresh_data)
        
        filters_layout.addWidget(self.chk_prev)
        filters_layout.addWidget(self.chk_corr)
        filters_layout.addWidget(self.chk_one)
        filters_layout.addStretch()
        left_layout.addWidget(filter_card)

        self.splitter.addWidget(left_card)

        # Right side: Scheduled activities cards
        self.right_frame = QFrame()
        self.right_frame.setObjectName("cardFrame")
        right_layout = QVBoxLayout(self.right_frame)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        header_row = QHBoxLayout()
        self.lbl_date = QLabel("Seleccione una fecha")
        self.lbl_date.setStyleSheet("font-size: 17px; font-weight: bold; color: #F8FAFC;")
        header_row.addWidget(self.lbl_date)
        header_row.addStretch()
        right_layout.addLayout(header_row)

        self.day_banner_container = QWidget()
        self.day_banner_layout = QVBoxLayout(self.day_banner_container)
        self.day_banner_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.day_banner_container)

        list_card = QFrame()
        list_card.setObjectName("eqSectionCard")
        list_card.setStyleSheet(
            "QFrame#eqSectionCard {"
            "  background-color: #0F172A;"
            "  border: 1px solid #1E293B;"
            "  border-radius: 8px;"
            "}"
        )
        lc_layout = QVBoxLayout(list_card)
        lc_layout.setContentsMargins(0, 0, 0, 0)
        lc_layout.setSpacing(0)

        lh = QFrame()
        lh.setObjectName("eqCardHeader")
        lh.setStyleSheet(
            "QFrame#eqCardHeader {"
            "  background-color: #1E293B;"
            "  border-top-left-radius: 7px;"
            "  border-top-right-radius: 7px;"
            "  border-bottom: 2px solid #F59E0B;"
            "}"
        )
        lh_lay = QHBoxLayout(lh)
        lh_lay.setContentsMargins(12, 6, 12, 6)
        lbl_lh = QLabel("ACTIVIDADES PROGRAMADAS EN EL DÍA (DOBLE CLIC PARA ABRIR)")
        lbl_lh.setStyleSheet("color: #F59E0B; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; background: transparent; border: none;")
        lh_lay.addWidget(lbl_lh)
        lc_layout.addWidget(lh)

        self.events_list = QListWidget()
        self.events_list.setStyleSheet("border: none; background: transparent; padding: 6px;")
        self.events_list.itemDoubleClicked.connect(self.on_event_double_clicked)
        lc_layout.addWidget(self.events_list, 1)

        right_layout.addWidget(list_card, 1)
        
        self.splitter.addWidget(self.right_frame)
        self.splitter.setSizes([560, 440])

    def refresh_data(self):
        try:
            wos = self.work_order_service.get_all_work_orders()
            events = {}
            for wo in wos:
                wtype = wo.work_order_type if hasattr(wo, 'work_order_type') else (wo.type.value if hasattr(wo.type, 'value') else str(wo.type))
                
                if wtype == "PREVENTIVE" and not self.chk_prev.isChecked():
                    continue
                if wtype == "CORRECTIVE" and not self.chk_corr.isChecked():
                    continue
                if wtype not in ("PREVENTIVE", "CORRECTIVE") and not self.chk_one.isChecked():
                    continue

                if wo.scheduled_date:
                    if wo.scheduled_date not in events:
                        events[wo.scheduled_date] = []
                    status_val = wo.status.value if hasattr(wo.status, 'value') else str(wo.status)
                    color = "#10B981" if status_val == "COMPLETED" else "#3B82F6" if status_val == "IN_PROGRESS" else "#F59E0B"
                    events[wo.scheduled_date].append({"type": wtype, "color": color, "title": wo.title})

            self.calendar.set_events(events)
            
            curr_date = self.calendar.selectedDate()
            if curr_date.isValid():
                self.on_date_selected(curr_date)

        except Exception as e:
            print(f"Error refreshing calendar: {e}")
        
    def on_date_selected(self, date):
        self.lbl_date.setText(f"Agenda del {date.toString('dd/MM/yyyy')}")
        self.events_list.clear()
        self.day_wos_map.clear()
        clear_layout_widgets(self.day_banner_layout)
        try:
            iso_date = date.toString(Qt.DateFormat.ISODate)
            wos = self.work_order_service.get_all_work_orders()
            day_wos = [wo for wo in wos if wo.scheduled_date == iso_date]
            
            filtered_day_wos = []
            for wo in day_wos:
                wtype = wo.work_order_type if hasattr(wo, 'work_order_type') else (wo.type.value if hasattr(wo.type, 'value') else str(wo.type))
                if wtype == "PREVENTIVE" and not self.chk_prev.isChecked():
                    continue
                if wtype == "CORRECTIVE" and not self.chk_corr.isChecked():
                    continue
                if wtype not in ("PREVENTIVE", "CORRECTIVE") and not self.chk_one.isChecked():
                    continue
                filtered_day_wos.append(wo)

            comp_cnt = sum(1 for w in filtered_day_wos if (w.status.value if hasattr(w.status, 'value') else str(w.status)) == "COMPLETED")
            pend_cnt = len(filtered_day_wos) - comp_cnt

            self.day_banner_layout.addWidget(
                build_status_banner([
                    ("TAREAS PROGRAMADAS", f"{len(filtered_day_wos)} órdenes", "#38BDF8", "#0C4A6E"),
                    ("ESTADO DEL DÍA", f"{comp_cnt} completadas / {pend_cnt} pendientes", "#10B981" if pend_cnt == 0 and comp_cnt > 0 else "#F59E0B", "#064E3B" if pend_cnt == 0 and comp_cnt > 0 else "#451A03"),
                ])
            )

            for wo in filtered_day_wos:
                status_val = wo.status.value if hasattr(wo.status, 'value') else str(wo.status)
                status_lbl = WORK_ORDER_STATUS_LABELS.get(wo.status, WORK_ORDER_STATUS_LABELS.get(status_val, status_val))
                badge = "🟢" if status_val == "COMPLETED" else "🔵" if status_val == "IN_PROGRESS" else "🟠"
                tech = getattr(wo, 'assigned_technician', '') or getattr(wo, 'assigned_to', '') or "Sin asignar"
                eq_tag = wo.equipment_tag or getattr(wo, 'manual_equipment_tag', '') or "General"
                item_text = f"{badge} [{wo.id}] {wo.title}\n    ⚙️ Equipo: {eq_tag} | Estado: {status_lbl} | Técnico: {tech}"
                item = QListWidgetItem(item_text)
                self.events_list.addItem(item)
                self.day_wos_map[self.events_list.count() - 1] = wo

            if self.events_list.count() == 0:
                item = QListWidgetItem("No hay actividades programadas para este día.")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.events_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def on_event_double_clicked(self, list_item):
        row = self.events_list.row(list_item)
        wo = self.day_wos_map.get(row)
        if wo:
            equipments = self.equipment_service.get_all_equipment()
            dialog = WorkOrderDialog(parent=self, equipment_list=equipments, work_order=wo)
            if dialog.exec():
                updated = dialog.get_work_order()
                self.work_order_service.save_work_order(updated)
                self.refresh_data()

    def on_new_programming(self):
        equipments = self.equipment_service.get_all_equipment()
        dialog = WorkOrderDialog(parent=self, equipment_list=equipments)
        
        sel_date = self.calendar.selectedDate()
        if sel_date.isValid() and hasattr(dialog, 'fecha_prog'):
            dialog.fecha_prog.setDate(sel_date)
            
        if dialog.exec():
            wo = dialog.get_work_order()
            self.work_order_service.save_work_order(wo)
            self.refresh_data()
