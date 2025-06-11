import os
from datetime import datetime, timedelta, time
import pytz

from app import create_app, db
from app.models import PickupSlot

def create_daily_pickup_slots(days_to_create=30):
    """
    Crée des créneaux de retrait quotidiens à 12h00 à Paris pour un nombre de jours donné.
    Évite de créer des doublons.
    """
    app = create_app()
    with app.app_context():
        paris_tz = pytz.timezone('Europe/Paris')
        start_date = datetime.now(paris_tz).date()
        
        slots_created_count = 0
        slots_skipped_count = 0

        for i in range(days_to_create):
            current_date = start_date + timedelta(days=i)
            # Créneau à 12h00
            slot_datetime_naive = datetime.combine(current_date, time(12, 0))
            slot_datetime_paris = paris_tz.localize(slot_datetime_naive)
         
            existing_slot = PickupSlot.query.filter_by(
                slot_datetime=slot_datetime_paris,
                location="Paris"
            ).first()
            
            if not existing_slot:
                new_slot = PickupSlot(
                    slot_datetime=slot_datetime_paris,
                    location="Paris",
                    is_available=True
                )
                db.session.add(new_slot)
                slots_created_count += 1
            else:
                slots_skipped_count += 1
        
        if slots_created_count > 0:
            try:
                db.session.commit()
                print(f"{slots_created_count} nouveaux créneaux de retrait créés.")
            except Exception as e:
                db.session.rollback()
                print(f"Erreur lors de la création des créneaux : {str(e)}")
        
        if slots_skipped_count > 0:
            print(f"{slots_skipped_count} créneaux existants ont été ignorés.")
        
        if slots_created_count == 0 and slots_skipped_count == 0:
            print("Aucun créneau à créer ou à ignorer.")

if __name__ == '__main__':
    print("Création des créneaux de retrait de test...")
    create_daily_pickup_slots()
    print("Terminé.")
