"""Regressions for process-group lifetime and evidence/profile handling."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import acw
from test_lifecycle import LifecycleTests


class ExtraLifecycleTests(unittest.TestCase):
    setUp = LifecycleTests.setUp
    commit = LifecycleTests.commit
    set_gates = LifecycleTests.set_gates
    run_cli = LifecycleTests.run_cli

    def test_normal_success_cleans_background_process(self):
        child_pid = self.root / ".acw/evidence/child.pid"
        script = 'sleep 42 & echo $! > "' + str(child_pid) + '"; echo ok'
        self.set_gates(["sh", "-c", script])
        self.assertEqual(acw.run_checks(self.root, "light", self.root/".acw/evidence/pass.json")["status"], "PASS")
        pid = int(child_pid.read_text())
        self.assertFalse(_active(pid), f"Background sleep {pid} remained active after success")

    def test_interrupt_persists_partial_evidence_and_cleans_process_group(self):
        child_pid = self.root / ".acw/evidence/child.pid"
        script = 'sleep 42 & echo $! > "' + str(child_pid) + '"; wait'
        self.set_gates(["sh", "-c", script], timeout=60)
        output = self.root / ".acw/evidence/interrupted.json"
        # Simulate Ctrl+C to the runner after its child is definitely running.
        cmd = [sys.executable, "-B", str(self.cli), "run", str(self.root),
               "--profile", "light", "--output", str(output)]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        try:
            for _ in range(100):
                if child_pid.exists():
                    break
                time.sleep(.03)
            self.assertTrue(child_pid.exists(), "Gate never started")
            os.kill(proc.pid, 2) # SIGINT
            proc.communicate(timeout=7)
            self.assertNotEqual(proc.returncode, 0)
            self.assertTrue(output.exists(), "Evidence was lost on Ctrl+C")
            report = acw.load(output)
            self.assertFalse(report["complete"])
            self.assertEqual(report["checks"][0]["result"], "interrupted")
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                acw.validate_evidence(report, self.root, "light")
            self.assertFalse(_active(int(child_pid.read_text())), "Orphan survived Ctrl+C")
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()

    def test_valid_acceptance_with_angle_brackets_and_todo(self):
        task = acw.load(self.taskfile)
        task["acceptance"] = [
            "HTTP 200 when x < 5 and y > 3",
            "List<String> is returned",
            "Render the <Button> component",
            "Fix the TODO list feature",
        ]
        self.assertTrue(acw.validate_task(task))
        for placeholder in ["<your-criterion>", "{{TODO}}", "TODO: implement later", "Replace this criterion"]:
            task["acceptance"] = [placeholder]
            with self.subTest(placeholder=placeholder), self.assertRaisesRegex(ValueError, "placeholder"):
                acw.validate_task(task)

    def test_higher_profile_evidence_validates_lower_risk_task(self):
        output = self.root / ".acw/evidence/critical.json"
        acw.run_checks(self.root, "critical", output)
        source = acw.repository_state(self.root)["sha"]
        task = acw.load(self.taskfile)
        task.update({"status": "done", "risk": "light", "source_sha": source,
                     "self_review": {"verdict": "passed", "source_sha": source, "findings": []}})
        self.assertTrue(acw.validate_task(task, root=self.root, evidence=acw.load(output)))
        with self.assertRaisesRegex(ValueError, "profile"):
            acw.validate_evidence(acw.load(output), self.root, "invalid")

    def test_unexpected_exception_records_evidence(self):
        # Verify interruption path also works for unexpected faults after log directory creation.
        from unittest.mock import patch
        import acw_runner
        out = self.root/".acw/evidence/error.json"
        with patch.object(acw_runner, "_execute_check", side_effect=RuntimeError("injected failure")):
            with self.assertRaisesRegex(RuntimeError, "injected"):
                acw.run_checks(self.root, "light", out)
        self.assertTrue(out.exists())
        self.assertEqual(acw.load(out)["checks"], [])
        self.assertFalse(acw.load(out)["complete"])


def _active(pid):
    try:
        state = Path(f"/proc/{pid}/stat").read_text().split()[2]
        return state != "Z"
    except FileNotFoundError:
        return False


if __name__ == "__main__":
    unittest.main()
