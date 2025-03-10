from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DrawerBase(BaseModel):
    name: str
    width: float
    depth: float
    height: float

class DrawerCreate(DrawerBase):
    pass

class Drawer(DrawerBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class BinBase(BaseModel):
    width: float
    depth: float
    height: float
    is_standard: bool

class BinCreate(BinBase):
    drawer_id: int

class Bin(BinBase):
    id: int
    drawer_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class DrawerWithBins(Drawer):
    bins: List[Bin]

class UserWithDrawers(User):
    drawers: List[DrawerWithBins]

class ModelBase(BaseModel):
    width: float
    depth: float
    height: float

class GenerateResponse(BaseModel):
    success: bool
    message: str
    file_path: Optional[str] = None

class ModelResponse(BaseModel):
    id: str
    type: str  # 'bin' or 'baseplate'
    name: str
    date_created: datetime
    width: float
    depth: float
    height: float
    file_path: str
    
class BinUpdate(BaseModel):
    id: Optional[int] = None
    width: float
    depth: float
    x_position: float
    y_position: float

class BinUpdateList(BaseModel):
    bins: List[BinUpdate]