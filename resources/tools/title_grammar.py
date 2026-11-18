"""Grammar of pull request titles: Conventional Commits with the scope `data`."""

import re
from collections.abc import Iterable
from dataclasses import dataclass

DATA_FILES = (
    "crypto_db.bib",
    "crypto_misc.bib",
    "crypto_conf_list.bib",
    "abbrev.bibyml",
)
DATA_TYPES = ("add", "fix")
OTHER_TYPES = ("feat", "fix", "chore", "ci", "docs", "build", "refactor", "test")

FORMAT = "type(scope): description"
_TITLE = re.compile(
    r"(?P<type>[A-Za-z][\w-]*)(?:\((?P<scope>[^()\s]+)\))?(?P<breaking>!)?:(?P<rest>.*)",
    re.DOTALL,
)
_LEADING_VERB = re.compile(
    r"(?P<verb>add|added|fix|fixed|fixes)(?:\s+|$)", re.IGNORECASE
)


class TitleError(ValueError):
    """The title does not follow the format. `str(e)` is one sentence for the contributor."""


@dataclass(frozen=True)
class Title:
    type: str
    scope: str | None
    breaking: bool
    description: str


def parse_title(title: str) -> Title:
    match = _TITLE.fullmatch(title.strip())
    if match is None:
        raise TitleError(
            f"The title must have the form {FORMAT}, for example fix(data): title of EC:CFSY96."
        )
    type_, scope, rest = match["type"], match["scope"], match["rest"]
    description = rest.strip()
    if not description:
        raise TitleError("The title needs a description after the colon.")
    if not rest.startswith(" "):
        raise TitleError(
            f"The title must have the form {FORMAT}, with a space after the colon."
        )
    if description.endswith("."):
        raise TitleError("The description must not end with a period.")
    if scope == "data":
        if type_ not in DATA_TYPES:
            raise TitleError(
                f"The type {type_} is not allowed with the scope data. Use add(data) or fix(data)."
            )
    elif type_ in DATA_TYPES and type_ not in OTHER_TYPES:
        raise TitleError(
            f"The type {type_} needs the scope data, as in {type_}(data): ..."
        )
    elif type_ not in OTHER_TYPES:
        hint = (
            " Data changes are written add(data) or fix(data). Here data is the scope."
            if type_ == "data"
            else ""
        )
        raise TitleError(
            f"The type {type_} is not allowed, use one of {', '.join(OTHER_TYPES)}.{hint}"
        )
    return Title(type_, scope, match["breaking"] is not None, description)


def _data_files(files: Iterable[str]) -> list[str]:
    return [f for f in files if f in DATA_FILES]


def touches_data(files: Iterable[str]) -> bool:
    return bool(_data_files(files))


def check_title(title: str, files: Iterable[str]) -> Title:
    parsed = parse_title(title)
    touched = _data_files(files)
    if touched and parsed.scope != "data":
        raise TitleError(
            f"The change touches {', '.join(touched)}, so the title needs the scope data, "
            "as in add(data): ... or fix(data): ..."
        )
    return parsed


def suggest_title(title: str, files: Iterable[str]) -> str:
    data = touches_data(files)
    stripped = title.strip().rstrip(". \t\n").strip()
    # A title of the shape `word(scope)!: text` contributes its text only.
    shaped = _TITLE.fullmatch(stripped)
    base = shaped["rest"].strip() if shaped else stripped
    verb = _LEADING_VERB.match(base)
    adding = (verb is not None and verb["verb"].lower() in ("add", "added")) or (
        shaped is not None and shaped["type"].lower() in ("add", "added")
    )
    if verb:
        base = base[verb.end() :].strip()
    if data:
        bang = "!" if shaped and shaped["breaking"] else ""
        return f"{'add' if adding else 'fix'}(data){bang}: {base or 'update entries'}"
    return f"chore: {base or 'update'}"
