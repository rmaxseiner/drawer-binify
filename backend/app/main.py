from pathlib import Path
import sys
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List
from app.services.model_service import ModelService
from . import crud, models, schemas
from .database import SessionLocal, engine
from .models import Drawer
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
from core.gridfinity_baseplate import GridfinityBaseplate
from core.gridfinity_config import GridfinityConfig
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import logging.handlers

# Configure logging
def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parents[2] / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "drawerfinity.log"
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(name)s - %(message)s'
    )
    
    # Create handlers
    # File handler with rotation (10 MB max, keep 5 backup files)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(console_formatter)
    
    # Get the root logger and configure it
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates on reload
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add the new handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Return application logger
    return logging.getLogger(__name__)

# Initialize logger
logger = setup_logging()
logger.info("Logging system initialized")

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

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom exception handler for validation errors to log and return detailed information.
    """
    # Log detailed validation errors
    error_details = exc.errors()
    logger.error(f"Validation errors on path {request.url.path}: {error_details}")
    
    # Return the validation errors to the client
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_details},
    )

# Update after creating the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:8000", "http://192.168.86.51:3001"],  # Specific origins
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
    drawer_id: int

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
    drawer_id: int
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
        height=request.height,
        drawer_id=0
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
        drawer_id=request.drawer_id,
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
    
    # Get base URL from request - use the actual host/port from the request
    base_url = str(request.base_url).rstrip('/')
    logger.info(f"Base URL for file paths: {base_url}")
    
    # Convert relative paths to full URLs
    for model in models:
        if model.file_path:
            # Clean up any path that might be problematic
            file_path = model.file_path
            # Remove leading slash if present
            if file_path.startswith('/'):
                file_path = file_path[1:]
            # Create the full URL
            model.file_path = f"{base_url}/files/{file_path}"
            logger.debug(f"Model file path: {model.file_path}")
        else:
            logger.warning(f"Model {model.id} ({model.name}) has no file path")
    
    logger.info(f"Returning {len(models)} models")
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

@app.get("/models/view/{model_id}/stl")
async def get_model_stl_file(
        model_id: int,
        db: Session = Depends(get_db)
):
    """Get the STL file for a specific model."""
    try:
        logger.info(f"Checking for model with ID: {model_id}")

        # Try to find the bin with this ID
        bin_model = db.query(models.Bin).filter(models.Bin.id == model_id).first()

        if bin_model and bin_model.model_id:
            logger.info(f"Found bin: ID={bin_model.id}, Name={bin_model.name}")
            # Get the model associated with this bin
            model = db.query(models.Model).filter(models.Model.id == bin_model.model_id).first()
            if model:
                return await get_stl_file_from_model(model, f"bin_{model_id}.stl")

        # If not a bin, try baseplate
        baseplate = db.query(models.Baseplate).filter(models.Baseplate.id == model_id).first()

        if baseplate and baseplate.model_id:
            logger.info(f"Found baseplate: ID={baseplate.id}, Name={baseplate.name}")
            # Get the model associated with this baseplate
            model = db.query(models.Model).filter(models.Model.id == baseplate.model_id).first()
            if model:
                return await get_stl_file_from_model(model, f"baseplate_{model_id}.stl")

        # Also try directly looking for a model with this ID
        model = db.query(models.Model).filter(models.Model.id == model_id).first()
        if model:
            logger.info(f"Found model directly: ID={model.id}, Type={model.type}")
            return await get_stl_file_from_model(model, f"model_{model_id}.stl")

        # If we get here, we couldn't find a valid model
        logger.warning(f"No valid model found for ID {model_id}")
        raise HTTPException(status_code=404, detail=f"No valid model found for ID {model_id}")

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error retrieving STL file for model {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving STL file: {str(e)}")


async def get_stl_file_from_model(model, filename):
    """Helper function to get STL file from a model"""
    try:
        # Find the STL file associated with this model
        stl_file = next((f for f in model.files if f.file_type.upper() == "STL"), None)

        if stl_file:
            logger.info(f"Found STL file: ID={stl_file.id}, Path={stl_file.file_path}")
            base_output_dir = Path("/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output")
            file_path = base_output_dir / stl_file.file_path

            logger.info(f"Full file path: {file_path}")
            logger.info(f"File exists: {file_path.exists()}")

            if file_path.exists():
                logger.info(f"Returning STL file response for model {model.id}")
                return FileResponse(
                    path=file_path,
                    filename=filename,
                    media_type="model/stl"
                )
            else:
                logger.warning(f"STL file not found on disk at {file_path}")
                raise HTTPException(status_code=404, detail=f"STL file not found on disk at {file_path}")
        else:
            logger.warning(f"No STL file found for model {model.id}")
            raise HTTPException(status_code=404, detail=f"No STL file found for model {model.id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in get_stl_file_from_model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving STL file: {str(e)}")


async def _ids_to_check(model_id):
    logger.info(f"STL file requested for model ID: {model_id}")
    # List of IDs to check - try the requested ID, then ID-1, then ID+1
    # This handles the case where model IDs and directory names don't match
    ids_to_check = [model_id]
    # If the model_id is even, check the odd number below it first
    if model_id % 2 == 0:
        ids_to_check.append(model_id - 1)
        ids_to_check.append(model_id + 1)
    else:
        ids_to_check.append(model_id + 1)
        ids_to_check.append(model_id - 1)
    logger.info(f"Will check these IDs in order: {ids_to_check}")
    return ids_to_check


@app.get("/models/view/{model_id}/cad")
async def get_model_cad_file(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Get the CAD file (FCStd) for a specific model."""
    try:
        ids_to_check = await _ids_to_check(model_id)
        
        # Try each ID in order
        for check_id in ids_to_check:
            logger.info(f"Checking for model with ID: {check_id}")
            
            # Attempt to find the bin first
            bin_model = db.query(models.Bin).filter(models.Bin.id == check_id).first()
            
            if bin_model:
                logger.info(f"Found bin model: ID={bin_model.id}, Name={bin_model.name}")
                # Find the CAD file associated with this bin
                cad_file = next((f for f in bin_model.files if f.file_type.upper() == "FCSTD"), None)
                
                if cad_file:
                    logger.info(f"Found CAD file: ID={cad_file.id}, Path={cad_file.file_path}")
                    file_path = Path("/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output") / cad_file.file_path
                    logger.info(f"Full file path: {file_path}")
                    logger.info(f"File exists: {file_path.exists()}")
                    
                    if file_path.exists():
                        logger.info(f"Returning CAD file response for bin {check_id} (originally requested ID: {model_id})")
                        return FileResponse(
                            path=file_path,
                            filename=f"bin_{check_id}.FCStd",
                            media_type="application/octet-stream"
                        )
                    else:
                        logger.warning(f"CAD file not found on disk at {file_path}")
                
            # If not a bin, try baseplate
            baseplate = db.query(models.Baseplate).filter(models.Baseplate.id == check_id).first()
            
            if baseplate:
                logger.info(f"Found baseplate model: ID={baseplate.id}, Name={baseplate.name}")
                # Find the CAD file associated with this baseplate
                cad_file = next((f for f in baseplate.files if f.file_type.upper() == "FCSTD"), None)
                
                if cad_file:
                    logger.info(f"Found CAD file: ID={cad_file.id}, Path={cad_file.file_path}")
                    file_path = Path("/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output") / cad_file.file_path
                    logger.info(f"Full file path: {file_path}")
                    logger.info(f"File exists: {file_path.exists()}")
                    
                    if file_path.exists():
                        logger.info(f"Returning CAD file response for baseplate {check_id} (originally requested ID: {model_id})")
                        return FileResponse(
                            path=file_path,
                            filename=f"baseplate_{check_id}.FCStd",
                            media_type="application/octet-stream"
                        )
                    else:
                        logger.warning(f"CAD file not found on disk at {file_path}")
        
        # If we get here, we tried all the IDs and couldn't find a valid model
        logger.warning(f"No valid model found for ID {model_id} or adjacent IDs")
        raise HTTPException(status_code=404, detail=f"No valid model found for ID {model_id} or adjacent IDs")
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error retrieving CAD file for model {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving CAD file: {str(e)}")

@app.get("/models/download/{model_id}")
async def download_model_file(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Get the downloadable CAD file for a specific model - redirect to CAD endpoint."""
    # Redirect to the CAD endpoint for backward compatibility
    return RedirectResponse(url=f"/models/view/{model_id}/cad")
        
@app.get("/debug/model/{model_id}")
async def debug_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Debug endpoint to check model details."""
    logger.info(f"Debug request for model ID: {model_id}")
    
    # Create a response object
    debug_info = {
        "model_id": model_id,
        "bin": None,
        "baseplate": None,
        "file_paths": []
    }
    
    # Check if model exists as a bin
    bin_model = db.query(models.Bin).filter(models.Bin.id == model_id).first()
    if bin_model:
        debug_info["bin"] = {
            "id": bin_model.id,
            "name": bin_model.name,
            "width": bin_model.width,
            "depth": bin_model.depth,
            "height": bin_model.height,
            "files": []
        }
        
        # Get files for this bin
        for file in bin_model.files:
            file_path = Path("/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output") / file.file_path
            debug_info["bin"]["files"].append({
                "id": file.id,
                "file_type": file.file_type,
                "file_path": file.file_path,
                "full_path": str(file_path),
                "exists": file_path.exists()
            })
            debug_info["file_paths"].append(str(file_path))
    
    # Check if model exists as a baseplate
    baseplate = db.query(models.Baseplate).filter(models.Baseplate.id == model_id).first()
    if baseplate:
        debug_info["baseplate"] = {
            "id": baseplate.id,
            "name": baseplate.name,
            "width": baseplate.width,
            "depth": baseplate.depth,
            "files": []
        }
        
        # Get files for this baseplate
        for file in baseplate.files:
            file_path = Path("/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output") / file.file_path
            debug_info["baseplate"]["files"].append({
                "id": file.id,
                "file_type": file.file_type,
                "file_path": file.file_path,
                "full_path": str(file_path),
                "exists": file_path.exists()
            })
            debug_info["file_paths"].append(str(file_path))
    
    # Check if any files were found
    if not debug_info["bin"] and not debug_info["baseplate"]:
        debug_info["status"] = "Model not found"
    else:
        debug_info["status"] = "Model found"
    
    return debug_info

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
    request: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Modified to receive raw dict instead of validated model to debug validation issues
    """
    logger.info(f"Generate drawer models request received: {request}")
    
    # Manually validate the request
    validated_request = await _validate_generate_request(request)
    
    try:
        if validated_request.drawer_id:
            drawer = await _retrieve_drawer(current_user, db, validated_request)
        else:
            drawer = await _create_drawer(current_user, db, validated_request)

        model_ids = []

        await _create_baseplate(db, model_ids, drawer, validated_request)

        await _generate_bins(db, model_ids, drawer, validated_request)

        # Commit all changes
        logger.debug("Committing all changes to database")
        db.commit()
        
        logger.info(f"Successfully generated {len(model_ids)} models for drawer {validated_request.name}")
        return GenerateDrawerModelsResponse(
            message=f"Drawer {validated_request.name} models generated successfully",
            modelIds=model_ids
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Catch any other exceptions and log them
        logger.exception(f"Unexpected error generating drawer models: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error generating drawer models: {str(e)}"
        )


async def _retrieve_drawer(current_user: models.User, db: Session, validated_request: GenerateDrawerModelsRequest):
    drawer = db.query(models.Drawer).filter(
        models.Drawer.id == validated_request.drawer_id,
        models.Drawer.owner_id == current_user.id
    ).first()
    if not drawer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drawer not found or you don't have permission to modify it"
        )
    # Update drawer details if needed
    drawer.name = validated_request.name
    drawer.width = validated_request.width
    drawer.depth = validated_request.depth
    drawer.height = validated_request.height
    return drawer


async def _generate_bins(db: Session, model_ids, drawer: Drawer, validated_request: GenerateDrawerModelsRequest):
    # Then generate bins
    bin_service = BinGenerationService(
        db=db,
        base_output_dir=Path("/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output")
    )
    # Group bins by their dimensions to optimize model reuse
    dimension_groups = {}
    for bin_request in validated_request.bins:
        key = (bin_request.width, bin_request.depth, validated_request.height)
        if key not in dimension_groups:
            dimension_groups[key] = []
        dimension_groups[key].append(bin_request)
    
    # Generate bins group by group to improve model reuse
    for i, (dimensions, bins_in_group) in enumerate(dimension_groups.items()):
        width, depth, height = dimensions

        logger.debug(f"Processing bin group {i + 1}/{len(dimension_groups)}: "
                     f"dimensions: {width}x{depth}x{height}, count: {len(bins_in_group)}")

        try:
            # Get or create the model - without creating a bin record
            result = await bin_service.get_or_create_bin_model(
                width=width,
                depth=depth,
                height=height,
                drawer_id=drawer.id
            )

            model = result

            # Process all bins in this dimension group
            for j, bin_request in enumerate(bins_in_group):
                bin_name = f"Bin_{bin_request.id.split('-')[0]}"
                
                if j == 0:
                    logger.debug(f"Adding first bin in group: {bin_name}")
                else:
                    logger.debug(f"Adding bin {j + 1}/{len(bins_in_group)}: {bin_name} (reusing model)")

                # Create bin record linked to the drawer and the model
                new_bin = models.Bin(
                    name=bin_name,
                    width=width,
                    depth=depth,
                    height=height,
                    x_position=bin_request.x,
                    y_position=bin_request.y,
                    drawer_id=drawer.id ,
                    model_id=model.id  # Use the same model for all bins in this group
                )
                db.add(new_bin)
                
                # No need to create file records for individual bins anymore
                # Files are associated with the model and can be accessed via bin.model.files

            # Flush after each group to ensure changes are saved
            db.flush()


        except Exception as e:
            logger.exception(f"Failed to generate bin group {dimensions}: {str(e)}")
            # Roll back the transaction and re-raise
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate bin group {dimensions}: {str(e)}"
            )


async def _create_baseplate(db: Session, model_ids , drawer: Drawer, validated_request: GenerateDrawerModelsRequest):
    # First generate baseplate
    config = GridfinityConfig()
    baseplate_service = BaseplateService(
        db=db,
        base_output_dir=Path("/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output")
    )
    logger.debug(f"Generating baseplate for drawer {validated_request.name}")
    baseplate_name = f"Baseplate_{validated_request.name}"
    try:
        baseplate, baseplate_files = await baseplate_service.generate_baseplate(
            baseplate_name,
            drawer.id,
            width=validated_request.width,
            depth=validated_request.depth
        )

        for file in baseplate_files:
            model_ids.append(str(file.id))
            logger.debug(f"Added baseplate file ID: {file.id}, path: {file.file_path}")
    except Exception as e:
        logger.exception(f"Failed to generate baseplate: {str(e)}")
        # Roll back the transaction and re-raise
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate baseplate: {str(e)}"
        )


async def _create_drawer(current_user: models.User , db: Session, validated_request: GenerateDrawerModelsRequest):
    # Create drawer record
    new_drawer = models.Drawer(
        name=validated_request.name,
        width=validated_request.width,
        depth=validated_request.depth,
        height=validated_request.height,
        owner_id=current_user.id
    )
    db.add(new_drawer)
    db.flush()  # Get the drawer ID
    logger.debug(f"Created drawer record with ID: {new_drawer.id}")
    return new_drawer


async def _validate_generate_request(request):
    try:
        # Check for required fields
        if not isinstance(request, dict):
            raise ValueError("Request must be a JSON object")

        required_fields = ["name", "width", "depth", "height", "bins"]
        for field in required_fields:
            if field not in request:
                raise ValueError(f"Missing required field: {field}")

        # Validate bins array
        if not isinstance(request["bins"], list):
            raise ValueError("'bins' must be an array")

        for i, bin_item in enumerate(request["bins"]):
            if not isinstance(bin_item, dict):
                raise ValueError(f"Bin at index {i} must be an object")

            bin_fields = ["id", "width", "depth", "x", "y", "unitX", "unitY", "unitWidth", "unitDepth"]
            for field in bin_fields:
                if field not in bin_item:
                    raise ValueError(f"Bin at index {i} is missing required field: {field}")

        # Convert to validated model
        validated_request = GenerateDrawerModelsRequest(
            name=request["name"],
            width=float(request["width"]),
            depth=float(request["depth"]),
            height=float(request["height"]),
            drawer_id = int(request["drawer_id"]),
            bins=[
                PlacedBinRequest(
                    id=bin_item["id"],
                    width=float(bin_item["width"]),
                    depth=float(bin_item["depth"]),
                    x=float(bin_item["x"]),
                    y=float(bin_item["y"]),
                    unitX=int(bin_item["unitX"]),
                    unitY=int(bin_item["unitY"]),
                    unitWidth=int(bin_item["unitWidth"]),
                    unitDepth=int(bin_item["unitDepth"])
                ) for bin_item in request["bins"]
            ]
        )

        logger.info(f"Validated request for drawer: {validated_request.name} - "
                    f"dimensions: {validated_request.width}x{validated_request.depth}x{validated_request.height} - "
                    f"bins count: {len(validated_request.bins)}")
    except Exception as e:
        logger.error(f"Validation error in generate_drawer_models: {str(e)}")
        logger.error(f"Request data: {request}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request data: {str(e)}"
        )
    return validated_request


@app.get("/users/settings/", response_model=schemas.UserSettings)
async def get_user_settings(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    local_kw: str = None,
):
    """Get current user settings"""
    logger.info(f"Getting settings for user {current_user.username}")
    settings = crud.get_user_settings(db, current_user.id)
    if not settings:
        # Create default settings if none exist
        logger.info(f"Creating default settings for user {current_user.username}")
        settings = crud.create_user_settings(db, current_user.id, schemas.UserSettingsCreate())
    return settings

@app.put("/users/settings/", response_model=schemas.UserSettings)
async def update_user_settings(
    settings_update: schemas.UserSettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user settings"""
    logger.info(f"Updating settings for user {current_user.username}: {settings_update}")
    updated_settings = crud.update_user_settings(db, current_user.id, settings_update)
    return updated_settings


@app.get("/drawers/{drawer_id}/baseplates")
def get_drawer_baseplates(
        drawer_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    drawer = crud.get_drawer(db, drawer_id=drawer_id)
    if drawer is None:
        raise HTTPException(status_code=404, detail="Drawer not found")
    if drawer.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this drawer")

    # Get baseplates for this drawer
    baseplates = db.query(models.Baseplate).filter(models.Baseplate.drawer_id == drawer_id).all()
    return baseplates


@app.get("/models/view/{model_id}/baseplate/stl")
async def get_baseplate_stl_file(model_id: int, db: Session = Depends(get_db)):
    """Get the STL file for a specific baseplate model."""
    try:
        # Find the baseplate
        baseplate = db.query(models.Baseplate).filter(models.Baseplate.id == model_id).first()

        if not baseplate:
            raise HTTPException(status_code=404, detail="Baseplate not found")

        if not baseplate.model_id:
            raise HTTPException(status_code=404, detail="Baseplate has no associated model")

        # Get the model associated with this baseplate
        model = db.query(models.Model).filter(models.Model.id == baseplate.model_id).first()

        if not model:
            raise HTTPException(status_code=404, detail="Associated model not found")

        # Find the STL file associated with this model
        stl_file = next((f for f in model.files if f.file_type.upper() == "STL"), None)

        if not stl_file:
            raise HTTPException(status_code=404, detail="STL file not found for this baseplate model")

        file_path = Path("/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output") / stl_file.file_path

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="STL file not found on disk")

        return FileResponse(
            path=file_path,
            filename=f"baseplate_{model_id}.stl",
            media_type="model/stl"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving STL file for baseplate {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving STL file: {str(e)}")


@app.get("/models/view/{model_id}/baseplate/cad")
async def get_baseplate_cad_file(model_id: int, db: Session = Depends(get_db)):
    """Get the CAD file for a specific baseplate model."""
    try:
        # Find the baseplate
        baseplate = db.query(models.Baseplate).filter(models.Baseplate.id == model_id).first()

        if not baseplate:
            raise HTTPException(status_code=404, detail="Baseplate not found")

        if not baseplate.model_id:
            raise HTTPException(status_code=404, detail="Baseplate has no associated model")

        # Get the model associated with this baseplate
        model = db.query(models.Model).filter(models.Model.id == baseplate.model_id).first()

        if not model:
            raise HTTPException(status_code=404, detail="Associated model not found")

        # Find the CAD file associated with this model
        cad_file = next((f for f in model.files if f.file_type.upper() == "FCSTD"), None)

        if not cad_file:
            raise HTTPException(status_code=404, detail="CAD file not found for this baseplate model")

        file_path = Path("/home/ron-maxseiner/PycharmProjects/drawerfinity/model-output") / cad_file.file_path

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="CAD file not found on disk")

        return FileResponse(
            path=file_path,
            filename=f"baseplate_{model_id}.FCStd",
            media_type="application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving CAD file for baseplate {model_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving CAD file: {str(e)}")