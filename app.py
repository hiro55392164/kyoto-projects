"""Open the bid schedule as the application home page."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).parent / "pages" / "1_入札工程表.py"), run_name="__main__")
