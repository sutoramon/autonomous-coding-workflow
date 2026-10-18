"""Regression checks for ACW rules; only disposable repositories are modified."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import acw

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "app"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "ACW Test"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "acw@example.invalid"], check=True)
        (self.root / "README.md").write_text("# Temporary app\n")
        acw.init_project(self.root)
        (self.root / ".acw/project.json").write_text(json.dumps({
            "schema_version":1, "workflow_version":"1.0.0", "project":"Temporary app", "mode":"solo",
            "authority":{"merge":"user","deploy":"user"}, "required_files":["README.md"]}))
        (self.root / ".acw/quality-gates.json").write_text(json.dumps({
            "schema_version":1,"checks":[
                {"id":"test-check","argv":["python3","-c","print('ok')"],
                 "required_for":["light","standard","critical"],"timeout_seconds":5}]}))
        subprocess.run(["git","-C",str(self.root),"add","."], check=True)
        subprocess.run(["git","-C",str(self.root),"commit","-qm","baseline"], check=True)

    def task(self, **overrides):
        x={"schema_version":1,"id":"TASK-001","status":"in_progress","risk":"standard",
            "critical_triggers":[],"acceptance":["The feature responds correctly."],
            "next_action":"Write test.","blockers":[],
            "self_review":{"verdict":"not_run","source_sha":None,"findings":[]}}
        x.update(overrides)
        return x

    def test_project_valid(self):
        config,gates=acw.validate_project(self.root)
        self.assertEqual(config["mode"],"solo")
        self.assertEqual(acw.required_ids(gates,"critical"),["test-check"])

    def test_risk_escalation_blocks_downgrade(self):
        with self.assertRaisesRegex(ValueError,"Critical triggers"):
            acw.validate_task(self.task(risk="standard",critical_triggers=["auth change"]))

    def test_real_gate_required(self):
        obj=acw.load(self.root/".acw/quality-gates.json")
        obj["checks"][0]["example_only"]=True
        with self.assertRaisesRegex(ValueError,"No configured real"):
            acw.validate_gates(obj)

    def test_missing_required_profile_fails(self):
        obj=acw.load(self.root/".acw/quality-gates.json")
        obj["checks"][0]["required_for"]=["standard"]
        with self.assertRaisesRegex(ValueError,"No real mandatory gate"):
            acw.validate_gates(obj)

    def test_missing_done_evidence_fails(self):
        t=self.task(status="done",self_review={"verdict":"passed","source_sha":"x","findings":[]})
        with self.assertRaisesRegex(ValueError,"requires live project"):
            acw.validate_task(t)

    def test_gate_roundtrip(self):
        out=self.root/".acw/evidence"/"first.json"
        info=acw.run_checks(self.root,"standard",out)
        self.assertEqual(info["checks"],1)
        self.assertFalse(info["dirty"])
        self.assertTrue(acw.validate_evidence(acw.load(out),self.root,"standard"))

    def test_changed_source_invalidates_evidence(self):
        out=self.root/".acw/evidence"/"first.json"
        acw.run_checks(self.root,"standard",out)
        (self.root/"README.md").write_text("# Changed\n")
        with self.assertRaisesRegex(ValueError,"clean application source"):
            acw.validate_evidence(acw.load(out),self.root,"standard")

    def test_failed_gate_cannot_pass(self):
        obj=acw.load(self.root/".acw/quality-gates.json")
        obj["checks"][0]["argv"]=["python3","-c","raise SystemExit(3)"]
        (self.root/".acw/quality-gates.json").write_text(json.dumps(obj))
        out=self.root/".acw/evidence"/"failure.json"
        with self.assertRaisesRegex(ValueError,"mandatory checks"):
            acw.run_checks(self.root,"light",out)
        self.assertEqual(acw.load(out)["checks"][0]["result"],"failed")

    def test_missing_binary_blocked(self):
        obj=acw.load(self.root/".acw/quality-gates.json")
        obj["checks"][0]["argv"]=["acw-tool-that-does-not-exist-5467"]
        (self.root/".acw/quality-gates.json").write_text(json.dumps(obj))
        out=self.root/".acw/evidence"/"missing.json"
        with self.assertRaisesRegex(ValueError,"mandatory checks"):
            acw.run_checks(self.root,"critical",out)
        self.assertEqual(acw.load(out)["checks"][0]["result"],"blocked")

    def test_timeout_blocked(self):
        obj=acw.load(self.root/".acw/quality-gates.json")
        obj["checks"][0]["argv"]=["python3","-c","import time; time.sleep(2)"]
        obj["checks"][0]["timeout_seconds"]=1
        (self.root/".acw/quality-gates.json").write_text(json.dumps(obj))
        out=self.root/".acw/evidence"/"timeout.json"
        with self.assertRaisesRegex(ValueError,"mandatory checks"):
            acw.run_checks(self.root,"light",out)
        self.assertEqual(acw.load(out)["checks"][0]["result"],"timed_out")

    def test_lock_blocks_parallel_cli(self):
        p=self.root/".acw/check-run.lock"
        import fcntl
        fd = p.open("w")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(ValueError,"Another ACW"):
                acw.run_checks(self.root,"light",self.root/".acw/evidence/checks.json")
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            fd.close()
        self.assertTrue(p.exists())

    def test_existing_project_config_not_overwritten(self):
        with self.assertRaisesRegex(ValueError,"already exists"):
            acw.init_project(self.root)

    def test_dirty_tree_has_distinct_identity(self):
        before=acw.repository_state(self.root)
        (self.root/"README.md").write_text("# Revised\n")
        after=acw.repository_state(self.root)
        self.assertTrue(after["dirty"])
        self.assertNotEqual(before["tree_digest"],after["tree_digest"])

if __name__ == "__main__":
    unittest.main()
