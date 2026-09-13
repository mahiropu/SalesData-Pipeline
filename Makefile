.PHONY: install seed run analytics test clean

install:
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

seed:
	python3 -m src.generate_data

run:
	python3 -m src.pipeline

analytics:
	python3 -m src.analytics

test:
	python3 -m pytest -v

clean:
	rm -rf sales.duckdb logs/*.log data/incoming/*.csv data/archive/*.csv data/quarantine/*.csv data/warehouse/order_year=*
