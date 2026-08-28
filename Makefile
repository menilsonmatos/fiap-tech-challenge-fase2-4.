.PHONY: setup test lint demo simulate validate terraform-fmt

setup:
	python -m venv .venv
	.venv/bin/pip install -e ".[dev,aws]"

test:
	python -m unittest discover -s tests -v

lint:
	ruff check src tests

demo:
	python -m alfabetizacao_pipeline.cli batch --source data/source/indicador_alfabetizacao.csv --output data

simulate:
	python -m alfabetizacao_pipeline.cli simulate-stream --events data/source/eventos_indicadores.jsonl --output data

validate:
	python -m alfabetizacao_pipeline.cli validate --input data/silver/indicadores.csv

terraform-fmt:
	terraform -chdir=infra/terraform fmt -recursive
