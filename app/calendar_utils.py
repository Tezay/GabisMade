import calendar
from datetime import datetime, date

def generate_calendar_data(year, month, available_slots):
    """
    Génère les données pour afficher un calendrier mensuel.
    available_slots: une liste d'objets PickupSlot.
    Retourne un dictionnaire avec 'month_name', 'year', 'prev_month', 'next_month', 'weeks'.
    'weeks' est une liste de listes, où chaque sous-liste est une semaine,
    et chaque élément de la semaine est un dictionnaire {'day': num, 'is_today': bool, 'has_slots': bool, 'slots_for_day': list}.
    """
    cal = calendar.Calendar()
    month_days = cal.monthdatescalendar(year, month) # Donne des objets date complets

    month_name = date(year, month, 1).strftime("%B")
    
    # Calculer le mois précédent et suivant
    if month == 1:
        prev_month_val = 12
        prev_year_val = year - 1
    else:
        prev_month_val = month - 1
        prev_year_val = year

    if month == 12:
        next_month_val = 1
        next_year_val = year + 1
    else:
        next_month_val = month + 1
        next_year_val = year

    prev_month_url_params = f"?year={prev_year_val}&month={prev_month_val}"
    next_month_url_params = f"?year={next_year_val}&month={next_month_val}"

    # Organiser les créneaux par jour
    slots_by_date = {}
    for slot in available_slots:
        slot_date = slot.slot_datetime.date()
        if slot_date not in slots_by_date:
            slots_by_date[slot_date] = []
        slots_by_date[slot_date].append({
            'id': slot.id,
            'time': slot.slot_datetime.strftime("%H:%M"),
            'location': slot.location
        })

    weeks_data = []
    today = datetime.now().date()

    for week in month_days:
        week_data = []
        for day_date_obj in week: # day_date_obj est un objet datetime.date
            day_num = day_date_obj.day
            is_current_month = day_date_obj.month == month
            
            slots_for_this_day = []
            has_available_slots = False
            if is_current_month and day_date_obj >= today : # Vérifier si le jour est dans le futur ou aujourd'hui
                slots_for_this_day = slots_by_date.get(day_date_obj, [])
                if slots_for_this_day:
                    has_available_slots = True
            
            week_data.append({
                'day': day_num,
                'date_obj': day_date_obj, # Objet date complet
                'is_current_month': is_current_month,
                'is_today': day_date_obj == today,
                'has_slots': has_available_slots,
                'slots_for_day': slots_for_this_day,
                'is_past': day_date_obj < today and is_current_month
            })
        weeks_data.append(week_data)

    return {
        'month_name': month_name,
        'year': year,
        'prev_month_params': prev_month_url_params,
        'next_month_params': next_month_url_params,
        'weeks': weeks_data
    }
