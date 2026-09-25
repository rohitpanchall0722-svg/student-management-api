import logging
from fastapi import FastAPI,Request,HTTPException,status
from fastapi.responses import JSONResponse
from backend.app.models.users import StudentDetails
from backend.app.database.database import Base,engine
from backend.app.core.logger import setup_logger
from backend.app.routers.users import router as user_router
from backend.app.routers.admin import router as admin_router
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.secuirty_header import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)
Base.metadata.create_all(bind=engine)

setup_logger()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.include_router(user_router)
app.include_router(admin_router)
@app.get("/")
def home():
    return {
        "message":"this is the start of student management api"
    }

@app.exception_handler(Exception)
def global_exception_handler(request:Request,exp:Exception):
    logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "details":"Internal Server Error"
        }
    )