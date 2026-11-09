from enum import Enum

class SystemType(str, Enum):
    AHU = "AHU"
    FANCOIL = "FANCOIL"
    VAV = "VAV"
    SPLIT = "SPLIT"
    WATER_COOLED_DUCT_COMPACT = "WATER_COOLED_DUCT_COMPACT"
    ROOFTOP = "ROOFTOP"
    CHILLER = "CHILLER"
    COOLING_TOWER = "COOLING_TOWER"
    PUMP = "PUMP"
    EXPANSION_TANK = "EXPANSION_TANK"
    WATER_TREATMENT = "WATER_TREATMENT"
    VRF = "VRF"
    VRF_INDOOR = "VRF_INDOOR"
    VRF_HR_BOX = "VRF_HR_BOX"
    FAN = "FAN"
    ELECTRICAL_CABINET = "ELECTRICAL_CABINET"
    VFD = "VFD"
    ELECTRIC_WATER_HEATER = "ELECTRIC_WATER_HEATER"

SYSTEM_TYPE_LABELS = {
    SystemType.AHU: "Manejadora de Aire (UMA)",
    SystemType.FANCOIL: "Fan Coil",
    SystemType.VAV: "Caja de Volumen Variable",
    SystemType.SPLIT: "Split / Multi-Split",
    SystemType.WATER_COOLED_DUCT_COMPACT: "Compacto de Ducto Condensado por Agua",
    SystemType.ROOFTOP: "Rooftop",
    SystemType.CHILLER: "Chiller (aire/agua)",
    SystemType.COOLING_TOWER: "Torre de Enfriamiento",
    SystemType.PUMP: "Bomba de Agua",
    SystemType.EXPANSION_TANK: "Estanque de Expansión",
    SystemType.WATER_TREATMENT: "Tratamiento de Agua",
    SystemType.VRF: "VRV/VRF (Unidad Exterior)",
    SystemType.VRF_INDOOR: "VRV/VRF Unidad Interior",
    SystemType.VRF_HR_BOX: "Caja HR / BS (Heat Recovery VRV/VRF)",
    SystemType.FAN: "Ventilador Extracción/Inyección",
    SystemType.ELECTRICAL_CABINET: "Gabinete Eléctrico",
    SystemType.VFD: "Inversor / Variador de Frecuencia (VDF)",
    SystemType.ELECTRIC_WATER_HEATER: "Termo Eléctrico de Agua",
}

class OperationalStatus(str, Enum):
    OPERATIONAL = "OPERATIONAL"
    WARNING = "WARNING"
    FAULT = "FAULT"
    IN_MAINTENANCE = "IN_MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"

# Alias for backwards compatibility
EquipmentStatus = OperationalStatus

OPERATIONAL_STATUS_LABELS = {
    OperationalStatus.OPERATIONAL: "Operativo",
    OperationalStatus.WARNING: "En Observación",
    OperationalStatus.FAULT: "En Falla",
    OperationalStatus.IN_MAINTENANCE: "En Mantenimiento",
    OperationalStatus.DECOMMISSIONED: "Fuera de Servicio",
}
EQUIPMENT_STATUS_LABELS = OPERATIONAL_STATUS_LABELS

class GuideKind(str, Enum):
    SERVICE = "SERVICE"         # Guía de Servicio (OTS)
    MAINTENANCE = "MAINTENANCE" # Guía de Mantenimiento (OTM)

GUIDE_KIND_LABELS = {
    GuideKind.SERVICE: "Guía de Servicio (OTS)",
    GuideKind.MAINTENANCE: "Guía de Mantenimiento (OTM)",
}

class ServiceType(str, Enum):
    REPARACION = "REPARACION"
    MANTENCION = "MANTENCION"
    CORRECCION = "CORRECCION"
    VISITA_TECNICA = "VISITA_TECNICA"
    INSTALACION = "INSTALACION"
    INSPECCION = "INSPECCION"
    CAMBIO_FILTROS = "CAMBIO_FILTROS"
    MEJORA = "MEJORA"
    BAJA = "BAJA"
    OBSOLESCENCIA = "OBSOLESCENCIA"
    REEMPLAZO_EQUIPO = "REEMPLAZO_EQUIPO"
    REEMPLAZO_PIEZAS = "REEMPLAZO_PIEZAS"
    OTRO = "OTRO"

SERVICE_TYPE_LABELS = {
    ServiceType.REPARACION: "Reparación",
    ServiceType.MANTENCION: "Mantención Correctiva",
    ServiceType.CORRECCION: "Corrección / Ajuste",
    ServiceType.VISITA_TECNICA: "Visita Técnica / Diagnóstico",
    ServiceType.INSTALACION: "Instalación / Montaje",
    ServiceType.INSPECCION: "Inspección / Auditoría",
    ServiceType.CAMBIO_FILTROS: "Cambio de Filtros",
    ServiceType.MEJORA: "Mejora a Largo Plazo",
    ServiceType.BAJA: "Dando de Baja",
    ServiceType.OBSOLESCENCIA: "Obsolescencia",
    ServiceType.REEMPLAZO_EQUIPO: "Reemplazo de Equipo",
    ServiceType.REEMPLAZO_PIEZAS: "Reemplazo Partes y Piezas",
    ServiceType.OTRO: "Otro / Personalizado",
}

class WorkOrderType(str, Enum):
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    ONE_TIME = "ONE_TIME"

WORK_ORDER_TYPE_LABELS = {
    WorkOrderType.PREVENTIVE: "Preventivo (OTM)",
    WorkOrderType.CORRECTIVE: "Servicio / Correctivo (OTS)",
    WorkOrderType.ONE_TIME: "Única Vez",
}

class WorkOrderStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

WORK_ORDER_STATUS_LABELS = {
    WorkOrderStatus.SCHEDULED: "Programada",
    WorkOrderStatus.IN_PROGRESS: "En Progreso",
    WorkOrderStatus.COMPLETED: "Completada",
    WorkOrderStatus.OVERDUE: "Atrasada",
    WorkOrderStatus.CANCELLED: "Cancelada",
}

class MaintenanceFrequency(str, Enum):
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    ANNUAL = "ANNUAL"

    def get_days(self) -> int:
        return {
            self.WEEKLY: 7,
            self.BIWEEKLY: 14,
            self.MONTHLY: 30,
            self.QUARTERLY: 90,
            self.SEMI_ANNUAL: 180,
            self.ANNUAL: 365,
        }[self]

MAINTENANCE_FREQUENCY_LABELS = {
    MaintenanceFrequency.WEEKLY: "Semanal",
    MaintenanceFrequency.BIWEEKLY: "Quincenal",
    MaintenanceFrequency.MONTHLY: "Mensual",
    MaintenanceFrequency.QUARTERLY: "Trimestral",
    MaintenanceFrequency.SEMI_ANNUAL: "Semestral",
    MaintenanceFrequency.ANNUAL: "Anual",
}

class Priority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"

PRIORITY_LABELS = {
    Priority.LOW: "Baja",
    Priority.NORMAL: "Normal",
    Priority.HIGH: "Alta",
    Priority.URGENT: "Urgente",
}

class ToolStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    IN_CALIBRATION = "IN_CALIBRATION"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"

TOOL_STATUS_LABELS = {
    ToolStatus.AVAILABLE: "Disponible",
    ToolStatus.IN_USE: "En Uso",
    ToolStatus.IN_CALIBRATION: "En Calibración",
    ToolStatus.OUT_OF_SERVICE: "Fuera de Servicio",
}

class CondenserType(str, Enum):
    AIR_COOLED = "AIR_COOLED"
    WATER_COOLED = "WATER_COOLED"

CONDENSER_TYPE_LABELS = {
    CondenserType.AIR_COOLED: "Enfriado por Aire",
    CondenserType.WATER_COOLED: "Enfriado por Agua",
}

class ChillerCompressorType(str, Enum):
    SCROLL = "SCROLL"
    SCREW = "SCREW"
    CENTRIFUGAL = "CENTRIFUGAL"
    RECIPROCATING = "RECIPROCATING"

CHILLER_COMPRESSOR_TYPE_LABELS = {
    ChillerCompressorType.SCROLL: "Scroll",
    ChillerCompressorType.SCREW: "Tornillo",
    ChillerCompressorType.CENTRIFUGAL: "Centrífugo",
    ChillerCompressorType.RECIPROCATING: "Reciprocante",
}

class FancoilPipeConfig(str, Enum):
    TWO_PIPE = "TWO_PIPE"
    FOUR_PIPE = "FOUR_PIPE"

FANCOIL_PIPE_CONFIG_LABELS = {
    FancoilPipeConfig.TWO_PIPE: "2 Tubos",
    FancoilPipeConfig.FOUR_PIPE: "4 Tubos",
}

class VRFSystemType(str, Enum):
    HEAT_PUMP = "HEAT_PUMP"
    HEAT_RECOVERY = "HEAT_RECOVERY"

VRF_SYSTEM_TYPE_LABELS = {
    VRFSystemType.HEAT_PUMP: "Bomba de Calor",
    VRFSystemType.HEAT_RECOVERY: "Recuperación de Calor",
}

class FanType(str, Enum):
    EXTRACTION = "EXTRACTION"
    INJECTION = "INJECTION"
    PRESSURIZATION = "PRESSURIZATION"
    SUPPLY_RETURN = "SUPPLY_RETURN"

FAN_TYPE_LABELS = {
    FanType.EXTRACTION: "Extracción",
    FanType.INJECTION: "Inyección",
    FanType.PRESSURIZATION: "Presurizador",
    FanType.SUPPLY_RETURN: "Inyección/Retorno",
}

class IncidentType(str, Enum):
    AVERIA = "AVERIA"
    OBSERVACION = "OBSERVACION"
    ELECTRICO = "ELECTRICO"
    MOTORES = "MOTORES"
    VALVULAS = "VALVULAS"
    SOLDADURA = "SOLDADURA"
    COMPRESOR = "COMPRESOR"
    ESTRUCTURAL = "ESTRUCTURAL"
    OTRO = "OTRO"

INCIDENT_TYPE_LABELS = {
    IncidentType.AVERIA: "Avería / Falla de Equipo",
    IncidentType.OBSERVACION: "Observación / Alerta Preventiva",
    IncidentType.ELECTRICO: "Eléctrico (Contactores, Relés, Luces)",
    IncidentType.MOTORES: "Motores (Reparación, Rebobinado, Rodamientos)",
    IncidentType.VALVULAS: "Válvulas y Actuadores",
    IncidentType.SOLDADURA: "Soldadura y Fugas de Tuberías",
    IncidentType.COMPRESOR: "Compresor y Circuito Frigorífico",
    IncidentType.ESTRUCTURAL: "Estructural / Ductos / Aislación",
    IncidentType.OTRO: "Otro Trabajo / Reparación",
}

class IncidentSeverity(str, Enum):
    CRITICA = "CRITICA"
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"

INCIDENT_SEVERITY_LABELS = {
    IncidentSeverity.CRITICA: "Crítica (Equipo Detenido)",
    IncidentSeverity.ALTA: "Alta (Falla Parcial / Rendimiento)",
    IncidentSeverity.MEDIA: "Media (Requiere Intervención)",
    IncidentSeverity.BAJA: "Baja (Cosmética / Leve)",
}

class IncidentStatus(str, Enum):
    REPORTADA = "REPORTADA"
    EN_DIAGNOSTICO = "EN_DIAGNOSTICO"
    ESPERANDO_REPUESTOS = "ESPERANDO_REPUESTOS"
    EN_REPARACION = "EN_REPARACION"
    RESUELTA = "RESUELTA"
    CANCELADA = "CANCELADA"

INCIDENT_STATUS_LABELS = {
    IncidentStatus.REPORTADA: "Reportada / Pendiente",
    IncidentStatus.EN_DIAGNOSTICO: "En Diagnóstico",
    IncidentStatus.ESPERANDO_REPUESTOS: "Esperando Repuestos",
    IncidentStatus.EN_REPARACION: "En Reparación",
    IncidentStatus.RESUELTA: "Resuelta / Reparada",
    IncidentStatus.CANCELADA: "Cancelada",
}

class TechnicianStatus(str, Enum):
    ACTIVE = "ACTIVO"
    INACTIVE = "INACTIVO"
    ON_LEAVE = "LICENCIA"
    VACATION = "VACACIONES"

TECHNICIAN_STATUS_LABELS = {
    TechnicianStatus.ACTIVE: "Activo / Disponible",
    TechnicianStatus.INACTIVE: "Inactivo",
    TechnicianStatus.ON_LEAVE: "Licencia Médica",
    TechnicianStatus.VACATION: "Vacaciones",
}

class TechnicianSpecialty(str, Enum):
    HVAC = "HVAC"
    ELECTRICAL = "ELECTRICAL"
    REFRIGERATION = "REFRIGERATION"
    AUTOMATION = "AUTOMATION"
    MECHANICAL = "MECHANICAL"
    ASSISTANT = "ASSISTANT"
    OTHER = "OTHER"

TECHNICIAN_SPECIALTY_LABELS = {
    TechnicianSpecialty.HVAC: "Técnico en Climatización / HVAC",
    TechnicianSpecialty.ELECTRICAL: "Técnico Electricista",
    TechnicianSpecialty.REFRIGERATION: "Técnico en Refrigeración Industrial",
    TechnicianSpecialty.AUTOMATION: "Técnico en Control y Automatización / BMS",
    TechnicianSpecialty.MECHANICAL: "Técnico Mecánico / Soldadura",
    TechnicianSpecialty.ASSISTANT: "Ayudante / Asistente Técnico",
    TechnicianSpecialty.OTHER: "Otro",
}

class LibraryCategory(str, Enum):
    FLOOR_PLAN = "FLOOR_PLAN"
    MANUAL = "MANUAL"
    DATASHEET = "DATASHEET"
    SAFETY_SHEET = "SAFETY_SHEET"
    DIAGRAM = "DIAGRAM"
    IMAGE = "IMAGE"
    CERTIFICATE = "CERTIFICATE"
    OTHER = "OTHER"

LIBRARY_CATEGORY_LABELS = {
    LibraryCategory.FLOOR_PLAN: "Plano de Planta / Piso / Área",
    LibraryCategory.MANUAL: "Manual de Usuario / Fabricante",
    LibraryCategory.DATASHEET: "Ficha Técnica (Datasheet)",
    LibraryCategory.SAFETY_SHEET: "Hoja de Seguridad (HDS / MSDS)",
    LibraryCategory.DIAGRAM: "Plano / Diagrama Eléctrico o Frigorífico",
    LibraryCategory.IMAGE: "Fotografía / Evidencia Gráfica",
    LibraryCategory.CERTIFICATE: "Certificado / Garantía / Calibración",
    LibraryCategory.OTHER: "Documentación Variada / Otro",
}


