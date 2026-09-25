from backend.app.database.database import Base
from sqlalchemy import Column, Integer, DateTime, Sequence, ForeignKey

class Enrollment(Base):
    __tablename__ = "enrollment_details"
    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, Sequence("enrollment_number_sequence", start=20001), unique=True, nullable=False)
    student_id = Column(Integer, ForeignKey("student_data.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    enrolled_at = Column(DateTime, nullable=False)