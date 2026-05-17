# seed.py
from src.database import SessionLocal, engine, Base
from src.db_models import DBCarrierService, DBRateCard

def seed_database():
    print("Connecting to database and creating tables if missing...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        if db.query(DBCarrierService).first() is not None:
            print("Database already contains data. Skipping seeding.")
            return

        print("Seeding multi-carrier services...")
        # FIXED: Removed explicit primary key IDs to let PostgreSQL sequences auto-increment safely
        dhl_std = DBCarrierService(carrier_name='DHL', service_name='Standard Paket', max_weight_kg=31.50)
        dhl_exp = DBCarrierService(carrier_name='DHL', service_name='Express Kurier', max_weight_kg=31.50)
        dpd_cls = DBCarrierService(carrier_name='DPD', service_name='Classic Service', max_weight_kg=20.00)
        
        db.add_all([dhl_std, dhl_exp, dpd_cls])
        
        # We flush to state changes into the transaction buffer so Python can resolve relationship anchors
        db.flush()

        print("Seeding rate cards...")
        # FIXED: Instead of hardcoding guessed service_id foreign keys, 
        # we assign the parent object instance directly to the ORM relationship attribute.
        rates = [
            DBRateCard(service=dhl_std, postal_code_prefix='10', weight_break_kg=2.00, base_cost=4.95),
            DBRateCard(service=dhl_std, postal_code_prefix='10', weight_break_kg=5.00, base_cost=6.95),
            DBRateCard(service=dhl_exp, postal_code_prefix='10', weight_break_kg=2.00, base_cost=12.50),
            DBRateCard(service=dpd_cls, postal_code_prefix='10', weight_break_kg=2.00, base_cost=4.20),
            DBRateCard(service=dpd_cls, postal_code_prefix='10', weight_break_kg=5.00, base_cost=7.10)
        ]
        
        db.add_all(rates)
        db.commit()
        print("Database seeded successfully with production base records!")
        
    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()