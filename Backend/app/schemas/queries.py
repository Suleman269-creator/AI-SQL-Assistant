from pydantic import BaseModel


class QueryCreate(BaseModel):
    question: str
    generated_sql: str


class SQLResponse(BaseModel):
    question: str


class AskRequest(BaseModel):
    dataset_id: str
    question: str