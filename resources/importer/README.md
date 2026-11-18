# CryptoBib Database Import

Tools that import bibtex entries from DBLP, ePrint and other sources. See the root `README.md` for the steps to add a conference.

`import.py` opens `utf8ienc.dtx` relative to the current directory. Run the scripts in this directory from inside `resources/importer`:

    cd resources/importer
    uv run python fetch_dblp_dump.py
    uv run python import.py <conf><year>

`fetch_dblp_dump.py` downloads a local copy of the DBLP XML dump into `dblp-dump/`. `import.py` reads it before it falls back to a live DBLP fetch.
