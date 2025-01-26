from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Gridfinity API")

# Update CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Update to match your frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)