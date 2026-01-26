import os
import re
from canvasapi import Canvas
from ics import Calendar, Event
from datetime import datetime, timedelta

# --- THE SMART PARSER ---
def find_date_in_text(text, default_date_str):
    """
    Looks for dates like '28 Jan', 'Jan 28th', 'January 28' in the text.
    If found, returns that specific date object.
    If not found, returns the original default_date.
    """
    if not text:
        return datetime.strptime(default_date_str, "%Y-%m-%d")

    # Current year (to handle "Jan 28" without a year)
    current_year = datetime.now().year
    
    # Regex Patterns to catch dates
    # 1. Catch "28 Jan" or "28th January" or "28 Jan 2026"
    #    Group 1: Day, Group 3: Month, Group 5: Year (Optional)
    pattern1 = r"(\d{1,2})(?:st|nd|rd|th)?\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*(\d{4})?"
    
    # 2. Catch "Jan 28" or "January 28th" or "Jan 28 2026"
    #    Group 1: Month, Group 2: Day, Group 4: Year (Optional)
    pattern2 = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(\d{4})?"

    match1 = re.search(pattern1, text, re.IGNORECASE)
    match2 = re.search(pattern2, text, re.IGNORECASE)

    try:
        day, month_str, year_str = 0, "", ""

        if match1:
            day = int(match1.group(1))
            month_str = match1.group(2)
            year_str = match1.group(3)
        elif match2:
            month_str = match2.group(1)
            day = int(match2.group(2))
            year_str = match2.group(3)
        else:
            # No date found in title, use the posted date
            return datetime.strptime(default_date_str[:10], "%Y-%m-%d")

        # Convert Month Name to Number
        months = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }
        month = months[month_str.lower()[:3]]
        
        # Handle Year: Use found year, or guess current/next year
        if year_str:
            year = int(year_str)
        else:
            # If explicit date is "Jan" but we are in "Dec", assume next year
            if month < datetime.now().month and (datetime.now().month - month) > 6:
                year = current_year + 1
            else:
                year = current_year

        # Return the parsed date!
        return datetime(year, month, day)

    except Exception as e:
        print(f"⚠️ Regex failed on '{text}': {e}")
        return datetime.strptime(default_date_str[:10], "%Y-%m-%d")


# --- MAIN SCRIPT ---
def main():
    API_URL = os.environ["CANVAS_API_URL"]
    API_KEY = os.environ["CANVAS_API_KEY"]
    canvas = Canvas(API_URL, API_KEY)
    cal = Calendar()
    
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")

    print("🔄 Syncing with Smart Date Parsing...")

    courses = canvas.get_courses(enrollment_state='active')
    
    for course in courses:
        try:
            # A. Assignments (Standard)
            assignments = course.get_assignments(bucket='upcoming')
            for assign in assignments:
                if assign.due_at:
                    e = Event()
                    e.name = f"📝 {assign.name} ({course.course_code})"
                    e.begin = assign.due_at
                    e.description = assign.html_url
                    cal.events.add(e)
            
            # B. Announcements (With Regex Magic)
            announcements = course.get_discussion_topics(only_announcements=True)
            for ann in announcements:
                if ann.posted_at and ann.posted_at > start_date:
                    e = Event()
                    
                    # 1. Try to find a date in the Title
                    parsed_date = find_date_in_text(ann.title, ann.posted_at)
                    
                    e.name = f"📢 {ann.title} ({course.course_code})"
                    e.begin = parsed_date
                    e.make_all_day()
                    e.description = f"Originally Posted: {ann.posted_at[:10]}\nLink: {ann.html_url}\n\n{ann.message[:200]}..."
                    cal.events.add(e)

        except Exception as e:
            print(f"⚠️ Skipped {course.name}: {e}")

    # C. Calendar Events
    try:
        user = canvas.get_current_user()
        events = user.get_calendar_events(start_date=start_date, end_date=end_date)
        for event in events:
            e = Event()
            e.name = f"🗓️ {event.title}"
            e.begin = event.start_at
            if event.end_at:
                e.end = event.end_at
            else:
                e.duration = {"hours": 1}
            cal.events.add(e)
    except:
        pass

    with open('my_schedule.ics', 'w', encoding='utf-8') as f:
        f.writelines(cal)
    
    print("✅ Success!")

if __name__ == "__main__":
    main()
