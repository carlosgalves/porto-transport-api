import os
import uvicorn
from app.core.config import settings
from app.main import app

if __name__ == "__main__":
    workers = int(os.getenv("WEB_CONCURRENCY", "1"))
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.port,
        workers=workers,
    )