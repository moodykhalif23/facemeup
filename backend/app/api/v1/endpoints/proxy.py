"""Image proxy endpoint to handle CORS issues with external images"""
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/image")
async def proxy_image(url: str = Query(..., description="Image URL to proxy")):
    """
    Proxy external images to avoid CORS issues
    
    Args:
        url: The external image URL to fetch
        
    Returns:
        The image content with appropriate headers
    """
    try:
        if not url.startswith("https://"):
            raise HTTPException(status_code=400, detail="Invalid image URL format. Must be HTTPS.")
        
        # Fetch the image
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Get content type from response
            content_type = response.headers.get("content-type", "image/jpeg")
            
            # Return image with CORS headers
            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Access-Control-Allow-Origin": "*",
                }
            )
            
    except httpx.HTTPError as e:
        logger.error(f"Error fetching image from {url}: {e}")
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        logger.error(f"Unexpected error proxying image: {e}")
        raise HTTPException(status_code=500, detail="Error fetching image")
