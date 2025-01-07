from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.routes import router  # 모듈화된 라우트 임포트
from api.services.db import load_all_image_urls # 캐싱 초기화 위해

# JSON 응답 클래스 커스터마이징
class CustomJSONResponse(JSONResponse):
    def render(self, content: any) -> bytes:
        import json
        return json.dumps(content, ensure_ascii=False).encode("utf-8")


# FastAPI 앱 생성
app = FastAPI(default_response_class=CustomJSONResponse)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    서버 시작 시 이미지 URL 캐싱 초기화
    """
    load_all_image_urls()  # DB에서 이미지 데이터 로드 후 캐싱


@app.middleware("http")
async def utf8_middleware(request, call_next):
    """
    모든 JSON 응답에 UTF-8 인코딩 적용
    """
    response = await call_next(request)
    if response.headers.get("Content-Type", "").startswith("application/json"):
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


# API 라우터 등록
app.include_router(router)
