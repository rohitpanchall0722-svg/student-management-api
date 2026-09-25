from datetime import datetime, timezone
from sqlalchemy import DateTime, String,Column,Integer,Sequence,ForeignKey,Boolean, CheckConstraint
from backend.app.database.database import Base

class StudentDetails(Base):
    __tablename__ = "student_data"
    id = Column(Integer,primary_key=True,index=True)
    registration_id = Column(Integer,Sequence("student_is_squence",start=22072000))
    student_name = Column(String(50),nullable=False)
    email = Column(String(255),nullable=False,unique=True)
    hashed_password = Column(String(255),nullable=False)
    role = Column(String(30),nullable=False,default="student")
    created_at = Column( DateTime(timezone=True),
                default=lambda: datetime.now(timezone.utc),nullable=False )
    phone_number = Column(String(20),unique=True ,nullable=True)
    address = Column(String(255), nullable=True)




class AdminDetails(Base):
    __tablename__ = "admindata"
    id = Column(Integer,primary_key=True,index=True,nullable=False)
    admin_id = Column(Integer,Sequence("adminid_sequen",start=1000),unique=True)
    admin_name = Column(String(50),nullable=False)    
    email = Column(String(99),unique=True,nullable=False)
    hashed_pass = Column(String(255),nullable=False)
    role  = Column(String(30),nullable=False,default="admin")
    
class RefreshToken(Base):
    __tablename__="refresh_tokens"
    __table_args__ = (
        CheckConstraint("(user_id IS NOT NULL) <> (admin_id IS NOT NULL)", name="refresh_token_owner_xor"),
    )

    token_id=Column(Integer,primary_key=True,index=True)
    token = Column(String,nullable=False,unique=True,)
    user_id=Column(Integer,ForeignKey("student_data.id"),nullable=True)
    admin_id=Column(Integer,ForeignKey("admindata.admin_id"),nullable=True)
    expire_at = Column(DateTime(timezone=True),nullable=False)
    revoked_at = Column(Boolean,default=False,nullable=False)
    created_at = Column(DateTime(timezone=True),
                        default=lambda:datetime.now(timezone.utc))
