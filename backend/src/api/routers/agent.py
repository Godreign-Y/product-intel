from fastapi import APIRouter, Depends, HTTPException

from src.api.schemas.agent import AgentQueryRequest, AgentQueryResponse
from src.api.dependencies import get_planner_agent
from src.core.agent.planner import LLMPlannerAgent

router = APIRouter(prefix="/agent", tags=["LLM Planner Agent"])

@router.post("/query", response_model=AgentQueryResponse)
async def query_agent_endpoint(
    payload: AgentQueryRequest,
    agent: LLMPlannerAgent = Depends(get_planner_agent)
):
    try:
        result = agent.process_query(payload.query)
        return AgentQueryResponse(
            query=result["query"],
            route_called=result["route_called"],
            raw_data=result["raw_data"],
            response=result["response"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent process error: {str(e)}")
