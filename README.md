# UI Test Automation — Image Preview Verification

This repository contains a Playwright-based automation that uploads an image to an online conversion page and verifies whether a preview (image/canvas/video/svg) appears.

**What it does**
- Uploads a sample image (auto-created if missing) to the configured URL.
- Waits for a visible preview to appear using robust DOM heuristics.
- Saves a screenshot to the `result/` folder and writes a single-row CSV report (`execution_results.csv` by default).

**Tools**: Playwright (Python) — browser automation

**Workspace files**
- `image_preview_test.py` — main test script
- `requirements.txt` — Python dependencies
- `sample.png` — default input (created automatically if missing)
- `result/` — screenshots saved here
- `execution_results.csv` — CSV test report

**Prerequisites**
- Python 3.8+ installed and on PATH (3.11+ recommended)
- Git (optional, only for pushing to GitHub)

Windows note: if `python` is not recognized, call the full path to your Python binary, for example `C:/Python311/python.exe`.

**One-time setup**

1. (Optional) Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install Python dependencies and Playwright browsers:

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

If you prefer all browsers, run `python -m playwright install` instead.

**Run the test**

Basic example (uses default URL and sample.png):

```bash
python image_preview_test.py
```

Run headless (no UI):

```bash
python image_preview_test.py --headless
```

Run against a different URL and slow down actions for debugging:

```bash
python image_preview_test.py --url "https://www.pixelssuite.com/convert-to-png" --slow-mo-ms 2000
```

Append results to CSV instead of overwriting:

```bash
python image_preview_test.py --append-csv
```

Full CLI options (summary)
- `--url` : Target page to test (default: https://www.pixelssuite.com/convert-to-png)
- `--png` : Input PNG file path (default: `sample.png` in project root)
- `--out-dir` : Output folder for screenshots (default: `result`)
- `--csv` : CSV filename for results (default: `execution_results.csv`)
- `--append-csv` : Append a new row instead of overwriting the CSV
- `--headless` : Run browser headless
- `--timeout-ms` : Overall timeout in milliseconds (default: 60000)
- `--slow-mo-ms` : Slow down browser actions in milliseconds (default: 0)

Example that customizes everything:

```bash
python image_preview_test.py --url "https://example.com/upload" --png tests/myfile.png --out-dir results --csv my_results.csv --append-csv --headless
```

**Outputs**
- Screenshot: `result/preview_pass.png` or `result/preview_fail.png` (or `preview_error.png` on unhandled exceptions)
- CSV: `execution_results.csv` with columns: `file_type,file_path,preview_detected,status,screenshot`

**Troubleshooting**
- Playwright errors: ensure `python -m playwright install chromium` completed successfully.
- If the script can't find the file input, try running with `--slow-mo-ms 1000` or open the browser without `--headless` to observe page behavior.
- If the target page changes layout, update the DOM heuristics in `check_preview_visible()` inside `image_preview_test.py`.

**CI / Automation notes**
- Ensure browsers are installed in CI by running `python -m playwright install --with-deps` (Linux) or the Windows equivalent.
- Use `--headless` and `--csv` to produce machine-readable test reports as part of CI.

**Contributing / Extending**
- To support additional file types (JPEG, GIF), update `create_default_png_if_missing()` and detection heuristics.
- To add unit tests for detection logic, extract DOM-evaluation code into a small function and write pytest tests that exercise it against saved HTML fixtures.

If you want, I can also:
- Add pytest-style unit tests, or
- Extend the script to support multiple file types.

