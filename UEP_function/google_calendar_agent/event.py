import re
from datetime import datetime, timedelta
from tzlocal import get_localzone
from google_calendar_agent.color import color_options 

def create_new_event(service):
    start_date = input("Enter start date (YYYY-MM-DD): ")
    start_time = input("Enter start time (HH:MM) or type 'all day': ")
    end_date = input("Enter end date (YYYY-MM-DD):")
    end_time = input("Enter end time (HH:MM) or type 'all day': ")
    title = input("Enter event title: ")
    reminder_time = int(input("Set number of reminders?(enter 0 is no reminder)"))
    overrides = []
    i = 0

    if start_time != "all day":
        event_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    else:
        event_datetime = datetime.strptime(f"{start_date} 00:00", "%Y-%m-%d %H:%M")

    while i < reminder_time:
        rem_inform = input(f"set reminder {i+1} : (e.g., '2 day', '1 hour') or 'cancel' to stop: ")
        if rem_inform =="cancel":
            break
        minutes = calculate_reminder_time(rem_inform)

        if minutes is None :
            print("Invalid format! Please try again.")
            continue  

        reminder_datetime = event_datetime - timedelta(minutes=minutes)
        if reminder_datetime < datetime.now():
            print("Reminder time is before the current time! Please enter a valid reminder.")
            continue
        overrides.append({'method': 'popup', 'minutes': minutes})
        i += 1
    description = input("Enter event description (optional): ")
    location = input("Enter event location (optional): ")

    print("Available colors:")
    for cid, name in color_options.items():
        print(f"{cid}: {name}")
    color = input("Enter event color_id or press enter(optional): ")
    local_tz = get_localzone()

    if start_time.lower() != 'all day':
        start = {'dateTime': f"{start_date}T{start_time}:00", 'timeZone': local_tz}
        end = {'dateTime': f"{end_date}T{end_time}:00", 'timeZone': local_tz}  # 可自行調整結束時間
    else:
        start = {'date': start_date}
        end = {'date': start_date}

    event = {
        'summary': title,
        'location' : location,
        'description': description,
        'start' : start,
        'end': end,  
        'reminders':{
            'userDefault':True,
            'override':overrides
        }if overrides else {'useDefault': True},
        'color_id' : color,
    }
    service.events().insert(calendarId='primary', body=event).execute()

def calculate_reminder_time(rem):
    num = re.findall(r'\d+', rem)
    unit = re.findall(r'[a-zA-Z]+', rem)

    if not num or not unit:
        return None
    unit = unit[0].lower()

    try:
        n = int(num[0])
    except ValueError:
        return None

    if unit == "week":
        return n*7*24*60
    elif unit == "day":
        return n*24*60
    elif unit == "hour":
        return n*60
    elif unit[0] == "minute":
        return n
    else:
        print("illegal unit")
        return None

def delete_event(service, keyword):
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    if not events:
        print('No upcoming events found.')
        return
    matched_events = [event for event in events if keyword.lower() in event.get('summary', '').lower()]
    if not matched_events:
        print(f'No events found with keyword: {keyword}')
        return
    print("Matched Events:")
    for i, event in enumerate(matched_events):
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"{i + 1}: {event['summary']} (Start: {start})")
    choice = int(input("Enter the number of the event to delete (0 to cancel): "))
    if choice == 0:
        print("Deletion cancelled.")
        return
    if 1 <= choice <= len(matched_events):
        event_to_delete = matched_events[choice - 1]
        service.events().delete(calendarId='primary', eventId=event_to_delete['id']).execute()
        print(f"Event '{event_to_delete['summary']}' deleted.")
    else:
        print("Invalid choice.")
