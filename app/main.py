from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import init_db
from app.core.scheduler import start_scheduler, get_cached_videos
from app.routes.main import router as main_router
from app.routes.admin import router as admin_router

import os

settings = get_settings()

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
app.include_router(main_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/admin")

# Static Files
# Serve 'public' directory as /static
public_dir = os.path.join(os.path.dirname(__file__), '..', 'public')
if not os.path.exists(public_dir):
    os.makedirs(public_dir)

app.mount("/static", StaticFiles(directory=public_dir), name="static")

# Templates
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
templates = Jinja2Templates(directory=templates_dir)

# Page Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(name="index.html", request=request)

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(name="about.html", request=request)

@app.get("/ministry", response_class=HTMLResponse)
async def ministry(request: Request):
    return templates.TemplateResponse(name="ministry.html", request=request)

@app.get("/resources", response_class=HTMLResponse)
async def resources(request: Request):
    return templates.TemplateResponse(
        name="resources.html",
        request=request,
        context={"videos": get_cached_videos()}
    )

@app.get("/tithing", response_class=HTMLResponse)
async def tithing(request: Request):
    return templates.TemplateResponse(name="tithing.html", request=request)

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse(name="contact.html", request=request)

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(name="login.html", request=request)

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse(name="admin/dashboard.html", request=request)

@app.on_event("startup")
def on_startup():
    init_db()
    start_scheduler()
