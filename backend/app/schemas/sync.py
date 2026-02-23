from pydantic import BaseModel


class BitmojiSyncRequest(BaseModel):
    user_id: str
    skin_type: str
    conditions: list[str]
    source_scan_id: str


class BitmojiSyncResponse(BaseModel):
    synced: bool
