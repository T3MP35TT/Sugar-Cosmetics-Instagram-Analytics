from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP_FILES = [ROOT / "app.py", *sorted((ROOT / "pages").glob("*.py"))]


@pytest.mark.parametrize("script_path", APP_FILES, ids=lambda path: path.stem)
def test_dashboard_script_runs_without_streamlit_exceptions(script_path):
    app = AppTest.from_file(str(script_path), default_timeout=30).run()
    assert not app.exception, "\n".join(str(error.value) for error in app.exception)
