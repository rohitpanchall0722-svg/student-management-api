from backend.app.models.enroll import Enrollment 
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException, status
from datetime import datetime, timezone
import logging
logger = logging.getLogger(__name__)

class StudentEnrollment :

    def new_enrollment(self, db:Session, student_id:int, course_id:int):
        new_enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id,
            enrolled_at=datetime.now(timezone.utc),
        )

        db.add(new_enrollment)
        db.commit()
        db.refresh(new_enrollment)

        return new_enrollment

    def get_enrollment_by_student_course(self,db:Session,student_id:int,course_id:int):
        stmt = select(Enrollment).where(Enrollment.student_id==student_id,
                                        Enrollment.course_id==course_id)
        return db.execute(stmt).scalar_one_or_none()

    def get_enrollments_by_student(self,db: Session,student_id: int
        ):
        stmt = select(Enrollment).where(Enrollment.student_id == student_id)

        return db.execute(stmt).scalars().all()  

    def get_all_enrollment(self,db:Session):
        stmt = select(Enrollment)
        return db.execute(stmt).scalars().all()

    def get_enrollment_by_courseid(self,db:Session,course_id:int):
        stmt = select(Enrollment).where(Enrollment.course_id==course_id)
        return db.execute(stmt).scalars().all()


   