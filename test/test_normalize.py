import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from list_diff import normalize


class TestNormalize(unittest.TestCase):
    def test_strip_and_blank_by_default(self):
        pairs = normalize(["  alpha  ", "", "   ", "beta"])
        self.assertEqual([k for k, _ in pairs], ["alpha", "beta"])
        self.assertEqual([v for _, v in pairs], ["alpha", "beta"])

    def test_no_strip_keeps_whitespace(self):
        pairs = normalize(["  alpha  ", "beta"], strip=False, ignore_blank=False)
        self.assertEqual([k for k, _ in pairs], ["  alpha  ", "beta"])

    def test_keep_blank_keeps_empty_lines(self):
        pairs = normalize(["a", "", "b"], ignore_blank=False)
        self.assertEqual([k for k, _ in pairs], ["a", "", "b"])

    def test_ignore_case(self):
        pairs = normalize(["Alpha", "ALPHA", "beta"], ignore_case=True)
        self.assertEqual([k for k, _ in pairs], ["alpha", "beta"])
        # display keeps the first-seen original form
        self.assertEqual([v for _, v in pairs], ["Alpha", "beta"])

    def test_comment_prefix(self):
        pairs = normalize(["# header", "alpha", "  # indented", "beta"],
                          comment="#")
        self.assertEqual([k for k, _ in pairs], ["alpha", "beta"])

    def test_dedupe_first_seen_order(self):
        pairs = normalize(["b", "a", "b", "a", "c"])
        self.assertEqual([k for k, _ in pairs], ["b", "a", "c"])

    def test_no_dedupe_keeps_duplicates(self):
        pairs = normalize(["b", "a", "b"], dedupe=False)
        self.assertEqual([k for k, _ in pairs], ["b", "a", "b"])


if __name__ == "__main__":
    unittest.main()
