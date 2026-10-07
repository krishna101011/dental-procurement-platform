from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import Base, engine
from app.models import *
from app.api.routes import router

app=FastAPI(title="Dental Procurement Platform API",version="0.1.0")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",")],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(router,prefix="/api/v1")
@app.get("/health")
def health(): return {"status":"ok","service":"dental-procurement-api"}
@app.on_event("startup")
def startup(): Base.metadata.create_all(bind=engine)
