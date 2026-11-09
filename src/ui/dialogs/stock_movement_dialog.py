from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QSpinBox,
    QLineEdit, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QCursor

from src.ui.icon_manager import IconManager
from src.core.models.inventory import SparePart
from src.ui.dialogs.equipment_dialog import _create_dialog_card


class StockMovementDialog(QDialog):
    """Dialog for recording detailed incoming and outgoing spare part stock movements."""

    IN_REASONS = [
        "Reposición de stock",
        "Adquisición / Compra nueva",
        "Ajuste de stock (Conteo físico)",
        "Devolución de repuesto no utilizado",
        "Personalizado"
    ]

    OUT_REASONS = [
        "Mantenimiento / Reparación",
        "Asignar / Instalar en Equipo",
        "Envío a otra Instalación / Sede",
        "Caducado o dañado",
        "Ajuste de stock (Merma o pérdida)",
        "Personalizado"
    ]

    def __init__(self, spare_part: SparePart, movement_type: str = "IN", equipment_service=None, client_service=None, parent=None):
        super().__init__(parent)
        self.spare_part = spare_part
        self.movement_type = movement_type.upper()  # "IN" or "OUT"
        self.equipment_service = equipment_service
        self.client_service = client_service

        self.is_in = (self.movement_type == "IN")

        action_title = "Ingreso de Stock (+)" if self.is_in else "Salida / Egreso de Stock (-)"
        self.setWindowTitle(f"{action_title} - {self.spare_part.name}")
        self.resize(560, 520)
        self.setModal(True)

        self.setup_ui()
        self._on_reason_changed()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(14, 14, 14, 14)

        # ── Header Banner ──
        header_frame = QFrame()
        header_frame.setObjectName("dialogHeaderBanner")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(14)

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
        header_layout.addWidget(icon_badge)

        part_info_layout = QVBoxLayout()
        part_info_layout.setSpacing(2)

        lbl_pname = QLabel(f"{self.spare_part.name}  (Cód: {self.spare_part.part_number or 'N/A'})")
        lbl_pname.setObjectName("detailTitleLabel")
        lbl_pname.setStyleSheet("font-size: 15px; font-weight: 700; background: transparent;")

        unit_str = getattr(self.spare_part, 'unit', 'unid.')
        lbl_stock = QLabel(f"Stock Actual: {self.spare_part.quantity} {unit_str}  |  Ubicación: {self.spare_part.location or 'Bodega Principal'}")
        lbl_stock.setObjectName("kvKeyLabel")

        part_info_layout.addWidget(lbl_pname)
        part_info_layout.addWidget(lbl_stock)
        header_layout.addLayout(part_info_layout, 1)

        pill_txt = f"●  {self.spare_part.quantity} {unit_str}"
        pill_bg = "#064E3B" if self.is_in else "#451A03"
        lbl_pill = QLabel(pill_txt)
        lbl_pill.setStyleSheet(
            f"background-color: {pill_bg}; color: {accent}; border: 1px solid {accent}; "
            f"border-radius: 5px; padding: 4px 10px; font-weight: bold; font-size: 11px;"
        )
        header_layout.addWidget(lbl_pill)

        main_layout.addWidget(header_frame)

        # ── Movement Details Card ──
        card, card_body = _create_dialog_card("Detalles del Movimiento de Stock", accent)
        form_layout = QFormLayout(card_body)
        form_layout.setContentsMargins(16, 14, 16, 16)
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        qty_row = QHBoxLayout()
        self.spin_qty = QSpinBox()
        self.spin_qty.setMinimum(1)
        if self.is_in:
            self.spin_qty.setMaximum(999999)
            self.spin_qty.setValue(1)
        else:
            max_out = max(1, self.spare_part.quantity)
            self.spin_qty.setMaximum(max_out)
            self.spin_qty.setValue(1)

        self.spin_qty.setFixedWidth(120)
        lbl_unit = QLabel(unit_str)
        lbl_unit.setObjectName("kvKeyLabel")
        qty_row.addWidget(self.spin_qty)
        qty_row.addWidget(lbl_unit)
        qty_row.addStretch()
        form_layout.addRow("Cantidad *:", qty_row)

        self.combo_reason = QComboBox()
        reasons_list = self.IN_REASONS if self.is_in else self.OUT_REASONS
        for r in reasons_list:
            self.combo_reason.addItem(r)
        self.combo_reason.currentIndexChanged.connect(self._on_reason_changed)
        form_layout.addRow("Motivo / Razón *:", self.combo_reason)

        self.txt_custom_reason = QLineEdit()
        self.txt_custom_reason.setPlaceholderText("Escriba el motivo personalizado...")
        self.lbl_custom_reason = QLabel("Motivo Personalizado *:")
        form_layout.addRow(self.lbl_custom_reason, self.txt_custom_reason)

        self.combo_equipment = QComboBox()
        self._populate_equipments()
        self.lbl_equipment = QLabel("Equipo Destino *:")
        form_layout.addRow(self.lbl_equipment, self.combo_equipment)

        self.combo_dest_client = QComboBox()
        self.combo_dest_site = QComboBox()
        self._populate_destinations()
        self.combo_dest_client.currentIndexChanged.connect(self._on_dest_client_changed)

        self.dest_widget = QWidget()
        self.dest_widget.setObjectName("eqCardBody")
        dest_layout = QVBoxLayout(self.dest_widget)
        dest_layout.setContentsMargins(0, 0, 0, 0)
        dest_layout.setSpacing(4)
        dest_layout.addWidget(self.combo_dest_client)
        dest_layout.addWidget(self.combo_dest_site)

        self.lbl_destination = QLabel("Instalación Destino *:")
        form_layout.addRow(self.lbl_destination, self.dest_widget)

        self.txt_reference = QLineEdit()
        if self.is_in:
            self.txt_reference.setPlaceholderText("Ej: Factura N° 12450, Guía de Despacho 883...")
            form_layout.addRow("N° Factura / Guía / Ref:", self.txt_reference)
        else:
            self.txt_reference.setPlaceholderText("Ej: OT-0042, Solicitud Mantenimiento #15...")
            form_layout.addRow("N° OT / Solicitud / Ref:", self.txt_reference)

        self.txt_performed_by = QLineEdit("Usuario")
        self.txt_performed_by.setPlaceholderText("Nombre del técnico o responsable...")
        form_layout.addRow("Responsable / Técnico:", self.txt_performed_by)

        self.txt_notes = QLineEdit()
        self.txt_notes.setPlaceholderText("Observaciones o comentarios adicionales...")
        form_layout.addRow("Observaciones:", self.txt_notes)

        main_layout.addWidget(card, 1)

        # ── Footer Bar ──
        footer_bar = QFrame()
        footer_bar.setObjectName("dialogFooterBar")
        btn_layout = QHBoxLayout(footer_bar)
        btn_layout.setContentsMargins(14, 10, 14, 10)
        btn_layout.setSpacing(10)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        btn_layout.addStretch()

        btn_action_label = "Registrar Entrada (+)" if self.is_in else "Registrar Salida (-)"
        btn_obj_name = "successButton" if self.is_in else "primaryButton"

        self.btn_confirm = QPushButton(btn_action_label)
        self.btn_confirm.setObjectName(btn_obj_name)
        self.btn_confirm.setIcon(IconManager.get_icon(icon_name, "#FFFFFF" if self.is_in else "#000000", 16))
        self.btn_confirm.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_confirm.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.btn_confirm)

        main_layout.addWidget(footer_bar)

    def _populate_equipments(self):
        self.combo_equipment.clear()
        if not self.equipment_service:
            return
        all_eq = self.equipment_service.get_all_equipment()
        for eq in all_eq:
            loc = eq.floor_area or eq.location_description or "General"
            bms = f" [BMS: {eq.bms_id}]" if getattr(eq, 'bms_id', '') else ""
            label = f"{eq.tag}{bms} - {eq.manufacturer or ''} {eq.model_number or ''} ({loc})".strip()
            self.combo_equipment.addItem(label, (eq.id, eq.tag))

    def _populate_destinations(self):
        self.combo_dest_client.clear()
        if not self.client_service:
            return
        clients = self.client_service.get_all_clients()
        for c in clients:
            self.combo_dest_client.addItem(c.company_name, c.id)
        self._on_dest_client_changed()

    def _on_dest_client_changed(self):
        self.combo_dest_site.clear()
        cid = self.combo_dest_client.currentData()
        if cid and self.client_service:
            sites = self.client_service.get_sites_for_client(cid)
            for s in sites:
                self.combo_dest_site.addItem(s.name, s.id)

    def _on_reason_changed(self):
        reason = self.combo_reason.currentText()
        is_custom = (reason == "Personalizado")
        self.lbl_custom_reason.setVisible(is_custom)
        self.txt_custom_reason.setVisible(is_custom)

        is_equip = (not self.is_in and reason == "Asignar / Instalar en Equipo")
        self.lbl_equipment.setVisible(is_equip)
        self.combo_equipment.setVisible(is_equip)

        is_dest = (not self.is_in and reason == "Envío a otra Instalación / Sede")
        self.lbl_destination.setVisible(is_dest)
        self.dest_widget.setVisible(is_dest)

    def _on_confirm(self):
        qty = self.spin_qty.value()
        if qty <= 0:
            QMessageBox.warning(self, "Cantidad Inválida", "La cantidad debe ser mayor a 0.")
            return

        if not self.is_in and qty > self.spare_part.quantity:
            QMessageBox.warning(self, "Stock Insuficiente", f"No hay suficiente stock disponible. Stock actual: {self.spare_part.quantity}")
            return

        selected_reason = self.combo_reason.currentText()
        if selected_reason == "Personalizado":
            custom_val = self.txt_custom_reason.text().strip()
            if not custom_val:
                QMessageBox.warning(self, "Motivo Requerido", "Por favor ingrese el motivo personalizado del movimiento.")
                return

        self.accept()

    def get_movement_data(self) -> dict:
        reason = self.combo_reason.currentText()
        if reason == "Personalizado":
            final_reason = self.txt_custom_reason.text().strip() or "Personalizado"
        else:
            final_reason = reason

        eq_id = ""
        eq_tag = ""
        if not self.is_in and reason == "Asignar / Instalar en Equipo":
            eq_data = self.combo_equipment.currentData()
            if eq_data:
                eq_id, eq_tag = eq_data

        destination_str = ""
        if not self.is_in and reason == "Envío a otra Instalación / Sede":
            c_name = self.combo_dest_client.currentText()
            s_name = self.combo_dest_site.currentText()
            destination_str = f"{c_name} - {s_name}" if s_name else c_name

        return {
            "part_id": self.spare_part.id,
            "movement_type": self.movement_type,
            "quantity": self.spin_qty.value(),
            "reason": final_reason,
            "reference": self.txt_reference.text().strip(),
            "equipment_id": eq_id,
            "equipment_tag": eq_tag,
            "destination": destination_str,
            "performed_by": self.txt_performed_by.text().strip() or "Usuario",
            "notes": self.txt_notes.text().strip()
        }
