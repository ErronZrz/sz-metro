from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import metro

app = FastAPI(
    title="地铁寻路游戏 API",
    description="地铁最短路径查找和验证 API（支持深圳、上海、北京、广州、长沙）",
    version="1.3.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (frontend proxies API requests via Nginx)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(metro.router, prefix="/api", tags=["metro"])

@app.get("/")
async def root():
    return {
        "message": "地铁寻路游戏 API",
        "docs": "/docs",
        "version": "1.3.0",
        "supported_cities": ["sz", "sh", "bj", "gz", "cs"]
    }
