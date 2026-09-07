import os
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app import models

# In a real deployment this MUST come from an environment variable, never
# hardcoded - but for a local student project running only on localhost,
# a fixed dev secret is acceptable. If you ever deploy this beyond your
# own machine, move this to an env var before doing so.
SECRET_KEY = os.environ.get("CDSS_JWT_SECRET", "dev-only-secret-change-before-deploying")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8-hour login session, reasonable for a work shift

# tokenUrl points Swagger's "Authorize" button at the right login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# --- Password hashing ---
# Using bcrypt directly rather than passlib's CryptContext wrapper: current
# passlib releases have a known incompatibility with bcrypt>=4.1 (passlib
# expects an internal attribute bcrypt removed), which throws on the very
# first hash() call. Calling bcrypt directly avoids that broken layer
# entirely while using the exact same underlying hashing algorithm.

def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# --- JWT tokens ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# --- Route protection dependency ---
# Add `current_doctor: models.DoctorAccount = Depends(get_current_doctor)`
# as a parameter to any endpoint that should require login.

def get_current_doctor(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.DoctorAccount:
    payload = decode_access_token(token)
    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    doctor = db.query(models.DoctorAccount).filter(models.DoctorAccount.email == email).first()
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Doctor account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return doctor