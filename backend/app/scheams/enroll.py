from datetime import datetime
from pydantic import BaseModel, ConfigDict

class EnrollmentCreate(BaseModel):
    course_id:int

class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    enrollment_id: int
    student_id: int
    course_id: int
    enrolled_at: datetime    