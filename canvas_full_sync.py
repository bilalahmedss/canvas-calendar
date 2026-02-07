import os
import re
import json
from canvasapi import Canvas
from ics import Calendar, Event
from ics.grammar.parse import ContentLine  # Critical for the fix
from datetime import datetime, timedelta
import pytz
# --- LOAD CONFIGURATION ---
def load_config():
    timetable_str = os.environ.get("MY_TIMETABLE", "{}")
    try:
        return json.loads(timetable_str)
    except json.JSONDecodeError:
        print("⚠️ Warning: MY_TIMETABLE secret is not valid JSON")
        return {}

CONFIG = load_config()
COURSE_CONFIGS = CONFIG.get("courses", {})

def get_course_config(course_name):
    for key, data in COURSE_CONFIGS.items():
        clean_key = key.replace(" ", "").upper()
        clean_name = course_name.replace(" ", "").upper()
        if clean_key in clean_name or clean_name in clean_key:
            return data
    return None

def is_relevant_announcement(title, message, my_sections):
    text = (title + " " + message).upper()
    mentioned_sections = set(re.findall(r"\b[LSR]\d+\b", text))
    if not mentioned_sections: return True 
    for sec in my_sections:
        if sec.upper() in mentioned_sections: return True
    return False

def find_date_in_text(text, default_date_str, class_days):
    # Robust date parser for announcements
    posted_date_obj = datetime.strptime(default_date_str[:10], "%Y-%m-%d")
    return posted_date_obj

def main():
    API_URL = os.environ.get("CANVAS_API_URL")
    API_KEY = os.environ.get("CANVAS_API_KEY")
    
    if not API_URL or not API_KEY:
        print("❌ Error: Missing CANVAS_API_URL or CANVAS_API_KEY")
        return

    canvas = Canvas(API_URL, API_KEY)
    cal = Calendar()
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print("🔄 Syncing Canvas Data...")
    try:
        courses = canvas.get_courses(enrollment_state='active')
        for course in courses:
            config_data = get_course_config(course.course_code)
            class_days = config_data['days'] if config_data else []
            my_sections = config_data['sections'] if config_data else []
            
            # 1. Assignments
            for assign in course.get_assignments():
                if assign.due_at and assign.due_at > start_date:
                    e = Event()
                    e.name = f"📝 {assign.name} ({course.course_code})"
                    e.begin = assign.due_at
                    e.description = assign.html_url
                    cal.events.add(e)
            
            # 2. Announcements
            for ann in course.get_discussion_topics(only_announcements=True):
                if ann.posted_at and ann.posted_at > start_date:
                    if my_sections and not is_relevant_announcement(ann.title, ann.message, my_sections):
                        continue 
                    e = Event()
                    parsed_date = find_date_in_text(f"{ann.title} {ann.message}", ann.posted_at, class_days)
                    e.name = f"📢 {ann.title} ({course.course_code})"
                    e.begin = parsed_date
                    e.make_all_day()
                    cal.events.add(e)
    except Exception as e:
        print(f"⚠️ Canvas Sync Error: {e}")

    # --- 3. ADD MANUAL CLASS TIMINGS (TIMEZONE FIXED) ---
    print("📅 Injecting Class Timings from MY_TIMETABLE...")
    import pytz # You might need to add 'pytz' to requirements.txt
    local_tz = pytz.timezone("Asia/Karachi")

    for course_name, data in COURSE_CONFIGS.items():
        if 'times' in data and 'days' in data:
            for day_index in data['days']:
                for start_t, end_t in data['times']:
                    e = Event()
                    e.name = f"🏫 Class: {course_name}"
                    
                    today = datetime.now(local_tz)
                    start_of_week = today - timedelta(days=today.weekday())
                    class_date = start_of_week + timedelta(days=day_index)
                    
                    try:
                        # Create "naive" time first
                        begin_naive = datetime.strptime(f"{class_date.strftime('%Y-%m-%d')} {start_t}", "%Y-%m-%d %H:%M")
                        end_naive = datetime.strptime(f"{class_date.strftime('%Y-%m-%d')} {end_t}", "%Y-%m-%d %H:%M")
                        
                        # Localize to Pakistan Time
                        e.begin = local_tz.localize(begin_naive)
                        e.end = local_tz.localize(end_naive)
                        
                        day_names = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
                        rrule = ContentLine(name="RRULE", value=f"FREQ=WEEKLY;BYDAY={day_names[day_index]}")
                        e.extra.append(rrule)
                        
                        cal.events.add(e)
                    except Exception as time_err:
                        print(f"❌ Time format error for {course_name}: {time_err}")

    with open('my_schedule.ics', 'w', encoding='utf-8') as f:
        f.writelines(cal)
    print("✅ Success! Calendar file generated with repeating Class Timings.")

if __name__ == "__main__":
    main()


