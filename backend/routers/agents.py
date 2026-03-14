from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from config.agent_config import AGENT_CONFIGS

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


class AgentListItem(BaseModel):
    id: str
    name: str
    description: str
    display_order: int
    enabled: bool = True


DISPLAY_ORDER = [
    "brief_analyzer",
    "trend_agent",
    "case_intelligence",
    "market_landscape",
    "insight_generator",
    "creator_agent",
]


@router.get("", response_model=List[AgentListItem])
async def list_agents() -> List[AgentListItem]:
    """
    Agent catalog for the left-side "Agents Team" panel.
    """
    items: List[AgentListItem] = []

    for idx, agent_id in enumerate(DISPLAY_ORDER, start=1):
        conf = AGENT_CONFIGS.get(agent_id)
        if not conf:
            continue
        items.append(
            AgentListItem(
                id=agent_id,
                name=conf.get("display_name") or conf.get("name", agent_id),
                description=conf.get("description", ""),
                display_order=idx,
                enabled=True,
            )
        )

    return items
