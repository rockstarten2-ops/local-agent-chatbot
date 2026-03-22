"""FastAPI backend for agents."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Agents.routes.agent_router import router as agent_router
from Agents.config import API_HOST, API_PORT

app = FastAPI(
    title="Local Agent Chatbot API",
    description="Multi-agent system with ChromaDB semantic search",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agent_router)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "API is running"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Local Agent Chatbot API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "api": "/api/agents"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )
