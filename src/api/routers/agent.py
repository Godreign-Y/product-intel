from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.api.schemas.agent import AgentQueryRequest, AgentQueryResponse
from src.api.dependencies import get_planner_agent
from src.core.agent.planner import LLMPlannerAgent

router = APIRouter(prefix="/agent", tags=["LLM Planner Agent"])

@router.post("/query")
async def query_agent_endpoint(
    payload: AgentQueryRequest,
    agent: LLMPlannerAgent = Depends(get_planner_agent)
):
    try:
        return StreamingResponse(
            agent.process_query_stream(payload.query),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent process error: {str(e)}")
