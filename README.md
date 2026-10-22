# list-diff

> Compare two line-based lists: what's only in A, only in B, or in both — with CI-friendly exit codes and JSON output. Daily Tools #16.

## Why

Comparing two lists is a daily chore: which hosts were added after maintenance,
which packages changed between deploys, which emails are new this month. The
closest tools fall short: Unix `comm` is POSIX-only (no Windows), has no
normalization (a trailing space counts as a different line), no JSON output,
and always exits 0 — useless as a CI gate. Raw `diff` compares line *positions*,
not list *membership*. list-diff is cross-platform, normalizes noise
(case, whitespace, blank lines, comment lines), emits machine-readable JSON,
and exits 0 when the lists match, 1 when they differ, 2 on error — so a CI job
can fail on drift with a single line.

## Install

```bash
git clone https://github.com/Kayzenn123/list-diff.git
cd list-diff
# no dependencies — Python standard library only
```

Requires: Python >= 3.9

## Usage

```bash
python3 list_diff.py --help
python3 list_diff.py old.txt new.txt
python3 list_diff.py old.txt new.txt --ignore-case --json
python3 list_diff.py old.txt new.txt --quiet && echo "lists match"
```

| Flag | Function | Default |
| --- | --- | --- |
| `-i, --ignore-case` | Compare case-insensitively | off |
| `--no-strip` | Do not strip leading/trailing whitespace | strip on |
| `--keep-blank` | Do not skip blank lines | blanks skipped |
| `--comment PREFIX` | Skip lines starting with PREFIX (e.g. `#`) | none |
| `--no-dedupe` | Compare as multisets (count duplicate lines) | dedupe on |
| `--json` | Machine-readable JSON output | text report |
| `-q, --quiet` | Print nothing; exit code only | off |
| `--sort` | Sort output items alphabetically | input order |
| `--only-a / --only-b / --common` | Show only that section | all sections |

Exit codes: `0` = lists identical, `1` = differences found, `2` = error (bad arguments, unreadable file). Either input may be `-` for stdin (not both).

## Example output

Command:

```bash
python3 list_diff.py hosts-before.txt hosts-after.txt
```

Output (real, copied from an actual run):

```text
Only in hosts-before.txt (1):
  cache-01
Only in hosts-after.txt (1):
  db-02
In both (4):
  web-01
  web-02
  db-01
  worker-01
```

Exit code was `1` (differences found). With `--ignore-case --json` on two
`pip freeze` snapshots the same tool produces parseable JSON, e.g.:

```bash
python3 list_diff.py freeze-before.txt freeze-after.txt --ignore-case --json
```

```text
{
  "a": {
    "label": "freeze-before.txt",
    "total": 4
  },
  "b": {
    "label": "freeze-after.txt",
    "total": 4
  },
  "only_a": [
    "requests==2.31.0",
    "psycopg2-binary==2.9.9"
  ],
  "only_b": [
    "requests==2.32.3",
    "redis==5.0.1"
  ],
  "common": [
    "Django==4.2.7",
    "gunicorn==21.2.0"
  ],
  "counts": {
    "a": 4,
    "b": 4,
    "only_a": 2,
    "only_b": 2,
    "common": 2
  },
  "identical": false
}
```

## How it works

1. Read both inputs (file or stdin) as text lines; `\r\n` and `\n` are treated the same.
2. Normalize each line: strip whitespace, drop blank lines, drop comment lines,
   optionally casefold — while remembering the first-seen display form.
3. Deduplicate per list (unless `--no-dedupe`, which does a multiset comparison
   counting extra occurrences).
4. Compute set differences in stable first-seen order and render text or JSON.
5. Exit 0/1/2 per the Usage table above.

Structure: single file `list_diff.py` — pure functions `normalize`, `compare`,
`format_text`, `format_json` separated from argparse I/O in `main`.
Tests live in `test/` and run with `python3 -m unittest discover -s test`.

## Limitations

- Line-based only: multi-line records and CSV-aware column comparison are out of scope.
- No fuzzy matching — `web-01` vs `web-01 ` (trailing space) match only with the default strip on; typos are different items.
- `--ignore-case` compares case-insensitively but displays the first-seen casing, which may look inconsistent.
- `--no-dedupe` multiset mode counts occurrences, not positions: reordered duplicates are still identical.
- Files are read fully into memory; each line is one item (no streaming mode).

## Development

```bash
python3 -m unittest discover -s test -q
```

## License

MIT

---
Ringkasan (Bahasa Indonesia): list-diff membandingkan dua daftar baris dan melaporkan item yang hanya ada di daftar A, hanya di B, atau di keduanya, lengkap dengan normalisasi (huruf besar/kecil, spasi, baris kosong, komentar), output JSON, dan exit code 0/1/2 yang cocok dipakai sebagai gate di CI. Cara pakai: `python3 list_diff.py lama.txt baru.txt`. Batasan utama: hanya per-baris (bukan CSV multi-kolom), tanpa pencocokan fuzzy, dan file dibaca seluruhnya ke memori.
