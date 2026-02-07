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
        print("⚠️ Warning: MY_TIMETABLE secret is not valid JSON")
        return {}

CONFIG = load_config()
COURSE_CONFIGS = CONFIG.get("courses", {})
LOCAL_TZ = pytz.timezone("Asia/Karachi")

def get_course_config(course_code, course_name):
    # This checks both the ID (like CS 492) and the long name (like Visual Programming)
    combined_name = (str(course_code) + " " + str(course_name)).replace(" ", "").upper()
    for key, data in COURSE_CONFIGS.items():
        clean_key = key.replace(" ", "").upper()
        if clean_key in combined_name:
            return data
    return None

def is_relevant_announcement(title, message, my_sections):
    text = (title + " " + message).upper()
    mentioned_sections = set(re.findall(r"\b[LSR]\d+\b", text))
    if not mentioned_sections: return True 
    for sec in my_sections:
        if sec.upper() in mentioned_sections: return True
    return False

def main():
    API_URL = os.environ.get("CANVAS_API_URL")
    API_KEY = os.environ.get("CANVAS_API_KEY")
    print("🔄 Syncing Canvas Data...")
    courses = canvas.get_courses(enrollment_state='active')
    
    found_any_course = False
    for course in courses:
        found_any_course = True
        # NEW: This prints every course the robot finds to the GitHub Log
        print(f"📂 Found on Canvas: {course.course_code} - {course.name}")
        
        config_data = get_course_config(course.course_code, course.name)
        if not config_data:
            print(f"⚠️ Skipping: No match in MY_TIMETABLE for {course.course_code}")
            continue
    
    if not API_URL or not API_KEY:
        print("❌ Error: Missing CANVAS_API_URL or CANVAS_API_KEY")
        return

    canvas = Canvas(API_URL, API_KEY)
    cal = Calendar()
    start_date = (datetime.now(LOCAL_TZ) - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # 1. Sync Canvas Data (Assignments & Announcements)
    print("🔄 Syncing Canvas Data...")
    try:
        courses = canvas.get_courses(enrollment_state='active')
        for course in courses:
            config_data = get_course_config(course.course_code)
            class_days = config_data['days'] if config_data else []
            my_sections = config_data['sections'] if config_data else []
            
            # Assignments
            for assign in course.get_assignments():
                if assign.due_at and assign.due_at > start_date:
                    e = Event()
                    e.name = f"📝 {assign.name} ({course.course_code})"
                    e.begin = assign.due_at # Canvas times are UTC; ics handles them
                    e.description = assign.html_url
                    cal.events.add(e)
            
            # Announcements
            for ann in course.get_discussion_topics(only_announcements=True):
                if ann.posted_at and ann.posted_at > start_date:
                    if my_sections and not is_relevant_announcement(ann.title, ann.message, my_sections):
                        continue 
                    e = Event()
                    e.name = f"📢 {ann.title} ({course.course_code})"
                    # Simple date for announcements
                    e.begin = datetime.strptime(ann.posted_at[:10], "%Y-%m-%d")
                    e.make_all_day()
                    cal.events.add(e)
    except Exception as e:
        print(f"⚠️ Canvas Sync Error: {e}")

    # 2. Injecting Class Timings (Fixed Karachi Time)
    print("📅 Injecting Class Timings (Asia/Karachi)...")
    for course_name, data in COURSE_CONFIGS.items():
        if 'times' in data and 'days' in data:
            for day_index in data['days']:
                for start_t, end_t in data['times']:
                    e = Event()
                    e.name = f"🏫 Class: {course_name}"
                    
                    now = datetime.now(LOCAL_TZ)
                    start_of_week = now - timedelta(days=now.weekday())
                    class_date = start_of_week + timedelta(days=day_index)
                    
                    try:
                        begin_naive = datetime.strptime(f"{class_date.strftime('%Y-%m-%d')} {start_t}", "%Y-%m-%d %H:%M")
                        end_naive = datetime.strptime(f"{class_date.strftime('%Y-%m-%d')} {end_t}", "%Y-%m-%d %H:%M")
                        
                        e.begin = LOCAL_TZ.localize(begin_naive)
                        e.end = LOCAL_TZ.localize(end_naive)
                        
                        day_names = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
                        rrule = ContentLine(name="RRULE", value=f"FREQ=WEEKLY;BYDAY={day_names[day_index]}")
                        e.extra.append(rrule)
                        
                        cal.events.add(e)
                    except Exception as time_err:
                        print(f"❌ Time error for {course_name}: {time_err}")

    with open('my_schedule.ics', 'w', encoding='utf-8') as f:
        f.writelines(cal)
    print("✅ Success! Complete calendar generated.")

if __name__ == "__main__":
    main()

