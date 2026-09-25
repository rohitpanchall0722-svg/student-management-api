from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.repositories.course import CourseRepositories
from backend.app.repositories.enroll import StudentEnrollment


class StudentEnrollmentService:
	def __init__(self):
		self.course_repository = CourseRepositories()
		self.enrollment_repository = StudentEnrollment()

	def enroll(self, db: Session, student_id: int, public_course_id: int):
		course = self.course_repository.get_course_by_id(db, public_course_id)
		if course is None:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
								detail="Course not found")

		existing = self.enrollment_repository.get_enrollment_by_student_course(
			db, student_id, course.id
		)
		if existing is not None:
			raise HTTPException(status_code=status.HTTP_409_CONFLICT,
								detail="Student is already enrolled in this course")

		return self.enrollment_repository.new_enrollment(db, student_id, course.id)

	def get_student_by_enrollments(self, db: Session, student_id: int):
		return self.enrollment_repository.get_enrollments_by_student(db, student_id)


	def show_all_enrollment(self,db:Session,limit:int,page:int):
		return self.course_repository.get_all_courses(db=db,limit=limit,page=page)

	def show_specific_enroll(self, db: Session, course_id: int):
		return self.enrollment_repository.get_enrollment_by_courseid(
        db=db,
        course_id=course_id
    )