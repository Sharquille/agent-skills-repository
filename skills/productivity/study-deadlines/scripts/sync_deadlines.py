#!/usr/bin/env python3
"""Sync study deadlines into Apple Reminders and Apple Calendar.

Reads every <Course>/Week-*/deadlines.json under --root (or the files given),
plus an optional <root>/deadlines.config.json. For each open item it keeps:

- one reminder in the course's Reminders list, due at the personal target
  (no alert of its own, so each moment notifies once, from Calendar);
- one Calendar event ending at the official deadline, with an alert every day
  at each configured alert time until the deadline, and a final call when no
  alert lands in the last three hours.

Re-running updates in place: each item carries a hidden marker [sd:<id>].
A reminder ticked off in Reminders marks the item done, and the next sync
clears that event's remaining alerts. Past deadlines are never created.

Usage: sync_deadlines.py [--root DIR] [--dry-run] [--now "YYYY-MM-DD HH:MM"] [FILE ...]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, time, timedelta, timezone, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Blackboard prints "AST" (Atlantic Standard Time, UTC-4, no daylight time).
# Instructors write "EST" for US Eastern clock time, which shifts with DST.
ZONES = {
    "AST": "America/Puerto_Rico",
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "ET": "America/New_York",
    "UTC": "UTC",
}
DEFAULTS = {
    "calendar": None,            # Calendar name; required to create events
    "alert_times": ["09:00", "16:00"],
    "target_time": "16:00",      # personal target: due day at this time when the deadline is later
    "final_call_minutes": 60,    # extra alert before the deadline when none lands in the last 3 h
    "max_days": 14,              # daily alerts start at most this many days before the deadline
    "event_minutes": 30,
    "calendar_default_alert_minutes": 10,  # the alert Calendar adds to every new event; scripts can't edit it
}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,80}$")
WHEN_FMT = "%Y-%m-%d %H:%M"


def zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(ZONES.get(name.upper(), name))
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"unknown time zone {name!r}; use AST, EST, or an IANA name") from None


def parse_when(text: str, zone_name: str) -> datetime:
    return datetime.strptime(text, WHEN_FMT).replace(tzinfo=zone(zone_name))


def hm(text: str) -> time:
    return datetime.strptime(text, "%H:%M").time()


def load_config(root: Path) -> dict:
    cfg = dict(DEFAULTS)
    path = root / "deadlines.config.json"
    if path.is_file():
        cfg.update(json.loads(path.read_text()))
    return cfg


def find_files(root: Path) -> list[Path]:
    return sorted(root.glob("*/Week-*/deadlines.json"))


def validate(docs: list[tuple[Path, dict]]) -> list[str]:
    errors, seen = [], {}
    for path, doc in docs:
        if not isinstance(doc.get("course"), str) or not doc["course"].strip():
            errors.append(f"{path}: missing course")
        for i, item in enumerate(doc.get("items") or []):
            where = f"{path} item {i + 1}"
            for key in ("id", "title", "due", "zone"):
                if not item.get(key):
                    errors.append(f"{where}: missing {key}")
            iid = item.get("id", "")
            if iid and not ID_RE.match(iid):
                errors.append(f"{where}: id {iid!r} must be lowercase letters, digits, and hyphens")
            if iid in seen:
                errors.append(f"{where}: duplicate id {iid!r} (also in {seen[iid]})")
            seen[iid] = path
            if item.get("status", "open") not in ("open", "done"):
                errors.append(f"{where}: status must be open or done")
            try:
                if item.get("due") and item.get("zone"):
                    parse_when(item["due"], item["zone"])
                    if item.get("target"):
                        parse_when(item["target"], item["zone"])
            except ValueError as e:
                errors.append(f"{where}: {e}")
    return errors


def plan_item(item: dict, course: str, cfg: dict, now: datetime, local: tzinfo) -> dict:
    """Pure schedule for one item: target, alert times, and mode."""
    due = parse_when(item["due"], item["zone"]).astimezone(local)
    if item.get("target"):
        target = parse_when(item["target"], item["zone"]).astimezone(local)
    else:
        cap = datetime.combine(due.date(), hm(cfg["target_time"]), local)
        target = min(due, cap)
    if target <= now < due:
        target = due  # the personal target already passed; keep the real one live
    if item.get("status") == "done":
        mode = "done"
    elif due <= now:
        mode = "past"
    else:
        mode = "open"
    alarms: list[datetime] = []
    if mode == "open":
        first = max(now.date(), due.date() - timedelta(days=int(cfg["max_days"])))
        day = first
        while day <= due.date():
            for t in cfg["alert_times"]:
                a = datetime.combine(day, hm(t), local)
                if now < a < due:
                    alarms.append(a)
            day += timedelta(days=1)
        if not any(a >= due - timedelta(hours=3) for a in alarms):
            final = due - timedelta(minutes=int(cfg["final_call_minutes"]))
            if final > now:
                alarms.append(final)
    official = parse_when(item["due"], item["zone"])
    return {
        "id": item["id"],
        "course": course,
        "title": item["title"],
        "mode": mode,
        "due": due,
        "target": target,
        "alarms": sorted(alarms),
        "official": f"{official:%a %b %-d, %-I:%M %p} {item['zone']}",
        "marker": f"[sd:{item['id']}]",
    }


def body_text(p: dict, item: dict, source_rel: str) -> str:
    lines = [f"Official deadline: {p['official']}", f"Your target: {p['target']:%a %b %-d, %-I:%M %p}"]
    if item.get("notes"):
        lines.append(item["notes"])
    if item.get("source"):
        lines.append(f"Prompt: {source_rel}/{item['source']}")
    lines.append(p["marker"])
    return "\n".join(lines)


def date_args(d: datetime) -> list[str]:
    return [str(d.year), str(d.month), str(d.day), str(d.hour * 3600 + d.minute * 60)]


MKDATE = """
on mk(y, mo, d, s)
	set t to current date
	set day of t to 1
	set year of t to (y as integer)
	set month of t to (mo as integer)
	set day of t to (d as integer)
	set time of t to (s as integer)
	return t
end mk
"""

REMINDER_SCRIPT = MKDATE + """
on run argv
	set {listName, marker, mode, ttl, bodyText} to items 1 thru 5 of argv
	set td to mk(item 6 of argv, item 7 of argv, item 8 of argv, item 9 of argv)
	tell application "Reminders"
		if (name of every account) contains "iCloud" then
			set acct to account "iCloud"
		else
			set acct to first account
		end if
		if (name of every list of acct) does not contain listName then make new list at acct with properties {name:listName}
		set L to list listName of acct
		set found to (every reminder of L whose body contains marker)
		if (count of found) is 0 then
			if mode is not "open" then return "none"
			set r to make new reminder at end of reminders of L with properties {name:ttl, body:bodyText}
			set res to "created"
		else
			set r to item 1 of found
			if completed of r then return "completed"
			if mode is "past" then return "past"
			set name of r to ttl
			set body of r to bodyText
			set res to "updated"
		end if
		if mode is "done" then
			set completed of r to true
			return "completed"
		end if
		set due date of r to td
		return res
	end tell
end run
"""

CALENDAR_SCRIPT = MKDATE + """
on run argv
	set {calName, marker, mode, ttl, descText} to items 1 thru 5 of argv
	set sd to mk(item 6 of argv, item 7 of argv, item 8 of argv, item 9 of argv)
	set ed to mk(item 10 of argv, item 11 of argv, item 12 of argv, item 13 of argv)
	set deadMinutes to item 14 of argv
	set defaultMinutes to item 15 of argv
	set offsets to {}
	if (count of argv) > 15 then set offsets to items 16 thru -1 of argv
	tell application "Calendar"
		set cal to first calendar whose name is calName
		set found to (every event of cal whose description contains marker)
		if (count of found) is 0 then
			if mode is not "open" then return "none"
			set ev to make new event at end of events of cal with properties {summary:ttl, start date:sd, end date:ed, description:descText}
			set res to "created"
		else
			set ev to item 1 of found
			set summary of ev to ttl
			set description of ev to descText
			if sd > (end date of ev) then
				set end date of ev to ed
				set start date of ev to sd
			else
				set start date of ev to sd
				set end date of ev to ed
			end if
			set res to "updated"
		end if
		-- Calendar's scripting cannot delete alarms (-10000), and every new
		-- event gets the calendar's default alert, which also ignores edits.
		-- Leave the default alone, reuse the other slots for planned alerts,
		-- and park unneeded slots at a moment already past.
		set n to count of offsets
		set idx to 1
		repeat with a in (display alarms of ev)
			if (trigger interval of a) is not (0 - (defaultMinutes as integer)) then
				if idx ≤ n then
					set trigger interval of a to (0 - ((item idx of offsets) as integer))
					set idx to idx + 1
				else
					set trigger interval of a to (0 - (deadMinutes as integer))
				end if
			end if
		end repeat
		repeat while idx ≤ n
			make new display alarm at end of display alarms of ev with properties {trigger interval:(0 - ((item idx of offsets) as integer))}
			set idx to idx + 1
		end repeat
		return res
	end tell
end run
"""


def osa(script: str, args: list[str]) -> str:
    out = subprocess.run(["osascript", "-", *args], input=script, capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or "osascript failed")
    return out.stdout.strip()


def sync(p: dict, item: dict, cfg: dict, source_rel: str, now: datetime) -> tuple[str, str]:
    body = body_text(p, item, source_rel)
    rem = osa(REMINDER_SCRIPT, [p["course"], p["marker"], p["mode"], p["title"], body, *date_args(p["target"])])
    mode = "done" if rem == "completed" else p["mode"]
    span = timedelta(minutes=int(cfg["event_minutes"]))
    default = int(cfg["calendar_default_alert_minutes"])
    if mode == "done":
        # The default alert can't be removed, so a finished item's event moves
        # to the moment it was found done, which puts that alert in the past.
        start, end = now, now + span
    else:
        start, end = p["due"] - span, p["due"]
    offsets = [int((start - a).total_seconds() // 60) for a in p["alarms"]] if mode == "open" else []
    offsets = [str(m) for m in offsets if m != default]  # the default alert already covers that moment
    # An alert one day before now never fires; unneeded slots are parked there.
    dead = str(max(0, int((start - now).total_seconds() // 60)) + 1440)
    prefix = "✓ " if mode == "done" else "DUE "
    cal = osa(CALENDAR_SCRIPT, [cfg["calendar"], p["marker"], mode, f"{prefix}{p['course']}: {p['title']}", body,
                                *date_args(start), *date_args(end), dead, str(default), *offsets])
    return rem, cal


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--root", type=Path, default=Path.cwd(), help="semester folder holding <Course>/Week-*/")
    ap.add_argument("--dry-run", action="store_true", help="print the plan; touch nothing")
    ap.add_argument("--now", help="pretend it is this local time (testing)")
    args = ap.parse_args(argv)

    root = args.root.resolve()
    cfg = load_config(root)
    files = [f.resolve() for f in args.files] or find_files(root)
    if not files:
        print(f"no deadlines.json under {root}", file=sys.stderr)
        return 1
    docs = [(f, json.loads(f.read_text())) for f in files]
    errors = validate(docs)
    if not args.dry_run and not cfg.get("calendar"):
        errors.append(f"set \"calendar\" in {root / 'deadlines.config.json'}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    local = datetime.now().astimezone().tzinfo or timezone.utc
    now = datetime.strptime(args.now, WHEN_FMT).replace(tzinfo=local) if args.now else datetime.now(local)
    failed = 0
    for path, doc in docs:
        try:
            source_rel = str(path.parent.relative_to(root))
        except ValueError:
            source_rel = str(path.parent)
        for item in doc.get("items") or []:
            p = plan_item(item, doc["course"], cfg, now, local)
            line = (f"{p['course']:7} {p['mode']:5} due {p['due']:%a %m/%d %H:%M} target {p['target']:%a %H:%M} "
                    f"alerts {len(p['alarms']):2}  {p['title']}")
            if args.dry_run:
                print(line)
                continue
            try:
                rem, cal = sync(p, item, cfg, source_rel, now)
                print(f"{line}  [reminder {rem}, calendar {cal}]")
            except (RuntimeError, subprocess.TimeoutExpired) as e:
                failed += 1
                print(f"{line}  [FAILED: {e}]", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
