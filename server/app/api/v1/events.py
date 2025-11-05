"""
DLP Events API Endpoints
Query, filter, and manage DLP events
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
import structlog

from app.core.security import get_current_user
from app.core.database import get_mongodb

logger = structlog.get_logger()
router = APIRouter()


class DLPEvent(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    source: str
    user_email: str
    classification_score: float
    classification_labels: List[str]
    policy_id: Optional[str]
    action_taken: str
    severity: str
    file_path: Optional[str]
    destination: Optional[str]
    blocked: bool


class EventQueryParams(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    severity: Optional[List[str]] = None
    source: Optional[List[str]] = None
    user_email: Optional[str] = None
    blocked_only: bool = False


@router.get("/", response_model=List[DLPEvent])
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = None,
    source: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Get DLP events with pagination and filtering
    """
    db = get_mongodb()

    # Build query filter
    query_filter = {}
    if severity:
        query_filter["severity"] = severity
    if source:
        query_filter["source"] = source

    # Query MongoDB
    cursor = db.dlp_events.find(query_filter).sort("timestamp", -1).skip(skip).limit(limit)
    events = await cursor.to_list(length=limit)

    logger.info(
        "Events queried",
        user=current_user["email"],
        count=len(events),
        filters=query_filter,
    )

    return events


@router.get("/{event_id}", response_model=DLPEvent)
async def get_event(
    event_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get specific DLP event by ID
    """
    db = get_mongodb()
    event = await db.dlp_events.find_one({"id": event_id})

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return event


@router.get("/stats/summary")
async def get_event_stats(
    current_user: dict = Depends(get_current_user),
):
    """
    Get event statistics summary
    """
    db = get_mongodb()

    # Aggregate statistics
    total_events = await db.dlp_events.count_documents({})
    blocked_events = await db.dlp_events.count_documents({"blocked": True})

    # Events by severity
    severity_pipeline = [
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
    ]
    severity_stats = await db.dlp_events.aggregate(severity_pipeline).to_list(None)

    # Events by source
    source_pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}}
    ]
    source_stats = await db.dlp_events.aggregate(source_pipeline).to_list(None)

    return {
        "total_events": total_events,
        "blocked_events": blocked_events,
        "by_severity": {item["_id"]: item["count"] for item in severity_stats},
        "by_source": {item["_id"]: item["count"] for item in source_stats},
    }
