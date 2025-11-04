.venv:
	uv venv

venv:	.venv

build:	venv
	uv sync

test:	build
	uv run pytest tests/ -v

.PHONY:	test venv build
