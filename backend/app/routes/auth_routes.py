from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app import models
from backend.app.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    id: int
    full_name: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(models.DoctorAccount).filter(
        models.DoctorAccount.email == payload.email
    ).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    doctor = models.DoctorAccount(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    return RegisterResponse(id=doctor.id, full_name=doctor.full_name, email=doctor.email)


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm uses "username" as the field name by spec,
    # even though we're treating it as the doctor's email here - this is
    # what lets Swagger's built-in "Authorize" login box work out of the box.
    doctor = db.query(models.DoctorAccount).filter(
        models.DoctorAccount.email == form_data.username
    ).first()

    if doctor is None or not verify_password(form_data.password, doctor.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": doctor.email})
    return TokenResponse(access_token=access_token)