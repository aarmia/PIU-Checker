from fastapi import APIRouter
from .songs import router as songs_router
from .all_data import router as all_data_router
from .dashboard import router as dashboard_router

router = APIRouter()

router.include_router(songs_router)
router.include_router(all_data_router)
router.include_router(dashboard_router)