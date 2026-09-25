from backend.app.repositories.users import StudentRepositories
from backend.app.scheams.student import StudentDashBoard 
from sqlalchemy.orm import Session
from uuid import uuid4
from backend.app.repositories.course import CourseRepositories
from backend.app.core.redis import redis_client
from backend.app.core.secuirty import verify_refresh_access_token
from backend.app.repositories.refresh_token import RefreshTokenRepositiory
from backend.app.core.secuirty import create_access_token,refresh_token
import json
from fastapi import status, HTTPException
import logging
loggeer = logging.getLogger(__name__)
class StudentServiceDashboard:
    def __init__(self):
        self.student_repository = StudentRepositories()
        self.course_repository = CourseRepositories()
        self.refersh_token_repo = RefreshTokenRepositiory()

        # get student dashboard by registration_id
    def get_student_dashboard(self, db: Session, registration_id: int) -> dict:
        student = self.student_repository.get_by_registration_id(
            db,registration_id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Student not found")
        return {
            "message": "welcome to student management system",
            "registration_id": student.registration_id,
            "student_name": student.student_name,
            "email": student.email,
            "register_date": student.created_at.strftime("%d %B %Y")
        }
    
    def get_course_by_id(self, db: Session, course_id: int):
        course = self.course_repository.get_course_by_id(
            db=db,
            course_id=course_id
        )
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Course not found")
        return course

    def show_all_courses(self, db: Session,limit:int,page:int):
        cached_courses = redis_client.get("courses:all")
        if cached_courses:
            loggeer.info("HIT")
            return json.loads(cached_courses)
        loggeer.info("MISS")
        courses = self.course_repository.get_all_courses(
            db=db,page=page,limit=limit
            )
        course_data = [
        {
            "course_id": course.course_id,
            "course_name": course.course_name,
            "description": course.description,
            "live_at": course.live_at.isoformat() if course.live_at else None,
            "duration": course.duration,
            "status": course.status
        }
        for course in courses
    ]
        redis_client.setex(
        "courses:all",
        300,
        json.dumps(course_data)
    )
        return course_data
        

    def update_student_profile(
             self,
        db: Session,
        student_id: int,
        student_data: dict):
        student = self.student_repository.update_student_profile(
        db=db,
        student_id=student_id,
        student_data=student_data
        )
        if student is None:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
            )

        return student

    def refresh_access_token(self,db:Session,refresh_token_value:str):
        token_type, user_id, jti = verify_refresh_access_token(refresh_token_value)

        token = self.refersh_token_repo.get_by_token(db=db,token=refresh_token_value)

        if token is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="invalid access ")
        if token.revoked_at : 
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="token already revoked")

        self.refersh_token_repo.revoke_token(db=db, refresh_token=token)

        new_access_token = create_access_token(
            data={
                "sub": str(user_id),
                "role": "student"
            }
        )

        new_refresh_token, expires_at = refresh_token(
            data={
                "sub": str(user_id),
                "role": "student"
            }
        )

        self.refersh_token_repo.create(
            db=db,
            user_id=token.user_id,
            token=new_refresh_token,
            expire_at=expires_at
        )
        db.commit()
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }






