from __future__ import annotations
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

@dataclass
class Tool:
    id: str
    name: str
    brand: str
    model: str
    serial_number: str
    category: str
    status: str = "AVAILABLE"
    location: str = ""
    assigned_to: str = ""
    purchase_date: str = ""
    calibration_date: str = ""
    next_calibration: str = ""
    calibration_interval_days: int = 365
    notes: str = ""
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

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Tool:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass
class SparePart:
    id: str
    name: str
    part_number: str
    category: str
    description: str = ""
    quantity: int = 0
    minimum_quantity: int = 0
    unit: str = "unidad"
    location: str = ""
    supplier: str = ""
    unit_cost: float = 0.0
    currency: str = "CLP"
    compatible_equipment: list = field(default_factory=list)
    notes: str = ""
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
    def manufacturer(self) -> str:
        return self.supplier

    @property
    def code(self) -> str:
        return self.part_number

    @property
    def current_stock(self) -> int:
        return self.quantity

    @property
    def minimum_stock(self) -> int:
        return self.minimum_quantity

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> SparePart:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

@dataclass 
class InventoryMovement:
    id: str = ""
    part_id: str = ""
    part_name: str = ""
    movement_type: str = "IN"
    quantity: int = 0
    reason: str = ""
    work_order_id: str = ""
    reference: str = ""
    equipment_id: str = ""
    equipment_tag: str = ""
    destination: str = ""
    performed_by: str = ""
    date: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    type: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.type and not self.movement_type:
            self.movement_type = self.type
        elif not self.type and self.movement_type:
            self.type = self.movement_type
        if not self.part_name and self.part_id:
            pass
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
        if not self.date:
            self.date = now

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> InventoryMovement:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class PanolSupply:
    """Insumo de Pañol (Detergente, Paños de limpieza, terminales de manguera, etc.)."""
    id: str = ""
    name: str = ""
    code: str = ""
    category: str = "Limpieza y Químicos"
    unit: str = "unidad"
    quantity: int = 0
    minimum_quantity: int = 0
    location: str = "Pañol"
    supplier: str = ""
    unit_cost: float = 0.0
    currency: str = "CLP"
    notes: str = ""
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

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> PanolSupply:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class EppItem:
    """Elemento de Protección Personal (EPP) en Pañol.
    Soporta:
      - epp_type = 'DELIVERY' (Entrega directa/consumible: Guantes, lentes, ropa, calzado, casco, bloqueador solar, etc.)
      - epp_type = 'ASSIGNMENT' (Por asignación/cargo retornable: Arnés de seguridad, líneas de vida, carro y estrobos, polainas y coletos, etc.)
    """
    id: str = ""
    name: str = ""
    code: str = ""
    epp_type: str = "DELIVERY"  # "DELIVERY" o "ASSIGNMENT"
    category: str = "General"
    brand: str = ""
    size_or_model: str = ""
    serial_number: str = ""
    quantity: int = 0
    minimum_quantity: int = 0
    unit: str = "unidad"
    status: str = "AVAILABLE"  # Para ASSIGNMENT: AVAILABLE, ASSIGNED, IN_INSPECTION, OUT_OF_SERVICE
    assigned_to: str = ""      # Nombre de técnico / personal externo / recinto
    assigned_type: str = ""    # "TECHNICIAN", "EXTERNAL", "SITE"
    assigned_date: str = ""
    expiration_date: str = ""  # Fecha vencimiento o próxima inspección
    location: str = "Pañol"
    notes: str = ""
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

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> EppItem:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class PanolMovement:
    """Registro de movimiento en Pañol (Ingreso, Entrega, Asignación o Devolución de Insumos, EPP y Herramientas)."""
    id: str = ""
    item_id: str = ""
    item_name: str = ""
    item_code: str = ""
    item_category: str = "SUPPLY"  # "SUPPLY", "EPP_DELIVERY", "EPP_ASSIGNMENT", "TOOL"
    movement_type: str = "IN"      # "IN", "OUT", "ASSIGN", "RETURN"
    quantity: int = 1
    unit: str = "unidad"
    recipient_type: str = ""       # "TECHNICIAN", "EXTERNAL", "SITE", ""
    recipient_name: str = ""       # Nombre del técnico, personal externo o recinto
    reason: str = ""
    reference: str = ""
    performed_by: str = "Pañolero / Usuario"
    date: str = ""
    notes: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.date:
            self.date = now

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> PanolMovement:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class GasCylinder:
    """Cilindro / Bombona de Gas en Pañol.
    Soporta:
      - gas_category = 'WELDING': Gases combustibles / técnicos para soldadura y presurización
        (Oxígeno, Nitrógeno, Gas Propano, Gas Butano, Gas MAPP, Argón, Acetileno, etc.) manejados en m³ o Kg.
      - gas_category = 'REFRIGERANT': Cilindros (Bombonas) de gases refrigerantes vírgenes
        (R-410A, R-32, R-134a, R-407C, R-22, R-454B, R-507, R-404A, etc.) en Kg.
      - gas_category = 'RECOVERED': Cilindros de almacenamiento de gas refrigerante recuperado en Kg.
      - gas_category = 'CLEANING': Cilindros de agente de limpieza de circuitos frigoríficos (R-141b, etc.) en Kg.
    """
    id: str = ""
    code: str = ""                  # N° de cilindro / serie / código identificatorio (Ej: CIL-R410-01, TUBO-OXI-02)
    gas_category: str = "REFRIGERANT"  # "WELDING", "REFRIGERANT", "RECOVERED", "CLEANING"
    gas_type: str = ""              # Ej: "R-410A", "Oxígeno", "Nitrógeno", "Gas Propano", "R-141b", etc.
    unit: str = "Kg"                # "Kg" o "m³"
    initial_amount: float = 11.3    # Contenido neto inicial / capacidad (Ej: 11.3 Kg, 10 m³)
    current_amount: float = 11.3    # Contenido restante actual en el cilindro (Kg o m³)
    tare_weight_kg: float = 0.0     # Peso tara del cilindro vacío (opcional)
    status: str = "AVAILABLE"       # "AVAILABLE" (En Pañol), "IN_USE" (En Terreno), "EMPTY" (Vacío), "RETURNED" (Devuelto a proveedor)
    assigned_to: str = ""           # Técnico o recinto si está en terreno
    location: str = "Pañol - Jaula de Gases"
    supplier: str = ""
    notes: str = ""
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
    def used_amount(self) -> float:
        if self.gas_category == "RECOVERED":
            return self.current_amount
        return max(0.0, round(self.initial_amount - self.current_amount, 3))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> GasCylinder:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class GasUsageRecord:
    """Registro de consumo, carga, recarga o recuperación de gas desde/hacia un cilindro."""
    id: str = ""
    cylinder_id: str = ""
    cylinder_code: str = ""
    gas_category: str = "REFRIGERANT"  # "WELDING", "REFRIGERANT", "RECOVERED", "CLEANING"
    gas_type: str = ""
    movement_type: str = "OUT"         # "IN" (Ingreso/Recarga/Recuperación hacia cilindro), "OUT" (Uso/Carga en equipo/Soldadura)
    amount: float = 0.0                # Cantidad usada o ingresada (Kg o m³)
    unit: str = "Kg"                   # "Kg" o "m³"
    remaining_after: float = 0.0       # Saldo restante en el cilindro tras el movimiento
    equipment_id: str = ""             # ID del equipo intervenido (si aplica)
    equipment_tag: str = ""            # Tag del equipo donde se cargó/usó o desde donde se recuperó el gas
    recipient_type: str = "TECHNICIAN" # "TECHNICIAN", "EXTERNAL", "SITE"
    recipient_name: str = ""           # Técnico o responsable
    work_order_ref: str = ""           # N° OT o guía asociada
    reason: str = ""                   # Ej: "Carga de refrigerante", "Soldadura de tubería", "Barrido con R-141b", "Recuperación de gas"
    date: str = ""
    notes: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.date:
            self.date = now

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> GasUsageRecord:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


