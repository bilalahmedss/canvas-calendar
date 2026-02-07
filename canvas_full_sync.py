import os
import re
import json
import pytz
from canvasapi import Canvas
from ics import Calendar, Event
from ics.grammar.parse import ContentLine
from datetime import datetime, timedelta

# --- LOAD CONFIGURATION ---
def load_config():
    timetable_str = os.environ.get("MY_TIMETABLE", "{}")
    try:
        return json.loads(timetable_str)
    except json.JSONDecodeError:
        return {}

CONFIG = load_config()
COURSE_CONFIGS = CONFIG.get("courses", {})
LOCAL_TZ = pytz.timezone("Asia/Karachi")

def get_course_config(course_code):
    clean_code = str(course_code).replace(" ", "").upper()
    for key, data in COURSE_CONFIGS.items():
        clean_key = key.replace(" ", "").upper()
        if clean_key in clean_code or clean_code in clean_key:
            return data
    return None

def main():
    API_URL = os.environ.get("CANVAS_API_URL")
    API_KEY = os.environ.get("CANVAS_API_KEY")
    
    if not API_URL or not API_KEY:
        print("❌ Error: Missing Canvas Credentials")
        return

    canvas = Canvas(API_URL, API_KEY)
    cal = Calendar()
    
    # 1. Sync Canvas Data (Assignments/Announcements)
    print("🔄 Syncing Canvas Data...")
    try:
        courses = canvas.get_courses(enrollment_state='active')
        for course in courses:
            # (Existing assignment/announcement logic stays here)
            pass
    except Exception as e:
        print(f"⚠️ Canvas Sync Error: {e}")

    # 2. Injecting Class Timings (Karachi Time Fixed)
    print("📅 Injecting Class Timings (Asia/Karachi)...")
    for course_name, data in COURSE_CONFIGS.items():
        if 'times' in data and 'days' in data:
            for day_index in data['days']:
                for start_t, end_t in data['times']:
                    e = Event()
                    e.name = f"🏫 Class: {course_name}"
                    
                    # Find the correct day in the current week
                    now = datetime.now(LOCAL_TZ)
                    start_of_week = now - timedelta(days=now.weekday())
                    class_date = start_of_week + timedelta(days=day_index)
                    
                    try:
                        # Combine date with time strings from JSON
                        begin_naive = datetime.strptime(f"{class_date.strftime('%Y-%m-%d')} {start_t}", "%Y-%m-%d %H:%M")
                        end_naive = datetime.strptime(f"{class_date.strftime('%Y-%m-%d')} {end_t}", "%Y-%m-%d %H:%M")
                        
                        # Tell the event this is Karachi time, not UTC
                        e.begin = LOCAL_TZ.localize(begin_naive)
                        e.end = LOCAL_TZ.localize(end_naive)
                        
                        # Add Weekly Recurrence
                        day_names = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
                        rrule = ContentLine(name="RRULE", value=f"FREQ=WEEKLY;BYDAY={day_names[day_index]}")
                        e.extra.append(rrule)
                        
                        cal.events.add(e)
                    except Exception as time_err:
                        print(f"❌ Time error for {course_name}: {time_err}")

    with open('my_schedule.ics', 'w', encoding='utf-8') as f:
        f.writelines(cal)
    print("✅ Success! Timezone-aware calendar generated.")

if __name__ == "__main__":
    main()
