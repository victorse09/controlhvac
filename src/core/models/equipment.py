from __future__ import annotations
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

@dataclass
class HVACEquipment:
    id: str
    site_id: str
    client_id: str
    tag: str
    system_type: str
    manufacturer: str
    model_number: str
    serial_number: str
    installation_date: str
    bms_id: str = ""
    bms_status: str = "Operativo"
    floor_area: str = ""
    warranty_expiry: str = ""
    location_description: str = ""
    status: str = "OPERATIONAL"
    maintenance_frequency: str = "MONTHLY"
    runtime_hours: float = 0.0
    last_service_date: str = ""
    next_service_due: str = ""
    technical_specs: dict = field(default_factory=dict)
    notes: str = ""
    photos: list = field(default_factory=list)
    spare_parts: list = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    @property
    def name(self) -> str:
        parts = [self.manufacturer, self.model_number]
        full = " ".join(p.strip() for p in parts if p and p.strip())
        return full if full else (self.tag or "Equipo")

    @property
    def model(self) -> str:
        return self.model_number

    @property
    def serial(self) -> str:
        return self.serial_number

    @property
    def client_name(self) -> str:
        return getattr(self, '_client_name', '')

    @property
    def site_name(self) -> str:
        return getattr(self, '_site_name', '')

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> HVACEquipment:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

TECHNICAL_SPEC_FIELDS = {
    "AHU": [
        ("airflow_cfm", "Caudal", "float", "CFM", 0.0),
        ("airflow_unit", "Unidad de Caudal", "str", "", "CFM"),
        ("static_pressure_pa", "Presión Estática", "float", "Pa", 0.0),
        ("static_pressure_unit", "Unidad de Presión Estática", "str", "", "Pa"),
        ("fan_type", "Tipo de Ventilador", "str", "", ""),
        ("motor_power_kw", "Potencia Motor", "float", "kW", 0.0),
        ("motor_power_unit", "Unidad de Potencia Motor", "str", "", "kW"),
        ("motor_rpm", "RPM Motor", "int", "RPM", 0),
        ("vfd", "VFD (Variador de Frecuencia)", "bool", "", False),
        ("filter_type", "Tipo de Filtro", "str", "", ""),
        ("filter_count", "Cantidad de Filtros", "int", "", 0),
        ("chw_coil", "Serpentín Agua Helada", "bool", "", False),
        ("hw_coil", "Serpentín Agua Caliente", "bool", "", False),
        ("dx_coil", "Serpentín DX", "bool", "", False),
        ("refrigerant", "Refrigerante", "str", "", ""),
        ("refrigerant_charge", "Carga de Refrigerante", "float", "", 0.0),
        ("refrigerant_unit", "Unidad Carga Refrigerante (Kg/g)", "str", "", "Kg"),
        ("cooling_capacity_kw", "Capacidad Frío", "float", "kW", 0.0),
        ("cooling_capacity_unit", "Unidad de Capacidad Frío", "str", "", "kW"),
        ("heating_capacity_kw", "Capacidad Calor", "float", "kW", 0.0),
        ("heating_capacity_unit", "Unidad de Capacidad Calor", "str", "", "kW"),
    ],
    "FANCOIL": [
        ("pipe_config", "Configuración de Tubos", "str", "", "TWO_PIPE"),
        ("fan_speeds", "Velocidades de Ventilador", "int", "", 3),
        ("valve_type", "Tipo de Válvula", "str", "", ""),
        ("cooling_capacity_kw", "Capacidad / Potencia Frío", "float", "kW", 0.0),
        ("cooling_capacity_unit", "Unidad de Capacidad / Potencia", "str", "", "kW"),
        ("airflow_cfm", "Caudal", "float", "CFM", 0.0),
        ("airflow_unit", "Unidad de Caudal", "str", "", "CFM"),
        ("motor_type", "Tipo de Motor", "str", "", ""),
        ("motor_power_kw", "Potencia Motor", "float", "W", 0.0),
        ("motor_power_unit", "Unidad de Potencia Motor", "str", "", "W"),
        ("has_drain_pump", "Posee Bomba de Condensado", "bool", "", False),
        ("drain_pump_type", "Tipo de Bomba de Condensado", "str", "", ""),
    ],
    "VAV": [
        ("vav_type", "Tipo VAV", "str", "", ""),
        ("min_cfm", "Caudal Mínimo", "float", "CFM", 0.0),
        ("min_cfm_unit", "Unidad Caudal Mínimo", "str", "", "CFM"),
        ("max_cfm", "Caudal Máximo", "float", "CFM", 0.0),
        ("max_cfm_unit", "Unidad Caudal Máximo", "str", "", "CFM"),
        ("has_reheat", "Tiene Calefacción", "bool", "", False),
        ("reheat_type", "Tipo de Calefacción", "str", "", ""),
        ("controller_protocol", "Protocolo de Control", "str", "", ""),
    ],
    "SPLIT": [
        ("split_ui_type", "Tipo de Split UI (Presentación)", "str", "", ""),
        ("refrigerant", "Refrigerante", "str", "", ""),
        ("refrigerant_charge", "Carga de Refrigerante", "float", "", 0.0),
        ("refrigerant_unit", "Unidad Carga Refrigerante (Kg/g)", "str", "", "Kg"),
        ("cooling_capacity_btu", "Capacidad Frío", "float", "BTU/h", 0.0),
        ("cooling_capacity_unit", "Unidad de Capacidad Frío", "str", "", "BTU/h"),
        ("compressor_type", "Tipo de Compresor", "str", "", ""),
        ("indoor_units_count", "Cantidad Unidades Interiores", "int", "", 1),
        ("has_drain_pump", "Posee Bomba de Condensado", "bool", "", False),
        ("drain_pump_type", "Tipo de Bomba de Condensado", "str", "", ""),
    ],
    "WATER_COOLED_DUCT_COMPACT": [
        ("cooling_capacity_btu", "Capacidad Frío", "float", "BTU/h", 0.0),
        ("cooling_capacity_unit", "Unidad de Capacidad Frío", "str", "", "BTU/h"),
        ("airflow_cfm", "Caudal de Aire", "float", "CFM", 0.0),
        ("airflow_unit", "Unidad de Caudal de Aire", "str", "", "CFM"),
        ("static_pressure_pa", "Presión Estática Disponible", "float", "Pa", 0.0),
        ("static_pressure_unit", "Unidad de Presión Estática", "str", "", "Pa"),
        ("water_flow_gpm", "Caudal de Agua Condensador", "float", "GPM", 0.0),
        ("water_flow_unit", "Unidad Caudal de Agua", "str", "", "GPM"),
        ("refrigerant", "Refrigerante", "str", "", ""),
        ("refrigerant_charge", "Carga de Refrigerante", "float", "", 0.0),
        ("refrigerant_unit", "Unidad Carga Refrigerante (Kg/g)", "str", "", "Kg"),
        ("compressor_type", "Tipo de Compresor", "str", "", ""),
        ("condenser_hx_type", "Tipo Intercambiador Condensador", "str", "", ""),
        ("filter_type", "Tipo de Filtro", "str", "", ""),
    ],
    "ROOFTOP": [
        ("cooling_capacity_tons", "Capacidad Frío", "float", "", 0.0),
        ("cooling_capacity_unit", "Unidad de Capacidad Frío", "str", "", "Ton"),
        ("heating_type", "Tipo de Calefacción", "str", "", ""),
        ("economizer", "Economizador", "bool", "", False),
        ("refrigerant", "Refrigerante", "str", "", ""),
        ("refrigerant_charge", "Carga de Refrigerante", "float", "", 0.0),
        ("refrigerant_unit", "Unidad Carga Refrigerante (Kg/g)", "str", "", "Kg"),
        ("compressor_count", "Cantidad de Compresores", "int", "", 1),
    ],
    "CHILLER": [
        ("condenser_type", "Tipo de Condensador", "str", "", "AIR_COOLED"),
        ("cooling_capacity_tons", "Capacidad Frío", "float", "Ton", 0.0),
        ("cooling_capacity_unit", "Unidad de Capacidad Frío", "str", "", "Ton"),
        ("refrigerant", "Refrigerante", "str", "", ""),
        ("refrigerant_charge", "Carga de Refrigerante", "float", "", 0.0),
        ("refrigerant_unit", "Unidad Carga Refrigerante (Kg/g)", "str", "", "Kg"),
        ("compressor_type", "Tipo de Compresor", "str", "", "SCROLL"),
        ("ewt_design", "EWT Diseño", "float", "°C", 0.0),
        ("ewt_unit", "Unidad Temperatura EWT", "str", "", "°C"),
        ("lwt_design", "LWT Diseño", "float", "°C", 0.0),
        ("lwt_unit", "Unidad Temperatura LWT", "str", "", "°C"),
        ("compressor_count", "Cantidad de Compresores", "int", "", 1),
        ("evaporator_type", "Tipo de Evaporador", "str", "", ""),
    ],
    "COOLING_TOWER": [
        ("flow_rate_m3h", "Caudal", "float", "m3/h", 0.0),
        ("flow_rate_unit", "Unidad de Caudal", "str", "", "m3/h"),
        ("design_range_c", "Rango Diseño", "float", "°C", 0.0),
        ("design_range_unit", "Unidad Rango Diseño", "str", "", "°C"),
        ("design_approach_c", "Approach Diseño", "float", "°C", 0.0),
        ("design_approach_unit", "Unidad Approach Diseño", "str", "", "°C"),
        ("fill_type", "Tipo de Intercambiador de Calor", "str", "", ""),
        ("fan_type", "Tipo de Ventilador", "str", "", ""),
        ("motor_power_kw", "Potencia Motor", "float", "kW", 0.0),
        ("motor_power_unit", "Unidad de Potencia Motor", "str", "", "kW"),
        ("basin_makeup_type", "Tipo de Llenado de Piscina", "str", "", ""),
        ("drain_type", "Tipo de Drenaje", "str", "", ""),
        ("blowdown_type", "Tipo de Purga", "str", "", ""),
    ],
    "PUMP": [
        ("pump_type", "Tipo de Bomba", "str", "", ""),
        ("flow_rate_m3h", "Caudal", "float", "m3/h", 0.0),
        ("flow_rate_unit", "Unidad de Caudal", "str", "", "m3/h"),
        ("head_m", "Carga / Altura Manométrica", "float", "m", 0.0),
        ("head_unit", "Unidad de Carga / Altura", "str", "", "m"),
        ("motor_power_kw", "Potencia Motor", "float", "kW", 0.0),
        ("motor_power_unit", "Unidad de Potencia Motor", "str", "", "kW"),
        ("impeller_diameter_mm", "Diámetro Impulsor", "float", "mm", 0.0),
        ("impeller_diameter_unit", "Unidad Diámetro Impulsor", "str", "", "mm"),
        ("seal_type", "Tipo de Sello", "str", "", ""),
    ],
    "EXPANSION_TANK": [
        ("volume_liters", "Volumen", "float", "L", 0.0),
        ("volume_unit", "Unidad de Volumen", "str", "", "L"),
        ("max_pressure_bar", "Presión Máxima", "float", "Bar", 0.0),
        ("max_pressure_unit", "Unidad de Presión Máx.", "str", "", "Bar"),
        ("pre_charge_pressure_bar", "Presión Precarga", "float", "Bar", 0.0),
        ("pre_charge_pressure_unit", "Unidad de Presión Precarga", "str", "", "Bar"),
        ("connection_size", "Tamaño Conexión", "str", "", ""),
    ],
    "WATER_TREATMENT": [
        ("treatment_type", "Tipo de Tratamiento", "str", "", ""),
        ("dosing_system", "Sistema de Dosificación", "str", "", ""),
        ("conductivity_target", "Objetivo Conductividad", "float", "µS/cm", 0.0),
        ("ph_target", "Objetivo pH", "float", "", 0.0),
        ("capacity_m3", "Capacidad", "float", "m3", 0.0),
        ("capacity_unit", "Unidad de Capacidad", "str", "", "m3"),
    ],
    "VRF": [
        ("vrf_system_type", "Tipo de Sistema VRF", "str", "", "HEAT_PUMP"),
        ("outdoor_units", "Unidades Exteriores", "int", "", 1),
        ("indoor_units", "Unidades Interiores", "int", "", 1),
        ("total_capacity_kw", "Capacidad Total", "float", "kW", 0.0),
        ("total_capacity_unit", "Unidad de Capacidad Total", "str", "", "kW"),
        ("refrigerant", "Refrigerante", "str", "", ""),
        ("refrigerant_charge", "Carga de Refrigerante", "float", "", 0.0),
        ("refrigerant_unit", "Unidad Carga Refrigerante (Kg/g)", "str", "", "Kg"),
        ("pipe_length_m", "Longitud Tubería", "float", "m", 0.0),
        ("pipe_length_unit", "Unidad Longitud Tubería", "str", "", "m"),
    ],
    "VRF_INDOOR": [
        ("vrf_ui_type", "Tipo de Unidad Interior (Presentación)", "str", "", ""),
        ("cooling_capacity_btu", "Capacidad Frío", "float", "BTU/h", 0.0),
        ("cooling_capacity_unit", "Unidad de Capacidad Frío", "str", "", "BTU/h"),
        ("airflow_cfm", "Caudal", "float", "CFM", 0.0),
        ("airflow_unit", "Unidad de Caudal", "str", "", "CFM"),
        ("fan_speeds", "Velocidades de Ventilador", "int", "", 3),
        ("motor_type", "Tipo de Motor Ventilador", "str", "", ""),
        ("has_drain_pump", "Bomba de Condensado", "bool", "", False),
        ("parent_outdoor_tag", "Tag Unidad Exterior Asociada", "str", "", ""),
        ("hr_box_tag", "Tag Caja HR / BS Asociada", "str", "", ""),
        ("refrigerant", "Refrigerante", "str", "", ""),
    ],
    "VRF_HR_BOX": [
        ("hr_box_type", "Tipo de Caja HR / BS", "str", "", ""),
        ("ports_count", "Cantidad de Puertos / Ramales", "int", "", 4),
        ("connected_indoor_units", "Unidades Interiores Conectadas", "int", "", 1),
        ("max_capacity_kw", "Capacidad Máxima", "float", "kW", 0.0),
        ("max_capacity_unit", "Unidad de Capacidad Máxima", "str", "", "kW"),
        ("parent_outdoor_tag", "Tag Unidad Exterior Asociada", "str", "", ""),
        ("requires_drain", "Requiere Drenaje de Condensado", "bool", "", False),
    ],
    "FAN": [
        ("fan_function", "Función (Extracción/Inyección/Presurizador)", "str", "", ""),
        ("fan_type", "Tipo de Ventilador", "str", "", ""),
        ("airflow_cfm", "Caudal", "float", "CFM", 0.0),
        ("airflow_unit", "Unidad de Caudal", "str", "", "CFM"),
        ("static_pressure_pa", "Presión Estática", "float", "Pa", 0.0),
        ("static_pressure_unit", "Unidad de Presión Estática", "str", "", "Pa"),
        ("motor_power_kw", "Potencia Motor", "float", "kW", 0.0),
        ("motor_power_unit", "Unidad de Potencia Motor", "str", "", "kW"),
        ("drive_type", "Tipo de Transmisión", "str", "", ""),
        ("belt_count", "Cantidad de Correas (si usa correa)", "int", "", 0),
        ("bearing_type", "Tipo de Rodamientos", "str", "", ""),
        ("has_local_disconnect", "Tiene Corta Corriente Local", "bool", "", False),
        ("starting_method", "Tipo de Alimentación / Arranque", "str", "", ""),
        ("has_vfd", "Tiene Variador de Frecuencia (VDF)", "bool", "", False),
    ],
    "ELECTRICAL_CABINET": [
        ("cabinet_type", "Tipo de Gabinete", "str", "", ""),
        ("voltage", "Voltaje", "float", "V", 0.0),
        ("voltage_unit", "Unidad de Voltaje", "str", "", "V"),
        ("amperage", "Amperaje", "float", "A", 0.0),
        ("amperage_unit", "Unidad de Amperaje", "str", "", "A"),
        ("circuits_count", "Cantidad de Circuitos", "int", "", 0),
        ("has_vfd", "Tiene VFD", "bool", "", False),
        ("has_plc", "Tiene PLC", "bool", "", False),
        ("has_bms", "Integración BMS", "bool", "", False),
    ],
    "VFD": [
        ("vfd_application", "Aplicación / Equipo Controlado", "str", "", ""),
        ("associated_equipment_tag", "Tag Equipo Asociado", "str", "", ""),
        ("motor_power_kw", "Potencia Nominal", "float", "kW", 0.0),
        ("motor_power_unit", "Unidad de Potencia", "str", "", "kW"),
        ("voltage", "Tensión / Alimentación", "str", "", ""),
        ("nominal_current_a", "Corriente Nominal Salida", "float", "A", 0.0),
        ("nominal_current_unit", "Unidad de Corriente", "str", "", "A"),
        ("frequency_range_hz", "Rango de Frecuencia", "str", "Hz", "0 - 50 Hz"),
        ("vfd_control_mode", "Modo de Control", "str", "", ""),
        ("control_protocol", "Protocolo de Comunicación", "str", "", ""),
        ("has_transducer", "Tiene Transductor", "bool", "", False),
        ("transducer_type", "Tipo de Transductor", "str", "", ""),
        ("sensor_type", "Tipo de Sensor", "str", "", ""),
        ("transducer_signal", "Señal de Transductor", "str", "", ""),
        ("enclosure_ip", "Grado de Protección (IP / NEMA)", "str", "", ""),
        ("has_bypass", "Tiene Bypass", "bool", "", False),
        ("has_local_keypad", "Panel / Keypad Local", "bool", "", True),
        ("has_harmonic_filter", "Filtro de Armónicos / Reactancia", "bool", "", False),
    ],
    "ELECTRIC_WATER_HEATER": [
        ("electrical_phase", "Alimentación Eléctrica (Fases)", "str", "", ""),
        ("mounting_type", "Tipo de Montaje / Instalación", "str", "", ""),
        ("volume_liters", "Capacidad", "float", "L", 0.0),
        ("volume_unit", "Unidad de Capacidad", "str", "", "L"),
        ("heating_power_kw", "Potencia Eléctrica", "float", "kW", 0.0),
        ("heating_power_unit", "Unidad de Potencia", "str", "", "kW"),
        ("voltage", "Voltaje", "float", "V", 220.0),
        ("voltage_unit", "Unidad de Voltaje", "str", "", "V"),
        ("amperage", "Amperaje / Consumo", "float", "A", 0.0),
        ("amperage_unit", "Unidad de Amperaje", "str", "", "A"),
        ("elements_count", "Cantidad de Resistencias", "int", "", 1),
        ("element_type", "Tipo de Resistencia Calefactora", "str", "", ""),
        ("anode_type", "Tipo de Ánodo de Sacrificio", "str", "", ""),
        ("anode_status", "Estado / Cambio de Ánodo de Sacrificio", "str", "", ""),
        ("relief_valve_type", "Válvula de Alivio y Sobrepresión", "str", "", ""),
        ("max_pressure_bar", "Presión de Taraje / Trabajo Máx.", "float", "Bar", 0.0),
        ("max_pressure_unit", "Unidad de Presión", "str", "", "Bar"),
        ("thermostat_type", "Tipo de Termostato", "str", "", ""),
        ("has_expansion_vessel", "Posee Vaso de Expansión Sanitario", "bool", "", False),
        ("has_dielectric_unions", "Posee Manguitos Dieléctricos", "bool", "", True),
        ("has_check_valve", "Posee Válvula de Retención (Antirretorno)", "bool", "", True),
        ("has_drain_valve", "Posee Válvula de Drenaje / Vaciado", "bool", "", True),
    ]
}

TECHNICAL_SPEC_VALUE_TRANSLATIONS = {
    "TWO_PIPE": "2 Tubos",
    "FOUR_PIPE": "4 Tubos",
    "AIR_COOLED": "Enfriado por Aire",
    "WATER_COOLED": "Enfriado por Agua",
    "SCROLL": "Scroll",
    "SCREW": "Tornillo",
    "CENTRIFUGAL": "Centrífugo",
    "RECIPROCATING": "Reciprocante",
    "HEAT_PUMP": "Bomba de Calor",
    "HEAT_RECOVERY": "Recuperación de Calor",
    "EXTRACTION": "Extracción",
    "INJECTION": "Inyección",
    "PRESSURIZATION": "Presurizador",
    "SUPPLY_RETURN": "Inyección/Retorno",
}


def format_technical_specs(system_type: str, specs_dict: dict) -> list[tuple[str, str]]:
    """Returns a list of (Spanish Label, Formatted Value) tuples for an equipment's technical_specs."""
    if not specs_dict:
        return []

    st_str = system_type.value if hasattr(system_type, "value") else str(system_type or "")

    # Build lookup map from all system types (prioritizing the equipment's own system_type)
    field_meta: dict[str, tuple[str, str, str]] = {}
    for _, fields in TECHNICAL_SPEC_FIELDS.items():
        for fname, flabel, ftype, funit, _ in fields:
            field_meta[fname] = (flabel, ftype, funit)
    for fname, flabel, ftype, funit, _ in TECHNICAL_SPEC_FIELDS.get(st_str, []):
        field_meta[fname] = (flabel, ftype, funit)

    ref_unit = specs_dict.get("refrigerant_unit", "Kg") or "Kg"
    result: list[tuple[str, str]] = []

    paired_units = {
        "airflow_cfm": ("airflow_unit", "CFM", "Caudal"),
        "static_pressure_pa": ("static_pressure_unit", "Pa", "Presión Estática"),
        "motor_power_kw": ("motor_power_unit", "kW", "Potencia Motor"),
        "cooling_capacity_tons": ("cooling_capacity_unit", "Ton", "Capacidad Frío"),
        "cooling_capacity_kw": ("cooling_capacity_unit", "kW", "Capacidad / Potencia Frío"),
        "cooling_capacity_btu": ("cooling_capacity_unit", "BTU/h", "Capacidad Frío"),
        "heating_capacity_kw": ("heating_capacity_unit", "kW", "Capacidad Calor"),
        "heating_power_kw": ("heating_power_unit", "kW", "Potencia Eléctrica"),
        "min_cfm": ("min_cfm_unit", "CFM", "Caudal Mínimo"),
        "max_cfm": ("max_cfm_unit", "CFM", "Caudal Máximo"),
        "water_flow_gpm": ("water_flow_unit", "GPM", "Caudal de Agua Condensador"),
        "ewt_design": ("ewt_unit", "°C", "EWT Diseño"),
        "lwt_design": ("lwt_unit", "°C", "LWT Diseño"),
        "flow_rate_m3h": ("flow_rate_unit", "m3/h", "Caudal"),
        "design_range_c": ("design_range_unit", "°C", "Rango Diseño"),
        "design_approach_c": ("design_approach_unit", "°C", "Approach Diseño"),
        "head_m": ("head_unit", "m", "Carga / Altura Manométrica"),
        "impeller_diameter_mm": ("impeller_diameter_unit", "mm", "Diámetro Impulsor"),
        "volume_liters": ("volume_unit", "L", "Volumen"),
        "max_pressure_bar": ("max_pressure_unit", "Bar", "Presión Máxima"),
        "pre_charge_pressure_bar": ("pre_charge_pressure_unit", "Bar", "Presión Precarga"),
        "capacity_m3": ("capacity_unit", "m3", "Capacidad"),
        "total_capacity_kw": ("total_capacity_unit", "kW", "Capacidad Total"),
        "pipe_length_m": ("pipe_length_unit", "m", "Longitud Tubería"),
        "max_capacity_kw": ("max_capacity_unit", "kW", "Capacidad Máxima"),
        "voltage": ("voltage_unit", "V", "Voltaje"),
        "amperage": ("amperage_unit", "A", "Amperaje"),
        "nominal_current_a": ("nominal_current_unit", "A", "Corriente Nominal Salida"),
    }
    skip_unit_keys = {
        "refrigerant_unit",
        "airflow_unit",
        "static_pressure_unit",
        "motor_power_unit",
        "cooling_capacity_unit",
        "heating_capacity_unit",
        "heating_power_unit",
        "min_cfm_unit",
        "max_cfm_unit",
        "water_flow_unit",
        "ewt_unit",
        "lwt_unit",
        "flow_rate_unit",
        "design_range_unit",
        "design_approach_unit",
        "head_unit",
        "impeller_diameter_unit",
        "volume_unit",
        "max_pressure_unit",
        "pre_charge_pressure_unit",
        "capacity_unit",
        "total_capacity_unit",
        "pipe_length_unit",
        "max_capacity_unit",
        "voltage_unit",
        "amperage_unit",
        "nominal_current_unit",
    }

    for k, v in specs_dict.items():
        if k in skip_unit_keys:
            continue
        if k == "refrigerant_charge":
            try:
                if v and float(v) > 0:
                    val_num = float(v)
                    val_str = f"{int(val_num)}" if val_num.is_integer() else f"{val_num:g}"
                    result.append(("Cantidad de Gas Refrigerante", f"{val_str} {ref_unit}"))
            except (ValueError, TypeError):
                pass
            continue

        if k in paired_units and not (st_str == "VFD" and k == "voltage"):
            u_key, def_u, pair_lbl = paired_units[k]
            if k in field_meta:
                pair_lbl, _, meta_u = field_meta[k]
                if meta_u:
                    def_u = meta_u
            if st_str == "VFD" and k == "motor_power_kw":
                pair_lbl = "Potencia Nominal"
            elif st_str == "FANCOIL" and k == "motor_power_kw":
                def_u = "W"
            chosen_u = specs_dict.get(u_key, def_u) or def_u
            try:
                if v and float(v) > 0:
                    val_num = float(v)
                    val_str = f"{int(val_num)}" if val_num.is_integer() else f"{val_num:g}"
                    result.append((pair_lbl, f"{val_str} {chosen_u}"))
            except (ValueError, TypeError):
                pass
            continue

        if v is None or v is False or v == "" or v == 0 or v == 0.0:
            continue

        label, ftype, unit = field_meta.get(k, (k.replace("_", " ").capitalize(), "str", ""))

        if isinstance(v, bool) or ftype == "bool":
            val_display = "Sí" if v else "No"
        elif isinstance(v, float) or ftype == "float":
            try:
                fval = float(v)
                num_str = f"{int(fval)}" if fval.is_integer() else f"{fval:g}"
            except (ValueError, TypeError):
                num_str = str(v)
            val_display = f"{num_str} {unit}".strip() if (unit and f"({unit})" not in label) else num_str
        else:
            s_val = str(v).strip()
            val_display = TECHNICAL_SPEC_VALUE_TRANSLATIONS.get(s_val, s_val)
            if unit and f"({unit})" not in label and not val_display.endswith(unit):
                val_display = f"{val_display} {unit}"

        result.append((label, val_display))

    return result
