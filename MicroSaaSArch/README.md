# Content Management Microservices

A microservices-based content management system built with FastAPI that handles content drafts, tagging, and analytics.

## Services

- **Draft Service**: Manages content drafts with versioning
- **Tagging Service**: Handles content tagging and categorization
- **MongoDB Maintenance Service**: Database operations service
- **Analytics Service**: Tracks content metrics and analytics

## Installation

1. Clone the repository
2. Create virtual environments and install dependencies for each service:

```bash
# For each service directory (draft-service, tagging-service, etc.)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Each service runs on its own port:

- MongoDB Maintenance Service: http://localhost:8000
- Draft Service: http://localhost:8001
- Tagging Service: http://localhost:8002
- Analytics Service: http://localhost:8003

## Usage Example

Here's a complete example showing how to use all services together:

```python
import httpx
import asyncio
from datetime import datetime

async def main():
    # 1. Create a new draft
    draft_data = {
        "title": "My First Blog Post",
        "content": "This is the content of my first blog post",
        "user_id": "user123"
    }
    
    async with httpx.AsyncClient() as client:
        # Create draft
        draft_response = await client.post(
            "http://localhost:8001/drafts/",
            json=draft_data
        )
        draft = draft_response.json()
        print(f"Created draft: {draft}")
        
        # Add tags to the content
        tag_data = {"name": "technology"}
        tag_response = await client.post(
            f"http://localhost:8002/content/{draft['draft_id']}/tags/",
            json=tag_data
        )
        print(f"Added tag: {tag_response.json()}")
        
        # Track analytics event
        analytics_data = {
            "content_id": draft['draft_id'],
            "event_type": "content_created",
            "timestamp": datetime.utcnow().isoformat()
        }
        analytics_response = await client.post(
            "http://localhost:8003/events/",
            json=analytics_data
        )
        print(f"Tracked event: {analytics_response.json()}")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Documentation

Each service provides its own Swagger UI documentation at `/docs`:

- MongoDB Service: http://localhost:8000/docs
- Draft Service: http://localhost:8001/docs
- Tagging Service: http://localhost:8002/docs
- Analytics Service: http://localhost:8003/docs

## Service Details

### Draft Service
Reference to implementation:
```python:draft-service/main.py
startLine: 1
endLine: 51
```

### Tagging Service
Reference to implementation:
```python:tagging-service/main.py
startLine: 1
endLine: 51
```

## Dependencies

Each service requires:
- FastAPI
- httpx
- pydantic

The MongoDB Maintenance Service additionally requires:
- pymongo

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

MIT

