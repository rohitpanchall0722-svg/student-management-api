from backend.app.database.database import Base
from sqlalchemy import Column,Integer,String,DateTime,Sequence


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer,primary_key=True,index=True)
    course_id = Column(Integer,Sequence("course_id_sequence",start=1001),
                    nullable=False,unique=True,index=True)
    course_name = Column(String(100),nullable=False)
    description = Column(String(255),nullable=True)
    live_at = Column(DateTime,nullable=False)
    duration = Column(Integer,nullable=False)
    status = Column(String(20),nullable=False,default="draft")