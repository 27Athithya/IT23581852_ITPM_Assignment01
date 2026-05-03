# UI Test Automation (Option 2) — Preview Verification

This repository automates **one** test scenario (as required in Option 2):

- Feature: **Image format conversion**
- Scenario: Upload a **PNG** file and verify the **Preview** is displayed
- Tool: **Playwright (Python)**
- Evidence: Writes a single row to `execution_results.csv` and saves a screenshot to `result/preview_pass.png` (or `preview_fail.png`).

## Prerequisites

- Python 3.11+ installed
- Git installed (only needed to push to GitHub)

If `python` is not recognized in your terminal, use the full path to Python (example):

```bash
c:/python313/python.exe --version
```

## Setup (one-time)

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Run the automation

```bash
python image_preview_test.py --url "https://www.pixelssuite.com/convert-to-png" --slow-mo-ms 2000
```

Optional:

- Headless mode:

```bash
python image_preview_test.py --headless
```

- Append multiple runs to the CSV (default is overwrite so the CSV has one data row):

```bash
python image_preview_test.py --append-csv
```

## Outputs

- `execution_results.csv`
  - Columns: `file_type,file_path,preview_detected,status,screenshot`
  - Default behavior overwrites the file so it contains **exactly one data row** per run.

- `result/preview_pass.png` or `result/preview_fail.png`

## Notes

- Default input image is `sample.png`. If it is missing, the script creates a tiny PNG automatically.

## Push to GitHub

1) Create a new empty repository on GitHub (no README/license, because this folder already has a README).

2) In your terminal, open this project folder and run:

```bash
git init
git add .
git commit -m "Add Playwright automation"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
git push -u origin main
```

If you are using SSH instead of HTTPS, use a remote like:

```bash
git remote set-url origin git@github.com:<YOUR_USERNAME>/<YOUR_REPO>.git
```
