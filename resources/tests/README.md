# CryptoBib Tests

## Getting started

### Requirements

- the setup of the root `README.md` (`uv sync`)
- TeX Live with `biber`
- a C compiler
- compile bibtex8:

		cd bibtex8
		make -f unix.mak linux-gcc

  The bibtex8 sources do not compile as C23, the default of gcc 15 and newer. With these compilers, run instead:

		make -f unix.mak bibtex-exe CC=gcc CFLAGS="-std=gnu17 -Wall -Wno-char-subscripts -funsigned-char" LD=gcc

- `scons` (for example `uv tool install scons`) and the PCRE development headers (`libpcre3-dev` on Debian)
- compile pplatex

		cd pplatex
		scons

Note: If pplatex compilation fails with `src/regex.h:12:10: fatal error: 'pcreposix.h' file not found`, on macOS do:

```
brew install pcre
scons PCREPATH="$(brew --prefix pcre)"
```

### Run all tests

Run `make test` in the repository root. Check the output and the `*.pdf` files.

On systems without `libpcre3-dev` (Ubuntu 26.04, Debian 13), skip pplatex and run `make test PDFLATEX="pdflatex -interaction=nonstopmode -halt-on-error"` in the repository root. CI does the same.

## Troubleshooting

### Clean tests

Run `make -C resources/tests clean` from the repository root.

## Under the hood

### bibtex8

`bibtex`/`bibtex8` (<http://www.ctan.org/tex-archive/biblio/bibtex/8-bit>) cannot support by default such a big bibliography.
We needed to modify `bibtex8` (more precisely the file `bibtex8/utils.c` - the original file is `bibtex8/utils.c.orig`).
