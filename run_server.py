"""
Police Dashboard & Quantum-Safe Backend Server Launcher
Runs FastAPI backend with Uvicorn on http://127.0.0.1:8000
"""

import sys
import uvicorn
from backend.app.config import settings

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if __name__ == "__main__":
    print("=" * 70)
    print("🚔 STARTING POLICE COMMAND HQ & QUANTUM-SAFE EVIDENCE SERVER")
    print(f"🌐 Host: http://{settings.HOST if settings.HOST != '0.0.0.0' else '127.0.0.1'}:{settings.PORT}")
    print("🛡️  Default Admin:   admin    / PoliceSecure2026!")
    print("👮 Default Officer: officer  / OfficerPass2026!")
    print("=" * 70)

    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        reload_dirs=["backend"],
        log_level="info"
    )
