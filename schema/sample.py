from pydantic import BaseModel

class SampleRecord(BaseModel):
    name: str
    description: str = ""

class SampleRecordResponse(BaseModel):
    id: int
    name: str
    description: str