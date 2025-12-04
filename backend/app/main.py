from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import metro

app = FastAPI(
    title="深圳地铁寻路游戏 API",
    description="深圳地铁最短路径查找和验证 API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(metro.router, prefix="/api", tags=["metro"])

@app.get("/")
async def root():
    return {
        "message": "深圳地铁寻路游戏 API",
        "docs": "/docs",
        "version": "1.0.0"
    }
