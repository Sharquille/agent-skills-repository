import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

spec = importlib.util.spec_from_file_location(
    "sync_deadlines", Path(__file__).resolve().parents[1] / "scripts" / "sync_deadlines.py")
assert spec is not None and spec.loader is not None
sd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sd)

LOCAL = timezone(timedelta(hours=-4))  # the learner's clock (AST)
CFG = dict(sd.DEFAULTS, calendar="Test")


def at(text):
    return datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=LOCAL)


def item(**kw):
    base = {"id": "it100-w09-post", "title": "Post", "due": "2026-11-08 18:00", "zone": "AST"}
    base.update(kw)
    return base


class PlanTests(unittest.TestCase):
    def test_est_sunday_5pm_equals_ast_6pm_in_november(self):
        self.assertEqual(sd.parse_when("2026-11-08 17:00", "EST"), sd.parse_when("2026-11-08 18:00", "AST"))

    def test_target_caps_at_4pm_on_due_day(self):
        p = sd.plan_item(item(), "IT-100", CFG, at("2026-11-04 20:00"), LOCAL)
        self.assertEqual(p["target"], at("2026-11-08 16:00"))

    def test_daily_alerts_at_9_and_4_until_due(self):
        p = sd.plan_item(item(), "IT-100", CFG, at("2026-11-04 20:00"), LOCAL)
        self.assertEqual(len(p["alarms"]), 8)  # Thu-Sun, twice a day
        self.assertEqual(p["alarms"][0], at("2026-11-05 09:00"))
        self.assertEqual(p["alarms"][-1], at("2026-11-08 16:00"))

    def test_final_call_when_no_alert_in_last_three_hours(self):
        p = sd.plan_item(item(due="2026-11-04 23:00", target="2026-11-04 23:00"), "IT-100", CFG,
                         at("2026-11-04 20:00"), LOCAL)
        self.assertEqual(p["alarms"], [at("2026-11-04 22:00")])

    def test_passed_target_falls_back_to_due(self):
        p = sd.plan_item(item(due="2026-11-04 23:00"), "IT-100", CFG, at("2026-11-04 20:00"), LOCAL)
        self.assertEqual(p["target"], at("2026-11-04 23:00"))

    def test_past_and_done_items_get_no_alerts(self):
        past = sd.plan_item(item(due="2026-11-01 18:00"), "IT-100", CFG, at("2026-11-04 20:00"), LOCAL)
        done = sd.plan_item(item(status="done"), "IT-100", CFG, at("2026-11-04 20:00"), LOCAL)
        self.assertEqual((past["mode"], past["alarms"]), ("past", []))
        self.assertEqual((done["mode"], done["alarms"]), ("done", []))

    def test_alerts_start_at_most_max_days_before(self):
        p = sd.plan_item(item(due="2026-12-31 18:00"), "IT-100", CFG, at("2026-11-04 20:00"), LOCAL)
        self.assertEqual(p["alarms"][0], at("2026-12-17 09:00"))


class SyncArgsTests(unittest.TestCase):
    def calendar_args(self, rem_result, **kw):
        now = at("2026-11-04 20:00")
        p = sd.plan_item(item(**kw), "IT-100", CFG, now, LOCAL)
        with mock.patch.object(sd, "osa", side_effect=[rem_result, "updated"]) as osa:
            sd.sync(p, item(**kw), CFG, "IT-100/Week-09", now)
        return osa.call_args_list[1].args[1]

    def test_open_event_ends_at_deadline_with_one_slot_per_alert(self):
        args = self.calendar_args("updated")
        self.assertEqual(args[9:13], ["2026", "11", "8", str(18 * 3600)])  # end date
        self.assertEqual(len(args[15:]), 8)

    def test_default_alert_moment_is_not_duplicated(self):
        args = self.calendar_args("updated", due="2026-11-05 09:40", target="2026-11-05 09:40")
        self.assertNotIn("10", args[15:])  # 09:00 alert = 10 min before a 09:10 start

    def test_ticked_reminder_moves_event_to_now_with_no_alerts(self):
        args = self.calendar_args("completed")
        self.assertEqual(args[2], "done")
        self.assertTrue(args[3].startswith("✓ "))
        self.assertEqual(args[5:9], ["2026", "11", "4", str(20 * 3600)])
        self.assertEqual(args[15:], [])


class ValidateTests(unittest.TestCase):
    def test_good_file_passes(self):
        self.assertEqual(sd.validate([(Path("a.json"), {"course": "IT-100", "items": [item()]})]), [])

    def test_duplicate_ids_across_files_fail(self):
        docs = [(Path("a.json"), {"course": "IT-100", "items": [item()]}),
                (Path("b.json"), {"course": "MA-235", "items": [item()]})]
        self.assertTrue(any("duplicate id" in e for e in sd.validate(docs)))

    def test_bad_zone_and_missing_fields_fail(self):
        errors = sd.validate([(Path("a.json"), {"course": "IT-100", "items": [item(zone="Mars"), {"id": "x"}]})])
        self.assertTrue(any("unknown time zone" in e for e in errors))
        self.assertTrue(any("missing title" in e for e in errors))

    def test_find_files_reads_course_week_folders(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "IT-100" / "Week-09_2026-11-02_to_2026-11-08" / "deadlines.json"
            f.parent.mkdir(parents=True)
            f.write_text(json.dumps({"course": "IT-100", "items": []}))
            self.assertEqual(sd.find_files(Path(d)), [f])

    def test_dry_run_touches_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "IT-100" / "Week-09" / "deadlines.json"
            f.parent.mkdir(parents=True)
            f.write_text(json.dumps({"course": "IT-100", "items": [item()]}))
            with mock.patch.object(sd, "osa", side_effect=AssertionError("dry run called osascript")) as osa, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sd.main(["--root", d, "--dry-run", "--now", "2026-11-04 20:00"]), 0)
            osa.assert_not_called()


if __name__ == "__main__":
    unittest.main()
