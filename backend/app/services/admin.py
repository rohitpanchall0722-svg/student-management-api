from sqlalchemy.orm import Session
from backend.app.repositories.admin import  AdminRepositories 
from backend.app.core.secuirty import (hash_password,verify_password,
                                create_access_token,verify_access_token,
                                verify_refresh_access_token,refresh_token)
from fastapi import status,HTTPException
from backend.app.repositories.refresh_token import RefreshTokenRepositiory
from backend.app.core.redis import redis_client
from backend.app.models.users import AdminDetails
import logging
logger = logging.getLogger(__name__)
from backend.app.repositories.course import CourseRepositories
from backend.app.repositories.users import StudentRepositories
admin_repo = AdminRepositories()
refresh_token_repo = RefreshTokenRepositiory()
course_repository = CourseRepositories()


class AdminService():
    def __init__(self):
        self.admin_repo = AdminRepositories()
        self.refresh_token_repo = RefreshTokenRepositiory()
        self.student_repo = StudentRepositories()

    def create_admin(
    self,
    db: Session,
    admin_name: str,
    email: str,
    password: str
):
        logger.info("admin registration start")
        existing_email = self.admin_repo.get_by_email(
        db,
        email
    )
        if existing_email is not None:
            logger.warning("this email already exists")
            raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )
        hashed_password = hash_password(password)

        new_admin = self.admin_repo.create_new_admin(
        db=db,
        admin_data={
            "admin_name": admin_name,
            "email": email,
            "hashed_pass": hashed_password
        }
    )
        logger.info("admin registration complete")
        return new_admin

    def admin_login(self,db:Session,admin_id:int,password:str):
        logger.info("admin login request recived")
        admin = self.admin_repo.get_by_admin_id(
            db,
            admin_id
        )
        logger.info("admin login request complete")
        if admin is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="admin ID or password is wrong")
        if not verify_password(
            password,
            admin.hashed_pass
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="admin ID or password is wrong"
            )
        access_token = create_access_token(
            data={
                "sub":str(admin.admin_id),
                "role":"admin"
            }
        )
        refresh_token_value, expires_at = refresh_token(
            data={
                "sub":str(admin.admin_id),
                "role":"admin",
                "type":"refresh"
            }
        )
        self.refresh_token_repo.create(
            db=db,
            admin_id=admin.admin_id,
            token=refresh_token_value,
            expire_at=expires_at
        )
        db.commit()
        logger.info("admin login complete")
        return {
            "access_token":access_token,
            "refresh_token":refresh_token_value,
            "token_type":"bearer"
        }

    def admin_logout(self,db:Session,refresh_token:str,access_token:str | None = None):
             logger.info("logout request recived")
             if access_token:
                 try:
                     payload = verify_access_token(access_token)
                 except HTTPException:
                     raise
                 jti = payload.get("jti")
                 if jti:
                     try:
                         redis_client.setex(f"blacklist:{jti}", 1800, "revoked")
                     except Exception:
                         logger.exception("Failed to blacklist admin access token jti=%s", jti)
             token = self.refresh_token_repo.get_by_token(
                  db=db,
                  token=refresh_token
             )
             if token is None:
                  raise HTTPException(
                       status_code=status.HTTP_401_UNAUTHORIZED,
                       detail="Invalid refresh token"
                  )
             if token.admin_id is None:
                  raise HTTPException(
                       status_code=status.HTTP_401_UNAUTHORIZED,
                       detail="Refresh token does not belong to an admin account"
                  )
             if access_token:
                 try:
                     payload = verify_access_token(access_token)
                     token_owner = str(token.admin_id)
                     if payload.get("sub") != token_owner:
                         raise HTTPException(
                             status_code=status.HTTP_401_UNAUTHORIZED,
                             detail="Access token does not match this admin account"
                         )
                 except HTTPException:
                     raise
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

    def add_course(self,db:Session,course_data:dict):
        logger.info("create course request recived")
        new_course = course_repository.create_course(
            db=db,
            course_data=course_data
        )
        logger.info("create course request complete")
        return new_course

    def get_course_by_id(self,db:Session,course_id:int):
        logger.info("get course by id request recived")
        course = course_repository.get_course_by_id(
            db=db,
            course_id=course_id
        )
        logger.info("get course by id request complete")
        return course

    def show_all_courses(self,db:Session,page:int,limit:int):
        logger.info("get all courses request recived")
        courses = course_repository.get_all_courses(
            db=db,page=page,limit=limit
        )
        logger.info("get all courses request complete")
        return courses

    def show_all_students(self, 
                          db: Session,
                          page:int,
                          limit:int):
        return self.student_repo.show_all(db=db,
                                          page=page,
                                          limit=limit)

    def get_student_by_registration_id(self, db: Session, registration_id: int):
        student = self.student_repo.get_by_registration_id(db, registration_id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Student not found")
        return student

    def remove_student(self, db: Session, registration_id: int):
        student = self.student_repo.delete_by_registration_id(db, registration_id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Student not found")
        return {"message": "Student removed successfully"}
    