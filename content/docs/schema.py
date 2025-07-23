from pydantic import BaseModel

class DocsSchema(BaseModel):
    name: str
    category: str
    tags: str