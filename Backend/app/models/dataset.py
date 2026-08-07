from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from app.database.database import Base


class DatasetMetadata(Base):

    __tablename__ = "dataset_metadata"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    filename = Column(
        String(255),
        nullable=False
    )

    file_type = Column(
        String(50),
        nullable=True
    )

    rows = Column(
        Integer,
        nullable=True
    )

    columns = Column(
        Integer,
        nullable=True
    )

    column_names = Column(
        Text,
        nullable=True
    )

    metadata_json = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )