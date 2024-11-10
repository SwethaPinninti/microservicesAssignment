from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from bson import ObjectId
from bson.json_util import dumps, loads
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify the Streamlit app origin here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["content_db"]  

# Collections
tags_collection = db["tags"]  # Collection for tags
drafts_collection = db["drafts"]  # Collection for drafts
analytics_collection = db["analytics"]  # Collection for analytics

# Pydantic Models
class Tag(BaseModel):
    name: str

class Draft(BaseModel):
    title: str
    content: str
    user_id: str

class Analytics(BaseModel):
    content_id: str
    views: int = 0

class ContentTag(BaseModel):
    content_id: str
    tag_name: str

class ContentTags(BaseModel):
    content_id: str
    tags: List[str]

class ViewIncrement(BaseModel):
    draft_id: str

class ContentAnalytics(BaseModel):
    content_id: str
    views: int
    last_viewed: Optional[datetime]

class TopContent(BaseModel):
    content_id: str
    views: int

class DraftAnalytics(BaseModel):
    draft_id: str
    views: int
    last_viewed: Optional[datetime]

class TopDraft(BaseModel):
    draft_id: str
    views: int

# Tag Endpoints
@app.post("/tags/", response_model=Tag)
async def create_tag(tag: Tag):
    if tags_collection.find_one({"name": tag.name}):
        raise HTTPException(status_code=400, detail="Tag already exists")
    tags_collection.insert_one(tag.dict())
    return tag

@app.get("/tags/", response_model=List[Tag])
async def get_tags():
    return list(tags_collection.find({}, {"_id": 0}))

@app.get("/tags/{tag_name}", response_model=Optional[Tag])
async def get_tag(tag_name: str):
    tag = tags_collection.find_one({"name": tag_name}, {"_id": 0})
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

# Draft Endpoints
@app.post("/drafts/", response_model=Draft)
async def create_draft_db(draft: Draft):
    draft_dict = draft.dict()
    draft_dict["draft_id"] = str(uuid.uuid4())
    draft_dict["created_at"] = datetime.utcnow()
    draft_dict["updated_at"] = datetime.utcnow()
    
    result = drafts_collection.insert_one(draft_dict)
    if not result.acknowledged:
        raise HTTPException(status_code=400, detail="Failed to create draft")
    
    return draft_dict

@app.get("/drafts/{draft_id}", response_model=Draft)
async def get_draft_db(draft_id: str):
    draft = drafts_collection.find_one({"draft_id": draft_id})
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft

@app.get("/drafts/user/{user_id}", response_model=List[Draft])
async def get_user_drafts_db(user_id: str):
    drafts = list(drafts_collection.find({"user_id": user_id}))
    return drafts

@app.put("/drafts/{draft_id}", response_model=Draft)
async def update_draft_db(draft_id: str, draft_update: dict):
    draft = drafts_collection.find_one_and_update(
        {"draft_id": draft_id},
        {"$set": draft_update},
        return_document=True
    )
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return draft

@app.delete("/drafts/{draft_id}")
async def delete_draft_db(draft_id: str):
    result = drafts_collection.delete_one({"draft_id": draft_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"message": "Draft deleted successfully"}

# Analytics Endpoints
@app.post("/analytics/views/increment")
async def increment_view_count_db(view: ViewIncrement):
    result = analytics_collection.update_one(
        {"draft_id": view.draft_id},
        {
            "$inc": {"views": 1},
            "$set": {"last_viewed": datetime.utcnow()}
        },
        upsert=True
    )
    
    if not result.acknowledged:
        raise HTTPException(
            status_code=400, 
            detail="Failed to increment view count"
        )
    
    updated_analytics = analytics_collection.find_one({"draft_id": view.draft_id})
    if updated_analytics:
        updated_analytics["_id"] = str(updated_analytics["_id"])
    return updated_analytics

@app.get("/analytics/content/{content_id}", response_model=ContentAnalytics)
async def get_content_analytics_db(content_id: str):
    analytics = analytics_collection.find_one({"content_id": content_id})
    if not analytics:
        raise HTTPException(
            status_code=404, 
            detail="Content analytics not found"
        )
    return analytics

@app.get("/analytics/top-content", response_model=List[TopContent])
async def get_top_content_db(limit: int = 10):
    top_content = list(
        analytics_collection.find()
        .sort("views", -1)
        .limit(limit)
    )
    return top_content

@app.get("/analytics/views/total")
async def get_total_views_db():
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_views": {"$sum": "$views"}
            }
        }
    ]
    
    result = list(analytics_collection.aggregate(pipeline))
    total_views = result[0]["total_views"] if result else 0
    
    return {"total_views": total_views}

@app.get("/analytics/draft/{draft_id}", response_model=DraftAnalytics)
async def get_draft_analytics_db(draft_id: str):
    analytics = analytics_collection.find_one({"draft_id": draft_id})
    if not analytics:
        raise HTTPException(status_code=404, detail="Draft analytics not found")
    analytics["_id"] = str(analytics["_id"])
    return analytics

@app.get("/analytics/top-drafts", response_model=List[TopDraft])
async def get_top_drafts_db(limit: int = 10):
    top_drafts = list(
        analytics_collection.find()
        .sort("views", -1)
        .limit(limit)
    )
    return top_drafts

# Content-Tag relationship endpoints
@app.post("/content/tags/")
async def create_content_tag(content_tag: ContentTag):
    result = tags_collection.update_one(
        {"content_id": content_tag.content_id},
        {"$addToSet": {"tags": content_tag.tag_name}},
        upsert=True
    )
    return {"message": "Tag assigned successfully"}

@app.get("/content/{content_id}/tags")
async def get_content_tags(content_id: str):
    content = tags_collection.find_one({"content_id": content_id})
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content.get("tags", [])

@app.get("/tags/{tag_name}/content")
async def get_content_by_tag(tag_name: str):
    content_items = tags_collection.find({"tags": tag_name})
    return [item["content_id"] for item in content_items]

@app.delete("/content/{content_id}/tags/{tag_name}")
async def delete_content_tag(content_id: str, tag_name: str):
    result = tags_collection.update_one(
        {"content_id": content_id},
        {"$pull": {"tags": tag_name}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Tag or content not found")
    return {"message": "Tag removed successfully"}
