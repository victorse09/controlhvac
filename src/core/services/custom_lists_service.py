import os
from typing import Dict, List, Any
from src.data.json_storage import JsonStorageEngine

DEFAULT_CUSTOM_LISTS = {
    # GENERAL / CONTROL BMS
    "bms_status": [
        "Operativo",
        "En Falla",
        "Sin Grafica",
        "Sin Control",
        "Fuera de Servicio",
        "Inexistente",
    ],

    # AHU
    "ahu_filter_type": [
        "Filtro Sintético G4",
        "Filtro Bolsa F7",
        "Filtro Bolsa F9",
        "Filtro HEPA H13",
        "Filtro HEPA H14",
        "Filtro Carbón Activado",
        "Pre-filtro Metálico Lavable",
        "Filtro Compacto V-Bank",
    ],
    "ahu_refrigerant": [
        "R410A",
        "R32",
        "R134a",
        "R407C",
        "R22",
        "R454B",
        "R1234ze",
    ],
    "ahu_fan_type": [
        "Plug Fan EC (Electrónico)",
        "Centrífugo Inclinado hacia Atrás",
        "Centrífugo Inclinado hacia Adelante (Si-roco)",
        "Axial de Alta Eficiencia",
    ],

    # FANCOIL
    "fancoil_pipe_config": [
        "2 Tubos (2-Pipe)",
        "4 Tubos (4-Pipe)",
    ],
    "fancoil_valve_type": [
        "Válvula 2 Vías ON/OFF",
        "Válvula 3 Vías ON/OFF",
        "Válvula Proporcional Modulante 0-10V",
        "Válvula PICV (Independiente de Presión)",
        "Sin Válvula",
    ],
    "fancoil_motor_type": [
        "Motor EC (Electrónico Modulante)",
        "Motor AC 3 Velocidades",
        "Motor Inverter DC",
    ],

    # VAV
    "vav_type": [
        "Solo Frío (Cooling Only)",
        "Con Calefacción Eléctrica",
        "Con Serpentín Agua Caliente (Hot Water)",
        "Con Ventilador Paralelo (Fan-Powered)",
        "Con Ventilador Serie (Fan-Powered)",
        "Doble Conducto (Dual Duct)",
    ],
    "vav_heating_type": [
        "Resistencia Eléctrica Modulante (SCR)",
        "Resistencia Eléctrica Escalonada",
        "Serpentín de Agua Caliente",
        "Sin Calefacción",
    ],
    "vav_protocol": [
        "BACnet MS/TP",
        "BACnet IP",
        "Modbus RTU",
        "Modbus TCP",
        "LonWorks",
        "N2 (Johnson Controls)",
        "Analógico 0-10V",
    ],

    # SPLIT
    "split_ui_type": [
        "Presentación Muro",
        "Presentación Cielo",
        "Piso Cielo",
        "Ducto",
        "Baja Silueta",
        "Multi-posicional",
        "Modular",
        "Cassette",
        "Consola de Piso",
        "Columna / Gabinete Vertical",
    ],
    "split_refrigerant": [
        "R410A",
        "R32",
        "R407C",
        "R22",
    ],
    "split_compressor_type": [
        "Inverter Scroll",
        "Inverter Twin Rotary",
        "Rotary Fijo",
        "Scroll Fijo",
        "Reciprocante Fijo",
    ],
    "split_drain_pump_type": [
        "Mini",
        "Maxi",
        "Mini Tanque",
        "Tanque",
        "Estanque y Bomba",
        "Incorporada de Fábrica (Interna)",
        "Peristáltica",
        "Esquinera / Canaleta",
        "Sin Bomba (Drenaje por Gravedad)",
    ],

    # COMPACTO DE DUCTO CONDENSADO POR AGUA (WSHP / Compacto Agua)
    "wcdc_condenser_hx_type": [
        "Coaxial (Tubo en Tubo)",
        "Placas Soldadas (Brazed Plate)",
        "Casco y Serpentín",
        "Cuproníquel (Aguas Duras/Marinas)",
    ],

    # ROOFTOP
    "rooftop_capacity_unit": [
        "Ton",
        "BTU/h",
        "HP",
        "kW",
    ],
    "rooftop_heating_type": [
        "Bomba de Calor (Heat Pump)",
        "Quemador a Gas Natural/GLP",
        "Resistencias Eléctricas",
        "Sin Calefacción",
    ],
    "rooftop_refrigerant": [
        "R410A",
        "R32",
        "R407C",
        "R454B",
    ],

    # CHILLER
    "chiller_condenser_type": [
        "Enfriado por Aire (Air Cooled)",
        "Enfriado por Agua (Water Cooled)",
        "Condensador Evaporativo",
        "Condensador Remoto",
    ],
    "chiller_refrigerant": [
        "R134a",
        "R410A",
        "R32",
        "R1234ze (HFO Ecológico)",
        "R513A",
        "R407C",
        "Amoníaco (R717)",
    ],
    "chiller_compressor_type": [
        "Tornillo (Screw)",
        "Centrífugo",
        "Centrífugo Levitación Magnética (Turbocor)",
        "Scroll",
        "Reciprocante (Pistón)",
    ],
    "chiller_evaporator_type": [
        "Casco y Tubo (Shell & Tube)",
        "Placas Soldadas (Brazed Plate)",
        "Inundado (Flooded)",
        "Expansión Directa (DX)",
    ],

    # TORRE
    "tower_fill_type": [
        "Intercambiador de Láminas o Film (Abierta)",
        "Película PVC de Alta Eficiencia (Film)",
        "Serpentín Circuito Cerrado (Tubular)",
        "Híbrido (Serpentín + Relleno Laminar / Film)",
        "Salpicadura Anti-incrustante (Splash)",
        "Polipropileno para Aguas Sucias",
    ],
    "tower_fan_type": [
        "Axial Tiro Inducido",
        "Axial Tiro Forzado",
        "Centrífugo Bajo Ruido",
        "Accionamiento Directo EC",
    ],
    "tower_basin_makeup_type": [
        "Manual",
        "Válvula de Llenado por Flotador Mecánico",
        "Válvula Solenoide (Control de Nivel)",
        "Válvula Motorizada",
        "Control Electrónico por Sondas / Boyas de Nivel",
    ],
    "tower_drain_type": [
        "Manual (Válvula de Fondo)",
        "Automático",
        "Por Válvula Solenoide",
        "Por Válvula Motorizada",
        "Rebalse y Drenaje por Gravedad",
    ],
    "tower_blowdown_type": [
        "Sin Purga",
        "Purga Manual",
        "Por Solenoide",
        "Solenoide y Nivel TDS",
        "Solenoide y Conductividad",
        "Solenoide y Tiempo (Temporizada)",
        "Válvula Motorizada",
        "Purga Continua Regulada",
    ],

    # BOMBAS
    "pump_type": [
        "Centrífuga en Línea (In-Line)",
        "Centrífuga Aspiración Axial (End-Suction)",
        "Cámara Partida (Split-Case)",
        "Multietapa Vertical",
        "Sumergible",
        "Bombas Gemelas",
        "Bombas de Alta Presión",
    ],
    "pump_seal_type": [
        "Sello Mecánico Carbón / Carburo Silicio",
        "Sello Mecánico Carburo Tungsteno / Vitón",
        "Empaquetadura Prensaestopas",
    ],
    "refrigerant_unit": [
        "Kg",
        "g",
    ],

    # TRATAMIENTO DE AGUA
    "treatment_type": [
        "Inhibidor de Corrosión e Incrustación",
        "Biocida Oxidante (Cloro / Bromo)",
        "Biocida No Oxidante (Isotiazolinona)",
        "Dispersante de Lodos",
        "Filtración Multimedia / Arena",
        "Suavizador / Descalcificador por Resina",
        "Ósmosis Inversa",
    ],
    "treatment_dosing_system": [
        "Bomba Dosificadora Electromagnética",
        "Bomba Dosificadora Peristáltica",
        "Controlador Automático de Purga y Químico",
        "Dosificación por Pulso / Caudal",
        "Dosificación Manual",
    ],

    # VRV / VRF
    "vrf_type": [
        "Bomba de Calor (Heat Pump - 2 Tubos)",
        "Recuperación de Calor (Heat Recovery - 3 Tubos)",
        "Enfriado por Agua (Water Cooled VRF)",
    ],
    "vrf_refrigerant": [
        "R410A",
        "R32",
    ],
    "vrf_ui_type": [
        "Muro (Split Muro)",
        "Cassette 4 Vías",
        "Cassette 1 Vía / 2 Vías",
        "Cassette Circular 360°",
        "Ducto Baja Silueta",
        "Ducto Media / Alta Presión Estática",
        "Piso-Cielo",
        "Presentación Cielo",
        "Consola de Piso",
        "Columna / Gabinete Vertical",
        "Multi-posicional",
        "Modular",
    ],
    "vrf_hr_box_type": [
        "Caja HR Individual (1 Puerto)",
        "Caja HR Múltiple (Multi-Puerto)",
        "Caja BS / BC / MS (Selector de Ramal)",
        "Caja HR Principal (Main)",
        "Caja HR Secundaria (Sub)",
    ],

    # VENTILADOR
    "fan_function": [
        "Extracción",
        "Inyección",
        "Presurizador",
        "Inyección / Retorno",
    ],
    "fan_fan_type": [
        "Centrífugo Descubierto",
        "Centrífugo con Caja",
        "Axial con Caja",
        "Centrífugo Inclinado hacia Atrás",
        "Centrífugo Si-roco (Adelante)",
        "Axial Tubular",
        "Axial Mural",
        "Helicoidal",
        "Tipo Hongo para Techo / Extracción",
        "Caja de Ventilación Insonorizada",
    ],
    "fan_drive_type": [
        "Transmisión por Poleas y Correas",
        "Acoplamiento Directo al Eje",
        "Motor EC de Accionamiento Directo",
    ],
    "fan_bearing_type": [
        "Rodamientos Sellados",
        "Rodamientos Lubricados (Con Grasera)",
    ],
    "fan_starting_method": [
        "Alimentación Directa (DOL)",
        "Arranque Estrella-Triángulo (Delta-Estrella)",
        "Variador de Frecuencia (VDF)",
        "Partidor Suave (Soft Starter)",
    ],
    "fan_airflow_unit": [
        "CFM",
        "m3/h",
        "L/s",
        "m3/s",
    ],
    "fan_pressure_unit": [
        "Pa",
        "PSI",
        "Bar",
        "mmca",
        "inWG",
    ],
    "fan_power_unit": [
        "kW",
        "W",
        "HP",
        "CV",
    ],
    "water_flow_unit": [
        "m3/h",
        "GPM",
        "L/s",
        "L/min",
    ],
    "temperature_unit": [
        "°C",
        "°F",
        "K",
    ],
    "head_unit": [
        "m",
        "mca",
        "ft",
        "PSI",
        "Bar",
    ],
    "length_mm_unit": [
        "mm",
        "cm",
        "in",
    ],
    "length_m_unit": [
        "m",
        "ft",
    ],
    "volume_unit": [
        "L",
        "m3",
        "Gal",
    ],
    "electric_voltage_unit": [
        "V",
        "VAC",
        "VDC",
        "kV",
    ],
    "electric_current_unit": [
        "A",
        "mA",
    ],

    # GABINETE
    "cabinet_type": [
        "Tablero Fuerza y Control (TFC)",
        "Tablero de Fuerza (TF)",
        "Tablero de Control / DDC",
        "Gabinete de Variadores de Frecuencia (VFD)",
        "Gabinete BMS Central",
        "Tablero de Transferencia Automática (TTA)",
    ],

    # VARIADOR DE FRECUENCIA (VFD / VDF)
    "vfd_application": [
        "Ventilador de Inyección / Suministro",
        "Ventilador de Extracción / Retorno",
        "Ventilador Presurizador",
        "Manejadora de Aire (UMA / AHU)",
        "Bomba de Agua Helada (CHW)",
        "Bomba de Agua Condensación (CW)",
        "Bomba de Agua Caliente (HW)",
        "Ventilador de Torre de Enfriamiento",
        "Compresor",
    ],
    "vfd_voltage": [
        "380 - 480 VAC Trifásico",
        "200 - 240 VAC Trifásico",
        "220 VAC Monofásico",
        "500 - 690 VAC Trifásico",
    ],
    "vfd_enclosure_ip": [
        "IP20 / NEMA 1 (Montaje en Tablero)",
        "IP21 / NEMA 1 (Montaje Mural)",
        "IP54 / IP55 / NEMA 12 (Uso Interior / Polvo y Salpicaduras)",
        "IP66 / NEMA 4X (Intemperie / Exterior)",
    ],
    "vfd_control_mode": [
        "BMS",
        "Transductor Autónomo (Lazo PID Interno)",
        "Manual Local (Keypad / Potenciómetro)",
        "BMS / Manual Local (Selector)",
        "Controlador Externo / PLC / DDC",
        "Velocidad Fija / Multivelocidad",
    ],
    "vfd_transducer_type": [
        "Transductor de Temperatura",
        "Transductor de Presión",
        "Transductor de Presión Diferencial (Aire)",
        "Transductor de Presión Diferencial (Agua)",
        "Transductor de Caudal / Flujo",
        "Transductor de Humedad",
        "Transductor de Calidad de Aire (CO2 / CO)",
        "Sin Transductor",
    ],
    "vfd_sensor_type": [
        "PT100",
        "PT1000",
        "NTC",
        "PTC",
        "Termocupla",
        "Presostato",
        "Diferencial de Presión",
        "Presión de Baja",
        "Presión de Alta",
        "Flujo",
        "Caudal",
        "Humedad Relativa",
        "CO2 / Monóxido (CO)",
    ],
    "vfd_transducer_signal": [
        "0 a 10V",
        "2 a 10V",
        "4 a 20mA",
        "0 a 20mA",
        "0 a 5V",
        "Contacto Seco (ON/OFF)",
        "Pulsos / Frecuencia",
        "Comunicación Digital (RS485 / Modbus / BACnet)",
    ],

    # TERMO ELÉCTRICO DE AGUA
    "ewh_electrical_phase": [
        "Monofásico (220V)",
        "Trifásico (380V)",
        "Bifásico / Dual (220V / 380V)",
    ],
    "ewh_mounting_type": [
        "Mural Vertical",
        "Mural Horizontal",
        "De Piso / Pedestal Vertical",
        "Industrial Acumulador de Piso",
        "Bajo Lavamanos / Punto de Uso",
        "Multiposi-ción (Vertical / Horizontal)",
    ],
    "ewh_element_type": [
        "Resistencia Blindada Sumergida (Cobre / Inox)",
        "Resistencia Cerámica Envainada (Seca / Steatite)",
        "Banco de Resistencias Bridadas Industriales",
        "Resistencia Enroscada (1¼\" / 1½\" / 2\")",
    ],
    "ewh_anode_type": [
        "Ánodo de Magnesio",
        "Ánodo de Aluminio",
        "Ánodo Electrónico / Corriente Impresa (Titanio)",
        "Doble Ánodo de Magnesio",
        "Sin Ánodo (Cuba Inoxidable)",
    ],
    "ewh_anode_status": [
        "Óptimo / Nuevo",
        "En Buen Estado (< 50% desgaste)",
        "Desgaste Medio (Programar Cambio)",
        "Requiere Cambio Inmediato (> 75% desgaste)",
        "Reemplazado en Última Mantención",
        "Sin Revisión / Pendiente",
    ],
    "ewh_relief_valve_type": [
        "Válvula de Seguridad y Alivio de Presión (Estándar)",
        "Válvula Combinada Presión y Temperatura (P&T / T&P)",
        "Válvula de Alivio con Retención Incorporada",
        "Válvula de Seguridad Industrial Calibrada",
        "Sin Válvula de Alivio (Requiere Instalación)",
    ],
    "ewh_thermostat_type": [
        "Termostato Mecánico de Bulbo / Capilar con Rearme Térmico",
        "Termostato de Varilla Enchufable (RTS / Bipolar)",
        "Termostato Electrónico Digital con Sonda NTC/PT100",
        "Doble Termostato (Control + Límite de Seguridad Alta Temp.)",
    ],
}

# Metadata mapping each equipment system_type to its customizable dropdown lists
EQUIPMENT_DROPDOWN_MAP = {
    "AHU": [
        ("ahu_filter_type", "Tipo de Filtro", "filter_type"),
        ("ahu_refrigerant", "Refrigerante", "refrigerant"),
        ("refrigerant_unit", "Unidad Refrigerante", "refrigerant_unit"),
        ("ahu_fan_type", "Tipo de Ventilador", "fan_type"),
    ],
    "FANCOIL": [
        ("fancoil_pipe_config", "Configuración de Tubos", "pipe_config"),
        ("fancoil_valve_type", "Tipo de Válvula", "valve_type"),
        ("rooftop_capacity_unit", "Unidad de Capacidad / Potencia", "cooling_capacity_unit"),
        ("fan_airflow_unit", "Unidad de Caudal", "airflow_unit"),
        ("fancoil_motor_type", "Tipo de Motor", "motor_type"),
        ("fan_power_unit", "Unidad de Potencia Motor", "motor_power_unit"),
        ("split_drain_pump_type", "Tipo de Bomba de Condensado", "drain_pump_type"),
    ],
    "VAV": [
        ("vav_type", "Tipo VAV", "vav_type"),
        ("vav_heating_type", "Tipo de Calefacción", "reheat_type"),
        ("vav_protocol", "Protocolo de Control", "controller_protocol"),
    ],
    "SPLIT": [
        ("split_ui_type", "Tipo de Split UI (Presentación)", "split_ui_type"),
        ("split_refrigerant", "Refrigerante", "refrigerant"),
        ("refrigerant_unit", "Unidad Refrigerante", "refrigerant_unit"),
        ("rooftop_capacity_unit", "Unidad de Capacidad Frío", "cooling_capacity_unit"),
        ("split_compressor_type", "Tipo de Compresor", "compressor_type"),
        ("split_drain_pump_type", "Tipo de Bomba de Condensado", "drain_pump_type"),
    ],
    "WATER_COOLED_DUCT_COMPACT": [
        ("split_refrigerant", "Refrigerante", "refrigerant"),
        ("refrigerant_unit", "Unidad Refrigerante", "refrigerant_unit"),
        ("split_compressor_type", "Tipo de Compresor", "compressor_type"),
        ("wcdc_condenser_hx_type", "Tipo Intercambiador Condensador", "condenser_hx_type"),
        ("ahu_filter_type", "Tipo de Filtro", "filter_type"),
    ],
    "ROOFTOP": [
        ("rooftop_capacity_unit", "Unidad de Capacidad Frío", "cooling_capacity_unit"),
        ("rooftop_heating_type", "Tipo de Calefacción", "heating_type"),
        ("rooftop_refrigerant", "Refrigerante", "refrigerant"),
        ("refrigerant_unit", "Unidad Refrigerante", "refrigerant_unit"),
    ],
    "CHILLER": [
        ("chiller_condenser_type", "Tipo de Condensador", "condenser_type"),
        ("chiller_refrigerant", "Refrigerante", "refrigerant"),
        ("refrigerant_unit", "Unidad Refrigerante", "refrigerant_unit"),
        ("chiller_compressor_type", "Tipo de Compresor", "compressor_type"),
        ("chiller_evaporator_type", "Tipo de Evaporador", "evaporator_type"),
    ],
    "COOLING_TOWER": [
        ("tower_fill_type", "Tipo de Intercambiador de Calor", "fill_type"),
        ("tower_fan_type", "Tipo de Ventilador", "fan_type"),
        ("tower_basin_makeup_type", "Tipo de Llenado de Piscina", "basin_makeup_type"),
        ("tower_drain_type", "Tipo de Drenaje", "drain_type"),
        ("tower_blowdown_type", "Tipo de Purga", "blowdown_type"),
    ],
    "PUMP": [
        ("pump_type", "Tipo de Bomba", "pump_type"),
        ("pump_seal_type", "Tipo de Sello", "seal_type"),
    ],
    "WATER_TREATMENT": [
        ("treatment_type", "Tipo de Tratamiento", "treatment_type"),
        ("treatment_dosing_system", "Sistema de Dosificación", "dosing_system"),
    ],
    "VRF": [
        ("vrf_type", "Tipo de VRF", "vrf_system_type"),
        ("vrf_refrigerant", "Refrigerante", "refrigerant"),
        ("refrigerant_unit", "Unidad Refrigerante", "refrigerant_unit"),
    ],
    "VRF_INDOOR": [
        ("vrf_ui_type", "Tipo de Unidad Interior (Presentación)", "vrf_ui_type"),
        ("fancoil_motor_type", "Tipo de Motor Ventilador", "motor_type"),
        ("vrf_refrigerant", "Refrigerante", "refrigerant"),
    ],
    "VRF_HR_BOX": [
        ("vrf_hr_box_type", "Tipo de Caja HR / BS", "hr_box_type"),
    ],
    "FAN": [
        ("fan_function", "Función (Extracción/Inyección/Presurizador)", "fan_function"),
        ("fan_fan_type", "Tipo de Ventilador", "fan_type"),
        ("fan_airflow_unit", "Unidad de Caudal", "airflow_unit"),
        ("fan_pressure_unit", "Unidad de Presión Estática", "static_pressure_unit"),
        ("fan_power_unit", "Unidad de Potencia Motor", "motor_power_unit"),
        ("fan_drive_type", "Tipo de Transmisión", "drive_type"),
        ("fan_bearing_type", "Tipo de Rodamientos", "bearing_type"),
        ("fan_starting_method", "Tipo de Alimentación / Arranque", "starting_method"),
    ],
    "ELECTRICAL_CABINET": [
        ("cabinet_type", "Tipo de Gabinete", "cabinet_type"),
    ],
    "VFD": [
        ("vfd_application", "Aplicación / Equipo Controlado", "vfd_application"),
        ("fan_power_unit", "Unidad de Potencia", "motor_power_unit"),
        ("vfd_voltage", "Tensión / Alimentación", "voltage"),
        ("vfd_control_mode", "Modo de Control", "vfd_control_mode"),
        ("vav_protocol", "Protocolo de Comunicación", "control_protocol"),
        ("vfd_transducer_type", "Tipo de Transductor", "transducer_type"),
        ("vfd_sensor_type", "Tipo de Sensor", "sensor_type"),
        ("vfd_transducer_signal", "Señal de Transductor", "transducer_signal"),
        ("vfd_enclosure_ip", "Grado de Protección (IP / NEMA)", "enclosure_ip"),
    ],
    "ELECTRIC_WATER_HEATER": [
        ("ewh_electrical_phase", "Alimentación Eléctrica (Fases)", "electrical_phase"),
        ("ewh_mounting_type", "Tipo de Montaje / Instalación", "mounting_type"),
        ("volume_unit", "Unidad de Capacidad", "volume_unit"),
        ("fan_power_unit", "Unidad de Potencia", "heating_power_unit"),
        ("ewh_element_type", "Tipo de Resistencia Calefactora", "element_type"),
        ("ewh_anode_type", "Tipo de Ánodo de Sacrificio", "anode_type"),
        ("ewh_anode_status", "Estado / Cambio de Ánodo de Sacrificio", "anode_status"),
        ("ewh_relief_valve_type", "Válvula de Alivio y Sobrepresión", "relief_valve_type"),
        ("ewh_thermostat_type", "Tipo de Termostato", "thermostat_type"),
    ],
    "GENERAL": [
        ("bms_status", "Estado BMS / Control", "bms_status"),
    ],
}

EQUIPMENT_GROUP_NAMES = {
    "GENERAL": "Control & Automatización (BMS / DDC)",
    "AHU": "Manejadoras de Aire (AHU / UMA)",
    "FANCOIL": "Fan Coils (FCU)",
    "VAV": "Cajas de Volumen Variable (VAV)",
    "SPLIT": "Equipos Split / Multi-Split",
    "WATER_COOLED_DUCT_COMPACT": "Compacto de Ducto Condensado por Agua",
    "ROOFTOP": "Equipos Rooftop",
    "CHILLER": "Chillers (Enfriadores de Líquido)",
    "COOLING_TOWER": "Torres de Enfriamiento",
    "PUMP": "Bombas de Agua",
    "WATER_TREATMENT": "Tratamiento de Agua",
    "VRF": "Sistemas VRV / VRF (Unidad Exterior)",
    "VRF_INDOOR": "VRV / VRF Unidades Interiores",
    "VRF_HR_BOX": "Cajas HR / BS (Heat Recovery VRV/VRF)",
    "FAN": "Ventiladores / Extractores",
    "ELECTRICAL_CABINET": "Gabinetes / Tableros Eléctricos",
    "VFD": "Inversores / Variadores de Frecuencia (VDF)",
    "ELECTRIC_WATER_HEATER": "Termos Eléctricos de Agua",
}

class CustomListsService:
    """Service to persist and provide customizable dropdown lists."""

    def __init__(self, storage: JsonStorageEngine):
        self.storage = storage
        self._lists: Dict[str, List[str]] = {}
        self.load_lists()

    def load_lists(self):
        saved = self.storage.load("config/custom_lists.json", default=None)
        if isinstance(saved, dict):
            # Merge with default keys to ensure all lists exist
            self._lists = dict(DEFAULT_CUSTOM_LISTS)
            self._lists.update(saved)
            # Ensure newly added default pump types exist in existing saved lists
            if "pump_type" in self._lists:
                for pt in ["Bombas Gemelas", "Bombas de Alta Presión"]:
                    if pt not in self._lists["pump_type"]:
                        self._lists["pump_type"].append(pt)
            if "refrigerant_unit" not in self._lists:
                self._lists["refrigerant_unit"] = ["Kg", "g"]
            if "split_ui_type" not in self._lists:
                self._lists["split_ui_type"] = list(DEFAULT_CUSTOM_LISTS["split_ui_type"])
            if "vrf_ui_type" not in self._lists:
                self._lists["vrf_ui_type"] = list(DEFAULT_CUSTOM_LISTS["vrf_ui_type"])
            if "vrf_hr_box_type" not in self._lists:
                self._lists["vrf_hr_box_type"] = list(DEFAULT_CUSTOM_LISTS["vrf_hr_box_type"])
            if "fan_fan_type" in self._lists:
                for ft in reversed(["Centrífugo Descubierto", "Centrífugo con Caja", "Axial con Caja"]):
                    if ft not in self._lists["fan_fan_type"]:
                        self._lists["fan_fan_type"].insert(0, ft)
            if "tower_fill_type" in self._lists:
                for tft in [
                    "Intercambiador de Láminas o Film (Abierta)",
                    "Serpentín Circuito Cerrado (Tubular)",
                    "Híbrido (Serpentín + Relleno Laminar / Film)",
                ]:
                    if tft not in self._lists["tower_fill_type"]:
                        self._lists["tower_fill_type"].insert(0, tft)
            for fan_key in (
                "fan_function", "fan_bearing_type", "fan_starting_method",
                "fan_airflow_unit", "fan_pressure_unit", "fan_power_unit",
                "water_flow_unit", "temperature_unit", "head_unit",
                "length_mm_unit", "length_m_unit", "volume_unit",
                "electric_voltage_unit", "electric_current_unit",
                "rooftop_capacity_unit", "split_drain_pump_type",
                "tower_basin_makeup_type", "tower_drain_type", "tower_blowdown_type",
                "ewh_electrical_phase", "ewh_mounting_type", "ewh_element_type",
                "ewh_anode_type", "ewh_anode_status", "ewh_relief_valve_type", "ewh_thermostat_type",
                "vfd_application", "vfd_voltage", "vfd_enclosure_ip",
                "vfd_control_mode", "vfd_transducer_type", "vfd_sensor_type", "vfd_transducer_signal"
            ):
                if fan_key not in self._lists:
                    self._lists[fan_key] = list(DEFAULT_CUSTOM_LISTS[fan_key])
        else:
            self._lists = dict(DEFAULT_CUSTOM_LISTS)
            self.save_lists()

    def save_lists(self):
        try:
            self.storage.save("config/custom_lists.json", self._lists, backup=False)
        except Exception as e:
            print(f"Error saving custom lists: {e}")

    def get_list(self, key: str) -> List[str]:
        return list(self._lists.get(key, DEFAULT_CUSTOM_LISTS.get(key, [])))

    def set_list(self, key: str, items: List[str]):
        self._lists[key] = [str(x).strip() for x in items if str(x).strip()]
        self.save_lists()

    def add_item(self, key: str, item: str) -> bool:
        item = item.strip()
        if not item:
            return False
        if key not in self._lists:
            self._lists[key] = list(DEFAULT_CUSTOM_LISTS.get(key, []))
        if item not in self._lists[key]:
            self._lists[key].append(item)
            self.save_lists()
            return True
        return False

    def remove_item(self, key: str, item: str) -> bool:
        if key in self._lists and item in self._lists[key]:
            self._lists[key].remove(item)
            self.save_lists()
            return True
        return False

    def reset_list_to_default(self, key: str):
        if key in DEFAULT_CUSTOM_LISTS:
            self._lists[key] = list(DEFAULT_CUSTOM_LISTS[key])
            self.save_lists()

    def reset_all_to_defaults(self):
        self._lists = dict(DEFAULT_CUSTOM_LISTS)
        self.save_lists()
