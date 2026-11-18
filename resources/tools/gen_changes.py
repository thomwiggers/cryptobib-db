"""Generate changes.txt from the git history and changes-archive.txt.

The commits after the cutoff (the first-parent commit that adds changes-archive.txt)
become dated blocks, newest date first, followed by the archive verbatim.
A merge without a pull request title is replaced by the commits it brings in, so changes
made in the merge commit itself, such as a conflict resolution, are not listed.
"""

import argparse
import datetime
import re
import subprocess
import sys
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from title_grammar import TitleError, parse_title, touches_data

ARCHIVE = "changes-archive.txt"
OUTPUT = "changes.txt"
CATEGORIES = ("Breaking", "Added", "Fixed", "Other")
ROOT = Path(__file__).resolve().parents[2]

_PR_MERGE = re.compile(r"Merge pull request #(\d+) from ")
_PR_SUFFIX = re.compile(r"(?P<title>.*) \(#(?P<pr>\d+)\)")
# Settings from the user's configuration that change the output of the commands below.
_CONFIG = ("-c", "log.showSignature=false", "-c", "core.quotePath=false")


class HistoryError(RuntimeError):
    """The history cannot produce the changelog: no git, a shallow clone, or no cutoff."""


@dataclass(frozen=True)
class Entry:
    date: datetime.date
    category: str
    text: str
    pr: int | None


@dataclass(frozen=True)
class _Commit:
    sha: str
    parents: list[str]
    subject: str
    body: str
    timestamp: int


def _git(repo: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *_CONFIG, *args],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError as e:
        raise HistoryError(f"Cannot run git: {e}") from e
    if result.returncode != 0:
        raise HistoryError(
            f"git {' '.join(args)} failed: {result.stderr.strip() or result.returncode}"
        )
    return result.stdout


def find_cutoff(repo: Path) -> str:
    lines = _git(
        repo,
        "log",
        "--first-parent",
        "--diff-merges=first-parent",
        "--no-patch",
        "--no-renames",
        "--diff-filter=A",
        "--format=%H",
        "--",
        ARCHIVE,
    ).split()
    if not lines:
        raise HistoryError(f"No commit adds {ARCHIVE}, so there is no cutoff.")
    return lines[-1]


def _commit(repo: Path, sha: str) -> _Commit:
    fields = _git(repo, "show", "-s", "--format=%P%x00%s%x00%b%x00%ct", sha)
    parents, subject, body, timestamp = fields.split("\0")
    return _Commit(sha, parents.split(), subject, body, int(timestamp))


def _changed_files(repo: Path, commit: _Commit) -> list[str]:
    if commit.parents:
        args = ["diff", "--no-ext-diff", commit.parents[0], commit.sha]
    else:
        args = ["diff-tree", "-r", "--root", "--no-commit-id", commit.sha]
    out = _git(repo, *args, "--name-only", "--no-renames", "-z", "--")
    return [name for name in out.split("\0") if name]


def _first_parents(repo: Path, tip: str, excluded: Iterable[str]) -> list[str]:
    """The first-parent chain of tip, oldest first, without commits reachable from excluded."""
    negated = [f"^{sha}" for sha in excluded]
    return _git(
        repo, "rev-list", "--first-parent", "--reverse", tip, *negated, "--"
    ).split()


def _title(commit: _Commit) -> tuple[str, int | None] | None:
    """The title and pull request number, or None for a merge without a title."""
    text, pr = commit.subject, None
    if len(commit.parents) > 1:
        merge = _PR_MERGE.match(commit.subject)
        lines = commit.body.strip().splitlines()
        if merge is None or not lines:
            return None
        text, pr = lines[0].strip(), int(merge[1])
    suffix = _PR_SUFFIX.fullmatch(text)
    if suffix:
        text = suffix["title"]
        pr = int(suffix["pr"]) if pr is None else pr
    return text, pr


def _entries(
    repo: Path, sha: str, date: datetime.date | None, excluded: tuple[str, ...]
) -> list[Entry]:
    """Entries of one commit; a merge without a title becomes the commits it brings in.

    excluded holds the commits whose ancestors are already listed elsewhere in this run.
    """
    commit = _commit(repo, sha)
    if date is None:
        date = datetime.datetime.fromtimestamp(commit.timestamp, datetime.UTC).date()
    titled = _title(commit)
    if titled is None:
        seen = [*excluded, commit.parents[0]]
        entries = []
        for parent in commit.parents[1:]:
            for side in _first_parents(repo, parent, seen):
                entries += _entries(repo, side, date, tuple(seen))
            seen.append(parent)
        return entries
    title, pr = titled
    try:
        parsed = parse_title(title)
    except TitleError:
        parsed = None
    if parsed is not None and parsed.scope == "data":
        if parsed.breaking:
            category = "Breaking"
        else:
            category = "Added" if parsed.type == "add" else "Fixed"
        return [Entry(date, category, parsed.description, pr)]
    if touches_data(_changed_files(repo, commit)):
        return [Entry(date, "Other", title, pr)]
    return []


def read_entries(repo: Path) -> list[Entry]:
    if _git(repo, "rev-parse", "--is-shallow-repository").strip() == "true":
        raise HistoryError(
            "The repository is a shallow clone. Fetch the full history first "
            "(git fetch --unshallow)."
        )
    cutoff = find_cutoff(repo)
    return [
        entry
        for sha in _first_parents(repo, "HEAD", [cutoff])
        for entry in _entries(repo, sha, None, ())
    ]


def render(entries: list[Entry]) -> str:
    days: dict[datetime.date, dict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for entry in entries:
        text = entry.text if entry.pr is None else f"{entry.text} (#{entry.pr})"
        days[entry.date][entry.category].append(text)
    blocks = []
    for date in sorted(days, reverse=True):
        lines = [f"* {date.isoformat()}"]
        lines += [
            f"{category}: {'; '.join(days[date][category])}"
            for category in CATEGORIES
            if category in days[date]
        ]
        blocks.append("\n".join(lines) + "\n\n")
    return "".join(blocks)


def generate(repo: Path) -> bytes:
    entries = read_entries(repo)
    try:
        archive = (repo / ARCHIVE).read_bytes()
    except OSError as e:
        raise HistoryError(f"Cannot read {ARCHIVE}: {e}") from e
    return render(entries).encode("utf-8") + archive


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    try:
        content = generate(ROOT)
    except HistoryError as e:
        print(f"gen_changes: {e}", file=sys.stderr)
        return 1
    (ROOT / OUTPUT).write_bytes(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
