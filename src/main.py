from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="LogiKur Routing API")

# 🌐 ALLOW CROSS-ORIGIN BACKEND TRAFFIC
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

class OrderPayload(BaseModel):
    order_id: str
    weight_kg: float = Field(..., gt=0, description="Weight must be greater than zero.")
    postal_code: str = Field(..., min_length=2, description="Postal code must contain at least a zone prefix.")
    requested_sla: str

@app.post("/api/v1/route", status_code=status.HTTP_200_OK)
async def route_order(payload: OrderPayload):
    w = payload.weight_kg
    
    # Standardize SLA format to handle case insensitivity issues and typos safely
    sla = payload.requested_sla.strip().capitalize()
    if sla not in ["Standard", "Express"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid requested_sla '{payload.requested_sla}'. Supported options are 'Standard' or 'Express'."
        )

    # 1. ULTRA-LIGHT TIER (0 - 2kg)
    if w <= 2.0:
        carrier = "Deutsche Post" if sla == "Standard" else "DHL Express"
        service = "Warenpost Brief" if sla == "Standard" else "Express Document"
        base_cost = 2.95 if sla == "Standard" else 14.50

    # 2. STANDARD PARCEL TIER (2kg - 31.5kg)
    elif w <= 31.5:
        if sla == "Express":
            carrier = "UPS"
            service = "Express Saver"
            base_cost = 18.50 + (w * 0.40)
        else:
            # FIXED: Evaluates the last digit char string safely to avoid ValueError crashes on non-numeric or leading-zero prefixes
            last_digit = payload.postal_code.strip()[-1]
            is_even = ord(last_digit) % 2 == 0 if last_digit.isdigit() else len(payload.postal_code) % 2 == 0
            
            carrier = "DHL Paket" if is_even else "DPD Ground"
            service = "Standard Domestic"
            base_cost = 5.90 + (w * 0.15)

    # 3. HEAVY COURIER TIER (31.5kg - 70kg)
    elif w <= 70.0:
        carrier = "DHL Express" if sla == "Express" else "GLS Heavy"
        service = "Medical/Industrial Priority" if sla == "Express" else "Oversized Parcel"
        base_cost = 35.00 + (w * 0.80) if sla == "Express" else 19.90 + (w * 0.50)

    # 4. FREIGHT PALLET TIER (Above 70kg)
    else:
        carrier = "DHL Freight" if sla == "Express" else "DB Schenker"
        service = "Premium Cargo LTL" if sla == "Express" else "Economy Pallet Network"
        base_cost = 75.00 + (w * 1.20) if sla == "Express" else 45.00 + (w * 0.75)

    return {
        "assigned_carrier": carrier,
        "assigned_service": service,
        "calculated_cost": round(base_cost, 2),
        "telemetry": {
            "processed_weight": w,
            "routing_zone": f"DE-{payload.postal_code.strip()[:2]}"
        }
    }