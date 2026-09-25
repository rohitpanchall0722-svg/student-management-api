from fastapi import APIRouter,Depends,status,Query,Request
from backend.app.scheams.admin import AdminRegistration,AdminResponse,AdminLoginRequest
from backend.app.scheams.users import StudentResponse
from backend.app.database.database import get_db
from sqlalchemy.orm import Session
from backend.app.services.admin import AdminService
from fastapi.security import OAuth2PasswordRequestForm
from backend.app.scheams.users import TokenResponse
from backend.app.scheams.enroll import EnrollmentResponse
from backend.app.core.secuirty import require_role
from backend.app.scheams.admin import CourseCreate
from backend.app.services.enroll import StudentEnrollmentService
from backend.app.core.redis import redis_client
from backend.app.core.rate_limiter import rate_limit

import logging  
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)
admin_service = AdminService()
enroll_service = StudentEnrollmentService()
@router.post(
    "/registration",
    status_code=status.HTTP_201_CREATED,
    response_model=AdminResponse
)
def admin_registration(
    request: Request,
    new_admin: AdminRegistration,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    logger.info("new admin registration request received")
    rate_limit(request=request, key_prefix="admin_registration", limit=5, window=60)

    admin_service = AdminService()

    new_admin = admin_service.create_admin(
        db=db,
        admin_name=new_admin.admin_name,
        email=new_admin.email,
        password=new_admin.password
    )

    logger.info("new admin registration complete")

    return new_admin

@router.post("/login",response_model=TokenResponse)
def admin_login(request: Request, admin_login_request:AdminLoginRequest,
                db:Session=Depends(get_db)):
    logger.info("admin login request recived")
    rate_limit(request=request, key_prefix="admin_login", limit=5, window=60)
    admin_service = AdminService()
    token_response = admin_service.admin_login(
        db=db,
        admin_id=admin_login_request.admin_id,
        password=admin_login_request.password
    )
    logger.info("admin login complete")
    return token_response

@router.post("/logout",status_code=status.HTTP_200_OK)
def logout_usee(refresh_token:str,db:Session=Depends(get_db)):
    logger.info("logout request recived")
    result = admin_service.admin_logout(
        db=db,
        refresh_token=refresh_token
    )
    logger.info("logout request complete")
    return result


@router.post("/create_course",status_code=status.HTTP_201_CREATED)
def create_course(request: Request, course_data:CourseCreate,db:Session=Depends(get_db)
                  ,current_user=Depends(require_role("admin"))):
    logger.info("create course request recived")
    rate_limit(request=request, key_prefix="admin_create_course", limit=5, window=60)
    new_course = admin_service.add_course(
        db=db,
        course_data=course_data.model_dump()
    )
    redis_client.delete("courses:all")
    logger.info("course cache invalidated")

    logger.info("create course request complete")
    return new_course

@router.get("/course/{course_id}",status_code=status.HTTP_200_OK)
def get_course(course_id:int,db:Session=Depends(get_db)
                    ,current_user=Depends(require_role("admin"))):
        logger.info("get course by id request recived")
        course = admin_service.get_course_by_id(
            db=db,
            course_id=course_id
        )
        logger.info("get course by id request complete")
        return course

@router.get("/courses",status_code=status.HTTP_200_OK)
def get_all_courses(page:int=Query(1,ge=1),limit:int=Query(20,ge=1,le=100),db:Session=Depends(get_db)
                    ,current_user=Depends(require_role("admin"))):
        logger.info("get all courses request recived")
        courses = admin_service.show_all_courses(
            db=db,page=page,limit=limit     
        )
        logger.info("get all courses request complete")
        return courses

@router.get("/students", response_model=list[StudentResponse], status_code=status.HTTP_200_OK)
def get_all_students(page:int=Query(1,ge=1),limit:int=Query(20,ge=1,le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    logger.info("get all students request")
    return admin_service.show_all_students(db=db,page=page,limit=limit)

@router.get("/student/{registration_id}", response_model=StudentResponse,
            status_code=status.HTTP_200_OK)
def get_student_by_registration_id(
    registration_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    return admin_service.get_student_by_registration_id(
        db=db,
        registration_id=registration_id,
    )

@router.delete("/student/{registration_id}", status_code=status.HTTP_200_OK)
def remove_student(
    request: Request,
    registration_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    rate_limit(request=request, key_prefix="admin_remove_student", limit=5, window=60)
    return admin_service.remove_student(
        db=db,
        registration_id=registration_id,
    )


@router.get("/view-all-enrollments",status_code=status.HTTP_200_OK)
def view_all(page:int=Query(1,ge=1),limit:int=Query(10,ge=1,le=100),db:Session=Depends(get_db),current_user=Depends(require_role("admin"))):
     return enroll_service.show_all_enrollment(db=db,limit=limit,page=page)

@router.get(
    "/course/{course_id}/enrollments",
    response_model=list[EnrollmentResponse],
    status_code=status.HTTP_200_OK
)
def get_course_enrollments(
    course_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    return enroll_service.show_specific_enroll(
        db=db,
        course_id=course_id
    )