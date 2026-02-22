# 📅 Canvas to Calendar Bot (Smart Edition)

This tool automatically pulls your **Assignments**, **Announcements**, and **Events** from Canvas and syncs them to your Google/Apple Calendar.

### ✨ Smart Features
* **Auto-Sync:** Runs automatically every day to keep your schedule fresh.
* **The "Bouncer" Filter:** Intelligent logic that reads announcement titles (e.g., "Quiz for Section L1") and **only adds it** if it matches *your* specific section.
* **Smart Date Parsing:** If a professor writes "Quiz next class" or "Midterm on Jan 29th" in an announcement, this bot calculates the exact date and adds it to your calendar.
* **"All Sections" Support:** Handles courses where one announcement applies to everyone (like Math or General Science).

---

## 🚀 How to Set This Up

### Step 1: Get the Code
1. Click the **Fork** button (top right of this page) to copy this repository to your own GitHub account.

### Step 2: Get Your Canvas Key
1. Log in to your school's Canvas website.
2. Go to **Account** $\rightarrow$ **Settings**.
3. Scroll down to **Approved Integrations** and click **+ New Access Token**.
4. Name it "Calendar Bot" and set an expiration date (e.g., 6 months).
5. **Copy the long token immediately** (you won't see it again).

### Step 3: Configure Your Secrets (Crucial Step)
1. Go to your new repository's **Settings** tab.
2. On the left sidebar, click **Secrets and variables** $\rightarrow$ **Actions**.
3. Click **New repository secret** and add these 3 secrets:

| Secret Name | Value |
| :--- | :--- |
| `CANVAS_API_KEY` | Paste the long token you just copied. |
| `CANVAS_API_URL` | Your school's Canvas URL (e.g., `https://canvas.instructure.com`). *Must start with https://* |
| `MY_TIMETABLE` | Your specific class schedule configuration. **See the JSON guide below.** |

#### 📝 How to Format `MY_TIMETABLE`
This is how the bot knows which sections you are in. Copy the code below, paste it into a text editor, and update it for your classes.

* **Course Name:** Must match the name in Canvas (e.g. if Canvas says `CS/CE 412`, use `"CS/CE 412"`).
* **days:** 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday.
* **sections:** Put your section name here (e.g., "L1", "S2").
    * *Tip:* If you leave sections empty `[]`, the bot will accept **ALL** announcements for that course (good for general courses like Math).

```json
{
  "courses": {
    "CS 101": {
      "days": [0, 2],
      "sections": ["L1"]
    },
    "MATH 205": {
      "days": [1, 3],
      "sections": []
    },
    "CS/CE 412": {
      "days": [0, 4],
      "sections": ["L4"]
    }
  }
}

```
(Note: In the example above, MATH 205 has empty sections [], so the bot will grab every announcement for Math. CS 101 has ["L1"], so it will ignore announcements meant for L2 or L3.)
Step 4: Turn on the RobotGo to the Actions tab at the top of your repo.Click Daily Calendar Sync on the left.Click Enable Workflow (if asked).Click Run workflow $\rightarrow$ Run workflow to start it for the first time.
Step 5: Get Your LinkOnce the run turns Green ✅, go to Settings $\rightarrow$ Pages.Under Branch, ensure it is set to main (or gh-pages if created) and click Save.Your calendar link will appear at the top in a minute or two!It looks like: https://(your-username).github.io/canvas-calendar/my_schedule.ics
