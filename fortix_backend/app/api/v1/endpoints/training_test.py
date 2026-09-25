from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    return {"message": "Training router is working"}

@router.get("/status")
async def get_status():
    return {"status": "idle", "message": "No training in progress"}
