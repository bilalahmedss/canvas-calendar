📅 Canvas to Calendar Bot
This tool automatically pulls your Assignments and Announcements from Canvas and puts them into your Google/Apple Calendar. It updates every day automatically!

🚀 How to set this up for yourself
Step 1: Get the Code
Click the Fork button (top right of this page) to copy this repository to your own account.

Step 2: Get Your Canvas Key
Log in to Canvas.

Go to Account → Settings.

Scroll down to Approved Integrations and click + New Access Token.

Name it "Calendar" and copy the long code it gives you.

Step 3: Add Your Secrets
Go to your new repository's Settings tab.

Click Secrets and variables → Actions → New repository secret.

Add these two secrets:

CANVAS_API_KEY: Paste the long token you just copied.

CANVAS_API_URL: Paste our school's Canvas URL (e.g., https://canvas.instructure.com). Make sure it starts with https://

Step 4: Turn on the Robot
Go to the Actions tab.

Click Daily Calendar Sync on the left.

Click Enable Workflow (if asked).

Click Run workflow to start it for the first time.

Step 5: Get Your Link
Once the run turns Green ✅, go to Settings → Pages.

Under Branch, select main and click Save.

Your calendar link will appear at the top!

It will look like: https://<your-username>.github.io/canvas-calendar/canvas_full.ics

Step 6: Add to Phone
iPhone: Settings → Apps → Calendar → Calendar Accounts → Add Account → Other → Add Subscribed Calendar.

Google: Calendar Website → "+" next to Other Calendars → From URL.
