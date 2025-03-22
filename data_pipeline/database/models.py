from sqlalchemy import Column, Integer, String, LargeBinary
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import TIMESTAMP, func

TARGET_SIZE = (224, 224)

class Base(DeclarativeBase):
    pass

class SourceImage(Base):
    __tablename__ = "source_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    image_path = Column(String, nullable=False)
    color_image = Column(LargeBinary, nullable=False)
    grey_image = Column(LargeBinary, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    

class CrawlImage(Base):
    __tablename__ = "crawl_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    image_url = Column(String, nullable=False)
    color_image = Column(LargeBinary, nullable=True)
    grey_image = Column(LargeBinary, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())