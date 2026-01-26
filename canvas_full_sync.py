import os
from canvasapi import Canvas
from ics import Calendar, Event
from datetime import datetime

# --- CONFIGURATION ---
# Checks for Environment Variables (for GitHub) OR uses hardcoded strings (for Local Test)
# --- CONFIGURATION ---
# This tells the script: "Look for the key in GitHub Secrets, don't read it from here."
API_URL = os.environ["CANVAS_API_URL"]
API_KEY = os.environ["CANVAS_API_KEY"]
# ---------------------
OUTPUT_FILE = "my_schedule.ics"
# ---------------------

def main():
    try:
        canvas = Canvas(API_URL, API_KEY)
        calendar = Calendar()
        
        # Get active courses
        courses = canvas.get_courses(enrollment_state='active')
        
        count = 0
        print("Starting Sync...")

        for course in courses:
            if not hasattr(course, 'name'): continue
            
            # 1. Fetch Assignments (Upcoming)
            try:
                assignments = course.get_assignments(bucket='upcoming')
                for assign in assignments:
                    if assign.due_at:
                        e = Event()
                        e.name = f"📝 {assign.name} ({course.course_code})"
                        e.begin = assign.due_at 
                        e.description = f"Due: {assign.due_at}\n{assign.html_url}"
                        e.url = assign.html_url
                        calendar.events.add(e)
                        count += 1
            except Exception as e:
                print(f"Skipping assignments for {course.name}: {e}")

            # 2. Fetch Announcements (Last 14 Days)
            try:
                announcements = canvas.get_announcements(
                    context_codes=[f"course_{course.id}"],
                    start_date="2025-01-01",
                    end_date=datetime.now().strftime("%Y-%m-%d")
                )
                for ann in announcements:
                    e = Event()
                    icon = "📢"
                    if "exam" in ann.title.lower() or "urgent" in ann.title.lower():
                        icon = "🔥"
                    
                    e.name = f"{icon} {ann.title} ({course.course_code})"
                    e.begin = ann.posted_at
                    e.description = f"{ann.message}\n{ann.url}"
                    e.url = ann.url
                    calendar.events.add(e)
                    count += 1
            except Exception as e:
                print(f"Skipping announcements for {course.name}: {e}")

        # Save to file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.writelines(calendar.serialize())
        
        print(f"✅ Success! {count} items saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    main()
