from datetime import datetime
from pydantic import BaseModel, Field


class StudentDashBoard(BaseModel):
    registration_id:int
    student_name:str
    email:str
    register_date:str

class StudentProfileUpdate(BaseModel):
    student_name: str | None = None
    phone_number: str | None = None
    address: str | None = None    