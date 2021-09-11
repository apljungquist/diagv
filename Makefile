# Configuration
# =============

# Have zero effect by default to prevent accidental changes.
.DEFAULT_GOAL := none

# Delete targets that fail to prevent subsequent attempts incorrectly assuming
# the target is up to date.
.DELETE_ON_ERROR: ;

# Prevent pesky default rules from creating unexpected dependency graphs.
.SUFFIXES: ;


# Verbs
# =====

.PHONY: none

none:
	@echo No target specified

fix_formating:
	isort examples setup.py src tests
	black examples setup.py src tests

# Nouns
# =====

constraints.txt:  $(wildcard requirements/*.txt) requirements/tox.txt
	pip-compile --allow-unsafe --no-header --output-file $@ $^

reports/type_coverage/_envoy:
	mkdir -p $(@D)
	git clean -xdff $(@D)
	mypy --html-report $(@D) examples src tests

requirements.txt: $(wildcard requirements/*.txt) requirements/tox.txt
	echo "-e." > $@
	echo $^ | tr " " "\n" | sed -e 's/^/-r/g' >> $@

requirements/tox.txt: tox.ini
	tox -l --requirements-file $@ >/dev/null