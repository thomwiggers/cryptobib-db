# CryptoBib Libraries

Python libraries used by the tools and the importer.

## Mybibtex

Mybibtex contains customized versions of some `pybtex` files (https://pybtex.org/) to prevent field values to be flattened to a string (and instead be stored as `Value`, see `mybibtex/database.py`. This is necessary to be able to generate files actually using macros.
It also contains a custom way of printing bibtex entries (`generator.py`).
