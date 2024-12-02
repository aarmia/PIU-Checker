from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes import router


class CustomJSONResponse(JSONResponse):
    def render(self, content: any) -> bytes:
        import json
        return json.dumps(content, ensure_ascii=False).encode("utf-8")


app = FastAPI(default_response_class=CustomJSONResponse)


@app.middleware("http")
async def utf8_middleware(request, call_next):
    response = await call_next(request)
    if response.headers.get("Content-Type", "").startswith("application/json"):
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


# 라우터 등록
app.include_router(router)
