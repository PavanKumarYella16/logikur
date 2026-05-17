# src/engine.py
from sqlalchemy.orm import Session
from src.db_models import DBCarrierService, DBRateCard

class LogiKurEngine:
    def __init__(self, db: Session):
        self.db = db
        # Define our fulfillment center origin (e.g., Berlin prefix '10')
        self.WAREHOUSE_PREFIX = 10 

    def calculate_best_route(self, weight: float, postal_code: str, sla: str) -> dict:
        # Extract the first two digits of the destination postal code as an integer
        try:
            dest_prefix = int(postal_code[:2])
        except (ValueError, TypeError):
            dest_prefix = 10 # Fallback to local zone if invalid string passed

        # DYNAMIC DISTANCE CALCULATION:
        zone_distance = abs(self.WAREHOUSE_PREFIX - dest_prefix)
        
        # Surcharge rule: Add €0.40 for every zone unit away from the warehouse
        distance_surcharge = zone_distance * 0.40

        # 1. Fetch active carrier services matching weight limits
        # Cast model values to float if needed or evaluate numeric thresholds safely
        services = self.db.query(DBCarrierService).filter(
            DBCarrierService.max_weight_kg >= weight,
            DBCarrierService.is_active == True
        ).all()

        if not services:
            raise ValueError(f"Package weight ({weight}kg) exceeds physical limits of our carrier networks.")

        best_route = None
        cheapest_cost = float('inf')

        # 2. Evaluate carriers and inject real-time distance pricing
        for service in services:
            is_express_service = "Express" in service.service_name
            if sla == "Express" and not is_express_service:
                continue
            if sla == "Standard" and is_express_service:
                continue

            # FIXED: Order by weight_break_kg ascending to match the tightest fitting bracket first, 
            # rather than matching a larger bracket arbitrarily.
            rate_card = self.db.query(DBRateCard).filter(
                DBRateCard.service_id == service.service_id,
                DBRateCard.postal_code_prefix == "10",  # Base contract anchor
                DBRateCard.weight_break_kg >= weight
            ).order_by(DBRateCard.weight_break_kg.asc()).first()

            # Fallback to top-tier weight card if heavy package exceeds explicit brackets
            if not rate_card:
                rate_card = self.db.query(DBRateCard).filter(
                    DBRateCard.service_id == service.service_id,
                    DBRateCard.postal_code_prefix == "10"
                ).order_by(DBRateCard.weight_break_kg.desc()).first()

            if rate_card:
                # FIXED: Force conversions to float to prevent TypeError when dealing with Decimal types from Numeric columns
                base_price = float(rate_card.base_cost)
                rate_weight_break = float(rate_card.weight_break_kg)
                
                # If package exceeds the contract weight bracket, apply a weight penalty
                if weight > rate_weight_break:
                    extra_weight = weight - rate_weight_break
                    base_price += extra_weight * 1.50

                # DYNAMIC REAL-TIME PRICE COMPOSITION:
                final_calculated_cost = base_price + distance_surcharge

                if final_calculated_cost < cheapest_cost:
                    cheapest_cost = final_calculated_cost
                    best_route = {
                        "carrier": service.carrier_name,
                        "service": service.service_name,
                        "cost": round(final_calculated_cost, 2),
                        "distance_zones": zone_distance,
                        "surcharge": round(distance_surcharge, 2)
                    }

        if not best_route:
            raise ValueError(f"No delivery paths could be dynamically mapped for SLA '{sla}' and destination '{postal_code}'.")

        return best_route