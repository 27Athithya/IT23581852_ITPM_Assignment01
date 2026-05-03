from playwright.sync_api import sync_playwright
from pathlib import Path
import argparse
import base64
import time
import sys
import csv


DEFAULT_URL = "https://www.pixelssuite.com/convert-to-png"
DEFAULT_TIMEOUT_MS = 60000
DEFAULT_SLOW_MO_MS = 0

DEFAULT_OUT_DIR = "result"
DEFAULT_CSV = "execution_results.csv"
DEFAULT_PNG = "sample.png"

PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/6X9wYQAAAAASUVORK5CYII="
)


def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--png", default=DEFAULT_PNG)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--csv", default=DEFAULT_CSV)
    parser.add_argument(
        "--append-csv",
        action="store_true",
        default=False,
        help="Append a new row to the CSV instead of overwriting it (default: overwrite).",
    )
    parser.add_argument("--headless", action="store_true", default=False)
    parser.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS)
    parser.add_argument("--slow-mo-ms", type=int, default=DEFAULT_SLOW_MO_MS)
    return parser.parse_args()


def resolve_repo_relative_path(repo_root: Path, path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def create_default_png_if_missing(file_path: Path):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        file_path.write_bytes(base64.b64decode(PNG_1X1_BASE64))


def find_file_input(page, timeout_ms: int):
    deadline = time.time() + (timeout_ms / 1000)

    while time.time() < deadline:
        try:
            locator = page.locator('input[type="file"]').first
            if locator.count() > 0:
                return locator
        except Exception:
            pass
        page.wait_for_timeout(300)

    raise RuntimeError("File upload input was not found.")


def check_preview_visible(page):
    script = """
    () => {
        const isVisible = (el) => {
            if (!el) return false;
            if (!(el.getClientRects && el.getClientRects().length)) return false;
            const style = window.getComputedStyle(el);
            return style && style.visibility !== 'hidden' && style.display !== 'none' && style.opacity !== '0';
        };

        const mediaVisible = (root) => {
            const nodes = Array.from(root.querySelectorAll('img, canvas, svg, video'));
            for (const el of nodes) {
                if (!isVisible(el)) continue;

                if (el.tagName.toLowerCase() === 'img') {
                    const src = (el.getAttribute('src') || '').trim();
                    const w = el.naturalWidth || el.width || 0;
                    const h = el.naturalHeight || el.height || 0;
                    if ((src.startsWith('blob:') || src.startsWith('data:')) && w >= 40 && h >= 40) return true;
                }

                if (el.tagName.toLowerCase() === 'canvas') {
                    const w = el.width || 0;
                    const h = el.height || 0;
                    if (w >= 40 && h >= 40) return true;
                }

                if (el.tagName.toLowerCase() === 'video') {
                    const w = el.videoWidth || el.clientWidth || 0;
                    const h = el.videoHeight || el.clientHeight || 0;
                    if (w >= 40 && h >= 40) return true;
                }

                // svg: treat any visible svg as weak signal; only accept if reasonably sized.
                if (el.tagName.toLowerCase() === 'svg') {
                    const rect = el.getBoundingClientRect();
                    if (rect.width >= 40 && rect.height >= 40) return true;
                }
            }
            return false;
        };

        // Primary: find a visible label that includes "preview" and ensure media exists near it.
        const previewLabels = Array.from(document.querySelectorAll('body *'))
            .filter(el => el.childElementCount === 0)
            .filter(el => (el.textContent || '').trim().toLowerCase().includes('preview'))
            .filter(isVisible);

        for (const label of previewLabels) {
            let parent = label;
            for (let i = 0; i < 7 && parent; i++) {
                if (mediaVisible(parent)) return true;
                parent = parent.parentElement;
            }
        }

        // Secondary: common DOM hooks that include "preview" in id/class/aria.
        const hooked = Array.from(document.querySelectorAll('[id*="preview" i], [class*="preview" i], [aria-label*="preview" i]'))
            .filter(isVisible);
        for (const root of hooked.slice(0, 20)) {
            if (mediaVisible(root)) return true;
        }

        return false;
    }
    """
    return page.evaluate(script)


def write_result_to_csv(csv_path: Path, row: dict, append: bool):
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "file_type",
        "file_path",
        "preview_detected",
        "status",
        "screenshot",
    ]

    mode = "a" if append else "w"
    with csv_path.open(mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not append:
            writer.writeheader()
        elif csv_path.stat().st_size == 0:
            writer.writeheader()
        writer.writerow({
            "file_type": row.get("file_type", ""),
            "file_path": row.get("file_path", ""),
            "preview_detected": row.get("preview_detected", ""),
            "status": row.get("status", ""),
            "screenshot": row.get("screenshot", ""),
        })


def run_test():
    configure_stdout()
    args = parse_args()

    repo_root = Path(__file__).resolve().parent

    png_path = resolve_repo_relative_path(repo_root, args.png)
    out_dir = resolve_repo_relative_path(repo_root, args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = resolve_repo_relative_path(repo_root, args.csv)
    create_default_png_if_missing(png_path)

    result = {
        "file_type": "PNG",
        "file_path": str(png_path),
        "preview_detected": False,
        "status": "FAIL",
        "screenshot": "",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=args.headless,
            slow_mo=args.slow_mo_ms
        )
        page = browser.new_page()
        page.set_default_timeout(args.timeout_ms)

        try:
            page.goto(args.url, wait_until="domcontentloaded")

            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass

            file_input = find_file_input(page, args.timeout_ms)
            file_input.set_input_files(str(png_path))

            deadline = time.time() + (args.timeout_ms / 1000)
            preview_found = False

            while time.time() < deadline:
                if check_preview_visible(page):
                    preview_found = True
                    break
                page.wait_for_timeout(500)

            status = "PASS" if preview_found else "FAIL"

            screenshot_path = out_dir / ("preview_pass.png" if status == "PASS" else "preview_fail.png")
            page.screenshot(path=str(screenshot_path), full_page=True)

            result = {
                "file_type": "PNG",
                "file_path": str(png_path),
                "preview_detected": preview_found,
                "status": status,
                "screenshot": str(screenshot_path),
            }

            print("========== TEST RESULT ==========")
            print(f"PNG file        : {png_path}")
            print(f"Preview detected: {preview_found}")
            print(f"Status          : {status}")
            print(f"Screenshot      : {screenshot_path}")
            print(f"CSV             : {csv_path}")

        except Exception as e:
            error_screenshot = out_dir / "preview_error.png"
            try:
                page.screenshot(path=str(error_screenshot), full_page=True)
            except Exception:
                pass

            result = {
                "file_type": "PNG",
                "file_path": str(png_path),
                "preview_detected": False,
                "status": "FAIL",
                "screenshot": str(error_screenshot),
            }

            print("========== TEST RESULT ==========")
            print(f"PNG file        : {png_path}")
            print("Preview detected: False")
            print("Status          : FAIL")
            print(f"Screenshot      : {error_screenshot}")
            print(f"CSV             : {csv_path}")
            print(f"Error           : {e}")

        finally:
            browser.close()

    write_result_to_csv(csv_path, result, append=args.append_csv)


if __name__ == "__main__":
    run_test()