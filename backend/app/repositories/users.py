from backend.app.models.users import StudentDetails
from backend.app.models.enroll import Enrollment
from backend.app.models.users import RefreshToken
from sqlalchemy.orm import Session
from sqlalchemy import delete, select
from fastapi import HTTPException, status
import logging
logger = logging.getLogger(__name__)

class StudentRepositories :

    #search the student by there registration id
    def get_by_registration_id(self,db:Session,register_id:str):
        try:
            stmt = select(StudentDetails).where(StudentDetails.registration_id==register_id)
            user = db.execute(stmt).scalar_one_or_none()
            return user
        except Exception:
            logger.exception("failed to fetch the student data")
            raise
    #search student by there email id
    def get_by_email(self,db:Session,email:str):
        try :
            stmt = select(StudentDetails).where(StudentDetails.email==email)
            studentemail = db.execute(stmt).scalar_one_or_none()
            return studentemail
        except Exception:
            logger.exception("failed to fetch the user data")
            raise

       #create an new student 
    def create_new_student(
                        self,
                        db:Session,
                        studentname:str,
                        email:str,
                        hashed_password:str,
                        phone_number: str | None = None,
                        address: str | None = None
                        ):
        new_student = StudentDetails(
            student_name = studentname,
            email = email,
            hashed_password = hashed_password,
            phone_number=phone_number,address=address,
            role = "student"
        )
        db.add(new_student)
        db.commit()
        db.refresh(new_student)

        return new_student

    
    # show all student measn search all students
    def show_all(self,db:Session,limit:int,page:int):
        try :
            offset = (page-1)*limit

            stmt = select(StudentDetails).offset(offset).limit(limit)
            return db.execute(stmt).scalars().all()
        except Exception:
            logger.exception("failed to fetch students")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="failed to fetch students")

    def delete_by_registration_id(self, db: Session, registration_id: int):
        student = self.get_by_registration_id(db, registration_id)
        if student is None:
            return None

        db.execute(delete(Enrollment).where(Enrollment.student_id == student.id))
        db.execute(delete(RefreshToken).where(RefreshToken.user_id == student.id))
        db.delete(student)
        db.commit()
        return student


    def update_student_profile(
    self,
    db: Session,
    student_id: int,
    student_data: dict
        ):
        student = db.get(StudentDetails, student_id)

        if student is None:
            return None

        for field, value in student_data.items():
            if value is not None:
                setattr(student, field, value)

        db.commit()
        db.refresh(student)

        return student
    
        
