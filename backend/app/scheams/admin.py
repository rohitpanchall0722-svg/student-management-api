from pydantic import BaseModel,EmailStr,Field
from datetime import datetime

class AdminRegistration(BaseModel):
    admin_name:str = Field(min_length=3)
    email:EmailStr
    password:str=Field(min_length=6,max_length=32)

class AdminResponse(BaseModel):
    admin_id:int
    admin_name:str
    email:EmailStr
    role:str

class AdminLoginRequest(BaseModel):
    admin_id:int
    password:str


class CourseCreate(BaseModel):
    course_name: str
    description: str | None = None
    live_at: datetime | None = None
    duration: int
