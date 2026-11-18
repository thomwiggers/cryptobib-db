#!/usr/bin/env python3
"""
This script generates crypto.bib from
  abbrev0.bib
  crypto_db.bib
  crypto_conf_list.bib
  crypto_misc.bib

Run this script from the repository root.
"""

import sys
import os

scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(scriptdir, "..", "lib"))
sys.path.append(os.path.join(scriptdir, "..", ".."))

from config import *
import config
import header
import logging
from confs_years import *
import mybibtex.generator
import mybibtex.parser

mybibtex.generator.config = config
logging.basicConfig(level=logging.DEBUG)


def gen_crypto_bib(db, confs_years, expand_crossrefs: bool):
    if expand_crossrefs == False:
        outname = "crypto_crossref.bib"
    else:
        outname = "crypto.bib"

    with open(outname, "w") as out:
        out.write(header.get_header(config, "gen.py", confs_years))

        mybibtex.generator.bibtex_gen(out, db, expand_crossrefs=expand_crossrefs,
                                      include_crossrefs=not expand_crossrefs, remove_empty_fields=True)

        out.write("\n")
        out.write("\n")

        with open("crypto_misc.bib") as fin:
            for line in fin:
                out.write(line)


def main():
    parser = mybibtex.parser.Parser()
    # It's important to use abbrev0.bib for the parsing
    # otherwise we may be removing fields that are empty for abbrev3.bib but not for abbrev0.bib
    # as we are removing fields that are empty after macro expansion
    parser.parse_file("abbrev0.bib")
    parser.parse_file("crypto_db.bib")
    db = parser.parse_file("crypto_conf_list.bib")

    confs_years = get_confs_years_inter(db, confs_missing_years)

    gen_crypto_bib(db, confs_years, True)
    gen_crypto_bib(db, confs_years, False)


if __name__ == "__main__":
    main()
