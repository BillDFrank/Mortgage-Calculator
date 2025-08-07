import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="Mortgage Calculator API",
    description="API for mortgage calculations with EURIBOR integration",
    version="1.0.0"
)

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Mortgage Calculator API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)