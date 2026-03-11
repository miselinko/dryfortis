import os
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()  # loads .env in local dev; no-op in production

from fastapi import FastAPI, Request, Depends, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import date
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

import models
import database
from database import engine, get_db, check_db_connection

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dryfortis")

# Session middleware
SECRET_KEY = os.environ.get("SECRET_KEY", "dryfortis-dev-secret-change-in-production")
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=86400,
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")

# Templates
templates = Jinja2Templates(directory="templates")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

UPLOAD_DIR = "static/uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Ensure upload directories exist
for _cat in ["bitumenska", "poliuretanska", "revestech", "ostalo"]:
    os.makedirs(f"{UPLOAD_DIR}/{_cat}", exist_ok=True)

DEFAULT_SETTINGS = {
    "phone": "0658322779",
    "whatsapp": "381658322779",
    "email": "Isoterm25@gmail.com",
    "working_hours": "Pon–Sub: 07:00 – 20:00",
}


def load_settings() -> dict:
    """Load site settings from DB, fall back to defaults."""
    db = database.SessionLocal()
    try:
        rows = db.query(models.SiteSettings).all()
        if rows:
            return {**DEFAULT_SETTINGS, **{r.key: r.value for r in rows}}
    except Exception:
        pass
    finally:
        db.close()
    return DEFAULT_SETTINGS.copy()


def save_settings(data: dict):
    """Save site settings to DB."""
    db = database.SessionLocal()
    try:
        for key, value in data.items():
            row = db.query(models.SiteSettings).filter(models.SiteSettings.key == key).first()
            if row:
                row.value = value
            else:
                db.add(models.SiteSettings(key=key, value=value))
        db.commit()
    finally:
        db.close()


# Make settings available in all templates
templates.env.globals["load_site"] = load_settings

# SEO globals
BASE_URL = "https://dryfortis.rs"
templates.env.globals["BASE_URL"] = BASE_URL


# ─────────────────────────────────────────
# Auth helper
# ─────────────────────────────────────────

def is_admin(request: Request) -> bool:
    return bool(request.session.get("admin"))


# ─────────────────────────────────────────
# Public routes
# ─────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    recent_images = (
        db.query(models.GalleryImage)
        .order_by(models.GalleryImage.created_at.desc())
        .limit(6)
        .all()
    )
    return templates.TemplateResponse("index.html", {
        "request": request,
        "recent_images": recent_images,
        "active_page": "home",
    })


@app.get("/bitumenska", response_class=HTMLResponse)
async def bitumenska(request: Request, db: Session = Depends(get_db)):
    images = (
        db.query(models.GalleryImage)
        .filter(models.GalleryImage.category == "bitumenska")
        .order_by(models.GalleryImage.created_at.desc())
        .all()
    )
    return templates.TemplateResponse("bitumenska.html", {
        "request": request,
        "images": images,
        "active_page": "bitumenska",
    })


@app.get("/poliuretanska", response_class=HTMLResponse)
async def poliuretanska(request: Request, db: Session = Depends(get_db)):
    images = (
        db.query(models.GalleryImage)
        .filter(models.GalleryImage.category == "poliuretanska")
        .order_by(models.GalleryImage.created_at.desc())
        .all()
    )
    return templates.TemplateResponse("poliuretanska.html", {
        "request": request,
        "images": images,
        "active_page": "poliuretanska",
    })


@app.get("/revestech", response_class=HTMLResponse)
async def revestech(request: Request, db: Session = Depends(get_db)):
    images = (
        db.query(models.GalleryImage)
        .filter(models.GalleryImage.category == "revestech")
        .order_by(models.GalleryImage.created_at.desc())
        .all()
    )
    return templates.TemplateResponse("revestech.html", {
        "request": request,
        "images": images,
        "active_page": "revestech",
    })


@app.get("/galerija", response_class=HTMLResponse)
async def galerija(request: Request, db: Session = Depends(get_db)):
    all_images = (
        db.query(models.GalleryImage)
        .order_by(models.GalleryImage.created_at.desc())
        .all()
    )
    grouped = {
        "bitumenska": [img for img in all_images if img.category == "bitumenska"],
        "poliuretanska": [img for img in all_images if img.category == "poliuretanska"],
        "revestech": [img for img in all_images if img.category == "revestech"],
        "ostalo": [img for img in all_images if img.category == "ostalo"],
    }
    return templates.TemplateResponse("galerija.html", {
        "request": request,
        "all_images": all_images,
        "grouped": grouped,
        "active_page": "galerija",
    })


@app.get("/o-nama", response_class=HTMLResponse)
async def o_nama(request: Request, db: Session = Depends(get_db)):
    workers = db.query(models.Worker).order_by(models.Worker.order, models.Worker.id).all()
    return templates.TemplateResponse("o_nama.html", {
        "request": request,
        "workers": workers,
        "active_page": "o_nama",
    })


@app.get("/kontakt", response_class=HTMLResponse)
async def kontakt(request: Request, success: Optional[str] = None):
    return templates.TemplateResponse("kontakt.html", {
        "request": request,
        "success": success == "1",
        "active_page": "kontakt",
    })


@app.get("/sitemap.xml", response_class=Response)
async def sitemap():
    today = date.today().isoformat()
    pages = [
        ("",               "1.0", "weekly"),
        ("/bitumenska",    "0.9", "monthly"),
        ("/poliuretanska", "0.9", "monthly"),
        ("/revestech",     "0.9", "monthly"),
        ("/galerija",      "0.7", "weekly"),
        ("/o-nama",        "0.6", "monthly"),
        ("/kontakt",       "0.5", "monthly"),
    ]
    urls = ""
    for path, priority, freq in pages:
        urls += f"""
  <url>
    <loc>{BASE_URL}{path}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>"""
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}
</urlset>"""
    return Response(content=xml, media_type="application/xml")


@app.get("/robots.txt", response_class=Response)
async def robots():
    content = f"""User-agent: *
Allow: /
Disallow: /admin/

Sitemap: {BASE_URL}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")


@app.get("/health")
async def health():
    db_ok = check_db_connection()
    status = "ok" if db_ok else "degraded"
    return JSONResponse({"status": status, "db": db_ok}, status_code=200 if db_ok else 503)


@app.post("/kontakt")
async def kontakt_post(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    message: str = Form(...),
    db: Session = Depends(get_db),
):
    msg = models.ContactMessage(name=name, phone=phone, message=message)
    db.add(msg)
    db.commit()
    return RedirectResponse(url="/kontakt?success=1", status_code=303)


# ─────────────────────────────────────────
# Admin routes
# ─────────────────────────────────────────

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    if request.session.get("admin"):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "error": None,
    })


@app.post("/admin/login")
async def admin_login_post(
    request: Request,
    password: str = Form(...),
):
    if password == ADMIN_PASSWORD:
        request.session["admin"] = True
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "error": "Pogrešna lozinka. Pokušajte ponovo.",
    })


@app.get("/admin/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=302)


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    unread_count = db.query(models.ContactMessage).filter(
        models.ContactMessage.is_read == False
    ).count()
    total_images = db.query(models.GalleryImage).count()
    recent_messages = (
        db.query(models.ContactMessage)
        .order_by(models.ContactMessage.created_at.desc())
        .limit(5)
        .all()
    )

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "unread_count": unread_count,
        "total_images": total_images,
        "recent_messages": recent_messages,
        "active_admin": "dashboard",
    })


@app.get("/admin/galerija", response_class=HTMLResponse)
async def admin_galerija(request: Request, db: Session = Depends(get_db)):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    images = (
        db.query(models.GalleryImage)
        .order_by(models.GalleryImage.created_at.desc())
        .all()
    )
    return templates.TemplateResponse("admin/galerija.html", {
        "request": request,
        "images": images,
        "active_admin": "galerija",
    })


@app.post("/admin/galerija/upload")
async def admin_upload(
    request: Request,
    file: UploadFile = File(...),
    category: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    allowed_categories = ["bitumenska", "poliuretanska", "revestech", "ostalo"]
    if category not in allowed_categories:
        category = "ostalo"

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"

    unique_name = f"{uuid.uuid4().hex}{ext}"
    upload_path = f"{UPLOAD_DIR}/{category}/{unique_name}"

    contents = await file.read()
    with open(upload_path, "wb") as f:
        f.write(contents)

    img = models.GalleryImage(
        category=category,
        filename=f"/static/uploads/{category}/{unique_name}",
        description=description.strip() or None,
    )
    db.add(img)
    db.commit()

    return RedirectResponse(url="/admin/galerija", status_code=303)


@app.post("/admin/galerija/delete/{image_id}")
async def admin_delete_image(
    request: Request,
    image_id: int,
    db: Session = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    img = db.query(models.GalleryImage).filter(models.GalleryImage.id == image_id).first()
    if img:
        if img.filename.startswith("/static/uploads/"):
            local_path = img.filename.lstrip("/")
            if os.path.exists(local_path):
                os.remove(local_path)
        db.delete(img)
        db.commit()

    return RedirectResponse(url="/admin/galerija", status_code=303)


@app.get("/admin/poruke", response_class=HTMLResponse)
async def admin_poruke(request: Request, db: Session = Depends(get_db)):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    messages = (
        db.query(models.ContactMessage)
        .order_by(models.ContactMessage.created_at.desc())
        .all()
    )

    db.query(models.ContactMessage).filter(
        models.ContactMessage.is_read == False
    ).update({"is_read": True})
    db.commit()

    return templates.TemplateResponse("admin/poruke.html", {
        "request": request,
        "messages": messages,
        "active_admin": "poruke",
    })


@app.post("/admin/poruke/delete/{message_id}")
async def admin_delete_message(
    request: Request,
    message_id: int,
    db: Session = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    msg = db.query(models.ContactMessage).filter(
        models.ContactMessage.id == message_id
    ).first()
    if msg:
        db.delete(msg)
        db.commit()

    return RedirectResponse(url="/admin/poruke", status_code=303)


@app.get("/admin/radnici", response_class=HTMLResponse)
async def admin_radnici(request: Request, db: Session = Depends(get_db)):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    workers = db.query(models.Worker).order_by(models.Worker.order, models.Worker.id).all()
    return templates.TemplateResponse("admin/radnici.html", {
        "request": request,
        "workers": workers,
        "active_admin": "radnici",
        "saved": request.query_params.get("saved") == "1",
    })


@app.post("/admin/radnici/add")
async def admin_radnici_add(
    request: Request,
    name: str = Form(...),
    role: str = Form(...),
    description: str = Form(""),
    order: int = Form(0),
    db: Session = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    worker = models.Worker(
        name=name.strip(),
        role=role.strip(),
        description=description.strip() or None,
        order=order,
    )
    db.add(worker)
    db.commit()
    return RedirectResponse(url="/admin/radnici?saved=1", status_code=303)


@app.post("/admin/radnici/edit/{worker_id}")
async def admin_radnici_edit(
    request: Request,
    worker_id: int,
    name: str = Form(...),
    role: str = Form(...),
    description: str = Form(""),
    order: int = Form(0),
    db: Session = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    worker = db.query(models.Worker).filter(models.Worker.id == worker_id).first()
    if worker:
        worker.name = name.strip()
        worker.role = role.strip()
        worker.description = description.strip() or None
        worker.order = order
        db.commit()
    return RedirectResponse(url="/admin/radnici?saved=1", status_code=303)


@app.post("/admin/radnici/delete/{worker_id}")
async def admin_radnici_delete(
    request: Request,
    worker_id: int,
    db: Session = Depends(get_db),
):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    worker = db.query(models.Worker).filter(models.Worker.id == worker_id).first()
    if worker:
        db.delete(worker)
        db.commit()
    return RedirectResponse(url="/admin/radnici", status_code=303)


@app.get("/admin/podesavanja", response_class=HTMLResponse)
async def admin_podesavanja(request: Request):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    return templates.TemplateResponse("admin/podesavanja.html", {
        "request": request,
        "site": load_settings(),
        "active_admin": "podesavanja",
        "saved": request.query_params.get("saved") == "1",
    })


@app.post("/admin/podesavanja")
async def admin_podesavanja_post(
    request: Request,
    phone: str = Form(...),
    whatsapp: str = Form(...),
    email: str = Form(...),
    working_hours: str = Form(...),
):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    whatsapp_clean = whatsapp.replace("+", "").replace(" ", "")
    save_settings({
        "phone": phone.strip(),
        "whatsapp": whatsapp_clean,
        "email": email.strip(),
        "working_hours": working_hours.strip(),
    })
    return RedirectResponse(url="/admin/podesavanja?saved=1", status_code=303)
