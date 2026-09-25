from pydantic import BaseModel,ConfigDict,EmailStr,Field


class StudentRegistration(BaseModel):
    student_name:str = Field(min_length=2)
    email:EmailStr
    password:str=Field(min_length=6,max_length=12)
    phone_number: str | None = Field(default=None, min_length=10)
    address: str | None = None



class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    registration_id:int     
    student_name:str
    email:EmailStr
    phone_number : str | None = None
    address : str | None=None


class LoginRequest(BaseModel):
    registration_id:int = Field(max_length=6)
    password:str = Field(min_length=6,max_length=12)

class LoginResponse(BaseModel):
    registration_id:int

class TokenResponse(BaseModel):
    access_token:str
    refresh_token:str
    token_type:str    

class RefreshTokenRequest(BaseModel):
    refresh_token: str    




    