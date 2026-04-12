from pydantic import BaseModel

class IssueCreate(BaseModel):
    title: str
    description: str
    location: str
    category: str

class IssueResponse(BaseModel):
    id: int
    title: str
    description: str
    location: str
    category: str
    complaint_number: str | None = None
    media_urls: str | None = None

    class Config:
        from_attributes = True
