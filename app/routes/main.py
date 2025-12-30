from fastapi import APIRouter, Depends, Form, HTTPException, BackgroundTasks
from sqlmodel import Session
from app.core.database import get_session
from app.models import Message
from app.core.config import get_settings
import hashlib
import os

router = APIRouter()
settings = get_settings()

from app.auth import AltchaService

@router.get("/altcha-challenge")
def get_altcha_challenge():
    service = AltchaService(settings.ALTCHA_SECRET, settings.ALTCHA_COMPLEXITY)
    return service.create_challenge()

@router.post("/contact")
def submit_contact_form(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    message: str = Form(...),
    altcha: str = Form(...),
    session: Session = Depends(get_session)
):
    service = AltchaService(settings.ALTCHA_SECRET)
    if not service.verify_solution(altcha):
        raise HTTPException(status_code=400, detail="Security verification failed")

    new_message = Message(
        name=name,
        email=email,
        phone=phone,
        message=message
    )
    session.add(new_message)
    session.commit()
    return {"status": "success", "message": "Message sent successfully"}
