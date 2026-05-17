# src/db_models.py
from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.database import Base

class DBCarrierService(Base):
    __tablename__ = "carrier_services"

    service_id = Column(Integer, primary_key=True, index=True)
    carrier_name = Column(String(50), nullable=False)
    service_name = Column(String(100), nullable=False)
    # Changed to Numeric to maintain strict decimal precision for package weight calculations
    max_weight_kg = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationship to cleanly pull all linked rate rules back if needed
    rates = relationship("DBRateCard", back_populates="service", cascade="all, delete-orphan")


class DBRateCard(Base):
    __tablename__ = "rate_cards"

    rate_id = Column(Integer, primary_key=True, index=True)
    postal_code_prefix = Column(String(10), nullable=False, index=True)
    # Precise logistics metrics configurations
    weight_break_kg = Column(Numeric(10, 2), nullable=False)
    base_cost = Column(Numeric(10, 2), nullable=False)
    
    # Foreign Key constraint specified correctly to reference parent primary key
    service_id = Column(
        Integer, 
        ForeignKey("carrier_services.service_id", ondelete="CASCADE"), 
        nullable=False
    )

    # Establishes clean dot-notation lookup (e.g., rate_card.service.carrier_name)
    service = relationship("DBCarrierService", back_populates="rates")