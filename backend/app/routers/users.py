from fastapi import APIRouter,Depends,status,Query,Header
from typing import List
from backend.app.scheams.users import StudentRegistration,StudentResponse
from backend.app.scheams.student import StudentProfileUpdate
from backend.app.database.database import get_db
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
security = HTTPBearer()
from backend.app.services.users import StudentService
from fastapi.security import OAuth2PasswordRequestForm
from backend.app.scheams.users import TokenResponse
from backend.app.core.secuirty import get_current_user,require_role
from backend.app.services.student import StudentServiceDashboard
from backend.app.services.enroll import StudentEnrollmentService
from backend.app.scheams.enroll import EnrollmentCreate, EnrollmentResponse
from fastapi import Request
from backend.app.core.rate_limiter import rate_limit,rate_limit_dependency
from backend.app.scheams.users import RefreshTokenRequest
import logging
logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/students",
    tags=["Students"]
)
student_service = StudentService()
student_dashboard_service = StudentServiceDashboard()
student_enrollment_service = StudentEnrollmentService()
@router.post("/registration",response_model=StudentResponse,
             status_code=status.HTTP_201_CREATED)
def studentegistration(
                        request: Request,
                        new_student:StudentRegistration,
                        db:Session=Depends(get_db)
                          ):
    logger.info("new refistation request recived")
    rate_limit(request=request, key_prefix="student_registration", limit=5, window=60)
    new_registation =  student_service.create_student(
        db=db,
        student_data=new_student
    )
    logger.info("new registration done")
    return new_registation

@router.post("/student_login",response_model=TokenResponse)
def login(request:Request,student:OAuth2PasswordRequestForm=Depends(),
          db:Session=Depends(get_db)):
    rate_limit(request=request,key_prefix="student_login",limit=5,window=60)
    return student_service.login_user(
        db=db,
        register_id=student.username,
        password=student.password
    )
@router.post("/logout",status_code=status.HTTP_200_OK)
def logout_usee(
    refresh_token:str,
    authorization: str | None = Header(default=None),
    db:Session=Depends(get_db),
):
    logger.info("logout request recived")
    access_token = None
    if authorization and authorization.lower().startswith("bearer "):
        access_token = authorization.split(" ", 1)[1]

    result = student_service.logout_user(
        db=db,
        refresh_token=refresh_token,
        access_token=access_token or ""
    )
    logger.info("logout request complete")
    return result

@router.get("/me",status_code=status.HTTP_200_OK)
def me(db:Session=Depends(get_db),current_user=Depends(require_role("student"))):
     logger.info("get current user request recived")
     result = student_dashboard_service.get_student_dashboard(
        db=db,
        registration_id=current_user.registration_id
    )
     return result


@router.get("/courses",status_code=status.HTTP_200_OK)
def get_all_courses(page:int=Query(1,ge=1),limit:int=Query(20,ge=1,le=100),
                    db:Session=Depends(get_db),current_user=Depends(require_role("student"))):
    logger.info("get all courses request recived")
    courses = student_dashboard_service.show_all_courses(
        db=db,page=page,limit=limit
    )
    logger.info("get all courses request complete")
    return courses

@router.get("/course/{course_id}",status_code=status.HTTP_200_OK)
def get_course_by_id(course_id:int,db:Session=Depends(get_db),current_user=Depends(require_role("student"))):
        logger.info("get course by id request recived")
        course = student_dashboard_service.get_course_by_id(
            db=db,
            course_id=course_id
        )
        logger.info("get course by id request complete")
        return course

enrollment_rate_limit = rate_limit_dependency(
     key_prefix="enrollment",limit=5,window=60
)
@router.post("/enrollments", 
             dependencies=[Depends(enrollment_rate_limit)],response_model=EnrollmentResponse,
             status_code=status.HTTP_201_CREATED)
def create_enrollment(
    enrollment: EnrollmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("student")),
):
    return student_enrollment_service.enroll(
        db=db,
        student_id=current_user.id,
        public_course_id=enrollment.course_id,
    )

@router.get("/enrollments", response_model=List[EnrollmentResponse])
def get_my_enrollments(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("student")),
):
    return student_enrollment_service.get_student_by_enrollments(
        db=db,
        student_id=current_user.id,
    )


@router.patch("/me",response_model=StudentResponse,status_code=status.HTTP_200_OK
)
def update_my_profile(request: Request, student_data: StudentProfileUpdate,db: Session = Depends(get_db),
    current_user=Depends(require_role("student"))
):
    rate_limit(request=request, key_prefix="student_profile_update", limit=5, window=60)
    return student_dashboard_service.update_student_profile(
        db=db,
        student_id=current_user.id,
        student_data=student_data.model_dump(exclude_unset=True)
    )
@router.post("/refresh", response_model=TokenResponse)
def refresh_student_token(
    request: Request,
    request_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    rate_limit(request=request, key_prefix="student_refresh", limit=5, window=60)
    return student_dashboard_service.refresh_access_token(
        db=db,
        refresh_token_value=request_data.refresh_token
    )