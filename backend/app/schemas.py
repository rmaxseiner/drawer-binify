from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
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

class ModelMetadataBase(BaseModel):
    width: float
    depth: float
    height: float

class ModelBase(BaseModel):
    type: str  # 'bin' or 'baseplate'
    model_metadata: Dict[str, Any]  # Flexible metadata for different model types

class ModelCreate(ModelBase):
    pass

class Model(ModelBase):
    id: int
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
    model_id: Optional[int] = None  # Optional because it might be set later

class Bin(BinBase):
    id: int
    drawer_id: int
    created_at: datetime
    x_position: Optional[float] = None
    y_position: Optional[float] = None
    name: Optional[str] = None
    model_id: Optional[int] = None

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

class BaseplateResponse(BaseModel):
    id: int
    name: str
    width: float
    depth: float
    created_at: datetime
    model_id: Optional[int] = None

    class Config:
        from_attributes = True

class DrawerWithBins(Drawer):
    bins: List[Bin]
    baseplates: List[BaseplateResponse] = []

class UserWithDrawers(User):
    drawers: List[DrawerWithBins]
    baseplates: List[BaseplateResponse] = []

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
    
class UserSettingsBase(BaseModel):
    theme: Optional[str] = "light"
    default_drawer_height: Optional[float] = 40.0
    default_bin_height: Optional[float] = 25.0
    notification_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict)

class UserSettingsCreate(UserSettingsBase):
    pass

class UserSettingsUpdate(UserSettingsBase):
    pass

class UserSettings(UserSettingsBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True