"""
Main FastAPI Application Entrypoint
Serves REST APIs, WebSockets, and Police Dashboard UI.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings, BASE_DIR
from backend.app.database import engine, Base, SessionLocal, ensure_police_keys
from backend.app.models import User, Camera, RestrictedZone
from backend.app.security.auth_handler import get_password_hash
from backend.app.api import api_router
from backend.app.websocket.manager import ws_manager


def seed_database():
    """Initializes schema and seeds default users, cameras, and demo zones"""
    Base.metadata.create_all(bind=engine)
    ensure_police_keys()

    db = SessionLocal()
    try:
        # Seed Admin & Officer Users
        if not db.query(User).filter(User.username == "admin").first():
            admin_user = User(
                username="admin",
                badge_number="POLICE-HQ-001",
                full_name="Chief Inspector Davis",
                role="admin",
                hashed_password=get_password_hash("PoliceSecure2026!"),
                is_active=True
            )
            db.add(admin_user)

        if not db.query(User).filter(User.username == "officer").first():
            officer_user = User(
                username="officer",
                badge_number="POLICE-OFF-042",
                full_name="Officer Sarah Connor",
                role="officer",
                user_type="police",
                organization="Police Headquarters",
                location_address="City Police Department HQ",
                hashed_password=get_password_hash("OfficerPass2026!"),
                is_active=True
            )
            db.add(officer_user)

        # Seed Citizen / Store Owner Users
        if not db.query(User).filter(User.username == "user").first():
            citizen_user = User(
                username="user",
                badge_number="CUST-STORE-001",
                full_name="Alexander Vance (Store Manager)",
                role="citizen",
                user_type="citizen",
                organization="Metro Jewelers & Gold Exchange",
                location_address="45 North Commercial Mall, Store #12",
                hashed_password=get_password_hash("UserSecure2026!"),
                is_active=True
            )
            db.add(citizen_user)

        if not db.query(User).filter(User.username == "bank1").first():
            bank_user = User(
                username="bank1",
                badge_number="BANK-SEC-004",
                full_name="Robert Hayes (Chief Security)",
                role="citizen",
                user_type="citizen",
                organization="First State Security Bank - Branch 4",
                location_address="12 Financial District Blvd",
                hashed_password=get_password_hash("BankSecure2026!"),
                is_active=True
            )
            db.add(bank_user)

        # Seed Cameras
        cameras_data = [
            ("CAM-01", "Main Gate Entrance", "Main Gate North", "webcam", "192.168.1.101"),
            ("CAM-02", "Perimeter Fence Corridor", "East Perimeter", "rtsp://192.168.1.102/stream", "192.168.1.102"),
            ("CAM-03", "Evidence & Weapons Vault", "High Security Vault", "rtsp://192.168.1.103/stream", "192.168.1.103"),
            ("CAM-04", "Laboratory Entrance", "Bio-Research Lab", "demo", "192.168.1.104")
        ]

        for code, name, loc, src, ip in cameras_data:
            if not db.query(Camera).filter(Camera.camera_code == code).first():
                cam = Camera(
                    camera_code=code,
                    name=name,
                    location=loc,
                    stream_source=src,
                    status="ONLINE",
                    ai_detection="ACTIVE",
                    ip_address=ip
                )
                db.add(cam)

        db.commit()

        # Seed Restricted Zone on CAM-04 (Laboratory Entrance)
        cam4 = db.query(Camera).filter(Camera.camera_code == "CAM-04").first()
        if cam4 and not db.query(RestrictedZone).filter(RestrictedZone.zone_code == "ZONE-LAB-01").first():
            # Normalized polygon points [[x1, y1], [x2, y2], ...] in range 0.0 - 1.0
            polygon_points = "[[0.20, 0.40], [0.80, 0.40], [0.85, 0.90], [0.15, 0.90]]"
            zone = RestrictedZone(
                zone_code="ZONE-LAB-01",
                name="Bio-Lab Secured Perimeter",
                camera_id=cam4.id,
                polygon_points_json=polygon_points,
                severity="HIGH",
                is_active=True
            )
            db.add(zone)
            db.commit()

    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup & shutdown events"""
    seed_database()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real-Time Edge AI Surveillance, Weapon Detection, and Hybrid Post-Quantum (ML-KEM + AES-256-GCM) Evidence Management Framework",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API
app.include_router(api_router, prefix=settings.API_PREFIX)

# WebSocket Endpoint for Live Alerts
@app.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Heartbeat / ping response
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# Mount Static Files & Frontend SPA
FRONTEND_DIR = BASE_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_dashboard():
    """Serves Single Page Application index.html for Police HQ"""
    index_file = FRONTEND_DIR / "templates" / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Police Command Dashboard UI initializing..."}


@app.get("/user")
async def serve_user_portal():
    """Serves User / Citizen Camera Security Portal user_portal.html"""
    portal_file = FRONTEND_DIR / "templates" / "user_portal.html"
    if portal_file.exists():
        return FileResponse(str(portal_file))
    return FileResponse(str(FRONTEND_DIR / "templates" / "index.html"))
