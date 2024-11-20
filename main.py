from fastapi import FastAPI
from routes import router

app = FastAPI()

# 라우터 등록
app.include_router(router)
