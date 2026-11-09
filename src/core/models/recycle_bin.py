from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import uuid

@dataclass
class RecycledItem:
    id: str
    original_id: str
    item_type: str  # "CLIENT", "SITE", "EQUIPMENT", "WORK_ORDER", "TOOL", "SPARE_PART"
    display_name: str
    deleted_at: str
    payload: dict
    extra_info: dict

    @classmethod
    def create(cls, original_id: str, item_type: str, display_name: str, payload: dict, extra_info: dict = None):
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            id=str(uuid.uuid4()),
            original_id=original_id,
            item_type=item_type,
            display_name=display_name,
            deleted_at=now,
            payload=payload,
            extra_info=extra_info or {}
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'RecycledItem':
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
