"""
Agents API Endpoints
Manage DLP agents deployed on endpoints
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, ConfigDict
import structlog

from app.core.security import get_current_user
from app.core.database import get_mongodb

logger = structlog.get_logger()
router = APIRouter()


class AgentBase(BaseModel):
    """Base agent model"""
    name: str = Field(..., description="Agent name/hostname")
    os: str = Field(..., description="Operating system (windows/linux)")
    ip_address: str = Field(..., description="Agent IP address")
    version: str = Field(default="1.0.0", description="Agent version")


class AgentCreate(BaseModel):
    """Agent creation model"""
    agent_id: Optional[str] = Field(None, description="Custom agent ID (auto-generated if not provided)")
    name: str = Field(..., description="Agent name/hostname")
    os: str = Field(..., description="Operating system (windows/linux)")
    ip_address: str = Field(..., description="Agent IP address")
    version: str = Field(default="1.0.0", description="Agent version")


class Agent(AgentBase):
    """Agent response model"""
    agent_id: str = Field(..., description="Unique agent ID")
    status: str = Field(..., description="Agent status (online/offline/warning)")
    last_seen: datetime = Field(..., description="Last heartbeat timestamp")
    created_at: datetime = Field(..., description="Registration timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent_id": "agt-001",
                "name": "WIN-DESK-01",
                "os": "windows",
                "ip_address": "192.168.1.100",
                "version": "1.0.0",
                "status": "online",
                "last_seen": "2025-01-02T10:30:00Z",
                "created_at": "2025-01-01T08:00:00Z"
            }
        }
    )


@router.get("/", response_model=List[Agent])
async def list_agents(
    status: Optional[str] = None,
    os: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
) -> List[Agent]:
    """
    List all registered DLP agents

    Query parameters:
    - status: Filter by status (online/offline/warning)
    - os: Filter by operating system (windows/linux)
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    # Build query filter
    query = {}
    if status:
        query["status"] = status
    if os:
        query["os"] = os

    # Query agents from database
    agents_cursor = agents_collection.find(query).sort("last_seen", -1)
    agents = []

    async for agent_doc in agents_cursor:
        # Remove MongoDB _id field
        if "_id" in agent_doc:
            del agent_doc["_id"]
        agents.append(Agent(**agent_doc))

    logger.info("Listed agents", count=len(agents), filters=query)
    return agents


@router.post("/", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def register_agent(
    request: Request,
    agent: AgentCreate,
) -> Agent:
    """
    Register a new DLP agent (public endpoint - no auth required for agent self-registration)
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    # Extract agent_id from raw request body (workaround for Pydantic not picking up the field)
    body = await request.json()
    provided_agent_id = body.get("agent_id")

    # Use provided agent_id or generate one from name
    if provided_agent_id:
        agent_id = provided_agent_id
    else:
        agent_id = f"{agent.os.upper()}-{agent.name.replace(' ', '-')}"

    # Create agent document with custom agent_id
    now = datetime.utcnow()
    agent_doc = {
        "agent_id": agent_id,
        "name": agent.name,
        "os": agent.os,
        "ip_address": agent.ip_address,
        "version": agent.version,
        "status": "online",
        "last_seen": now,
        "created_at": now,
    }

    # Upsert - update if exists, insert if new
    await agents_collection.update_one(
        {"agent_id": agent_id},
        {"$set": agent_doc},
        upsert=True
    )

    logger.info("Agent registered", agent_id=agent_id, name=agent.name)
    return Agent(**agent_doc)


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
) -> Agent:
    """
    Get details of a specific agent
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    agent_doc = await agents_collection.find_one({"agent_id": agent_id})

    if not agent_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    # Remove MongoDB _id field
    if "_id" in agent_doc:
        del agent_doc["_id"]

    return Agent(**agent_doc)


@router.put("/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: str,
) -> Dict[str, Any]:
    """
    Update agent heartbeat (public endpoint - no auth required for agents)
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    result = await agents_collection.update_one(
        {"agent_id": agent_id},
        {
            "$set": {
                "last_seen": datetime.utcnow(),
                "status": "online"
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    logger.debug("Agent heartbeat", agent_id=agent_id)
    return {"status": "success", "message": "Heartbeat recorded"}


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete/unregister an agent
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    result = await agents_collection.delete_one({"agent_id": agent_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )

    logger.info("Agent deleted", agent_id=agent_id)
    return None


@router.get("/stats/summary")
async def get_agents_summary(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get summary statistics of all agents
    """
    db = get_mongodb()
    agents_collection = db["agents"]

    # Aggregate stats
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
