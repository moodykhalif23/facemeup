from pydantic import BaseModel


class BitmojiSyncRequest(BaseModel):
    skin_type: str
    conditions: list[str]
    source_scan_id: str


class BitmojiSyncResponse(BaseModel):
    synced: bool


class WooCommerceSyncResponse(BaseModel):
    success: bool
    products_synced: int
    products_added: int
    products_updated: int
    products_failed: int
    message: str


class WooCommerceWcIdSyncResponse(BaseModel):
    success: bool
    total_missing: int
    updated: int
    still_missing: int
    message: str
