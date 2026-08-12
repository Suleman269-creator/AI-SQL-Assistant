from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.database.database import Base


class QueryHistory(Base):

    __tablename__ = "query_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    dataset_id = Column(
        String,
        nullable=False,
        index=True
    )

    user_question = Column(
        Text,
        nullable=False
    )

    generated_sql = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )