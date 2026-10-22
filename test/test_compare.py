import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from list_diff import compare, normalize


def n(lines, **kw):
    return normalize(lines, **kw)


class TestCompare(unittest.TestCase):
    def test_basic_set_diff(self):
        r = compare(n(["a", "b", "c"]), n(["b", "c", "d"]))
        self.assertEqual(r["only_a"], ["a"])
        self.assertEqual(r["only_b"], ["d"])
        self.assertEqual(r["common"], ["b", "c"])
        self.assertFalse(r["identical"])
        self.assertEqual(r["counts"],
                         {"a": 3, "b": 3, "only_a": 1, "only_b": 1, "common": 2})

    def test_identical(self):
        r = compare(n(["x", "y"]), n(["y", "x"]))
        self.assertTrue(r["identical"])
        self.assertEqual(r["only_a"], [])
        self.assertEqual(r["only_b"], [])
        self.assertEqual(sorted(r["common"]), ["x", "y"])

    def test_both_empty(self):
        r = compare(n([]), n([]))
        self.assertTrue(r["identical"])
        self.assertEqual(r["counts"]["a"], 0)

    def test_one_side_empty(self):
        r = compare(n(["a", "b"]), n([]))
        self.assertEqual(r["only_a"], ["a", "b"])
        self.assertEqual(r["only_b"], [])
        self.assertFalse(r["identical"])

    def test_multiset_extra_occurrences(self):
        r = compare(n(["a", "a", "b"], dedupe=False),
                    n(["a", "b"], dedupe=False), dedupe=False)
        self.assertEqual(r["only_a"], ["a"])  # one extra "a"
        self.assertEqual(r["only_b"], [])
        self.assertEqual(sorted(r["common"]), ["a", "b"])
        self.assertFalse(r["identical"])

    def test_multiset_identical_counts(self):
        r = compare(n(["a", "a", "b"], dedupe=False),
                    n(["b", "a", "a"], dedupe=False), dedupe=False)
        self.assertTrue(r["identical"])

    def test_casefold_keys_still_first_seen_display(self):
        r = compare(n(["Web Server"], ignore_case=True),
                    n(["web server"], ignore_case=True))
        self.assertTrue(r["identical"])
        self.assertEqual(r["common"], ["Web Server"])


if __name__ == "__main__":
    unittest.main()
