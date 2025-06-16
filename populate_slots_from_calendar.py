import requests
from icalendar import Calendar
from datetime import datetime, timedelta, date as datetime_date, time as datetime_time
import pytz

from config import Config

# Configuration
CALENDAR_URL = Config.EXTERNAL_CALENDAR_URL
TARGET_TIMEZONE_STR = 'Europe/Paris'
TARGET_TIMEZONE = pytz.timezone(TARGET_TIMEZONE_STR)

# Imports spécifiques à l'application Flask
# S'assurer que ce script est au même niveau que le dossier 'app'
try:
    from app import create_app
    from app.utils import add_pickup_slot
except ImportError as e:
    print(f"Erreur d'importation des modules Flask: {e}")
    exit(1)

def log_message(message):
    """Affiche un message avec un horodatage UTC."""
    # Utilisation de TARGET_TIMEZONE pour l'affichage de l'heure du log
    print(f"[{datetime.now(TARGET_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')}] {message}")

def calculate_planning_period():
    """
    Calcule la période de planification : du lundi de la semaine S+1 au dimanche de la semaine S+2.
    S est la semaine de la date d'exécution.
    Retourne (start_date_period, end_date_period) comme objets date.
    """
    today = datetime.now(TARGET_TIMEZONE).date()
    
    # Calculer le lundi de la semaine actuelle (S)
    # weekday() retourne 0 pour lundi, ..., 6 pour dimanche
    current_week_monday = today - timedelta(days=today.weekday())
    
    # Lundi de la semaine S+1
    start_date_period = current_week_monday + timedelta(weeks=1)
    
    # Dimanche de la semaine S+2 (13 jours après le lundi de S+1, pour une période de 14 jours)
    end_date_period = start_date_period + timedelta(days=13)
    
    return start_date_period, end_date_period

def parse_datetime_from_ical(ical_dt_prop):
    """
    Convertit une propriété DTSTART ou DTEND d'icalendar en datetime localisé.
    ical_dt_prop: L'objet propriété (ex: event.get('dtstart')).
    Retourne un datetime conscient du fuseau horaire (TARGET_TIMEZONE) ou None si erreur.
    """
    if ical_dt_prop is None:
        return None
    
    dt_value = ical_dt_prop.dt
    
    try:
        if isinstance(dt_value, datetime_date) and not isinstance(dt_value, datetime):
            # C'est un événement sur toute la journée (objet date)
            # Interpréter comme minuit au début de cette journée dans TARGET_TIMEZONE
            naive_dt = datetime.combine(dt_value, datetime_time.min)
            return TARGET_TIMEZONE.localize(naive_dt)
        elif isinstance(dt_value, datetime):
            # C'est un objet datetime
            if dt_value.tzinfo is None or dt_value.tzinfo.utcoffset(dt_value) is None:
                # Datetime naïf, le localiser à TARGET_TIMEZONE
                return TARGET_TIMEZONE.localize(dt_value)
            else:
                # Datetime déjà conscient, le convertir à TARGET_TIMEZONE
                return dt_value.astimezone(TARGET_TIMEZONE)
        else:
            log_message(f"WARN: Type de date/heure non supporté: {type(dt_value)}")
            return None
    except Exception as e:
        log_message(f"WARN: Erreur lors du parsing de la date/heure iCal ({dt_value}): {e}")
        return None

def generate_slots_from_event(event_start_dt, event_end_dt, location_str):
    """
    Génère des créneaux de retrait potentiels basés sur un événement de calendrier.
    Les datetimes en argument doivent être localisés à TARGET_TIMEZONE.
    Retourne une liste de dictionnaires de créneaux.
    """
    slots = []
    duration = event_end_dt - event_start_dt

    # Règle 1: Milieu d'un cours de 2 heures
    # Tolérance pour la durée (ex: 1h50 à 2h10)
    min_duration_2h = timedelta(hours=1, minutes=50)
    max_duration_2h = timedelta(hours=2, minutes=10)
    if min_duration_2h <= duration <= max_duration_2h:
        middle_time = event_start_dt + duration / 2
        slots.append({
            'datetime': middle_time,
            'location': location_str,
            'rule': '2h_middle'
        })

    # Règle 2: Autour de chaque bloc de cours
    # Créneau 5 minutes avant le début
    before_slot_dt = event_start_dt - timedelta(minutes=5)
    slots.append({
        'datetime': before_slot_dt,
        'location': location_str,
        'rule': 'before_block'
    })

    # Créneau à la fin du bloc
    end_slot_dt = event_end_dt
    slots.append({
        'datetime': end_slot_dt,
        'location': location_str,
        'rule': 'end_block'
    })
    
    return slots

def main_script_logic():
    """Logique principale du script de peuplement des créneaux."""
    log_message("Début du script de peuplement des créneaux.")

    if not CALENDAR_URL:
        log_message("ERREUR: La variable d'environnement EXTERNAL_CALENDAR_URL n'est pas configurée.")
        return

    start_date_period, end_date_period = calculate_planning_period()
    log_message(f"Période de planification calculée : du {start_date_period.strftime('%Y-%m-%d')} au {end_date_period.strftime('%Y-%m-%d')}.")

    try:
        log_message(f"Téléchargement du calendrier depuis : {CALENDAR_URL}")
        response = requests.get(CALENDAR_URL, timeout=20)
        response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP
        calendar_content = response.text
    except requests.exceptions.RequestException as e:
        log_message(f"ERREUR: Impossible de télécharger le calendrier : {e}")
        return

    try:
        gcal = Calendar.from_ical(calendar_content)
    except ValueError as e:
        log_message(f"ERREUR: Impossible de parser le contenu du calendrier : {e}")
        return

    added_count = 0
    skipped_existing_count = 0
    skipped_error_count = 0
    processed_events = 0
    
    log_message("Début du traitement des événements du calendrier...")

    for component in gcal.walk('VEVENT'):
        summary = component.get('summary')
        dtstart_prop = component.get('dtstart')
        dtend_prop = component.get('dtend')
        location_prop = component.get('location')

        if not dtstart_prop or not dtend_prop or not location_prop:
            # log_message(f"INFO: Événement '{summary}' ignoré (dtstart, dtend ou location manquant).")
            continue

        event_start_dt = parse_datetime_from_ical(dtstart_prop)
        event_end_dt = parse_datetime_from_ical(dtend_prop)
        
        if not event_start_dt or not event_end_dt:
            log_message(f"WARN: Événement '{summary}' ignoré (erreur de parsing des dates).")
            continue
            
        event_location_str = str(location_prop)

        # Filtrer les événements par la période de planification
        # Un événement est pertinent si sa plage de dates chevauche la période de planification.
        event_starts_in_period_or_before = event_start_dt.date() <= end_date_period
        event_ends_in_period_or_after = event_end_dt.date() >= start_date_period
        
        if not (event_starts_in_period_or_before and event_ends_in_period_or_after):
            continue # L'événement ne chevauche pas la période de planification

        processed_events += 1
        # log_message(f"DEBUG: Traitement de l'événement: {summary} ({event_start_dt.strftime('%Y-%m-%d %H:%M')} - {event_end_dt.strftime('%Y-%m-%d %H:%M')}) à {event_location_str}")

        potential_slots = generate_slots_from_event(event_start_dt, event_end_dt, event_location_str)

        for slot_info in potential_slots:
            slot_dt = slot_info['datetime']
            slot_loc = slot_info['location']
            slot_rule = slot_info['rule']

            # Filtrer les créneaux générés pour s'assurer qu'ils tombent DANS la période de planification
            if not (start_date_period <= slot_dt.date() <= end_date_period):
                # log_message(f"DEBUG: Créneau généré ({slot_rule}) pour '{summary}' à {slot_dt.strftime('%Y-%m-%d %H:%M')} hors période, ignoré.")
                continue

            slot_date_str = slot_dt.strftime('%Y-%m-%d')
            slot_time_str = slot_dt.strftime('%H:%M')

            # add_pickup_slot attend date/heure en Europe/Paris, ce qui est déjà le cas pour slot_dt
            success, message = add_pickup_slot(slot_date_str, slot_time_str, slot_loc)

            if success:
                added_count += 1
                log_message(f"SUCCESS: Créneau ajouté: {slot_date_str} {slot_time_str} à '{slot_loc}' (Règle: {slot_rule}). Message: {message}")
            else:
                if "existe déjà" in message:
                    skipped_existing_count += 1
                    # log_message(f"INFO: Créneau existant ignoré: {slot_date_str} {slot_time_str} à '{slot_loc}'. Message: {message}")
                else:
                    skipped_error_count += 1
                    log_message(f"ERREUR lors de l'ajout du créneau: {slot_date_str} {slot_time_str} à '{slot_loc}' (Règle: {slot_rule}). Message: {message}")
    
    log_message("-" * 50)
    log_message("Résumé du traitement :")
    log_message(f"  Événements du calendrier pertinents traités : {processed_events}")
    log_message(f"  Nouveaux créneaux ajoutés                 : {added_count}")
    log_message(f"  Créneaux existants ignorés              : {skipped_existing_count}")
    log_message(f"  Erreurs lors de l'ajout de créneaux     : {skipped_error_count}")
    log_message("Fin du script de peuplement des créneaux.")
    log_message("-" * 50)

if __name__ == '__main__':
    flask_app = create_app()
    with flask_app.app_context():
        main_script_logic()
