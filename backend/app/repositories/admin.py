from backend.app.models.users import AdminDetails
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException,status
import logging
logger = logging.getLogger(__name__)

class AdminRepositories:
    def get_by_admin_id(self,db:Session,admin_id:int):
        try:
            stmt = select(AdminDetails).where(AdminDetails.admin_id==admin_id)
            admin = db.execute(stmt).scalar_one_or_none()
            return admin
        except Exception:
            logger.exception("failed to fetch the admin data")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="failed to fetch the admin data")

    def get_by_email(self,db:Session,email:str):
        try:
            stmt= select(AdminDetails).where(AdminDetails.email==email)
            admin = db.execute(stmt).scalar_one_or_none()
            return admin
        except Exception:
            logger.exception("failed to fetch the admin data")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="failed to fetch the admin data")
        

    def create_new_admin(self,db:Session,admin_data:AdminDetails):
        try:
            new_admin = AdminDetails(
                admin_name=admin_data["admin_name"],
                email=admin_data["email"],
                hashed_pass=admin_data["hashed_pass"],
                role="admin"
            )
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            return new_admin
        except Exception:
            logger.exception("failed to create new admin")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="failed to create new admin")

    def show_all_admins(self,db:Session):
        try:
            stmt = select(AdminDetails)
            return db.execute(stmt).scalar().all()
        except Exception:
            logger.exception("failed to fetch the admin data")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="failed to fetch the admin data")

        
        