PYTHON=uv run python
ABBREV_BIB=abbrev0.bib abbrev1.bib abbrev2.bib abbrev3.bib
GENERATED=$(ABBREV_BIB) crypto.bib crypto_crossref.bib
EXPORT_DIR=export
EXPORT_CROSSREF_DIR=export_crossref

.PHONY: all export test web clean FORCE

all: $(GENERATED)

abbrev%.bib: abbrev.bibyml resources/tools/gen_abbrev.py
	$(PYTHON) resources/tools/gen_abbrev.py

crypto.bib crypto_crossref.bib: abbrev0.bib crypto_db.bib crypto_misc.bib crypto_conf_list.bib resources/tools/gen.py
	$(PYTHON) resources/tools/gen.py

changes.txt: FORCE
	$(PYTHON) resources/tools/gen_changes.py

FORCE:

export: all changes.txt
	@test -d "$(EXPORT_DIR)" || { echo "EXPORT_DIR=$(EXPORT_DIR) is not a directory. Clone cryptobib/export there." >&2; exit 1; }
	@test -d "$(EXPORT_CROSSREF_DIR)" || { echo "EXPORT_CROSSREF_DIR=$(EXPORT_CROSSREF_DIR) is not a directory. Clone cryptobib/export_crossref there." >&2; exit 1; }
	cp $(ABBREV_BIB) changes.txt crypto.bib "$(EXPORT_DIR)"
	cp $(ABBREV_BIB) changes.txt crypto_crossref.bib "$(EXPORT_CROSSREF_DIR)"

test: all
	cd resources/tests && $(MAKE)

clean:
	rm -f $(GENERATED) changes.txt

web: all changes.txt webapp/static/files/crypto.zip
	$(PYTHON) resources/tools/update_webapp_db.py

webapp/static/files/crypto.zip: crypto.bib crypto_crossref.bib $(ABBREV_BIB)
	zip -j $@ $^
