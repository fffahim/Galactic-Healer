from pydantic import BaseModel


class UserInfo(BaseModel):
    email: str
    firstName: str
    lastName: str
    age: int
