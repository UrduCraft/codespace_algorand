"""
Silexa Main Entry Point
Run the Silexa backend application
"""

import uvicorn
from backend.app.main import app
from backend.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
