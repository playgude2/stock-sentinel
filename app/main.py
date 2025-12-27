from fastapi import FastAPI
import uvicorn.config

from app.routers.whatsapp import router as whatsapp_router

# Initialize FastAPI
app = FastAPI()

# Include routers
app.include_router(whatsapp_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
