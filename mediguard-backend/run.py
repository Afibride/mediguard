"""
MediGuard backend entry-point.
Starts Uvicorn on port 3000 (0.0.0.0 so it's reachable on the LAN).

Usage:
    python run.py              # production-like, single worker
    python run.py --reload     # development with auto-reload
"""

import sys
import uvicorn

if __name__ == "__main__":
    reload = "--reload" in sys.argv or "-r" in sys.argv

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=3000,
        reload=reload,
        log_level="info",
    )
