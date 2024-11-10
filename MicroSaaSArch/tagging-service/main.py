from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
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
MONGODB_SERVICE_URL = "http://localhost:8000"  # MongoDB Maintenance Service URL

class Tag(BaseModel):
    name: str

class ContentTag(BaseModel):
    content_id: str
    tag_name: str

class ContentTags(BaseModel):
    content_id: str
    tags: List[str]

@app.post("/content/{content_id}/tags/")
async def assign_tag_to_content(content_id: str, tag: Tag):
    """Assign a tag to a specific content item"""
    async with httpx.AsyncClient() as client:
        # First, ensure the tag exists in the database
        tag_response = await client.get(f"{MONGODB_SERVICE_URL}/tags/{tag.name}")
        
        if tag_response.status_code == 404:
            # Create the tag if it doesn't exist
            await client.post(f"{MONGODB_SERVICE_URL}/tags/", json={"name": tag.name})
        
        # Associate the tag with the content
        content_tag = ContentTag(content_id=content_id, tag_name=tag.name)
        response = await client.post(
            f"{MONGODB_SERVICE_URL}/content/tags/",
            json=content_tag.dict()
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to assign tag")
        
        return {"message": f"Tag '{tag.name}' assigned to content {content_id}"}

@app.get("/content/{content_id}/tags/")
async def get_content_tags(content_id: str) -> List[str]:
    """Get all tags for a specific content item"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MONGODB_SERVICE_URL}/content/{content_id}/tags")
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Content not found")
        
        return response.json()

@app.get("/tags/{tag_name}/content/")
async def get_content_by_tag(tag_name: str) -> List[str]:
    """Get all content items associated with a specific tag"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MONGODB_SERVICE_URL}/tags/{tag_name}/content")
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Tag not found")
        
        return response.json()

@app.delete("/content/{content_id}/tags/{tag_name}")
async def remove_tag_from_content(content_id: str, tag_name: str):
    """Remove a tag from a specific content item"""
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{MONGODB_SERVICE_URL}/content/{content_id}/tags/{tag_name}"
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Tag or content not found")
        
        return {"message": f"Tag '{tag_name}' removed from content {content_id}"}
