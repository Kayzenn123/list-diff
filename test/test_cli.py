import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from list_diff import compare, format_json, format_text, main, normalize


class TestFormat(unittest.TestCase):
    def setUp(self):
        self.result = compare(normalize(["a", "b"]), normalize(["b", "c"]))

    def test_text_all_sections(self):
        out = format_text(self.result, "old.txt", "new.txt",
                          ["only_a", "only_b", "common"], False, False)
        self.assertIn("Only in old.txt (1):", out)
        self.assertIn("Only in new.txt (1):", out)
        self.assertIn("In both (1):", out)
        self.assertIn("  a", out)
        self.assertIn("  c", out)

    def test_text_section_filter(self):
        out = format_text(self.result, "a", "b", ["only_a"], False, False)
        self.assertIn("Only in a (1):", out)
        self.assertNotIn("Only in b", out)
        self.assertNotIn("In both", out)

    def test_text_sorted(self):
        r = compare(normalize(["z", "m"]), normalize(["q"]))
        out = format_text(r, "a", "b", ["only_a"], False, True)
        lines = [l.strip() for l in out.splitlines() if l.startswith("  ")]
        self.assertEqual(lines, ["m", "z"])

    def test_no_color_by_default_flag_off(self):
        out = format_text(self.result, "a", "b",
                          ["only_a"], False, False)
        self.assertNotIn("\033[", out)

    def test_json_structure_parseable(self):
        out = format_json(self.result, "old.txt", "new.txt", False)
        payload = json.loads(out)
        self.assertEqual(payload["only_a"], ["a"])
        self.assertEqual(payload["only_b"], ["c"])
        self.assertEqual(payload["common"], ["b"])
        self.assertFalse(payload["identical"])
        self.assertEqual(payload["a"]["total"], 2)


class TestCli(unittest.TestCase):
    def test_missing_file_exit_2(self):
        err = io.StringIO()
        old = sys.stderr
        sys.stderr = err
        try:
            code = main(["/no/such/file-a.txt", "/no/such/file-b.txt"])
        finally:
            sys.stderr = old
        self.assertEqual(code, 2)
        self.assertIn("error", err.getvalue())

    def test_both_stdin_rejected(self):
        err = io.StringIO()
        old = sys.stderr
        sys.stderr = err
        try:
            with self.assertRaises(SystemExit) as ctx:
                main(["-", "-"])
        finally:
            sys.stderr = old
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("stdin", err.getvalue())

    def test_missing_arg_exits_2(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["only-one.txt"])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
