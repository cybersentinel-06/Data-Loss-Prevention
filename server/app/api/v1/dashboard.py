"""
Dashboard API Endpoints
Real-time statistics and metrics for dashboard
Returns actual data from database (populated by agents)
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
import structlog

from app.core.security import get_current_user
from app.core.database import get_mongodb

logger = structlog.get_logger()
router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get dashboard overview statistics
    Returns real data from database populated by agents
    """
    db = get_mongodb()

    # Calculate time ranges
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    # Query actual data from database
    events_collection = db["events"]
    policies_collection = db["policies"]

    # Total events
    total_events_24h = await events_collection.count_documents({
        "timestamp": {"$gte": last_24h}
    })
    total_events_7d = await events_collection.count_documents({
        "timestamp": {"$gte": last_7d}
    })

    # Blocked events
    blocked_events_24h = await events_collection.count_documents({
        "timestamp": {"$gte": last_24h},
        "action": "blocked"
    })
    blocked_events_7d = await events_collection.count_documents({
        "timestamp": {"$gte": last_7d},
        "action": "blocked"
    })

    # High severity events
    critical_events_24h = await events_collection.count_documents({
        "timestamp": {"$gte": last_24h},
        "severity": "critical"
    })
    critical_events_7d = await events_collection.count_documents({
        "timestamp": {"$gte": last_7d},
        "severity": "critical"
    })

    # Active policies
    active_policies = await policies_collection.count_documents({
        "status": "active"
    })

    # Top users by event count
    top_users_pipeline = [
        {"$match": {"timestamp": {"$gte": last_24h}}},
        {"$group": {"_id": "$user_email", "event_count": {"$sum": 1}}},
        {"$sort": {"event_count": -1}},
        {"$limit": 5}
    ]
    top_users_cursor = events_collection.aggregate(top_users_pipeline)
    top_users = []
    async for user in top_users_cursor:
        top_users.append({
            "email": user["_id"],
            "event_count": user["event_count"]
        })

    # Top policy violations
    top_violations_pipeline = [
        {"$match": {"timestamp": {"$gte": last_7d}}},
        {"$group": {"_id": "$policy_name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    top_violations_cursor = events_collection.aggregate(top_violations_pipeline)
    top_violations = []
    async for violation in top_violations_cursor:
        top_violations.append({
            "policy": violation["_id"],
            "count": violation["count"]
        })

    # Recent events
    recent_events_cursor = events_collection.find().sort("timestamp", -1).limit(10)
    recent_events = []
    async for event in recent_events_cursor:
        recent_events.append({
            "id": str(event["_id"]),
            "timestamp": event["timestamp"].isoformat() if isinstance(event["timestamp"], datetime) else event["timestamp"],
            "severity": event.get("severity", "medium"),
            "description": event.get("description", ""),
            "blocked": event.get("action") == "blocked",
        })

    return {
        "metrics": {
            "events_24h": total_events_24h,
            "events_7d": total_events_7d,
            "blocked_24h": blocked_events_24h,
            "blocked_7d": blocked_events_7d,
            "critical_24h": critical_events_24h,
            "critical_7d": critical_events_7d,
            "active_policies": active_policies,
        },
        "top_users": top_users,
        "top_violations": top_violations,
        "recent_events": recent_events,
    }


@router.get("/timeline")
async def get_event_timeline(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to retrieve"),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get event timeline data for charts
    Returns actual event counts grouped by hour
    """
    db = get_mongodb()
    events_collection = db["events"]

    now = datetime.utcnow()
    start_time = now - timedelta(hours=hours)

    # Aggregate events by hour
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_time}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%dT%H:00:00Z",
                        "date": "$timestamp"
                    }
                },
                "total_events": {"$sum": 1},
                "blocked_events": {
                    "$sum": {"$cond": [{"$eq": ["$action", "blocked"]}, 1, 0]}
                },
                "critical_events": {
                    "$sum": {"$cond": [{"$eq": ["$severity", "critical"]}, 1, 0]}
                }
            }
        },
        {"$sort": {"_id": 1}}
    ]

    cursor = events_collection.aggregate(pipeline)
    timeline_data = []

    async for item in cursor:
        timeline_data.append({
            "timestamp": item["_id"],
            "total_events": item["total_events"],
            "blocked_events": item["blocked_events"],
            "critical_events": item["critical_events"],
        })

    return {"timeline": timeline_data}


@router.get("/stats/agents")
async def get_agents_stats(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get agent statistics
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    total = await agents_collection.count_documents({})
    online = await agents_collection.count_documents({"status": "online"})
    offline = await agents_collection.count_documents({"status": "offline"})
    warning = await agents_collection.count_documents({"status": "warning"})

    return {
        "total": total,
        "online": online,
        "offline": offline,
        "warning": warning,
    }


@router.get("/stats/classification")
async def get_classification_stats(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get data classification statistics
    """
    db = get_mongodb()
    files_collection = db["classified_files"]

    total = await files_collection.count_documents({})
    public = await files_collection.count_documents({"classification": "public"})
    internal = await files_collection.count_documents({"classification": "internal"})
    confidential = await files_collection.count_documents({"classification": "confidential"})
    restricted = await files_collection.count_documents({"classification": "restricted"})

    return {
        "total": total,
        "public": public,
        "internal": internal,
        "confidential": confidential,
        "restricted": restricted,
    }
