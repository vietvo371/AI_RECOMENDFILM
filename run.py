import os
import sys

# Thêm đường dẫn hiện tại vào PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from app.core.config import settings
from fastapi import FastAPI
from app.api import endpoints


app = FastAPI()

app.include_router(endpoints.router, prefix="/api")



if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=5001,
        reload=True if settings.API_ENV == "development" else False
    ) 