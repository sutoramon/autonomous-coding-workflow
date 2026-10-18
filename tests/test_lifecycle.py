"""Regression coverage for completion, metadata identity, safety and CLI wiring."""
import contextlib
import fcntl
import io
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


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "app"
        self.root.mkdir()
        subprocess.run(["git","init","-q",str(self.root)],check=True)
        subprocess.run(["git","-C",str(self.root),"config","user.name","ACW Tester"],check=True)
        subprocess.run(["git","-C",str(self.root),"config","user.email","acw@example.invalid"],check=True)
        (self.root/"README.md").write_text("# Test project\n")
        acw.init_project(self.root)
        self.config = self.root/".acw/project.json"
        self.gates = self.root/".acw/quality-gates.json"
        project=acw.load(self.config)
        project["project"]="Example app"
        self.config.write_text(json.dumps(project))
        self.set_gates(["python3","-c","print('passed')"])
        self.taskfile=self.root/".acw/tasks/TASK-EXAMPLE.json"
        task=acw.load(self.taskfile)
        task["acceptance"]=["API returns the expected response."]
        task["next_action"]="Run verification and close task."
        self.taskfile.write_text(json.dumps(task))
        self.commit("baseline")
        self.cli=Path(acw.__file__).resolve()

    def commit(self, msg):
        subprocess.run(["git","-C",str(self.root),"add","."],check=True)
        subprocess.run(["git","-C",str(self.root),"commit","-qm",msg],check=True)

    def set_gates(self, argv, timeout=5, required=None):
        self.gates.write_text(json.dumps({"schema_version":1,"checks":[
            {"id":"sample-check","argv":argv,"timeout_seconds":timeout,"required_for":required or ["light"]}
        ]}))

    def run_cli(self,*args):
        return subprocess.run([sys.executable,"-B",str(self.cli),*map(str,args)],
                              cwd=self.root,capture_output=True,text=True,timeout=20)

    def test_done_task_cli_happy_path_after_metadata_commit(self):
        evidence=self.root/".acw/evidence/proof.json"
        acw.run_checks(self.root,"critical",evidence) # cumulative from light
        checked=acw.repository_state(self.root)
        task=acw.load(self.taskfile)
        task.update({"status":"done","risk":"critical","source_sha":checked["sha"],
                     "self_review":{"verdict":"passed","source_sha":checked["sha"],"findings":[]},
                     "next_action":"Task complete; start next authorized task."})
        self.taskfile.write_text(json.dumps(task))
        self.commit("record task closeout")
        current=acw.repository_state(self.root)
        self.assertNotEqual(checked["sha"],current["sha"])
        self.assertEqual(checked["tree_digest"],current["tree_digest"])
        cli=self.run_cli("task",self.taskfile,"--project",self.root,"--evidence",evidence)
        self.assertEqual(cli.returncode,0,cli.stderr)
        self.assertEqual(json.loads(cli.stdout)["status"],"PASS")
        self.assertEqual(self.run_cli("verify",evidence,"--project",self.root,"--profile","critical").returncode,0)

    def test_done_cli_without_evidence_rejected(self):
        task=acw.load(self.taskfile)
        task.update({"status":"done","source_sha":acw.repository_state(self.root)["sha"],
                     "self_review":{"verdict":"passed","source_sha":acw.repository_state(self.root)["sha"]}})
        self.taskfile.write_text(json.dumps(task))
        cli=self.run_cli("task",self.taskfile,"--project",self.root)
        self.assertNotEqual(cli.returncode,0)
        self.assertIn("--evidence",cli.stderr)

    def test_old_log_preserved_and_hash_verified(self):
        first=self.root/".acw/evidence/first.json"
        second=self.root/".acw/evidence/second.json"
        acw.run_checks(self.root,"standard",first)
        old=acw.load(first)["checks"][0]
        original=(self.root/old["log"]).read_bytes()
        acw.run_checks(self.root,"standard",second)
        newer=acw.load(second)["checks"][0]
        self.assertNotEqual(old["log"],newer["log"])
        self.assertEqual(original,(self.root/old["log"]).read_bytes())
        (self.root/old["log"]).write_text("tampered")
        with self.assertRaisesRegex(ValueError,"checksum mismatch"):
            acw.validate_evidence(acw.load(first),self.root,"standard")
        self.assertTrue(acw.validate_evidence(acw.load(second),self.root,"standard"))

    def test_timeout_kills_background_descendant(self):
        pidfile=self.root/".acw/evidence/descendant.pid"
        # backgrounded child inherits process group but not child's foreground lifetime
        script='sleep 30 & echo $! > "'+str(pidfile)+'"; wait'
        self.set_gates(["sh","-c",script],timeout=1)
        proof=self.root/".acw/evidence/timeouts.json"
        with self.assertRaisesRegex(ValueError,"mandatory checks"):
            acw.run_checks(self.root,"light",proof)
        self.assertEqual(acw.load(proof)["checks"][0]["result"],"timed_out")
        pid=int(pidfile.read_text().strip())
        # Linux may briefly retain a zombie; absence of an active process is the invariant.
        for _ in range(30):
            try:
                state=Path(f"/proc/{pid}/stat").read_text().split()[2]
            except FileNotFoundError:
                break
            if state=="Z":
                break
            time.sleep(.05)
        else:
            self.fail("Timed-out background child still running")

    def test_unlock_after_unexpected_process_death(self):
        lock=self.root/".acw/check-run.lock"
        lock.write_text("dead process id")
        report=self.root/".acw/evidence/checks.json"
        self.assertEqual(acw.run_checks(self.root,"light",report)["status"],"PASS")
        self.assertTrue(lock.exists())

    def test_manifest_write_roundtrip_and_cache_ignore(self):
        package=Path(acw.__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            from shutil import copytree
            out=Path(td)/"package"
            copytree(package,out,ignore=lambda d,n:{".git","__pycache__"}.intersection(n))
            (out/".pytest_cache").mkdir()
            (out/".pytest_cache/state").write_text("cache")
            self.assertEqual(acw.write_manifest(out)["status"],"WRITTEN")
            self.assertEqual(acw.package(out)["status"],"PASS")
            (out/"README.md").write_text("changed")
            with self.assertRaisesRegex(ValueError,"checksum mismatch"):
                acw.package(out)
            result=self.run_cli("manifest",out,"--write")
            self.assertEqual(result.returncode,0,result.stderr)

    def test_cumulative_profiles_include_earlier_checks(self):
        checks={"schema_version":1,"checks":[
            {"id":"light-gate","argv":["true"],"timeout_seconds":5,"required_for":["light"]},
            {"id":"standard-gate","argv":["true"],"timeout_seconds":5,"required_for":["standard"]},
            {"id":"critical-gate","argv":["true"],"timeout_seconds":5,"required_for":["critical"]}
        ]}
        acw.validate_gates(checks)
        self.assertEqual(acw.required_ids(checks,"critical"),["critical-gate","light-gate","standard-gate"])

    def test_placeholder_or_empty_action_rejected(self):
        task=acw.load(self.taskfile)
        task["next_action"]="  "
        with self.assertRaisesRegex(ValueError,"concrete"):
            acw.validate_task(task)
        task["next_action"]="TODO"
        with self.assertRaisesRegex(ValueError,"concrete"):
            acw.validate_task(task)

    def test_no_commit_repo_has_clear_error(self):
        root=Path(self.temp.name)/"empty"
        root.mkdir()
        subprocess.run(["git","init","-q",str(root)],check=True)
        with self.assertRaisesRegex(ValueError,"no commits"):
            acw.repository_state(root)

    def test_cli_project_and_failure_json(self):
        good=self.run_cli("project",self.root)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertEqual(json.loads(good.stdout)["status"],"PASS")
        bad=self.run_cli("task",self.taskfile,"--project",self.root)
        # initial task has valid acceptance and action
        self.assertEqual(bad.returncode,0,bad.stderr)
        task=acw.load(self.taskfile)
        task["next_action"]=""
        self.taskfile.write_text(json.dumps(task))
        error=self.run_cli("task",self.taskfile,"--project",self.root)
        self.assertEqual(error.returncode,1)
        self.assertEqual(json.loads(error.stderr)["status"],"FAIL")

if __name__=="__main__":
    unittest.main()
