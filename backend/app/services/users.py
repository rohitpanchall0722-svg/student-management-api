from sqlalchemy.orm import Session
from backend.app.repositories.users import StudentRepositories
from backend.app.core.secuirty import (hash_password,verify_password,
                                create_access_token,verify_access_token,
                                verify_refresh_access_token,refresh_token)
from fastapi import status,HTTPException
from backend.app.core.redis import redis_client
from backend.app.scheams.users import StudentRegistration
from backend.app.repositories.refresh_token import RefreshTokenRepositiory
import logging
logger = logging.getLogger(__name__)
class StudentService():
    def __init__(self):
        self.user_repo = StudentRepositories()
        self.refresh_token_repo=RefreshTokenRepositiory()

    def create_student(self,
    student_data:StudentRegistration,
    db:Session
    ):        
        logger.info("user regustration start")
        existing_email = self.user_repo.get_by_email(
            db,
            student_data.email
        )
        if existing_email :
            logger.warning("this email  is alreay exist")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="try with an diffrent email")

        hashed_password = hash_password(
            student_data.password
        )
        new_student =  self.user_repo.create_new_student(
            db=db,
            studentname=student_data.student_name,
            email=student_data.email,
            hashed_password=hashed_password,
            phone_number=student_data.phone_number,
               address=student_data.address
        )
        logger.info("student registation complete")
        return new_student

    

    def login_user(self,
                       db:Session,
                       register_id:int,
                       password:str):
          logger.info("login request recived")
          user = self.user_repo.get_by_registration_id(
                db,register_id
           )
          if user is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="registration is or password is wrong")
          if not verify_password(
                password,
                user.hashed_password
           ):
                raise HTTPException(
                     status_code=status.HTTP_401_UNAUTHORIZED,
                     detail="registration id or password is wrong"
                )
          logger.info("login request complete")
          access_token =  create_access_token(
                data={"sub":str(user.registration_id),
                      "role":"student"}
           )
          refresh_token_value, expires_at = refresh_token(
                data={
                     "sub":str(user.registration_id),
                     "role":"student",
                     "type":"refresh"
                }
           )
           
          self.refresh_token_repo.create(
        db=db,
        user_id=user.id,
        token=refresh_token_value,
        expire_at=expires_at,

        )
           
          db.commit()
          logger.info("access token and refresh token created")

          return {
        "access_token": access_token,
        "refresh_token": refresh_token_value,
        "token_type": "bearer"
    }

          #logout user
    def logout_user(self,db:Session,refresh_token:str,access_token:str):
         logger.info("logout request recived")
         jti = None
         if access_token:
             payload = verify_access_token(access_token)
             jti = payload.get("jti")
             if not jti :
                  raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                      detail="invalid access token")
         token = self.refresh_token_repo.get_by_token(
              db=db,
              token=refresh_token
         )
         if token is None:
              raise HTTPException(
                   status_code=status.HTTP_401_UNAUTHORIZED,
                   detail="Invalid refresh token"
              )
         if jti:
             try:
                 redis_client.setex(
                      f"blacklist:{jti}",
                      1800,
                      "revoked"
                 )
             except Exception:
                 logger.exception("Failed to blacklist access token jti=%s", jti)
         if token.revoked_at:
              raise HTTPException(
                   status_code=status.HTTP_401_UNAUTHORIZED,
                   detail="Refresh token has already been revoked"
              )
         self.refresh_token_repo.revoke_token(
              db=db,
              refresh_token =token 
         )
         
         db.commit()
         return {
              "message":"logout successfully"
         }