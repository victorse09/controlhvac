import os
import re
from datetime import datetime
from typing import List, Any

_HVACReportPDF_Class = None

def get_hvac_report_pdf_class():
    """Lazily import FPDF and define/return HVACReportPDF class to avoid 1.8s startup overhead."""
    global _HVACReportPDF_Class
    if _HVACReportPDF_Class is not None:
        return _HVACReportPDF_Class

    from fpdf import FPDF

    class _InternalHVACReportPDF(FPDF):
        def __init__(self, title_text="Informe de Avería / Incidencia", subtitle_text="ControlHVAC CMMS - Climatización", logo_path=""):
            super().__init__()
            self.title_text = title_text
            self.subtitle_text = subtitle_text
            self.logo_path = logo_path
            self.alias_nb_pages()
            self.set_margins(12, 34, 12)

        def _enc(self, txt: str) -> str:
            if not txt:
                return ""
            return str(txt).encode('latin-1', 'replace').decode('latin-1')

        def header(self):
            # Dark top banner #2B2E3D
            self.set_fill_color(43, 46, 61)
            self.rect(0, 0, 210, 25, 'F')
            
            # Orange accent bar #F15A29
            self.set_fill_color(241, 90, 41)
            self.rect(0, 25, 210, 2, 'F')
            
            # Logo on left
            if self.logo_path and os.path.exists(self.logo_path):
                try:
                    self.image(self.logo_path, x=10, y=3, h=19)
                except Exception:
                    self.set_xy(10, 7)
                    self.set_font("helvetica", "B", 14)
                    self.set_text_color(255, 255, 255)
                    self.cell(60, 10, self._enc("ControlHVAC"))
            else:
                self.set_xy(10, 7)
                self.set_font("helvetica", "B", 14)
                self.set_text_color(255, 255, 255)
                self.cell(60, 10, self._enc("ControlHVAC"))
                
            # Title on right
            self.set_xy(80, 4)
            self.set_font("helvetica", "B", 13)
            self.set_text_color(255, 255, 255)
            self.cell(118, 7, self._enc(self.title_text), align="R")
            
            self.set_xy(80, 13)
            self.set_font("helvetica", "", 9)
            self.set_text_color(203, 213, 225)
            self.cell(118, 6, self._enc(self.subtitle_text), align="R")
            
            # Position cursor strictly below header banner (y=35mm)
            self.set_y(35)

        def footer(self):
            self.set_y(-15)
            self.set_draw_color(203, 213, 225)
            self.line(12, 282, 198, 282)
            
            self.set_font("helvetica", "I", 8)
            self.set_text_color(148, 163, 184)
            self.cell(120, 10, self._enc("ControlHVAC CMMS - Suite de Mantenimiento y Climatización"), align="L")
            self.cell(66, 10, self._enc(f"Página {self.page_no()} de {{nb}}"), align="R")

        def add_section_title(self, title: str):
            self.ln(3)
            self.set_font("helvetica", "B", 11)
            self.set_text_color(241, 90, 41) # Orange title
            self.cell(0, 6, self._enc(title), new_x="LMARGIN", new_y="NEXT")
            
            # Underline
            y = self.get_y()
            self.set_draw_color(241, 90, 41)
            self.set_line_width(0.3)
            self.line(12, y, 198, y)
            self.ln(3)

        def add_metadata_grid(self, items: list):
            """Renders 2-column key-value pairs."""
            self.set_font("helvetica", "", 9)
            for i in range(0, len(items), 2):
                k1, v1 = items[i]
                self.set_font("helvetica", "B", 9)
                self.set_text_color(30, 41, 59)
                self.cell(45, 6, self._enc(f"{k1}:"), align="L")
                self.set_font("helvetica", "", 9)
                self.set_text_color(71, 85, 105)
                self.cell(48, 6, self._enc(str(v1)), align="L")
                
                if i + 1 < len(items):
                    k2, v2 = items[i+1]
                    self.set_font("helvetica", "B", 9)
                    self.set_text_color(30, 41, 59)
                    self.cell(45, 6, self._enc(f"{k2}:"), align="L")
                    self.set_font("helvetica", "", 9)
                    self.set_text_color(71, 85, 105)
                    self.cell(48, 6, self._enc(str(v2)), align="L")
                self.ln(6)
            self.ln(2)

        def add_text_box(self, content: str):
            if not content:
                content = "Sin información registrada."
            self.set_fill_color(248, 250, 252)
            self.set_draw_color(226, 232, 240)
            self.set_font("helvetica", "", 9)
            self.set_text_color(51, 65, 85)
            self.multi_cell(186, 6, self._enc(content), border=1, fill=True)
            self.ln(2)

        def add_signature_block(self, technician_name: str = ""):
            self.ln(8)
            if self.get_y() > 235:
                self.add_page()
                
            y = self.get_y() + 15
            self.set_xy(130, y)
            self.set_draw_color(30, 41, 59)
            self.line(130, y, 190, y)
            
            self.set_xy(130, y + 2)
            self.set_font("helvetica", "B", 9)
            self.set_text_color(30, 41, 59)
            self.cell(60, 5, self._enc("Analista - Técnico"), align="C", new_x="LMARGIN", new_y="NEXT")
            
            tech_label = technician_name if technician_name else "Victor Saavedra E."
            self.set_xy(130, y + 7)
            self.set_font("helvetica", "", 9)
            self.set_text_color(71, 85, 105)
            self.cell(60, 5, self._enc(tech_label), align="C")

        def add_dual_signature_block(self, technician_name: str = "", client_name: str = ""):
            self.ln(6)
            if self.get_y() > 230:
                self.add_page()
                
            y = self.get_y() + 16
            # Left signature: Technician
            self.set_xy(16, y)
            self.set_draw_color(30, 41, 59)
            self.line(16, y, 90, y)
            self.set_xy(16, y + 2)
            self.set_font("helvetica", "B", 9)
            self.set_text_color(30, 41, 59)
            self.cell(74, 5, self._enc("Técnico Responsable"), align="C")
            self.set_xy(16, y + 7)
            self.set_font("helvetica", "", 8.5)
            self.set_text_color(71, 85, 105)
            tech_label = technician_name if technician_name else "Firma y Nombre Técnico"
            self.cell(74, 5, self._enc(tech_label), align="C")

            # Right signature: Client / Receptor
            self.set_xy(120, y)
            self.line(120, y, 194, y)
            self.set_xy(120, y + 2)
            self.set_font("helvetica", "B", 9)
            self.set_text_color(30, 41, 59)
            self.cell(74, 5, self._enc("Recepción Conforme / Cliente"), align="C")
            self.set_xy(120, y + 7)
            self.set_font("helvetica", "", 8.5)
            self.set_text_color(71, 85, 105)
            client_label = client_name if client_name else "Firma y Nombre Receptor"
            self.cell(74, 5, self._enc(client_label), align="C")

    _HVACReportPDF_Class = _InternalHVACReportPDF
    return _HVACReportPDF_Class


def HVACReportPDF(*args, **kwargs):
    """Factory proxy returning an instance of the lazily imported HVACReportPDF class."""
    cls = get_hvac_report_pdf_class()
    return cls(*args, **kwargs)

from src.core.models.work_order import WorkOrder
from src.core.models.equipment import HVACEquipment
from src.core.models.incident import Incident
from src.core.models.inventory import Tool, SparePart
from src.core.models.maintenance import MaintenanceSchedule
from src.core.models.enums import (
    WORK_ORDER_STATUS_LABELS, PRIORITY_LABELS, SERVICE_TYPE_LABELS,
    INCIDENT_SEVERITY_LABELS, INCIDENT_STATUS_LABELS,
    GuideKind, WorkOrderStatus, Priority, IncidentSeverity, IncidentStatus
)
from src.data.json_storage import JsonStorageEngine


def format_chilean_date(date_val: Any, include_time: bool = False) -> str:
    """Formats an ISO or arbitrary date string into Chilean format dd-mm-yyyy or dd-mm-yyyy HH:MM."""
    if not date_val:
        return ""
    date_str = str(date_val).strip()
    if not date_str or date_str in ["-", "N/A", "None", "null", "No definida", "Pendiente"]:
        return date_str

    # Check if already in dd-mm-yyyy or dd-mm-yyyy HH:MM
    if re.match(r"^\d{2}-\d{2}-\d{4}( \d{2}:\d{2}(:\d{2})•)•$", date_str):
        if not include_time and " " in date_str:
            return date_str.split(" ")[0]
        return date_str

    formats_to_try = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d"
    ]

    clean_str = date_str
    if len(clean_str) > 19 and ("+" in clean_str[10:] or "-" in clean_str[10:]):
        pos_plus = clean_str[10:].find("+")
        pos_minus = clean_str[10:].find("-")
        if pos_plus != -1:
            clean_str = clean_str[:10 + pos_plus]
        elif pos_minus != -1:
            clean_str = clean_str[:10 + pos_minus]
    if clean_str.endswith("Z"):
        clean_str = clean_str[:-1]

    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(clean_str, fmt)
            if include_time and (dt.hour != 0 or dt.minute != 0 or "%H" in fmt):
                return dt.strftime("%d-%m-%Y %H:%M")
            return dt.strftime("%d-%m-%Y")
        except ValueError:
            continue

    match = re.search(r"(\d{4})-(\d{2})-(\d{2})(•:[ T](\d{2}):(\d{2}))•", date_str)
    if match:
        year, month, day, hour, minute = match.groups()
        if include_time and hour and minute:
            return f"{day}-{month}-{year} {hour}:{minute}"
        return f"{day}-{month}-{year}"

    return date_str



class ExportService:
    """Service for exporting data to PDF, Excel, and CSV."""

    def __init__(self, storage: JsonStorageEngine):
        self.storage = storage

    def export_work_order_pdf(self, work_order: WorkOrder, output_path: str, logo_path: str = "", options: dict = None) -> str:
        if options is None: options = {}
        is_service = getattr(work_order, 'guide_kind', '') == GuideKind.SERVICE.value or (work_order.id and work_order.id.startswith("OTS"))
        guide_title = f"Guía de Servicio Técnico: {work_order.id}" if is_service else f"Guía de Mantenimiento Preventivo: {work_order.id}"
        guide_subtitle = "ControlHVAC CMMS - Climatización y Mantenimiento"
        
        pdf = HVACReportPDF(
            title_text=guide_title,
            subtitle_text=guide_subtitle,
            logo_path=logo_path
        )
        pdf.add_page()
        
        # Section 1: General Details
        pdf.add_section_title("Detalles de la Guía y Ubicación")
        
        is_manual = getattr(work_order, 'is_manual_equipment', False)
        if is_manual:
            eq_tag = getattr(work_order, 'manual_equipment_tag', '') or work_order.equipment_tag or "Equipo Esporádico"
            client_name = getattr(work_order, 'manual_client', '') or work_order.client_name or "Cliente General"
            site_name = getattr(work_order, 'manual_site', '') or work_order.site_name or "Instalación"
            loc_name = getattr(work_order, 'manual_location', '') or "-"
        else:
            eq_tag = work_order.equipment_tag or work_order.equipment_id or "Equipo General"
            client_name = work_order.client_name or "Cliente General"
            site_name = work_order.site_name or "Instalación Principal"
            loc_name = "-"

        service_type = getattr(work_order, 'service_type', '') or ("Servicio Técnico" if is_service else "Mantenimiento Preventivo")
        status_val = work_order.status.value if hasattr(work_order.status, 'value') else str(work_order.status)
        status_label = WORK_ORDER_STATUS_LABELS.get(work_order.status, status_val)
        priority_val = work_order.priority.value if hasattr(work_order.priority, 'value') else str(work_order.priority)
        priority_label = PRIORITY_LABELS.get(work_order.priority, priority_val)
        technician = work_order.assigned_technician or getattr(work_order, 'assigned_to', '') or "No asignado"

        meta = [
            ("Cliente / Empresa", client_name),
            ("Código Guía / OT", work_order.id),
            ("Proyecto / Sede", site_name),
            ("Equipo / Tag", eq_tag),
            ("Tipo / Modalidad", service_type),
            ("Prioridad", priority_label),
            ("Estado Actual", status_label),
            ("Técnico Asignado", technician),
            ("Fecha Programada", format_chilean_date(work_order.scheduled_date) if work_order.scheduled_date else "No definida"),
            ("Fecha Límite", format_chilean_date(work_order.due_date) if work_order.due_date else "No definida"),
            ("Inicio de Trabajo", format_chilean_date(work_order.start_date, include_time=True) if work_order.start_date else "No iniciado"),
            ("Término de Trabajo", format_chilean_date(work_order.completed_date, include_time=True) if work_order.completed_date else "Pendiente")
        ]
        if getattr(work_order, 'incident_id', ''):
            meta.append(("Avería Vinculada", work_order.incident_id))
        if loc_name and loc_name != "-":
            meta.append(("Ubicación Manual", loc_name))

        pdf.add_metadata_grid(meta)

        # Section 2: Title and Diagnosis / Description
        if options.get('print_general', True):
            pdf.add_section_title("Título y Diagnóstico Técnico")
            diag_str = getattr(work_order, 'diagnosis', '') or getattr(work_order, 'description', '') or "Sin diagnóstico especificado."
            pdf.add_text_box(f"Título: {work_order.title}\n\nDiagnóstico / Falla:\n{diag_str}")
        elif options.get('manual_checklist'):
            pdf.add_section_title("Título y Diagnóstico Técnico")
            pdf.add_text_box(f"Título: {work_order.title}\n\nDiagnóstico / Falla:\n\n\n\n")

        # Section 3: Work Performed
        if getattr(work_order, 'work_performed', '') and options.get('print_general', True):
            pdf.add_section_title("Trabajos Ejecutados y Reparaciones")
            pdf.add_text_box(work_order.work_performed)
        elif not options.get('print_general', True) and options.get('manual_checklist'):
            pdf.add_section_title("Trabajos Ejecutados y Reparaciones")
            pdf.add_text_box("\n\n\n\n")

        # Section 4: Checklist / Tareas
        if work_order.checklist:
            pdf.add_section_title("Pautas de Mantenimiento / Lista de Tareas")
            for item in work_order.checklist:
                if isinstance(item, dict):
                    desc = item.get('description', '') or item.get('task_description', '')
                    cat = item.get('category', '')
                    val = item.get('measured_value', '')
                    unit = item.get('unit', '')
                    is_comp = item.get('is_completed', False) or (item.get('status') == 'COMPLETED')
                else:
                    desc = getattr(item, 'description', '') or getattr(item, 'task_description', '')
                    cat = getattr(item, 'category', '')
                    val = getattr(item, 'measured_value', '')
                    unit = getattr(item, 'unit', '')
                    is_comp = getattr(item, 'is_completed', False) or (getattr(item, 'status', '') == 'COMPLETED')

                st_tag = "[OK - Realizado]" if is_comp else "[Pendiente]"
                extra = f" | Medición: {val} {unit}" if val else ""
                cat_tag = f"({cat}) " if cat else ""
                pdf.cell(0, 5, pdf._enc(f"• {st_tag} {cat_tag}{desc}{extra}"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

        # Section 5: Materials / Parts Used
        materials = getattr(work_order, 'materials_used', []) or getattr(work_order, 'parts_used', [])
        if materials:
            pdf.add_section_title("Materiales y Repuestos Utilizados")
            for mat in materials:
                if isinstance(mat, dict):
                    m_name = mat.get('name') or mat.get('part_name') or mat.get('description') or 'Repuesto'
                    m_code = mat.get('part_number') or mat.get('code', '')
                    m_qty = mat.get('quantity', 1)
                    m_unit = mat.get('unit', 'unid')
                else:
                    m_name = str(mat)
                    m_code = ""
                    m_qty = 1
                    m_unit = "unid"
                code_str = f" [Cód: {m_code}]" if m_code else ""
                pdf.cell(0, 5, pdf._enc(f"• {m_qty} {m_unit} - {m_name}{code_str}"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)

        # Section 6: Observations
        if getattr(work_order, 'observations', '') and options.get('print_general', True):
            pdf.add_section_title("Observaciones y Recomendaciones")
            pdf.add_text_box(work_order.observations)
        elif not options.get('print_general', True) and options.get('manual_checklist'):
            pdf.add_section_title("Observaciones y Recomendaciones")
            pdf.add_text_box("\n\n\n")

        # Section 7: History
        if options.get('history_text'):
            pdf.add_section_title("Resumen Últimas Intervenciones")
            pdf.add_text_box(options.get('history_text'))

        # Signature Block
        if options.get('add_signature', True):
            pdf.add_dual_signature_block(technician, client_name)
        else:
            pdf.ln(10)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 10, pdf._enc(f"Tcnico: {technician}"), new_x="LMARGIN", new_y="NEXT")

        pdf.output(output_path)
        return output_path

    def export_equipment_list_excel(self, equipment_list: List[HVACEquipment], output_path: str) -> str:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Equipos HVAC"
        
        headers = ["Tag", "Tipo", "Fabricante", "Modelo", "Serial", "Estado", "Instalación", "Último Servicio", "Próximo Servicio"]
        
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            
        for row, eq in enumerate(equipment_list, 2):
            sys_type = eq.system_type.value if hasattr(eq.system_type, 'value') else eq.system_type
            status = eq.status.value if hasattr(eq.status, 'value') else eq.status
            
            ws.cell(row=row, column=1, value=eq.tag)
            ws.cell(row=row, column=2, value=sys_type)
            ws.cell(row=row, column=3, value=eq.manufacturer)
            ws.cell(row=row, column=4, value=eq.model)
            ws.cell(row=row, column=5, value=eq.serial_number)
            ws.cell(row=row, column=6, value=status)
            ws.cell(row=row, column=7, value=format_chilean_date(eq.installation_date) if eq.installation_date else "")
            ws.cell(row=row, column=8, value=format_chilean_date(eq.last_service_date) if eq.last_service_date else "")
            ws.cell(row=row, column=9, value=format_chilean_date(eq.next_service_due) if eq.next_service_due else "")
            
        # Auto-width columns
        for column_cells in ws.columns:
            length = max(len(str(cell.value)) for cell in column_cells if cell.value is not None)
            ws.column_dimensions[column_cells[0].column_letter].width = length + 2
            
        wb.save(output_path)
        return output_path

    def export_equipment_list_csv(self, equipment_list: List[HVACEquipment], output_path: str) -> str:
        with open(output_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Tag", "Tipo", "Fabricante", "Modelo", "Serial", "Estado", "Instalación", "Último Servicio", "Próximo Servicio"])
            for eq in equipment_list:
                sys_type = eq.system_type.value if hasattr(eq.system_type, 'value') else eq.system_type
                status = eq.status.value if hasattr(eq.status, 'value') else eq.status
                writer.writerow([
                    eq.tag, sys_type, eq.manufacturer, eq.model, eq.serial_number, 
                    status, format_chilean_date(eq.installation_date), format_chilean_date(eq.last_service_date), format_chilean_date(eq.next_service_due)
                ])
        return output_path

    def export_work_orders_excel(self, work_orders: List[WorkOrder], output_path: str) -> str:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Órdenes de Trabajo"
        
        headers = ["ID", "Título", "Tipo", "Estado", "Prioridad", "Técnico", "Fecha Programada"]
        
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            
        for row, wo in enumerate(work_orders, 2):
            type_val = wo.type.value if hasattr(wo.type, 'value') else wo.type
            status_val = wo.status.value if hasattr(wo.status, 'value') else wo.status
            priority_val = wo.priority.value if hasattr(wo.priority, 'value') else wo.priority
            
            ws.cell(row=row, column=1, value=wo.id)
            ws.cell(row=row, column=2, value=wo.title)
            ws.cell(row=row, column=3, value=type_val)
            ws.cell(row=row, column=4, value=status_val)
            ws.cell(row=row, column=5, value=priority_val)
            ws.cell(row=row, column=6, value=wo.assigned_to or "")
            ws.cell(row=row, column=7, value=format_chilean_date(wo.scheduled_date) if wo.scheduled_date else "")
            
        for column_cells in ws.columns:
            length = max(len(str(cell.value)) for cell in column_cells if cell.value is not None)
            ws.column_dimensions[column_cells[0].column_letter].width = length + 2
            
        wb.save(output_path)
        return output_path

    def export_work_orders_csv(self, work_orders: List[WorkOrder], output_path: str) -> str:
        with open(output_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Título", "Tipo", "Estado", "Prioridad", "Técnico", "Fecha Programada"])
            for wo in work_orders:
                type_val = wo.type.value if hasattr(wo.type, 'value') else wo.type
                status_val = wo.status.value if hasattr(wo.status, 'value') else wo.status
                priority_val = wo.priority.value if hasattr(wo.priority, 'value') else wo.priority
                writer.writerow([
                    wo.id, wo.title, type_val, status_val, priority_val, 
                    wo.assigned_to or "", format_chilean_date(wo.scheduled_date) if wo.scheduled_date else ""
                ])
        return output_path

    def export_inventory_excel(self, tools: List[Tool], spare_parts: List[SparePart], output_path: str) -> str:
        wb = openpyxl.Workbook()
        
        # Tools Sheet
        ws_tools = wb.active
        ws_tools.title = "Herramientas"
        
        t_headers = ["ID", "Nombre", "Marca", "Modelo", "Estado", "Asignado a"]
        for col, header in enumerate(t_headers, 1):
            cell = ws_tools.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            
        for row, tool in enumerate(tools, 2):
            status = tool.status.value if hasattr(tool.status, 'value') else tool.status
            ws_tools.cell(row=row, column=1, value=tool.id)
            ws_tools.cell(row=row, column=2, value=tool.name)
            ws_tools.cell(row=row, column=3, value=tool.brand)
            ws_tools.cell(row=row, column=4, value=tool.model)
            ws_tools.cell(row=row, column=5, value=status)
            ws_tools.cell(row=row, column=6, value=tool.assigned_to or "")
            
        for column_cells in ws_tools.columns:
            length = max(len(str(cell.value)) for cell in column_cells if cell.value is not None)
            ws_tools.column_dimensions[column_cells[0].column_letter].width = length + 2
            
        # Parts Sheet
        ws_parts = wb.create_sheet(title="Repuestos")
        p_headers = ["ID", "Nombre", "Número de Parte", "Cantidad", "Mínimo", "Costo"]
        for col, header in enumerate(p_headers, 1):
            cell = ws_parts.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            
        for row, part in enumerate(spare_parts, 2):
            ws_parts.cell(row=row, column=1, value=part.id)
            ws_parts.cell(row=row, column=2, value=part.name)
            ws_parts.cell(row=row, column=3, value=part.part_number)
            ws_parts.cell(row=row, column=4, value=part.quantity)
            ws_parts.cell(row=row, column=5, value=part.minimum_quantity)
            ws_parts.cell(row=row, column=6, value=part.unit_cost)
            
        for column_cells in ws_parts.columns:
            length = max(len(str(cell.value)) for cell in column_cells if cell.value is not None)
            ws_parts.column_dimensions[column_cells[0].column_letter].width = length + 2
            
        wb.save(output_path)
        return output_path

    def export_maintenance_schedule_pdf(self, schedules: List[MaintenanceSchedule], output_path: str) -> str:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "Cronograma de Mantenimiento", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        
        pdf.set_font("helvetica", "", 11)
        for sched in schedules:
            pdf.set_font("helvetica", "B", 12)
            pdf.cell(0, 8, f"Equipo: {sched.equipment_id}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 11)
            
            active_str = "Sí" if sched.is_active else "No"
            pdf.cell(0, 6, f"Activo: {active_str}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Frecuencia (días): {sched.frequency_days}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Próxima Fecha: {format_chilean_date(sched.next_date) if sched.next_date else 'No definida'}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 6, f"Descripción: {sched.description or 'N/A'}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
        pdf.output(output_path)
        return output_path

    def export_incident_pdf(self, incident, output_path: str, logo_path: str = "", client_name: str = "", site_name: str = "", equipment_service=None) -> str:
        pdf = HVACReportPDF(
            title_text=f"Informe de Avería: {incident.id}",
            subtitle_text="Inspección Técnica de Climatización",
            logo_path=logo_path
        )
        pdf.add_page()

        # Section 1: Details and Client
        pdf.add_section_title("Detalles del Informe y Cliente")
        
        client_val = client_name or "Cliente General"
        site_val = site_name or "Planta Principal"
        
        eq_notes = ""
        eq_model = ""
        eq_bms = getattr(incident, 'bms_id', '') or ""
        eq_bms_status = ""
        if equipment_service and incident.equipment_id:
            eq = equipment_service.get_equipment(incident.equipment_id)
            if eq:
                eq_notes = (getattr(eq, 'notes', '') or '').strip()
                eq_model = f"{eq.manufacturer or ''} {eq.model_number or ''}".strip()
                eq_bms_status = getattr(eq, 'bms_status', '') or ""
                if not eq_bms:
                    eq_bms = getattr(eq, 'bms_id', '') or ""

        meta = [
            ("Cliente / Empresa", client_val),
            ("Código Avería", incident.id),
            ("Proyecto / Planta", site_val),
            ("Equipo / Tag", incident.equipment_tag or incident.equipment_id),
            ("ID BMS", eq_bms or "N/A"),
            ("Estado BMS/Ctrl", eq_bms_status or "Operativo"),
            ("Modelo / Serie", eq_model or "N/A"),
            ("Tipo / Incidencia", incident.type_display),
            ("Severidad", incident.severity_display),
            ("Estado Actual", incident.status_display),
            ("Fecha Reporte", format_chilean_date(incident.reported_date)),
            ("Técnico Asignado", incident.technician or "No asignado"),
            ("Fecha Resolución", format_chilean_date(incident.resolved_date) if incident.resolved_date else "Pendiente")
        ]
        pdf.add_metadata_grid(meta)

        # Section 2: Equipment Notes if available
        if eq_notes:
            pdf.add_section_title("Notas de la Ficha del Equipo")
            pdf.add_text_box(eq_notes)

        # Section 3: Title and Falla Description
        pdf.add_section_title("Descripción de la Avería / Falla")
        pdf.add_text_box(f"Título: {incident.title}\n\n{incident.description}")

        # Section 4: Diagnosis
        pdf.add_section_title("Diagnóstico Técnico")
        pdf.add_text_box(incident.diagnosis or "Diagnóstico no especificado.")

        # Section 5: Actions & Repairs
        pdf.add_section_title("Acciones y Reparaciones Realizadas")
        pdf.add_text_box(incident.action_taken or "No se han registrado acciones aún.")

        # Section 6: Parts and Labor
        if incident.parts_used or incident.labor_hours > 0 or incident.cost_estimate > 0:
            pdf.add_section_title("Recursos, Repuestos y Costos")
            parts_str = ", ".join(incident.parts_used) if incident.parts_used else "Ninguno"
            parts_meta = [
                ("Repuestos Utilizados", parts_str),
                ("Horas Hombre", f"{incident.labor_hours} hrs"),
                ("Costo Estimado", f"${incident.cost_estimate:,.2f}")
            ]
            pdf.add_metadata_grid(parts_meta)

        # Section 7: Notes
        if incident.notes:
            pdf.add_section_title("Observaciones Generales de la Incidencia")
            pdf.add_text_box(incident.notes)

        # Signature Block
        pdf.add_signature_block(incident.technician)

        pdf.output(output_path)
        return output_path

    def export_faulty_equipment_pdf(self, equipment_list: List[HVACEquipment], incident_service, output_path: str, logo_path: str = "", client_service=None) -> str:
        pdf = HVACReportPDF(
            title_text="Listado de Equipos en Avería",
            subtitle_text="Resumen e Inspección de Equipos Fuera de Servicio / En Falla",
            logo_path=logo_path
        )
        pdf.add_page()
        pdf.ln(2)

        # Section 1: Summary Overview
        pdf.add_section_title("Resumen e Índice de Equipos en Avería")
        
        total_eq = len(equipment_list)
        now_str = datetime.now().strftime("%d-%m-%Y %H:%M")
        
        summary_meta = [
            ("Total Equipos Registrados", str(total_eq)),
            ("Fecha de Emisión", now_str),
            ("Estado Informe", "Equipos en Falla / Observación")
        ]
        pdf.add_metadata_grid(summary_meta)

        # Section 2: Table of Faulty Equipment
        pdf.add_section_title("Detalle del Listado de Equipos")

        # Table Header
        pdf.set_fill_color(29, 34, 55) # Navy #1D2237
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 7.5)
        
        # Total widths = 186mm
        # # (6), Tag (22), ID BMS (18), Estado BMS (22), Fabricante (22), Ubicación (24), Estado (20), Notas / Diagnóstico (52)
        pdf.cell(6, 7, pdf._enc("#"), border=1, fill=True, align="C")
        pdf.cell(22, 7, pdf._enc("Tag / Equipo"), border=1, fill=True, align="L")
        pdf.cell(18, 7, pdf._enc("ID BMS"), border=1, fill=True, align="L")
        pdf.cell(22, 7, pdf._enc("Estado BMS"), border=1, fill=True, align="L")
        pdf.cell(22, 7, pdf._enc("Fabricante/Mod."), border=1, fill=True, align="L")
        pdf.cell(24, 7, pdf._enc("Ubicación / Área"), border=1, fill=True, align="L")
        pdf.cell(20, 7, pdf._enc("Estado"), border=1, fill=True, align="C")
        pdf.cell(52, 7, pdf._enc("Notas / Diagnóstico"), border=1, fill=True, align="L")
        pdf.ln(7)

        # Rows
        pdf.set_font("helvetica", "", 7.5)
        pdf.set_text_color(30, 41, 59)
        
        for idx, eq in enumerate(equipment_list, 1):
            if pdf.get_y() > 255:
                pdf.add_page()
                pdf.ln(2)
                # Repeat header on new page
                pdf.set_fill_color(29, 34, 55)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("helvetica", "B", 7.5)
                pdf.cell(6, 7, pdf._enc("#"), border=1, fill=True, align="C")
                pdf.cell(22, 7, pdf._enc("Tag / Equipo"), border=1, fill=True, align="L")
                pdf.cell(18, 7, pdf._enc("ID BMS"), border=1, fill=True, align="L")
                pdf.cell(22, 7, pdf._enc("Estado BMS"), border=1, fill=True, align="L")
                pdf.cell(22, 7, pdf._enc("Fabricante/Mod."), border=1, fill=True, align="L")
                pdf.cell(24, 7, pdf._enc("Ubicación / Área"), border=1, fill=True, align="L")
                pdf.cell(20, 7, pdf._enc("Estado"), border=1, fill=True, align="C")
                pdf.cell(52, 7, pdf._enc("Notas / Diagnóstico"), border=1, fill=True, align="L")
                pdf.ln(7)
                pdf.set_font("helvetica", "", 7.5)
                pdf.set_text_color(30, 41, 59)

            # Row fill background alternating
            if idx % 2 == 0:
                pdf.set_fill_color(248, 250, 252)
            else:
                pdf.set_fill_color(255, 255, 255)

            # Extract equipment notes and incident diagnosis
            eq_notes_str = (getattr(eq, 'notes', '') or '').strip()
            diag_text = ""
            if eq_notes_str:
                diag_text = eq_notes_str

            if incident_service:
                incs = incident_service.get_incidents_for_equipment(eq.id)
                open_incs = [i for i in incs if (i.status.value if hasattr(i.status, 'value') else str(i.status)) != "RESUELTA"]
                if open_incs:
                    latest = open_incs[0]
                    inc_info = latest.diagnosis or latest.notes or latest.title
                    if inc_info and inc_info not in diag_text:
                        diag_text = f"{diag_text} | {inc_info}" if diag_text else inc_info

            if not diag_text:
                diag_text = "Sin notas ni diagnóstico registrado."

            status_map = {
                "FAULT": "En Falla",
                "WARNING": "En Obs.",
                "OUT_OF_SERVICE": "Fuera Serv.",
                "DECOMMISSIONED": "Fuera Serv.",
                "OPERATIONAL": "Operativo"
            }
            eq_status = eq.status.value if hasattr(eq.status, 'value') else str(eq.status)
            status_str = status_map.get(eq_status, "Fuera Serv." if "DECOMMISSION" in eq_status.upper() else eq_status)

            bms_id_str = getattr(eq, 'bms_id', '') or "N/A"
            bms_st_str = getattr(eq, 'bms_status', '') or "Operativo"
            make_model = f"{eq.manufacturer} {eq.model_number}".strip() or "N/A"
            loc_str = eq.location_description or eq.floor_area or "N/A"

            # Render row cells
            pdf.cell(6, 6, pdf._enc(str(idx)), border=1, fill=True, align="C")
            pdf.cell(22, 6, pdf._enc(eq.tag[:13]), border=1, fill=True, align="L")
            pdf.cell(18, 6, pdf._enc(bms_id_str[:10]), border=1, fill=True, align="L")
            pdf.cell(22, 6, pdf._enc(bms_st_str[:12]), border=1, fill=True, align="L")
            pdf.cell(22, 6, pdf._enc(make_model[:12]), border=1, fill=True, align="L")
            pdf.cell(24, 6, pdf._enc(loc_str[:13]), border=1, fill=True, align="L")
            pdf.cell(20, 6, pdf._enc(status_str[:10]), border=1, fill=True, align="C")
            pdf.cell(52, 6, pdf._enc(diag_text[:34]), border=1, fill=True, align="L")
            pdf.ln(6)

        # Signature Block
        pdf.add_signature_block()

        pdf.output(output_path)
        return output_path

    def export_bms_issues_pdf(self, equipment_list: List[HVACEquipment], incident_service, output_path: str, logo_path: str = "", client_service=None) -> str:
        """Exports a dedicated PDF report of all equipment having BMS / Control system issues."""
        pdf = HVACReportPDF(
            title_text="Listado de Equipos con Problemas de Control / BMS",
            subtitle_text="Auditoría e Inspección del Sistema de Control y Automatización",
            logo_path=logo_path
        )
        pdf.add_page()
        pdf.ln(2)

        # Section 1: Summary Overview
        pdf.add_section_title("Resumen del Estado de Control / BMS")
        
        total_eq = len(equipment_list)
        now_str = datetime.now().strftime("%d-%m-%Y %H:%M")
        
        summary_meta = [
            ("Total Equipos con Obs. BMS", str(total_eq)),
            ("Fecha de Emisión", now_str),
            ("Especialidad / Área", "Control Automático y BMS"),
            ("Criterio", "Equipos no operativos a nivel de control")
        ]
        pdf.add_metadata_grid(summary_meta)

        # Section 2: Table of BMS Issues Equipment
        pdf.add_section_title("Detalle de Equipos con Problemas de Control")

        # Table Header
        pdf.set_fill_color(29, 34, 55) # Navy #1D2237
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 7.5)
        
        # Total widths = 186mm
        # # (6), Tag (22), ID BMS (20), Estado Control/BMS (26), Estado Op. (20), Ubicación (26), Notas / Diagnóstico (66)
        pdf.cell(6, 7, pdf._enc("#"), border=1, fill=True, align="C")
        pdf.cell(22, 7, pdf._enc("Tag / Equipo"), border=1, fill=True, align="L")
        pdf.cell(20, 7, pdf._enc("ID BMS"), border=1, fill=True, align="L")
        pdf.cell(26, 7, pdf._enc("Estado Control/BMS"), border=1, fill=True, align="L")
        pdf.cell(20, 7, pdf._enc("Estado Op."), border=1, fill=True, align="C")
        pdf.cell(26, 7, pdf._enc("Ubicación / Área"), border=1, fill=True, align="L")
        pdf.cell(66, 7, pdf._enc("Notas / Detalle del Problema"), border=1, fill=True, align="L")
        pdf.ln(7)

        # Rows
        pdf.set_font("helvetica", "", 7.5)
        pdf.set_text_color(30, 41, 59)
        
        for idx, eq in enumerate(equipment_list, 1):
            if pdf.get_y() > 255:
                pdf.add_page()
                pdf.ln(2)
                # Repeat header on new page
                pdf.set_fill_color(29, 34, 55)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("helvetica", "B", 7.5)
                pdf.cell(6, 7, pdf._enc("#"), border=1, fill=True, align="C")
                pdf.cell(22, 7, pdf._enc("Tag / Equipo"), border=1, fill=True, align="L")
                pdf.cell(20, 7, pdf._enc("ID BMS"), border=1, fill=True, align="L")
                pdf.cell(26, 7, pdf._enc("Estado Control/BMS"), border=1, fill=True, align="L")
                pdf.cell(20, 7, pdf._enc("Estado Op."), border=1, fill=True, align="C")
                pdf.cell(26, 7, pdf._enc("Ubicación / Área"), border=1, fill=True, align="L")
                pdf.cell(66, 7, pdf._enc("Notas / Detalle del Problema"), border=1, fill=True, align="L")
                pdf.ln(7)
                pdf.set_font("helvetica", "", 7.5)
                pdf.set_text_color(30, 41, 59)

            # Row fill background alternating
            if idx % 2 == 0:
                pdf.set_fill_color(248, 250, 252)
            else:
                pdf.set_fill_color(255, 255, 255)

            # Extract equipment notes and incident diagnosis
            eq_notes_str = (getattr(eq, 'notes', '') or '').strip()
            diag_text = ""
            if eq_notes_str:
                diag_text = eq_notes_str

            if incident_service:
                incs = incident_service.get_incidents_for_equipment(eq.id)
                open_incs = [i for i in incs if (i.status.value if hasattr(i.status, 'value') else str(i.status)) != "RESUELTA"]
                if open_incs:
                    latest = open_incs[0]
                    inc_info = latest.diagnosis or latest.notes or latest.title
                    if inc_info and inc_info not in diag_text:
                        diag_text = f"{diag_text} | {inc_info}" if diag_text else inc_info

            if not diag_text:
                diag_text = "Sin observaciones registradas."

            status_map = {
                "FAULT": "En Falla",
                "WARNING": "En Obs.",
                "OUT_OF_SERVICE": "Fuera Serv.",
                "DECOMMISSIONED": "Fuera Serv.",
                "OPERATIONAL": "Operativo"
            }
            eq_status = eq.status.value if hasattr(eq.status, 'value') else str(eq.status)
            status_str = status_map.get(eq_status, eq_status)

            bms_id_str = getattr(eq, 'bms_id', '') or "N/A"
            bms_st_str = getattr(eq, 'bms_status', '') or "No Operativo"
            loc_str = eq.location_description or eq.floor_area or "N/A"

            # Render row cells
            pdf.cell(6, 6, pdf._enc(str(idx)), border=1, fill=True, align="C")
            pdf.cell(22, 6, pdf._enc(eq.tag[:13]), border=1, fill=True, align="L")
            pdf.cell(20, 6, pdf._enc(bms_id_str[:12]), border=1, fill=True, align="L")
            pdf.cell(26, 6, pdf._enc(bms_st_str[:15]), border=1, fill=True, align="L")
            pdf.cell(20, 6, pdf._enc(status_str[:10]), border=1, fill=True, align="C")
            pdf.cell(26, 6, pdf._enc(loc_str[:15]), border=1, fill=True, align="L")
            pdf.cell(66, 6, pdf._enc(diag_text[:44]), border=1, fill=True, align="L")
            pdf.ln(6)

        # Signature Block
        pdf.add_signature_block()

        pdf.output(output_path)
        return output_path

    def export_equipment_inventory_pdf(
        self, 
        equipment_list: List[HVACEquipment], 
        title_text: str = "Listado Oficial de Equipos HVAC", 
        subtitle_text: str = "ControlHVAC CMMS - Gestión e Inventario de Activos",
        scope_info: str = "Todos los Equipos",
        client_name: str = "",
        site_name: str = "",
        logo_path: str = "", 
        incident_service = None,
        output_path: str = ""
    ) -> str:
        """Exports a customized PDF inventory report of equipment matching selected criteria."""
        pdf = HVACReportPDF(
            title_text=title_text,
            subtitle_text=subtitle_text,
            logo_path=logo_path
        )
        pdf.add_page()
        pdf.ln(2)

        # Section 1: Summary Overview
        pdf.add_section_title("Resumen del Reporte de Equipos")
        
        total_eq = len(equipment_list)
        now_str = datetime.now().strftime("%d-%m-%Y %H:%M")
        
        summary_meta = [
            ("Total Equipos en Listado", str(total_eq)),
            ("Fecha de Emisión", now_str),
            ("Criterio / Filtro Aplicado", scope_info or "General")
        ]
        if client_name:
            summary_meta.append(("Cliente", client_name))
        if site_name:
            summary_meta.append(("Instalación", site_name))

        pdf.add_metadata_grid(summary_meta)

        # Section 2: Equipment Detail Table
        pdf.add_section_title("Detalle del Listado de Equipos")

        # Table Header
        pdf.set_fill_color(29, 34, 55) # Navy #1D2237
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 7.5)
        
        # Total widths = 186mm: # (6), Tag (22), ID BMS (18), Tipo (22), Fabricante/Mod (24), Piso/Ubicación (24), BMS Status (20), Estado Op (18), Observaciones (32)
        pdf.cell(6, 7, pdf._enc("#"), border=1, fill=True, align="C")
        pdf.cell(22, 7, pdf._enc("Tag / Equipo"), border=1, fill=True, align="L")
        pdf.cell(18, 7, pdf._enc("ID BMS"), border=1, fill=True, align="L")
        pdf.cell(22, 7, pdf._enc("Tipo / Sistema"), border=1, fill=True, align="L")
        pdf.cell(24, 7, pdf._enc("Marca / Modelo"), border=1, fill=True, align="L")
        pdf.cell(24, 7, pdf._enc("Piso / Ubicación"), border=1, fill=True, align="L")
        pdf.cell(20, 7, pdf._enc("Estado BMS"), border=1, fill=True, align="L")
        pdf.cell(18, 7, pdf._enc("Estado Op."), border=1, fill=True, align="C")
        pdf.cell(32, 7, pdf._enc("Notas / Obs."), border=1, fill=True, align="L")
        pdf.ln(7)

        # Rows
        pdf.set_font("helvetica", "", 7.5)
        pdf.set_text_color(30, 41, 59)
        
        for idx, eq in enumerate(equipment_list, 1):
            if pdf.get_y() > 255:
                pdf.add_page()
                pdf.ln(2)
                # Repeat header on new page
                pdf.set_fill_color(29, 34, 55)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("helvetica", "B", 7.5)
                pdf.cell(6, 7, pdf._enc("#"), border=1, fill=True, align="C")
                pdf.cell(22, 7, pdf._enc("Tag / Equipo"), border=1, fill=True, align="L")
                pdf.cell(18, 7, pdf._enc("ID BMS"), border=1, fill=True, align="L")
                pdf.cell(22, 7, pdf._enc("Tipo / Sistema"), border=1, fill=True, align="L")
                pdf.cell(24, 7, pdf._enc("Marca / Modelo"), border=1, fill=True, align="L")
                pdf.cell(24, 7, pdf._enc("Piso / Ubicación"), border=1, fill=True, align="L")
                pdf.cell(20, 7, pdf._enc("Estado BMS"), border=1, fill=True, align="L")
                pdf.cell(18, 7, pdf._enc("Estado Op."), border=1, fill=True, align="C")
                pdf.cell(32, 7, pdf._enc("Notas / Obs."), border=1, fill=True, align="L")
                pdf.ln(7)
                pdf.set_font("helvetica", "", 7.5)
                pdf.set_text_color(30, 41, 59)

            # Row fill background alternating
            if idx % 2 == 0:
                pdf.set_fill_color(248, 250, 252)
            else:
                pdf.set_fill_color(255, 255, 255)

            # Extract fields
            bms_id_str = getattr(eq, 'bms_id', '') or "N/A"
            bms_st_str = getattr(eq, 'bms_status', '') or "Operativo"
            sys_type = eq.system_type.value if hasattr(eq.system_type, 'value') else str(eq.system_type)
            make_model = f"{eq.manufacturer or ''} {eq.model_number or ''}".strip() or "N/A"
            loc_str = eq.location_description or eq.floor_area or "N/A"

            status_map = {
                "FAULT": "En Falla",
                "WARNING": "En Obs.",
                "IN_MAINTENANCE": "En Mant.",
                "OUT_OF_SERVICE": "Fuera Serv.",
                "DECOMMISSIONED": "Fuera Serv.",
                "OPERATIONAL": "Operativo"
            }
            eq_status = eq.status.value if hasattr(eq.status, 'value') else str(eq.status)
            status_str = status_map.get(eq_status, eq_status)

            notes_str = (getattr(eq, 'notes', '') or '').strip()
            if not notes_str and incident_service:
                incs = incident_service.get_incidents_for_equipment(eq.id)
                open_incs = [i for i in incs if (i.status.value if hasattr(i.status, 'value') else str(i.status)) != "RESUELTA"]
                if open_incs:
                    notes_str = open_incs[0].title

            if not notes_str:
                notes_str = "-"

            # Render row cells
            pdf.cell(6, 6, pdf._enc(str(idx)), border=1, fill=True, align="C")
            pdf.cell(22, 6, pdf._enc(eq.tag[:13]), border=1, fill=True, align="L")
            pdf.cell(18, 6, pdf._enc(bms_id_str[:10]), border=1, fill=True, align="L")
            pdf.cell(22, 6, pdf._enc(sys_type[:13]), border=1, fill=True, align="L")
            pdf.cell(24, 6, pdf._enc(make_model[:14]), border=1, fill=True, align="L")
            pdf.cell(24, 6, pdf._enc(loc_str[:14]), border=1, fill=True, align="L")
            pdf.cell(20, 6, pdf._enc(bms_st_str[:11]), border=1, fill=True, align="L")
            pdf.cell(18, 6, pdf._enc(status_str[:9]), border=1, fill=True, align="C")
            pdf.cell(32, 6, pdf._enc(notes_str[:20]), border=1, fill=True, align="L")
            pdf.ln(6)

        # Signature Block
        pdf.add_signature_block()

        pdf.output(output_path)
        return output_path

    def _render_floor_plan_in_pdf(
        self,
        pdf: HVACReportPDF,
        floor_name: str,
        library_service,
        site_id: str = ""
    ):
        """Finds and renders floor plan / plant layout image for the given floor in PDF."""
        if not library_service:
            return

        img_path = library_service.get_floor_plan_image_path(floor_name, site_id=site_id)
        if not img_path or not os.path.exists(img_path):
            return

        try:
            from PIL import Image
            with Image.open(img_path) as img:
                orig_w, orig_h = img.size

            # If less than 110mm left before page footer, add a new page
            current_y = pdf.get_y()
            if current_y > 165:
                pdf.add_page()
                pdf.ln(2)

            pdf.add_section_title(f"Plano de Distribución y Ubicación de Equipos - {floor_name}")

            content_width = 186.0  # between 12mm left and right margins
            max_img_height = 110.0  # mm

            img_ratio = orig_w / float(orig_h) if orig_h > 0 else 1.0
            calc_w = content_width
            calc_h = calc_w / img_ratio
            if calc_h > max_img_height:
                calc_h = max_img_height
                calc_w = calc_h * img_ratio

            x_pos = 12.0 + (content_width - calc_w) / 2.0
            y_pos = pdf.get_y()

            # Background frame
            pdf.set_fill_color(248, 250, 252)
            pdf.set_draw_color(203, 213, 225)
            pdf.rect(x_pos - 1, y_pos - 1, calc_w + 2, calc_h + 2, style="FD")

            pdf.image(img_path, x=x_pos, y=y_pos, w=calc_w, h=calc_h)
            pdf.set_y(y_pos + calc_h + 5)

        except Exception as e:
            print(f"Error rendering floor plan image in PDF: {e}")

    def export_equipment_by_floor_pdf(
        self,
        equipment_list: List[HVACEquipment],
        title_text: str = "Listado de Equipos por Piso / Área",
        subtitle_text: str = "ControlHVAC CMMS - Gestión e Inventario de Activos",
        client_name: str = "",
        site_name: str = "",
        logo_path: str = "",
        incident_service = None,
        library_service = None,
        include_floor_plans: bool = True,
        output_path: str = ""
    ) -> str:
        """Exports a PDF report where each floor/area is presented on its own dedicated page(s)."""
        # Group equipment by floor_area
        floors_dict: dict[str, List[HVACEquipment]] = {}
        for eq in equipment_list:
            fl = (getattr(eq, 'floor_area', '') or '').strip()
            if not fl:
                fl = (eq.location_description or '').strip()
            if not fl:
                fl = "Sin Piso / Área Asignada"
            if fl not in floors_dict:
                floors_dict[fl] = []
            floors_dict[fl].append(eq)

        # Smart sort floors (Subterráneos first, then numbered floors, then roof/other)
        def floor_sort_key(name: str):
            n_lower = name.lower()
            if "subt" in n_lower or "-1" in n_lower or "-2" in n_lower or "-3" in n_lower:
                return (0, n_lower)
            digits = re.findall(r'\d+', name)
            if digits:
                return (1, int(digits[0]), n_lower)
            if "azot" in n_lower or "tech" in n_lower or "cubier" in n_lower:
                return (3, n_lower)
            if "sin" in n_lower:
                return (4, n_lower)
            return (2, n_lower)

        sorted_floor_names = sorted(floors_dict.keys(), key=floor_sort_key)

        pdf = HVACReportPDF(
            title_text=title_text,
            subtitle_text=subtitle_text,
            logo_path=logo_path
        )

        status_map = {
            "FAULT": "En Falla",
            "WARNING": "En Obs.",
            "IN_MAINTENANCE": "En Mant.",
            "OUT_OF_SERVICE": "Fuera Serv.",
            "DECOMMISSIONED": "Fuera Serv.",
            "OPERATIONAL": "Operativo"
        }

        def draw_table_header():
            pdf.set_fill_color(29, 34, 55)  # Navy #1D2237
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("helvetica", "B", 7.5)
            pdf.cell(6, 7, pdf._enc("#"), border=1, fill=True, align="C")
            pdf.cell(24, 7, pdf._enc("Tag / Equipo"), border=1, fill=True, align="L")
            pdf.cell(18, 7, pdf._enc("ID BMS"), border=1, fill=True, align="L")
            pdf.cell(22, 7, pdf._enc("Tipo / Sistema"), border=1, fill=True, align="L")
            pdf.cell(24, 7, pdf._enc("Marca / Modelo"), border=1, fill=True, align="L")
            pdf.cell(24, 7, pdf._enc("Ubicación"), border=1, fill=True, align="L")
            pdf.cell(20, 7, pdf._enc("Estado BMS"), border=1, fill=True, align="L")
            pdf.cell(18, 7, pdf._enc("Estado Op."), border=1, fill=True, align="C")
            pdf.cell(30, 7, pdf._enc("Notas / Obs."), border=1, fill=True, align="L")
            pdf.ln(7)

        total_floors = len(sorted_floor_names)
        now_str = datetime.now().strftime("%d-%m-%Y %H:%M")

        for f_idx, floor_name in enumerate(sorted_floor_names, 1):
            floor_eqs = floors_dict[floor_name]
            pdf.add_page()
            pdf.ln(2)

            # Floor Header Banner
            pdf.add_section_title(f"Piso / Área: {floor_name}")

            summary_meta = [
                ("Piso / Sector", f"{floor_name} ({f_idx} de {total_floors})"),
                ("Equipos en este Piso", f"{len(floor_eqs)} equipos"),
                ("Fecha de Emisión", now_str)
            ]
            if client_name:
                summary_meta.append(("Cliente", client_name))
            if site_name:
                summary_meta.append(("Instalación", site_name))

            pdf.add_metadata_grid(summary_meta)

            # Table Title & Header
            pdf.add_section_title(f"Inventario de Equipos - {floor_name}")
            draw_table_header()

            # Rows
            pdf.set_font("helvetica", "", 7.5)
            pdf.set_text_color(30, 41, 59)

            for idx, eq in enumerate(floor_eqs, 1):
                if pdf.get_y() > 255:
                    pdf.add_page()
                    pdf.ln(2)
                    pdf.add_section_title(f"Inventario de Equipos - {floor_name} (Continuación)")
                    draw_table_header()
                    pdf.set_font("helvetica", "", 7.5)
                    pdf.set_text_color(30, 41, 59)

                # Alternating row background
                if idx % 2 == 0:
                    pdf.set_fill_color(248, 250, 252)
                else:
                    pdf.set_fill_color(255, 255, 255)

                bms_id_str = getattr(eq, 'bms_id', '') or "N/A"
                bms_st_str = getattr(eq, 'bms_status', '') or "Operativo"
                sys_type = eq.system_type.value if hasattr(eq.system_type, 'value') else str(eq.system_type)
                make_model = f"{eq.manufacturer or ''} {eq.model_number or ''}".strip() or "N/A"
                loc_str = eq.location_description or eq.floor_area or "-"

                eq_status = eq.status.value if hasattr(eq.status, 'value') else str(eq.status)
                status_str = status_map.get(eq_status, eq_status)

                notes_str = (getattr(eq, 'notes', '') or '').strip()
                if not notes_str and incident_service:
                    incs = incident_service.get_incidents_for_equipment(eq.id)
                    open_incs = [i for i in incs if (i.status.value if hasattr(i.status, 'value') else str(i.status)) != "RESUELTA"]
                    if open_incs:
                        notes_str = open_incs[0].title

                if not notes_str:
                    notes_str = "-"

                pdf.cell(6, 6, pdf._enc(str(idx)), border=1, fill=True, align="C")
                pdf.cell(24, 6, pdf._enc(eq.tag[:14]), border=1, fill=True, align="L")
                pdf.cell(18, 6, pdf._enc(bms_id_str[:10]), border=1, fill=True, align="L")
                pdf.cell(22, 6, pdf._enc(sys_type[:13]), border=1, fill=True, align="L")
                pdf.cell(24, 6, pdf._enc(make_model[:14]), border=1, fill=True, align="L")
                pdf.cell(24, 6, pdf._enc(loc_str[:14]), border=1, fill=True, align="L")
                pdf.cell(20, 6, pdf._enc(bms_st_str[:11]), border=1, fill=True, align="L")
                pdf.cell(18, 6, pdf._enc(status_str[:9]), border=1, fill=True, align="C")
                pdf.cell(30, 6, pdf._enc(notes_str[:18]), border=1, fill=True, align="L")
                pdf.ln(6)

            # Render floor plan layout image if available
            if include_floor_plans and library_service:
                self._render_floor_plan_in_pdf(pdf, floor_name, library_service)

        # Add signature / validation block only on the last page of the report
        pdf.add_signature_block()

        pdf.output(output_path)
        return output_path

    def export_incidents_list_pdf(
        self,
        incident_list: List[Incident],
        title_text: str = "Listado Oficial de Averías e Incidencias",
        subtitle_text: str = "ControlHVAC CMMS - Gestión y Control de Averías",
        scope_info: str = "Todas las Averías",
        client_name: str = "",
        site_name: str = "",
        logo_path: str = "",
        equipment_service = None,
        output_path: str = ""
    ) -> str:
        """Exports a consolidated list of incidents to PDF with Chilean dates and status."""
        pdf = HVACReportPDF(
            title_text=title_text,
            subtitle_text=subtitle_text,
            logo_path=logo_path
        )
        pdf.add_page()
        pdf.ln(2)

        # Summary
        pdf.add_section_title("Resumen del Reporte de Averías")
        total_inc = len(incident_list)
        now_str = datetime.now().strftime("%d-%m-%Y %H:%M")

        summary_meta = [
            ("Total Averías en Listado", f"{total_inc} averías"),
            ("Fecha de Emisión", now_str),
            ("Criterio / Filtro", scope_info or "General")
        ]
        if client_name:
            summary_meta.append(("Cliente", client_name))
        if site_name:
            summary_meta.append(("Instalación", site_name))

        pdf.add_metadata_grid(summary_meta)

        # Table
        pdf.add_section_title("Detalle del Listado de Averías e Incidencias")

        eq_map = {}
        if equipment_service:
            try:
                all_eqs = equipment_service.get_all_equipment()
                for eq in all_eqs:
                    eq_map[eq.id] = eq
            except Exception:
                pass

        severity_map = {
            "CRITICA": "Crítica",
            "ALTA": "Alta",
            "MEDIA": "Media",
            "BAJA": "Baja",
            "CRITICAL": "Crítica",
            "HIGH": "Alta",
            "MEDIUM": "Media",
            "LOW": "Baja"
        }
        status_map = {
            "REPORTADA": "Reportada",
            "EN_PROCESO": "En Reparación",
            "EN_REPARACION": "En Reparación",
            "RESUELTA": "Resuelta",
            "CANCELADA": "Cancelada"
        }

        def draw_table_header():
            pdf.set_fill_color(29, 34, 55)  # Navy #1D2237
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("helvetica", "B", 7.5)
            # Total = 186mm: 6 + 16 + 20 + 18 + 34 + 44 + 16 + 18 + 14
            pdf.cell(6, 7, pdf._enc("#"), border=1, fill=True, align="C")
            pdf.cell(16, 7, pdf._enc("Código"), border=1, fill=True, align="L")
            pdf.cell(20, 7, pdf._enc("Tag Equipo"), border=1, fill=True, align="L")
            pdf.cell(18, 7, pdf._enc("ID BMS"), border=1, fill=True, align="L")
            pdf.cell(34, 7, pdf._enc("Título / Falla"), border=1, fill=True, align="L")
            pdf.cell(44, 7, pdf._enc("Notas / Detalle"), border=1, fill=True, align="L")
            pdf.cell(16, 7, pdf._enc("Severidad"), border=1, fill=True, align="C")
            pdf.cell(18, 7, pdf._enc("Estado"), border=1, fill=True, align="C")
            pdf.cell(14, 7, pdf._enc("Fecha Rep."), border=1, fill=True, align="C")
            pdf.ln(7)

        draw_table_header()

        pdf.set_font("helvetica", "", 7.5)
        pdf.set_text_color(30, 41, 59)

        for idx, inc in enumerate(incident_list, 1):
            if pdf.get_y() > 255:
                pdf.add_page()
                pdf.ln(2)
                pdf.add_section_title("Detalle del Listado de Averías (Continuación)")
                draw_table_header()
                pdf.set_font("helvetica", "", 7.5)
                pdf.set_text_color(30, 41, 59)

            if idx % 2 == 0:
                pdf.set_fill_color(248, 250, 252)
            else:
                pdf.set_fill_color(255, 255, 255)

            sev_val = inc.severity.value if hasattr(inc.severity, 'value') else str(inc.severity)
            sev_str = severity_map.get(sev_val.upper(), sev_val)

            st_val = inc.status.value if hasattr(inc.status, 'value') else str(inc.status)
            st_str = status_map.get(st_val.upper(), st_val)

            rep_date_str = format_chilean_date(inc.reported_date)
            notes_str = (getattr(inc, 'notes', '') or inc.diagnosis or inc.description or '').strip() or '-'

            bms_id_str = getattr(inc, 'bms_id', '') or ""
            if not bms_id_str:
                eq = eq_map.get(inc.equipment_id)
                if eq:
                    bms_id_str = getattr(eq, 'bms_id', '') or ""
            if not bms_id_str:
                bms_id_str = "N/A"

            pdf.cell(6, 6, pdf._enc(str(idx)), border=1, fill=True, align="C")
            pdf.cell(16, 6, pdf._enc(inc.id[:9]), border=1, fill=True, align="L")
            pdf.cell(20, 6, pdf._enc((inc.equipment_tag or inc.equipment_id)[:12]), border=1, fill=True, align="L")
            pdf.cell(18, 6, pdf._enc(bms_id_str[:11]), border=1, fill=True, align="L")
            pdf.cell(34, 6, pdf._enc(inc.title[:22]), border=1, fill=True, align="L")
            pdf.cell(44, 6, pdf._enc(notes_str[:30]), border=1, fill=True, align="L")
            pdf.cell(16, 6, pdf._enc(sev_str[:9]), border=1, fill=True, align="C")
            pdf.cell(18, 6, pdf._enc(st_str[:10]), border=1, fill=True, align="C")
            pdf.cell(14, 6, pdf._enc(rep_date_str[:10]), border=1, fill=True, align="C")
            pdf.ln(6)

        pdf.add_signature_block()
        pdf.output(output_path)
        return output_path

    def export_incidents_by_floor_pdf(
        self,
        incident_list: List[Incident],
        equipment_service,
        title_text: str = "Listado de Averías por Piso / Área",
        subtitle_text: str = "ControlHVAC CMMS - Gestión y Control de Averías",
        client_name: str = "",
        site_name: str = "",
        logo_path: str = "",
        library_service = None,
        include_floor_plans: bool = True,
        output_path: str = ""
    ) -> str:
        """Exports a PDF report where each floor/area with incidents is presented on its own dedicated page(s)."""
        eq_map = {}
        if equipment_service:
            try:
                all_eqs = equipment_service.get_all_equipment()
                for eq in all_eqs:
                    eq_map[eq.id] = eq
            except Exception:
                pass

        floors_dict: dict[str, List[Incident]] = {}
        for inc in incident_list:
            eq = eq_map.get(inc.equipment_id)
            if eq:
                fl = (getattr(eq, 'floor_area', '') or '').strip() or (eq.location_description or '').strip()
            else:
                fl = ""
            if not fl:
                fl = "Sin Piso / Área Asignada"
            if fl not in floors_dict:
                floors_dict[fl] = []
            floors_dict[fl].append(inc)

        def floor_sort_key(name: str):
            n_lower = name.lower()
            if "subt" in n_lower or "-1" in n_lower or "-2" in n_lower or "-3" in n_lower:
                return (0, n_lower)
            digits = re.findall(r'\d+', name)
            if digits:
                return (1, int(digits[0]), n_lower)
            if "azot" in n_lower or "tech" in n_lower or "cubier" in n_lower:
                return (3, n_lower)
            if "sin" in n_lower:
                return (4, n_lower)
            return (2, n_lower)

        sorted_floor_names = sorted(floors_dict.keys(), key=floor_sort_key)

        pdf = HVACReportPDF(
            title_text=title_text,
            subtitle_text=subtitle_text,
            logo_path=logo_path
        )

        severity_map = {
            "CRITICA": "Crítica",
            "ALTA": "Alta",
            "MEDIA": "Media",
            "BAJA": "Baja",
            "CRITICAL": "Crítica",
            "HIGH": "Alta",
            "MEDIUM": "Media",
            "LOW": "Baja"
        }
        status_map = {
            "REPORTADA": "Reportada",
            "EN_PROCESO": "En Reparación",
            "EN_REPARACION": "En Reparación",
            "RESUELTA": "Resuelta",
            "CANCELADA": "Cancelada"
        }

        def draw_table_header():
            pdf.set_fill_color(29, 34, 55)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("helvetica", "B", 7.5)
            # Total = 186mm: 6 + 16 + 20 + 18 + 34 + 44 + 16 + 18 + 14
            pdf.cell(6, 7, pdf._enc("#"), border=1, fill=True, align="C")
            pdf.cell(16, 7, pdf._enc("Código"), border=1, fill=True, align="L")
            pdf.cell(20, 7, pdf._enc("Tag Equipo"), border=1, fill=True, align="L")
            pdf.cell(18, 7, pdf._enc("ID BMS"), border=1, fill=True, align="L")
            pdf.cell(34, 7, pdf._enc("Título / Falla"), border=1, fill=True, align="L")
            pdf.cell(44, 7, pdf._enc("Notas / Detalle"), border=1, fill=True, align="L")
            pdf.cell(16, 7, pdf._enc("Severidad"), border=1, fill=True, align="C")
            pdf.cell(18, 7, pdf._enc("Estado"), border=1, fill=True, align="C")
            pdf.cell(14, 7, pdf._enc("Fecha Rep."), border=1, fill=True, align="C")
            pdf.ln(7)

        total_floors = len(sorted_floor_names)
        now_str = datetime.now().strftime("%d-%m-%Y %H:%M")

        for f_idx, floor_name in enumerate(sorted_floor_names, 1):
            floor_incs = floors_dict[floor_name]
            pdf.add_page()
            pdf.ln(2)

            pdf.add_section_title(f"Piso / Área: {floor_name}")

            summary_meta = [
                ("Piso / Sector", f"{floor_name} ({f_idx} de {total_floors})"),
                ("Averías en este Piso", f"{len(floor_incs)} incidencias"),
                ("Fecha de Emisión", now_str)
            ]
            if client_name:
                summary_meta.append(("Cliente", client_name))
            if site_name:
                summary_meta.append(("Instalación", site_name))

            pdf.add_metadata_grid(summary_meta)

            pdf.add_section_title(f"Averías e Incidencias - {floor_name}")
            draw_table_header()

            pdf.set_font("helvetica", "", 7.5)
            pdf.set_text_color(30, 41, 59)

            for idx, inc in enumerate(floor_incs, 1):
                if pdf.get_y() > 255:
                    pdf.add_page()
                    pdf.ln(2)
                    pdf.add_section_title(f"Averías e Incidencias - {floor_name} (Continuación)")
                    draw_table_header()
                    pdf.set_font("helvetica", "", 7.5)
                    pdf.set_text_color(30, 41, 59)

                if idx % 2 == 0:
                    pdf.set_fill_color(248, 250, 252)
                else:
                    pdf.set_fill_color(255, 255, 255)

                sev_val = inc.severity.value if hasattr(inc.severity, 'value') else str(inc.severity)
                sev_str = severity_map.get(sev_val.upper(), sev_val)

                st_val = inc.status.value if hasattr(inc.status, 'value') else str(inc.status)
                st_str = status_map.get(st_val.upper(), st_val)

                rep_date_str = format_chilean_date(inc.reported_date)
                notes_str = (getattr(inc, 'notes', '') or inc.diagnosis or inc.description or '').strip() or '-'

                bms_id_str = getattr(inc, 'bms_id', '') or ""
                if not bms_id_str:
                    eq = eq_map.get(inc.equipment_id)
                    if eq:
                        bms_id_str = getattr(eq, 'bms_id', '') or ""
                if not bms_id_str:
                    bms_id_str = "N/A"

                pdf.cell(6, 6, pdf._enc(str(idx)), border=1, fill=True, align="C")
                pdf.cell(16, 6, pdf._enc(inc.id[:9]), border=1, fill=True, align="L")
                pdf.cell(20, 6, pdf._enc((inc.equipment_tag or inc.equipment_id)[:12]), border=1, fill=True, align="L")
                pdf.cell(18, 6, pdf._enc(bms_id_str[:11]), border=1, fill=True, align="L")
                pdf.cell(34, 6, pdf._enc(inc.title[:22]), border=1, fill=True, align="L")
                pdf.cell(44, 6, pdf._enc(notes_str[:30]), border=1, fill=True, align="L")
                pdf.cell(16, 6, pdf._enc(sev_str[:9]), border=1, fill=True, align="C")
                pdf.cell(18, 6, pdf._enc(st_str[:10]), border=1, fill=True, align="C")
                pdf.cell(14, 6, pdf._enc(rep_date_str[:10]), border=1, fill=True, align="C")
                pdf.ln(6)

            # Render floor plan layout image if available
            if include_floor_plans and library_service:
                self._render_floor_plan_in_pdf(pdf, floor_name, library_service)

        # Add signature / validation block only on the last page of the report
        pdf.add_signature_block()

        pdf.output(output_path)
        return output_path



    def export_single_equipment_pdf(
        self,
        equipment: HVACEquipment,
        output_path: str,
        logo_path: str = "",
        client_name: str = "",
        site_name: str = "",
        incident_service=None,
        library_service=None
    ) -> str:
        pdf = HVACReportPDF(
            title_text=f"Ficha Técnica de Equipo: {equipment.tag}",
            subtitle_text="ControlHVAC CMMS - Gestión e Inventario de Activos",
            logo_path=logo_path
        )
        pdf.add_page()
        pdf.ln(2)

        # Section 1: Details
        pdf.add_section_title("Detalles del Equipo y Ubicación")
        
        from src.core.models.enums import SYSTEM_TYPE_LABELS, OPERATIONAL_STATUS_LABELS, MAINTENANCE_FREQUENCY_LABELS
        
        sys_type = SYSTEM_TYPE_LABELS.get(equipment.system_type, equipment.system_type.value if hasattr(equipment.system_type, 'value') else str(equipment.system_type))
        status = OPERATIONAL_STATUS_LABELS.get(equipment.status, equipment.status.value if hasattr(equipment.status, 'value') else str(equipment.status))
        freq = MAINTENANCE_FREQUENCY_LABELS.get(equipment.maintenance_frequency, equipment.maintenance_frequency.value if hasattr(equipment.maintenance_frequency, 'value') else str(equipment.maintenance_frequency))
        
        bms_st_str = getattr(equipment, 'bms_status', '') or "Operativo"
        bms_id_str = getattr(equipment, 'bms_id', '') or "N/A"
        loc_str = getattr(equipment, 'floor_area', '') or "Sin especificar"
        if not getattr(equipment, 'floor_area', '') and equipment.location_description:
            loc_str = equipment.location_description
            
        meta = [
            ("Tag / Equipo", equipment.tag),
            ("ID / Orden BMS", bms_id_str),
            ("Estado BMS / Control", bms_st_str),
            ("Piso / Nivel / Área", loc_str),
            ("Tipo de Sistema", sys_type),
            ("Fabricante", equipment.manufacturer or "N/A"),
            ("Modelo", getattr(equipment, 'model_number', None) or getattr(equipment, 'model', "N/A") or "N/A"),
            ("Nro. Serie", getattr(equipment, 'serial_number', None) or getattr(equipment, 'serial', "N/A") or "N/A"),
            ("Estado Operativo", status),
            ("Frecuencia Mant.", freq),
            ("Ubicación Específica", equipment.location_description or "N/A"),
            ("Fecha Instalación", format_chilean_date(equipment.installation_date) or "N/A"),
            ("Garantía Hasta", format_chilean_date(getattr(equipment, 'warranty_expiry_date', None) or getattr(equipment, 'warranty_expiry', None)) or "N/A"),
            ("Último Servicio", format_chilean_date(equipment.last_service_date) or "N/A"),
            ("Próximo Servicio", format_chilean_date(equipment.next_service_due) or "N/A")
        ]
        if client_name:
            meta.append(("Cliente", client_name))
        if site_name:
            meta.append(("Instalación", site_name))
            
        pdf.add_metadata_grid(meta)

        # Specs
        if equipment.technical_specs:
            from src.core.models.equipment import format_technical_specs
            formatted_specs = format_technical_specs(equipment.system_type, equipment.technical_specs)
            if formatted_specs:
                pdf.add_section_title("Especificaciones Técnicas")
                pdf.add_metadata_grid(formatted_specs)
        
        # Notes
        if equipment.notes:
            pdf.add_section_title("Notas y Observaciones")
            pdf.add_text_box(equipment.notes)

        # Historial (Averias)
        if incident_service:
            incs = incident_service.get_incidents_for_equipment(equipment.id)
            if incs:
                pdf.add_section_title("Historial de Averías y Reparaciones")
                inc_str = ""
                for inc in incs[:10]:
                    st_val = inc.status.value if hasattr(inc.status, 'value') else str(inc.status)
                    st_display = getattr(inc, 'status_display', st_val)
                    inc_str += f"• [{format_chilean_date(inc.reported_date)}] {inc.id}: {inc.title} - {st_display}\n"
                    if inc.action_taken:
                        inc_str += f"  Trabajo/Mejora: {inc.action_taken}\n"
                pdf.add_text_box(inc_str.strip())

        pdf.output(output_path)
        return output_path
