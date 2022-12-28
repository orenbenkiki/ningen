# PREAMBLE

## VARIABLES

PROJECT_NAME = ningen

ALL_SOURCE_FILES = $(shell git ls-files)

PY_SOURCE_FILES = $(filter %.py, $(ALL_SOURCE_FILES))

TAG_SOURCE_FILES = $(PY_SOURCE_FILES)

RST_SOURCE_FILES = $(filter %.rst, $(ALL_SOURCE_FILES))

MAX_LINE_LENGTH = 120

## HELP

define PRINT_HELP_PYSCRIPT
import re, sys, fileinput

print('%-20s %s' % ('help', 'Print this help message (default goal)'))
for line in fileinput.input():
	line = line.replace('TODO_X', 'TODO' + 'X').replace('todo_x', 'todo' + 'x')
	match = re.match(r'^([$$()a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		print('%-20s %s' % match.groups())
endef
export PRINT_HELP_PYSCRIPT

.PHONY: help
.DEFAULT_GOAL: help
help:
	@python -c "$$PRINT_HELP_PYSCRIPT" $(MAKEFILE_LIST)

# ON-PUSH

.PHONY: on-push
on-push:  ## Verify a pushed commit in a CI action

## TODO_X

EMPTY =
TODO_X = TODO$(EMPTY)X
todo_x = todo$(EMPTY)x

on-push: todo_x

.PHONY: todo_x  ## Verify there are no leftover TODO_X in the code
$(todo_x): .make.$(todo_x)

.make.$(todo_x): $(ALL_SOURCE_FILES)
	@echo $(todo_x)
	@if grep -in TODO''X $^; \
	then \
	    echo 'Source file(s) contain unresolved TODO''X issues (edit manually to fix)'; \
	    false; \
	else true; \
	fi
	@touch $@

## SMELLS

on-push: smells

.PHONY: smells
smells:  ## Check for code smells

### MYPY

smells: mypy

.PHONY: mypy
mypy: .make.mypy  ## Check code with mypy

.make.mypy: $(PY_SOURCE_FILES)
	@echo mypy
	@if mypy $(PROJECT_NAME) tests; \
	then true; \
	else \
	    echo 'Python code does not satisfy mypy (edit manually to fix).'; \
	    false; \
	fi
	touch $@

clean: clean-mypy

.PHONY: clean-mypy
clean-mypy:
	find . -name .mypy_cache -exec rm -fr {} +

### PYLINT

smells: pylint

.PHONY: pylint
pylint: .make.pylint  ## Check Python code with pylint

.make.pylint: $(PY_SOURCE_FILES)
	@echo pylint
	@if pylint --max-line-length $(MAX_LINE_LENGTH) $(PROJECT_NAME) tests; \
	then true; \
	else \
	    echo 'Python code does not satisfy pylint (edit manually to fix).'; \
	    false; \
	fi
	touch $@

## TEST

on-push: test  # Test code is correct

.PHONY: test
test:  ## Run all Python code tests with pytest

### PYTEST

test: pytest  # Test Python code is correct

.PHONY: pytest
pytest: .make.pytest  ## Run all Python code tests with pytest

.make.pytest: $(PY_SOURCE_FILES)
	@echo pytest
	@if pytest -s --cov=$(PROJECT_NAME) --cov-report=html --cov-report=term --no-cov-on-fail; \
	then true; \
	else \
	    echo 'Python unit tests failed (edit manually to fix).'; \
	    false; \
	fi
	touch $@

clean: clean-pytest

.PHONY: clean-pytest
clean-test:
	rm -rf .coverage htmlcov/ .pytest_cache
	find . -name '*.py[co]' -o -name '__pycache__' -exec rm -rf {} +

### DOCS

on-push: docs

.PHONY: docs
docs: docs/build/html/index.html  ## Build the documentation

docs/build/html/index.html: $(PY_SOURCE_FILES) $(DOCS_SOURCE_FILES) $(RST_SOURCE_FILES)
	@rm -rf docs/build -f docs/$(PROJECT_NAME).rst docs/modules.rst
	sphinx-apidoc -o docs/ $(PROJECT_NAME)
	cd docs && python -m sphinx -M html . build $(SPHINXOPTS)

clean: clean-docs

clean-docs:
	rm -rf docs/build

## FORMATTED

on-push: formatted

.PHONY: formatted
formatted:  ## Check source files formatting

.PHONY: format
format: stripspaces  ## Reformat the source files

### TRAILINGSPACES

formatted: trailingspaces

.PHONY: trailingspaces
trailingspaces: .make.trailingspaces  ## Check for trailing spaces

.make.trailingspaces: $(ALL_SOURCE_FILES)
	@echo trailingspaces
	@if grep -Hn '\s$$' $^; \
	then \
	    echo 'Source file(s) contain trailing spaces (run `make stripspaces` or `make format` to fix)'; \
	    false; \
	else true; \
	fi
	@touch $@

.PHONY: stripspaces
stripspaces: .make.stripspaces  # Strip trailing spaces from source files

.make.stripspaces: $(ALL_SOURCE_FILES)
	@echo stripspaces
	@for SOURCE_FILE in $^; \
	do sed -i -s 's/\s\s*$$//' $$SOURCE_FILE; \
	done
	@touch $@

### BACKTICKS

formatted: backticks

.PHONY: backticks
backticks: .make.backticks  ## Check usage of backticks in Python documentation

.make.backticks: $(PY_SOURCE_FILES) $(RST_SOURCE_FILES)
	@echo backticks
	@OK=true; \
	for FILE in $(PY_SOURCE_FILES) $(RST_SOURCE_FILES); \
	do \
	    if sed 's/``\([^`]*\)``/\1/g;s/:`\([^`]*\)`/:\1/g;s/`\([^`]*\)`_/\1_/g' "$$FILE" \
	    | grep --label "$$FILE" -n -H '`' \
	    | sed 's//`/g' \
	    | grep '.'; \
	    then OK=false; \
	    fi; \
	done; \
	if $$OK; \
	then true; \
	else \
	    echo 'Python documentation contains invalid ` markers (edit manually to fix).'; \
	    false; \
	fi
	@touch $@

### ISORT

formatted: is-isort

.PHONY: is-isort
is-isort: .make.is-isort  ## Check Python imports with isort

.make.is-isort: $(PY_SOURCE_FILES)
	@echo isort
	@if isort --line-length $(MAX_LINE_LENGTH) --force-single-line-imports --check $(PROJECT_NAME) tests; \
	then true; \
	else \
	    echo 'Python imports are unsorted (run `make isort` or `make format` to fix).'; \
	    false; \
	fi
	@touch $@

format: isort

.PHONY: isort
isort: .make.isort  ## Sort Python imports with isort

.make.isort: $(PY_SOURCE_FILES)
	isort --line-length $(MAX_LINE_LENGTH) --force-single-line-imports $(PROJECT_NAME) tests
	@touch $@

### BLACK

formatted: is-black

is-black: .make.is-black  ## Check Python format with black

.make.is-black: $(PY_SOURCE_FILES)
	@echo black
	@if black --line-length $(MAX_LINE_LENGTH) --check $(PROJECT_NAME) tests; \
	then true; \
	else \
	    echo 'Python code is not formatted by black (run `make black` or `make format` to fix).'; \
	    false; \
	fi
	@touch $@

format: black

black: .make.black  ## Reformat Python code with black

.make.black: $(PY_SOURCE_FILES)
	black --line-length $(MAX_LINE_LENGTH) $(PROJECT_NAME) tests
	@touch $@

### FLAKE8

format: flake8

flake8: .make.flake8  ## Check Python style format with flake8

.make.flake8: $(PY_SOURCE_FILES)
	@echo flake8
	@if flake8 --max-line-length $(MAX_LINE_LENGTH) --ignore E203,F401,F403,W503 $(PROJECT_NAME) tests; \
	then true; \
	else \
	    echo 'Python code does not satisfy flake8 (edit manually to fix).'; \
	    false; \
	fi
	@touch $@

# PRE-COMMIT

.PHONY: pre-commit
pre-commit: on-push  ## Verify everything before commit

## STAGED

pre-commit: staged

.PHONY: staged
staged: ## Verify everything is staged for git commit
	@if git status . | grep -q 'Changes not staged\|Untracked files'; \
	then \
	    git status; \
	    echo 'Source file(s) contain unstaged changes (run `git add` to fix)'; \
	    false; \
	else true; \
	fi

# CLEAN

.PHONY: clean
clean:  clean-make  ## Remove all generated files

.PHONY: clean-make
clean-make:
	rm -f .make.*
	find . -name '*~' -exec rm -f {} +

# MISC

## TAGS

tags: $(TAG_SOURCE_FILES)  ## Generate a tags file for vi or emacs
	ctags --recurse .

clean: clean-tags

clean-tags:
	rm -rf tags

## REQUIREMENTS

install-reqs:  ## Install all the required Python modules for development.
	pip install --upgrade $$(cat requirements*.txt | grep -v '#\|^$$' | sort -u)

update-reqs: install_requirements   ## Update all the required Python modules for development.
