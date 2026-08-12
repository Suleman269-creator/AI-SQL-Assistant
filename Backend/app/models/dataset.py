from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime

from app.database.database import Base


class DatasetMetadata(Base):

    __tablename__ = "dataset_metadata"

    id = Column(Integer, primary_key=True, index=True)

    dataset_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    filename = Column(
        String,
        nullable=False
    )

    table_name = Column(
        String,
        nullable=False
    )

    row_count = Column(
        Integer,
        nullable=False
    )

    column_count = Column(
        Integer,
        nullable=False
    )

    columns = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )