## End-to-End Tests

### Prerequisites
```bash
pip install pytest-playwright
playwright install chromium
```

### Running Tests
Set `BASE_URL` to your running API address (default: `http://localhost:8000`; if local scripts auto-fallback, use the actual port), then execute:
```bash
BASE_URL=http://localhost:8000
pytest tests/e2e/test_ui_interactions.py -v
```
