"""Check a pull request title and render the comment that helps the author fix it."""

import argparse
import re
import sys
from pathlib import Path

from title_grammar import TitleError, check_title, suggest_title

MARKER = "<!-- cryptobib-title-check -->"

FORMS = (
    (
        "`add(data): ...`",
        "new venues, volumes, entries",
        "`add(data): FC 2025, FCW 2025, ICISC 2025`",
    ),
    (
        "`fix(data): ...`",
        "corrections to existing entries",
        "`fix(data): title of EC:CFSY96`",
    ),
    (
        "`add(data)!: ...`, `fix(data)!: ...`",
        "a change that can break a user's document, such as renamed or removed keys",
        "`fix(data)!: rename keys of entries with more than six authors`",
    ),
    (
        "`type(scope): ...`",
        "any other change. The scope is optional.",
        "`ci: cache the bibtex8 binary`",
    ),
)


def fenced(text: str) -> str:
    """Return text in a code block whose fence is longer than any backtick run in it."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(4, longest + 1)
    return f"{fence}\n{text}\n{fence}"


def render_failure(title: str, files: list[str], error: TitleError) -> str:
    table = "\n".join(f"| {form} | {use} | {example} |" for form, use, example in FORMS)
    return f"""{MARKER}
{error}

Suggested title:

{fenced(suggest_title(title, files))}

| Form | Use | Example |
|---|---|---|
{table}

To change the title, edit the pull request title. The check runs again.
"""


def render_success() -> str:
    return f"{MARKER}\nThe pull request title follows the format.\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument(
        "--files-from", required=True, help="file with one changed path per line"
    )
    parser.add_argument("--comment-out", help="write the comment body to this file")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        return exit_.code if isinstance(exit_.code, int) else 2
    try:
        files = Path(args.files_from).read_text().splitlines()
    except OSError as exc:
        print(f"cannot read {args.files_from}: {exc}", file=sys.stderr)
        return 2
    files = [f for f in files if f]
    try:
        check_title(args.title, files)
    except TitleError as error:
        comment, code = render_failure(args.title, files, error), 1
        print(error, file=sys.stderr)
    else:
        comment, code = render_success(), 0
    if args.comment_out:
        Path(args.comment_out).write_text(comment)
    return code


if __name__ == "__main__":
    sys.exit(main())
