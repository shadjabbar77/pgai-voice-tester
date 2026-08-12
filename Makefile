.PHONY: install test serve scenarios call process

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

test:
	.venv/bin/python -m pytest -q

serve:
	.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

scenarios:
	.venv/bin/python -m scripts.list_scenarios

call:
	@test -n "$(SCENARIO)" || (echo "Usage: make call SCENARIO=appointment_basic" && exit 1)
	.venv/bin/python -m scripts.run_call --scenario "$(SCENARIO)"

process:
	@test -n "$(CALL_SID)" || (echo "Usage: make process CALL_SID=CA..." && exit 1)
	.venv/bin/python -m scripts.process_call --call-sid "$(CALL_SID)"
