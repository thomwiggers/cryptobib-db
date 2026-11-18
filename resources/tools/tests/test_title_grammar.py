import re

import pytest
from title_grammar import (
    Title,
    TitleError,
    check_title,
    parse_title,
    suggest_title,
    touches_data,
)

VALID = [
    ("add(data): FC 2025, FCW 2025", Title("add", "data", False, "FC 2025, FCW 2025")),
    (
        "fix(data): title of EC:CFSY96",
        Title("fix", "data", False, "title of EC:CFSY96"),
    ),
    (
        "fix(data)!: rename keys of entries with more than six authors",
        Title("fix", "data", True, "rename keys of entries with more than six authors"),
    ),
    (
        "fix(tools): keep the month macros in add.py",
        Title("fix", "tools", False, "keep the month macros in add.py"),
    ),
    (
        "ci: cache the bibtex8 binary",
        Title("ci", None, False, "cache the bibtex8 binary"),
    ),
    ("  fix(data): x  ", Title("fix", "data", False, "x")),
]

INVALID = [
    ("Fixed my own last name", "type(scope): description"),
    ("Fix(data): x", "Fix"),
    ("feat(data): FC 2025", "add"),
    ("add: FC 2025", "add"),
    ("data: FC 2025", "data"),
    ("fix(data): ", "description"),
    ("fix(data):no space", "type(scope): description"),
    ("fix(data): ends with a period.", "period"),
    ("", "type(scope): description"),
]

CHECK = [
    ("fix(data): x", ["crypto_db.bib"], True),
    ("chore: x", ["crypto_db.bib"], False),
    ("fix(tools): x", ["abbrev.bibyml", "README.md"], False),
    ("fix(data): venue name", ["config.py"], True),
    ("chore: venue name", ["config.py"], True),
    ("ci: x", [".github/workflows/ci.yaml"], True),
    ("add(data): x", ["README.md"], True),
]

SUGGEST = [
    ("Fixed my own last name", ["crypto_db.bib"], "fix(data): my own last name"),
    (
        "Added FC 2025, FCW 2025.",
        ["crypto_db.bib", "abbrev.bibyml"],
        "add(data): FC 2025, FCW 2025",
    ),
    (
        "add IEEE S&P 2026 entries",
        ["crypto_db.bib"],
        "add(data): IEEE S&P 2026 entries",
    ),
    (
        "Small Typo Tapei -> Taipei",
        ["crypto_db.bib"],
        "fix(data): Small Typo Tapei -> Taipei",
    ),
    (
        "fixes capitalization of Clapoti(s)",
        ["crypto_db.bib"],
        "fix(data): capitalization of Clapoti(s)",
    ),
    ("Update the README", ["README.md"], "chore: Update the README"),
    ("chore: x", ["crypto_db.bib"], "fix(data): x"),
    ("Fix.", ["crypto_db.bib"], "fix(data): update entries"),
    ("Fixed typo in README", ["README.md"], "chore: typo in README"),
    ("Add support for X", ["README.md"], "chore: support for X"),
    ("add(tools)!: y", ["README.md"], "chore: y"),
    ("Fix.", ["README.md"], "chore: update"),
    ("feat(data): FC 2025", ["crypto_db.bib"], "fix(data): FC 2025"),
    ("feat(data): x", ["README.md"], "chore: x"),
    ("Fix(data): x", ["crypto_db.bib"], "fix(data): x"),
    ("add: FC 2025", ["crypto_db.bib"], "add(data): FC 2025"),
]


@pytest.mark.parametrize(("title", "expected"), VALID)
def test_parse_valid(title, expected):
    assert parse_title(title) == expected


@pytest.mark.parametrize(("title", "fragment"), INVALID)
def test_parse_invalid(title, fragment):
    with pytest.raises(TitleError, match=re.escape(fragment)):
        parse_title(title)


@pytest.mark.parametrize(("title", "files", "ok"), CHECK)
def test_check(title, files, ok):
    if ok:
        check_title(title, files)
        return
    with pytest.raises(TitleError) as info:
        check_title(title, files)
    data_files = [f for f in files if f in ("crypto_db.bib", "abbrev.bibyml")]
    for name in data_files:
        assert name in str(info.value)


@pytest.mark.parametrize(("title", "files", "expected"), SUGGEST)
def test_suggest(title, files, expected):
    assert suggest_title(title, files) == expected
    check_title(suggest_title(title, files), files)


def test_only_root_paths_are_data_files():
    assert touches_data(["resources/tools/crypto_db.bib"]) is False
    assert touches_data(["crypto_misc.bib"]) is True
