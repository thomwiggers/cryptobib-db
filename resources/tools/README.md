# CryptoBib Tools

Scripts that generate the output files and maintain the database. Run them from the repository root with `uv run python resources/tools/<script>.py`. See the root `README.md` for the workflow.

- `gen_abbrev.py` generates `abbrev0.bib` to `abbrev3.bib` from `abbrev.bibyml`.
- `gen.py` generates `crypto.bib` and `crypto_crossref.bib`.
- `add.py` merges an imported bibtex file into `crypto_db.bib`.
- `add_doi_crossref.py`, `merge_doi.py`, `sanity_checks_doi.py`, `check_many_authors_keys.py`, `fix_shelat_keys.py`: maintenance scripts for the database content.
- `update_webapp_db.py`: updates the website database.
