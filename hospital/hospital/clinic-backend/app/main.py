from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import engine, Base
from app.routers import auth, appointments, medical_records, files, medications, telegram, chatbot, visit, patient_notes, doctors, clinic_owner
from app.services.reminder_scheduler import start_scheduler

def create_app() -> FastAPI:
    app = FastAPI(
        title="نظام إدارة العيادات",
        description="FastAPI Backend for Clinic Management System",
        version="1.0.0"
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # adjust to specific origins in prod
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize DB (creates tables on start)
    try:
        Base.metadata.create_all(bind=engine)
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE doctors ADD COLUMN IF NOT EXISTS slot_duration_minutes INTEGER DEFAULT 15;"))
            conn.execute(text("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS patient_name VARCHAR(200);"))
            conn.execute(text("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS patient_phone VARCHAR(50);"))
            conn.commit()
        print("[OK] Database initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")

    # Register routers matching backend specifications
    app.include_router(auth.router, prefix="/api")
    app.include_router(appointments.router, prefix="/api")
    app.include_router(medical_records.router, prefix="/api")
    app.include_router(files.router, prefix="/api")
    app.include_router(medications.router, prefix="/api")
    app.include_router(telegram.router, prefix="/api")
    app.include_router(chatbot.router, prefix="/api")
    app.include_router(visit.router, prefix="/api")
    app.include_router(patient_notes.router, prefix="/api")
    app.include_router(doctors.router, prefix="/api")
    app.include_router(clinic_owner.router, prefix="/api")


    # Start medication reminder scheduler (background thread)
    try:
        start_scheduler()
        print("[OK] Medication + Appointment reminder scheduler started.")
    except Exception as e:
        print(f"[WARN] Reminder scheduler failed to start: {e}")

    # Mount static files (index.html, style.css, script.js)
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if os.path.exists(os.path.join(frontend_dir, "index.html")):
        app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")

        @app.get("/")
        async def serve_index():
            return FileResponse(os.path.join(frontend_dir, "index.html"))
        
        @app.get("/style.css")
        async def serve_css():
            return FileResponse(os.path.join(frontend_dir, "style.css"))

        @app.get("/script.js")
        async def serve_js():
            return FileResponse(os.path.join(frontend_dir, "script.js"))


    @app.get("/api/health")
    async def health():
        return {
            "success": True,
            "message": "الخادم يعمل بشكل طبيعي",
            "status": "healthy"
        }

    # Custom general error handling
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        print(f"Server Error: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "خطأ غير متوقع في الخادم",
                "error": str(exc)
            }
        )

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=True)
