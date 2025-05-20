from fastapi import APIRouter
# wrap Microsoft Graph calls: fetch messages, move messages
router = APIRouter()

@router.post("/run-cleanse")
async def run_cleanse():
    # fetch messages, call classifier, move & record undo
    ...
