UV ?= $(shell command -v uv 2>/dev/null || echo $(HOME)/.local/bin/uv)
NB ?=
MODE ?=

.PHONY: env test nb all freeze

env:
	$(UV) sync

test:
	$(UV) run pytest -q

# Contoh: make nb NB=01 / make nb NB=14 MODE=sample
nb:
	@test -n "$(NB)" || (echo "Pakai: make nb NB=01 [MODE=sample]" && exit 2)
	$(UV) run python scripts/run_notebook.py --nb "$(NB)" --mode "$(MODE)"

all:
	$(UV) run python scripts/run_all.py

freeze:
	bash scripts/freeze_env.sh "$(UV)"
