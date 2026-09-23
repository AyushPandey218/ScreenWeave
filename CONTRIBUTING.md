# Contributing

Keep reconstruction changes measurable. Do not commit private screenshots, credentials, .env files, model downloads or local reports.

## Checks

```bash
pip install -r backend/requirements-ocr.txt httpx
python -m unittest discover -s backend -p "test_*.py"
npm --prefix frontend ci
npm --prefix frontend run build
```

Start both local servers for browser regressions. Scripts accept an absolute Playwright package path; install with `npm --prefix frontend install --no-save --package-lock=false playwright`.

```bash
node frontend/test-advanced.cjs /absolute/path/to/frontend/node_modules/playwright
node frontend/test-quality.cjs /absolute/path/to/frontend/node_modules/playwright
node frontend/test-region.cjs /absolute/path/to/frontend/node_modules/playwright
```

Browser regression scripts currently use Microsoft Edge. The advanced test checks extraction preview/cancel/apply, undo/redo, mobile preview, exports and persistence using the included text-banner fixture. CI runs backend unit tests and the frontend build.

Describe user-visible behavior, validation and limitations in a pull request. For detector changes include regressions as well as improvements. Preserve saved-layout compatibility and all exports. Development-fixture metrics must not be called model accuracy.
