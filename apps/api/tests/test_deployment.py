"""Exercise the root ASGI adapter and fixture layout away from the checkout."""

import json
from pathlib import Path
import shutil
import subprocess
import sys


def test_backend_config_preserves_python_framework_detection():
    root = Path(__file__).resolve().parents[3]
    config = json.loads((root / "vercel.json").read_text())
    assert config["framework"] == "fastapi"
    # Vercel's detector treats an empty buildCommand/outputDirectory as static.
    assert config["buildCommand"] is None
    assert config.get("outputDirectory") is None
    assert config["installCommand"] == "uv pip install -r requirements.txt"


def test_root_adapter_in_isolated_bundle_from_unrelated_directory(tmp_path):
    root = Path(__file__).resolve().parents[3]
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    shutil.copy2(root / "index.py", bundle / "index.py")
    shutil.copytree(root / "apps/api/app", bundle / "apps/api/app",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(root / "data/demo/sprint-08", bundle / "data/demo/sprint-08")
    script = """
import json, sys
sys.path.insert(0, sys.argv[1])
from index import app
from fastapi.testclient import TestClient
from app.services.demo_burndown import sprint_08_burndown
from app.services.demo_delivery_flow import sprint_08_delivery_flow
from app.services.demo_quality_rework import sprint_08_quality_rework
with TestClient(app) as client:
    expected = {
        '/health': {'status': 'ok', 'service': 'adi-api'},
        '/demo/sprint-08/burndown': sprint_08_burndown(),
        '/demo/sprint-08/delivery-flow': sprint_08_delivery_flow(),
        '/demo/sprint-08/quality-rework': sprint_08_quality_rework(),
    }
    for route, result in expected.items():
        response = client.get(route)
        assert response.status_code == 200, route
        assert response.json() == result, route
    assert client.get('/api/health').status_code == 404
print(json.dumps(list(expected)))
"""
    result = subprocess.run([sys.executable, "-B", "-c", script, str(bundle)],
                            cwd=tmp_path, capture_output=True, text=True, check=True)
    assert len(json.loads(result.stdout)) == 4
