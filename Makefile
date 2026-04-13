.PHONY: dev

dev:
	@bash -c 'source .venv/bin/activate && python -m backend.main & BACKEND=$$!; trap "kill $$BACKEND 2>/dev/null" EXIT; cd frontend && npm run dev'
