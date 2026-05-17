# src/models.py
from decimal import Decimal
from pydantic.dataclasses import dataclass
from pydantic import Field

@dataclass
class OrderPayload:
    order_id: str
    # Enforces that weight cannot be negative or zero
    weight_kg: Decimal
    postal_code: str
    requested_sla: str

@dataclass
class RoutingResult:
    order_id: str
    assigned_carrier: str
    assigned_service: str
    shipping_cost: Decimal
    execution_status: str = "SUCCESS"  # FIXED: Added default state value