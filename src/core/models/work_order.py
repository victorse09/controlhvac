from __future__ import annotations
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

@dataclass
class ChecklistItem:
    id: str
    description: str
    category: str
    is_completed: bool = False
    measured_value: str = ""
    unit: str = ""
    expected_min: str = ""
    expected_max: str = ""
    status: str = "PENDING"
    notes: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    @property
    def task_description(self) -> str:
        return self.description

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ChecklistItem:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass
class WorkOrder:
    id: str
    equipment_id: str
    equipment_tag: str
    site_id: str
    site_name: str
    client_id: str
    client_name: str
    title: str
    description: str
    work_order_type: str
    guide_kind: str = "SERVICE" # "SERVICE" (OTS) or "MAINTENANCE" (OTM)
    service_type: str = "REPARACION"
    is_manual_equipment: bool = False
    manual_equipment_tag: str = ""
    manual_location: str = ""
    manual_client: str = ""
    manual_site: str = ""
    diagnosis: str = ""
    work_performed: str = ""
    priority: str = "NORMAL"
    status: str = "SCHEDULED"
    scheduled_date: str = ""
    start_date: str = ""
    completed_date: str = ""
    due_date: str = ""
    assigned_technician: str = ""
    checklist: list = field(default_factory=list)
    parts_used: list = field(default_factory=list)
    materials_used: list = field(default_factory=list)
    tools_used: list = field(default_factory=list)
    incident_id: str = ""
    photos: list = field(default_factory=list)
    attachments: list = field(default_factory=list)
    labor_hours: float = 0.0
    total_cost: float = 0.0
    observations: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        # Do not overwrite self.id with UUID if it's empty so services can assign correlatives (OTS... / OTM...)
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
        # Convert dictionaries to ChecklistItem if necessary
        if self.checklist:
            self.checklist = [
                ChecklistItem.from_dict(item) if isinstance(item, dict) else item 
                for item in self.checklist
            ]

    @property
    def type(self) -> str:
        return self.work_order_type

    @property
    def assigned_to(self) -> str:
        return self.assigned_technician

    def to_dict(self) -> dict:
        d = asdict(self)
        d['checklist'] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.checklist]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> WorkOrder:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

DEFAULT_CHECKLISTS = {
    "AHU": [
        {"id": "", "description": "Revisión de caída de presión en filtros (ΔP)", "category": "Mecánico", "unit": "Pa"},
        {"id": "", "description": "Medición de corriente motor ventilador (L1/L2/L3)", "category": "Eléctrico", "unit": "A"},
        {"id": "", "description": "Inspección de vibración de rodamientos", "category": "Mecánico"},
        {"id": "", "description": "Verificación tensión y estado de correas", "category": "Mecánico"},
        {"id": "", "description": "Medición ΔT serpentín de aire/agua", "category": "Controles", "unit": "°C"},
        {"id": "", "description": "Revisión de recorrido actuador damper", "category": "Controles"},
        {"id": "", "description": "Limpieza de drenaje de condensado", "category": "Mecánico"},
        {"id": "", "description": "Lubricación de rodamientos motor/ventilador", "category": "Mecánico"},
        {"id": "", "description": "Inspección de aislamiento acústico/térmico", "category": "General"},
        {"id": "", "description": "Ajuste de conexiones eléctricas", "category": "Eléctrico"},
    ],
    "FANCOIL": [
        {"id": "", "description": "Inspección y limpieza de filtro de aire", "category": "Mecánico"},
        {"id": "", "description": "Medición ΔT del aire (Suministro/Retorno)", "category": "Refrigeración", "unit": "°C"},
        {"id": "", "description": "Medición ΔT del agua (EWT/LWT)", "category": "Mecánico", "unit": "°C"},
        {"id": "", "description": "Medición de corriente del motor del ventilador", "category": "Eléctrico", "unit": "A"},
        {"id": "", "description": "Inspección y limpieza de bandeja de drenaje", "category": "Mecánico"},
        {"id": "", "description": "Calibración y verificación de termostato", "category": "Controles"},
        {"id": "", "description": "Comprobación de válvula de control a 0/100%", "category": "Controles"},
        {"id": "", "description": "Revisión de ruidos o vibraciones inusuales", "category": "General"},
    ],
    "VAV": [
        {"id": "", "description": "Calibración de caudalímetro (Airflow)", "category": "Controles", "unit": "CFM"},
        {"id": "", "description": "Revisión de recorrido actuador del damper", "category": "Controles"},
        {"id": "", "description": "Verificación del sensor de temperatura de descarga", "category": "Controles", "unit": "°C"},
        {"id": "", "description": "Comprobación de funcionamiento del recalentamiento", "category": "Mecánico"},
        {"id": "", "description": "Inspección de aislación interna", "category": "General"},
        {"id": "", "description": "Prueba de lazo de control desde BMS", "category": "Controles"},
        {"id": "", "description": "Verificación de alimentación eléctrica de control", "category": "Eléctrico", "unit": "V"},
        {"id": "", "description": "Revisión general de fugas de aire", "category": "Mecánico"},
    ],
    "SPLIT": [
        {"id": "", "description": "Medición de presión de succión y descarga", "category": "Refrigeración", "unit": "PSI"},
        {"id": "", "description": "Cálculo de sobrecalentamiento (Superheat)", "category": "Refrigeración", "unit": "°C"},
        {"id": "", "description": "Cálculo de subenfriamiento (Subcooling)", "category": "Refrigeración", "unit": "°C"},
        {"id": "", "description": "Medición de corriente de compresor", "category": "Eléctrico", "unit": "A"},
        {"id": "", "description": "Limpieza de filtros unidad interior", "category": "Mecánico"},
        {"id": "", "description": "Prueba de drenaje de unidad interior", "category": "Mecánico"},
        {"id": "", "description": "Limpieza de serpentín condensador", "category": "Mecánico"},
        {"id": "", "description": "Revisión de aislamientos en tuberías de refrigerante", "category": "Mecánico"},
    ],
    "WATER_COOLED_DUCT_COMPACT": [
        {"id": "", "description": "Medición de presión de succión y descarga de refrigerante", "category": "Refrigeración", "unit": "PSI"},
        {"id": "", "description": "Medición ΔT de agua en condensador (EWT/LWT)", "category": "Refrigeración", "unit": "°C"},
        {"id": "", "description": "Medición ΔP de agua en intercambiador coaxial/placas", "category": "Mecánico", "unit": "PSI"},
        {"id": "", "description": "Inspección y limpieza de filtro Y de agua y válvula motorizada", "category": "Mecánico"},
        {"id": "", "description": "Inspección y limpieza de filtro de aire de retorno", "category": "Mecánico"},
        {"id": "", "description": "Limpieza de bandeja de condensado y bomba/línea de drenaje", "category": "Mecánico"},
        {"id": "", "description": "Medición de corriente de compresor y ventilador centrífugo", "category": "Eléctrico", "unit": "A"},
        {"id": "", "description": "Verificación de presostatos de alta/baja e interruptor de flujo de agua", "category": "Controles"},
    ],
    "ROOFTOP": [
        {"id": "", "description": "Calibración de economizador", "category": "Controles"},
        {"id": "", "description": "Medición de presión manifold de gas", "category": "Mecánico", "unit": "wc"},
        {"id": "", "description": "Limpieza y verificación de sensor de flama", "category": "Controles"},
        {"id": "", "description": "Inspección de ventilador de condensador", "category": "Mecánico"},
        {"id": "", "description": "Revisión de contactores de compresores", "category": "Eléctrico"},
        {"id": "", "description": "Limpieza de serpentines evaporador/condensador", "category": "Mecánico"},
        {"id": "", "description": "Verificación de correas y rodamientos (suministro)", "category": "Mecánico"},
        {"id": "", "description": "Medición de consumos de corriente generales", "category": "Eléctrico", "unit": "A"},
    ],
    "CHILLER": [
        {"id": "", "description": "Medición de EWT/LWT en evaporador", "category": "Refrigeración", "unit": "°C"},
        {"id": "", "description": "Medición de EWT/LWT en condensador", "category": "Refrigeración", "unit": "°C"},
        {"id": "", "description": "Cálculo de temperaturas de aproximación (Approach)", "category": "Refrigeración", "unit": "°C"},
        {"id": "", "description": "Revisión de presión, temperatura y nivel de aceite", "category": "Refrigeración"},
        {"id": "", "description": "Medición de amperaje en compresores (L1/L2/L3)", "category": "Eléctrico", "unit": "A"},
        {"id": "", "description": "Inspección de posición de la válvula EEV", "category": "Controles", "unit": "%"},
        {"id": "", "description": "Revisión de alarmas en panel de control", "category": "Controles"},
        {"id": "", "description": "Inspección de vibración en compresor(es)", "category": "Mecánico"},
    ],
    "COOLING_TOWER": [
        {"id": "", "description": "Inspección de nivel de agua en piscina", "category": "Mecánico"},
        {"id": "", "description": "Revisión de transmisión y correas del ventilador", "category": "Mecánico"},
        {"id": "", "description": "Inspección de eliminadores de gota (Drift)", "category": "Mecánico"},
        {"id": "", "description": "Análisis rápido de calidad de agua (Conductividad)", "category": "Químico", "unit": "µS/cm"},
        {"id": "", "description": "Análisis rápido de calidad de agua (pH)", "category": "Químico"},
        {"id": "", "description": "Prueba de switch de vibración", "category": "Controles"},
        {"id": "", "description": "Limpieza de rejillas y filtros en succión", "category": "Mecánico"},
        {"id": "", "description": "Engrase de descansos de ventilador", "category": "Mecánico"},
    ],
    "PUMP": [
        {"id": "", "description": "Medición de presión de succión y descarga", "category": "Mecánico", "unit": "PSI"},
        {"id": "", "description": "Cálculo de Carga Dinámica Total (TDH)", "category": "Mecánico", "unit": "m"},
        {"id": "", "description": "Medición de corriente del motor (L1/L2/L3)", "category": "Eléctrico", "unit": "A"},
        {"id": "", "description": "Inspección de fugas en sello mecánico", "category": "Mecánico"},
        {"id": "", "description": "Medición de temperatura en rodamientos", "category": "Mecánico", "unit": "°C"},
        {"id": "", "description": "Verificación de alineación de acople", "category": "Mecánico"},
        {"id": "", "description": "Reapriete de pernos base", "category": "Mecánico"},
        {"id": "", "description": "Inspección de válvula de retención y filtro Y", "category": "Mecánico"},
    ],
    "EXPANSION_TANK": [
        {"id": "", "description": "Medición de presión de precarga de aire", "category": "Mecánico", "unit": "bar"},
        {"id": "", "description": "Inspección de integridad de la vejiga (golpes)", "category": "Mecánico"},
        {"id": "", "description": "Prueba de válvula de alivio", "category": "Mecánico"},
        {"id": "", "description": "Inspección visual de corrosión externa", "category": "Mecánico"},
        {"id": "", "description": "Revisión de válvula de aislamiento y drenaje", "category": "Mecánico"},
        {"id": "", "description": "Lectura de presión en sistema hidrónico", "category": "Mecánico", "unit": "bar"},
    ],
    "WATER_TREATMENT": [
        {"id": "", "description": "Medición de conductividad real del agua", "category": "Químico", "unit": "µS/cm"},
        {"id": "", "description": "Medición de pH real del agua", "category": "Químico"},
        {"id": "", "description": "Revisión de nivel de biocida/inhibidor en estanques", "category": "Químico"},
        {"id": "", "description": "Prueba de apertura de válvula de purga (Blowdown)", "category": "Controles"},
        {"id": "", "description": "Limpieza y calibración de sondas", "category": "Controles"},
        {"id": "", "description": "Verificación de bombas dosificadoras", "category": "Mecánico"},
        {"id": "", "description": "Inspección de filtro de lecho profundo/separador de arena", "category": "Mecánico"},
    ],
    "VRF": [
        {"id": "", "description": "Lectura de frecuencia del compresor inverter", "category": "Refrigeración", "unit": "Hz"},
        {"id": "", "description": "Lectura de presión Alta y Baja (HP/LP)", "category": "Refrigeración", "unit": "PSI"},
        {"id": "", "description": "Revisión de pulsos de EEV unidades interiores", "category": "Controles"},
        {"id": "", "description": "Verificación de ciclo de retorno de aceite", "category": "Refrigeración"},
        {"id": "", "description": "Medición de voltaje de bus de comunicaciones", "category": "Eléctrico", "unit": "VDC"},
        {"id": "", "description": "Revisión de códigos de error históricos", "category": "Controles"},
        {"id": "", "description": "Inspección de ventiladores condensador exterior", "category": "Mecánico"},
        {"id": "", "description": "Limpieza general de unidad condensadora", "category": "Mecánico"},
    ],
    "VRF_INDOOR": [
        {"id": "", "description": "Inspección y limpieza de filtros de aire de retorno", "category": "Mecánico"},
        {"id": "", "description": "Limpieza de serpentín evaporador y turbina/ventilador", "category": "Mecánico"},
        {"id": "", "description": "Inspección y limpieza de bandeja de condensado y bomba de drenaje", "category": "Mecánico"},
        {"id": "", "description": "Medición ΔT de aire (Inyección / Retorno)", "category": "Refrigeración", "unit": "°C"},
        {"id": "", "description": "Verificación de apertura/pulsos de válvula de expansión electrónica (EEV)", "category": "Controles"},
        {"id": "", "description": "Medición de consumo eléctrico del motor ventilador", "category": "Eléctrico", "unit": "A"},
        {"id": "", "description": "Comprobación de comunicación con unidad exterior / control remoto / BMS", "category": "Controles"},
        {"id": "", "description": "Revisión de ruidos, vibraciones y aislamiento térmico", "category": "General"},
    ],
    "VRF_HR_BOX": [
        {"id": "", "description": "Inspección visual de fugas de refrigerante y estado de aislamiento térmico", "category": "Refrigeración"},
        {"id": "", "description": "Verificación de conmutación de válvulas solenoides / motorizadas (Frío/Calor)", "category": "Controles"},
        {"id": "", "description": "Medición de temperaturas en tuberías de alta, baja y líquido por ramal", "category": "Refrigeración", "unit": "°C"},
        {"id": "", "description": "Revisión de tarjeta electrónica de control y direccionamiento", "category": "Controles"},
        {"id": "", "description": "Medición de voltaje de alimentación y señal de comunicación F1/F2", "category": "Eléctrico", "unit": "V"},
        {"id": "", "description": "Inspección de bandeja y línea de drenaje de condensado (si aplica)", "category": "Mecánico"},
        {"id": "", "description": "Verificación de ruidos anormales durante cambio de ciclo (golpe de ariete/expansión)", "category": "General"},
    ],
    "FAN": [
        {"id": "", "description": "Medición de amperaje del motor (L1/L2/L3)", "category": "Eléctrico", "unit": "A"},
        {"id": "", "description": "Inspección general de vibración", "category": "Mecánico"},
        {"id": "", "description": "Inspección de estado y tensión de correas", "category": "Mecánico"},
        {"id": "", "description": "Lubricación de rodamientos de chumacera/motor", "category": "Mecánico"},
        {"id": "", "description": "Medición estimada de caudal de aire", "category": "Mecánico", "unit": "CFM"},
        {"id": "", "description": "Limpieza de hélice/rodete", "category": "Mecánico"},
        {"id": "", "description": "Revisión de conexiones de ductos/acoples flexibles", "category": "Mecánico"},
        {"id": "", "description": "Verificación de compuertas anti-retorno", "category": "Mecánico"},
    ],
    "ELECTRICAL_CABINET": [
        {"id": "", "description": "Termografía / Escaneo térmico de conexiones", "category": "Eléctrico", "unit": "°C"},
        {"id": "", "description": "Torque de interruptores (Breakers)", "category": "Eléctrico"},
        {"id": "", "description": "Inspección visual de contactores (Fogueos)", "category": "Eléctrico"},
        {"id": "", "description": "Respaldo de parámetros de VFD (si aplica)", "category": "Controles"},
        {"id": "", "description": "Prueba de falla a tierra (Ground Fault)", "category": "Eléctrico"},
        {"id": "", "description": "Limpieza de filtros/ventiladores del tablero", "category": "Eléctrico"},
        {"id": "", "description": "Verificación de voltaje entrada L1-L2, L2-L3, L1-L3", "category": "Eléctrico", "unit": "V"},
        {"id": "", "description": "Inspección de fusibles y relés", "category": "Eléctrico"},
    ],
    "VFD": [
        {"id": "", "description": "Respaldo y verificación de parámetros de configuración del variador", "category": "Controles"},
        {"id": "", "description": "Medición de voltaje de entrada (L1-L2, L2-L3, L1-L3) y bus DC", "category": "Eléctrico", "unit": "V"},
        {"id": "", "description": "Medición de corriente de salida hacia el motor (U, V, W)", "category": "Eléctrico", "unit": "A"},
        {"id": "", "description": "Lectura de frecuencia de operación y temperatura interna (IGBT / Disipador)", "category": "Controles", "unit": "°C"},
        {"id": "", "description": "Limpieza de disipador térmico y ventiladores de refrigeración internos", "category": "Mecánico"},
        {"id": "", "description": "Reapriete de bornes de fuerza y control / Inspección termográfica", "category": "Eléctrico"},
        {"id": "", "description": "Revisión de historial de fallas/alarmas y prueba de señal de referencia BMS (0-10V / Red)", "category": "Controles"},
    ],
    "ELECTRIC_WATER_HEATER": [
        {"id": "", "description": "Inspección y/o cambio de ánodo de sacrificio (magnesio/aluminio)", "category": "Mecánico"},
        {"id": "", "description": "Prueba de apertura de válvula de alivio y sobrepresión / seguridad", "category": "Mecánico"},
        {"id": "", "description": "Medición de voltaje de alimentación (Monofásico 220V / Trifásico 380V)", "category": "Eléctrico", "unit": "V"},
        {"id": "", "description": "Medición de consumo eléctrico y resistencia óhmica de elementos calefactores", "category": "Eléctrico", "unit": "A"},
        {"id": "", "description": "Purga de sedimentos / vaciado y limpieza de sarro en fondo de estanque", "category": "Mecánico"},
        {"id": "", "description": "Verificación de corte por termostato de regulación y límite de seguridad térmica", "category": "Controles", "unit": "°C"},
        {"id": "", "description": "Inspección de manguitos dieléctricos, válvula de retención y ausencia de filtraciones", "category": "Mecánico"},
        {"id": "", "description": "Reapriete de bornes eléctricos e inspección de aislamiento térmico", "category": "Eléctrico"},
    ],
}
