import base64
import os
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .auth import create_admin_user, get_current_user, router as auth_router
from .database import SessionLocal, engine
from .models import Base, Incident, User, Violation
from .alert import dispatch_alert
from .pdf_report import generate_report
from .process_frame import process_frame

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RoadGuard AI Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)

SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots"
SNAPSHOT_DIR.mkdir(exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        create_admin_user(db)
    finally:
        db.close()


@app.get("/")
def health_check():
    return {"status": "RoadGuard AI backend is running"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    db = SessionLocal()
    try:
        while True:
            payload = await websocket.receive_json()
            frame_base64 = payload.get("frame")
            if not frame_base64:
                await websocket.send_json({"error": "frame payload required"})
                continue

            try:
                frame_bytes = base64.b64decode(frame_base64)
            except Exception:
                await websocket.send_json({"error": "invalid base64 payload"})
                continue

            result = process_frame(frame_bytes)
            annotated_frame = result.get("annotated_frame") or frame_bytes
            if isinstance(annotated_frame, str):
                annotated_frame = annotated_frame.encode("utf-8")

            snapshot_path = result.get("snapshot_path")
            if not snapshot_path:
                snapshot_path = str(SNAPSHOT_DIR / f"{uuid.uuid4().hex}.png")
                try:
                    with open(snapshot_path, "wb") as f:
                        f.write(annotated_frame)
                except Exception:
                    snapshot_path = None

            incident = Incident(
                location=payload.get("location", "unknown"),
                severity=result.get("severity", "low"),
                vehicles=int(result.get("vehicles", 0)),
                accident=bool(result.get("accident", False)),
                annotated_frame=annotated_frame,
                snapshot_path=snapshot_path,
            )

            violations = result.get("violations") or []
            for violation_data in violations:
                violation = Violation(
                    violation_type=violation_data.get("type", "unknown"),
                    description=violation_data.get("description", ""),
                )
                incident.violations.append(violation)

            db.add(incident)
            db.commit()
            db.refresh(incident)

            incident_payload = {
                "id": incident.id,
                "vehicles": incident.vehicles,
                "violations": [
                    {"type": v.violation_type, "description": v.description}
                    for v in incident.violations
                ],
                "accident": incident.accident,
                "severity": incident.severity,
                "snapshot_path": incident.snapshot_path,
                "annotated_frame": base64.b64encode(incident.annotated_frame).decode("utf-8") if incident.annotated_frame else None,
            }

            if incident.accident:
                dispatch_alert(
                    {
                        "id": incident.id,
                        "timestamp": str(incident.timestamp),
                        "severity": incident.severity,
                        "location": incident.location,
                    }
                )

            await websocket.send_json(incident_payload)
    except WebSocketDisconnect:
        return
    finally:
        db.close()


@app.get("/report/{incident_id}")
def get_report(incident_id: int):
    try:
        report_path = generate_report(incident_id)
        return FileResponse(report_path, media_type="application/pdf", filename=os.path.basename(report_path))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Incident not found")


@app.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "is_admin": current_user.is_admin}
