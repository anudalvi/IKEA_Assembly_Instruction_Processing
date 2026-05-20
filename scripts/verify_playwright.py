import importlib.util
import subprocess
import sys

def check_playwright():
    # 1. Check if module is importable
    spec = importlib.util.find_spec("playwright")
    if spec is None:
        print("❌ Playwright is NOT installed.")
        print("   To install: pip install playwright && playwright install firefox")
        return False

    # 2. Get version from pip
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "playwright"],
            capture_output=True, text=True
        )
        version_line = next(
            (line for line in result.stdout.splitlines() if line.startswith("Version:")),
            None
        )
        version = version_line.split(": ")[1].strip() if version_line else "Unknown"
    except Exception:
        version = "Unknown"

    print(f"✅ Playwright IS installed.")
    print(f"   Version : {version}")
    print(f"   Location: {spec.origin}")

    # 3. Check if Chromium browser binary is available
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("about:blank")
            browser.close()
        print("   Chromium: ✅ Chromium browser is available and working")
    except Exception as e:
        error_msg = str(e)
        if "Executable doesn't exist" in error_msg:
            print("   Chromium: ❌ Chromium browser binary not found.")
            print("             Run this to install it:")
            print("             playwright install chromium")
        else:
            print(f"   Chromium: ⚠️  Unexpected error — {error_msg}")
        return False

    return True

if __name__ == "__main__":
    check_playwright()