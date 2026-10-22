#!/usr/bin/env python3
"""list-diff: compare two line-based lists and report the difference.

Compares two lists (files, or one file and stdin) and reports which items are
only in A, only in B, or in both. Supports normalization (case, whitespace,
blank lines, comment lines), machine-readable JSON output, and meaningful exit
codes for CI: 0 = identical, 1 = differences found, 2 = error.

Standard library only. Python 3.9+.
"""

import argparse
import json
import os
import sys

VERSION = "1.0.0"
PROG = "list-diff"


class ListDiffError(Exception):
    """A user-facing error (bad input, unreadable file)."""


def read_source(path, label):
    """Read lines from a file path, or from stdin when path == '-'."""
    if path == "-":
        try:
            return sys.stdin.read().splitlines(), label
        except OSError as exc:
            raise ListDiffError("cannot read stdin: %s" % exc)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read().splitlines(), label
    except FileNotFoundError:
        raise ListDiffError("file not found: %s" % path)
    except IsADirectoryError:
        raise ListDiffError("not a file: %s" % path)
    except OSError as exc:
        raise ListDiffError("cannot read %s: %s" % (path, exc))


def normalize(raw_lines, ignore_case=False, strip=True,
              ignore_blank=True, comment=None, dedupe=True):
    """Normalize raw lines into a list of (key, display) pairs.

    key is used for comparison; display is the first-seen human form.
    With dedupe=True each distinct key appears once (first-seen order).
    """
    pairs = []
    seen = set()
    for line in raw_lines:
        text = line.strip() if strip else line
        if ignore_blank and text == "":
            continue
        if comment and text.startswith(comment):
            continue
        key = text.casefold() if ignore_case else text
        if dedupe:
            if key in seen:
                continue
            seen.add(key)
        pairs.append((key, text))
    return pairs


def compare(pairs_a, pairs_b, dedupe=True):
    """Compare two normalized pair lists.

    Returns a dict with only_a / only_b / common (display values, first-seen
    order) plus counts. With dedupe=False this is a multiset comparison:
    an item appearing more times in A than in B shows up the extra times in
    only_a.
    """
    if dedupe:
        keys_a = {k for k, _ in pairs_a}
        keys_b = {k for k, _ in pairs_b}
        disp_a = {k: v for k, v in pairs_a}
        disp_b = {k: v for k, v in pairs_b}
        only_a = [disp_a[k] for k, _ in pairs_a if k not in keys_b]
        only_b = [disp_b[k] for k, _ in pairs_b if k not in keys_a]
        common = [disp_a[k] for k, _ in pairs_a if k in keys_b]
    else:
        from collections import Counter
        ca = Counter(k for k, _ in pairs_a)
        cb = Counter(k for k, _ in pairs_b)
        disp_a = {k: v for k, v in pairs_a}
        disp_b = {k: v for k, v in pairs_b}
        only_a, only_b, common = [], [], []
        # multiset walk: emit shared and extra copies in first-seen order
        done = set()
        for k, _ in pairs_a:
            if k in done:
                continue
            done.add(k)
            shared = min(ca[k], cb[k])
            if shared:
                common.extend([disp_a[k]] * shared)
            extra = ca[k] - cb[k]
            if extra > 0:
                only_a.extend([disp_a[k]] * extra)
        for k, _ in pairs_b:
            if k in done:
                continue
            done.add(k)
            extra = cb[k] - ca[k]
            if extra > 0:
                only_b.extend([disp_b[k]] * extra)
    return {
        "only_a": only_a,
        "only_b": only_b,
        "common": common,
        "counts": {
            "a": len(pairs_a),
            "b": len(pairs_b),
            "only_a": len(only_a),
            "only_b": len(only_b),
            "common": len(common),
        },
        "identical": not only_a and not only_b,
    }


def format_text(result, label_a, label_b, sections, use_color, sort):
    """Human-readable report. sections is a subset of ('only_a','only_b','common')."""
    lines = []
    headers = {
        "only_a": "Only in %s" % label_a,
        "only_b": "Only in %s" % label_b,
        "common": "In both",
    }
    for sec in ("only_a", "only_b", "common"):
        if sec not in sections:
            continue
        items = result[sec]
        if sort:
            items = sorted(items)
        head = "%s (%d):" % (headers[sec], len(items))
        if use_color:
            head = "\033[1;36m%s\033[0m" % head
        lines.append(head)
        lines.extend("  %s" % item for item in items)
    return "\n".join(lines) + ("\n" if lines else "")


def format_json(result, label_a, label_b, sort):
    payload = {
        "a": {"label": label_a, "total": result["counts"]["a"]},
        "b": {"label": label_b, "total": result["counts"]["b"]},
        "only_a": sorted(result["only_a"]) if sort else result["only_a"],
        "only_b": sorted(result["only_b"]) if sort else result["only_b"],
        "common": sorted(result["common"]) if sort else result["common"],
        "counts": result["counts"],
        "identical": result["identical"],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def build_parser():
    p = argparse.ArgumentParser(
        prog=PROG,
        description="Compare two line-based lists: report items only in A, "
                    "only in B, or in both. Exit 0 = identical, "
                    "1 = differences, 2 = error.",
    )
    p.add_argument("file_a", help="first list file ('-' reads stdin)")
    p.add_argument("file_b", help="second list file ('-' reads stdin)")
    p.add_argument("--version", action="version", version="%(prog)s " + VERSION)
    p.add_argument("-i", "--ignore-case", action="store_true",
                   help="compare case-insensitively")
    p.add_argument("--no-strip", action="store_true",
                   help="do not strip leading/trailing whitespace")
    p.add_argument("--keep-blank", action="store_true",
                   help="do not skip blank lines")
    p.add_argument("--comment", metavar="PREFIX", default=None,
                   help="skip lines starting with PREFIX (e.g. '#')")
    p.add_argument("--no-dedupe", action="store_true",
                   help="compare as multisets (count duplicates)")
    p.add_argument("--json", action="store_true",
                   help="machine-readable JSON output")
    p.add_argument("-q", "--quiet", action="store_true",
                   help="print nothing; only the exit code matters")
    p.add_argument("--sort", action="store_true",
                   help="sort output items alphabetically")
    sel = p.add_argument_group("output sections (default: all)")
    sel.add_argument("--only-a", action="store_true", help="show only items in A")
    sel.add_argument("--only-b", action="store_true", help="show only items in B")
    sel.add_argument("--common", action="store_true", help="show only common items")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.file_a == "-" and args.file_b == "-":
        parser.error("only one input may be stdin ('-')")

    label_a = "stdin" if args.file_a == "-" else os.path.basename(args.file_a) or args.file_a
    label_b = "stdin" if args.file_b == "-" else os.path.basename(args.file_b) or args.file_b

    try:
        raw_a, _ = read_source(args.file_a, label_a)
        raw_b, _ = read_source(args.file_b, label_b)
    except ListDiffError as exc:
        print("%s: error: %s" % (PROG, exc), file=sys.stderr)
        return 2

    norm = dict(ignore_case=args.ignore_case, strip=not args.no_strip,
                ignore_blank=not args.keep_blank, comment=args.comment,
                dedupe=not args.no_dedupe)
    pairs_a = normalize(raw_a, **norm)
    pairs_b = normalize(raw_b, **norm)
    result = compare(pairs_a, pairs_b, dedupe=not args.no_dedupe)

    selectors = [s for s, on in (("only_a", args.only_a),
                                 ("only_b", args.only_b),
                                 ("common", args.common)) if on]
    sections = selectors or ["only_a", "only_b", "common"]

    if not args.quiet:
        use_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
        try:
            if args.json:
                out = format_json(result, label_a, label_b, args.sort)
            else:
                out = format_text(result, label_a, label_b, sections,
                                  use_color, args.sort)
            sys.stdout.write(out)
        except BrokenPipeError:
            # Downstream closed the pipe (e.g. `| head`); not an error.
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
            return 0

    return 0 if result["identical"] else 1


if __name__ == "__main__":
    sys.exit(main())
