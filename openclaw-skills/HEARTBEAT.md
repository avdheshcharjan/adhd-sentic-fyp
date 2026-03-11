## Every morning at 7:30 AM:
- Fetch Whoop morning briefing from http://localhost:8420/whoop/morning-briefing
- Deliver formatted ADHD morning briefing to user using the morning-briefing skill
- If the fetch fails, send fallback: "Couldn't fetch your Whoop data this morning. Start with 25-min focus blocks and check in with yourself."

## Every 30 minutes during active hours (9 AM - 10 PM):
- Fetch current insights from http://localhost:8420/insights/current
- Only message the user if:
  - behavioral_state is "distracted" AND distraction_ratio > 0.5
  - OR hyperfocus_detected is true AND current_streak_minutes > 180
- Use the focus-check skill to format the message
- Do NOT message if everything looks normal — avoid notification fatigue

## Every Sunday at 8 PM:
- Fetch weekly review from http://localhost:8420/insights/weekly
- Deliver formatted weekly ADHD pattern summary using the weekly-review skill
