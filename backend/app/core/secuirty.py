import logging
from uuid import uuid4
from datetime import timezone,timedelta,datetime

from pwdlib import PasswordHash
password_hash = PasswordHash.recommended()
from jose import jwt,JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends,HTTPException,status
from sqlalchemy.orm import Session
from sqlalchemy import select
from redis.exceptions import RedisError

from backend.app.models.users import StudentDetails,AdminDetails
from backend.app.database.database import get_db
from backend.app.core.config import settings
password_hash = PasswordHash.recommended()
from uuid import uuid4
from datetime import timezone,timedelta,datetime
from backend.app.core.redis import redis_client

logger = logging.getLogger(__name__)
password_hash = PasswordHash.recommended()
security = HTTPBearer()

# hash the user password
def hash_password(password:str)->str:
    return password_hash.hash(password)
#the the user hash password and plain password while login
def verify_password(plain_password,hash_password:str) -> bool :
    return password_hash.verify(
        plain_password,
        hash_password
    )
# after login it create access token
def create_access_token(
                        data:dict,
                        expire_mintues:int=30
                        ):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expire_mintues)

    to_encode.update({
        "iat":now,
        "exp":expire,
        "jti":str(uuid4()),
        "type":"access"
    })
    payload = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHEM
    )
    return payload
#it verify that the access token is correct or not while using
def verify_access_token(token: str):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHEM]
        )

        user_id = payload.get("sub")
        role = payload.get("role")
        token_type = payload.get("type")

        if (
            user_id is None
            or role is None
            or token_type != "access"
        ):
            raise credentials_exception

        return payload

    except JWTError:
        raise credentials_exception


def is_token_blacklisted(jti: str) -> bool:
    if not jti:
        return False

    try:
        return bool(redis_client.exists(f"blacklist:{jti}"))
    except RedisError:
        logger.exception("Redis blacklist lookup failed for jti=%s", jti)
        return False
#each user and its role "studnet" or "admin" it just get what the role
# of current user and help in autrizaton   
     
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )

    payload = verify_access_token(token)
    jti = payload.get("jti")
    if not jti :
        raise credentials_exception
    if is_token_blacklisted(jti):
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has been revoked"
        )
    user_id = payload.get("sub")
    role = payload.get("role")

    if role == "student":

        user = db.execute(
            select(StudentDetails).where(
                StudentDetails.registration_id == user_id
            )
        ).scalar_one_or_none()

    elif role == "admin":

        user = db.execute(
            select(AdminDetails).where(
                AdminDetails.admin_id == user_id
            )
        ).scalar_one_or_none()

    else:
        raise credentials_exception

    if user is None:
        raise credentials_exception

    return user

# basically it check the current user role and  requird role is match or not 
def require_role(required_role: str):

    def check_role(
        current_user=Depends(get_current_user)
    ):

        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required role"
            )

        return current_user

    return check_role


def refresh_token(data:dict,expire_time:int=7):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=expire_time)
    to_encode.update({
        "iat":now,
        "exp":expire,
        "jti":str(uuid4()),
        "type":"refresh"
    })
    token = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHEM
    )
    return token,expire

def verify_refresh_access_token(token:str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="not a vaild refresh access token ")
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHEM]
        )
        user_id = payload.get("sub")
        token_type = payload.get("type")
        jti = payload.get("jti")
        if user_id is None or token_type!='refresh' or not jti :
            raise credentials_exception
        return token_type,user_id,jti
    except JWTError:
        raise credentials_exception