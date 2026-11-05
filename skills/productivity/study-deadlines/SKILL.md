---
name: study-deadlines
description: "Send Monroe course deadlines (discussion posts and replies, assignments, homework, essays, speeches, group work) from captured Blackboard prompts into Apple Reminders and Apple Calendar, with a reminder per deliverable in the course's list and a calendar event at the official deadline that alerts every day at 9 AM and 4 PM until it is due. Re-running updates in place; a reminder ticked off in Reminders stops that deadline's alerts on the next sync. Use when chapter-study-kit or assignment-workspace captures a prompt with a due date, or when the learner says add my deadlines, remind me, put this week's work in my calendar, or sync deadlines. Do not use to guess deadlines that no captured prompt shows, to read Blackboard, or for personal errands (the Reminders app or Siri covers those)."
# --- provenance ---
category: productivity
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-11-04
---

# Study deadlines

Turn the due dates in captured course prompts into Reminders tasks and
Calendar alerts, so every deliverable nags once a day until it is done. This
replaces the manual Capture Tasks command of the Raycast Study To-Do
extension; its drills stay where they are.

Workflow version: **1.0.0**

```text
SKILL_DIR=/Users/sharquilleandrew/Documents/development/github-local/agent-skills-repository/skills/productivity/study-deadlines
```

## Non-negotiables

- **Only captured deadlines.** Every item comes from a prompt file in the
  week's `Work/prompts/` (screenshot or PDF) and names it in `source`. Never
  invent a due date. If the deadline isn't visible, ask for the screenshot.
- **Record the zone as printed.** Blackboard's "Details & Information" shows
  `AST`; instructors often write "5pm EST" in the body. In November 5 PM EST
  and 6 PM AST are the same moment. When the two disagree, use the earlier one
  and say so in `notes`. When a time has no zone, use the earlier reading.
- **One deliverable per item.** A discussion post and its replies are two
  items; a group assignment is its own item, never merged with individual
  work.
- **Dry-run first, then sync.** Read the dry-run table before writing to the
  learner's apps.
- **Never delete the learner's reminders or events.** The script updates only
  items carrying its `[sd:<id>]` marker and never deletes anything.

## Files it reads

`<semester>/deadlines.config.json`, once per semester:

```json
{"calendar": "Monroe University - Fall 2026", "alert_times": ["09:00", "16:00"], "target_time": "16:00"}
```

`<semester>/<Course>/Week-NN_.../deadlines.json`, one per course week:

```json
{
  "course": "IT-100",
  "week": 9,
  "items": [
    {"id": "it100-w09-discussion-replies", "title": "Discussion: reply to 3 classmates",
     "due": "2026-11-08 18:00", "zone": "AST", "source": "Work/prompts/week-9-discussion.png",
     "notes": "Prompt says Sunday 5pm EST, the same moment as 6:00 PM AST."}
  ]
}
```

| Field | Rule |
| --- | --- |
| `course` | The Reminders list name (`EN-221`, `IT-100`, `LA-122`, `MA-235`); created if missing |
| `id` | `<course>-wNN-<slug>`, lowercase and hyphens, unique across the semester; never reuse one |
| `due`, `zone` | Official deadline as printed: `YYYY-MM-DD HH:MM` and `AST`, `EST`, or an IANA name |
| `target` | Optional personal target in the same zone. Default: 4 PM on the due day when the deadline is later |
| `status` | `open` (default) or `done`, to close an item from the file side |
| `source`, `notes` | Prompt path relative to the week folder; anything the learner should see in the task |

## What the sync makes

- **Reminders:** one task per item in the course list, due at the target,
  with the official deadline, notes, and prompt path in its notes. It carries
  no alert, so each moment notifies once.
- **Calendar:** one event, `DUE <course>: <title>`, ending at the official
  deadline. Alerts fire at every `alert_times` slot from today (at most 14
  days out) until the deadline, plus a final call one hour before when no
  alert lands in the last three hours.
- **Done:** tick the reminder. On the next sync the event becomes
  `✓ <course>: <title>`, moves to the moment the sync found it done, and its
  alerts are parked in the past.
- **Past deadlines** are never created and their events keep no live alerts.

Calendar scripting cannot delete alerts, and every new event gets the
calendar's default alert (10 minutes before the event starts, which is 40
minutes before the deadline). That alert also ignores edits. The script
leaves it alone, reuses every other slot, and parks unused slots a day in the
past, where they never fire. Full EventKit access is denied on this Mac (write
only), so EventKit can't find events to update. Keep `calendar_default_alert_minutes` in the config
matched to Calendar → Settings → Alerts.

## Workflow

1. Read every prompt in each course's `Week-NN/Work/prompts/`. List each
   deliverable with its printed deadline and zone.
2. Write or update that week's `deadlines.json`. Keep existing ids, change
   dates in place, and set `"status": "done"` rather than removing an item.
3. Dry run from the semester folder and read the table:
   `python3 -I "$SKILL_DIR/scripts/sync_deadlines.py" --root . --dry-run`
4. Sync: the same command without `--dry-run`. It takes a few seconds per
   item; a failure on one item is reported and the rest still sync.
5. Report a table: course, deliverable, official deadline, target, alert
   count. Flag anything due within 24 hours first.

Re-run step 4 any time; it is idempotent. Run it again after the learner
ticks items off, so finished work stops alerting.

## Called from

- `chapter-study-kit`: when a drop includes assignment or discussion prompts.
- `assignment-workspace`: step 2 (status table), after capture.

## Tests

`python3 -I -m unittest discover -s "$SKILL_DIR/tests"` (no Apple apps
touched).
