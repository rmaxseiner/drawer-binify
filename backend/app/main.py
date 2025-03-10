from pathlib import Path
import os
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
from app.services.baseplate_generator_service import BaseplateService
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from core.gridfinity_baseplate import GridfinityBaseplate, Unit
from core.gridfinity_config import GridfinityConfig
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
import logging

logger = logging.getLogger(__name__)

class QueryFilterMiddleware(BaseHTTPMiddleware):
    """Middleware to filter out problematic query parameters."""
    
    async def dispatch(self, request: Request, call_next):
        # Create a copy of the original request
        scope = request.scope.copy()
        
        # Get and filter query parameters
        query_params = []
        for param_name, param_value in request.query_params.items():
            # Skip problematic parameters
            if param_name == "local_kw":
                logger.info(f"Filtering out query parameter: {param_name}={param_value}")
                continue
            query_params.append((param_name.encode(), param_value.encode()))
        
        # Replace query parameters in the scope
        scope["query_string"] = b"&".join(b"=".join(param) for param in query_params)
        
        # Create a new request with filtered query parameters
        filtered_request = Request(scope=scope, receive=request.receive)
        
        # Process the request with filtered parameters
        response = await call_next(filtered_request)
        return response

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gridfinity API")

# Update after creating the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"],  # Specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add our query parameter filter middleware
app.add_middleware(QueryFilterMiddleware)
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
    
class PlacedBinRequest(BaseModel):
    id: str
    width: float
    depth: float
    x: float
    y: float
    unitX: int
    unitY: int
    unitWidth: int
    unitDepth: int
    
class GenerateDrawerModelsRequest(BaseModel):
    name: str
    width: float
    depth: float
    height: float
    bins: list[PlacedBinRequest]
    
class GenerateDrawerModelsResponse(BaseModel):
    message: str
    modelIds: list[str]

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
    print(f"Login attempt for user: {form_data.username}")
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        print(f"Authentication failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"Authentication successful for user: {form_data.username}")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    print(f"Generated token for user {user.username}: {access_token[:10]}...")
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/me/")
async def read_users_me(
    current_user: models.User = Depends(get_current_user),
    # Explicitly declare optional query parameters to prevent them from being
    # passed to other dependencies
    local_kw: str = None,
):
    # Return a dict instead of the model object to avoid validation issues
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name or "",
        "last_name": current_user.last_name or "",
        "created_at": current_user.created_at
    }

@app.post("/users/change-password/")
async def change_password(
    password_data: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.change_user_password(
        db, 
        user_id=current_user.id,
        current_password=password_data.current_password,
        new_password=password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    return {"message": "Password updated successfully"}

@app.put("/users/update-profile/", response_model=schemas.User)
async def update_profile(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_user = crud.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already taken"
        )
    return updated_user

@app.post("/users/change-password/")
async def change_password(
    password_change: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = crud.change_user_password(
        db, 
        current_user.id, 
        password_change.current_password, 
        password_change.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )
    
    return {"message": "Password changed successfully"}

@app.post("/drawers/", response_model=schemas.Drawer)
def create_drawer(
    drawer: schemas.DrawerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_drawer(db=db, drawer=drawer, user_id=current_user.id)

@app.get("/drawers/")
def read_drawers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    # Explicitly declare optional query parameters to prevent them from being
    # passed to other dependencies
    local_kw: str = None,
):
    drawers = crud.get_user_drawers(db, user_id=current_user.id)
    # Convert drawer objects to dict to avoid validation issues
    drawer_list = []
    for drawer in drawers:
        drawer_dict = {
            "id": drawer.id,
            "name": drawer.name,
            "width": drawer.width,
            "depth": drawer.depth,
            "height": drawer.height,
            "owner_id": drawer.owner_id,
            "created_at": drawer.created_at,
            "bins": []
        }
        for bin in drawer.bins:
            bin_dict = {
                "id": bin.id,
                "width": bin.width,
                "depth": bin.depth, 
                "height": bin.height,
                "is_standard": bin.is_standard,
                "drawer_id": bin.drawer_id,
                "created_at": bin.created_at
            }
            drawer_dict["bins"].append(bin_dict)
        drawer_list.append(drawer_dict)
    return drawer_list

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

@app.put("/drawers/{drawer_id}/bins", response_model=dict)
def update_drawer_bins(
    drawer_id: int,
    bin_data: schemas.BinUpdateList,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update all bins for a drawer"""
    
    # Verify drawer exists and belongs to the user
    drawer = crud.get_drawer(db, drawer_id=drawer_id)
    if drawer is None:
        raise HTTPException(status_code=404, detail="Drawer not found")
    if drawer.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this drawer")
    
    # Use the CRUD function to update bins
    updated_bins = crud.update_drawer_bins(db, drawer_id=drawer_id, bins_data=bin_data.bins)
    
    return {"message": "Bins updated successfully", "bin_count": len(updated_bins)}

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
async def get_models_endpoint(
    request: Request, 
    db: Session = Depends(get_db),
    # Explicitly declare optional query parameters to prevent them from being
    # passed to other dependencies
    local_kw: str = None,
):
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
        
@app.post("/drawers/generate-models/", response_model=GenerateDrawerModelsResponse)
async def generate_drawer_models(
    request: GenerateDrawerModelsRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        # Create drawer record
        new_drawer = models.Drawer(
            name=request.name,
            width=request.width,
            depth=request.depth,
            height=request.height,
            owner_id=current_user.id
        )
        db.add(new_drawer)
        db.flush()  # Get the drawer ID
        
        model_ids = []
        
        # First generate baseplate
        config = GridfinityConfig()
        baseplate_service = BaseplateService(
            db=db,
            base_output_dir=Path("/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output")
        )
        
        baseplate_name = f"Baseplate_{request.name}"
        baseplate, baseplate_files = await baseplate_service.generate_baseplate(
            baseplate_name,
            width=request.width,
            depth=request.depth
        )
        
        for file in baseplate_files:
            model_ids.append(str(file.id))
            
        # Then generate bins
        bin_service = BinGenerationService(
            db=db,
            base_output_dir=Path("/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output")
        )
        
        for bin_request in request.bins:
            bin_name = f"Bin_{bin_request.id.split('-')[0]}"
            bin_model, bin_files = await bin_service.generate_bin(
                bin_name,
                width=bin_request.width,
                depth=bin_request.depth,
                height=request.height
            )
            
            for file in bin_files:
                model_ids.append(str(file.id))
                
            # Create bin record linked to the drawer
            new_bin = models.Bin(
                name=bin_name,
                width=bin_request.width,
                depth=bin_request.depth,
                height=request.height,
                x_position=bin_request.x,
                y_position=bin_request.y,
                drawer_id=new_drawer.id,
                model_id=bin_model.id
            )
            db.add(new_bin)
        
        # Commit all changes
        db.commit()
        
        return GenerateDrawerModelsResponse(
            message=f"Drawer {request.name} models generated successfully",
            modelIds=model_ids
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating drawer models: {str(e)}"
        )