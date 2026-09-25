from backend.app.models.course import Course
from sqlalchemy.orm import Session
from sqlalchemy import select,delete
from fastapi import HTTPException,status
import logging
logger = logging.getLogger(__name__)

class CourseRepositories:

    # create new course
    def create_course(self,db:Session,course_data:dict):
        try:
            new_course = Course(
                course_name=course_data["course_name"],
                description=course_data.get("description"),
                live_at=course_data.get("live_at"),
                duration=course_data.get("duration"),
                status="draft"
            )
            db.add(new_course)
            db.commit()
            db.refresh(new_course)
            return new_course
        except Exception:
            db.rollback()
            logger.exception("failed to create new course")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="failed to create new course")


        # search course by course_id
    def get_course_by_id(self,db:Session,course_id:int):
        try:
            stmt = select(Course).where(Course.course_id==course_id)
            course = db.execute(stmt).scalar_one_or_none()
            return course
        except Exception:
            logger.exception("failed to fetch the course data")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="failed to fetch the course data")


    def get_all_courses(self,db:Session,page:int,limit:int):
        try:
            offset = (page-1)*limit
            stmt = select(Course).offset(offset).limit(limit)
            courses = db.execute(stmt).scalars().all()
            return courses
        except Exception:
            logger.exception("failed to fetch all courses")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="failed to fetch all courses")    

    def remove_course(self,db:Session,course_id:int):
        course = self.get_course_by_id(db,course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="course not found")
        db.delete(course)
        db.commit()
        return course