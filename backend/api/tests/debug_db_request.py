"""
Debug helper: run a FastAPI TestClient request to `/api/admin/carrusel`
Prints response or full exception traceback to help diagnose database errors.
"""
import traceback
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend/api is on sys.path so imports like `from main import app` work
HERE = Path(__file__).resolve().parent
API_DIR = HERE.parent  # backend/api
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

try:
    from main import app
except Exception:
    # fallback to package import if running from repo root
    from backend.api.main import app


def run():
    client = TestClient(app)
    try:
        # TrustedHostMiddleware expects allowed host values; set Host header to localhost
        resp = client.get("/api/admin/carrusel", headers={"host": "localhost"})
        print("STATUS:", resp.status_code)
        print(resp.text)
    except Exception as e:
        print("Exception during request:")
        traceback.print_exc()


if __name__ == '__main__':
    run()
