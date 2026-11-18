# CryptoBib Developer Repository

This repository holds the CryptoBib database and the tools that generate the `.bib` files from it. To report an error in the database or to propose a change, open an issue or a pull request here.

To use CryptoBib in a LaTeX project, you want the generated files instead. They live in [cryptobib/export](https://github.com/cryptobib/export) and [cryptobib/export_crossref](https://github.com/cryptobib/export_crossref).

## Layout

- `crypto_db.bib`, `crypto_misc.bib`: the bibtex entries.
- `crypto_conf_list.bib`: the list of all conferences.
- `abbrev.bibyml`: the macro definitions, from which `abbrev0.bib` to `abbrev3.bib` are generated.
- `changes-archive.txt`: the frozen change log up to the cutoff. `changes.txt` is generated from pull request titles and the archive, and is not in the repository.
- `config.py`: the database configuration.
- `resources/tools`: generate the output files and merge imported entries into the database.
- `resources/lib`: Python libraries used by the tools, including the bibtex parser and generator `mybibtex`.
- `resources/importer`: import entries from DBLP, ePrint and other sources.
- `resources/tests`: check that the generated files work with `bibtex8` and `biber`.

## Setup

Install [uv](https://docs.astral.sh/uv/) and run

    uv sync

Python 3.12 or later is required. Run all commands from the repository root, except where stated otherwise.

## Commands

- `make` generates `abbrev0.bib` to `abbrev3.bib`, `crypto.bib` and `crypto_crossref.bib` in the root. Git ignores these files.
- `make test` runs the LaTeX tests. It needs TeX Live with `biber`, and `bibtex8` and `pplatex` compiled in `resources/tests` (see `resources/tests/README.md`). On systems without `libpcre3-dev` (Ubuntu 26.04, Debian 13), skip pplatex and run `make test PDFLATEX="pdflatex -interaction=nonstopmode -halt-on-error"`. With gcc 15 or newer, compile bibtex8 with `-std=gnu17` (see `resources/tests/README.md`).
- `make export` copies the generated files and `changes.txt` into `export/` and `export_crossref/`. Clone [cryptobib/export](https://github.com/cryptobib/export) and [cryptobib/export_crossref](https://github.com/cryptobib/export_crossref) there, or set `EXPORT_DIR` and `EXPORT_CROSSREF_DIR` to other clones.
- `make changes.txt` generates the change log from the git history. It needs the full history, not a shallow clone.
- `make clean` removes the generated files.

CI runs `make` and `make test` on every pull request. `changes.txt` is generated from pull request titles, so nobody edits it.

## Pull request titles

The changelog is generated from the titles of merged pull requests. Commits pushed directly to `master` follow the same format. CI checks the title and comments with a suggestion if it does not follow the format.

A title is `type(scope): description` or `type(scope)!: description`.

| Title | Use | Changelog |
|---|---|---|
| `add(data): ...` | new venues, volumes, entries | Added |
| `fix(data): ...` | corrections to existing entries | Fixed |
| `add(data)!: ...`, `fix(data)!: ...` | a change that can break a user's document: renamed or removed keys, changed abbreviations or displayed names | Breaking |
| any other title | no data change | omitted |

Examples:

    add(data): FC 2025, FCW 2025, ICISC 2025
    fix(data): title of EC:CFSY96
    fix(data)!: rename keys of entries with more than six authors
    fix(tools): keep the month macros in add.py
    ci: cache the bibtex8 binary

A pull request that changes `crypto_db.bib`, `crypto_misc.bib`, `crypto_conf_list.bib` or `abbrev.bibyml` must use the `data` scope with type `add` or `fix`. Other titles use one of `feat`, `fix`, `chore`, `ci`, `docs`, `build`, `refactor` or `test`. The scope is optional and free. The description is not empty and does not end with a period.

## Add a conference

`import.py` looks up DBLP publications in a local copy of the [DBLP XML dump](https://dblp.org/faq/How+can+I+download+the+whole+dblp+dataset.html). Before your first import, fetch the dump:

    cd resources/importer
    uv run python fetch_dblp_dump.py

This downloads `dblp.xml.gz` and `dblp.dtd` into `resources/importer/dblp-dump/` and skips the download if the local copy is current. Run it again occasionally to pick up new publications. Entries missing from the dump are fetched live from DBLP.

1. Go to `resources/importer` and run `uv run python import.py <conf><year>`. `import.py` must run from this directory.
2. Correct the generated file `<conf><year>.bib`.
3. Go back to the repository root.
4. Update `abbrev.bibyml` and run `uv run python resources/tools/gen_abbrev.py`.
5. Update `crypto_conf_list.bib`.
6. Merge the imported file into `crypto_db.bib`: `uv run python resources/tools/add.py resources/importer/<conf><year>.bib`.
7. Run `make`, then `make test`.

## Troubleshooting

### `KeyError: EntryKey(...)` when running `gen.py`

    KeyError: EntryKey(C24-10)
    make: *** [crypto.bib] Error 1

The cross-referenced entry `C24-10` is missing. Update `crypto_conf_list.bib`.

### `KeyError: '...'` when running `add.py`

    KeyError: 'crypto24-10'

The macro `crypto24-10` is not defined. Update `abbrev.bibyml` and run `uv run python resources/tools/gen_abbrev.py`.
