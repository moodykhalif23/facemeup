from fastapi import APIRouter

from app.schemas.sync import BitmojiSyncRequest, BitmojiSyncResponse


router = APIRouter()


@router.post("/bitmoji", response_model=BitmojiSyncResponse)
def sync_bitmoji(payload: BitmojiSyncRequest) -> BitmojiSyncResponse:
    _ = payload
    return BitmojiSyncResponse(synced=True)
