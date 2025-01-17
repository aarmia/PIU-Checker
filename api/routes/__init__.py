from fastapi import APIRouter
from .auth import router as auth_router
from .user import router as user_router
from .levels import router as levels_router
from .pumbility import router as pumbility_router
from .recently import router as recently_router
from .songs import router as songs_router
from .all_data import router as all_data_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(user_router)
router.include_router(levels_router)
router.include_router(pumbility_router)
router.include_router(recently_router)
router.include_router(songs_router)
router.include_router(all_data_router)
