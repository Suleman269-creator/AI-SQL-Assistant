from sqlalchemy import Column, Integer, String, Text
from app.database.database import Base


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=False)