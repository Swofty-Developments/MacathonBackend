# Catch N Go

Ever wanted to catch a Monash uni student? You can now grab one to your basement.

## Set up locally
0. (Optional step) Set up a virtual environment using `python3 -m venv .venv`. If using VSCode, accept using the new Python interpreter or otherwise ctrl+P and then `>Python: Select Interpreter` and choose the one located at `.\.venv`.
1. Install the dependencies using `pip install -r requirements.txt`.
2. Additionally install `pip install "fastapi[standard]" separately. This is not included in a production build.
3. Run the application using `fastapi dev src/main.py`.
4. Any new changes after using something like ctrl+S will reload and re-run the project automatically.

## Notes
- Easily test any endpoints at http://127.0.0.1:8000/docs 
- Use `_log.debug`, `_log.info`, `_log.warning`, `_log.error` and `log.exception` for permanent logging (can use `print` for quick debugging). Especially check out how to use `log.exception` in try except catches.
- If you are importing something for the sake of type hinting ONLY, import it under `if TYPE_CHECKING` from `from typing import TYPE_CHECKING`.
- Install `pip install ruff` and run `ruff format` to format all files. Can optionally also install the VSCode Ruff linter.

## Importing order
(Create an empty new line after each group of imports)
1. Import `from __future__ import annotations` where applicable (should also then have `from typing import TYPE_CHECKING` imported too) first (used when you face cyclic import errors when you are just trying to type hint).
2. Import all third-party and built-in libraries that are `import foo`.
3. Import all third-party and built-in libraries that are `from foo import bar`.
4. Import all project-specific libraries under `/src`. `import foo` first, and then `from foo import bar` but no need for empty new line in between.
5. Lastly import anything for only type hinting purposes under `if TYPE_CHECKING:`.
