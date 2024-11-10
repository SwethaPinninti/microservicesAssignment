from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
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

class DraftCreate(BaseModel):
    title: str
    content: str
    user_id: str

class DraftUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class Draft(DraftCreate):
    draft_id: str
    created_at: datetime
    updated_at: datetime

@app.post("/drafts/", response_model=Draft)
async def create_draft(draft: DraftCreate):
    """Create a new content draft"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MONGODB_SERVICE_URL}/drafts/",
            json={
                **draft.dict(),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to create draft")
        
        return response.json()

@app.get("/drafts/{draft_id}", response_model=Draft)
async def get_draft(draft_id: str):
    """Retrieve a specific draft"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MONGODB_SERVICE_URL}/drafts/{draft_id}")
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        return response.json()

@app.get("/drafts/user/{user_id}", response_model=List[Draft])
async def get_user_drafts(user_id: str):
    """Get all drafts for a specific user"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MONGODB_SERVICE_URL}/drafts/user/{user_id}")
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="User not found")
        
        return response.json()

@app.put("/drafts/{draft_id}", response_model=Draft)
async def update_draft(draft_id: str, draft_update: DraftUpdate):
    """Update an existing draft"""
    async with httpx.AsyncClient() as client:
        # Add updated_at timestamp
        update_data = {
            **draft_update.dict(exclude_unset=True),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = await client.put(
            f"{MONGODB_SERVICE_URL}/drafts/{draft_id}",
            json=update_data
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        return response.json()

@app.delete("/drafts/{draft_id}")
async def delete_draft(draft_id: str):
    """Delete a draft"""
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{MONGODB_SERVICE_URL}/drafts/{draft_id}")
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        return {"message": "Draft deleted successfully"}
