from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from app.services.model_service import ModelService
from . import crud, models, schemas
from .database import SessionLocal, engine
from .security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.services.bin_generation_service import BinGenerationService
from .services import BaseplateService
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from core.gridfinity_baseplate import GridfinityBaseplate, Unit
from core.gridfinity_config import GridfinityConfig

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gridfinity API")

# Update after creating the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)
app.mount("/files", StaticFiles(directory="/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output"), name="files")


class BinGenerateRequest(BaseModel):
    width: float
    depth: float
    height: float

class GeneratedFileResponse(BaseModel):
    id: int
    file_type: str
    file_path: str

class BinGenerateResponse(BaseModel):
    id: int
    name: str
    width: float
    depth: float
    height: float
    files: list[GeneratedFileResponse]
    
class DrawerGridRequest(BaseModel):
    name: str
    width: float
    depth: float
    height: float
    
class UnitResponse(BaseModel):
    width: float
    depth: float
    x_offset: float
    y_offset: float
    is_standard: bool
    
class DrawerGridResponse(BaseModel):
    units: list[UnitResponse]
    gridSizeX: int
    gridSizeY: int

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(
    current_user: models.User = Depends(get_current_user)
):
    return current_user

@app.post("/drawers/", response_model=schemas.Drawer)
def create_drawer(
    drawer: schemas.DrawerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_drawer(db=db, drawer=drawer, user_id=current_user.id)

@app.get("/drawers/", response_model=List[schemas.DrawerWithBins])
def read_drawers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    drawers = crud.get_user_drawers(db, user_id=current_user.id)
    return drawers

@app.get("/drawers/{drawer_id}", response_model=schemas.DrawerWithBins)
def read_drawer(
    drawer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    drawer = crud.get_drawer(db, drawer_id=drawer_id)
    if drawer is None:
        raise HTTPException(status_code=404, detail="Drawer not found")
    if drawer.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this drawer")
    return drawer

@app.post("/drawers/{drawer_id}/bins/", response_model=schemas.Bin)
def create_bin_for_drawer(
    drawer_id: int,
    bin: schemas.BinCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    drawer = crud.get_drawer(db, drawer_id=drawer_id)
    if drawer is None:
        raise HTTPException(status_code=404, detail="Drawer not found")
    if drawer.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this drawer")
    bin.drawer_id = drawer_id
    return crud.create_bin(db=db, bin=bin)

@app.delete("/drawers/{drawer_id}")
def delete_drawer(
    drawer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    drawer = crud.get_drawer(db, drawer_id=drawer_id)
    if drawer is None:
        raise HTTPException(status_code=404, detail="Drawer not found")
    if drawer.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this drawer")
    crud.delete_drawer(db, drawer_id=drawer_id)
    return {"message": "Drawer deleted successfully"}

@app.put("/drawers/{drawer_id}", response_model=schemas.Drawer)
def update_drawer(
    drawer_id: int,
    drawer_update: schemas.DrawerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    existing_drawer = crud.get_drawer(db, drawer_id=drawer_id)
    if existing_drawer is None:
        raise HTTPException(status_code=404, detail="Drawer not found")
    if existing_drawer.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this drawer")
    updated_drawer = crud.update_drawer(db, drawer_id=drawer_id, drawer_update=drawer_update)
    return updated_drawer


@app.post("/generate/bin/", response_model=BinGenerateResponse)
async def generate_bin(
        request: BinGenerateRequest,
        db: Session = Depends(get_db)
):
    service = BinGenerationService(
        db=db,
        base_output_dir=Path("/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output")
    )
    name = f"Bin_{request.width}_{request.depth}_{request.height}"
    bin_record, files = await service.generate_bin(
        name,
        width=request.width,
        depth=request.depth,
        height=request.height
    )

    return BinGenerateResponse(
        id=bin_record.id,
        name=bin_record.name,
        width=bin_record.width,
        depth=bin_record.depth,
        height=bin_record.height,
        files=[GeneratedFileResponse(**file.__dict__) for file in files]
    )

@app.post("/generate/baseplate/", response_model=BinGenerateResponse)
async def generate_baseplate_endpoint(
    request: BinGenerateRequest,
    db: Session = Depends(get_db)
):
    baseplate_service = BaseplateService(
        db=db,
        base_output_dir=Path("/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output")
    )
    name = f"Baseplate_{request.width}_{request.depth}_{request.height}"
    baseplate, files = await baseplate_service.generate_baseplate(
        name,
        width=request.width,
        depth=request.depth
    )

    return BinGenerateResponse(
        id=baseplate.id,
        name=baseplate.name,
        width=baseplate.width,
        depth=baseplate.depth,
        height=5,
        files=[GeneratedFileResponse(
            id=file.id,
            file_type=file.file_type,
            file_path=file.file_path
        ) for file in files]
    )


@app.get("/models/", response_model=List[schemas.ModelResponse])
async def get_models_endpoint(request: Request, db: Session = Depends(get_db)):
    model_service = ModelService(db)
    models = model_service.retrieve_models()

    # Get base URL from request
    base_url = str(request.base_url).rstrip('/')

    # Convert relative paths to full URLs
    for model in models:
        if model.file_path:
            model.file_path = f"{base_url}/files/{model.file_path}"

    return models

@app.delete("/models/{model_id}")
async def delete_model_endpoint(
    model_id: str,
    db: Session = Depends(get_db)
):
    model_service = ModelService(db)
    success = model_service.delete_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted successfully"}

@app.post("/drawers/grid-layout/", response_model=DrawerGridResponse)
async def calculate_drawer_grid(
    request: DrawerGridRequest
):
    try:
        # Create a GridfinityBaseplate instance
        config = GridfinityConfig()
        baseplate = GridfinityBaseplate(
            drawer_width=request.width,
            drawer_depth=request.depth,
            config=config
        )
        
        # Calculate grid units
        units = baseplate.grid_divider()
        
        # Convert to response model
        unit_responses = [
            UnitResponse(
                width=unit.width,
                depth=unit.depth,
                x_offset=unit.x_offset,
                y_offset=unit.y_offset,
                is_standard=unit.is_standard
            ) for unit in units
        ]
        
        return DrawerGridResponse(
            units=unit_responses,
            gridSizeX=baseplate.num_squares_x,
            gridSizeY=baseplate.num_squares_y
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating drawer grid: {str(e)}"
        )