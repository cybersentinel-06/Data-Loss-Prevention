"""
API v1 Router
Main API router aggregating all endpoints
"""

from fastapi import APIRouter

from app.api.v1 import auth, events, policies, users, dashboard, alerts, agents, classification

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(classification.router, prefix="/classification", tags=["Classification"])
api_router.include_router(policies.router, prefix="/policies", tags=["Policies"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
