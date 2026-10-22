import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "list_diff.py")


def run(args, stdin_text=None):
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for i, text in enumerate(args.pop("files")):
            p = os.path.join(tmp, "f%d.txt" % i)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(text)
            paths.append(p)
        cmd = [sys.executable, SCRIPT] + paths + args.pop("flags")
        proc = subprocess.run(cmd, input=stdin_text, capture_output=True,
                              text=True, timeout=30, env={**os.environ,
                                                          "NO_COLOR": "1"})
        return proc


class TestEndToEnd(unittest.TestCase):
    def test_e2e_text_exit_1(self):
        proc = run({"files": ["web1\ndb1\ncache1\n", "web1\ndb1\ndb2\n"],
                    "flags": []})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Only in f0.txt (1):", proc.stdout)
        self.assertIn("cache1", proc.stdout)
        self.assertIn("Only in f1.txt (1):", proc.stdout)
        self.assertIn("db2", proc.stdout)

    def test_e2e_identical_exit_0(self):
        proc = run({"files": ["a\nb\nc\n", "c\nb\na\n"], "flags": []})
        self.assertEqual(proc.returncode, 0)
        self.assertIn("In both (3):", proc.stdout)

    def test_e2e_json_parseable(self):
        proc = run({"files": ["# hosts\nalpha\nBETA\n", "alpha\nbeta\n"],
                    "flags": ["--ignore-case", "--comment", "#", "--json"]})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["identical"])
        self.assertEqual(sorted(payload["common"]), ["BETA", "alpha"])

    def test_e2e_quiet_and_stdin(self):
        proc = run({"files": ["only-this\n"], "flags": ["-", "--quiet"]},
                   stdin_text="only-this\nother\n")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")

    def test_e2e_version(self):
        proc = subprocess.run([sys.executable, SCRIPT, "--version"],
                              capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("1.0.0", proc.stdout)


if __name__ == "__main__":
    unittest.main()
