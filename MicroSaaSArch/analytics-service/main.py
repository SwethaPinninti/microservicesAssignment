from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import httpx
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify the Streamlit app origin here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MONGODB_SERVICE_URL = "http://localhost:8000"

class ViewIncrement(BaseModel):
    draft_id: str

class DraftAnalytics(BaseModel):
    draft_id: str
    views: int
    last_viewed: Optional[datetime]

class TopDraft(BaseModel):
    draft_id: str
    views: int

@app.post("/analytics/increment-view/{draft_id}")
async def increment_view_count(draft_id: str):
    """Increment the view count for a specific draft"""
    async with httpx.AsyncClient() as client:
        # First verify if draft exists
        draft_response = await client.get(f"{MONGODB_SERVICE_URL}/drafts/{draft_id}")
        if draft_response.status_code == 404:
            raise HTTPException(status_code=404, detail="Draft not found")
            
        response = await client.post(
            f"{MONGODB_SERVICE_URL}/analytics/views/increment",
            json={"draft_id": draft_id}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=400, 
                detail="Failed to increment view count"
            )
        
        data = response.json()
        return {
            "draft_id": data["draft_id"],
            "views": data["views"],
            "last_viewed": data.get("last_viewed")
        }

@app.get("/analytics/draft/{draft_id}", response_model=DraftAnalytics)
async def get_draft_analytics(draft_id: str):
    """Get analytics for a specific draft"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MONGODB_SERVICE_URL}/analytics/draft/{draft_id}"
        )
        
        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Draft analytics not found"
            )
        
        return response.json()

@app.get("/analytics/top-drafts", response_model=List[TopDraft])
async def get_top_drafts(limit: int = 10):
    """Get the most viewed drafts"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MONGODB_SERVICE_URL}/analytics/top-content?limit={limit}"
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=400, 
                detail="Failed to retrieve top drafts"
            )
        
        return response.json()

@app.get("/analytics/views/total")
async def get_total_views():
    """Get the total number of views across all drafts"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MONGODB_SERVICE_URL}/analytics/views/total"
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=400, 
                detail="Failed to retrieve total views"
            )
        
        return response.json()
