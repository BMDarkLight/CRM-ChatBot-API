import string
import secrets
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from fastapi import HTTPException
from pymongo import MongoClient
import os

def generate_random_string(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", generate_random_string(32))
ALGORITHM = os.environ.get("AUTH_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get("AUTH_TOKEN_EXPIRE", 120)

users_db = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017/")).crm.users

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = users_db.find_one({"username": username})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")